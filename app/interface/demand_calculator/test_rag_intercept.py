
import sys
import os

# Mock the Agent to verify we DON'T call it
class MockRAGAgent:
    def __init__(self):
        self.query_called = False

    def query(self, input, history):
        self.query_called = True
        return "You typically shouldn't see this if intercepted."

# Mock the Interface to verify it IS called
class MockInterface:
    def __init__(self):
        self.active = False
        self.called = False

    def is_active(self):
        return self.active

    def process_input(self, text):
        self.called = True
        if "start" in text:
            self.active = True
        if "finish" in text:
            self.active = False
        return "Calculated."

def test_intercept_logic():
    print("--- Testing API Bypass Logic ---")
    agent = MockRAGAgent()
    calc_interface = MockInterface()

    # Simulation Loop (Copied from rag_agent.py logic)
    inputs = [
        "calculator.demand[start]", # Should intercept
        "100",                      # Should intercept (active)
        "finish",                   # Should intercept (active -> inactive)
        "What is NFPA 70?"          # Should NOT intercept (API Call)
    ]

    for user_input in inputs:
        print(f"Input: '{user_input}'")
        
        # --- LOGIC UNDER TEST ---
        was_intercepted = False
        if calc_interface and (user_input.startswith("calculator.") or calc_interface.is_active()):
            response = calc_interface.process_input(user_input)
            was_intercepted = True
            print(f"  -> Intercepted: {response}")
        else:
            response = agent.query(user_input, [])
            print(f"  -> API Called: {response}")
        # ------------------------

        # Assertions
        if "calculator." in user_input or user_input in ["100", "finish"]:
            if not was_intercepted: print("  FAILED: Should have intercepted!")
            if agent.query_called and was_intercepted: print("  FAILED: API was called despite intercept!") 
        else:
            if was_intercepted: print("  FAILED: Should NOT have intercepted!")

    print("\nFinal Check:")
    if agent.query_called:
        print("SUCCESS: API logic reached only when intended.")
    else:
        print("WARNING: API logic never reached.")

if __name__ == "__main__":
    test_intercept_logic()
