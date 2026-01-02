The rag ai chat agent need to be able to call certain functions and python scripts. We need to create a way for the user to have session memory so that the user can write to memory when talking with the ai chat. 

The specific word that will be used to call the functions and python scripts is `calculator`

We will have different features associated with our chat interface and the calls the user can make. Lets start with the first the demand calculator. 

This demand calculator lives in the calculator_demandcalcs folder. We want the user to be able to follow this type of flow:

User: calculator.demand[name, list_of_functions, sqft] 

User: calculator.demand[my_new_instance, [elevators, fire_alarm], 50000]

the new instance is the name of this workspace. however the list of functions require the user to fill in the necessary information to complete the calculation. the sqft is the total square footage of the building, this is a global variable that is set with the iniial instance creation and is used wherever necessary

In our scenario once the user presses enter, the new instance is created `my_new_instance`. The user is prompted with "Your new workspace is created: `my_new_instance`". and then the user is prompted with the format of the information that needs to be filled in, in this case the user is prompted with the elevator format since it was the first element in the list. 

AI: Enter elevator data:
    
    Example entries:

    elevator[[amps,amps,amp],voltage,phase] | elevator[[100, 40, 50], 480, 3]
   
    1. elevator 100A at 480V, 3 phase
    2. elevator 40A at 480V, 3 phase
    3. elevator 50A at 480V, 3 phase

User: levator[[100, 40, 50], 480, 3]

once the user presse enter the information is properly stored to be used in our load table and the next element from our list propmpts the user to fill in the information necessary to complete the calculation.

AI: Enter fire_alarm data:
    
    Example entries:

    fire_alarm[[amps,amps,amp],voltage,phase] | fire_alarm[[10 , 12], 120, 1]

    1. fire_alarm 10A at 120V, 1 phase
    2. fire_alarm 12A at 120V, 1 phase

Once the user presses enter the information is properly stored to be used in our load table and the next element from our list propmpts the user to fill in the information necessary to complete the calculation.

if all is done the information is stored and nothing wlse happens. for the user to export the information they will need to use the export command. and this will export the final demand load table.

the export command will look like this:

User: demand.my_new_instance.export()

this will export the information to a csv file in the user's current directory.


Here is the breakdown of the final functions their respective calculator functions and the input parameters with the example ai prompts:


### Elevators
elevator - `calculate_elevator_metrics`

AI: Enter elevator data:
    
    Example entries:

    elevator[[amps,amps,amp],voltage,phase] | elevator[[100, 40, 50], 480, 3] 
    is equal to:
    1. elevator 100A at 480V, 3 phase
    2. elevator 40A at 480V, 3 phase
    3. elevator 50A at 480V, 3 phase

Example user input:
User: levator[[100, 40, 50], 480, 3]

default_elevator - `default_calculate_elevator_metrics`

AI: Enter default elevator data:
    
    Example entries:

    default_elevator[floors] | default_elevator[3]
    
    one elevator 50A at 480V, 3 phase is added for every two floors.

Example user input:
User: default_elevator[3]

### HVAC
hvac - `calculate_hvac_feeder_demand`

AI: Enter HVAC data:
    
    Example entries:

    Format: hvac[[[amps, voltage, phase, "type"], ...], system_voltage, sqft]

    hvac[[[100, 480, 3, "cool"], [40, 480, 3, "heat"], [10, 480, 3, "fan"]], 480, 25000]
   
    1. Equipment: 100A Cooling (480V/3ph), 40A Heating (480V/3ph), 10A Fan (480V/3ph)
    2. System Voltage: 480V
    3. Building Size: 25,000 SQFT

Example user input:
User: hvac[[
    [100, 480, 3, "cool"], 
    [40, 480, 3, "heat"], 
    [10, 480, 3, "fan"]], 
    480, 
    25000]

default_hvac - `default_calculate_hvac_feeder_demand`

