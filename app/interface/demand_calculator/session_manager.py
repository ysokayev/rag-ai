
import json
import os
import time
from typing import Dict, List, Optional
from main import ElectricalLoadSchedule  # Importing the logic class

STATE_DIR = "sessions"

class SessionManager:
    def __init__(self, base_dir: str = STATE_DIR):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _get_filepath(self, instance_name: str) -> str:
        # Sanitize filename
        safe_name = "".join([c for c in instance_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        return os.path.join(self.base_dir, f"{safe_name}.json")

    def create_session(self, instance_name: str, voltage: int = 480, phase: int = 3, sqft: float = 50000.0):
        """Creates a new empty session file."""
        filepath = self._get_filepath(instance_name)
        
        state = {
            "instance_name": instance_name,
            "created_at": time.time(),
            "updated_at": time.time(),
            "project_params": {
                "voltage": voltage,
                "phase": phase,
                "sqft": sqft
            },
            "rows": [],  # Store added loads here
            "status": "active"
        }
        
        self._save_state(filepath, state)
        return state

    def load_session(self, instance_name: str) -> Optional[Dict]:
        """Loads existing session state."""
        filepath = self._get_filepath(instance_name)
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)

    def update_session(self, instance_name: str, new_rows: List[Dict]):
        """Appends new rows (calculation results) to the session."""
        filepath = self._get_filepath(instance_name)
        state = self.load_session(instance_name)
        
        if not state:
             raise FileNotFoundError(f"Session '{instance_name}' not found.")
             
        state["rows"].extend(new_rows)
        state["updated_at"] = time.time()
        
        self._save_state(filepath, state)
        return state

    def _save_state(self, filepath: str, state: Dict):
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=4)

    def get_schedule_object(self, instance_name: str) -> Optional[ElectricalLoadSchedule]:
        """
        Re-hydrates the 'ElectricalLoadSchedule' class object 
        from the JSON state for export/printing.
        """
        state = self.load_session(instance_name)
        if not state:
            return None
            
        params = state.get("project_params", {})
        schedule = ElectricalLoadSchedule(
            system_voltage=params.get("voltage", 480),
            phase=params.get("phase", 3)
        )
        
        # Re-populate rows
        schedule.rows = state.get("rows", [])
        return schedule
