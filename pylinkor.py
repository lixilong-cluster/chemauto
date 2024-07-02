
'''
    pylinkor module of ChemAuto program.
    Plotting DOS spectra using PES data exported from exporter module
    Developed by: Li Xilong
    Last Updates：2024-07-02
    
    pylinkor.py == pylinkor_ver1.3.py
    
'''

import os
import time
import json
import logging
from datetime import datetime
from logcreator import logged_input, logged_print
import originpro as op

"""
    Last Update: 2024-04-05
    Author: Li Xilong
    Acknowledgments: Special thanks to ChatGPT-4 for assistance.
    
    -------------------------------------------------------------------------------
    This module is designed to automate the plotting of Density of States (DOS) using OriginLab software. It enables users to specify custom parameters such as the template file location and the x-axis range for DOS plots directly from a configuration file. The program checks for these settings at startup and applies them accordingly.
    
    -------------------------------------------------------------------------------
    Features:
    - Automatic recognition and processing of curve and line data files within a specified directory.
    - User-configurable settings for template path and plot range through a JSON configuration file.
    - Batch processing capabilities for handling multiple datasets efficiently.
    
    -------------------------------------------------------------------------------
    Configurable Parameters:
    1. Template file location: Path to the OriginLab graph template.
    2. Drawing x-axis range of DOS: Specifies the range of the x-axis for DOS plots, with an upper limit of 5.
    
    --------------------------------------------------------------------------------
    Notes on OriginLab Window Naming:
    - `page.name$` is a read-only property for the short name of a window. To rename a window's short name, use the `win -r` command.
    - `page.label$` and `page.longname$` can be used to read or set the long name/label of a page.
    - The `page.title` property controls the display of window names, allowing for the display of either the short name, long name, or both.
    
    ---------------------------------------------------------------------------------
    Example of setting a window's long name:
        page.label$ = "Temperature"  # Rename the long name to "Temperature"
    
    Example of renaming a window's short name:
        winname$ = page.name$  # Read-only short name
        win -r %(winname$) "Source"  # Rename short name to "Source"

    Example of displaying both short and long names in a window title:
        page.title = 3  # Show both short name and long name

"""

