
import sys
import ast
import traceback
from typing import List, Dict, Any

# Internal modules
import main  # The Calculation Engine
from session_manager import SessionManager
from command_parser import CommandParser
from interaction_map import FUNCTION_MAP

class DemandCalculatorInterface:
    def __init__(self):
        self.session_mgr = SessionManager()
        self.parser = CommandParser()
        
        # Runtime Memory (Not persisted in JSON, but keeps track of current conversation loop)
        self.active_instance = None
        self.pending_functions = []  # Queue of function keys ["hvac", "lighting"]
        self.current_function_key = None
        self.current_prompt_index = 0
        self.collected_args = {} # { "sqft": 5000, "voltage": 480 }

    def process_input(self, user_input: str) -> str:
        """
        Main entry point for the Chat System.
        """
        # 1. Check if we are in the middle of a Q&A loop
        if self.current_function_key:
            return self._handle_argument_input(user_input)

        # 2. If not, try to parse a new command
        status, instance_name, func_list, is_export = self.parser.parse_input(user_input)

        if status == "error":
            return self._get_help_message()

        # 3. Handle Export
        if is_export:
            schedule = self.session_mgr.get_schedule_object(instance_name)
            if not schedule:
                return f"Error: Instance '{instance_name}' not found."
            
            filename = f"Exporters/{instance_name}_LoadSchedule.csv"
            saved_path = schedule.export_to_csv(filename)
            if saved_path:
                return f"Successfully exported to: {saved_path}"
            return "Export failed."

        # 4. Handle Calculation Start
        if status == "calculate":
            self.active_instance = instance_name
            
            # Load or Create Session
            state = self.session_mgr.load_session(instance_name)
            if not state:
                # Default project params (could prompt for these too in V2)
                state = self.session_mgr.create_session(instance_name)
                msg_prefix = f"Created new project '{instance_name}'. "
            else:
                msg_prefix = f"Loaded project '{instance_name}'. "

            # Queue up functions
            if func_list:
                self.pending_functions = func_list
                # Trigger the first function immediately
                return msg_prefix + self._start_next_function()
            else:
                return msg_prefix + "No functions specified. Try `[\"default_lighting\"]`."

        return "Unknown state."

    def _start_next_function(self) -> str:
        """Pops the next function from queue and asks the first question."""
        if not self.pending_functions:
            self.current_function_key = None
            return "All tasks completed. You can export using `calculator.demand[Name].rlf_export`."
        
        # Pop next
        key = self.pending_functions.pop(0)
        
        if key not in FUNCTION_MAP:
             return f"Warning: Function '{key}' not found. Skipping...\n" + self._start_next_function()
             
        self.current_function_key = key
        self.current_prompt_index = 0
        self.collected_args = {}
        
        # Ask first question
        return self._get_current_question()

    def _get_current_question(self) -> str:
        """Constructs the prompt string for the current argument."""
        fn_def = FUNCTION_MAP[self.current_function_key]
        prompts = fn_def["prompts"]
        
        if self.current_prompt_index >= len(prompts):
            # No more questions -> Execute!
            return self._execute_current_function()
            
        current_prompt = prompts[self.current_prompt_index]
        
        # Check if default exists in project params
        if current_prompt.get("default_from_project"):
            # Auto-fill using session defaults (Simplification: just use 480/3/50000 for now or load from session)
            # In a real app, we check self.session_mgr.load_session(self.active_instance)
            # here we simply skip asking if we assume defaults, OR we ask with default value shown.
            # To be Agentic, let's ASK but show default.
            state = self.session_mgr.load_session(self.active_instance)
            params = state.get("project_params", {})
            
            arg_name = current_prompt["arg"] # e.g. "voltage" or "sqft"
            val = params.get(arg_name)
            
            return f"[{self.current_function_key}] {current_prompt['question']} (Default: {val})"
            
        return f"[{self.current_function_key}] {current_prompt['question']}"

    def _handle_argument_input(self, text: str) -> str:
        """Parses the user's answer to the specific question."""
        fn_def = FUNCTION_MAP[self.current_function_key]
        prompts = fn_def["prompts"]
        current_prompt = prompts[self.current_prompt_index]
        
        arg_name = current_prompt["arg"]
        arg_type = current_prompt["type"]
        
        # Parse Logic
        try:
            val = None
            text = text.strip()
            
            # Handle empty input -> Use Default logic
            if text == "":
                if current_prompt.get("default_from_project"):
                    state = self.session_mgr.load_session(self.active_instance)
                    params = state.get("project_params", {})
                    val = params.get(arg_name)
                elif "default" in current_prompt:
                    val = current_prompt["default"]
                else:
                    return f"Value required for '{arg_name}'. Please try again."
            else:
                # Type Casting
                if arg_type == "int":
                    val = int(text)
                elif arg_type == "float":
                    val = float(text)
                elif arg_type == "list_float":
                    # Parse "[1, 2]" or "1, 2"
                    clean = text.replace('[', '').replace(']', '')
                    val = [float(x) for x in clean.split(',') if x.strip()]
                elif arg_type == "list_dict":
                    # Use AST for complex dicts
                    val = ast.literal_eval(text)
                    if not isinstance(val, list): raise ValueError("Must be a list")
                elif arg_type == "bool":
                    # Simple 1/0, t/f, y/n parsing
                    lower_val = text.lower()
                    if lower_val in ['1', 'true', 't', 'yes', 'y']:
                        val = True
                    else:
                        val = False
                else:
                    val = text # str
            
            # Store it
            self.collected_args[arg_name] = val
            
            # Move to next
            self.current_prompt_index += 1
            return self._get_current_question()
            
        except Exception as e:
            return f"Invalid input for type '{arg_type}': {e}. Try again."

    def _execute_current_function(self) -> str:
        """Runs the calculation in main.py and saves result."""
        try:
            fn_def = FUNCTION_MAP[self.current_function_key]
            func_name = fn_def["function"]
            
            # Get function object from main module
            func_callable = getattr(main, func_name)
            
            # Execute
            result = func_callable(**self.collected_args)
            
            # Add to Session
            # We need a description. Use key or generated scenario name.
            desc = f"{self.current_function_key.title()}"
            if "Scenario Used" in result:
                desc += f" ({result['Scenario Used']})"
                
            # Create a "Row" format compatible with ElectricalLoadSchedule.add_load
            # But wait, add_load puts it into the class instance.
            # session_manager.update_session expects raw rows.
            
            # Let's use the helper in main to format the row first? 
            # Or manually map it here to ensure we save the COMPUTED row, not just the raw result.
            
            # Helper to create the row dict:
            row = {
                "Load Description": desc,
                "Connected Load (kVA)": result.get("Connected Load in kva", 0.0),
                "Connected VA/Square Feet": result.get("Connected Volt-Amps/SQFT", 0.0),
                "Demand Factor": result.get("demand factor", ""),
                "Demand Load (kVA)": result.get("Demand Load in kva", 0.0),
                "Demand VA/Square Feet": result.get("Demand Volt-Amps/SQFT", 0.0),
                "Demand FLA": result.get("demand FLA", 0.0)
            }
            
            self.session_mgr.update_session(self.active_instance, [row])
            
            output_msg = f"Added {desc}: {row['Demand Load (kVA)']} kVA Demand.\n"
            return output_msg + self._start_next_function()

        except Exception as e:
            traceback.print_exc()
            return f"Error executing {func_name}: {e}\n" + self._start_next_function()

    def is_active(self) -> bool:
        """Returns True if the interface is currently waiting for user input (mid-flow)."""
        return self.current_function_key is not None

    def _get_help_message(self) -> str:
        """Returns a condensed but comprehensive help guide."""
        return """
ERROR: Invalid Command Format.

--- AGENTIC DEMAND CALCULATOR HELP ---

COMMAND SYNTAX:
1. Start Calc: calculator.demand["ProjectName", ["func1", "func2"]]
2. Export CSV: calculator.demand["ProjectName"].rlf_export

AVAILABLE FUNCTIONS:

[General / Building Standard]
- default_lighting, lighting
- default_receptacles, receptacles
- default_kitchen, kitchen
- fire_alarm, default_fire_alarm
- it_systems, default_it_systems

[Mechanical & Plumbing]
- hvac, default_hvac
- pumps, default_pumps
- water_heaters
- electric_heating

[Specialized]
- elevators, default_elevators
- ev_charging, default_ev_charging
- data_center, default_data_center
- imaging, default_imaging
- signage, default_signage
- welders
- machine_shop
- multioutlet

INPUT EXAMPLES:
- Lists: `[10, 20, 30]`
- Dicts: `[{'name': 'Pump 1', 'amps': 10, 'voltage': 480}]`

EXAMPLE COMMAND:
User: calculator.demand["MyProject", ["hvac", "elevators", "default_lighting"]]
"""



