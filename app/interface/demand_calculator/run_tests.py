
from interface import DemandCalculatorInterface
import os

def run_test_scenario(scen_name, user_inputs):
    print(f"\n{'='*20} {scen_name} {'='*20}")
    bot = DemandCalculatorInterface()
    
    for inp in user_inputs:
        print(f"User: {inp}")
        response = bot.process_input(inp)
        print(f"Bot: {response}")
        
    return bot

def main():
    # --- Scenario 1: Complex Multi-Function ---
    inputs_1 = [
        # Start Command
        'calculator.demand["Project_Omega", ["elevators", "default_lighting", "fire_alarm"]]',
        # Elevators: Amps -> Voltage (Default) -> Phase (Default) -> SQFT (Default)
        "[30, 30, 45]",
        "", 
        "",
        "",
        # Lighting: Type -> SQFT (Default) -> Voltage (Default)
        "office",
        "",
        "",
        # Fire Alarm: Amps -> Voltage (Default) -> SQFT (Default)
        "[5.0, 2.5]",
        "",
        ""
    ]
    run_test_scenario("Scenario 1: Project_Omega (Creation)", inputs_1)

    # --- Scenario 2: Error Handling ---
    inputs_2 = [
        'calculator.demand["Project_Error_Check", ["elevators"]]',
        "bad_input_not_a_list", # Should trigger error message
        "[10, 10]", # Correct retry
        "", "", "" # Defaults
    ]
    run_test_scenario("Scenario 2: Error Handling", inputs_2)

    # --- Scenario 3: Persistence (Append) ---
    inputs_3 = [
        'calculator.demand["Project_Omega", ["default_receptacles"]]',
        # Receptacles: Type -> SQFT -> Voltage
        "office",
        "", 
        ""
    ]
    run_test_scenario("Scenario 3: Project_Omega (Append)", inputs_3)

    # --- Scenario 4: Export ---
    inputs_4 = [
        'calculator.demand["Project_Omega"].rlf_export'
    ]
    run_test_scenario("Scenario 4: Export Result", inputs_4)

if __name__ == "__main__":
    main()
