
'''
    ChemAuto program's submodule for generating term symbols
    TermGen.py == TermGen_ver2.6.1.py
    Written by Li Xiiong
    2024-06-25
'''

import re
import time
import logging
import numpy as np
from datetime import datetime
from itertools import combinations
from fractions import Fraction
from collections import defaultdict
from logcreator import setup_logging, logged_input, logged_print

class TermSymbolGenerator:

    def __init__(self):
        # Define the orbitals dictionary
        self.orbitals = {
            's': ['s+', 's-'],
            'p': ['px+', 'px-', 'py+', 'py-', 'pz+', 'pz-'],
            'd': ['dxy+', 'dxy-', 'dxz+', 'dxz-', 'dyz+', 'dyz-', 'dx2-y2+', 'dx2-y2-', 'dz2+', 'dz2-'],
            'f': ['fz3+', 'fz3-', 'fxz2+', 'fxz2-', 'fyz2+', 'fyz2-', 'fxyz+', 'fxyz-', 'fz(x2-y2)+', 'fz(x2-y2)-', 'fx(x2-3y2)+', 'fx(x2-3y2)-', 'fy(3x2-y2)+', 'fy(3x2-y2)-'],
            'g': ['gz4+','gz4-','gxz3+','gxz3-','gyz3+','gyz3-','gxyz2+','gxyz2-','gz2(x2-y2)+','gz2(x2-y2)-','gx3z+','gx3z-','gy3z+','gy3z-','gx4+y4+','gx4+y4-','gxy(x2-y2)+','gxy(x2-y2)-']
        }

        # Define ml and ms values for each orbital
        self.orbital_quantum_numbers = {
            's+': (0, 0.5), 's-': (0, -0.5),
            'px+': (1, 0.5), 'px-': (1, -0.5), 'py+': (0, 0.5), 'py-': (0, -0.5), 'pz+': (-1, 0.5), 'pz-': (-1, -0.5),
            'dxy+': (2, 0.5), 'dxy-': (2, -0.5), 'dxz+': (1, 0.5), 'dxz-': (1, -0.5), 'dyz+': (0, 0.5), 'dyz-': (0, -0.5), 'dx2-y2+': (-1, 0.5), 'dx2-y2-': (-1, -0.5), 'dz2+': (-2, 0.5), 'dz2-': (-2, -0.5),
            'fz3+': (3, 0.5), 'fz3-': (3, -0.5), 'fxz2+': (2, 0.5), 'fxz2-': (2, -0.5), 'fyz2+': (1, 0.5), 'fyz2-': (1, -0.5), 'fxyz+': (0, 0.5), 'fxyz-': (0, -0.5), 'fz(x2-y2)+': (-1, 0.5), 'fz(x2-y2)-': (-1, -0.5), 'fx(x2-3y2)+': (-2, 0.5), 'fx(x2-3y2)-': (-2, -0.5), 'fy(3x2-y2)+': (-3, 0.5), 'fy(3x2-y2)-': (-3, -0.5),
            'gz4+': (4, 0.5), 'gz4-': (4, -0.5), 'gxz3+': (3, 0.5), 'gxz3-': (3, -0.5), 'gyz3+': (2, 0.5), 'gyz3-': (2, -0.5), 'gxyz2+': (1, 0.5), 'gxyz2-': (1, -0.5), 'gz2(x2-y2)+': (0, 0.5), 'gz2(x2-y2)-': (0, -0.5), 'gx3z+': (-1, 0.5), 'gx3z-': (-1, -0.5), 'gy3z+': (-2, 0.5), 'gy3z-': (-2, -0.5), 'gx4+y4+': (-3, 0.5), 'gx4+y4-': (-3, -0.5), 'gxy(x2-y2)+': (-4, 0.5), 'gxy(x2-y2)-': (-4, -0.5)
        }
        
    # Handle single configuration input
    def handle_input(self, config):
        match = re.match(r'^([spdfg])(\d+)$', config)
        if not match:
            return None, None
        orb = match.group(1)
        n_e = int(match.group(2))
        if orb not in self.orbitals or n_e > len(self.orbitals[orb]):
            return None, None
        return n_e, orb
    
    # Handle mixed configuration input
    def handle_mixed_input(self, config):
        pattern = re.compile(r'([spdfg])(\d{1,2})')
        matches = pattern.findall(config)
        if not matches or len(''.join(f'{m[0]}{m[1]}' for m in matches)) != len(config):
            return None
        inputs = [(m[0], int(m[1])) for m in matches]
        
        for orb, n_e in inputs:
            if orb not in self.orbitals or n_e > len(self.orbitals[orb]):
                return None
        return inputs
    
    # Convert fraction format from 1.5 to 3/2
    def format_fraction(self, num):
        if num == int(num):
            return str(int(num))
        frac = Fraction(num).limit_denominator()
        return f"{frac.numerator}/{frac.denominator}"
    
    # Generate all possible electron configurations
    def generate_electron_configs(self, n_e, orb):
        orbs = self.orbitals[orb]
        return list(combinations(orbs, n_e))
    
    # Calculate the Ml and Ms values of each configuration
    def calculate_ml_ms(self, config):
        ml = sum(self.orbital_quantum_numbers[orb][0] for orb in config)
        ms = sum(self.orbital_quantum_numbers[orb][1] for orb in config)
        return ml, ms
    
    # Generate all valid electron states and count Ml and Ms
    def generate_ml_ms_table(self, n_e, orb):
        configs = self.generate_electron_configs(n_e, orb)
        ml_ms_table = {}
        for config in configs:
            ml, ms = self.calculate_ml_ms(config)
            ml_ms_table[(ml, ms)] = ml_ms_table.get((ml, ms), 0) + 1
        return ml_ms_table
    
    # Display the Ml and Ms table
    def display_ml_ms_table(self, ml_ms_table):
        ml_values = sorted(set(key[0] for key in ml_ms_table.keys()), key=lambda x: (-x, abs(x)))
        ms_values = sorted(set(key[1] for key in ml_ms_table.keys()), key=lambda x: (-x, abs(x)))
        count_array = np.zeros((len(ml_values), len(ms_values)), dtype=int)
    
        for (ml, ms), count in ml_ms_table.items():
            ml_index = ml_values.index(ml)
            ms_index = ms_values.index(ms)
            count_array[ml_index, ms_index] = count
        ms_headers = "\t".join(self.format_fraction(ms) for ms in ms_values)
    
        print("Ms")
        print(f"\t{ms_headers}")
        print("ML")
        for ml_index, ml in enumerate(ml_values):
            counts = "\t".join(str(count_array[ml_index, ms_index]) for ms_index in range(len(ms_values)))
            print(f"{ml}\t{counts}")
        total_count = count_array.sum()
        logged_print(f"Total micro states: {total_count}\n")
    
    # Identify the maximum Ml and Ms values
    def identify_max_ml_ms(self, ml_ms_table):
        max_ml = max(ml_ms_table.keys(), key=lambda x: x[0])[0]
        max_ms = max([ms for (ml, ms) in ml_ms_table.keys() if ml == max_ml])
        return max_ml, max_ms
    
    # Remove a specific combination from the Ml and Ms table
    def remove_combination(self, ml_ms_table, ml, ms):
        ml_values = np.arange(-abs(ml), abs(ml) + 1, 1)
        ms_values = np.arange(-abs(ms), abs(ms) + 1, 1)
        for delta_ml in ml_values:
            for delta_ms in ms_values:
                if (delta_ml, delta_ms) in ml_ms_table:
                    ml_ms_table[(delta_ml, delta_ms)] -= 1
                    if ml_ms_table[(delta_ml, delta_ms)] == 0:
                        del ml_ms_table[(delta_ml, delta_ms)]
        return ml_ms_table
    
    # Convert Ml value to corresponding term symbol
    def ml_to_l(self, ml):
        l_map = {0: 'S', 1: 'P', 2: 'D', 3: 'F', 4: 'G', 5: 'H', 6: 'I', 7: 'K', 8: 'L', 9: 'M', 10: 'N', 11:'O', 12:'Q', 13:'R', 14:'T', 15:'U', 16:'V'}
        return l_map.get(abs(ml), '?')
    
    # Generate term symbols for given Ml and Ms table
    def generate_term_symbols(self, ml_ms_table):
        term_symbols = []
        while ml_ms_table:
            max_ml, max_ms = self.identify_max_ml_ms(ml_ms_table)
            base_symbol = f"{int(2 * max_ms + 1)}{self.ml_to_l(max_ml)}"
            max_j = max_ml + max_ms
            min_j = abs(max_ml - max_ms)
            all_j_values = np.arange(max_j, min_j - 1, -1)
            j_symbols = [f"{base_symbol}{self.format_fraction(j)}" for j in all_j_values if j >= 0]
            term_symbols.append((base_symbol, j_symbols))
            ml_ms_table = self.remove_combination(ml_ms_table, max_ml, max_ms)
        return term_symbols
    
    # Generate term symbols for mixed configurations
    def generate_mutil_term_symbols(self, L_S_dict1, L_S_dict2):
        combined_symbols = []
        combined_terms = {}
        for key1, (max_ml1, max_ms1) in L_S_dict1.items():
            for key2, (max_ml2, max_ms2) in L_S_dict2.items():
                new_L_range = range(max_ml1 + max_ml2, abs(max_ml1 - max_ml2) - 1, -1)
                new_S_range = np.arange(max_ms1 + max_ms2, abs(max_ms1 - max_ms2) - 1, -1)
                
                combined_key = f"{key1}+{key2}"
                combined_terms[combined_key] = []
                
                for new_L in new_L_range:
                    for new_S in new_S_range:
                        combined_symbol = f"{int(2 * new_S + 1)}{self.ml_to_l(new_L)}"
                        combined_terms[combined_key].append(combined_symbol)
                        combined_symbols.append(combined_symbol)
    
                logged_print(f"{combined_key}: {', '.join(combined_terms[combined_key])}")
        return combined_symbols
    
    # Print the ground state term symbol
    def print_ground_state(self, term_symbols):
        l_map = {'S': 0, 'P': 1, 'D': 2, 'F': 3, 'G': 4, 'H': 5, 'I': 6, 'K': 7, 'L': 8, 'M': 9, 'N': 10, 'O': 11, 'Q': 12, 'R': 13, 'T': 14, 'U': 15, 'V': 16}
        max_S = -1
        max_L = -1
        ground_state = None
    
        for symbol in term_symbols:
            S = int(symbol[0])
            L = l_map[symbol[1]]
            if (S > max_S) or (S == max_S and L > max_L):
                max_S = S
                max_L = L
                ground_state = symbol
        logged_print(f"Ground state term symbol: {ground_state}\n")
    
    # Generate L and S values for a given configuration
    def generate_L_S(self, n_e, orb):
        L_S_dict = {}
        ml_ms_table = self.generate_ml_ms_table(n_e, orb)
        while ml_ms_table:
            max_ml, max_ms = self.identify_max_ml_ms(ml_ms_table)
            base_symbol = f"{int(2 * max_ms + 1)}{self.ml_to_l(max_ml)}"
            L_S_dict[base_symbol] = (max_ml, max_ms)
            ml_ms_table = self.remove_combination(ml_ms_table, max_ml, max_ms)
        return L_S_dict
    
    # Print term symbols ordered by Hund's rule
    def print_term_symbols(self, term_symbols, n_e, orb):
        print("Atomic term symbols (ordered by Hund's rule):")
        l_map = {'S': 0, 'P': 1, 'D': 2, 'F': 3, 'G': 4, 'H': 5, 'I': 6, 'K': 7, 'L': 8, 'M': 9, 'N': 10, 'O': 11, 'Q': 12, 'R': 13, 'T': 14, 'U': 15, 'V': 16}
        sorted_term_symbols = sorted(term_symbols, key=lambda x: (int(x[0][0]), l_map[x[0][1]]), reverse=True)
        re_sorted_term_symbols = []
        
        for base_symbol, j_symbols in sorted_term_symbols:
            j_values = [float(Fraction(js[2:])) for js in j_symbols]
            if n_e < len(self.orbitals[orb]) / 2:
                sorted_j_symbols = [j_symbol for _, j_symbol in sorted(zip(j_values, j_symbols))]
            else:
                sorted_j_symbols = [j_symbol for _, j_symbol in sorted(zip(j_values, j_symbols), reverse=True)]
            re_sorted_term_symbols.append((base_symbol, sorted_j_symbols))
        
        base_symbol_count = {}
        total_term_symbol = 0
        for base_symbol, _ in re_sorted_term_symbols:
            if base_symbol in base_symbol_count:
                base_symbol_count[base_symbol] += 1
            else:
                base_symbol_count[base_symbol] = 1
            total_term_symbol += 1
        printed_symbols = set()
        
        max_base_symbol_length = max(len(base_symbol) for base_symbol, _ in re_sorted_term_symbols)
        for base_symbol, j_symbols in (re_sorted_term_symbols):
            if base_symbol not in printed_symbols:
                count = base_symbol_count[base_symbol]
                base_symbol_str = f"{base_symbol}({count})" if count > 1 else base_symbol
                print(f"{base_symbol_str.ljust(max_base_symbol_length + 3)}: {', '.join(j_symbols)}")
                printed_symbols.add(base_symbol)
        logged_print(f"Total atomic term symbols: {total_term_symbol}.")
        lowest_energy_term = re_sorted_term_symbols[-1][0]
        ground_state = re_sorted_term_symbols[0][1][0]
        logged_print("Ground state term symbol: " + ground_state + '\n')
    
    def run(self):
        start_time = datetime.now() 
        logging.info(f"Func 7 started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        while True:
            config = logged_input("Please input the configuration without n number (e.g., 'p2', 'd3', 's2p2', 'p2d1') or 'q' to quit:\n")
            if config.lower() == 'q' or config == 'exit':
                break
            if len(config) < 2:
                logged_print("Invalid input! Please input again.")
                continue
            n_e, orb = self.handle_input(config)
            if n_e is not None and orb is not None:
                logged_print(f"\nSingle Configuration: {config}\n")
                ml_ms_table = self.generate_ml_ms_table(n_e, orb)
                self.display_ml_ms_table(ml_ms_table)
                term_symbols = self.generate_term_symbols(ml_ms_table)
                self.print_term_symbols(term_symbols, n_e, orb)
            else:
                inputs = self.handle_mixed_input(config)
                if inputs is None or len(inputs) < 2:
                    logged_print("Invalid angular momentum or electron number! Please check it carefully.")
                    continue
                logged_print(f"\nMixed Configuration: {config}\n")
                L_S_dicts = [self.generate_L_S(n_e, orb) for orb, n_e in inputs]
                combined_symbols = self.generate_mutil_term_symbols(L_S_dicts[0], L_S_dicts[1])
                self.print_ground_state(combined_symbols)
    
        end_time = datetime.now()
        logging.info(f"Func 7 ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        duration_seconds = int((end_time - start_time).total_seconds())
        minutes, seconds = divmod(duration_seconds, 60)
        logging.info(f"Total duration: {minutes} minutes {seconds} seconds")
    
if __name__ == "__main__":
     generator = TermSymbolGenerator()
     generator.run()
    
    