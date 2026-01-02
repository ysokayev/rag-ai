import json
import math
import os

class NEC_Calculator:
    def __init__(self, json_file_path=None):
        if json_file_path is None:
            # Default to json in same directory as script
            json_file_path = os.path.join(os.path.dirname(__file__), 'nfpa table 310_16_and_CH_9_table_8.json')
            
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Could not find {json_file_path}")
            
        with open(json_file_path, 'r') as f:
            self.data = json.load(f)
            
        self.table_8 = self.data['nec_chapter_9_table_8_properties']['data']
        self.table_amp = self.data['nec_table_310_16_ampacity']['wires']
        
        self.wire_sizes_order = [
            "14", "12", "10", "8", "6", "4", "3", "2", "1", 
            "1/0", "2/0", "3/0", "4/0", 
            "250", "300", "350", "400", "500", "600",
            "700", "750", "800", "900", "1000", "1250", "1500", "1750", "2000"
        ]

    def _parse_wire_type(self, type_str):
        type_str = type_str.lower()
        stranding = "solid" if "solid" in type_str else "stranded"
        material = "al" if "aluminum" in type_str else "cu"
        r_key = "r_al"
        if material == "cu":
            r_key = "r_cu_uncoated" if "uncoated" in type_str else "r_cu_coated"
        return stranding, material, r_key

    def get_table_8_data(self, size, stranding, key_suffix):
        lookup_key = f"{size}_{stranding}"
        if lookup_key not in self.table_8:
            lookup_key = f"{size}_stranded"
        if lookup_key not in self.table_8:
            return None, None
        data = self.table_8[lookup_key]
        return data['area_cmil'], data[key_suffix]

    def run(self, inputs):
        # Defaults
        volts = inputs.get('voltage', 480)
        max_drop_pct = inputs.get('max_desired_drop', 3.0)
        phase = inputs.get('phase', "3 Phase")
        wire_type_str = inputs.get('wire_type', "stranded copper uncoated")
        parallel = inputs.get('parallel_runs', 1)
        
        # Mandatory Inputs (except wire_size)
        try:
            length = inputs['length']
            # Allow 'load current' or 'amps'
            amps = inputs.get('load_current', inputs.get('amps'))
            if amps is None: raise KeyError("load_current")
        except KeyError as e:
            return [f"Error: Missing input {e}"]

        size = inputs.get('wire_size') # Optional

        stranding, material, r_key = self._parse_wire_type(wire_type_str)
        
        # 1. Calc Limits
        max_drop_volts = volts * (max_drop_pct / 100.0)
        min_volts_at_load = volts - max_drop_volts
        multiplier = 1.732050808 if "3" in str(phase) else 2.0
        
        # 5. Min Size Iteration (Performed early to auto-detect size)
        rec_size = "N/A"
        
        def calc_drop(check_size):
            _, check_r = self.get_table_8_data(check_size, stranding, r_key)
            if check_r is None: return float('inf')
            return (check_r * amps * length * multiplier) / (1000 * parallel)

        for check_size in self.wire_sizes_order:
            d = calc_drop(check_size)
            if d <= max_drop_volts:
                rec_size = check_size
                break
        
        # Auto-select size if missing
        if size is None:
            if rec_size == "N/A":
                size = self.wire_sizes_order[-1] # Fallback to largest
            else:
                size = rec_size

        # 2. Wire Props (Using determined size)
        area_cmil, r_per_1000 = self.get_table_8_data(size, stranding, r_key)
        if r_per_1000 is None: return [f"Error: Invalid wire config for size {size}"]
        
        r_total_per_foot = r_per_1000 / (1000.0 * parallel)

        # 3. Actuals
        actual_drop_volts = r_total_per_foot * amps * length * multiplier
        actual_volts_load = volts - actual_drop_volts
        voltage_diff = actual_volts_load - min_volts_at_load
        
        # 4. Max Dist
        max_distance = 0
        if amps > 0 and r_per_1000 > 0:
            max_distance = (max_drop_volts * 1000 * parallel) / (amps * r_per_1000 * multiplier)
            
        # 6. Ampacity (Table 310.16 75C)
        max_ampacity_nec = 0
        if size in self.table_amp:
            mat_data = self.table_amp[size].get(material)
            if mat_data: max_ampacity_nec = mat_data.get("75C")
        if max_ampacity_nec is None: max_ampacity_nec = 0
        
        min_parallel = 0
        if max_ampacity_nec > 0:
            min_parallel = math.ceil(amps / max_ampacity_nec)
            
        total_system_ampacity = max_ampacity_nec * parallel
        ampacity_diff = total_system_ampacity - amps

        return [
            [round(max_drop_volts, 2), round(actual_drop_volts, 2)],
            [round(min_volts_at_load, 2), round(actual_volts_load, 2)],
            [round(multiplier, 9), round(voltage_diff, 2)],
            [r_per_1000, f"{r_total_per_foot:.8f}"], 
            [size, rec_size],
            [length, int(max_distance)],
            [amps, max_ampacity_nec],
            [min_parallel, round(ampacity_diff, 2)]
        ]

if __name__ == "__main__":
    calc = NEC_Calculator()
    
    print("Test 1: Specified Size 12 AWG")
    inputs_1 = {"wire_size": "12", "length": 120, "load_current": 10}
    print(calc.run(inputs_1))
    
    print("\nTest 2: Auto-detect Size (Same loads)")
    inputs_2 = {"length": 120, "load_current": 10}
    # Should detect 12 or 14 -> 12 is rec based on previous test saying 14 works?
    # Actually previous test inputs: 12 AWG, 10A, 120'. Drop: 4.12V. Max allowed (3% of 480) = 14.4V.
    # So 14 AWG might even work.
    print(calc.run(inputs_2))