AI: Enter HVAC data:
    
    Example entries:

    Format: default_hvac[occupancy_type, sqft, voltage, phase] | default_hvac["office", 10000, 480, 3]
    
    is equal to 
    1. Occupancy Type: "office" (Uses 7.0 VA/SQFT)
    2. Building Size: 10,000 SQFT
    3. System: 480V, 3 phase

    *Available types: office 7.0 va/sqft, bank 7.0 va/sqft, school 6.0 va/sqft, college 7.0 va/sqft, medical 14.0 va/sqft, clinic 9.0 va/sqft, warehouse 2.0 va/sqft, storage 1.0 va/sqft, retail 6.5 va/sqft, corridor 2.0 va/sqft, industrial 6.0 va/sqft, restaurant 12.0 va/sqft*

Example user input:
User: default_hvac["office", 10000, 480, 3]


### Pumps
pumps - `calculate_pump_metrics`

AI: Enter Pumps data:
    
    Example entries:

    Format: pumps[[[amps, voltage, phase, is_standby (true/false)], ...], system_voltage, sqft]

    pumps[[[15, 480, 3, false], [15, 480, 3, true], [5, 120, 1, false]], 480, 15000]
    is equal to 
    1. Primary Pump: 15A (480V/3ph) - Active
    2. Standby Pump: 15A (480V/3ph) - Standby/Lag (Excluded from Demand)
    3. Circ Pump: 5A (120V/1ph) - Active
    4. System Voltage: 480V
    5. Building Size: 15,000 SQFT

Example user input:
User: pumps[[
    [15, 480, 3, false], 
    [15, 480, 3, true], 
    [5, 120, 1, false]], 
    480, 
    15000]


default_pump - `default_calculate_pump_metrics`

AI: Enter Pumps data:
    
    Example entries:

    Format: default_pumps[total_kva, voltage] | default_pumps[500, 480]
    is equal to 
    1. Total Project Load: 500 kVA
    2. System Voltage: 480V
    3. Calculation: Establishes Pump Load as 5% of Total (25 kVA)

    *Note: This estimation requires the total building load to be known or estimated beforehand.*

Example user input:
User: default_pumps[500, 480]

### Lighting
lighting - `calculate_lighting_metrics`

AI: Enter Lighting data:
    
    Example entries:

    Format: lighting[[["Room Name", sqft], ...], system_voltage, phase]

    lighting[[["Patient Room", 250], ["Operating Room", 600], ["Corridor", 1000]], 277, 3]
    is equal to 
    1. Room 1: "Patient Room", 250 SQFT (Lookup uses name for VA density)
    2. Room 2: "Operating Room", 600 SQFT
    3. Room 3: "Corridor", 1000 SQFT
    4. System: 277V, 3 phase
    *Note: The calculation applies NEC Hospital demand factors (40% of first 50kVA, 20% of remainder).*
    *Room Classification (FGI / NFPA 99)

    Airborne Infection Isolation (AII) Room — Essential (Category 2)
    Medical/Surgical Unit Patient Room — Essential (Category 2)
    Protective Environment Room — Essential (Category 2)
    Intermediate Care Unit Patient Room — Essential (Category 2)
    Postpartum Unit Patient Room — Essential (Category 2)
    Pediatric and Adolescent Unit Patient Room — Essential (Category 2)
    Rehabilitation Unit Patient Room — Noncritical (Category 3)
    Intensive Care Unit (ICU) Patient Care Station — Critical (Category 1)
    Pediatric Intensive Care Unit (PICU) Patient Room — Critical (Category 1)
    Neonatal Intensive Care Unit (NICU) Infant Care Station — Critical (Category 1)
    Labor/Delivery/Recovery (LDR) and LDRP Room — Critical (Category 1)
    Hospice and/or Palliative Care Room — Noncritical (Category 3)
    Newborn Nursery Infant Care Station — Essential (Category 2)
    Continuing Care Nursery Infant Care Station — Essential (Category 2)
    Behavioral and Mental Health Patient Bedroom — Noncritical (Category 3)
    Exam Room / Class 1 Imaging Room — Essential (Category 2)
    Cesarean Delivery Room — Critical (Category 1)
    Treatment Room for Basic Emergency Services — Essential (Category 2)
    Triage Room or Area in the Emergency Department — Essential (Category 2)
    Emergency Department Treatment Room — Critical (Category 1)
    Trauma/Resuscitation Room — Critical (Category 1)
    Low-Acuity Patient Treatment Station — Noncritical (Category 3)
    Interior Human Decontamination Room — Essential (Category 2)
    Observation Unit Patient Care Station — Essential (Category 2)
    Procedure Room (Including Endoscopy) Class 2 Imaging — Critical (Category 1)
    Operating Room / Class 3 Imaging Room — Critical (Category 1)
    Hemodialysis Patient Care Stations — Essential (Category 2)
    Phase I Post-Anesthetic Care Unit (PACU) Station — Critical (Category 1)
    Phase II Recovery Patient Care Station — Essential (Category 2)*

