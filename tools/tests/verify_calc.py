import sys
import os
import time

# Add execution dir to path
# Add root dir to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.rag_core.rag_agent import RAGAgent

def verify_calculation():
    print("--- Starting Verification: RAG V3 Calculation Flow ---")
    
    # 1. Initialize Agent
    print("Initializing Agent (Code Domain)...")
    agent = RAGAgent(collection_name="rag_code_only")
    
    if not agent.collection:
        print("ERROR: Collection not found. Ingestion might still be running or failed.")
        return

    # 2. Test Router & Calculation
    query = "Calculate the demand for 50 generic receptacles at 180 VA."
    print(f"\nTest Query: '{query}'")
    
    start = time.time()
    response = agent.query(query)
    duration = time.time() - start
    
    print("\n--- Agent Response ---")
    print(response)
    print("----------------------")
    
    # 3. Validation Checks
    checks = {
        "Two-Channel Output": "Normative Answer" in response and "Guidance" in response,
        "Tool Usage (Result)": "9000" in response or "9,000" in response, # 50 * 180 = 9000
        "Citation Present": "Source:" in response or "Article" in response or "220" in response
    }
    
    print("\n--- Validation Results ---")
    all_pass = True
    for name, result in checks.items():
        status = "PASS" if result else "FAIL"
        print(f"[{status}] {name}")
        if not result:
            all_pass = False
            
    if all_pass:
        print("\nSUCCESS: V3 Dynamic Calculation Verified.")
    else:
        print("\nWARNING: Verification Checks Failed.")

if __name__ == "__main__":
    verify_calculation()
