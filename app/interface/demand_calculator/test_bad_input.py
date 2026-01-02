
import sys
import os
sys.path.append(os.path.dirname(__file__))

from command_parser import CommandParser

def test_robust_parsing():
    parser = CommandParser()
    
    # Test Case 1: Typo in 'demand'
    cmd1 = 'calculator.demad["TypoProject", ["hvac"]]'
    status1, name1, funcs1, _ = parser.parse_input(cmd1)
    print(f"Test 1 (Typo): {status1} | {name1} | {funcs1}")
    
    # Test Case 2: Missing closing bracket
    cmd2 = 'calculator.demand["MissingBrace", ["elevators"'
    status2, name2, funcs2, _ = parser.parse_input(cmd2)
    print(f"Test 2 (Missing Brace): {status2} | {name2} | {funcs2}")
    
    # Test Case 3: Different keyword
    cmd3 = 'calculator.calc["ShortName", ["pumps"]]'
    status3, name3, funcs3, _ = parser.parse_input(cmd3)
    print(f"Test 3 (Alt Keyword): {status3} | {name3} | {funcs3}")

    if all(s == "calculate" for s in [status1, status2, status3]):
        print("\nSUCCESS: All malformed commands parsed correctly.")
    else:
        print("\nFAILURE: Some commands were not parsed.")

if __name__ == "__main__":
    test_robust_parsing()