Example user input:
User: lighting[[["Patient Room", 250], ["Operating Room", 600], ["Corridor", 1000]], 277, 3]

*Available Room Types:

airborne infection isolation (aii) room

medical/surgical unit patient room

protective environment room

intermediate care unit patient room

postpartum unit patient room

pediatric and adolescent unit patient room

rehabilitation unit patient room

intensive care unit (icu) patient care station

pediatric intensive care unit (picu) patient room

neonatal intensive care unit (nicu) infant care station

labor/delivery/recovery (ldr) and ldrp room

hospice and/or palliative care room

newborn nursery infant care station

continuing care nursery infant care station

behavioral and mental health patient bedroom

exam room / class 1 imaging room

cesarean delivery room

treatment room for basic emergency services

triage room or area in the emergency department

emergency department treatment room

trauma/resuscitation room

low-acuity patient treatment station

interior human decontamination room

observation unit patient care station

procedure room (including endoscopy) class 2 imaging

operating room / class 3 imaging room

hemodialysis patient care stations

phase i post-anesthetic care unit (pacu) station

phase ii recovery patient care station
*

default_lighting - `default_calculate_lighting_metrics`

AI: Enter default lighting data:
    
    Example entries:

    Format: default_lighting[sqft, "type", voltage, phase] | lighting_lighting[50000, "hospital", 277, 3]
    
    is equal to 
    1. Building Size: 50,000 SQFT
    2. Occupancy Type: "hospital" (Determines NEC Density and Demand Factors)
    3. System: 277V, 3 phase

    *Available types: office 1.3 va/sqft, school 1.3 va/sqft, hospital 1.6 va/sqft, hotel 1.7 va/sqft, warehouse 0.6 va/sqft, garage 0.3 va/sqft, retail 1.9 va/sqft, dwelling 3.0 va/sqft, auditorium 0.7 va/sqft, restaurant 1.5 va/sqft, gym 0.8 va/sqft*

    *Calculates NEC 220.12 Density and NEC 220.42 Demand Factors automatically.*

Example user input:
User: default_lighting[50000, "hospital", 277, 3]

### Receptacles
receptacles - `calculate_receptacle_metrics`

