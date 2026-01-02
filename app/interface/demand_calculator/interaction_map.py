
# interaction_map.py

# This file maps the "User Keywords" (e.g. "hvac") to:
# 1. The specific function in main.py to call.
# 2. The sequence of prompts required to gather arguments.

FUNCTION_MAP = {
    # --- ELEVATORS ---
    "elevators": {
        "function": "calculate_elevator_metrics",
        "prompts": [
            {"arg": "elevator_amps", "type": "list_float", "question": "Enter the FLA for each elevator as a list (e.g., [24.5, 40])"},
            {"arg": "voltage", "type": "int", "question": "System voltage for these elevators (e.g., 480)?", "default_from_project": True},
            {"arg": "sqft", "type": "float", "question": "Total Building Area (SQFT)?", "default_from_project": True},
            {"arg": "phase", "type": "int", "question": "Phase (1 or 3)?", "default": 3}
        ]
    },
    "default_elevators": {
        "function": "default_calculate_elevator_metrics",
        "prompts": [
            {"arg": "num_floors", "type": "int", "question": "Number of floors served?"},
            {"arg": "system_voltage", "type": "int", "question": "System Voltage?", "default_from_project": True},
            {"arg": "sqft", "type": "float", "question": "Total Building Area (SQFT)?", "default_from_project": True},
            {"arg": "phase", "type": "int", "question": "Phase (1 or 3)?", "default": 3}
        ]
    },

    # --- HVAC ---
    "hvac": {
        "function": "calculate_hvac_feeder_demand",
        "prompts": [
            {"arg": "equipment_list", "type": "list_dict", "question": "Enter list of HVAC equipment (e.g., [{'name': 'RTU-1', 'amps': 45, 'voltage': 480, 'phase': 3, 'type': 'cooling', 'is_motor': True}])"},
            {"arg": "system_voltage", "type": "int", "question": "System Voltage?", "default_from_project": True},
            {"arg": "sqft", "type": "float", "question": "Total Building Area (SQFT)?", "default_from_project": True}
        ]
    },
    "default_hvac": {
        "function": "default_calculate_hvac_feeder_demand",
        "prompts": [
            {"arg": "occupancy_type", "type": "str", "question": "Occupancy Type (office, school, hospital, retail, etc.)?", "default": "office"},
            {"arg": "sqft", "type": "float", "question": "Total Building Area (SQFT)?", "default_from_project": True},
            {"arg": "system_voltage", "type": "int", "question": "System Voltage?", "default_from_project": True},
            {"arg": "phase", "type": "int", "question": "Phase (1 or 3)?", "default": 3}
        ]
    },

    # --- PUMPS ---
    "pumps": {
        "function": "calculate_pump_metrics",
        "prompts": [
            {"arg": "pump_list", "type": "list_dict", "question": "Enter list of pumps (e.g., [{'name': 'P-1', 'amps': 10, 'voltage': 480, 'is_standby': False}])"},
            {"arg": "system_voltage", "type": "int", "question": "System Voltage?", "default_from_project": True},
            {"arg": "sqft", "type": "float", "question": "Total Building Area (SQFT)?", "default_from_project": True}
        ]
    },
    "default_pumps": {
        "function": "default_calculate_pump_metrics",
        "prompts": [
            {"arg": "project_connected_kva", "type": "float", "question": "Estimated Total Project Connected KVA (for 5% rule)?"},
            {"arg": "system_voltage", "type": "int", "question": "System Voltage?", "default_from_project": True}
        ]
    },

    # --- LIGHTING ---
    "lighting": {
        "function": "calculate_lighting_metrics",
        "prompts": [
             {"arg": "room_list", "type": "list_dict", "question": "Enter list of rooms (e.g., [{'name': 'Office 101', 'sqft': 150}])"},
             {"arg": "system_voltage", "type": "int", "question": "Lighting Voltage (e.g. 277)?", "default": 277},
             {"arg": "phase", "type": "int", "question": "Phase (1 or 3)?", "default": 3}
        ]
    },
    "default_lighting": {
        "function": "default_calculate_lighting_metrics",
        "prompts": [
             {"arg": "sqft", "type": "float", "question": "Total Area (SQFT)?", "default_from_project": True},
             {"arg": "building_type", "type": "str", "question": "Building Type (office, hospital, warehouse, garage, retail, dwelling)?", "default": "office"},
             {"arg": "voltage", "type": "int", "question": "Voltage?", "default_from_project": True},
             {"arg": "phase", "type": "int", "question": "Phase?", "default": 3}
        ]
    },

    # --- RECEPTACLES ---
    "receptacles": {
        "function": "calculate_receptacle_metrics",
        "prompts": [
             {"arg": "input_data", "type": "list_dict", "question": "Enter list of rooms (e.g. [{'name': 'Office', 'sqft': 100}]) OR total count (int)? "},
             {"arg": "system_voltage", "type": "int", "question": "Voltage (e.g. 120)?", "default": 120},
             {"arg": "phase", "type": "int", "question": "Phase?", "default": 3}
        ]
    },
    "default_receptacles": {
        "function": "default_calculate_receptacle_metrics",
        "prompts": [
             {"arg": "sqft", "type": "float", "question": "Total Area (SQFT)?", "default_from_project": True},
             {"arg": "building_type", "type": "str", "question": "Building Type?", "default": "office"},
             {"arg": "voltage", "type": "int", "question": "Voltage?", "default_from_project": True},
             {"arg": "phase", "type": "int", "question": "Phase?", "default": 3}
        ]
    },

    # --- KITCHEN ---
    "kitchen": {
        "function": "calculate_commercial_kitchen_metrics",
        "prompts": [
            {"arg": "equipment_list", "type": "list_dict", "question": "Enter kitchen equipment (e.g., [{'name': 'Oven', 'amps': 30, 'voltage': 208}])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 208},
            {"arg": "sqft", "type": "float", "question": "Kitchen Area?", "default": 1000}
        ]
    },
    "default_kitchen": {
        "function": "default_calculate_commercial_kitchen_metrics",
        "prompts": [
            {"arg": "kitchen_sqft", "type": "float", "question": "Kitchen SQFT?"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 208},
            {"arg": "phase", "type": "int", "question": "Phase?", "default": 3}
        ]
    },

    # --- EV CHARGING ---
    "ev_charging": {
        "function": "calculate_ev_metrics",
        "prompts": [
            {"arg": "charger_list", "type": "list_dict", "question": "Enter EV chargers (e.g. [{'name': 'EV-1', 'amps': 40}])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 208},
            {"arg": "sqft", "type": "float", "question": "Building SQFT?", "default_from_project": True},
            {"arg": "ems_limit_amps", "type": "float", "question": "EMS Limit Amps (Optional/0)?", "default": 0}
        ]
    },
    "default_ev_charging": {
        "function": "default_calculate_ev_metrics",
        "prompts": [
            {"arg": "num_level2", "type": "int", "question": "Number of Level 2 Chargers?"},
            {"arg": "num_fast", "type": "int", "question": "Number of DC Fast Chargers?"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 208}
        ]
    },

    # --- IMAGING ---
    "imaging": {
        "function": "calculate_imaging_metrics",
        "prompts": [
            {"arg": "equipment_list", "type": "list_dict", "question": "Enter Imaging Gear (e.g. [{'name': 'CT', 'amps': 100, 'type': 'medical_xray'}])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 480},
            {"arg": "sqft", "type": "float", "question": "Suite SQFT?", "default": 2000}
        ]
    },
    "default_imaging": {
        "function": "default_calculate_imaging_metrics",
        "prompts": [
            {"arg": "num_mri", "type": "int", "question": "Count of MRIs?"},
            {"arg": "num_ct", "type": "int", "question": "Count of CT Scanners?"},
            {"arg": "num_xray", "type": "int", "question": "Count of X-Ray Rooms?"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 480}
        ]
    },

    # --- DATA CENTER ---
    "data_center": {
        "function": "calculate_data_center_metrics",
        "prompts": [
            {"arg": "equipment_list", "type": "list_dict", "question": "Enter equipment (e.g. [{'name': 'UPS Input', 'amps': 300, 'voltage': 480}])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 480},
            {"arg": "sqft", "type": "float", "question": "White Space SQFT?", "default": 5000}
        ]
    },
    "default_data_center": {
        "function": "default_calculate_data_center_metrics",
        "prompts": [
            {"arg": "dc_sqft", "type": "float", "question": "Data Hall SQFT?"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 480}
        ]
    },

    # --- FIRE ALARM ---
    "fire_alarm": {
        "function": "calculate_fire_alarm_metrics",
        "prompts": [
            {"arg": "device_amps", "type": "list_float", "question": "List of panel amps (e.g., [5.0, 2.0])?"},
            {"arg": "voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True},
            {"arg": "phase", "type": "int", "question": "Phase?", "default": 1}
        ]
    },
    "default_fire_alarm": {
        "function": "default_calculate_fire_alarm_metrics",
        "prompts": [
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "phase", "type": "int", "question": "Phase?", "default": 1}
        ]
    },

    # --- IT SYSTEMS ---
    "it_systems": {
        "function": "calculate_it_system_metrics",
        "prompts": [
            {"arg": "device_amps", "type": "list_float", "question": "List of rack amps?"},
            {"arg": "voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True},
            {"arg": "phase", "type": "int", "question": "Phase?", "default": 1}
        ]
    },
    "default_it_systems": {
        "function": "default_calculate_it_system_metrics",
        "prompts": [
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "phase", "type": "int", "question": "Phase?", "default": 1}
        ]
    },

    # --- SIGNAGE ---
    "signage": {
        "function": "calculate_sign_lighting_metrics",
        "prompts": [
            {"arg": "sign_list", "type": "list_dict", "question": "Specific Signs (e.g. [{'name': 'Pylon', 'amps': 20}])?"},
            {"arg": "required_outlets_count", "type": "int", "question": "Extra Required Outlets (1200VA each)?", "default": 1},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True},
            {"arg": "phase", "type": "int", "question": "Phase?", "default": 1}
        ]
    },
    "default_signage": {
        "function": "default_calculate_sign_lighting_metrics",
        "prompts": [
            {"arg": "num_entrances", "type": "int", "question": "Number of Entrances/Exits?"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True}
        ]
    },

    # --- WATER HEATERS ---
    "water_heaters": {
        "function": "calculate_water_heater_metrics",
        "prompts": [
            {"arg": "heater_list", "type": "list_dict", "question": "List of Heaters (e.g. [{'name': 'WH-1', 'amps': 15, 'voltage': 480, 'phase': 3}])"},
            {"arg": "system_voltage", "type": "int", "question": "Main Voltage?", "default": 480},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True}
        ]
    },

    # --- ELECTRIC HEATING ---
    "electric_heating": {
        "function": "calculate_electric_heating_metrics",
        "prompts": [
            {"arg": "heater_list", "type": "list_dict", "question": "List of Heaters (e.g. [{'name': 'UH-1', 'amps': 10}])"},
            {"arg": "system_voltage", "type": "int", "question": "Main Voltage?", "default": 480},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True}
        ]
    },

    # --- MULTIOUTLET ---
    "multioutlet": {
        "function": "calculate_multioutlet_metrics",
        "prompts": [
            {"arg": "strip_lengths_ft", "type": "list_float", "question": "List of strip lengths in feet per strip (e.g. [6.0, 6.0])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 120},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True},
            {"arg": "simultaneous_usage", "type": "int", "question": "Simultaneous Usage? (1=True, 0=False)", "default": 0} 
            # Note: Arg type is bool in function, but parser handles int->bool easily or we adjust interface type casting. 
            # interface.py currently supports: int, float, list_float, list_dict, str.
            # I'll stick to int 0/1 for now and can ensure interface casts it if needed, or update interface to support 'bool'.
        ]
    },

    # --- WELDERS ---
    "welders": {
        "function": "calculate_welder_metrics",
        "prompts": [
            {"arg": "welder_list", "type": "list_dict", "question": "List of Welders (e.g. [{'name': 'MIG', 'amps': 50, 'duty_cycle': 60}])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 480},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True}
        ]
    },

    # --- MACHINE SHOP ---
    "machine_shop": {
        "function": "calculate_machine_shop_metrics",
        "prompts": [
            {"arg": "machine_list", "type": "list_dict", "question": "List of Machines (e.g. [{'name': 'Lathe', 'amps': 10}])"},
            {"arg": "system_voltage", "type": "int", "question": "Voltage?", "default": 480},
            {"arg": "sqft", "type": "float", "question": "Area?", "default_from_project": True}
        ]
    }
}
