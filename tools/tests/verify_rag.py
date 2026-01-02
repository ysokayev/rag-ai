
import sys
import os

# Add execution dir to path
# Add root dir to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.rag_core.rag_agent import RAGAgent

def run_verification():
    print("--- Starting RAG Verification ---")
    agent = RAGAgent(collection_name="rag_code_only")
    if not agent.collection:
        print("FAILED: ChromaDB collection not found.")
        return

    test_queries = [
        "What are the grounding requirements for patient care vicinities?",
        "Define 'Ampacity' according to the code.",
        "What is the maximum voltage for class 1 circuits?",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        response = agent.query(q)
        print(f"Response Preview: {response[:200]}...")
        if "Information not found" in response:
            print("  [WARN] Answer might be missing.")
        else:
            print("  [PASS] Answer generated.")

if __name__ == "__main__":
    run_verification()