AI: Enter receptacles data:
    
    Example entries:

    **Option 1: Detailed Room List**
    Format: receptacles[[["Room Name", sqft], ...], voltage, phase]
    
    receptacles[[["Office", 120], ["Conf Room", 0]], 120, 3]
    
    is equal to:
    1. "Office" (120 SQFT) -> Uses VA/SQFT density lookup.
    2. "Conf Room" (0 SQFT) -> Uses "Min Receptacles" count lookup * 90VA.
    3. System: 120V, 3 phase.

    **Option 2: Simple Total Count**
    Format: receptacles[total_count, voltage, phase]
    
    receptacles[50, 120, 3]
    
    is equal to:
    1. 50 Receptacles * 90VA = 4,500 VA Connected Load.
    2. System: 120V, 3 phase.

    *Note: Applies NEC 220.44 Demand Factors (First 10kVA @ 100%, Remainder @ 50%).*

    *Room Classification (FGI / NFPA 99)

    Airborne Infection Isolation (AII) Room — Essential (Category 2)
    Medical/Surgical Unit Patient Room — Essential (Category 2)
    Protective Environment Room — Essential (Category 2)
    Intermediate Care Unit Patient Room — Essential (Category 2)
    Postpartum Unit Patient Room — Essential (Category 2)
    Pediatric and Adolescent Unit Patient Room — Essential (Category 2)
    Rehabilitation Unit Patient Room — Noncritical (Category 3)
    Intensive Care Unit (ICU) Patient Care Station — Critical (Category 1)
    Pediatric Intensive Care Unit (PICU) Patient Room — Critical (Category 1)
    Neonatal Intensive Care Unit (NICU) Infant Care Station — Critical (Category 1)
    Labor/Delivery/Recovery (LDR) and LDRP Room — Critical (Category 1)
    Hospice and/or Palliative Care Room — Noncritical (Category 3)
    Newborn Nursery Infant Care Station — Essential (Category 2)
    Continuing Care Nursery Infant Care Station — Essential (Category 2)
    Behavioral and Mental Health Patient Bedroom — Noncritical (Category 3)
    Exam Room / Class 1 Imaging Room — Essential (Category 2)
    Cesarean Delivery Room — Critical (Category 1)
    Treatment Room for Basic Emergency Services — Essential (Category 2)
    Triage Room or Area in the Emergency Department — Essential (Category 2)
    Emergency Department Treatment Room — Critical (Category 1)
    Trauma/Resuscitation Room — Critical (Category 1)
    Low-Acuity Patient Treatment Station — Noncritical (Category 3)
    Interior Human Decontamination Room — Essential (Category 2)
    Observation Unit Patient Care Station — Essential (Category 2)
    Procedure Room (Including Endoscopy) Class 2 Imaging — Critical (Category 1)
    Operating Room / Class 3 Imaging Room — Critical (Category 1)
    Hemodialysis Patient Care Stations — Essential (Category 2)
    Phase I Post-Anesthetic Care Unit (PACU) Station — Critical (Category 1)
    Phase II Recovery Patient Care Station — Essential (Category 2)*

Example Option 1 user input:
User: receptacles[[
    ["Office", 120], 
    ["Conf Room", 0]], 
    120, 
    3]

Example Option 2 user input:
User: receptacles[50, 120, 3]

default_receptacles - `default_calculate_receptacle_metrics`

AI: Enter Receptacle data:
    
    Example entries:

    Format: default_receptacles[sqft, "type", voltage, phase] | default_receptacles[10000, "office", 208, 3]

    1. Building Size: 10,000 SQFT
    2. Occupancy Type: "office" (Uses 1.0 VA/SQFT per NEC 220.14(K))
    3. System: 208V, 3 phase

    *Available types: office 1.0 va/sqft, bank 1.0 va/sqft, school 1.0 va/sqft, college 1.0 va/sqft, medical 2.0 va/sqft, clinic 1.5 va/sqft, warehouse 0.25 va/sqft, storage 0.1 va/sqft, retail 0.5 va/sqft, corridor 0.1 va/sqft, industrial 1.5 va/sqft*

    *Automatically applies NEC 220.44 Demand Factors (First 10kVA @ 100%, Remainder @ 50%).*

Example user input:
User: default_receptacles[10000, "office", 208, 3]

### Commercial Kitchen
commercial_kitchen - `calculate_commercial_kitchen_metrics`

AI: Enter Commercial Kitchen data:
    Example entries:

    Format: commercial_kitchen[[[amps, voltage, phase, "name"], ...], system_voltage, sqft]

    commercial_kitchen[[[50, 208, 3, "Oven"], [30, 208, 3, "Fryer"], [20, 208, 1, "Booster"], [15, 120, 1, "Mixer"]], 208, 800]

    1. "Oven": 50A (208V/3ph)
    2. "Fryer": 30A (208V/3ph)
    3. "Booster": 20A (208V/1ph)
    4. "Mixer": 15A (120V/1ph)
    5. System: 208V, 800 SQFT

    *Note: Automatically applies NEC 220.56 logic (Table Demand Factors vs. Sum of 2 Largest Loads).*

