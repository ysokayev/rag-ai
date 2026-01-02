
import unittest
import os
import sys
import shutil

# Ensure imports work (Add root)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.rag_core.demand_session import DemandSession

class TestDemandSession(unittest.TestCase):
    def test_flow(self):
        print("\n--- Testing DemandSession Flow ---")
        
        # 1. Start Session
        session = DemandSession("test_inst", ["elevators", "fire_alarm"], 50000)
        start_msg = session.start()
        print(f"Start Msg: {start_msg}")
        
        self.assertIn("Your new workspace is created: `test_inst`", start_msg)
        self.assertIn("Enter elevator data", start_msg)
        
        # 2. Input Elevator Data
        # User input: elevator[[100, 40, 50], 480, 3]
        resp1 = session.process_input("elevator[[100, 40, 50], 480, 3]")
        print(f"Resp 1: {resp1}")
        
        self.assertIn("Enter fire_alarm data", resp1)
        
        # 3. Input Fire Alarm Data
        # User input: fire_alarm[[10, 12], 120, 1]
        resp2 = session.process_input("fire_alarm[[10, 12], 120, 1]")
        print(f"Resp 2: {resp2}")
        
        self.assertIn("All calculations completed", resp2)
        self.assertTrue(session.is_completed)
        
        # 4. Export
        export_msg = session.export_csv()
        print(f"Export Msg: {export_msg}")
        self.assertIn("Successfully exported", export_msg)
        
        # 5. Verify File
        filename = "test_inst_demand_load.csv"
        self.assertTrue(os.path.exists(filename))
        
        with open(filename, 'r') as f:
            content = f.read()
            print("\nCSV Content:")
            print(content)
            self.assertIn("Elevators", content)
            self.assertIn("Fire Alarm", content)
            
        # Cleanup
        os.remove(filename)

if __name__ == '__main__':
    unittest.main()
