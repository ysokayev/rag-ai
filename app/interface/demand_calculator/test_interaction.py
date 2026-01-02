
from interface import DemandCalculatorInterface
import time

def test_flow():
    bot = DemandCalculatorInterface()

    print("--- Test 1: Start New Project with Elevators ---")
    # Simulate User typing the command
    cmd = 'calculator.demand["TestProject_B", ["elevators"]]'
    print(f"User: {cmd}")
    response = bot.process_input(cmd)
    print(f"Bot: {response}")
    
    # Check if it asked for elevator amps
    if "[elevators]" in response:
        # Simulate User answering the question
        ans1 = "[20, 20, 30]"
        print(f"User: {ans1}")
        response = bot.process_input(ans1)
        print(f"Bot: {response}") # Should ask Voltage next

        # Answer Voltage (Empty for default?)
        print(f"User: (Enter) [Default]")
        response = bot.process_input("") 
        print(f"Bot: {response}") # Should ask Phase

        # Answer Phase
        print(f"User: (Enter) [Default]")
        response = bot.process_input("")
        print(f"Bot: {response}") # Should ask SQFT

        # Answer SQFT
        print(f"User: (Enter) [Default]")
        response = bot.process_input("")
        print(f"Bot: {response}") # Should finish and say completed
    
    print("\n--- Test 2: Export ---")
    cmd_export = 'calculator.demand["TestProject_B"].rlf_export'
    print(f"User: {cmd_export}")
    response = bot.process_input(cmd_export)
    print(f"Bot: {response}")

if __name__ == "__main__":
    test_flow()