Example user input:
User: commercial_kitchen[[
    [50, 208, 3, "Oven"], 
    [30, 208, 3, "Fryer"], 
    [20, 208, 1, "Booster"], 
    [15, 120, 1, "Mixer"]], 
    208, 
    800]

default_commercial_kitchen - `default_calculate_commercial_kitchen_metrics`

AI: Enter Commercial Kitchen data:

    Example entries:

    Format: default_commercial_kitchen[sqft, voltage, phase] | default_commercial_kitchen[800, 208, 3]

    1. Building Size: 800 SQFT
    2. System: 208V, 3 phase

    *Note: Automatically applies NEC 220.56 logic (Table Demand Factors vs. Sum of 2 Largest Loads).*

Example user input:
User: default_commercial_kitchen[800, 208, 3]

### EV Charging
ev - `calculate_ev_metrics`

AI: Enter EV data:
    Example entries:

    Format: ev[[[amps, voltage, phase, "name"], ...], system_voltage, sqft, ems_limit_amps]

    ev[[[40, 208, 1, "Station A"], [32, 208, 1, "Station B"]], 208, 0, 0]
    is equal to 
    1. "Station A": 40A (208V/1ph)
    2. "Station B": 32A (208V/1ph)
    3. System: 208V
    4. EMS Limit: None (0 indicates no limit; 100% Demand Factor applied per NEC 625.41).

    *Note: If `ems_limit_amps` is provided (e.g., 60), the total Demand Load is clamped to that value per NEC 625.42.*

Example user input:
User: ev[[[40, 208, 1, "Station A"], [32, 208, 1, "Station B"]], 208, 0, 0]

default_ev - `default_calculate_ev_metrics`

AI: Enter EV data:
    Example entries:

    Format: default_ev[num_level2, num_fast, voltage] | default_ev[5, 1, 480]

    1. Level 2 Chargers: 5 (Estimates 7.2 kVA each)
    2. Fast Chargers: 1 (Estimates 50 kVA each)
    3. System: 480V

    *Note: Assumes standard estimation values of 7.2 kVA for Level 2 and 50 kVA for DC Fast Chargers.*

Example user input:
User: default_ev[5, 1, 480]

### Medical Imaging
imaging - `calculate_imaging_metrics`

AI: Enter Medical Imaging data:
    Example entries:

    Format: imaging[[[amps, voltage, phase, "type", "name"], ...], system_voltage, sqft]

    imaging[[[100, 480, 3, "medical_xray", "CT Scan"], [50, 480, 3, "other", "MRI"], [20, 480, 3, "industrial_xray", "Scanner"]], 480, 10000]

    1. "CT Scan": 100A (Medical Type) -> Applies NEC 517.73 (50% Demand)
    2. "MRI": 50A (Other Type) -> Applies 100% Demand
    3. "Scanner": 20A (Industrial Type) -> Applies NEC 660.6 (100% for top 2)
    4. System: 480V, 10,000 SQFT

    *Available types: "medical_xray" (or "ct"), "industrial_xray", "other".*
    *Note: Critical to define the type to apply the correct NEC Demand Factors (50/25/10% for Medical vs 100/20% for Industrial).*

Example user input:
User: imaging[[[100, 480, 3, "medical_xray", "CT Scan"], [50, 480, 3, "other", "MRI"], [20, 480, 3, "industrial_xray", "Scanner"]], 480, 10000]

default_imaging - `default_calculate_imaging_metrics`

