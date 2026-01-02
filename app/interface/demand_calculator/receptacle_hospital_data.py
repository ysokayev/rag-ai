HOSPITAL_ROOM_DATA = {
    'airborne infection isolation (aii) room': {"location": "Airborne infection isolation (AII) room", "min_receptacles": "12", "min_sq_ft": "**120**", "va_per_sq_ft": 9.0},
    'medical/surgical unit patient room': {"location": "Medical/surgical unit patient room", "min_receptacles": "12", "min_sq_ft": "**** (Single) **100** per bed (Multiple)", "va_per_sq_ft": 10.8},
    'protective environment room': {"location": "Protective environment room", "min_receptacles": "12", "min_sq_ft": "**120**", "va_per_sq_ft": 9.0},
    'intermediate care unit patient room': {"location": "Intermediate care unit patient room", "min_receptacles": "12", "min_sq_ft": "*** (Single) **120** per bed (Multiple)", "va_per_sq_ft": 9.0},
    'postpartum unit patient room': {"location": "Postpartum unit patient room", "min_receptacles": "12", "min_sq_ft": "**** (Single) **124** per bed (Multiple)", "va_per_sq_ft": 8.71},
    'pediatric and adolescent unit patient room': {"location": "Pediatric and adolescent unit patient room", "min_receptacles": "12", "min_sq_ft": "**120** per bed", "va_per_sq_ft": 9.0},
    'rehabilitation unit patient room': {"location": "Rehabilitation unit patient room", "min_receptacles": "12", "min_sq_ft": "*** (Single) **125** per bed (Multiple)", "va_per_sq_ft": 8.64},
    'intensive care unit (icu) patient care station': {"location": "Intensive care unit (ICU) patient care station", "min_receptacles": "16", "min_sq_ft": "**200**", "va_per_sq_ft": 7.2},
    'pediatric intensive care unit (picu) patient room': {"location": "Pediatric intensive care unit (PICU) patient room", "min_receptacles": "16", "min_sq_ft": "**200**", "va_per_sq_ft": 7.2},
    'neonatal intensive care unit (nicu) infant care station': {"location": "Neonatal intensive care unit (NICU) infant care station", "min_receptacles": "16", "min_sq_ft": "**** (Single) **150** per bed (Multiple)", "va_per_sq_ft": 9.6},
    'labor/delivery/recovery (ldr) and labor/delivery/recovery/ postpartum (ldrp) room': {"location": "Labor/delivery/recovery (LDR) and Labor/delivery/recovery/ postpartum (LDRP) room", "min_receptacles": "16", "min_sq_ft": "**325**", "va_per_sq_ft": 4.43},
    'hospice and/or palliative care room': {"location": "Hospice and/or palliative care room", "min_receptacles": "16", "min_sq_ft": "**153**", "va_per_sq_ft": 9.41},
    'newborn nursery infant care station': {"location": "Newborn nursery infant care station", "min_receptacles": "4", "min_sq_ft": "**24**", "va_per_sq_ft": 15.0},
    'continuing care nursery infant carestation': {"location": "Continuing care nursery infant carestation", "min_receptacles": "5", "min_sq_ft": "**120**", "va_per_sq_ft": 3.75},
    'behavioral and mental health patient care unit patient bedroom': {"location": "Behavioral and mental health patient care unit patient bedroom", "min_receptacles": "No minimum", "min_sq_ft": "**** (Single) **80** per bed (Multiple)", "va_per_sq_ft": 0.0},
    'exam room class 1 imaging room': {"location": "Exam room Class 1 imaging room", "min_receptacles": "8", "min_sq_ft": "**120** (Single) **80** per station (Multiple)", "va_per_sq_ft": 6.0},
    'cesarean delivery room': {"location": "Cesarean delivery room", "min_receptacles": "30", "min_sq_ft": "**440**", "va_per_sq_ft": 6.14},
    'treatment room for basic emergency services': {"location": "Treatment room for basic emergency services", "min_receptacles": "12", "min_sq_ft": "**120**", "va_per_sq_ft": 9.0},
    'triage room or area in the emergency department': {"location": "Triage room or area in the emergency department", "min_receptacles": "6", "min_sq_ft": "**80** (implied)", "va_per_sq_ft": 6.75},
    'emergency department treatment room': {"location": "Emergency department treatment room", "min_receptacles": "12", "min_sq_ft": "**** (Single) **80** per station (Multiple)", "va_per_sq_ft": 13.5},
    'trauma/resuscitation room': {"location": "Trauma/resuscitation room", "min_receptacles": "16", "min_sq_ft": "**** (Single) **200** per station (Multiple)", "va_per_sq_ft": 7.2},
    'low-acuity patient treatment station': {"location": "Low-acuity patient treatment station", "min_receptacles": "4", "min_sq_ft": "**40** (estimated)", "va_per_sq_ft": 9.0},
    'interior human decontamination room': {"location": "Interior human decontamination room", "min_receptacles": "4", "min_sq_ft": "**100**", "va_per_sq_ft": 3.6},
    'observation unit patient care station': {"location": "Observation unit patient care station", "min_receptacles": "8", "min_sq_ft": "**** (Single) **80** (Multiple)", "va_per_sq_ft": 9.0},
    'procedure room (including endoscopy) class 2 imaging room': {"location": "Procedure room (including endoscopy) Class 2 imaging room", "min_receptacles": "12", "min_sq_ft": "**130**", "va_per_sq_ft": 8.31},
    'operating room class 3 imaging room': {"location": "Operating room Class 3 imaging room", "min_receptacles": "36", "min_sq_ft": "**400**", "va_per_sq_ft": 8.1},
    'hemodialysis patient care stations': {"location": "Hemodialysis patient care stations", "min_receptacles": "8", "min_sq_ft": "**80** (Chair) **** (Bed)", "va_per_sq_ft": 9.0},
    'phase i post-anesthetic care unit (pacu) patient care station': {"location": "Phase I post-anesthetic care unit (PACU) patient care station", "min_receptacles": "8", "min_sq_ft": "**80** (Multiple) **** (Single)", "va_per_sq_ft": 9.0},
    'phase ii recovery patient care station': {"location": "Phase II recovery patient care station", "min_receptacles": "4", "min_sq_ft": "**80** (Multiple) **** (Single)", "va_per_sq_ft": 4.5},
}

def get_room_data(location_name):
    """
    Retrieve hospital room data based on location name.
    Performs a normalized lookup.
    """
    import re
    
    # Normalize input
    key = re.sub(r'[*_]', '', location_name).strip().lower()
    key = re.sub(r'\s+', ' ', key)
    
    return HOSPITAL_ROOM_DATA.get(key)