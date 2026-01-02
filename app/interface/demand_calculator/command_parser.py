
import re
import ast
from typing import Tuple, List, Optional

class CommandParser:
    """
    Parses strings in the format: 
    1. calculator.demand["InstanceName", ["func1", "func2"]]
    2. calculator.demand["InstanceName", "func1"]  (Single string allowed)
    3. calculator.demand["InstanceName"].rlf_export
    """

    def parse_input(self, text: str) -> Tuple[str, Optional[str], Optional[List[str]], bool]:
        """
        Returns:
            (status, instance_name, function_list, is_export)
            status: "success", "error", "export"
        """
        text = text.strip()
        
        # --- 0. Pre-processing for Robustness ---
        # Fix missing closing bracket
        if text.count('[') > text.count(']'):
            text += ']' * (text.count('[') - text.count(']'))

        # --- Pattern 1: Export Command ---
        # calculator.demand["Name"].rlf_export
        # Allow typos in 'demand' -> calculator.\w+
        export_pattern = r'calculator\.\w+\[[\'"]?([a-zA-Z0-9_\-\s]+)[\'"]?\]\.rlf_export'
        export_match = re.search(export_pattern, text)
        if export_match:
            instance_name = export_match.group(1)
            return "export", instance_name, None, True

        # --- Pattern 2: Start/Function Command ---
        # calculator.demad["Name", ... -> Matches calculator.ANYTHING[...]
        base_pattern = r'calculator\.\w+\[(.*)\]'
        match = re.search(base_pattern, text)
        
        if match:
            inner_content = match.group(1).strip()
            # This string should look like: "Name", ["list"]  OR  "Name", "single_func"
            
            # Since ast.literal_eval expects a tuple/list syntax if there are commas,
            # we might need to wrap it if it's raw args.
            
            try:
                # Try parsing as a python tuple: ("Name", ["a", "b"])
                # We artificially wrap in parens to ensure it parses as a tuple
                if not inner_content.startswith("("):
                    eval_str = f"({inner_content})"
                else:
                    eval_str = inner_content
                    
                parsed = ast.literal_eval(eval_str)
                
                # Unpack
                if isinstance(parsed, tuple) and len(parsed) >= 1:
                    instance_name = parsed[0]
                    
                    func_list = []
                    if len(parsed) > 1:
                        raw_list = parsed[1]
                        if isinstance(raw_list, list):
                            func_list = raw_list
                        elif isinstance(raw_list, str):
                            func_list = [raw_list]
                            
                    return "calculate", instance_name, func_list, False
                
                # If just ["Name"] -> parsed is just "Name"
                elif isinstance(parsed, str): 
                     return "calculate", parsed, [], False

            except Exception as e:
                # Fallback for simple manual parsing if AST fails
                # Split by first comma
                parts = inner_content.split(',', 1)
                instance_name = parts[0].strip().replace('"', '').replace("'", "")
                
                func_list = []
                if len(parts) > 1:
                    raw_remainder = parts[1].strip()
                    # Basic cleanup to extract list items
                    clean_remainder = raw_remainder.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
                    func_list = [x.strip() for x in clean_remainder.split(',') if x.strip()]
                    
                return "calculate", instance_name, func_list, False

        return "error", None, None, False
