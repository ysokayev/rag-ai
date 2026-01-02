import os
import glob
import pickle
import numpy as np
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

# Configuration
BOOKS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'Books')
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.tmp')
CACHE_FILE = os.path.join(CACHE_DIR, 'rag_cache.pkl')
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"

def load_environment():
    """Load environment variables."""
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(dotenv_path)
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY not found in .env file")

def ensure_directories():
    """Ensure necessary directories exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def read_books() -> List[Dict[str, str]]:
    """Read all .txt files from Books directory."""
    documents = []
    if not os.path.exists(BOOKS_DIR):
        print(f"Warning: Books directory not found at {BOOKS_DIR}")
        return documents

    files = glob.glob(os.path.join(BOOKS_DIR, "*.txt"))
    print(f"Found {len(files)} books.")
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                documents.append({"source": file_name, "text": text})
        except Exception as e:
            print(f"Error reading {file_name}: {e}")
    
    return documents

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Simple character-based chunking."""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
        
    return chunks

import time

def get_embeddings(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    # OpenAI suggests batching, but for simplicity/reliability we'll limit batch size
    batch_size = 50  # Reduced batch size to help with rate limits
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        attempts = 0
        max_attempts = 5
        
        while attempts < max_attempts:
            try:
                response = client.embeddings.create(input=batch, model=EMBEDDING_MODEL)
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)
                break
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str or "429" in error_str:
                    wait_time = (2 ** attempts) * 2  # 2, 4, 8, 16, 32 seconds
                    print(f"Rate limit hit. Retrying batch {i} in {wait_time}s...")
                    time.sleep(wait_time)
                    attempts += 1
                else:
                    print(f"Error generating embeddings for batch {i}: {e}")
                    raise e
        else:
            raise Exception(f"Failed to generate embeddings after {max_attempts} attempts due to rate limiting.")
            
    return all_embeddings

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def build_index(client: OpenAI):
    """Read, chunk, and index books."""
    raw_docs = read_books()
    if not raw_docs:
        print("No documents to index.")
        return None

    indexed_chunks = [] # List of {"text": str, "source": str, "embedding": list}
    all_chunk_texts = []
    
    print("Process & Chunking...")
    for doc in raw_docs:
        chunks = chunk_text(doc["text"])
        for c in chunks:
            all_chunk_texts.append(c)
            indexed_chunks.append({"text": c, "source": doc["source"]})
    
    print(f"Generating embeddings for {len(all_chunk_texts)} chunks...")
    embeddings = get_embeddings(client, all_chunk_texts)
    
    for i, emb in enumerate(embeddings):
        indexed_chunks[i]["embedding"] = emb
        
    # Save to cache
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(indexed_chunks, f)
        
    print(f"Index built and saved to {CACHE_FILE}")
    return indexed_chunks

def load_index(client: OpenAI):
    """Load index from cache or build if missing."""
    if os.path.exists(CACHE_FILE):
        print("Loading index from cache...")
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    else:
        return build_index(client)

def retrieve(query: str, index: List[Dict], client: OpenAI, k: int = 5):
    """Retrieve top k chunks for query."""
    query_emb = client.embeddings.create(input=[query], model=EMBEDDING_MODEL).data[0].embedding
    query_vec = np.array(query_emb)
    
    scored_chunks = []
    for item in index:
        item_vec = np.array(item["embedding"])
        score = cosine_similarity(query_vec, item_vec)
        scored_chunks.append((score, item))
        
    # Sort descending
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return scored_chunks[:k]

SYSTEM_PROMPT = """You are a helpful expert assistant for NFPA codes and standards. 
Use the provided Context to answer the user's question. 
CRITICAL INSTRUCTIONS:
1. ALWAYS cite the specific source file (e.g., 'nfpa70.txt') for every piece of information.
2. ALWAYS cite the specific Code Section/Article numbers (e.g., 'Article 250.4', 'Section 13.4.1') if present in the text.
3. Do not generalize. If the text lists specific requirements, list them with their section numbers.
4. If the answer is not in the context, strictly state that the information is not available in the current library.
"""

def ask_rag_question(query: str, index: List[Dict], client: OpenAI, history: List[Dict] = None) -> str:
    """Reusable function to ask a question to the RAG system."""
    
    # 1. Retrieve
    # Increase k to ensure we catch relevant sections if they are spread out
    top_chunks = retrieve(query, index, client, k=8)
    
    # 2. Build Context
    context_str = ""
    for score, chunk in top_chunks:
        context_str += f"\n--- Source: {chunk['source']} ---\n{chunk['text']}\n"
        
    user_message_content = f"Context:\n{context_str}\n\nQuestion: {query}"
    
    # 3. Prepare Messages
    if history is None:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    else:
        messages = list(history)
        # Ensure the first message is the system prompt if not already compatible, 
        # or just rely on the fact that we append the user/context message.
        # But if the history passed doesn't have our new system prompt, we might want to enforce it.
        # For simplicity, we assume the history structure is maintained by the caller or we act as subsequent turns.
        if not messages or messages[0]["role"] != "system":
             messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
        
    messages.append({"role": "user", "content": user_message_content})
    
    # 4. Call LLM
    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            stream=False 
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def chat_loop(client: OpenAI, index: List[Dict]):
    print("\n--- RAG Chat Ready (Type 'exit' to quit) ---")
    
    # Basic history for CLI execution
    history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
            
        if not user_input:
            continue
            
        print(f"(Searching...)", end="\r")
        
        # We pass a copy of history so we don't double append inside the function, 
        # but for CLI simple loop we actually want to maintain state.
        # The helper function is stateless regarding history updates to keep it pure.
        
        answer = ask_rag_question(user_input, index, client, history)
        print(f"AI: {answer}")
        
        # Update history for next turn (store pure query/answer to save context window)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": answer})

import argparse

def main():
    parser = argparse.ArgumentParser(description="RAG Chat with Books")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the index ignoring cache")
    args = parser.parse_args()

    load_environment()
    ensure_directories()
    
    if args.rebuild and os.path.exists(CACHE_FILE):
        print(f"Removing cache at {CACHE_FILE}...")
        os.remove(CACHE_FILE)
    
    client = OpenAI()
    
    print("Initializing RAG System...")
    index = load_index(client)
    
    if index:
        chat_loop(client, index)
    else:
        print("Failed to initialize index.")

if __name__ == "__main__":
    main()