AI: Enter Medical Imaging data:
    Example entries:

    Format: default_imaging[num_mri, num_ct, num_xray, voltage] | default_imaging[1, 1, 2, 480]

    1. MRI Machines: 1 (Estimates 100 kVA each)
    2. CT Scanners: 1 (Estimates 70 kVA each)
    3. X-Ray Machines: 2 (Estimates 20 kVA each)
    4. System: 480V

    *Note: Uses standard engineering estimates (MRI=100kVA, CT=70kVA, XRay=20kVA) to determine the load.*

Example user input:
User: default_imaging[1, 1, 2, 480]

### Data Center
data_center - `calculate_data_center_metrics`

AI: Enter Data Center data:
    Example entries:

    Format: data_center[[[amps, voltage, phase, "name"], ...], system_voltage, sqft]

    data_center[[[400, 480, 3, "UPS-A Input"], [60, 480, 3, "CRAC-1"]], 480, 5000]

    1. "UPS-A Input": 400A (480V/3ph)
    2. "CRAC-1": 60A (480V/3ph)
    3. System: 480V, 5,000 SQFT

    *Note: Calculates at 100% Demand Factor per NEC 645.10 (No diversity permitted).*

Example user input:
User: data_center[[[400, 480, 3, "UPS-A Input"], [60, 480, 3, "CRAC-1"]], 480, 5000]

default_data_center - `default_calculate_data_center_metrics`

AI: Enter Data Center data:
    Example entries:

    Format: default_data_center[sqft, voltage] | datacenter_data_center[2000, 480]

    1. Data Center Size: 2,000 SQFT
    2. System: 480V
    3. Calculation: Uses a high-density estimation of 300 VA/SQFT.

Example user input:
User: datacenter_data_center[2000, 480]

### Fire Alarm / IT / Telecom / Electric Heating / Water Heaters
fire_alarm - `calculate_fire_alarm_metrics`

AI: Enter Fire Alarm data:
    Example entries:

    Format: fire_alarm[[amps, amps, ...], voltage, sqft, phase] | fire_alarm[[5.0, 2.5, 1.0], 120, 50000, 1]

    1. Device 1: 5.0A (e.g., Main FACP)
    2. Device 2: 2.5A (e.g., NAC Panel)
    3. Device 3: 1.0A (e.g., Annunciator)
    4. System: 120V, 1 phase, 50,000 SQFT

    *Note: Demand Factor is set to 100% (1.0) as Fire Alarm systems are considered continuous non-coincident loads without diversity.*

Example user input:
User: fire_alarm[[5.0, 2.5, 1.0], 120, 50000, 1]

it_system - `calculate_it_system_metrics`

AI: Enter IT System data:
    Example entries:

    Format: it_system[[amps, amps, ...], voltage, sqft, phase] | it_systems[[20.0, 16.0, 30.0], 120, 15000, 1]

    1. Device 1: 20.0A (e.g., IDF Rack 1)
    2. Device 2: 16.0A (e.g., Security Panel)
    3. Device 3: 30.0A (e.g., MDF UPS)
    4. System: 120V, 1 phase, 15,000 SQFT

    *Note: Demand Factor is set to 100% (1.0) as IT loads are typically considered continuous.*
    *For 208V Server Racks (Single Phase), enter voltage as 208 and phase as 1.*

Example user input:
User: it_systems[[20.0, 16.0, 30.0], 120, 15000, 1]

default_fire_alarm - `default_calculate_fire_alarm_metrics`

AI: Enter Fire Alarm data:
    Example entries:

    Format: default_fire_alarm[sqft, voltage, phase] | default_fire_alarm[50000, 120, 1]

    1. Building Size: 50,000 SQFT
    2. System: 120V, 1 phase
    3. Calculation: Uses a standard estimation density of 0.5 VA/SQFT.

Example user input:
User: default_fire_alarm[50000, 120, 1]

default_it_system - `default_calculate_it_system_metrics`

AI: Enter IT System data:
    Example entries:

    Format: default_it_system[sqft, voltage, phase] | default_it_system[15000, 120, 1]

    1. Building Size: 15,000 SQFT
    2. System: 120V, 1 phase
    3. Calculation: Uses a standard estimation density of 0.5 VA/SQFT.