class AutoDOS():
    def __init__(self):
        self.config_file_path = 'chemauto_config.json'
        self.default_config = {
            "template_path": "DOS-default.otpu",
            "default_x_range": [0, 3.3],
            "default_y_range": [-0.03, 6.5],
            "show_graph": False
        }
        self.config = self.load_or_update_config()

    def load_or_update_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, 'r') as file:
                try:
                    # try to load current config
                    config = json.load(file)
                except json.JSONDecodeError:
                    config = {}
            # Update current config
            for key, value in self.default_config.items():
                if key not in config:
                    config[key] = value
        else:
            config = self.default_config
        with open(self.config_file_path, 'w') as file:
            json.dump(config, file, indent=4)
        return config
        
    def process_file(self, curve_file_path=None, line_file_path=None, xlim_values=None, exit_origin = True):
        """
            Process the given curve and line files, create graphics and save.
        """
        if not curve_file_path or not line_file_path:
            logged_print("Parameter Error. Please input the required parameter.\n")
            while True:
                if not curve_file_path:
                    curve_file_path = logged_input("Input curve data file path (enter 'q' to return):\n").strip('"')
                    print(curve_file_path)
                    if curve_file_path.strip().lower() == 'q':
                        return 'r'
                    elif not curve_file_path.endswith("_curve.txt"):
                        logged_print("Invalid curve data file path. Please ensure the file ends with '_curve.txt'.")
                        curve_file_path = None
                        continue
                    else:
                        break
            while True:
                if not line_file_path:
                    line_file_path = logged_input("Input line data file path (enter 'q' to return):\n").strip('"')
                    print(line_file_path)
                    if line_file_path.strip().lower() == 'q':
                        return 'r'
                    elif not line_file_path.endswith("_line.txt"):
                        logged_print("Invalid line data file path. Please ensure the file ends with '_line.txt'.")
                        line_file_path = None  # Reset
                        continue
                    else:
                        break
        # No user defined xlim_values, using default value
        if xlim_values is None:
            default_x_range = self.config.get("default_x_range", [0, 3.3])
            while True:
                x_range = logged_input(f"Please input the x range of DOS spectrum in the format 'start,end' (default is {default_x_range[0]},{default_x_range[1]}):\n").strip()
                if x_range.strip().lower() == 'q' or x_range.strip().lower() == 'r':
                    print("Return to last menu!")
                    return
                elif not x_range:
                    xlim_values = default_x_range
                    break
                else:
                    logged_print(f"The x range you input is: {x_range}\n")
                try:
                    # Split user input then transfer to float
                    start, end = map(float, x_range.split(','))
                    # Check range validation
                    if start < end and 0 <= start and end <= 5:
                        xlim_values = (start, end)
                        #print(xlim_values)
                        break
                    else:
                        # Input again 
                        logged_print("Invalid input. The start must be less than the end, both between 0 and 5. Please try again.")
                except ValueError:
                    # Transfer failed, input again.
                    logged_print("Invalid input format. Please input two numbers separated by a comma (e.g., 0,3.3).")

        # Get parameters and prepare file paths
        ylim_values = self.config.get("default_y_range", [0, 6.5])
        template_path = self.config["template_path"]
        show_graph = self.config.get("show_graph", False)
        file_name = os.path.basename(os.path.dirname(curve_file_path))
        file_suffix = file_name.split('-')[-1] if '-' in file_name else file_name
        ogg_save_path = os.path.join(os.path.dirname(curve_file_path), f"{file_name}.ogg")
        opju_save_path = os.path.join(os.path.dirname(curve_file_path), f"{file_name}.opju")
        # Start plotting
        s = time.time()
        op.new()
        op.set_show(show_graph)
        wb = op.find_book()
        wb.lname = f'{file_name}_wb'
        wb.name = wb.lname
        wks_curve = wb.add_sheet(name=f'{file_name}_curve')
        wks_curve.name = f'{file_name}_curve'
        wks_line = wb.add_sheet(name = f'{file_name}_line')
        wks_line.name = f'{file_name}_line'
        op.find_sheet('w', f'[{wb.name}]sheet1').destroy()
        wks_curve.from_file(curve_file_path)
        wks_line.from_file(line_file_path)
        gp = op.new_graph(template = template_path)
        if gp is None:
            logged_print("Failed to create graph. The returned object is None.")
            op.exit()
            sys.exit(1)
        gl = gp[0]
        gl.add_plot(wks_curve, coly=1, colx=0, type='l')
        gl.add_plot(wks_line, coly=1, colx=0, type='l')
        gl.set_xlim(*xlim_values)
        gl.set_ylim(*ylim_values)
        gl.lname = f'{file_name}'
        gl.name = gl.lname
        gp.lname = f'{file_name}'
        gp.name = gp.lname

        # Set properties through .lt_exec method
        op.lt_exec(f'label -p 10 10 -n l "{file_suffix}";')
        op.lt_exec('l.font=font("Arial");')
        op.lt_exec('l.fsize=30;')
        op.lt_exec(f'save -ix "{ogg_save_path}";')
        op.save(f'{opju_save_path}')
        e = time.time()
        r = e - s
        print("Elapsed time: {:.2f} seconds".format(r))
        if exit_origin:
            op.exit()
        
        '''
            # Change longname of graph by page.label
            #op.lt_exec(f'page.label$ = "{file_name}";')
        
            # Page shortname is read-only, changed by win -r command
            #op.lt_exec(f'window -r Graph1 {file_name};')
        
            # Property name of layer is shortname
            #op.lt_exec(f'layer.name$ = "{file_name}";')
            #op.lt_exec(f'Layer.LongName$ = "123";')
        
            # Name property of page is read-only, can't be changed through following methods
            #op.lt_exec(f'page.name$ = "{file_name}";')
            #op.lt_exec(f'page.lname$ = "{file_name}";')
        '''

    def process_folder(self, folder_path=None):
        """
            Traverse all subfolders within a given folder, locate and process files ending with *_curve.txt and *_line.txt.
        """
        while True:
            if not folder_path:
                folder_path = logged_input("Please input the folder (enter 'r' to return):\n")
                if folder_path.strip().lower() == 'r' or folder_path.strip().lower() == 'q':
                    return 'r'
                elif not os.path.isdir(folder_path):
                    logged_print("Invalid folder path. Please try again.")
                    continue
                else:
                    break
        default_x_range = self.config.get("default_x_range", [0, 3.3])
        while True:
            x_range = logged_input(f"Please input the x range of DOS spectrum in the format 'start,end' (default is {default_x_range[0]},{default_x_range[1]}):\n").strip()
            if x_range.strip().lower() == 'q' or x_range.strip().lower() == 'r':
                print("Return to last menu!")
                return
            elif not x_range:
                xlim_values = default_x_range
                break
        
            try:
                # Split user input then transfer to float
                start, end = map(float, x_range.split(','))
                # Check range validation
                if start < end and 0 <= start and end <= 5:
                    xlim_values = (start, end)
                    break
                else:
                    # Input again 
                    logged_print("Invalid input. The start must be less than the end, both between 0 and 5. Please try again.")
            except ValueError:
                # Transfer failed, input again.
                logged_print("Invalid input format. Please input two numbers separated by a comma (e.g., 0,3.3).")

        logged_print("Start plotting, please wait...\n")

        start_time = time.time()
        for root, dirs, files in os.walk(folder_path):
            for dir_name in dirs:
                sub_folder_path = os.path.join(root, dir_name)
                curve_file = None
                line_file = None
                for file in os.listdir(sub_folder_path):
                    if file.endswith("_curve.txt"):
                        curve_file = os.path.join(sub_folder_path, file)
                    elif file.endswith("_line.txt"):
                        line_file = os.path.join(sub_folder_path, file)
                if curve_file and line_file:
                    self.process_file(curve_file, line_file, xlim_values=xlim_values, exit_origin=False)
        op.exit()
        end_time = time.time()
        run_time = end_time - start_time
        logged_print(f'Successfully completed! Total execution time: {run_time} seconds')
        
    def run(self):
        start_time = datetime.now()
        logging.info(f"Func 5 started at {start_time}.strftime('%Y-%m-%d %H:%M:%S')")
        
        while True:
            choice = logged_input("\nChoose an option:\n1. Batch plot DOS\n2. Plot single DOS\n")
            if choice == '1' or choice == '':
                # Assuming folder_path is defined or obtained elsewhere in your code
                result = self.process_folder()  # Call with required argument
                if result == 'r':
                    return
            elif choice == '2':
                # Call process_file without any arguments, using its default values
                result = self.process_file()
                if result == 'r':
                    return
            elif choice.strip().lower() == "q":
                logged_print("\nReturn to the main menu!\n")
                return
            else:
                logged_print("Invalid choice. Please enter again.")
        
        end_time = datetime.now()
        logging.info(f"Func 5 ended at{end_time}.strftime('%Y-%m-%d %H:%M:%S')")
        duration_seconds = int((end_time - start_time).total_seconds())
        minutes, seconds = divmod(duration_seconds, 60)
        logging.info(f"Total duration: {minutes} minutes {seconds} seconds")
    
if __name__ == "__main__":
    autodos = AutoDOS()
    autodos.run()