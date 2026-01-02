##STEP 1
every function will have a function_name and a default_function_name 
first update the existing functions that will actually be the "default" counter part.

Exisitng functions apply the new function name where you see **new_Function_name**:

### Elevators
- **Function**: `calculate_elevator_metrics`

### HVAC
- **Function**: `calculate_hvac_feeder_demand`

### Pumps
- **Function**: `calculate_pump_metrics`

### Lighting
- **Function**: `calculate_lighting_metrics`
- **new_Function_name**: `default_calculate_lighting_metrics`

### Receptacles
- **Function**: `calculate_receptacle_metrics`
- **new_Function_name**: `default_calculate_receptacle_metrics`

### Commercial Kitchen
- **Function**: `calculate_commercial_kitchen_metrics`

### EV Charging
- **Function**: `calculate_ev_metrics`

### Medical Imaging
- **Function**: `calculate_imaging_metrics`

### Data Center
- **Function**: `calculate_data_center_metrics`

### Fire Alarm / IT / Telecom / Electric Heating / Water Heaters
- **Functions**: `calculate_fire_alarm_metrics`, `calculate_it_system_metrics`, `calculate_electric_heating_metrics`, `calculate_water_heater_metrics`.

### Signage
- **Function**: `calculate_sign_lighting_metrics`

### Multioutlet Assemblies
- **Function**: `calculate_multioutlet_metrics`



##STEP 2

create new functions for Default Calculations:

### Elevators 
- **Function**: `default_calculate_elevator_metrics`
**Default calculation**: 50 Amps per elevator, 2-story building has 1 elevator, 20-story has 10 elevators
**Default Inputs Required**: `Number of Building floors`

### HVAC
- **Function**: `default_calculate_hvac_feeder_demand`
**Default calculation**:  hvac_density_table provides the density in voltsamps per sqft.
hvac_density_table = {
    'office': 7.0,      # Std: 350 sqft/ton + Ventilation
    'bank': 7.0,        # Similar to Office
    'school': 6.0,      # Std: 300-400 sqft/ton, seasonal usage
    'college': 7.0,     # Higher density labs/classrooms
    'medical': 14.0,    # Hospital: High air changes (100% OA), ~150 sqft/ton
    'clinic': 9.0,      # Outpatient: Less intense than hospital
    'warehouse': 2.0,   # Very low density (often heating only or spot cool)
    'storage': 1.0,     # Minimal freeze protection/ventilation
    'retail': 6.5,      # High occupancy + door infiltration
    'corridor': 2.0,    # Spillover conditioning usually
    'industrial': 6.0,  # Baseline factory HVAC (excludes process loads)
    'restaurant': 12.0  # (Added) High Make-Up Air requirements for kitchen hoods
}
**Default Inputs Required**: occupancy type, sqft

### Pumps
- **Function**: `default_calculate_pump_metrics`
**Default calculation**: 5% of Total Load. 
**Default Inputs Required**: None

### Commercial Kitchen
- **Function**: `default_calculate_commercial_kitchen_metrics`
**Default calculation**: 50 watts per sqft
**Default Inputs Required**: Total kitchen only sqft

### EV Charging
- **Function**: `default_calculate_ev_metrics`
**Default calculation**: function that will calculate "number of level 2 ev's" at 7.2kva and "number of fast chargers" at 50kva
**Default Inputs Required**: input("number of level 2 ev's", "number of fast chargers")

### Medical Imaging
- **Function**: `default_calculate_imaging_metrics`
**Default calculation**: MRI: 100kva, CT: 70kva, XRAY: 20kva    
**Default Inputs Required**: input("number of MRI units", "number of CT units", "number of XRAY units")

### Data Center
- **Function**: `default_calculate_data_center_metrics`
**Default calculation**: 300 watts per sqft
**Default Inputs Required**: Total data center only sqft

### Fire Alarm / IT / Telecom 
- **Function**: `default_calculate_fire_alarm_metrics`, `default_calculate_it_system_metrics`
**Default calculation**: 0.5 Volt-Amps per sqft
**Default Inputs Required**: Total building sqft

### Signage
- **Function**: `default_calculate_sign_lighting_metrics`
**Default calculation**: 1200VA per sign, 1 sign per entrance
**Default Inputs Required**: Total number of entrances


##STEP 3
if you completed step 1 we shouldnt have any of these function names so we will make the following new functions:


### Lighting
- **Function**: `calculate_lighting_metrics`
**Default calculation**:[list of rooms] has room name and sqft associated with each room then use the associated information in lighting_hospital_data.py to calculate the total VA from the user input sqft * the VA / sqft for that room type. 
**Default Inputs Required**: the user must provide [list of rooms] with room name and sqft associated with each room.

### Receptacles
- **Function**: `calculate_receptacle_metrics`
**Default calculation**: if [list of rooms] has room name and sqft associated with each room then use the associated information in receptacle_hospital_data.py to calculate the total VA from the user input sqft * the VA / sqft for that room type. 
else if [list of rooms] has room name and no sqft. use the room name and fond the minimum number of receptacle associated wiht each room in the list and multiply that by 90VA.
else the user will provide the total number of receptacles and we calculate using 90VA * total number of receptacles. 
**Default Inputs Required**: the user must either provide the [list of rooms] or the total number of receptacles.

the functions must opporate and return the values as necessary to be able to populate the demand load as the other functions do now. 