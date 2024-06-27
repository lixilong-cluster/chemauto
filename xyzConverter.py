
"""
    Converter Script for log or gjf to xyz File
    
    This script converts log or gjf files to xyz files with the same name.
    From log files, it extracts the last frame of structures.
    
    Author: Li Xilong
    
    xyzConverter.py == xyzConverter_ver1.6.py
"""
import os
import re
import sys
import logging
from logcreator import logged_input, logged_print

class Converter():
    def __init__(self):
        self.elementDict = {1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne', 
                    11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K', 20: 'Ca', 
                    21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu', 30: 'Zn', 
                    31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr', 
                    41: 'Nb', 42: 'Mo', 43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn', 
                    51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce', 59: 'Pr', 60: 'Nd', 
                    61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy', 67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb', 
                    71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W', 75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg', 
                    81: 'Tl', 82: 'Pb', 83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th', 
                    91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf', 99: 'Es', 100: 'Fm', 
                    101: 'Md', 102: 'No', 103: 'Lr', 104: 'Rf', 105: 'Db', 106: 'Sg', 107: 'Bh', 108: 'Hs', 109: 'Mt', 
                    110: 'Ds', 111: 'Rg', 112: 'Cn', 113: 'Nh', 114: 'Fl', 115: 'Mc', 116: 'Lv', 117: 'Ts', 118: 'Og'}
        self.default_basis_set =['#p opt freq b3lyp/6-31G*\n', '\n', 'Title\n', '\n', '-1 2\n', '\n', '\n']
        self.line = []
        self.atom_num = 0
        self.coord_start_indices = []

    def get_valid_path(self, prompt):
        while True:
            path = logged_input(prompt).strip()
            if path.lower() in ['q', 'quit', 'exit']:
                logged_print("Exiting the program.")
                sys.exit()
            if path == "":
                logged_print("The path cannot be empty. Please try again or enter 'q' to quit.")
                continue
            if os.path.exists(path):
                return path
            else:
                if '.' in os.path.basename(path): # judge whether it is a file or not.
                    logged_print("The file path is not valid. Please try again or enter 'q' to quit.")
                else:
                    create_dir = logged_input(f"The directory '{path}' does not exist. Would you like to create it? (y/n): ").strip().lower()
                    if create_dir == 'y':
                        os.makedirs(path)
                        logged_print(f"Directory {path} created.")
                        return path
                    elif create_dir == 'n':
                        logged_print("Please choose another path.")
                    elif create_dir.lower() == 'q':
                        exit(0)
                    else:
                        logged_print("Invalid choice. Please enter 'y' or 'n'.")
                        
    def process_log_file(self, log_file, save_path, generate_xyz, generate_gjf):
        self.lines = []
        self.coord_start_indices = []

        if log_file.endswith('.log'):
            with open(log_file, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
            atom_found = False
            for i, line in enumerate(self.lines):
                if 'NAtoms=' in line and not atom_found:
                    self.atom_num = int(line.split()[1])
                    atom_found = True
                if 'Standard orientation:' in line:
                    self.coord_start_indices.append(i + 5)
        else:
            raise ValueError(f"Invalid file: {log_file} or not a .log file")

        last_struct_index = len(self.coord_start_indices) - 1
        if len(self.coord_start_indices) == 0:
            logged_print("UnknownError: No standard orientation found")
            return ""

        if len(self.coord_start_indices) == 1:
            coord_string = self.lines[self.coord_start_indices[0]:self.coord_start_indices[0] + self.atom_num]
        else:
            coord_string = self.lines[self.coord_start_indices[last_struct_index - 1]:self.coord_start_indices[last_struct_index - 1] + self.atom_num]

        extrCoord = ''
        for item in coord_string:
            try:
                coord = [float(item.split()[3]), float(item.split()[4]), float(item.split()[5])]
                atom_type = self.elementDict[int(item.split()[1])]
                extrCoord += ' %-2s%27.8f%14.8f%14.8f\n' % (atom_type, coord[0], coord[1], coord[2])
            except ValueError:
                return "UnknownError: Invalid coordinate format"

        log_basename = os.path.splitext(os.path.basename(log_file))[0]
        
        # Save .xyz file
        if generate_xyz:
            xyz_file_path = os.path.join(save_path, log_basename + ".xyz")
            with open(xyz_file_path, 'w', encoding='utf-8') as f:
                f.write(str(self.atom_num) + "\n")
                f.write("\n")
                f.write(extrCoord)

        # Save .gjf file
        if generate_gjf:
            gjf_file_path = os.path.join(save_path, log_basename + ".gjf")
            try:
                with open('basis_set.txt', 'r', encoding='utf-8') as basis_file:
                    basis_content = basis_file.readlines()
            except FileNotFoundError:
                logged_print("\nbasis_set.txt not found. Using default basis set.")
                basis_content = self.default_basis_set
            
            with open(gjf_file_path, 'w', encoding='utf-8') as gjf_file:
                for line in basis_content:
                    gjf_file.write(line)
                    if line.startswith("-") or line.startswith("0"):
                        parts = line.split()
                        if len(parts) == 2 and parts[1].isdigit() and parts[1].isdigit():
                            gjf_file.write(extrCoord)
        if generate_xyz and generate_gjf:
            print(f"Processed:\n {log_file}\nCoordinates written to:\n {xyz_file_path} and {gjf_file_path}\n")
            return xyz_file_path, gjf_file_path
        elif generate_xyz:
            print(f"Processed:\n {log_file}\nCoordinates written to:\n {xyz_file_path}\n")
            return xyz_file_path
        elif generate_gjf:
            print(f"Processed:\n {log_file}\nCoordinates written to:\n {gjf_file_path}\n")
            return gjf_file_path

    def extract_opted_structure(self):
        while True:
            choice = logged_input("Choose an option:\n 1. Generate .xyz file\n 2. Generate .gjf file\n 3. Generate .xyz and .gjf files\n Enter 'q' to quit.\n")
            if choice.lower() in ['q', 'quit', 'exit']:
                logged_print("Exiting the program.")
                return
            if choice == '':
                choice = '1'
            if choice in ['1', '2', '3']:
                generate_xyz = choice == '1' or choice == '3'
                generate_gjf = choice == '2' or choice == '3'
                if choice == '1':
                    logged_print("It will be saved as .xyz file.")
                elif choice == '2':
                    logged_print("It will be saved as .gjf file.")
                elif choice == '3':
                    logged_print("It will be saved as both .xyz and .gjf files.")
                break
            else:
                logged_print("Invalid choice. Please choose again.")

        file_path = self.get_valid_path("Please input the .log file or folder path:\n")
        save_path = self.get_valid_path("Please input the path where you want to save the .gjf and .xyz files:\n")

        if os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    if file.endswith(".log"):
                        file_path = os.path.join(root, file)
                        result = self.process_log_file(file_path, save_path, generate_xyz, generate_gjf)
                        if result == "":
                            logged_print(f"Error processing file: {file_path}. Skipping to the next file.")
        elif os.path.isfile(file_path) and file_path.endswith(".log"):
            result = self.process_log_file(file_path, save_path, generate_xyz, generate_gjf)
            if result == "":
                logged_print(f"Error processing file: {file_path}. Please check the file and try again.")
        else:
            logged_print("Invalid path or file type. Please input a valid .log file or directory containing .log files.")

    def extract_coordinates(self, gjf_content):
        lines = gjf_content.splitlines()
        coordinates = []
        copy = False
        for line in lines:
            if copy:
                if line.strip() == "":
                    break
                coordinates.append(line)
            if line.startswith("-") or line.startswith("0"):
                parts = line.split()
                if len(parts) == 2 and parts[1].isdigit() and parts[1].isdigit():
                    copy = True
        return coordinates

    def process_gjf_file(self, file_path, save_path):
        with open(file_path, 'r') as file:
            content = file.read()
        coordinates = self.extract_coordinates(content)
        if coordinates:
            xyz_file_path = os.path.join(save_path, os.path.splitext(os.path.basename(file_path))[0] + ".xyz")
            with open(xyz_file_path, 'w') as xyz_file:
                xyz_file.write(f"{len(coordinates)}\n\n")
                xyz_file.write("\n".join(coordinates))
            print(f"Processed:\n {file_path}\ncoordinates written to:\n {xyz_file_path}\n")
        else:
            logged_print(f"No coordinates found in {file_path}")

    def convert_gjf_to_xyz(self):
        file_path = self.get_valid_path("Please input the .gjf file or the folder path:\n")
        save_path = self.get_valid_path("Please input the path where you want to save the .xyz files:\n")

        if os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for file in files:
                    if file.endswith(".gjf"):
                        file_path = os.path.join(root, file)
                        self.process_gjf_file(file_path, save_path)
        elif os.path.isfile(file_path) and file_path.endswith(".gjf"):
            self.process_gjf_file(file_path, save_path)
        else:
            logged_print("Invalid path or file type. Please input a valid .gjf file or directory containing .gjf files.")

    def run(self):
        while True:
            choice = logged_input("\n 1. Extract opted structure from .log and save to .gjf and/or .xyz. \n 2. Convert .gjf to .xyz\n")
            if choice == '1' or choice == '':
                self.extract_opted_structure()
            elif choice == '2':
                self.convert_gjf_to_xyz()
            elif choice.lower() in ['q', 'exit', 'quit']:
                logged_print("Exiting the program.")
                break
            else:
                logged_print("Invalid choice. Please choose again!")

if __name__ == "__main__":
    converter = Converter()
    converter.run()