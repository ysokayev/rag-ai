
from interface import DemandCalculatorInterface
import sys

def main():
    print("="*60)
    print("⚡ AGENTIC DEMAND CALCULATOR ⚡")
    print("Type 'exit' or 'quit' to stop.")
    print("Example: calculator.demand[\"MyProject\", [\"default_lighting\"]]")
    print("="*60)
    
    bot = DemandCalculatorInterface()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            response = bot.process_input(user_input)
            print(f"\n{response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
