import os
import chromadb
import uuid
import time
import json
import re
import sys
import ast
from typing import List, Dict, Optional, Tuple, Any
from dotenv import load_dotenv
from openai import OpenAI

# Add current directory to path for module imports
sys.path.append(os.path.dirname(__file__))
from calc_tools import SafeCalculator
from demand_session import DemandSession

import argparse

# Configuration
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.gemini', 'chroma_db')
EMBEDDING_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o"

DOMAIN_MAP = {
    "healthcare": {"collection": "rag_healthcare", "desc": "Healthcare (FGI + NFPA + FBC)"},
    "code": {"collection": "rag_code_only", "desc": "Code Books Only (NFPA Standards)"},
    "military": {"collection": "rag_military", "desc": "Military (UFC & Specs)"},
}

SYSTEM_PROMPT = """You are an expert technical assistant for NFPA codes, standards, and compliance calculations.

PROTOCOL:
1. RESTATE: Briefly restate the user's question in technical compliance terms.
2. SUFFICIENCY CHECK: Do you have enough cited context to answer?
   - If yes: Proceed.
   - If no: State "Information not found" or ask specific clarifying questions.
3. CONFLICT CHECK: If sources conflict (e.g., FGI vs NFPA), identify the conflict.

CALCULATION PROTOCOL:
1. Find the formula or unit value in the retrieved text (e.g., '180 VA per yoke').
2. Extract the variables from the user's query (e.g., '10 receptacles').
3. If variables are missing, ASK the user.
4. Once you have formula + variables, call the `perform_calculation` tool.
5. Output the result referencing the Citation.

OUTPUT FORMAT (Two Channels):

### Normative Answer (CITED ONLY)
- State ONLY requirements directly supported by the provided Context.
- MUST cite (Source, Section) for every claim, number, or usage rule.
- If performing a calculation, cite the specific rule/table used for the formula.
- List any exceptions explicitly found in the text.

### Guidance (Non-Citable)
- Provide calculation steps, input assumptions, and practical advice.
- Example: "Using the general lighting load of 3 VA/ft² from Table 220.12..."
- CLEARLY label any values provided by the user vs. constants from the code.
- Do NOT invent requirements or "rules of thumb" not found in the text.

CRITICAL CONSTRAINTS:
- No uncited numeric values or thresholds.
- Do not make up section numbers.
- If information is missing, STOP and ask or state "Not found".
"""

