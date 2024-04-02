
'''
    exporter module of ChemAuto program.Exporting PES plotting data.
    Developed by: Li Xilong 
    Last update: 2027-04-02
'''
import os
import sys
import json
import logging
from datetime import datetime
from logcreator import logged_input, logged_print
import numpy as np
import pandas as pd

class PesExporter:
    """
    A class to process and plot PES data from .fchk files.
    
    Parameters:
        self.PES_Xlow 
        self.PES_Xhigh 
        self.npoints 
        self.PES_FWHM 
        self.PES_str
        self.PES_scale  the ratio of curve and line

    Requirement:
        Prepare a folder containing all the .fchk files and an info.txt file. The info.txt file should 
        contain two columns: the first column lists the names of the .log files (with the extension), 
        and the second column records the corresponding VDE values. The names of the .log and .fchk files 
        must match.

    Usage:
        To process all files in a folder:
            pes_plotter = PesExporter()
            pes_plotter.process_folder('path/to/folder')
    
        To process a single file:
            pes_plotter = PesExporter()
            pes_plotter.process_file('path/to/file.fchk', vde_value)
    """
    
    def __init__(self):
        self.config_file_path = 'chemauto_config.json'
        self.load_or_update_config()

    def load_or_update_config(self):
        default_config = {
            "PES_Xlow": 0.0,
            "PES_Xhigh": 5.0,
            "npoints": 5000,
            "PES_FWHM": 0.2,
            "PES_str": 1.0,
            "PES_scale": 5
        }

        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, 'r') as file:
                try:
                    config = json.load(file)
                except json.JSONDecodeError:
                    config = {}
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
        else:
            config = default_config
        with open(self.config_file_path, 'w') as file:
            json.dump(config, file, indent=4)
        self.PES_Xlow = config["PES_Xlow"]
        self.PES_Xhigh = config["PES_Xhigh"]
        self.npoints = config["npoints"]
        self.PES_FWHM = config["PES_FWHM"]
        self.PES_str = config["PES_str"]
        self.PES_scale = config["PES_scale"]

    def get_input(self, prompt, default=None, type_cast=str, validation=None):
        """ Get user input，supply for default values，type transfer """
        while True:
            user_input = logged_input(prompt)
            if user_input.strip().lower() == 'q':
                logged_print("Program terminated!")
                exit(0)
            if not user_input and default is not None:
                return default
            try:
                value = type_cast(user_input)
                if validation and not validation(value):
                    raise ValueError("Validation failed.")
                return value
            except ValueError as e:
                logged_print(e)
                logged_print("Invalid input. Please try again.")

    def create_save_path(self, path):
        while True:
            # Check if the path exists
            if not os.path.exists(path):
                user_decision = logged_input(f"The directory {path} does not exist. Create it? [Y/n]: ").strip().lower()
                if user_decision in ['', 'y', 'yes']:
                    os.makedirs(path, exist_ok=True)
                    return path
                elif user_decision in ['n', 'no']:
                    # if user dont want to create, get user input again.
                    path = self.get_input("Please input the folder to save the data again: ")
            else:
                return path

    def read_info(self, info_file_path):
        data_pairs = {}
        try:
            with open(info_file_path, 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) == 2:
                        file_name, vde_str = parts
                        try:
                            vde = float(vde_str)
                            data_pairs[file_name.split('.')[0]] = vde
                        except ValueError:
                            logged_print(f"Warning: Invalid VDE value '{vde_str}' for file '{file_name}'.")
                            logged_print("Please check the info.txt file and correct any errors.")
                            raise  # Re-raise the exception
        except FileNotFoundError:
            logged_print(f"Error: The file {info_file_path} was not found.")
            raise  # Re-raise the exception so the calling code knows about it
        return data_pairs

    '''
        energies = alpha_energies + beta_energies
    '''
    def extract_orbital_energies(self, file_path):
        nalpha = nbeta = None
        alpha_energies = []
        beta_energies = []
    
        with open(file_path, 'r') as file:
            lines = file.readlines()
        # First stage：extract the num of electrons
        for line in lines:
            if 'Number of alpha electrons' in line:
                nalpha = int(line.split()[-1])
            elif 'Number of beta electrons' in line:
                nbeta = int(line.split()[-1])
        # Second stage：extract Alpha and Beta orbital energies
        alpha_section = False
        beta_section = False
        for line in lines:
            if 'Alpha Orbital Energies' in line:
                alpha_section = True
                beta_section = False
                continue
            elif 'Beta Orbital Energies' in line:
                alpha_section = False
                beta_section = True
                continue
            
            if alpha_section or beta_section:
                # Trying to transfer every value to folat, if failed , that means data part ended.
                try:
                    values = [float(value) for value in line.split()]
                    if alpha_section:
                        alpha_energies.extend(values)
                    elif beta_section:
                        beta_energies.extend(values)
                except ValueError:
                    # Non-numeric data, break out of the loop
                    break
        # Get the corresponding number of energy values ​​according to nalpha and nbeta
        alpha_energies = alpha_energies[:nalpha]
        alpha_energies = [value * 27.21138 for value in alpha_energies]
        beta_energies = beta_energies[:nbeta]
        beta_energies = [value * 27.21138 for value in beta_energies]
        energies = alpha_energies + beta_energies
        homo = max(energies)
        #print(len(energies))
        logged_print(f"HOMO :{homo}.")
        '''
        for energy in energies:
            print(f'{energy:.6f}')
        '''
        return energies, alpha_energies, beta_energies, homo

    def generate_pes_line(self, alpha_energies, beta_energies, homo, vde):
        # Combine alpha and beta energies，calc adjusted energy values.
        adjusted_energies = [-energy + homo + vde for energy in alpha_energies + beta_energies]
        # Sort adjusted energy values in ascending order.
        adjusted_energies.sort()
        line_data = []
        cycle = [0, 1, None]
        for index, energy in enumerate(adjusted_energies):
            # Loop adds 0, 1, and None to each energy value
            line_data.append([energy, 0])
            line_data.append([energy, 1])
            line_data.append([energy, None])
        return line_data

    def generate_pes_curve(self, energies, homo, vde, PES_FWHM, hv_energy):
        self.PES_FWHM = float(PES_FWHM)
        curvexpos = np.linspace(self.PES_Xlow, self.PES_Xhigh, self.npoints)
        PEScurve = np.zeros(self.npoints)
        for energy in energies:
            #print(energy)
            gauss_c = self.PES_FWHM / 2.0 / np.sqrt(2 * np.log(2))
            gauss_a = self.PES_str / (gauss_c * np.sqrt(2 * np.pi))
        
            adjusted_energy = -energy + homo + vde
            #print(adjusted_energy)
            gauss_curve = gauss_a * np.exp(-(curvexpos - adjusted_energy) ** 2 / (2 * gauss_c ** 2))
            PEScurve += gauss_curve
        
        # Normalized Maximum Y value of curve to scale_to value.
        # Find the maximum Y value within a specific X-axis range
        x_range_min = 0
        x_range_max = float(hv_energy)
        indices = np.where((curvexpos >= x_range_min) & (curvexpos <= x_range_max))
        max_curve_value = np.max(PEScurve[indices])
        if max_curve_value != 0:
            normalization_factor = self.PES_scale / max_curve_value
            PEScurve *= normalization_factor
            
        curve_data = [[x, y] for x, y in zip(curvexpos, PEScurve)]
        return curve_data
       
    def write_data(self, folder_path, data, data_type, base_filename):
        # Determine file name suffix based on data_type
        filename_suffix = '_line.txt' if data_type == 'line' else '_curve.txt'
        # Create the complete file name.
        filename = f'{base_filename}{filename_suffix}'
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'w') as file:
            for x, y in data:
                if y is not None:
                    file.write(f'{x:16.6f}\t{y:12.6f}\n')
                else:
                    file.write(f'{x:16.6f}\t{"":12}\n')

    def process_file(self, vde=None, fchk_file_path=None, save_path=None, PES_FWHM=None, hv_energy=None):

        """ Processing single file """
        vde = vde or self.get_input(
            "Please input VDE value (eV): ",
            type_cast=float,
            validation=lambda x: x >= 0
        )
        
        fchk_file_path = fchk_file_path or self.get_input(
            "Please input the complete fchk file path:\n",
            validation=lambda x: os.path.isfile(x) and x.endswith('.fchk')
        )
        
        while True:
            save_path = save_path or self.get_input(
                "Please input the folder to save the data: \n",
                default=os.path.dirname(fchk_file_path),
                validation=lambda x: True
            )

            if not os.path.exists(save_path):
                choice = logged_input(f"The directory {save_path} does not exist.\nCreate it? [Y/n]: ").strip()
                if choice == 'Y':
                    os.makedirs(save_path, exist_ok=True)
                    break
                elif choice == 'n':
                    logged_print("Please choose a exist path.")
                else:
                    logged_print("Invalid choice. Please enter 'Y' to create the directory or 'n' to choose another path.")
            else:
                break
                
        if PES_FWHM is None:
            PES_FWHM = self.get_input(
                f"Enter FWHM value (default {self.PES_FWHM}): ",
                default=self.PES_FWHM,
                type_cast=float,
                validation=lambda x: x > 0
                )
        else:
            PES_FWHM = PES_FWHM

        hv_energy = hv_energy or self.get_input(
            "Please input hv energy used for the spectra (in eV): ",
            type_cast=float,
            validation=lambda x: x > 0
        )

        energies, alpha_energies, beta_energies, homo = self.extract_orbital_energies(fchk_file_path)
        line_data = self.generate_pes_line(alpha_energies, beta_energies, homo, vde)
        curve_data = self.generate_pes_curve(energies, homo, vde, PES_FWHM, hv_energy)
        base_filename = os.path.splitext(os.path.basename(fchk_file_path))[0]
        self.write_data(save_path, line_data, 'line', base_filename)
        self.write_data(save_path, curve_data, 'curve', base_filename)

    def process_folder(self, folder_path=None):
        if not folder_path:
            folder_path = logged_input("Please input the folder containing fchk files:\n")
            if folder_path == 'q':
                logged_print("\nReturn to main menu!\n")
                return
        if os.path.exists(folder_path):
            # Prompts the user to input the half-width FWHM value
            while True:
                custom_FWHM = logged_input(f"Enter FWHM value (default {self.PES_FWHM}): ").strip()
                if custom_FWHM.lower() == 'q':
                    logged_print("Program terminated!\n")
                    exit(0)
                if custom_FWHM:
                    try:
                        self.PES_FWHM = float(custom_FWHM)
                        break
                    except ValueError:
                        logged_print(f"Invalid input. Please enter a numeric value or 'q' to quit.")
                else:
                    logged_print(f"Using default FWHM value: {self.PES_FWHM}")
                    break
                    
            while True:
                hv_energy_input = logged_input("Please enter the hv energy used to take the spectra.(in eV):\n").strip()
                if hv_energy_input.lower() == 'q':
                    logged_print("Program terminated!\n")
                    exit(0)
                else:
                    try:
                        hv_energy = float(hv_energy_input)
                        break
                    except ValueError:
                        logged_print("Invalid input for hv energy. Please enter a numeric value or 'q' to quit.")
            
            try:
                info_file_path = os.path.join(folder_path, 'info.txt')
                logged_print(info_file_path)
                data_pairs = self.read_info(info_file_path)
            except Exception as e:
                logged_print(f"An error occurred: {e}")
                return
            
            for filename, vde in data_pairs.items():
                logged_print(f"Processing {filename} with VDE {vde}")
                save_path = os.path.join(folder_path, filename)
                os.makedirs(save_path, exist_ok=True)
                fchk_file_path = os.path.join(folder_path, f'{filename}.fchk')
                self.process_file(vde, fchk_file_path, save_path, self.PES_FWHM, hv_energy)
                logged_print(f"{filename} is finished\n")
        else:
            logged_print("Error: Folder does not exist. Please check the path and try again.")

    def export_overlay_data(self, folder_path=None):
        folder_path = logged_input("Please enter the folder containing the fchk files and info.txt file for overlay:\n")
        if folder_path == 'q':
            logged_print("\nReturn to main menu！")
            return
        if not os.path.exists(folder_path):
            logged_print("Error: Folder does not exist. Please check the path and try again.")
            return
        while True:
            custom_FWHM = logged_input(f"Enter FWHM value (default {self.PES_FWHM}): ").strip()
            if custom_FWHM.lower() == 'q':
                logged_print("Program terminated!\n")
                exit(0)
            if custom_FWHM:
                try:
                    self.PES_FWHM = float(custom_FWHM)
                    break
                except ValueError:
                    logged_print(f"Invalid input. Please enter a numeric value or 'q' to quit.")
            else:
                logged_print(f"Using default FWHM value: {self.PES_FWHM}")
                break
    
        while True:
            hv_energy_input = logged_input("Please input hv energy you used for taking those spectra (in eV):\n").strip()
            if hv_energy_input.lower() == 'q':
                logged_print("Program terminated!\n")
                exit(0)
            try:
                hv_energy = float(hv_energy_input)
                break
            except ValueError:
                logged_print("Invalid input for hv energy. Please enter a numeric value or 'q' to quit.")
        try:
            info_file_path = os.path.join(folder_path, 'info.txt')
            data_pairs = self.read_info(info_file_path)
        except Exception as e:
            logged_print(f"An error occurred: {e}")
            return

        all_line_data = []
        all_adjusted_energies = [] 
        for filename, vde in data_pairs.items():
            print(f"Processing {filename} with VDE {vde}")
            save_path = os.path.join(folder_path, "overlay_data")
            os.makedirs(save_path, exist_ok=True)
            fchk_file_path = os.path.join(folder_path, f'{filename}.fchk')
            
            energies, alpha_energies, beta_energies, homo = self.extract_orbital_energies(fchk_file_path)
            #adjusted_energies = [-energy + homo + vde for energy in alpha_energies + beta_energies]
            # adjusted energies
            adjusted_energies = [-energy + homo + vde for energy in energies]
            # add adjusted_energies to all_energies列表中
            all_adjusted_energies.extend(adjusted_energies)
        
        all_adjusted_energies.sort()
        cycle = [0, 1, None]
        for energy in all_adjusted_energies:
            all_line_data.append([energy, 0])
            all_line_data.append([energy, 1])
            all_line_data.append([energy, None])
 
        curvexpos = np.linspace(self.PES_Xlow, self.PES_Xhigh, self.npoints)
        PEScurve = np.zeros(self.npoints)
        for energy in all_adjusted_energies:
            gauss_c = self.PES_FWHM / 2.0 / np.sqrt(2 * np.log(2))
            gauss_a = self.PES_str / (gauss_c * np.sqrt(2 * np.pi))
            gauss_curve = gauss_a * np.exp(-(curvexpos - energy) ** 2 / (2 * gauss_c ** 2))
            PEScurve += gauss_curve
        x_range_min = 0
        x_range_max = float(hv_energy)
        indices = np.where((curvexpos >= x_range_min) & (curvexpos <= x_range_max))
        max_curve_value = np.max(PEScurve[indices])
        if max_curve_value != 0:
            normalization_factor = self.PES_scale / max_curve_value
            PEScurve *= normalization_factor
        curve_data = [[x, y] for x, y in zip(curvexpos, PEScurve)]

        base_filename = "overlaid"
        self.write_data(save_path, all_line_data, 'line', base_filename)
        self.write_data(save_path, curve_data, 'curve', base_filename)


    def run(self):
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        logging.info(f"Func 4 started at {start_time}")
        while True:
            choice = logged_input("\nChoose an option:\n1. Batch export PES data\n2. Export Single PES Data\n3. Export Overlay Spectra Data\n")
            if choice == '1':
                # Assuming folder_path is defined or obtained elsewhere in your code
                self.process_folder()  # Call with required argument
            elif choice == '2':
                # Call process_file without any arguments, using its default values
                self.process_file()  # Assuming this is correct according to your class design
            elif choice == '3':
                self.export_overlay_data()
            elif choice.strip().lower() == "q":
                logged_print("\nReturn to main menu！")
                return
            else:
                logged_print("Invalid choice. Please enter 1 or 2.")

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Func 4 ended at{end_time}")
        duration_seconds = int((end_time - start_time).total_seconds())
        minutes, seconds = divmod(duration_seconds, 60)
        logging.info(f"Total duration: {minutes} minutes {seconds} seconds")


if __name__ == "__main__":
    exporter = PesExporter()
    exporter.run()
    
