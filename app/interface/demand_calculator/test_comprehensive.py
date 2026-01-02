
import sys
import os
import time

# Ensure imports work
sys.path.append(os.path.dirname(__file__))
from interface import DemandCalculatorInterface

def run_comprehensive_test():
    print("--- STARTING COMPREHENSIVE TEST ---")
    
    interface = DemandCalculatorInterface()
    
    # 1. Start a Massive Project with ALL new types
    cmd = 'calculator.demand["Mega_Test_Project", ["default_ev_charging", "data_center", "welders", "default_kitchen", "signage"]]'
    print(f"USER: {cmd}")
    resp = interface.process_input(cmd)
    print(f"SYS: {resp}")
    
    # --- INTERACTIONS ---
    
    # 1. Default EV Charging
    # Q1: Num L2 Chargers?
    # Q2: Num Fast Chargers?
    # Q3: Voltage (Default 208)?
    inputs_ev = ["10", "2", ""] 
    for inp in inputs_ev:
        print(f"USER: {inp}")
        resp = interface.process_input(inp)
        print(f"SYS: {resp}")

    # 2. Data Center
    # Q1: Equipment List
    # Q2: Voltage (Default 480)?
    # Q3: SQFT (Default 5000)?
    dc_list = "[{'name': 'UPS-A', 'amps': 200, 'voltage': 480, 'phase': 3}]"
    inputs_dc = [dc_list, "", ""]
    for inp in inputs_dc:
        print(f"USER: {inp}")
        resp = interface.process_input(inp)
        print(f"SYS: {resp}")

    # 3. Welders
    # Q1: Welder List
    # Q2: Voltage (Default 480)?
    # Q3: SQFT?
    weld_list = "[{'name': 'MIG-1', 'amps': 50, 'duty_cycle': 60}]"
    inputs_weld = [weld_list, "", ""]
    for inp in inputs_weld:
        print(f"USER: {inp}")
        resp = interface.process_input(inp)
        print(f"SYS: {resp}")
        
    # 4. Default Kitchen
    # Q1: SQFT
    # Q2: Voltage?
    # Q3: Phase?
    inputs_kitch = ["1500", "208", "3"]
    for inp in inputs_kitch:
        print(f"USER: {inp}")
        resp = interface.process_input(inp)
        print(f"SYS: {resp}")

    # 5. Signage
    # Q1: Specific Signs? (List Dict)
    # Q2: Required Outlets?
    # Q3: Voltage?
    # Q4: SQFT?
    # Q5: Phase?
    sign_list = "[{'name': 'Pylon', 'amps': 15}]"
    inputs_sign = [sign_list, "1", "", "", ""]
    for inp in inputs_sign:
        print(f"USER: {inp}")
        resp = interface.process_input(inp)
        print(f"SYS: {resp}")

    # EXPORT
    cmd_exp = 'calculator.demand["Mega_Test_Project"].rlf_export'
    print(f"USER: {cmd_exp}")
    resp = interface.process_input(cmd_exp)
    print(f"SYS: {resp}")
    
    if "Successfully exported" in resp:
        print("\n--- TEST PASSED: All functions processed and exported. ---")
    else:
        print("\n--- TEST FAILED: Export did not succeed. ---")

if __name__ == "__main__":
    run_comprehensive_test()
