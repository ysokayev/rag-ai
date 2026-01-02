import sys
import os
import ast
import csv
import re
import math
from typing import List, Dict, Any, Optional

# Add calculator directory to path
CALC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'interface', 'demand_calculator')
if CALC_DIR not in sys.path:
    sys.path.append(CALC_DIR)

try:
    import main as demand_lib  # type: ignore
except ImportError:
    # Use relative import if running as package (fallback)
    try:
        from calculator_demandcalcs import main as demand_lib
    except ImportError:
        print("Error: Could not import calculator_demandcalcs.main")
        demand_lib = None

class DemandSession:
    def __init__(self, instance_name: str, functions_list: list, sqft: float):
        self.instance_name = instance_name
        self.functions_queue = functions_list
        self.sqft = float(sqft)
        
        # Default Project Voltage/Phase (Can be adjusted per load, but table header needs one)
        # We assume 480V 3Phase as default for the facility
        self.voltage = 480
        self.phase = 3
        
        self.schedule = demand_lib.ElectricalLoadSchedule(self.voltage, self.phase)
        self.current_function = None
        self.is_completed = False
        
        # Map generic names to library functions and their parsing/argument needs
        self.function_map = {
            "elevators": {
                "func": demand_lib.calculate_elevator_metrics,
                "prompt": "Enter elevator data:\n\nExample entries:\n\nelevator[[amps,amps,amp],voltage,phase] | elevator[[100, 40, 50], 480, 3]\nis equal to\n1. elevator 100A at 480V, 3 phase\n...",
                "arg_handler": self._standard_arg_handler
            },
            "elevator": {
                 "func": demand_lib.calculate_elevator_metrics,
                 "prompt": "Enter elevator data:\n\nExample entries:\n\nelevator[[amps,amps,amp],voltage,phase] | elevator[[100, 40, 50], 480, 3]",
                 "arg_handler": self._standard_arg_handler
            },
            "fire_alarm": {
                "func": demand_lib.calculate_fire_alarm_metrics,
                "prompt": "Enter fire_alarm data:\n\nExample entries:\n\nfire_alarm[[amps,amps,amp],voltage,phase] | fire_alarm[[10 , 12], 120, 1]",
                "arg_handler": self._standard_arg_handler
            },
            # We can map other functions similarly
        }
        
    def _standard_arg_handler(self, func, parsed_args):
        # parsed_args: expected to be ([list_of_amps], voltage, phase)
        # func signature: (amps_list, voltage, sqft, phase)
        
        # Check if parsed_args is just the list (if user omitted voltage/phase)
        # But instructions say [[...], vol, ph]
        
        amps_list = parsed_args[0]
        vol = parsed_args[1] if len(parsed_args) > 1 else self.voltage
        ph = parsed_args[2] if len(parsed_args) > 2 else self.phase
        
        # Call function
        # Note: All mapped functions (elevator, fire_alarm) take (amps, volt, sqft, phase)
        # EXCEPT some might vary. Let's check main.py signatures.
        # calculate_elevator_metrics(elevator_amps, voltage, sqft, phase=3)
        # calculate_fire_alarm_metrics(device_amps, voltage=120, sqft=0.0, phase=1)
        
        return func(amps_list, vol, self.sqft, ph)

    def start(self):
        return f"Your new workspace is created: `{self.instance_name}`\n{self.next_step()}"

    def next_step(self):
        if not self.functions_queue:
            self.is_completed = True
            return f"All calculations completed. Use `demand.{self.instance_name}.export()` to save."
        
        self.current_function = self.functions_queue.pop(0)
        config = self.function_map.get(self.current_function)
        
        if config:
            return config['prompt']
        else:
            # Fallback for unknown function in list
            return f"Warning: Function '{self.current_function}' not recognized. Skipping.\n{self.next_step()}"

    def process_input(self, user_input: str):
        if self.is_completed:
            return "Session complete. Use export."
            
        config = self.function_map.get(self.current_function)
        if not config:
             return self.next_step()
             
        # Parse logic
        # Expecting: prefix[[data], volt, phase]
        # or just [[data], volt, phase]
        
        try:
            # Find the start of the list
            idx = user_input.find('[')
            if idx == -1:
                return "Invalid format. Expected brackets [ ... ]. Try again."
            
            data_str = user_input[idx:]
            
            # Use ast.literal_eval to parse the python-like list/tuple structure
            parsed = ast.literal_eval(data_str)
            
            if not isinstance(parsed, (list, tuple)):
                return "Invalid format. Expected a list structure."
            
            # Execute calculation
            result = config['arg_handler'](config['func'], parsed)
            
            # Add to schedule
            # Use a nice name
            row_name = self.current_function.replace('_', ' ').title()
            self.schedule.add_load(row_name, result)
            
            # Proceed
            return self.next_step()
            
        except Exception as e:
            return f"Error parsing input: {e}. Please follow the example format."

    def export_csv(self):
        filename = f"{self.instance_name}_demand_load.csv"
        spare_percent = 25.0  # Default or could be user-configured later
        
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Headers
                writer.writerow(self.schedule.columns)
                
                # Rows
                for row in self.schedule.rows:
                     # Create list ordered by columns
                     row_data = [row.get(col, "") for col in self.schedule.columns]
                     writer.writerow(row_data)
                
                # --- Calculates Totals (Logic ported from main.py) ---
                total_conn_kva = sum(r["Connected Load (kVA)"] for r in self.schedule.rows)
                total_conn_dens = sum(r["Connected VA/Square Feet"] for r in self.schedule.rows)
                total_dem_kva = sum(r["Demand Load (kVA)"] for r in self.schedule.rows)
                total_dem_dens = sum(r["Demand VA/Square Feet"] for r in self.schedule.rows)
                
                # Total FLA
                sqrt_factor = 1.73205 if self.phase == 3 else 1.0
                total_dem_fla = (total_dem_kva * 1000.0) / (self.voltage * sqrt_factor)

                # Spare Capacity
                spare_mult = spare_percent / 100.0
                spare_kva = total_dem_kva * spare_mult
                spare_fla = total_dem_fla * spare_mult
                
                # Grand Totals
                grand_total_kva = total_dem_kva + spare_kva
                grand_total_fla = total_dem_fla + spare_fla
                
                writer.writerow([])
                
                # TOTALS ROW
                writer.writerow([
                    "TOTALS", 
                    round(total_conn_kva, 2), 
                    round(total_conn_dens, 2), 
                    "", 
                    round(total_dem_kva, 2), 
                    round(total_dem_dens, 2), 
                    round(total_dem_fla, 2)
                ])

                # FUTURE GROWTH ROW
                writer.writerow([
                    f"FUTURE GROWTH ({spare_percent}%)", 
                    0.0, 
                    0.0, 
                    "", 
                    round(spare_kva, 2), 
                    0.0, 
                    round(spare_fla, 2)
                ])
                
                # GRAND TOTAL ROW
                writer.writerow([
                    "GRAND TOTAL", 
                    round(total_conn_kva, 2), 
                    round(total_conn_dens, 2), 
                    "", 
                    round(grand_total_kva, 2), 
                    round(total_dem_dens, 2), 
                    round(grand_total_fla, 2)
                ])
                
            # --- 2. HTML Export ---
            html_filename = f"{self.instance_name}_demand_load.html"
            with open(html_filename, 'w') as f:
                html_content = f"""
                <html>
                <head>
                    <title>Electrical Load Schedule - {self.instance_name}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f6f9; }}
                        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                        h1 {{ text-align: center; color: #333; }}
                        .summary {{ display: flex; justify-content: space-around; margin-bottom: 20px; padding: 10px; background: #e9ecef; border-radius: 5px; }}
                        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                        th, td {{ padding: 10px; border: 1px solid #dee2e6; text-align: right; }}
                        th {{ background-color: #0e1117; color: white; text-align: center; }}
                        td:first-child {{ text-align: left; font-weight: bold; }}
                        .totals-row {{ background-color: #f8f9fa; font-weight: bold; }}
                        .grand-total {{ background-color: #007bff; color: white; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Electrical Load Schedule</h1>
                        <div class="summary">
                            <div><b>Project:</b> {self.instance_name}</div>
                            <div><b>System:</b> {self.voltage}V {self.phase}-Phase</div>
                            <div><b>Area:</b> {self.sqft:,.0f} SQFT</div>
                            <div><b>Spare:</b> {spare_percent}%</div>
                        </div>

                        <table>
                            <thead>
                                <tr>
                                    {''.join(f'<th>{col}</th>' for col in self.schedule.columns)}
                                </tr>
                            </thead>
                            <tbody>
                """
                
                # Rows
                for row in self.schedule.rows:
                    html_content += "<tr>"
                    for col in self.schedule.columns:
                        html_content += f"<td>{row.get(col, '')}</td>"
                    html_content += "</tr>"
                
                # Footer Rows (Totals)
                html_content += f"""
                            </tbody>
                            <tfoot>
                                <tr class="totals-row">
                                    <td>TOTALS</td>
                                    <td>{total_conn_kva:.2f}</td>
                                    <td>{total_conn_dens:.2f}</td>
                                    <td></td>
                                    <td>{total_dem_kva:.2f}</td>
                                    <td>{total_dem_dens:.2f}</td>
                                    <td>{total_dem_fla:.2f}</td>
                                </tr>
                                <tr class="totals-row">
                                    <td>FUTURE GROWTH ({spare_percent}%)</td>
                                    <td>0.00</td>
                                    <td>0.00</td>
                                    <td></td>
                                    <td>{spare_kva:.2f}</td>
                                    <td>0.00</td>
                                    <td>{spare_fla:.2f}</td>
                                </tr>
                                <tr class="grand-total">
                                    <td style="text-align:left">GRAND TOTAL</td>
                                    <td>{total_conn_kva:.2f}</td>
                                    <td>{total_conn_dens:.2f}</td>
                                    <td></td>
                                    <td>{grand_total_kva:.2f}</td>
                                    <td>{total_dem_dens:.2f}</td>
                                    <td>{grand_total_fla:.2f}</td>
                                </tr>
                            </tfoot>
                        </table>
                        <div style="font-size: 0.8em; color: #666; text-align: center;">Generated by RAG Demand Calculator</div>
                    </div>
                </body>
                </html>
                """
                f.write(html_content)
                     
            return f"Successfully exported to {filename} and {html_filename}"
        except Exception as e:
            return f"Error exporting file: {e}"

