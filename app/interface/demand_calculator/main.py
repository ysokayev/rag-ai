
import math
import csv
from lighting_hospital_data import get_lighting_data
from receptacle_hospital_data import get_room_data
from typing import List, Dict, Union, Optional

area = 0
#area = input("Enter the area of the building in square feet:")
#elevator = input("Enter the number of elevators:")

columns = [
    "Load Description", 
    "Connected Load (kVA)", 
    "Connected VA/Square Feet", 
    "Demand Factor", 
    "Demand Load (kVA)", 
    "Demand VA/Square Feet", 
    "Demand FLA"
]

class ElectricalLoadSchedule:
    def __init__(self, system_voltage: int, phase: int = 3):
        self.voltage = system_voltage
        self.phase = phase
        self.rows = []
        
        # Exact columns requested
        self.columns = [
            "Load Description", 
            "Connected Load (kVA)", 
            "Connected VA/Square Feet", 
            "Demand Factor", 
            "Demand Load (kVA)", 
            "Demand VA/Square Feet", 
            "Demand FLA"
        ]

    def add_load(self, description: str, calc_result: Dict):
        """
        Takes the output dictionary from a calculation function and 
        maps it to the schedule columns.
        """
        row = {
            "Load Description": description,
            "Connected Load (kVA)": calc_result.get("Connected Load in kva", 0.0),
            "Connected VA/Square Feet": calc_result.get("Connected Volt-Amps/SQFT", 0.0),
            "Demand Factor": calc_result.get("demand factor", ""),
            "Demand Load (kVA)": calc_result.get("Demand Load in kva", 0.0),
            "Demand VA/Square Feet": calc_result.get("Demand Volt-Amps/SQFT", 0.0),
            "Demand FLA": calc_result.get("demand FLA", 0.0)
        }
        self.rows.append(row)

    def export_to_csv(self, filename: str) -> str:
        """Exports the current rows to a CSV file."""
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(self.rows)
            
        return os.path.abspath(filename)

    def generate_table(self, spare_percent: float = 20.0):
        """
        Calculates totals, applies spare capacity, and prints the table.
        Args:
            spare_percent (float): The percentage of spare capacity (e.g., 15, 20, 25).
        """
        # 1. Calculate Subtotals
        total_conn_kva = sum(r["Connected Load (kVA)"] for r in self.rows)
        total_conn_dens = sum(r["Connected VA/Square Feet"] for r in self.rows)
        total_dem_kva = sum(r["Demand Load (kVA)"] for r in self.rows)
        total_dem_dens = sum(r["Demand VA/Square Feet"] for r in self.rows)
        
        # Calculate Total FLA based on Total Demand KVA (More accurate than summing amps)
        sqrt_factor = 1.73205 if self.phase == 3 else 1.0
        total_dem_fla = (total_dem_kva * 1000.0) / (self.voltage * sqrt_factor)

        # 2. Calculate Spare Capacity Rows
        spare_mult = spare_percent / 100.0
        spare_kva = total_dem_kva * spare_mult
        spare_fla = total_dem_fla * spare_mult
        
        # 3. Calculate Grand Totals
        grand_total_kva = total_dem_kva + spare_kva
        grand_total_fla = total_dem_fla + spare_fla

        # --- PRINTING THE TABLE ---
        print(f"\n{'='*115}")
        print(f"ELECTRICAL LOAD SCHEDULE ({self.voltage}V {self.phase}-Phase)")
        print(f"{'='*115}")
        
        # Header Formatting
        header_fmt = "{:<25} | {:>20} | {:>15} | {:>20} | {:>18} | {:>15} | {:>10}"
        print(header_fmt.format(*self.columns))
        print(f"{'-'*115}")

        # Row Formatting
        row_fmt = "{:<25} | {:>20.2f} | {:>15.2f} | {:>20} | {:>18.2f} | {:>15.2f} | {:>10.1f}"

        for row in self.rows:
            # Handle mixed types (Demand factor can be string or float)
            df_val = row["Demand Factor"]
            if isinstance(df_val, float):
                df_str = f"{df_val*100:.0f}%" if df_val <= 1.0 else f"{df_val:.2f}"
            else:
                df_str = str(df_val)

            print(row_fmt.format(
                row["Load Description"],
                row["Connected Load (kVA)"],
                row["Connected VA/Square Feet"],
                df_str,
                row["Demand Load (kVA)"],
                row["Demand VA/Square Feet"],
                row["Demand FLA"]
            ))

        print(f"{'-'*115}")

        # --- SPECIAL ROWS ---
        
        # 1. TOTALS
        print(row_fmt.format(
            "TOTALS", total_conn_kva, total_conn_dens, "", total_dem_kva, total_dem_dens, total_dem_fla
        ))

        # 2. SPARE CAPACITY
        print(row_fmt.format(
            f"FUTURE GROWTH ({spare_percent}%)", 0.0, 0.0, "", spare_kva, 0.0, spare_fla
        ))
        
        print(f"{'='*115}")

        # 3. GRAND TOTAL
        print(row_fmt.format(
            "GRAND TOTAL", total_conn_kva, total_conn_dens, "", grand_total_kva, total_dem_dens, grand_total_fla
        ))
        print(f"{'='*115}\n")

def calculate_elevator_metrics(
    elevator_amps: List[float], 
    voltage: int, 
    sqft: float, 
    phase: int = 3
) -> Dict[str, float]:
    """
    Calculates NEC Elevator metrics including Connected Load, Demand Factors, 
    and Load Densities (VA/SQFT).
    
    Args:
        elevator_amps (List[float]): List of FLA for each elevator.
        voltage (int): System voltage.
        sqft (float): Total building square footage.
        phase (int): System phase (1 or 3). Default is 3.
        
    Returns:
        Dict: Dictionary containing specific keys for KVA, VA/SQFT, and FLA.
    """
    
    count = len(elevator_amps)
    
    # Avoid division by zero
    if count == 0 or sqft <= 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": 0.0,
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- 1. Setup Constants ---
    # NEC Table 620.14
    demand_factor_map = {
        1: 1.00, 2: 0.95, 3: 0.90, 4: 0.85, 5: 0.82,
        6: 0.79, 7: 0.77, 8: 0.75, 9: 0.73
    }
    # If 10 or more, use 0.72
    demand_factor = demand_factor_map.get(count, 0.72)
    
    # 3-Phase vs Single Phase factor
    sqrt_factor = 1.73205 if phase == 3 else 1.0

    # --- 2. Connected Load Calculations ---
    # Simple sum of all nameplates (Physical installed capacity)
    sum_flas = sum(elevator_amps)
    
    # Connected KVA
    connected_kva = (sum_flas * voltage * sqrt_factor) / 1000.0
    
    # Connected VA/SQFT (Use KVA * 1000 / SQFT)
    connected_va_sqft = (connected_kva * 1000.0) / sqft

    # --- 3. Demand Load Calculations ---
    # NEC 620.13 Base = (1.25 * Largest) + (Sum of others)
    largest_motor = max(elevator_amps)
    nec_base_amps = sum_flas + (0.25 * largest_motor)
    
    # Apply Demand Factor (NEC 620.14)
    demand_fla = nec_base_amps * demand_factor
    
    # Demand KVA
    demand_kva = (demand_fla * voltage * sqrt_factor) / 1000.0
    
    # Demand VA/SQFT
    demand_va_sqft = (demand_kva * 1000.0) / sqft

    # --- 4. Return Ordered Dictionary ---
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_va_sqft, 2),
        "demand factor": demand_factor,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_va_sqft, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_fire_alarm_metrics(
    device_amps: List[float], 
    voltage: int = 120, 
    sqft: float = 0.0, 
    phase: int = 1
) -> Dict[str, float]:
    """
    Calculates NEC Fire Alarm metrics.
    
    NOTE: The 1.25 continuous load multiplier is EXCLUDED from this function 
    per request. The Demand Factor is set to 1.0 (100%).
    
    Args:
        device_amps (List[float]): List of amps for panels/devices.
        voltage (int): System voltage. Default 120V.
        sqft (float): Total building square footage.
        phase (int): System phase (1 or 3). Default is 1.
        
    Returns:
        Dict: Dictionary containing specific keys for KVA, VA/SQFT, and FLA.
    """
    
    count = len(device_amps)
    
    # Avoid division by zero
    if count == 0 or sqft <= 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": 0.0,
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- 1. Setup Constants ---
    # Phase Factor: 1.0 for Single Phase, 1.732 for 3-Phase
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    
    # NEC Factor for Fire Alarm:
    # No diversity allowed, so factor is 1.0.
    demand_factor = 1.0
    
    # --- 2. Connected Load Calculations ---
    # Simple sum of all device currents
    connected_amps = sum(device_amps)
    
    # Connected KVA
    connected_kva = (connected_amps * voltage * sqrt_factor) / 1000.0
    
    # Connected VA/SQFT
    connected_va_sqft = (connected_kva * 1000.0) / sqft

    # --- 3. Demand Load Calculations ---
    # Factor is 1.0, and 1.25 multiplier is excluded for now.
    demand_fla = connected_amps * demand_factor
    
    # Demand KVA
    demand_kva = (demand_fla * voltage * sqrt_factor) / 1000.0
    
    # Demand VA/SQFT
    demand_va_sqft = (demand_kva * 1000.0) / sqft

    # --- 4. Return Ordered Dictionary ---
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_va_sqft, 2),
        "demand factor": demand_factor,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_va_sqft, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_it_system_metrics(
    device_amps: List[float], 
    voltage: int = 120, 
    sqft: float = 0.0, 
    phase: int = 1
) -> Dict[str, float]:
    """
    Calculates load metrics for IT / Data Systems.
    
    NOTE: Similar to Fire Alarm, IT loads are typically calculated at 100%.
    The 1.25 continuous load multiplier is EXCLUDED from this function per request.
    
    Args:
        device_amps (List[float]): List of amps for server racks, UPS inputs, or IDF/MDF panels.
        voltage (int): System voltage. Default 120V (Commonly 120V or 208V).
        sqft (float): Total building square footage.
        phase (int): System phase (1 or 3). Default is 1.
        
    Returns:
        Dict: Dictionary containing specific keys for KVA, VA/SQFT, and FLA.
    """
    
    count = len(device_amps)
    
    # Avoid division by zero
    if count == 0 or sqft <= 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": 0.0,
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- 1. Setup Constants ---
    # Phase Factor: 1.0 for Single Phase, 1.732 for 3-Phase
    # Note: Many IT racks run on 208V Single Phase (2-pole). 
    # If using 208V 1-phase, ensure 'voltage' is 208 and 'phase' is 1.
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    
    # IT System Demand Factor:
    # Generally calculated at 100% unless specific diversity is known.
    demand_factor = 1.0
    
    # --- 2. Connected Load Calculations ---
    # Simple sum of all equipment currents
    connected_amps = sum(device_amps)
    
    # Connected KVA
    connected_kva = (connected_amps * voltage * sqrt_factor) / 1000.0
    
    # Connected VA/SQFT
    connected_va_sqft = (connected_kva * 1000.0) / sqft

    # --- 3. Demand Load Calculations ---
    # Factor is 1.0, and 1.25 multiplier is excluded.
    demand_fla = connected_amps * demand_factor
    
    # Demand KVA
    demand_kva = (demand_fla * voltage * sqrt_factor) / 1000.0
    
    # Demand VA/SQFT
    demand_va_sqft = (demand_kva * 1000.0) / sqft

    # --- 4. Return Ordered Dictionary ---
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_va_sqft, 2),
        "demand factor": demand_factor,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_va_sqft, 2),
        "demand FLA": round(demand_fla, 2)
    }

