Part A. System Architecture & Calculator Mapping

The system uses a `calculator` keyword to interface with external Python scripts located in specific directories. The chat interface routes these keywords to the appropriate calculator module.

**Calculator Mapping:**
- `calculator.demand` -> `calculator_demandcalcs` (The Demand Load Calculator)
- `calculator.voltage_drop` -> `calculator_voltagedrop` (The Voltage Drop Calculator)
- *Additional calculators will follow this pattern.*

**Architecture Overview:**
The `calculator_demandcalcs` (and others) are designed to calculate specific metrics, generate formatted tables, and store final results in temporary storage for user export.

The chat interface is dynamic. Specific keywords trigger the corresponding calculator functions.

**Interaction Model:**
The user initiates interactions using the `calculator` namespace:
`calculator.demand`, `calculator.voltage_drop`, etc.

Part B. Usage, Syntax, and Input Parsing

The system is designed for deterministic execution triggered by specific string patterns.
**Core Command Pattern:**
`calculator.demand[instance_name, function_list]`

**Parameters:**
1.  `instance_name` (string): A unique identifier for the calculation session (e.g., "ProjectAlpha_Building1"). This key is used to store and retrieve the temporary state.
2.  `function_list` (list of strings/objects): A list of specific calculation modules to execute.

**Example Calls:**
- `calculator.demand["Hospital_Wing_A", ["lighting", "receptacles", "hvac", "elevators"]]`
- `calculator.demand["Office_Complex", ["default_lighting", "default_receptacles"]]`

**Behavior:**
- If `function_list` is provided, the system iterates through each item, prompting the user for the specific inputs required by that function.
- If `instance_name` is new, a new state object is created.
- If `instance_name` exists, `function_list` appends to the existing report.

Part C. Detailed Execution Plan & Function Contracts

The agent must parse the `function_list` and execute the corresponding Python functions from `calculator_demandcalcs.main`.
**Strict Rule:** Do not hallucinate arguments. You must ask the user for the exact arguments required by the function signatures below.

### 1. Elevators
- **User Keyword**: `elevators`
- **Function**: `calculate_elevator_metrics`
- **Required Inputs**:
    - `elevator_amps` (List[float]): "Enter the FLA for each elevator (e.g., [24.5, 24.5, 40])."
    - `voltage` (int): "System voltage?"
    - `sqft` (float): "Building SQFT?"
    - `phase` (int): "Phase (1 or 3)?"

### 2. HVAC (Standard & Default)
- **User Keyword**: `hvac`
- **Function**: `calculate_hvac_feeder_demand`
- **Required Inputs**:
    - `equipment_list` (List[Dict]): A list of objects. For each item ask:
        - `name` (str)
        - `amps` (float)
        - `voltage` (int)
        - `phase` (int)
        - `type` (str: 'cooling', 'heating', 'continuous')
        - `is_motor` (bool)
    - `system_voltage` (int)
    - `sqft` (float)

### 3. Pumps / Motors
- **User Keyword**: `pumps`
- **Function**: `calculate_pump_metrics`
- **Required Inputs**:
    - `pump_list` (List[Dict]): For each pump ask:
        - `name`, `amps`, `voltage`, `phase`, `is_standby` (bool)
    - `system_voltage` (int)
    - `sqft` (float)

### 4. Lighting (Detailed vs Default)
**Choice A: Detailed**
- **User Keyword**: `lighting`
- **Function**: `calculate_lighting_metrics` (Requires `lighting_hospital_data.py`)
- **Required Inputs**:
    - `room_counts` (Dict[str, int]): Map of {RoomType: Quantity}
    - `voltage` (int)
    - `sqft` (float)

**Choice B: Default (USE THIS for estimations)**
- **User Keyword**: `default_lighting`
- **Function**: `default_calculate_lighting_metrics`
- **Required Inputs**:
    - `sqft` (float)
    - `building_type` (str): 'office', 'hospital', 'school', etc.
    - `voltage` (int)
    - `phase` (int)

### 5. Receptacles (Detailed vs Default)
**Choice A: Detailed**
- **User Keyword**: `receptacles`
- **Function**: `calculate_receptacle_metrics`
- **Required Inputs**:
    - `room_counts` (Dict[str, int])
    - `voltage` (int)
    - `sqft` (float)

**Choice B: Default**
- **User Keyword**: `default_receptacles`
- **Function**: `default_calculate_receptacle_metrics`
- **Required Inputs**:
    - `sqft` (float)
    - `building_type` (str)
    - `voltage` (int)
    - `phase` (int)

### 6. Fire Alarm / IT / Telecom
- **User Keywords**: `fire_alarm`, `it_systems`
- **Functions**: `calculate_fire_alarm_metrics`, `calculate_it_system_metrics`
- **Required Inputs**:
    - `device_amps` (List[float])
    - `voltage` (int)
    - `sqft` (float)
    - `phase` (int)

Part D. State Management & Export

**State Object:**
The system maintains a temporary JSON structure for the active `instance_name`.
```json
{
  "instance_name": "ProjectAlpha",
  "created_at": "timestamp",
  "rows": [
    { "description": "Lighting", "connected_kva": 45.5, ... },
    { "description": "Elevators", "connected_kva": 120.0, ... }
  ]
}
```

**Exporting:**
When the user executes `calculator.demand[instance_name].rlf_export`, the system:
1.  Retrieves the state object for `instance_name`.
2.  Formats the `rows` into a CSV or formatted Table.
3.  Saves the artifact to `User Documents/Exporters/`.
4.  Returns the file path to the user.

**Step-By-Step Execution Flow:**
1.  **Parse**: Extract `instance_name` and `function_list` from the prompt.
2.  **Initialize**: Check if instance exists; if not, create new `ElectricalLoadSchedule` class instance (from `main.py`).
3.  **Iterate**: For each item in `function_list`:
    a. Check `main.py` for the mapping (e.g., "hvac" -> `calculate_hvac_feeder_demand`).
    b. **Prompt**: specific questions to satisfy the function arguments.
    c. **Execute**: Run the Python function with the gathered inputs.
    d. **Update**: Call `ElectricalLoadSchedule.add_load()` with the result.
4.  **Confirm**: Show the current sub-total or added row to the user.
5.  **Await**: Wait for next command or `.rlf_export` trigger.