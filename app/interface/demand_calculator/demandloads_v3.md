# Demand Load Calculations (Version 3)

This technical reference details the specific implementations of all loan calculation functions in `main.py`.

## 1. Transportation

### Elevators
- **Function**: `calculate_elevator_metrics`
- **Inputs**:
  - `elevator_amps` (List[float]): A list of the Full Load Amps (FLA) for each elevator motor.
  - `voltage` (int): System voltage (e.g., 480).
  - `sqft` (float): Building area for density metrics.
  - `phase` (int, default=3): Electrical phase (1 or 3).
- **Unique Outputs**: None (Returns *Typical Output*).
- **Logic**: NEC 620.14. Sum of all connected motors + 25% of the single largest motor, multiplied by a demand factor based on the count of elevators.
- **AI Instruction / Usage**:
  ```python
  # Calculate for bank of 3 elevators (50A each) at 480V
  result = calculate_elevator_metrics([50, 50, 50], voltage=480, sqft=50000)
  ```

---

## 2. Mechanical & Plumbing

### HVAC
- **Function**: `calculate_hvac_feeder_demand`
- **Inputs**:
  - `hvac_list` (List[Dict]):
    - `name` (str): ID of unit.
    - `amps` (float): Rated amps.
    - `type` (str): 'cooling', 'heating', or 'continuous'.
    - `is_motor` (bool): True if load is a motor (compressor/fan) for 25% sizing rule.
  - `system_voltage` (int): Main feeder voltage.
  - `sqft` (float): Building area.
- **Unique Outputs**:
  - `Scenario Used` (str): Indicates whether "Cooling" or "Heating" was the dominant load.
- **Logic**: NEC 440.33. Separates loads into Cooling and Heating groups. Adds "Continuous" loads to both. Applies 25% motor factor to the largest motor in each group. Compares totals and selects the larger scenario.
- **AI Instruction / Usage**:
  ```python
  hvac_data = [
      {"name": "RTU-1", "amps": 45, "type": "cooling", "is_motor": True},
      {"name": "Heat-1", "amps": 20, "type": "heating", "is_motor": False}
  ]
  metrics = calculate_hvac_feeder_demand(hvac_data, system_voltage=480, sqft=25000)
  ```

### Pumps
- **Function**: `calculate_pump_metrics`
- **Inputs**:
  - `pump_list` (List[Dict]):
    - `amps` (float): Nameplate amps.
    - `is_standby` (bool): If True, excluded from Demand Load.
  - `system_voltage` (int): Main feeder voltage.
  - `sqft` (float): Building area.
- **Unique Outputs**: None.
- **Logic**: NEC 430.24. Demand = Sum of non-standby motors + 25% of separate largest non-standby motor.
- **AI Instruction / Usage**:
  ```python
  pumps = [
      {"name": "P-1", "amps": 10, "is_standby": False},
      {"name": "P-2", "amps": 10, "is_standby": True}
  ]
  metrics = calculate_pump_metrics(pumps, system_voltage=480, sqft=50000)
  ```

---

## 3. General Power

### Lighting
- **Function**: `calculate_lighting_metrics`
- **Inputs**:
  - `sqft` (float): Area size.
  - `to_type` (str): Occupancy type ('hospital', 'warehouse', 'office', 'school').
  - `voltage` (int): System voltage.
  - `phase` (int, default=1): Phase.
- **Unique Outputs**: None.
- **Logic**: NEC 220.12 (Density) & 220.42 (Sliding Scale Factors). Connected Load determined by density table. Demand Factor applied based on occupancy rules.
- **AI Instruction / Usage**:
  ```python
  # Calculate 50k sqft Office Lighting
  res = calculate_lighting_metrics(50000, "office", voltage=480, phase=3)
  ```

### Receptacles
- **Function**: `calculate_receptacle_metrics`
- **Inputs**:
  - `sqft` (float): Area size.
  - `to_type` (str): Occupancy type (determines density).
  - `voltage` (int): System voltage.
  - `phase` (int, default=1): Phase.
- **Unique Outputs**: None.
- **Logic**: NEC 220.14(K) & 220.44. First 10 kVA at 100%, Remainder at 50%.
- **AI Instruction / Usage**:
  ```python
  res = calculate_receptacle_metrics(50000, "office", voltage=208, phase=3)
  ```

### Commercial Kitchen
- **Function**: `calculate_commercial_kitchen_metrics`
- **Inputs**:
  - `equipment_list` (List[Dict]): [{"amps": float, "voltage": int, "phase": int}].
  - `system_voltage` (int): Main feeder voltage.
  - `sqft` (float): For density only.