class RAGAgent:
    def __init__(self, collection_name):
        self.load_environment()
        self.client = OpenAI()
        self.calculator = SafeCalculator()
        
        if not os.path.exists(CHROMA_DIR):
            print(f"Warning: ChromaDB directory not found at {CHROMA_DIR}. Run ingest_books.py first.")
            self.collection = None
        else:
            try:
                self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
                # Check if collection exists
                try:
                    self.collection = self.chroma_client.get_collection(name=collection_name)
                    print(f"RAG Agent initialized. Connected to '{collection_name}' ({self.collection.count()} chunks).")
                except Exception:
                    print(f"Error: Collection '{collection_name}' does not exist. Run ingest_books.py --domain <name> first.")
                    self.collection = None
            except Exception as e:
                print(f"Error connecting to ChromaDB: {e}")
                self.collection = None

    def load_environment(self):
        """Load environment variables."""
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        load_dotenv(dotenv_path)
        if not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not found in .env file")

    def detect_domain(self, query: str) -> str:
        """Detect domain from query patterns."""
        q = query.lower()
        if any(x in q for x in ["ufc", "military", "corps of engineers", "dod"]):
            return "military"
        if any(x in q for x in ["fgi", "patient", "hospital", "nurse", "clinical"]):
            return "healthcare"
        if any(x in q for x in ["nec", "nfpa 70", "code", "article 210", "wiring"]):
            return "code"
        return "unknown"

    def detect_intent(self, query: str) -> str:
        """Detect if user wants a calculation or just information."""
        q = query.lower()
        calc_triggers = ["calculate", "demand", "load", "how many", "size of", "rating for", "va", "watts", "amps"]
        if any(x in q for x in calc_triggers):
            return "calc"
        return "lookup"
        
    def log_telemetry(self, data: Dict):
        """Log telemetry to console (production: file/db)."""
        print(f"\n[TELEMETRY] {json.dumps(data, default=str)}")

    def rank_parents(self, parents_map: Dict, k_top_children: int = 50) -> List[Dict]:
        """
        V3 Ranking Formula:
        Score = 0.55 * Max(Child) + 0.35 * Norm(Sum_Top5) + 0.10 * Norm(Count)
        """
        # Calculate raw components
        for pid, data in parents_map.items():
            child_scores = sorted(data["child_scores"], reverse=True)
            data["max_score"] = child_scores[0]
            data["sum_top5"] = sum(child_scores[:5])
            
        # Normalize
        max_sum = max((d["sum_top5"] for d in parents_map.values()), default=1)
        max_count = max((d["child_count"] for d in parents_map.values()), default=1)
        
        ranked = []
        for pid, data in parents_map.items():
            s_max = data["max_score"] # Typically 0-1ish already if cosine distance inverted, wait. Chroma returns distance.
            # Assuming distance. We converted to relevance score below.
            
            s_sum_norm = data["sum_top5"] / max_sum
            s_count_norm = data["child_count"] / max_count
            
            final_score = (0.55 * s_max) + (0.35 * s_sum_norm) + (0.10 * s_count_norm)
            data["final_score"] = final_score
            ranked.append(data)
            
        return sorted(ranked, key=lambda x: x["final_score"], reverse=True)

    def retrieve(self, query: str, k_children: int = 50, k_parents: int = 10) -> List[Dict]:
        """
        Retrieves top `k_children` *Child* chunks.
        Groups them by Parent.
        Ranks Parents by score.
        Returns top `k_parents` full Parent texts.
        """
        if not self.collection:
            return []

        # 1. Embed Query
        try:
            query_emb = self.client.embeddings.create(input=[query], model=EMBEDDING_MODEL).data[0].embedding
        except Exception as e:
            print(f"Error embedding query: {e}")
            return []

        # 2. Query Chroma (Child Chunks)
        print(f"  - Searching for top {k_children} child chunks...")
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=k_children, 
            include=["metadatas", "documents", "distances"]
        )
        
        if not results['ids'] or not results['ids'][0]:
            return []
            
        # 3. Collapse to Parents
        parents_map = {} 
        
        ids = results['ids'][0]
        metadatas = results['metadatas'][0]
        distances = results['distances'][0]
        
        for i, meta in enumerate(metadatas):
            parent_id = meta.get("parent_id")
            dist = distances[i] 
            # Convert L2 distance to Similarity Score (Approximate)
            # score = 1 / (1 + distance) is a decent proxy for relevance
            score = 1.0 / (1.0 + dist)
            
            if not parent_id:
                continue
                
            if parent_id not in parents_map:
                parents_map[parent_id] = {
                    "parent_id": parent_id,
                    "text": meta.get("parent_text", ""),
                    "source": meta.get("source", "Unknown"),
                    "domain": meta.get("domain", "unknown"),
                    "child_scores": [],
                    "child_count": 0
                }
            
            parents_map[parent_id]["child_scores"].append(score)
            parents_map[parent_id]["child_count"] += 1

        # 4. Rank Parents
        sorted_parents = self.rank_parents(parents_map)
        
        # 5. Return Top k_parents
        final_parents = sorted_parents[:k_parents]
        print(f"  - Collapsed {len(parents_map)} parents. Returning top {len(final_parents)}.")
        
        return final_parents

    def query(self, user_query: str, history: List[Dict] = None) -> str:
        """
        Main entry point for QA with V3 Logic: Intent -> Retrieval -> Calculation -> Answer.
        """
        start_time = time.time()
        
        # 1. Router
        domain = self.detect_domain(user_query)
        intent = self.detect_intent(user_query)
        print(f"DEBUG: Domain={domain}, Intent={intent}")
        
        # 2. Retrieve Context
        print(f"Retrieving context for: {user_query}")
        docs = self.retrieve(user_query, k_children=50, k_parents=10)
        
        if not docs:
            self.log_telemetry({"query": user_query, "found": False})
            return "Information not found in the provided library."
            
        # 3. Format Context
        context_str = ""
        citation_sources = set()
        for i, doc in enumerate(docs):
            src = f"{doc['source']} ({doc.get('domain','?')})"
            context_str += f"\n--- Source: {src} ---\n{doc['text']}\n"
            citation_sources.add(src)
            
        print(f"Found {len(docs)} relevant sections.")
        
        # 4. Prepare LLM Call
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history[-2:]) 
            
        user_prompt = f"Context:\n{context_str}\n\nQuestion: {user_query}"
        messages.append({"role": "user", "content": user_prompt})
        
        # 5. Execute with Tools if Calculation needed
        tools = None
        if intent == "calc":
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "perform_calculation",
                        "description": "Performs mathematical calculations when a formula is found in the text. Input must be a mathematical expression.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {"type": "string", "description": "The math expression (e.g., '1200 * 3 / 100')"},
                                "source_citation": {"type": "string", "description": "The Code Section providing the formula"}
                            },
                            "required": ["expression", "source_citation"]
                        }
                    }
                }
            ]
            
        try:
            print("  - Generating answer (calling LLM)...")
            response = self.client.chat.completions.create(
                model=CHAT_MODEL,
                messages=messages,
                temperature=0.0,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            
            msg = response.choices[0].message
            
            # Handle Tool Calls
            if msg.tool_calls:
                messages.append(msg) # Add Assistant's tool call intent
                for tool_call in msg.tool_calls:
                    if tool_call.function.name == "perform_calculation":
                        args = json.loads(tool_call.function.arguments)
                        print(f"  - Executing Calculation: {args}")
                        
                        # Execute Safe Calculation
                        result = self.calculator.evaluate_expression(args.get("expression", "0"))
                        
                        # Add Result to history
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                        
                        # Log Telemetry
                        self.log_telemetry({
                            "type": "calc_execution",
                            "inputs": args,
                            "output": result
                        })
                
                # Get final response after tool execution
                final_response = self.client.chat.completions.create(
                    model=CHAT_MODEL,
                    messages=messages,
                    temperature=0.0
                )
                answer = final_response.choices[0].message.content
            else:
                answer = msg.content
                
            # Final Telemetry
            self.log_telemetry({
                "query": user_query,
                "intent": intent,
                "domain": domain,
                "sources_count": len(docs),
                "duration": time.time() - start_time
            })
            
            return answer
            
        except Exception as e:
            return f"Error generating response: {e}"

def chat_loop():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=DOMAIN_MAP.keys(), help="Select domain agent")
    args = parser.parse_args()
    
    selected_domain = args.domain
    if not selected_domain:
        print("\n--- Select an Agent ---")
        domains = list(DOMAIN_MAP.keys())
        for i, d in enumerate(domains):
            print(f"{i+1}. {d.title().ljust(12)} - {DOMAIN_MAP[d]['desc']}")
        
        choice = input("\nEnter number (1-3): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(domains):
                selected_domain = domains[idx]
            else:
                print("Invalid selection.")
                return
        except:
             print("Invalid selection.")
             return
             
    col_name = DOMAIN_MAP[selected_domain]["collection"]
    print(f"\nStarting {selected_domain.upper()} Agent...")
    
    agent = RAGAgent(collection_name=col_name)
    if not agent.collection:
        return

    print("\n--- Advanced NFPA RAG Ready (Type 'exit' to quit) ---")
    history = []
    
    active_session = None
    sessions = {}
    
    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input:
                continue
                
            # --- 1. New Session Command ---
            # Pattern: calculator.demand[instance_name, [funcs], sqft]
            if user_input.startswith("calculator.demand"):
                # Regex to capture: name, [list], sqft
                # usage: calculator.demand[my_workspace, [elevators, fire_alarm], 50000]
                new_session_match = re.match(r"calculator\.demand\[\s*([^,]+),\s*(\[.*?\]),\s*(\d+)\s*\]", user_input)
                
                if new_session_match:
                    name = new_session_match.group(1).strip()
                    funcs_str = new_session_match.group(2).strip()
                    sqft = new_session_match.group(3).strip()
                    
                    # Parse the list manually to allow unquoted strings
                    try:
                        content = funcs_str.strip('[]')
                        funcs_list = [item.strip().strip("'\"") for item in content.split(',') if item.strip()]
                        
                        if funcs_list:
                             session = DemandSession(name, funcs_list, float(sqft))
                             sessions[name] = session
                             active_session = session
                             print(f"\nAI: {session.start()}")
                             continue
                    except Exception as e:
                        print(f"\nAI: Error starting session: {e}")
                        continue
                else:
                    # Prefix matched but regex failed -> Syntax Error
                    print("\nAI: Invalid syntax for calculator.demand.")
                    print("    Usage: calculator.demand[name, [func1, func2], sqft]")
                    print("    Example: calculator.demand[test, [elevators], 50000]")
                    continue

            # --- 2. Export Command ---
            # Pattern: demand.instance.export()
            if user_input.startswith("demand.") and ".export()" in user_input:
                export_match = re.match(r"demand\.(.+)\.export\(\)", user_input)
                if export_match:
                    name = export_match.group(1).strip()
                    if name in sessions:
                        print(f"\nAI: {sessions[name].export_csv()}")
                    else:
                         print(f"\nAI: Instance '{name}' not found. Active sessions: {list(sessions.keys())}")
                    continue
                else:
                    print("\nAI: Invalid export format. Usage: demand.instance_name.export()")
                    continue

            # --- 3. Active Session Input ---
            if active_session and not active_session.is_completed:
                result_msg = active_session.process_input(user_input)
                print(f"\nAI: {result_msg}")
                if active_session.is_completed:
                    active_session = None
                continue
                
            response = agent.query(user_input, history)
            print(f"\nAI: {response}")
            
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    chat_loop()
