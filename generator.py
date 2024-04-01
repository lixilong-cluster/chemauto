'''
    generator module of ChemAuto program.
    Developed by: Li Xilong
    Last Update: 2024-04-01
'''

import os
import time
import requests
import logging
from datetime import datetime
from logcreator import logged_input, logged_print
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

'''
    Implement batch modification of gjf input files.
    Customize the link0 line as needed; if omitted, default values are used.
    For Gauss support sets, write the link0 line directly, omitting the basis set and element part.
    For custom basis sets, both the basis set and elements must be specified.
    Supports batch modification of gjf files as well as modification of individual gjf files.
    Add a tab key auto-completion feature: use the latest pyreadline3 instead of readline.
'''

class GjfGenerator():

    def __init__(self):
        self.BASE_URL = "https://www.basissetexchange.org"
        
        self.elemDict ={'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
                    'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 
                    'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29, 'Zn': 30, 
                    'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37, 'Sr': 38, 'Y': 39, 'Zr': 40, 
                    'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46, 'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 
                    'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55, 'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 
                    'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64, 'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 
                    'Lu': 71, 'Hf': 72, 'Ta': 73, 'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 
                    'Tl': 81, 'Pb': 82, 'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 
                    'Pa': 91, 'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100, 
                    'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108, 'Mt': 109, 
                    'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116, 'Ts': 117, 'Og': 118}
        
        # Autocomplete list of options
        self.COMPLETION_OPTIONS = [
            'def2-tzvp', 'def2-tzvpd', 'def2-tzvpp', 'def2-tzvppd',
            '6-311g', '6-311g*', '6-311+g', '6-311+g*', '6-311+g**', '6-311g(d,p)',
            'cc-pVTZ', 'cc-pVQZ', 'cc-pVDZ', 'cc-pV5Z',
            'aug-cc-pVDZ', 'aug-cc-pVTZ', 'aug-cc-pVQZ', 'aug-cc-pV5Z'
        ]
        # Create a completer using WordCompleter
        self.completer = WordCompleter(self.COMPLETION_OPTIONS, ignore_case=True)
        # Create PromptSession instance
        self.session = PromptSession(completer=self.completer)
    
    def check_basis_elem(self, basis, elements):
        """Check if the basis set is supported, case-insensitive, and return the basis set name and a list of element numbers"""
        r = requests.get(self.BASE_URL + '/api/metadata')
        if r.ok:
            metadata = r.json()
            basis_matched = None
            for name in metadata.keys():
                if name.lower() == basis.replace('*', '_st_').lower():
                    basis = name
                    basis_matched = True
                    break
            if basis_matched:
                #print(f"Basis set {basis} is supported.\n")
                latest_version = metadata[basis]["latest_version"]
                elements_list = metadata[basis]["versions"][latest_version]["elements"]
                # Format the input element list
                elements = [elem.strip().capitalize() for elem in elements.split(',')]
                unsupported_elements = []
                # Check if each element is supported
                for elem in elements:
                    if elem in self.elemDict and str(self.elemDict[elem]) not in elements_list:
                        unsupported_elements.append(elem)
                # Unsupported elements, print an error and return False
                if unsupported_elements:
                    logged_print(f"Basis set {basis} does not support the following elements: {', '.join(unsupported_elements)}")
                    return False
                
                # All the elements are supported
                #print(f"All input elements are supported by the basis set {basis}.")
                return basis, elements
            else:
                logged_print(f"Basis set {basis} is not supported.\n")
                return False
        else:
            logged_print(f"Failed to fetch basis set metadata.")
            return False
    
    def getBasis(self, basis, elements, fmt='gaussian94'):
            result = self.check_basis_elem(basis, elements)
            #print(result)
            if result:
                basis, elements = result
                """Get basis set data and delete the header information"""
                elements_param = ','.join(elements)
                #print(elements_param)
                url = f"{self.BASE_URL}/api/basis/{basis.lower()}/format/{fmt}/?elements={elements_param}"
                #print(url)
                r = requests.get(url)
                if r.ok:
                    data = r.text
                    # Delete header information
                    data = data.split('!----------------------------------------------------------------------')[-1].strip() + "\n"*5
                    return data
                else:
                    print("Error fetching basis set:", r.status_code)
                    return None
            else:
                logged_print("Operation aborted due to unsupported basis set or elements.")
    
    def pretreatment(self):
        link0 = self.session.prompt("Please input link0 (enter 'q' to return):")
        if link0.strip().lower() == 'q':
            return 'r'
        basis = self.session.prompt("Please input basis set name (leave empty if not required, 'q' to return):")
        if basis.strip().lower() == 'q':
            return 'r'
        elements = self.session.prompt("Please input the elements separated by commas (e.g., H,C,O) (leave empty if not required, 'q' to return):")
        if elements.strip().lower() == 'q':
            return 'r'
        
        # if link0 is None, using dafault values
        if not link0:
            link0 = "#p opt freq pbepbe/def2-tzvp"
        content = link0 + "\n\nMark\n\n\n\n\n"  # Build the basic content, including the default link0, two blank lines, Mark mark and two more blank lines
        # If both the basis set and elements are provided, call the getBasis method to obtain the data
        if basis and elements:
            data = self.getBasis(basis, elements)  # Assume that the getBasis method is already defined in the class and returns the required data
            content = link0 + "\n\nMark\n\n\n" + data
        return content
    
    def process_file(self, file_path, output_folder, content, insert_after_line=4):
        os.makedirs(output_folder, exist_ok=True)
        filename = os.path.basename(file_path)
        with open(file_path, 'r') as file:
            lines = file.readlines()
        i = -1
        j = -1
        for index, line in enumerate(lines):
            if line.startswith('-1') or line.startswith('0'):
                i = index
                break
        for index in range(i + 1, len(lines)):
            if lines[index].strip() == '':
                j = index
                break
        if i != -1 and j != -1:
            content_to_insert = lines[i:j]
        else:
            content_to_insert = []
        lines = content.splitlines(keepends=True)
        for i, new_line in enumerate(content_to_insert):
            # List index started from 0
            lines.insert(insert_after_line + i, new_line)
        # Merge list of lines back into a string
        new_content = ''.join(lines)
        with open(os.path.join(output_folder, filename), 'w') as file:
            file.writelines(new_content)
    
    def process_files_in_folder(self, folder, output_folder, content):
        for filename in os.listdir(folder):
            if filename.endswith('.gjf'):
                file_path = os.path.join(folder, filename)
                self.process_file(file_path, output_folder, content)

    def get_valid_input_path(self):
        while True:
            input_path = self.session.prompt("Please input the path of a gjf file or a folder containing gjf files (enter 'r' to return): \n")
            if input_path.strip().lower() == 'q':
                print("Program terminated!")
                return 'r'
            elif not os.path.exists(input_path):
                logged_print("Invalid path! Please try again.")
            else:
                return input_path
    
    def get_valid_output_path(self, input_path):
        while True:
            output_path = self.session.prompt("Please input the folder to save processed files (press Enter to overwrite, enter 'r' to return): \n")
            if output_path.strip().lower() == 'r':
                return 'r'
            elif output_path.strip() == '':
                if os.path.isfile(input_path):
                    output_path = os.path.dirname(input_path)
                elif os.path.isdir(input_path):
                    output_path = input_path
                return output_path
            elif not os.path.isdir(output_path):
                logged_print("Invalid folder path. Please try again.")
            else:
                if not os.path.exists(output_path):
                    os.makedirs(output_path, exist_ok=True)
                return output_path
    
    def process_input_path(self, input_path, output_path, content):
        start_time = time.time()
        if os.path.isfile(input_path) and input_path.endswith('.gjf'):
            self.process_file(input_path, output_path, content, insert_after_line=4)
        elif os.path.isdir(input_path):
            self.process_files_in_folder(input_path, output_path, content)
        else:
            logged_print("ERROR: Invalid input path. Please provide a valid .gjf file or directory.")
        end_time = time.time()
        logged_print(f"Runing time：{end_time - start_time}s\nSuccessful!!!")
        
    def run(self):
        start_time = datetime.now() 
        logging.info(f"Func 3 started at {start_time}.strftime('%Y-%m-%d %H:%M:%S')")
        
        input_path = self.get_valid_input_path()
        if input_path == 'r':
            return 
        output_path = self.get_valid_output_path(input_path)
        if output_path == 'r':
            return 
        content = self.pretreatment()
        if content == 'r':
            return
        elif not content:
            logged_print("\nError: No basis set information!\n")
            return
        self.process_input_path(input_path, output_path, content)
        
        end_time = datetime.now()
        logging.info(f"Func 3 ended at{end_time}.strftime('%Y-%m-%d %H:%M:%S')")
        duration_seconds = int((end_time - start_time).total_seconds())
        minutes, seconds = divmod(duration_seconds, 60)
        logging.info(f"Total duration: {minutes} minutes {seconds} seconds")


if __name__ == "__main__":
    generator = GjfGenerator()
    generator.run()