# Define a simple structure for an HVAC load
# You can use a Python dictionary for each piece of equipment.
# Structure:
# {
#   "name": "RTU-1",
#   "amps": 30.5,
#   "voltage": 480,
#   "phase": 3,
#   "type": "cooling",  # or "heating" or "continuous" (e.g. toilet exhaust fan)
#   "is_motor": True    # True if it has a compressor/fan (gets 125% rule)
# }

def calculate_hvac_feeder_demand(
    equipment_list: List[Dict], 
    system_voltage: int,
    sqft: float
) -> Dict[str, Union[float, str]]:
    """
    Calculates HVAC Feeder Demand per NEC 440.33, 430.24, and 220.60.
    
    Handles:
      - 125% Largest Motor Rule (applied to the largest in the ACTIVE group).
      - Noncoincident Loads (Compares Heating vs Cooling totals).
      - Mixed 1-phase/3-phase loads (Sums via KVA).
    
    Args:
        equipment_list (List[Dict]): List of equipment dicts (structure above).
        system_voltage (int): The main feeder voltage (e.g., 480 or 208).
        sqft (float): Building SQFT for density calculation.
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    if not equipment_list:
         return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": 0.0,
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0,
            "Scenario Used": "None"
        }

    # --- Helper: Calculate KVA for a single item ---
    def get_kva(item):
        # 3-Phase: Amps * Volts * 1.732 / 1000
        # 1-Phase: Amps * Volts * 1.0 / 1000
        factor = 1.73205 if item['phase'] == 3 else 1.0
        return (item['amps'] * item['voltage'] * factor) / 1000.0

    # --- 1. Separate Loads into Groups ---
    heating_items = []
    cooling_items = []
    always_on_items = [] # e.g., Toilet Exhaust Fans, VAV boxes
    
    for item in equipment_list:
        tag = item.get('type', 'continuous').lower()
        if 'cool' in tag or 'ac' in tag:
            cooling_items.append(item)
        elif 'heat' in tag:
            heating_items.append(item)
        else:
            always_on_items.append(item)

    # --- 2. Define Calculation Logic (NEC 430.24 / 440.33) ---
    def calculate_group_load(group_items):
        """Returns total KVA for a group, accounting for 125% largest motor."""
        if not group_items:
            return 0.0
            
        total_kva = 0.0
        largest_motor_kva_add = 0.0
        
        for item in group_items:
            # Base Load
            k = get_kva(item)
            total_kva += k
            
            # Check for largest motor adder (25% extra of the largest motor)
            if item.get('is_motor', True):
                # We need the 25% slice in KVA
                extra_slice = k * 0.25
                if extra_slice > largest_motor_kva_add:
                    largest_motor_kva_add = extra_slice
        
        return total_kva + largest_motor_kva_add

    # --- 3. Calculate Scenarios ---
    
    # Base load (Fans, Pumps that run year-round)
    base_kva = calculate_group_load(always_on_items)
    
    # Scenario A: Cooling On + Base
    # Note: We technically need to find the single largest motor across 
    # (Cooling + Base) combined to apply the 125% rule correctly once.
    # For simplicity here, we assume the largest motor is likely a Chiller/RTU (Cooling).
    cooling_only_kva = calculate_group_load(cooling_items)
    scenario_cooling = base_kva + cooling_only_kva
    
    # Scenario B: Heating On + Base
    heating_only_kva = calculate_group_load(heating_items)
    scenario_heating = base_kva + heating_only_kva

    # --- 4. Apply NEC 220.60 (Noncoincident) ---
    # Pick the larger scenario
    if scenario_cooling >= scenario_heating:
        final_demand_kva = scenario_cooling
        scenario_name = "Cooling (Summer)"
    else:
        final_demand_kva = scenario_heating
        scenario_name = "Heating (Winter)"

    # --- 5. Calculate Connected Load (No coincident reduction) ---
    # This is just everything added together (for Transformer sizing mostly)
    connected_kva = sum(get_kva(i) for i in equipment_list)

    # --- 6. Final Outputs ---
    
    # Demand Amps (FLA)
    # Convert back to Amps using the Main Feeder Voltage (usually 3-phase)
    # I = KVA * 1000 / (Volts * 1.732)
    demand_fla = (final_demand_kva * 1000.0) / (system_voltage * 1.73205)
    
    # Densities
    connected_density = (connected_kva * 1000) / sqft if sqft > 0 else 0
    demand_density = (final_demand_kva * 1000) / sqft if sqft > 0 else 0
    
    # Demand Factor (Effective)
    # For HVAC, this isn't a fixed table value, but a calculated ratio 
    # of (Winner / Total Possible).
    eff_demand_factor = final_demand_kva / connected_kva if connected_kva > 0 else 0.0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": round(eff_demand_factor, 2),
        "Demand Load in kva": round(final_demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2),
        "Scenario Used": scenario_name
    }

def calculate_pump_metrics(
    pump_list: List[Dict], 
    system_voltage: int, 
    sqft: float
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Pump/Motor loads per NEC 430.24.
    
    Handles:
      - Mixed Voltages/Phases (converts to KVA first).
      - Redundant/Standby pumps (included in Connected, excluded from Demand).
      - NEC 430.24 Rule: 125% of Largest Active Motor + Sum of others.
    
    Args:
        pump_list (List[Dict]): List of pumps. Example structure:
            {
                "name": "P-1 Primary",
                "amps": 10.0,
                "voltage": 480,
                "phase": 3,
                "is_standby": False  # Set True for Lag pumps in Duplex sets
            }
        system_voltage (int): Main feeder voltage (e.g., 480, 208).
        sqft (float): Building SQFT.
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(pump_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": 0.0,
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 3)
        
        # Sqrt(3) for 3-phase, 1.0 for Single-phase
        factor = 1.73205 if phase == 3 else 1.0
        
        return (amps * volts * factor) / 1000.0

    # --- 1. Separate Active vs Standby ---
    active_pumps = []
    standby_pumps = []
    
    for pump in pump_list:
        if pump.get('is_standby', False):
            standby_pumps.append(pump)
        else:
            active_pumps.append(pump)

    # --- 2. Calculate Connected Load (Physical Installed Capacity) ---
    # Connected includes EVERYTHING (Active + Standby)
    connected_kva = sum(get_kva(p) for p in pump_list)

    # --- 3. Calculate Demand Load (NEC 430.24) ---
    # Rule: Sum of Active Motors + 25% of Largest Active Motor
    
    sum_active_kva = 0.0
    largest_active_motor_kva = 0.0
    largest_motor_adder = 0.0
    
    for p in active_pumps:
        k = get_kva(p)
        sum_active_kva += k
        
        # Check if this is the largest motor to calculate the 25% slice
        # (We calculate the slice in KVA to keep units consistent)
        if k > largest_active_motor_kva:
            largest_active_motor_kva = k
            largest_motor_adder = k * 0.25
            
    # Final Demand KVA
    demand_kva = sum_active_kva + largest_motor_adder

    # --- 4. Calculate Final Metrics ---
    
    # Demand FLA (Amps at Main Feeder Voltage)
    # I = KVA * 1000 / (Volts * 1.732)
    # Assuming Main Feeder is 3-Phase. If 1-Phase, adjust factor to 1.0.
    main_phase_factor = 1.73205 # Standard assumption for main distribution
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_phase_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0.0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0.0
    
    # Demand Factor
    # (Demand / Connected)
    demand_factor = demand_kva / connected_kva if connected_kva > 0 else 0.0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": round(demand_factor, 2),
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_lighting_metrics(
    sqft: float, 
    building_type: str,
    voltage: int,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Lighting Loads based on SQFT and Occupancy Type.
    
    Ref: NEC Table 220.12 (Density) and Table 220.42 (Demand Factors).
    
    Args:
        sqft (float): Total building square footage.
        building_type (str): 'office', 'school', 'hospital', 'warehouse', 
                             'hotel', 'garage', 'retail', or 'dwelling'.
        voltage (int): System voltage.
        phase (int): 1 or 3.
        
    Returns:
        Dict: Standard output format, but 'demand factor' is a description string.
    """
    
    if sqft <= 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- 1. Define Lookup Tables (NEC 220.12 - 2020 Edition) ---
    # Maps Building Type -> VA per SQFT
    density_table = {
        'office': 1.3,
        'school': 1.3,
        'hospital': 1.6,
        'hotel': 1.7,      # Hotels/Motels
        'warehouse': 0.6,  # Storage spaces
        'garage': 0.3,     # Parking Garages
        'retail': 1.9,     # Retail/Mercantile
        'dwelling': 3.0,   # Residential
        'auditorium': 0.7,
        'restaurant': 1.5,
        'gym': 0.8
    }
    
    # Normalize input
    b_type = building_type.lower().strip()
    
    # Get density (Default to 1.3 "Office" if type not found)
    density = density_table.get(b_type, 1.3) 

    # --- 2. Calculate Connected Load ---
    connected_va = sqft * density
    connected_kva = connected_va / 1000.0

    # --- 3. Calculate Demand Load (NEC 220.42 Sliding Scales) ---
    demand_va = 0.0
    factor_desc = ""

    if 'hospital' in b_type:
        # Hospitals: Total Watts * 1.6 (handled in density)
        # Demand: First 50kVA @ 40%, Remainder @ 20%
        factor_desc = "First 50kVA @ 40%, Remainder @ 20%"
        
        cutoff_va = 50000
        if connected_va <= cutoff_va:
            demand_va = connected_va * 0.40
        else:
            first_part = cutoff_va * 0.40
            remainder = connected_va - cutoff_va
            demand_va = first_part + (remainder * 0.20)

    elif 'hotel' in b_type or 'motel' in b_type:
        # Hotels: First 20kVA @ 50%, Remainder @ 40%
        factor_desc = "First 20kVA @ 50%, Remainder @ 40%"
        
        cutoff_va = 20000
        if connected_va <= cutoff_va:
            demand_va = connected_va * 0.50
        else:
            first_part = cutoff_va * 0.50
            remainder = connected_va - cutoff_va
            demand_va = first_part + (remainder * 0.40)

    elif 'warehouse' in b_type or 'storage' in b_type:
        # Warehouses: First 12.5kVA @ 100%, Remainder @ 50%
        factor_desc = "First 12.5kVA @ 100%, Remainder @ 50%"
        
        cutoff_va = 12500
        if connected_va <= cutoff_va:
            demand_va = connected_va * 1.0
        else:
            first_part = cutoff_va * 1.0
            remainder = connected_va - cutoff_va
            demand_va = first_part + (remainder * 0.50)
            
    elif 'dwelling' in b_type or 'apartment' in b_type:
        # Dwellings: First 3kVA @ 100%, 3k-120k @ 35%, Remainder @ 25%
        factor_desc = "First 3kVA @ 100%, Next 117kVA @ 35%, Remainder @ 25%"
        
        if connected_va <= 3000:
            demand_va = connected_va
        elif connected_va <= 120000:
            demand_va = 3000 + ((connected_va - 3000) * 0.35)
        else:
            demand_va = 3000 + (117000 * 0.35) + ((connected_va - 120000) * 0.25)

    else:
        # All others (Office, School, Retail, Garage) -> 100%
        factor_desc = "Continuous @ 100%"
        demand_va = connected_va # Continuous load usually gets 125%, but lighting tables are specific. 
                                 # Standard feeder calc usually takes Table 220.12 at 100% or 125% 
                                 # depending on breaker rating. 
                                 # We will output 100% here as the "Demand Load" per 220.42.

    # --- 4. Final Conversions ---
    demand_kva = demand_va / 1000.0
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = demand_va / (voltage * sqrt_factor)
    
    demand_density = demand_va / sqft

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(density, 2), # This comes from the Table
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_receptacle_metrics(
    sqft: float, 
    building_type: str,
    voltage: int,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Receptacle loads based on SQFT (NEC 220.14(K)) and 
    applies demand factors (NEC 220.44).
    
    Args:
        sqft (float): Total building square footage.
        building_type (str): 'office', 'bank', 'school', 'warehouse', 'medical', etc.
        voltage (int): System voltage (e.g., 208, 480).
        phase (int): 1 or 3.
        
    Returns:
        Dict: Standard output format with Demand Factor as text.
    """
    
    if sqft <= 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- 1. Define Density Tables (VA/SQFT) ---
    # NEC 220.14(K) mandates 1.0 VA/sqft for Banks and Offices.
    # Other values are based on standard engineering estimates (UFC/ASHRAE)
    # since NEC requires actual device counts (180VA) for others.
    density_table = {
        'office': 1.0,      # NEC 220.14(K)
        'bank': 1.0,        # NEC 220.14(K)
        'school': 1.0,      # Estimation
        'college': 1.0,     # Estimation
        'medical': 2.0,     # Estimation (High density)
        'clinic': 1.5,
        'warehouse': 0.25,  # Low density
        'storage': 0.1,
        'retail': 0.5,
        'corridor': 0.1,
        'industrial': 1.5
    }
    
    # Normalize input
    b_type = building_type.lower().strip()
    
    # Default to 0.5 VA/sqft if type not found (Safe estimation)
    density = density_table.get(b_type, 0.5) 

    # --- 2. Calculate Connected Load ---
    connected_va = sqft * density
    connected_kva = connected_va / 1000.0

    # --- 3. Calculate Demand Load (NEC 220.44) ---
    # Rule: First 10 kVA at 100%, Remainder at 50%
    
    demand_va = 0.0
    factor_desc = "First 10kVA @ 100%, Remainder @ 50%"
    
    cutoff_va = 10000.0 # 10 kVA
    
    if connected_va <= cutoff_va:
        # If load is under 10kVA, it's just 100%
        demand_va = connected_va
        if connected_va > 0:
            factor_desc = "100% (Load < 10kVA)"
    else:
        # First 10,000 VA + 50% of the rest
        remainder = connected_va - cutoff_va
        demand_va = cutoff_va + (remainder * 0.50)

    # --- 4. Final Conversions ---
    demand_kva = demand_va / 1000.0
    
    # Amps calculation
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = demand_va / (voltage * sqrt_factor)
    
    demand_density = demand_va / sqft

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_commercial_kitchen_metrics(
    equipment_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Commercial Kitchen Demand Load per NEC 220.56.
    
    Logic:
      1. Sum Connected Load.
      2. Apply Table 220.56 Demand Factors based on count.
      3. Compare result against the sum of the TWO largest loads.
      4. Return the larger of the two values.
    
    Args:
        equipment_list (List[Dict]): List of kitchen equipment.
            Structure: {"name": "Oven", "amps": 20, "voltage": 208, "phase": 3}
        system_voltage (int): Main Feeder Voltage (e.g., 208, 480).
        sqft (float): Kitchen area (used for density only, not calculation).
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(equipment_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0,
            "Note": "No equipment provided"
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 3) # Default to 3-phase
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load ---
    # Store KVAs in a list for sorting later
    all_kvas = [get_kva(item) for item in equipment_list]
    connected_kva = sum(all_kvas)

    # --- 2. Determine Table 220.56 Demand Factor ---
    # Table: 1-2 units=100%, 3=90%, 4=80%, 5=70%, 6+=65%
    if count >= 6:
        factor_pct = 0.65
    elif count == 5:
        factor_pct = 0.70
    elif count == 4:
        factor_pct = 0.80
    elif count == 3:
        factor_pct = 0.90
    else:
        factor_pct = 1.00
        
    calc_demand_kva = connected_kva * factor_pct

    # --- 3. The "Two Largest Loads" Check (NEC 220.56 Exception) ---
    # The demand load cannot be less than the sum of the two largest individual loads.
    
    all_kvas.sort(reverse=True) # Sort largest to smallest
    
    # Sum top 2 (or just the 1 if only 1 exists)
    two_largest_kva = sum(all_kvas[:2])
    
    # The Final Demand is the Winner of the comparison
    if calc_demand_kva >= two_largest_kva:
        final_demand_kva = calc_demand_kva
        note = f"Table 220.56 applied ({int(factor_pct*100)}%)"
    else:
        final_demand_kva = two_largest_kva
        note = "Override: Sum of 2 Largest Loads (NEC 220.56)"
        # Recalculate effective factor for display
        if connected_kva > 0:
            factor_pct = final_demand_kva / connected_kva

    # --- 4. Final Metrics ---
    
    # Amps (FLA) at Main Feeder Voltage (Assuming 3-phase main)
    # If main service is Single Phase, change 1.732 to 1.0
    main_sqrt_factor = 1.73205
    demand_fla = (final_demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (final_demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": f"{round(factor_pct * 100, 1)}%",
        "Demand Load in kva": round(final_demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2),
        "Note": note
    }

def calculate_ev_metrics(
    charger_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0,
    ems_limit_amps: Optional[float] = None
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC EV Charging Loads (NEC Article 625).
    
    Logic:
      1. Default Demand Factor is 1.0 (100%) per NEC 625.41.
      2. If 'ems_limit_amps' is provided (NEC 625.42), the Demand Load is clamped 
         to that limit.
      3. The 1.25 Continuous Duty multiplier is EXCLUDED per instructions.
    
    Args:
        charger_list (List[Dict]): List of chargers.
            Structure: {"name": "Station 1", "amps": 40, "voltage": 208, "phase": 1}
        system_voltage (int): Main Feeder Voltage (e.g., 208, 480).
        sqft (float): Area (used for density only).
        ems_limit_amps (float, optional): The max amps setting of an Energy Management System.
        
    Returns:
        Dict: Standard output format.
    """
    
    count = len(charger_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 1) # EVs are typically 1-phase (Level 2)
        
        # Sqrt(3) for 3-phase, 1.0 for Single-phase
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load ---
    connected_kva = sum(get_kva(item) for item in charger_list)

    # --- 2. Calculate Demand Load ---
    
    # Calculate what the Demand KVA would be at 100% (No EMS)
    raw_demand_kva = connected_kva
    
    # Check for Energy Management System (EMS) Override
    final_demand_kva = 0.0
    factor_desc = "1.0 (100%)"
    
    if ems_limit_amps is not None and ems_limit_amps > 0:
        # Convert EMS Amp Limit to KVA using Main System Voltage
        # Assuming Main Feeder is 3-Phase
        sqrt_factor = 1.73205
        ems_limit_kva = (ems_limit_amps * system_voltage * sqrt_factor) / 1000.0
        
        # Take the smaller of Connected vs EMS Limit (Code requires sizing to EMS setting)
        if ems_limit_kva < connected_kva:
            final_demand_kva = ems_limit_kva
            
            # Calculate effective factor
            pct = (final_demand_kva / connected_kva) * 100
            factor_desc = f"{round(pct, 1)}% (EMS Limited)"
        else:
            final_demand_kva = connected_kva
    else:
        # Standard NEC 625.41 (No Diversity)
        final_demand_kva = connected_kva

    # --- 3. Final Metrics ---
    
    # Demand FLA at Main Feeder Voltage (3-phase assumption for main panel)
    main_sqrt_factor = 1.73205
    demand_fla = (final_demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (final_demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(final_demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_sign_lighting_metrics(
    sign_list: List[Dict], 
    required_outlets_count: int = 0,
    system_voltage: int = 120,
    sqft: float = 0.0,
    phase: int = 1
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Signage Loads per NEC 220.14(F) and 600.5.
    
    Logic:
      1. Connected Load = Sum of actual nameplates (e.g., specific LED drivers).
      2. Demand Load = For each sign, use MAX(Actual, 1200 VA).
      3. Adds 1200 VA for any extra 'required_outlets_count' (placeholders).
      4. Continuous duty (1.25) excluded per instructions.
    
    Args:
        sign_list (List[Dict]): List of specific signs.
            Structure: {"name": "Main Logo", "amps": 2.5, "voltage": 120, "phase": 1}
        required_outlets_count (int): Number of mandated outlets NOT included in sign_list
                                      (e.g., "1 per entrance" if specific sign unknown).
        system_voltage (int): Main Feeder Voltage.
        sqft (float): Area (for density).
        phase (int): Main system phase.
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    # NEC Constant
    MIN_SIGN_VA = 1200.0

    # --- Helper: Get Actual KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        ph = item.get('phase', 1)
        factor = 1.73205 if ph == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load (Physical) ---
    # This is what is physically drawing power
    physical_kvas = [get_kva(item) for item in sign_list]
    connected_kva = sum(physical_kvas)
    
    # Add connected load for placeholders? 
    # Usually placeholders have 0 "connected" physical load, but full "demand" load.
    # We will exclude placeholders from "Connected" to show the true difference.

    # --- 2. Calculate Demand Load (NEC 220.14(F)) ---
    demand_kva_accum = 0.0
    
    # A. Process specific signs (Apply Min 1200VA rule)
    for kva in physical_kvas:
        va = kva * 1000.0
        if va < MIN_SIGN_VA:
            demand_kva_accum += (MIN_SIGN_VA / 1000.0)
        else:
            demand_kva_accum += kva
            
    # B. Add Placeholder Outlets (Always 1200VA)
    if required_outlets_count > 0:
        demand_kva_accum += (required_outlets_count * MIN_SIGN_VA / 1000.0)

    # --- 3. Determine Demand Factor Description ---
    # It's not a percentage, but a "Min Override".
    if connected_kva == 0 and demand_kva_accum > 0:
        factor_desc = "NEC Min 1200VA per outlet"
    elif demand_kva_accum > connected_kva:
        factor_desc = "100% (adjusted to Min 1200VA)"
    else:
        factor_desc = "1.0 (100%)"

    # --- 4. Final Metrics ---
    
    # Demand FLA at Main Feeder Voltage
    main_sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = (demand_kva_accum * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva_accum * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva_accum, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_water_heater_metrics(
    heater_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Water Heater loads (NEC 422.13).
    
    Logic:
      1. Water Heaters are generally calculated at 100% Demand Factor.
      2. NEC 422.13 defines storage heaters (<120gal) as Continuous Loads.
      3. The 1.25 Continuous Duty multiplier is EXCLUDED per instructions.
    
    Args:
        heater_list (List[Dict]): List of water heaters.
            Structure: {"name": "WH-1", "amps": 15, "voltage": 208, "phase": 1}
        system_voltage (int): Main Feeder Voltage (e.g., 208, 480).
        sqft (float): Area (used for density only).
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(heater_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 1) 
        
        # Sqrt(3) for 3-phase, 1.0 for Single-phase
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load ---
    connected_kva = sum(get_kva(item) for item in heater_list)

    # --- 2. Calculate Demand Load ---
    # NEC 422.13 -> Demand Factor is effectively 100% (1.0).
    # (Diversity for appliances per 220.53 applies to Dwellings, 
    # but commercial water heaters are typically 100%).
    demand_factor = 1.0
    demand_kva = connected_kva * demand_factor

    # --- 3. Final Metrics ---
    
    # Demand FLA at Main Feeder Voltage (Assuming 3-phase main)
    # If the main service is Single Phase (e.g. residential), change to 1.0
    main_sqrt_factor = 1.73205
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": "1.0 (100%)",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_electric_heating_metrics(
    heater_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Fixed Electric Space Heating loads (NEC 220.51).
    
    Includes: Baseboard heaters, unit heaters, duct heaters, heat trace.
    Logic: Calculated at 100% of Connected Load.
    
    Args:
        heater_list (List[Dict]): List of heating units.
            Structure: {"name": "UH-1", "amps": 10, "voltage": 208, "phase": 3}
        system_voltage (int): Main Feeder Voltage.
        sqft (float): Area.
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(heater_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 1) 
        
        # Sqrt(3) for 3-phase, 1.0 for Single-phase
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load ---
    connected_kva = sum(get_kva(item) for item in heater_list)

    # --- 2. Calculate Demand Load (NEC 220.51) ---
    # Rule: 100% of Total Connected Load
    demand_factor_val = 1.0
    demand_kva = connected_kva * demand_factor_val

    # --- 3. Final Metrics ---
    
    # Demand FLA at Main Feeder Voltage (Assuming 3-phase main)
    main_sqrt_factor = 1.73205
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": "1.0 (100%)",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_multioutlet_metrics(
    strip_lengths_ft: List[float], 
    system_voltage: int,
    sqft: float = 0.0,
    simultaneous_usage: bool = False
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Multioutlet Assembly loads (NEC 220.14(H)).
    
    Logic:
      1. Connected Load depends on usage:
         - Standard: 180VA per 5 ft (or fraction thereof).
         - Simultaneous: 180VA per 1 ft.
      2. Demand Load applies NEC 220.44 (First 10kVA @ 100%, Remainder @ 50%).
    
    Args:
        strip_lengths_ft (List[float]): List of lengths in feet for each strip.
            Example: [6.0, 10.0, 3.5]
        system_voltage (int): Main Feeder Voltage.
        sqft (float): Area (used for density).
        simultaneous_usage (bool): True = 180VA/ft, False = 180VA/5ft.
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(strip_lengths_ft)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- 1. Calculate Connected Load (NEC 220.14(H)) ---
    total_va = 0.0
    
    for length in strip_lengths_ft:
        if length <= 0:
            continue
            
        if simultaneous_usage:
            # Heavy Duty: 180 VA per 1 ft
            # "Or fraction thereof" -> ceil(length)
            sections = math.ceil(length)
            total_va += (sections * 180.0)
        else:
            # Standard: 180 VA per 5 ft
            # "Or fraction thereof" -> ceil(length / 5)
            sections = math.ceil(length / 5.0)
            total_va += (sections * 180.0)
            
    connected_kva = total_va / 1000.0

    # --- 2. Calculate Demand Load (NEC 220.44) ---
    # Rule: First 10 kVA at 100%, Remainder at 50%
    
    demand_va = 0.0
    factor_desc = "First 10kVA @ 100%, Remainder @ 50%"
    
    cutoff_va = 10000.0 # 10 kVA
    
    if total_va <= cutoff_va:
        demand_va = total_va
        if total_va > 0:
            factor_desc = "100% (Load < 10kVA)"
    else:
        remainder = total_va - cutoff_va
        demand_va = cutoff_va + (remainder * 0.50)

    # --- 3. Final Metrics ---
    
    demand_kva = demand_va / 1000.0
    
    # Demand FLA at Main Feeder Voltage (Assuming 3-phase main)
    main_sqrt_factor = 1.73205
    demand_fla = (demand_va) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_data_center_metrics(
    equipment_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Data Center Loads (NEC Article 645).
    
    Includes: UPS Inputs, PDUs, CRAC units, Mainframes.
    Logic:
      1. Calculated at 100% of Connected Load (No Diversity).
      2. NEC 645.10 requires sizing for Total Connected Load.
      3. The 1.25 Continuous Duty multiplier is EXCLUDED per instructions.
    
    Args:
        equipment_list (List[Dict]): List of equipment connected to the feeder.
            Structure: {"name": "UPS-A Input", "amps": 400, "voltage": 480, "phase": 3}
        system_voltage (int): Main Feeder Voltage (e.g., 480).
        sqft (float): White Space Area (used for density metrics).
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(equipment_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 3) # Data Centers are predominantly 3-phase
        
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load ---
    # In Data Centers, this is usually the Nameplate Input of the UPS or PDU
    connected_kva = sum(get_kva(item) for item in equipment_list)

    # --- 2. Calculate Demand Load ---
    # NEC 645/220: No diversity allowed for Data Center equipment.
    demand_factor_val = 1.0
    demand_kva = connected_kva * demand_factor_val

    # --- 3. Final Metrics ---
    
    # Demand FLA at Main Feeder Voltage
    main_sqrt_factor = 1.73205 # Assuming Main Feeder is 3-Phase
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities (Watts/sqft is a critical metric in Data Center design)
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": "1.0 (100%)",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_imaging_metrics(
    equipment_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC X-Ray and Imaging loads.
    
    Covers:
      - Medical X-Ray/CT (NEC 517.73): 50% / 25% / 10%
      - Industrial X-Ray (NEC 660.6): 100% (Top 2) / 20% (Rest)
      - MRI/Other: 100% (Standard NEC 220)
    
    Args:
        equipment_list (List[Dict]): List of imaging gear.
            Structure: {
                "name": "CT Scan 1", 
                "amps": 100,            # Momentary Rating
                "voltage": 480, 
                "phase": 3,
                "type": "medical_xray"  # Options: 'medical_xray', 'industrial_xray', 'other'
            }
        system_voltage (int): Main Feeder Voltage.
        sqft (float): Area (used for density).
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(equipment_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0,
            "Note": "No equipment provided"
        }

    # --- Helper: Get KVA ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 3)
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Separate by Type ---
    med_xray_kvas = []
    ind_xray_kvas = []
    other_kvas = [] # MRIs, Ultrasound, etc.
    
    for item in equipment_list:
        k = get_kva(item)
        t = item.get('type', 'other').lower()
        
        if 'medical' in t or 'ct' in t:
            med_xray_kvas.append(k)
        elif 'industrial' in t:
            ind_xray_kvas.append(k)
        else:
            other_kvas.append(k)
            
    # --- 2. Calculate Connected Load (Total Installed) ---
    connected_kva = sum(med_xray_kvas) + sum(ind_xray_kvas) + sum(other_kvas)

    # --- 3. Calculate Demand Load ---
    demand_kva = 0.0
    factor_notes = []

    # A. Medical X-Ray (NEC 517.73)
    # Rule: 50% Largest, 25% Next, 10% Remainder
    if med_xray_kvas:
        med_xray_kvas.sort(reverse=True)
        
        # 1st (Largest)
        demand_kva += med_xray_kvas[0] * 0.50
        
        # 2nd
        if len(med_xray_kvas) > 1:
            demand_kva += med_xray_kvas[1] * 0.25
            
        # 3rd+
        if len(med_xray_kvas) > 2:
            demand_kva += sum(med_xray_kvas[2:]) * 0.10
            
        factor_notes.append("Medical: 50/25/10%")

    # B. Industrial X-Ray (NEC 660.6)
    # Rule: 100% of Two Largest, 20% Remainder
    if ind_xray_kvas:
        ind_xray_kvas.sort(reverse=True)
        
        # Top 2 @ 100%
        top_two = ind_xray_kvas[:2]
        demand_kva += sum(top_two) * 1.0
        
        # Remainder @ 20%
        if len(ind_xray_kvas) > 2:
            demand_kva += sum(ind_xray_kvas[2:]) * 0.20
            
        factor_notes.append("Industrial: 100/100/20%")

    # C. Other (MRI, etc)
    # Rule: 100%
    if other_kvas:
        demand_kva += sum(other_kvas) * 1.0
        factor_notes.append("Other: 100%")

    # --- 4. Final Metrics ---
    
    # Generate Factor Description
    if connected_kva > 0:
        combined_pct = (demand_kva / connected_kva) * 100
        factor_desc = f"{round(combined_pct, 1)}% (Mixed Types)"
    else:
        factor_desc = "N/A"
        
    if len(factor_notes) == 1:
        # If only one type, use the specific note
        factor_desc = factor_notes[0]

    # Amps calculation
    main_sqrt_factor = 1.73205 # Assuming 3-phase main
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2),
        "Note": "; ".join(factor_notes)
    }

def calculate_welder_metrics(
    welder_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Welder Feeders (NEC Article 630).
    
    Logic:
      1. Correct individual welder Amps based on Duty Cycle (Table 630.11(A)).
      2. Sort corrected loads.
      3. Apply Feeder Diversity (NEC 630.11(B)):
         - 1st & 2nd largest: 100%
         - 3rd largest: 85%
         - 4th largest: 70%
         - All others: 60%
    
    Args:
        welder_list (List[Dict]): List of welders.
            Structure: {
                "name": "MIG Station 1", 
                "amps": 50.0,       # Nameplate Primary Amps
                "voltage": 480, 
                "phase": 1,         # Most welders are 1-phase or 2-wire
                "duty_cycle": 60    # Percentage (0-100)
            }
        system_voltage (int): Main Feeder Voltage.
        sqft (float): Area (used for density).
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(welder_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0,
            "Note": "No welders provided"
        }

    # --- Helper: Get Multiplier from Table 630.11(A) ---
    # Based on Non-Motor-Generator Welders (Standard Transformers/Inverters)
    def get_duty_multiplier(duty_pct):
        if duty_pct <= 20: return 0.45
        if duty_pct <= 30: return 0.55
        if duty_pct <= 40: return 0.63
        if duty_pct <= 50: return 0.71
        if duty_pct <= 60: return 0.78
        if duty_pct <= 70: return 0.84
        if duty_pct <= 80: return 0.89
        if duty_pct <= 90: return 0.95
        return 1.00

    # --- Helper: Get KVA ---
    def get_kva(amps, volts, phase):
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load (Nameplate) ---
    # This is the raw installed capacity before any corrections
    total_connected_kva = 0.0
    
    # We also need a list of "Corrected" KVAs for the Demand Step
    corrected_kvas = []
    
    for item in welder_list:
        # Inputs
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 1) # Default to 1-phase/2-pole
        duty = item.get('duty_cycle', 100) # Default to continuous if unknown
        
        # Raw KVA
        raw_kva = get_kva(amps, volts, phase)
        total_connected_kva += raw_kva
        
        # Corrected Amps (Step 1: Table 630.11(A))
        mult = get_duty_multiplier(duty)
        corrected_amps = amps * mult
        
        # Convert corrected amps to KVA for sorting/summing
        corrected_kva = get_kva(corrected_amps, volts, phase)
        corrected_kvas.append(corrected_kva)

    # --- 2. Calculate Demand Load (NEC 630.11(B)) ---
    # Sort corrected loads from largest to smallest
    corrected_kvas.sort(reverse=True)
    
    demand_kva = 0.0
    
    for i, k_val in enumerate(corrected_kvas):
        # i is 0-indexed (0=1st, 1=2nd, 2=3rd...)
        rank = i + 1
        
        if rank == 1 or rank == 2:
            # First and Second Largest: 100%
            demand_kva += (k_val * 1.00)
        elif rank == 3:
            # Third Largest: 85%
            demand_kva += (k_val * 0.85)
        elif rank == 4:
            # Fourth Largest: 70%
            demand_kva += (k_val * 0.70)
        else:
            # All Others: 60%
            demand_kva += (k_val * 0.60)

    # --- 3. Final Metrics ---
    
    # Calculate effective demand factor (Demand / Connected)
    if total_connected_kva > 0:
        eff_factor = (demand_kva / total_connected_kva) * 100
        factor_desc = f"{round(eff_factor, 1)}% (NEC 630.11)"
    else:
        factor_desc = "N/A"

    # Demand FLA at Main Feeder Voltage
    main_sqrt_factor = 1.73205 # Assuming 3-phase main distribution
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (total_connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(total_connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2),
        "Note": "Applies NEC 630.11(A) Duty Cycle & 630.11(B) Group Diversity"
    }

def calculate_machine_shop_metrics(
    machine_list: List[Dict], 
    system_voltage: int,
    sqft: float = 0.0
) -> Dict[str, Union[float, str]]:
    """
    Calculates NEC Metalworking Machine Loads (NEC 430.24).
    
    Includes: Lathes, Mills, Drills, Saws, Grinders, CNC machines.
    Logic:
      1. Connected Load = Sum of all motor nameplates.
      2. Demand Load = (1.25 * Largest Motor) + (Sum of Others).
         (This usually results in a Demand Factor > 100%).
    
    Args:
        machine_list (List[Dict]): List of machines.
            Structure: {"name": "Lathe 1", "amps": 15.5, "voltage": 480, "phase": 3}
        system_voltage (int): Main Feeder Voltage.
        sqft (float): Area (used for density).
        
    Returns:
        Dict: Standard NEC output format.
    """
    
    count = len(machine_list)
    
    if count == 0:
        return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0,
            "Note": "No machines provided"
        }

    # --- Helper: Get KVA for a single item ---
    def get_kva(item):
        amps = item.get('amps', 0.0)
        volts = item.get('voltage', system_voltage)
        phase = item.get('phase', 3) 
        factor = 1.73205 if phase == 3 else 1.0
        return (amps * volts * factor) / 1000.0

    # --- 1. Calculate Connected Load ---
    # We calculate KVA for every machine to normalize mixed voltages (e.g. 120V drill vs 480V lathe)
    all_kvas = []
    for m in machine_list:
        all_kvas.append(get_kva(m))
        
    connected_kva = sum(all_kvas)

    # --- 2. Calculate Demand Load (NEC 430.24) ---
    # Rule: Sum of all motors + 25% of the largest motor
    
    # Identify largest motor (in KVA terms to be safe across voltages)
    largest_motor_kva = max(all_kvas) if all_kvas else 0.0
    
    # Add the 25% buffer
    demand_kva = connected_kva + (0.25 * largest_motor_kva)

    # --- 3. Final Metrics ---
    
    # Calculate effective factor (Usually > 100%)
    if connected_kva > 0:
        eff_factor = (demand_kva / connected_kva) * 100
        factor_desc = f"{round(eff_factor, 1)}% (NEC 430.24)"
    else:
        factor_desc = "N/A"

    # Demand FLA at Main Feeder Voltage (Assuming 3-phase main)
    main_sqrt_factor = 1.73205 
    demand_fla = (demand_kva * 1000.0) / (system_voltage * main_sqrt_factor)
    
    # Densities
    connected_density = (connected_kva * 1000.0) / sqft if sqft > 0 else 0
    demand_density = (demand_kva * 1000.0) / sqft if sqft > 0 else 0

    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": factor_desc,
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2),
        "Note": "Includes 125% Largest Motor Rule"
    }

# --- Example Usage ---

# if __name__ == "__main__":
#     # Elevator Example Inputs
#     my_elevators = [150, 100, 50, 50, 50]
#     sys_voltage = 480
#     bldg_sqft = 50000

#     results = calculate_elevator_metrics(elevator_amps=my_elevators, voltage=sys_voltage, sqft=bldg_sqft)
#     print("calculate_elevator_metrics")    
#     # Print results iterating through the dictionary
#     for key, value in results.items():
#         print(f"{key}: {value}")
#     print("\n")


#     # Fire Alarm Example: A Main FACP (6A) and a NAC Booster Panel (4A) at 120V
#     fa_devices = [6.0, 4.0] 
#     sys_voltage = 120
#     bldg_sqftldg_sqft = 50000

#     results = calculate_fire_alarm_metrics(fa_devices, sys_voltage, bldg_sqft)
#     print("calculate_fire_alarm_metrics")    
#     for key, value in results.items():
#         print(f"{key}: {value}")
#     print("\n")   


#     # IT Systems Example: 
#     it_racks = [16.0, 16.0, 16.0, 16.0] 
#     sys_voltage = 208
#     bldg_sqft = 50000

#     # Note: Phase is 1 because standard rack power is often single-phase 208V
#     results = calculate_it_system_metrics(it_racks, sys_voltage, bldg_sqft, phase=1)
#     print("calculate_it_system_metrics") 
#     for key, value in results.items():
#         print(f"{key}: {value}")
#     print("\n")  


#     # HVAC Example: 
#     # Example Project: 
#     # 2 RTUs (Cooling), 1 Electric Duct Heater (Heating), 1 Toilet Exhaust Fan (Continuous)
#     hvac_data = [
#         {"name": "RTU-1", "amps": 45.0, "voltage": 480, "phase": 3, "type": "cooling", "is_motor": True},
#         {"name": "RTU-2", "amps": 45.0, "voltage": 480, "phase": 3, "type": "cooling", "is_motor": True},
#         {"name": "Heater-1", "amps": 20.0, "voltage": 480, "phase": 3, "type": "heating", "is_motor": False},
#         {"name": "TEF-1", "amps": 5.0, "voltage": 120, "phase": 1, "type": "continuous", "is_motor": True}
#         ]

#         # Building Data
#     main_volts = 480 # Main Service Voltage
#     bldg_sqft = 25000

#     result = calculate_hvac_feeder_demand(hvac_data, main_volts, bldg_sqft)
#     print("calculate_hvac_feeder_demand") 

#     print(f"--- HVAC Calculations ({result['Scenario Used']}) ---")
#     for k, v in result.items():
#         print(f"{k}: {v}")
#     print("\n")  


#     # Plumbing Example:
#     # 1. Domestic Water Booster (Duplex) - Only 1 runs at a time (1 Active, 1 Standby)
#     # 2. Circulation Pump (Always runs)
#     # 3. Sump Pump (120V)

#     project_pumps = [
#         # Duplex Booster Pump A (Active)
#         {"name": "DWBP-1A", "amps": 14.0, "voltage": 480, "phase": 3, "is_standby": False},
#         # Duplex Booster Pump B (Standby/Lag) - Won't add to Demand, adds to Connected
#         {"name": "DWBP-1B", "amps": 14.0, "voltage": 480, "phase": 3, "is_standby": True},
#         # Circulator
#         {"name": "CP-1", "amps": 2.5, "voltage": 480, "phase": 3, "is_standby": False},
#         # Sump Pump (120V Single Phase)
#         {"name": "SP-1", "amps": 9.8, "voltage": 120, "phase": 1, "is_standby": False}
#     ]

#     sys_volts = 480
#     bldg_sqft = 50000

#     result = calculate_pump_metrics(project_pumps, sys_volts, bldg_sqft)
#     print("calculate_pump_metrics") 

#     for k, v in result.items():
#         print(f"{k}: {v}")
#     print("\n") 


#     # Lighitng Example:
#     sys_volts = 480

#     # Example 1: Large Warehouse (Sliding Scale)
#     # 100,000 SQFT * 0.6 VA/SQFT = 60,000 VA Connected
#     # Demand: 12,500 + (47,500 * 0.5) = 12,500 + 23,750 = 36,250 VA
#     wh_result = calculate_lighting_metrics(100000, "warehouse", sys_volts)

#     # Example 2: Office (100% Demand)
#     # 10,000 SQFT * 1.3 VA/SQFT = 13,000 VA
#     # Demand: 13,000 VA
#     off_result = calculate_lighting_metrics(10000, "office", sys_volts)
#     print("calculate_lighting_metrics") 
#     print(f"--- WAREHOUSE ---")
#     print(f"Desc: {wh_result['demand factor']}")
#     print(f"Connected KVA: {wh_result['Connected Load in kva']}")
#     print(f"Demand KVA:    {wh_result['Demand Load in kva']}")

#     print(f"\n--- OFFICE ---")
#     print(f"Desc: {off_result['demand factor']}")
#     print(f"Connected KVA: {off_result['Connected Load in kva']}")
#     print(f"Demand KVA:    {off_result['Demand Load in kva']}")
#     print("\n") 


#     # Receptacle Example:
#     sys_volts = 208 # Receptacles are often calculated at 208V 3-phase for panel sizing

#     # Example 1: Large Office (NEC 220.14(K) + NEC 220.44)
#     # 50,000 SQFT @ 1.0 VA/SQFT = 50 kVA Connected
#     # Demand: 10 kVA + (40 kVA * 0.5) = 30 kVA
#     off_result = calculate_receptacle_metrics(50000, "office", sys_volts)
#     print("calculate_receptacle_metrics") 

#     print(f"--- OFFICE (50k SQFT) ---")
#     print(f"Factor:        {off_result['demand factor']}")
#     print(f"Connected KVA: {off_result['Connected Load in kva']}")
#     print(f"Demand KVA:    {off_result['Demand Load in kva']}")
#     print(f"Demand FLA:    {off_result['demand FLA']} A")
#     # Example 2: Small Warehouse
#     # 20,000 SQFT @ 0.25 VA/SQFT = 5 kVA Connected
#     # Demand: 5 kVA (Since it's under 10kVA)
#     wh_result = calculate_receptacle_metrics(20000, "warehouse", sys_volts)
#     print(f"\n--- WAREHOUSE (20k SQFT) ---")
#     print(f"Factor:        {wh_result['demand factor']}")
#     print(f"Connected KVA: {wh_result['Connected Load in kva']}")
#     print(f"Demand KVA:    {wh_result['Demand Load in kva']}")
#     print("\n") 


#     # Kitchen Example:
#     # Example: 6 pieces of equipment (Should get 65%)
#     # BUT we have 2 huge ovens, so the "2 Largest" rule might trigger override.
#     kitchen_gear = [
#         {"name": "Oven 1", "amps": 30, "voltage": 208, "phase": 3},  # ~10.8 kVA
#         {"name": "Oven 2", "amps": 30, "voltage": 208, "phase": 3},  # ~10.8 kVA
#         {"name": "Fryer", "amps": 15, "voltage": 208, "phase": 3},
#         {"name": "Steamer", "amps": 12, "voltage": 208, "phase": 3},
#         {"name": "Booster", "amps": 15, "voltage": 208, "phase": 3},
#         {"name": "Warmer", "amps": 5, "voltage": 120, "phase": 1}
#     ]

#     sys_volts = 208
#     sqft = 1000

#     result = calculate_commercial_kitchen_metrics(kitchen_gear, sys_volts, sqft)
#     print("calculate_commercial_kitchen_metrics") 

#     for k, v in result.items():
#         print(f"{k}: {v}")
#     print("\n")


#     # EV Charging Example:
#     # Example: 10 EV Chargers @ 40A each (Level 2), 208V Single Phase
#     # Total Connected Amps = 400A
#     chargers = [{"name": f"EV-{i}", "amps": 40, "voltage": 208, "phase": 1} for i in range(10)]

#     sys_volts = 208
#     sqft = 50000

#     # Case A: Standard (No EMS)
#     res_std = calculate_ev_metrics(chargers, sys_volts, sqft)

#     # Case B: With EMS limiting feeder to 200A
#     res_ems = calculate_ev_metrics(chargers, sys_volts, sqft, ems_limit_amps=200)
#     print("calculate_ev_metrics") 

#     print("--- Standard (No Diversity) ---")
#     print(f"Connected KVA: {res_std['Connected Load in kva']}")
#     print(f"Demand KVA:    {res_std['Demand Load in kva']}")
#     print(f"Demand FLA:    {res_std['demand FLA']}")

#     print("\n--- With Energy Management (EMS Limit 200A) ---")
#     print(f"Factor:        {res_ems['demand factor']}")
#     print(f"Demand KVA:    {res_ems['Demand Load in kva']}")
#     print(f"Demand FLA:    {res_ems['demand FLA']}")
#     print("\n")


#     # Sign Example:
#     # 1. High Efficiency LED Sign (300 Watts) -> Needs to be calc'd at 1200 VA
#     # 2. Large Digital Billboard (5000 Watts) -> Needs to be calc'd at 5000 VA
#     # 3. One "Future" outlet required for the back door (Placeholder)

#     signs = [
#         {"name": "Front LED Channel Letters", "amps": 2.5, "voltage": 120, "phase": 1}, # ~300 VA
#         {"name": "Highway Pylon", "amps": 24.0, "voltage": 208, "phase": 1}             # ~5000 VA
#     ]

#     extra_outlets = 1
#     sys_volts = 208
#     sqft = 10000

#     result = calculate_sign_lighting_metrics(
#         signs, 
#         required_outlets_count=extra_outlets, 
#         system_voltage=sys_volts, 
#         sqft=sqft,
#         phase=3
#     )
#     print("calculate_sign_lighting_metrics") 

#     print(f"--- Signage Load Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']} (Actual installed)")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']} (NEC Required)")
#     print(f"Demand FLA:    {result['demand FLA']} (Feeder Amps)")
#     print("\n")


#     # Water Heater Example: 
#     # 1. Large Building Water Heater (4500W, 208V, 3-Phase)
#     # 2. Small Under-sink heater (1500W, 120V, 1-Phase)
#     heaters = [
#         {"name": "WH-Main", "amps": 12.5, "voltage": 208, "phase": 3}, # ~4.5 kVA
#         {"name": "WH-Breakroom", "amps": 12.5, "voltage": 120, "phase": 1} # ~1.5 kVA
#     ]

#     sys_volts = 208
#     sqft = 15000

#     result = calculate_water_heater_metrics(heaters, sys_volts, sqft)
#     print("calculate_water_heater_metrics") 

#     print(f"--- Water Heater Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']}")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']}")
#     print(f"Demand FLA:    {result['demand FLA']}")
#     print("\n")


#     # Electric Heater Example: 
#     # Example: 
#     # 1. 10kW Unit Heater in Loading Dock (480V, 3-phase)
#     # 2. 500W Cabinet Heater in Sprinkler Room (120V, 1-phase)
#     heaters = [
#         {"name": "UH-1", "amps": 12.0, "voltage": 480, "phase": 3},  # ~10 kVA
#         {"name": "CabHeat-1", "amps": 4.2, "voltage": 120, "phase": 1} # ~0.5 kVA
#     ]

#     sys_volts = 480
#     sqft = 20000

#     result = calculate_electric_heating_metrics(heaters, sys_volts, sqft)
#     print("calculate_electric_heating_metrics") 

#     print(f"--- Electric Heating Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']}")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']}")
#     print(f"Demand FLA:    {result['demand FLA']}")
#     print("\n")


#     # Multioutlet Example: 
#     sys_volts = 208
#     sqft = 5000

#     # Example 1: Office Cubicles (Standard use)
#     # Ten 6-foot strips.
#     # Logic: 6ft / 5 = 1.2 -> rounds up to 2 sections per strip.
#     # 2 sections * 180 VA = 360 VA per strip.
#     # Total = 3600 VA.
#     strips_office = [6.0] * 10 

#     res_office = calculate_multioutlet_metrics(strips_office, sys_volts, sqft, simultaneous_usage=False)
#     print("calculate_multioutlet_metrics") 

#     print(f"--- Office Strips (Standard) ---")
#     print(f"Connected KVA: {res_office['Connected Load in kva']}")
#     print(f"Demand KVA:    {res_office['Demand Load in kva']}")
#     # Example 2: Lab Bench (Simultaneous use)
#     # Ten 6-foot strips.
#     # Logic: 6ft * 180 VA = 1080 VA per strip.
#     # Total = 10,800 VA.
#     # Demand: First 10,000 + (800 * 0.5) = 10,400 VA.
#     res_lab = calculate_multioutlet_metrics(strips_office, sys_volts, sqft, simultaneous_usage=True)

#     print(f"\n--- Lab Bench (Simultaneous) ---")
#     print(f"Connected KVA: {res_lab['Connected Load in kva']}")
#     print(f"Demand KVA:    {res_lab['Demand Load in kva']}")
#     print("\n")


#     # Data Center Example: 
#     # Example: A Feeder supplying "A-Side" infrastructure
#     # 1. 300kVA UPS Input (Nameplate might be 360A @ 480V)
#     # 2. Two CRAC Units (Cooling)
#     dc_equipment = [
#         {"name": "UPS-1A Input", "amps": 361.0, "voltage": 480, "phase": 3}, # ~300 kVA
#         {"name": "CRAC-1", "amps": 45.0, "voltage": 480, "phase": 3},        # ~37 kVA
#         {"name": "CRAC-2", "amps": 45.0, "voltage": 480, "phase": 3}         # ~37 kVA
#     ]

#     sys_volts = 480
#     whitespace_sqft = 2500 # Small server room

#     result = calculate_data_center_metrics(dc_equipment, sys_volts, whitespace_sqft)
#     print("calculate_data_center_metrics") 

#     print(f"--- Data Center Feeder Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']}")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']}")
#     print(f"Demand FLA:    {result['demand FLA']}")
#     print(f"Power Density: {result['Demand Volt-Amps/SQFT']} VA/sqft")
#     print("\n")





#     # X-Ray/Imaging Example: 
#     sys_volts = 480
#     sqft = 20000

#     # Example: Hospital Imaging Suite
#     # 1. CT Scan (Momentary 100A)
#     # 2. X-Ray Room 1 (Momentary 60A)
#     # 3. X-Ray Room 2 (Momentary 60A)
#     # 4. MRI (Continuous 50A) - Not an X-ray
#     imaging_gear = [
#         {"name": "CT Scan", "amps": 100, "voltage": 480, "phase": 3, "type": "medical_xray"},
#         {"name": "X-Ray 1", "amps": 60, "voltage": 480, "phase": 1, "type": "medical_xray"},
#         {"name": "X-Ray 2", "amps": 60, "voltage": 480, "phase": 1, "type": "medical_xray"},
#         {"name": "MRI", "amps": 50, "voltage": 480, "phase": 3, "type": "other"}
#     ]

#     result = calculate_imaging_metrics(imaging_gear, sys_volts, sqft)
#     print("calculate_imaging_metrics") 

#     print(f"--- Imaging Feeder Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']}")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']}")
#     print(f"Demand FLA:    {result['demand FLA']}")
#     print("\n")


#     # Welding Example: 
#     sys_volts = 480
#     sqft = 5000

#     # Example: A Welding Shop
#     # 1. Heavy Duty MIG (100A, 60% Duty)
#     # 2. Heavy Duty MIG (100A, 60% Duty)
#     # 3. Medium TIG (50A, 50% Duty)
#     # 4. Light Spot (30A, 20% Duty)
#     # 5. Backup (30A, 20% Duty)

#     welders = [
#         {"name": "MIG-1", "amps": 100, "voltage": 480, "phase": 1, "duty_cycle": 60},
#         {"name": "MIG-2", "amps": 100, "voltage": 480, "phase": 1, "duty_cycle": 60},
#         {"name": "TIG-1", "amps": 50, "voltage": 480, "phase": 1, "duty_cycle": 50},
#         {"name": "Spot-1", "amps": 30, "voltage": 480, "phase": 1, "duty_cycle": 20},
#         {"name": "Spot-2", "amps": 30, "voltage": 480, "phase": 1, "duty_cycle": 20},
#     ]

#     result = calculate_welder_metrics(welders, sys_volts, sqft)
#     print("calculate_welder_metrics") 
#     print(f"--- Welder Feeder Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']} (Nameplate)")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']} (Sizing Load)")
#     print(f"Demand FLA:    {result['demand FLA']}")
#     print("\n")




#     # Machine Shop Example: 
#     sys_volts = 480
#     sqft = 2500

#     # Example: Small Machine Shop
#     # 1. CNC Mill (Largest): 30A @ 480V
#     # 2. Manual Lathe: 10A @ 480V
#     # 3. Drill Press: 5A @ 480V
#     # 4. Bench Grinder: 5A @ 120V (Single Phase)
#     machines = [
#         {"name": "CNC Mill", "amps": 30, "voltage": 480, "phase": 3},   # ~25 kVA
#         {"name": "Lathe", "amps": 10, "voltage": 480, "phase": 3},      # ~8.3 kVA
#         {"name": "Drill", "amps": 5, "voltage": 480, "phase": 3},       # ~4.1 kVA
#         {"name": "Grinder", "amps": 5, "voltage": 120, "phase": 1},     # ~0.6 kVA
#     ]

#     result = calculate_machine_shop_metrics(machines, sys_volts, sqft)
#     print("calculate_machine_shop_metrics") 

#     print(f"--- Machine Shop Feeder Calculation ---")
#     print(f"Connected KVA: {result['Connected Load in kva']}")
#     print(f"Demand Factor: {result['demand factor']}")
#     print(f"Demand KVA:    {result['Demand Load in kva']}")
#     print(f"Demand FLA:    {result['demand FLA']}")
#     print("\n")

# ==========================================
# PART 2.5: New Default & Detailed Functions
# ==========================================

def default_calculate_elevator_metrics(
    num_floors: int,
    system_voltage: int = 480,
    sqft: float = 0.0,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for elevators.
    Rule: 2-story = 1 elevator, 20-story = 10 elevators. (1 per 2 floors), 50A each.
    """
    if num_floors <= 0:
        return {}
    
    # Estimate number of elevators (1 per 2 floors)
    num_elevators = max(1, math.ceil(num_floors / 2.0))
    
    # Create synthetic list of amps (50A per elevator)
    elevator_amps = [50.0] * num_elevators
    
    # Reuse existing detailed logic
    return calculate_elevator_metrics(elevator_amps, system_voltage, sqft, phase)

def default_calculate_hvac_feeder_demand(
    occupancy_type: str,
    sqft: float,
    system_voltage: int = 480,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for HVAC based on VA/sqft density table.
    """
    density_table = {
        'office': 7.0,
        'bank': 7.0,
        'school': 6.0,
        'college': 7.0,
        'medical': 14.0, # Hospital
        'clinic': 9.0,
        'warehouse': 2.0,
        'storage': 1.0,
        'retail': 6.5,
        'corridor': 2.0,
        'industrial': 6.0,
        'restaurant': 12.0
    }
    
    dens = density_table.get(occupancy_type.lower(), 7.0) # Default to Office if unknown
    
    connected_va = sqft * dens
    connected_kva = connected_va / 1000.0
    
    # Assuming Demand = Connected for HVAC estimation (Continuous)
    demand_kva = connected_kva
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = (demand_kva * 1000.0) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(dens, 2),
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(dens, 2),
        "demand FLA": round(demand_fla, 2),
        "Scenario Used": "Estimation"
    }

def default_calculate_pump_metrics(
    project_connected_kva: float = 0.0,
    system_voltage: int = 480
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for pumps: 5% of Total Load.
    NOTE: Requires 'project_connected_kva' to be known, which is circular.
    Returns 0 with a note if 0 passed.
    """
    if project_connected_kva <= 0:
         return {
            "Connected Load in kva": 0.0,
            "Connected Volt-Amps/SQFT": 0.0,
            "demand factor": "N/A",
            "Demand Load in kva": 0.0,
            "Demand Volt-Amps/SQFT": 0.0,
            "demand FLA": 0.0,
            "Note": "Requires Total Load to estimate 5%"
        }
    
    demand_kva = project_connected_kva * 0.05
    sqrt_factor = 1.73205
    demand_fla = (demand_kva * 1000.0) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(demand_kva, 2),
        "Connected Volt-Amps/SQFT": 0.0,
        "demand factor": "5% of Total",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": 0.0,
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_commercial_kitchen_metrics(
    kitchen_sqft: float,
    system_voltage: int = 208,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for Kitchen: 50 Watts (VA) per sqft.
    """
    density = 50.0
    connected_va = kitchen_sqft * density
    connected_kva = connected_va / 1000.0
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = (connected_va) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(density, 2),
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(connected_kva, 2),
        "Demand Volt-Amps/SQFT": round(density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_ev_metrics(
    num_level2: int,
    num_fast: int,
    system_voltage: int = 208
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for EV:
    - Level 2: 7.2 kVA
    - Fast: 50 kVA
    """
    l2_kva = num_level2 * 7.2
    fast_kva = num_fast * 50.0
    total_kva = l2_kva + fast_kva
    
    # Assuming 100% demand
    sqrt_factor = 1.73205 # usually 3-phase service
    demand_fla = (total_kva * 1000.0) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(total_kva, 2),
        "Connected Volt-Amps/SQFT": 0.0,
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(total_kva, 2),
        "Demand Volt-Amps/SQFT": 0.0,
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_imaging_metrics(
    num_mri: int,
    num_ct: int,
    num_xray: int,
    system_voltage: int = 480
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for Imaging:
    - MRI: 100 kVA
    - CT: 70 kVA
    - XRay: 20 kVA
    """
    mri_kva = num_mri * 100.0
    ct_kva = num_ct * 70.0
    xray_kva = num_xray * 20.0
    
    total_kva = mri_kva + ct_kva + xray_kva
    
    sqrt_factor = 1.73205
    demand_fla = (total_kva * 1000.0) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(total_kva, 2),
        "Connected Volt-Amps/SQFT": 0.0,
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(total_kva, 2),
        "Demand Volt-Amps/SQFT": 0.0,
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_data_center_metrics(
    dc_sqft: float,
    system_voltage: int = 480
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for Data Center: 300 Watts (VA) per sqft.
    """
    density = 300.0
    connected_va = dc_sqft * density
    connected_kva = connected_va / 1000.0
    
    sqrt_factor = 1.73205
    demand_fla = (connected_va) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(density, 2),
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(connected_kva, 2),
        "Demand Volt-Amps/SQFT": round(density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_fire_alarm_metrics(
    sqft: float,
    system_voltage: int = 120,
    phase: int = 1
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for Fire Alarm: 0.5 VA/sqft.
    """
    density = 0.5
    connected_va = sqft * density
    connected_kva = connected_va / 1000.0
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = (connected_va) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(density, 2),
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(connected_kva, 2),
        "Demand Volt-Amps/SQFT": round(density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_it_system_metrics(
    sqft: float,
    system_voltage: int = 120,
    phase: int = 1
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for IT Systems: 0.5 VA/sqft.
    """
    density = 0.5
    connected_va = sqft * density
    connected_kva = connected_va / 1000.0
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = (connected_va) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(density, 2),
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(connected_kva, 2),
        "Demand Volt-Amps/SQFT": round(density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def default_calculate_sign_lighting_metrics(
    num_entrances: int,
    system_voltage: int = 120,
    sqft: float = 0.0 # for density
) -> Dict[str, Union[float, str]]:
    """
    Default estimation for Signage: 1200 VA per entrance.
    """
    per_sign_va = 1200.0
    connected_va = num_entrances * per_sign_va
    connected_kva = connected_va / 1000.0
    
    sqrt_factor = 1.0 # Signs usually 1-phase
    demand_fla = (connected_va) / (system_voltage * sqrt_factor)
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": 0.0,
        "demand factor": "100% (Est)",
        "Demand Load in kva": round(connected_kva, 2),
        "Demand Volt-Amps/SQFT": 0.0,
        "demand FLA": round(demand_fla, 2)
    }

# New Detailed Functions

def calculate_lighting_metrics(
    room_list: List[Dict],
    system_voltage: int = 277,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Detailed Lighting Calc using Hospital Data lookup.
    Args:
        room_list (List[Dict]): [{'name': 'Room A', 'sqft': 150}, ...]
    """
    total_va = 0.0
    total_sqft = 0.0
    
    for room in room_list:
        sqft = room.get('sqft', 0)
        name = room.get('name', '')
        
        # Lookup
        data = get_lighting_data(name)
        if data:
            va_sqft = float(data.get('va_per_sq_ft', 0.0))
        else:
            va_sqft = 0.0 # Or default?
            
        total_va += (sqft * va_sqft)
        total_sqft += sqft
        
    connected_kva = total_va / 1000.0
    
    # 220.42 Demand Factors (Standard "Hospital" sliding scale?)
    # For now, simplistic 100% or we can apply 220.42 logic
    # Instructions say: "use ... lighting_hospital_data.py to calculate the total VA"
    # It doesn't explicitly ask for Demand Factor logic here, but implies using the data for input.
    # I'll apply standard 220.42 Hospital rule to be consistent with detailed intent.
    # Hospital: first 50kVA @ 40%, rem @ 20%
    
    cutoff_va = 50000
    if total_va <= cutoff_va:
        demand_va = total_va * 0.40
    else:
        first_part = cutoff_va * 0.40
        remainder = total_va - cutoff_va
        demand_va = first_part + (remainder * 0.20)
        
    demand_kva = demand_va / 1000.0
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = demand_va / (system_voltage * sqrt_factor)
    
    demand_density = demand_va / total_sqft if total_sqft > 0 else 0
    connected_density = total_va / total_sqft if total_sqft > 0 else 0
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": "Hospital Scale (40%/20%)",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

def calculate_receptacle_metrics(
    input_data: Union[List[Dict], int],
    system_voltage: int = 120,
    phase: int = 3
) -> Dict[str, Union[float, str]]:
    """
    Detailed Receptacle Calc.
    Args:
        input_data: Either a List[Dict] (rooms) or int (total count).
    """
    total_va = 0.0
    total_sqft = 0.0
    
    if isinstance(input_data, int):
        # Case 3: User provides total count
        count = input_data
        total_va = count * 90.0
        
    elif isinstance(input_data, list):
        for room in input_data:
            sqft = room.get('sqft', 0)
            name = room.get('name', '')
            total_sqft += sqft
            
            data = get_room_data(name)
            
            if data and sqft > 0:
                # Case 1: Room + SQFT -> Use VA/SQFT
                va_sqft = float(data.get('va_per_sq_ft', 0.0))
                total_va += (sqft * va_sqft)
            elif data and sqft <= 0:
                 # Case 2: Room + No SQFT -> Use Min Receptacles * 90
                 min_recep = data.get('min_receptacles', 0)
                 if isinstance(min_recep, str):
                     if min_recep.isdigit():
                         min_recep = int(min_recep)
                     else:
                         min_recep = 0
                 total_va += (min_recep * 90.0)
            else:
                 # Unknown room or empty
                 pass
    
    connected_kva = total_va / 1000.0
    
    # NEC 220.44: First 10kVA @ 100%, rem @ 50%
    cutoff_va = 10000
    if total_va <= cutoff_va:
        demand_va = total_va
    else:
        remainder = total_va - cutoff_va
        demand_va = cutoff_va + (remainder * 0.50)
        
    demand_kva = demand_va / 1000.0
    
    sqrt_factor = 1.73205 if phase == 3 else 1.0
    demand_fla = demand_va / (system_voltage * sqrt_factor)
    
    demand_density = demand_va / total_sqft if total_sqft > 0 else 0
    connected_density = total_va / total_sqft if total_sqft > 0 else 0
    
    return {
        "Connected Load in kva": round(connected_kva, 2),
        "Connected Volt-Amps/SQFT": round(connected_density, 2),
        "demand factor": "First 10kVA @ 100% / Rem @ 50%",
        "Demand Load in kva": round(demand_kva, 2),
        "Demand Volt-Amps/SQFT": round(demand_density, 2),
        "demand FLA": round(demand_fla, 2)
    }

# ==========================================
# PART 3: Execution / Main Method (CORRECTED)
# ==========================================

if __name__ == "__main__":
    # --- 1. Project Parameters ---
    PROJECT_VOLTAGE = 480       # Main Service Voltage (3-Phase)
    PROJECT_SQFT = 50000.0      # Total Building Area
    SPARE_CAPACITY_PCT = 25.0   # <--- ADJUSTABLE VARIABLE (e.g., 15, 20, 25)

    # Initialize the Schedule Table
    schedule = ElectricalLoadSchedule(PROJECT_VOLTAGE, phase=3)

    print(f"Generating Load Schedule for {PROJECT_SQFT:,.0f} SQFT Facility...")

    # ==========================================
    # 2. Process Loads & Add to Schedule
    # ==========================================

    # --- A. Elevators ---
    # 3 Elevators, 50A each
    elev_data = [50.0, 50.0, 50.0]
    # FIX: Added PROJECT_SQFT to the arguments below
    res_elev = calculate_elevator_metrics(elev_data, PROJECT_VOLTAGE, PROJECT_SQFT, phase=3)
    schedule.add_load("Elevators", res_elev)

    # --- B. Fire Alarm ---
    # Main FACP + Booster (120V)
    fa_data = [6.0, 4.0] 
    res_fa = calculate_fire_alarm_metrics(fa_data, voltage=120, sqft=PROJECT_SQFT, phase=1)
    schedule.add_load("Fire Alarm System", res_fa)

    # --- C. IT Systems ---
    # 4 IDF Racks (120V)
    it_data = [16.0, 16.0, 16.0, 16.0]
    res_it = calculate_it_system_metrics(it_data, voltage=120, sqft=PROJECT_SQFT, phase=1)
    schedule.add_load("IT / Telecom", res_it)

    # --- D. HVAC ---
    # 2 RTUs (Cooling), 1 Duct Heater (Heating), 1 Exhaust Fan (Continuous)
    hvac_data = [
        {"name": "RTU-1", "amps": 45.0, "voltage": 480, "phase": 3, "type": "cooling", "is_motor": True},
        {"name": "RTU-2", "amps": 45.0, "voltage": 480, "phase": 3, "type": "cooling", "is_motor": True},
        {"name": "DH-1", "amps": 20.0, "voltage": 480, "phase": 3, "type": "heating", "is_motor": False},
        {"name": "EF-1", "amps": 5.0, "voltage": 480, "phase": 3, "type": "continuous", "is_motor": True}
    ]
    res_hvac = calculate_hvac_feeder_demand(hvac_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load(f"HVAC ({res_hvac.get('Scenario Used', 'General')})", res_hvac)

    # --- E. Pumps ---
    # Duplex Booster (1 Active, 1 Standby) + Circulator
    pump_data = [
        {"name": "Dom Water A", "amps": 14.0, "voltage": 480, "phase": 3, "is_standby": False},
        {"name": "Dom Water B", "amps": 14.0, "voltage": 480, "phase": 3, "is_standby": True},
        {"name": "Circulator", "amps": 2.5, "voltage": 480, "phase": 3, "is_standby": False}
    ]
    res_pumps = calculate_pump_metrics(pump_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Plumbing Pumps", res_pumps)

    # --- F. Lighting ---
    # General Office Lighting
    res_ltg = default_calculate_lighting_metrics(PROJECT_SQFT, "office", PROJECT_VOLTAGE, phase=3)
    schedule.add_load("Lighting (Interior)", res_ltg)

    # --- G. Receptacles ---
    # General Office Receptacles
    res_recept = default_calculate_receptacle_metrics(PROJECT_SQFT, "office", PROJECT_VOLTAGE, phase=3)
    schedule.add_load("Receptacles", res_recept)

    # --- H. Commercial Kitchen ---
    # 6 items (Fryer, Oven, Steamer, etc.)
    kitchen_data = [
        {"name": "Oven 1", "amps": 30, "voltage": 208, "phase": 3},
        {"name": "Oven 2", "amps": 30, "voltage": 208, "phase": 3},
        {"name": "Fryer", "amps": 15, "voltage": 208, "phase": 3},
        {"name": "Steamer", "amps": 12, "voltage": 208, "phase": 3},
        {"name": "Booster", "amps": 15, "voltage": 208, "phase": 3},
        {"name": "Warmer", "amps": 5, "voltage": 120, "phase": 1}
    ]
    res_kitchen = calculate_commercial_kitchen_metrics(kitchen_data, system_voltage=208, sqft=1000)
    schedule.add_load("Kitchen Equipment", res_kitchen)

    # --- I. EV Charging ---
    # 4 Chargers, No EMS (100% Demand)
    ev_data = [{"name": f"EV-{i}", "amps": 40, "voltage": 208, "phase": 1} for i in range(4)]
    res_ev = calculate_ev_metrics(ev_data, system_voltage=208, sqft=PROJECT_SQFT)
    schedule.add_load("EV Charging", res_ev)

    # --- J. Signage ---
    # 1 Pylon Sign + 1 Required Entrance Outlet
    sign_data = [{"name": "Pylon", "amps": 15.0, "voltage": 120, "phase": 1}]
    res_signs = calculate_sign_lighting_metrics(sign_data, required_outlets_count=1, system_voltage=120, sqft=PROJECT_SQFT)
    schedule.add_load("Signage", res_signs)

    # --- K. Water Heaters ---
    # 1 Large Water Heater
    wh_data = [{"name": "WH-1", "amps": 15.0, "voltage": 480, "phase": 3}]
    res_wh = calculate_water_heater_metrics(wh_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Water Heaters", res_wh)

    # --- L. Electric Heating ---
    # 2 Cabinet Heaters
    heat_data = [{"name": "UH-1", "amps": 5.0, "voltage": 480, "phase": 3}, {"name": "UH-2", "amps": 5.0, "voltage": 480, "phase": 3}]
    res_heat = calculate_electric_heating_metrics(heat_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Space Heating (Misc)", res_heat)

    # --- M. Multioutlet Assemblies ---
    # Ten 6ft strips (Standard Use)
    strips_data = [6.0] * 10
    res_multi = calculate_multioutlet_metrics(strips_data, system_voltage=120, sqft=PROJECT_SQFT, simultaneous_usage=False)
    schedule.add_load("Multioutlet Assemblies", res_multi)

    # --- N. Data Center ---
    # Small UPS Input (No Diversity)
    dc_data = [{"name": "UPS Input", "amps": 50.0, "voltage": 480, "phase": 3}]
    res_dc = calculate_data_center_metrics(dc_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Server Room UPS", res_dc)

    # --- O. Imaging ---
    # 1 CT Scan, 1 X-Ray (Medical logic)
    img_data = [
        {"name": "CT", "amps": 80, "voltage": 480, "phase": 3, "type": "medical_xray"},
        {"name": "XRay", "amps": 60, "voltage": 480, "phase": 1, "type": "medical_xray"}
    ]
    res_img = calculate_imaging_metrics(img_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Medical Imaging", res_img)

    # --- P. Welders ---
    # 2 Welders with Duty Cycles
    weld_data = [
        {"name": "MIG", "amps": 60, "voltage": 480, "phase": 1, "duty_cycle": 50},
        {"name": "TIG", "amps": 40, "voltage": 480, "phase": 1, "duty_cycle": 40}
    ]
    res_weld = calculate_welder_metrics(weld_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Maintenance Shop Welders", res_weld)

    # --- Q. Machine Shop ---
    # Lathe and Drill Press
    mach_data = [
        {"name": "Lathe", "amps": 10, "voltage": 480, "phase": 3},
        {"name": "Drill", "amps": 5, "voltage": 480, "phase": 3}
    ]
    res_mach = calculate_machine_shop_metrics(mach_data, PROJECT_VOLTAGE, PROJECT_SQFT)
    schedule.add_load("Maintenance Machine Shop", res_mach)

    # ==========================================
    # 3. Generate Final Report
    # ==========================================
    # This will calculate totals, apply the adjustable spare %, and print the table.
    schedule.generate_table(spare_percent=SPARE_CAPACITY_PCT)