- **Unique Outputs**:
  - `Note` (str): Explains if Table 220.56 or the "Two Largest" override was used.
- **Logic**: NEC 220.56. Demand Factor scales with count (100% down to 65%). Results capped at minimum of Sum(Two Largest Loads).
- **AI Instruction / Usage**:
  ```python
  kitchen = [{"name": "Oven", "amps": 30}, {"name": "Fryer", "amps": 15}]
  res = calculate_commercial_kitchen_metrics(kitchen, system_voltage=208, sqft=1000)
  ```

---

## 4. Specialized

### EV Charging
- **Function**: `calculate_ev_metrics`
- **Inputs**:
  - `charger_list` (List[Dict]): [{"amps": float, "voltage": int, "phase": int}].
  - `system_voltage` (int): Main feeder voltage.
  - `ems_limit_amps` (Optional[float]): Max amps allowed by EMS.
- **Unique Outputs**: None.
- **Logic**: NEC 625. If `ems_limit_amps` is provided, Demand Load is clamped to that limit. Otherwise 100%.
- **AI Instruction / Usage**:
  ```python
  # 4 Chargers with 100A EMS Limit
  evs = [{"amps": 40} for _ in range(4)]
  res = calculate_ev_metrics(evs, system_voltage=208, ems_limit_amps=100)
  ```

### Medical Imaging
- **Function**: `calculate_imaging_metrics`
- **Inputs**:
  - `equipment_list` (List[Dict]):
    - `amps` (float): Momentary rating.
    - `type` (str): 'medical_xray', 'industrial_xray', or 'other'.
- **Unique Outputs**:
  - `Note` (str): Details the mix of factors applied.
- **Logic**: NEC 517.73. Medical X-Ray: 50% / 25% / 10%. Industrial: 100% / 100% / 20%. Other: 100%.
- **AI Instruction / Usage**:
  ```python
  gear = [{"name": "CT", "amps": 100, "type": "medical_xray"}]
  res = calculate_imaging_metrics(gear, system_voltage=480)
  ```

### Data Center
- **Function**: `calculate_data_center_metrics`
- **Inputs**:
  - `equipment_list` (List[Dict]): Normal equipment dict.
  - `sqft` (float): White space area.
- **Unique Outputs**: None.
- **Logic**: NEC 645.10. 100% Connected Load. No diversity.
- **AI Instruction / Usage**:
  ```python
  ups = [{"name": "UPS Input", "amps": 400}]
  res = calculate_data_center_metrics(ups, system_voltage=480, sqft=5000)
  ```

---

## 5. Other Load Types

### Fire Alarm / IT / Telecom / Electric Heating / Water Heaters
- **Functions**: `calculate_fire_alarm_metrics`, `calculate_it_system_metrics`, `calculate_electric_heating_metrics`, `calculate_water_heater_metrics`.
- **Inputs**: Standard List[Dict] of equipment (Amps/Volts/Phase).
- **Unique Outputs**: None.
- **Logic**: All calculated at **100% Demand Factor**. 1.25 continuous duty multiplier is explicitly excluded per instructions.

### Signage
- **Function**: `calculate_sign_lighting_metrics`
- **Inputs**:
  - `sign_list` (List[Dict]): Specific signs.
  - `required_outlets_count` (int): Extra placeholder outlets.
- **Logic**: NEC 220.14(F). Each outlet calculated at Max(Actual, 1200 VA).

### Multioutlet Assemblies
- **Function**: `calculate_multioutlet_metrics`
- **Inputs**:
  - `strip_lengths_ft` (List[float]): Length of each strip.
  - `simultaneous_usage` (bool): True = 180VA/1ft, False = 180VA/5ft.
- **Logic**: NEC 220.14(H). Usage mode determines Connected Load. First 10kVA of total is 100%, remainder is 50%.

---

## Appendix: Typical Output Dictionary
Unless otherwise noted as "**Unique Outputs**", every function returns a dictionary with this standard structure. This allows for uniform table generation in the UI.

| Key | Type | Description |
| :--- | :--- | :--- |
| `Connected Load in kva` | Float | The total installed capacity sum. |
| `Connected Volt-Amps/SQFT` | Float | Connected Load divided by SQFT. |
| `demand factor` | String | A quantitative (e.g., "0.90") or descriptive (e.g., "First 10kVA @ 100%") string explaining the reduction. |
| `Demand Load in kva` | Float | The calculated load used for sizing feeders and service. |
| `Demand Volt-Amps/SQFT` | Float | Demand Load divided by SQFT. |
| `demand FLA` | Float | Full Load Amps of the Demand Load at the specified `system_voltage`. |