Example user input:
User: default_it_system[15000, 120, 1]

electric_heating - `calculate_electric_heating_metrics`

AI: Enter Electric Heating data:
    Example entries:

    Format: electric_heating[[[amps, voltage, phase, "name"], ...], system_voltage, sqft]

    electric_heating[[[10, 208, 3, "UH-1"], [5, 208, 1, "Baseboard"]], 208, 2500]

    1. "UH-1": 10A (208V/3ph)
    2. "Baseboard": 5A (208V/1ph)
    3. System: 208V, 2,500 SQFT

    *Note: Calculates at 100% Demand Factor per NEC 220.51.*

Example user input:
User: electric_heating[[[10, 208, 3, "UH-1"], [5, 208, 1, "Baseboard"]], 208, 2500]

water_heater - `calculate_water_heater_metrics`

AI: Enter Water Heater data:
    Example entries:

    Format: water_heater[[[amps, voltage, phase, "name"], ...], system_voltage, sqft]

water_heater[[[30, 208, 1, "WH-1"], [15, 208, 3, "WH-2"]], 208, 5000]
    1. "WH-1": 30A (208V/1ph)
    2. "WH-2": 15A (208V/3ph)
    3. System: 208V, 5,000 SQFT

    *Note: Calculates at 100% Demand Factor per NEC 422.13.*

Example user input:
User: water_heater[[[30, 208, 1, "WH-1"], [15, 208, 3, "WH-2"]], 208, 5000]

### Signage
sign_lighting - `calculate_sign_lighting_metrics`

AI: Enter Signage data:
    Example entries:

    Format: sign_lighting[[[amps, voltage, phase, "name"], ...], required_outlets_count, system_voltage, sqft, system_phase]

    sign_lighting[[[2.5, 120, 1, "Logo"]], 1, 208, 5000, 3]

    1. "Logo": 2.5A (120V/1ph) -> 300 VA Actual.
    *NEC Logic: Demand calculated at minimum 1200 VA.*
    2. Required Outlets: 1 (Adds another 1200 VA Demand for a generic outlet).
    3. System: 208V, 3 phase, 5,000 SQFT.

    *Note: Automatically applies NEC 220.14(F) / 600.5 logic, ensuring every specific sign or required outlet is calculated at a minimum of 1200 VA for Demand.*

Example user input:
User: sign_lighting[[[2.5, 120, 1, "Logo"]], 1, 208, 5000, 3]

default_sign_lighting - `default_calculate_sign_lighting_metrics`

AI: Enter Signage data:
    Example entries:

    Format: default_sign_lighting[num_entrances, voltage, sqft] | default_sign_lighting[2, 120, 10000]

    1. Number of Entrances: 2 (Estimates 1200 VA per entrance per NEC 600.5)
    2. System: 120V
    3. Building Size: 10,000 SQFT

    *Note: Uses the NEC required minimum of 1200 VA for each public entrance.*

Example user input:
User: default_sign_lighting[2, 120, 10000]

### Multioutlet Assemblies
multioutlet - `calculate_multioutlet_metrics`

AI: Enter Multioutlet data:
    Example entries:

    Format: multioutlet[[length_ft, length_ft, ...], system_voltage, sqft, simultaneous_usage (true/false)]

    multioutlet[[10.0, 6.5, 3.0], 120, 2000, false]

    1. Strip 1: 10.0 ft
    2. Strip 2: 6.5 ft
    3. Strip 3: 3.0 ft
    4. System: 120V, 2,000 SQFT
    5. Usage: Standard (False) -> Calculates 180 VA per 5 ft section (NEC 220.14(H)).

    *Note: If `simultaneous_usage` is set to `true`, it calculates 180 VA per 1 ft section (Heavy Duty). Both modes apply NEC 220.44 Demand Factors (First 10kVA @ 100%, Remainder @ 50%).*

Example user input:
User: multioutlet[[10.0, 6.5, 3.0], 120, 2000, false]