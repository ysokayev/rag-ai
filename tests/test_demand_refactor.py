
import sys
import os

# Add parent directory to path to import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from calculator_demandcalcs.main import calculate_lighting_metrics, calculate_receptacle_metrics
except ImportError:
    # Try direct import if running from inside calculator_demandcalcs
    sys.path.append(os.getcwd())
    from main import calculate_lighting_metrics, calculate_receptacle_metrics

def test_detailed_lighting():
    print("\n--- Testing Detailed Lighting ---")
    # 'exam room / class 1 imaging room': va_per_sq_ft: 1.42
    room_list = [
        {'name': 'Exam room / Class 1 imaging room', 'sqft': 100},
        {'name': 'Exam room / Class 1 imaging room', 'sqft': 100}
    ]
    # Total SQFT = 200
    # Total VA = 200 * 1.42 = 284 VA
    # Connected KVA = 0.284
    
    result = calculate_lighting_metrics(room_list)
    print(f"Result: {result}")
    
    expected_va = 284.0
    conn_kva = result['Connected Load in kva']
    
    # Check close enough (floating point)
    if abs(conn_kva - (expected_va/1000.0)) < 0.01:
        print("PASS: Connected Load matches expected.")
    else:
        print(f"FAIL: Expected {expected_va/1000.0} kVA, got {conn_kva}")

def test_detailed_receptacle_list():
    print("\n--- Testing Detailed Receptacle (List) ---")
    # 'exam room class 1 imaging room': va_per_sq_ft: 6.0
    room_list = [
        {'name': 'Exam room Class 1 imaging room', 'sqft': 100}
    ]
    # Total VA = 100 * 6.0 = 600 VA
    
    result = calculate_receptacle_metrics(room_list)
    print(f"Result: {result}")
    
    expected_va = 600.0
    conn_kva = result['Connected Load in kva']
    
    if abs(conn_kva - (expected_va/1000.0)) < 0.01:
        print("PASS: Connected Load matches expected.")
    else:
        print(f"FAIL: Expected {expected_va/1000.0} kVA, got {conn_kva}")

def test_detailed_receptacle_count():
    print("\n--- Testing Detailed Receptacle (Count) ---")
    count = 10
    # 10 * 90 VA = 900 VA = 0.9 kVA
    
    result = calculate_receptacle_metrics(count)
    print(f"Result: {result}")
    
    expected_kva = 0.9
    conn_kva = result['Connected Load in kva']
    
    if abs(conn_kva - expected_kva) < 0.01:
        print("PASS: Connected Load matches expected.")
    else:
        print(f"FAIL: Expected {expected_kva} kVA, got {conn_kva}")

if __name__ == "__main__":
    test_detailed_lighting()
    test_detailed_receptacle_list()
    test_detailed_receptacle_count()
