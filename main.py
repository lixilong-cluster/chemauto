
'''
    - Main module of ChemAuto program. Main entry point of the program.
    - Developed by: Li Xilong
    - main.py == main_ver2.0.py
'''

import os
import sys
from datetime import datetime
from logcreator import *

def main_menu():
    clean_logs()
    setup_logging()
    logged_print('\nChemAuto - An Automated Analysis Software for Cluster Chemistry. \nVersion: 5.3 \nRelease Date: 2024.06.27 \nDeveloper: Li Xilong \nHomepage: https://github.com/lixilong-cluster/chemauto \nUser mannul:')
    start_time = datetime.now()
    logged_print(f"\nProgram started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    while True:
        choice = logged_input("\n 1. Log files analysis. \n 2. Extract Structures. \n 3. Create gjf files. \n 4. Generate PES plotting data. \n 5. Generate DOS in ogg format.\n 6. Convert .gjf to .xyz or extract opted sturc from .log and save as .xyz.\n 7. Generate atomic term symbol.\n")
        if choice == '1':
            from analyzer import GaussianLogAnalyzer
            analyzer = GaussianLogAnalyzer()
            analyzer.run()
        elif choice == '2':
            from extractor import StructExtractor
            extractor = StructExtractor()
            extractor.run()
        elif choice == '3':
            from generator import GjfGenerator
            generator = GjfGenerator()
            generator.run()
        elif choice == '4':
            from exporter import PesExporter
            plotter = PesExporter()
            plotter.run()
        elif choice == '5':
            from pylinkor import AutoDOS
            dos_generator = AutoDOS()
            dos_generator.run()
        elif choice == '6':
            from xyzConverter import Converter
            converter = Converter()
            converter.run()
        elif choice == '7':
            from TermGen import TermSymbolGenerator
            generator = TermSymbolGenerator()
            generator.run()
        elif choice.strip().lower() == 'q':
            logged_print("Exiting the program.")
            break
        else:
            logged_print("Invalid choice. Please choose again!")

    end_time = datetime.now()
    logged_print(f"Program ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    duration_seconds = int((end_time - start_time).total_seconds())
    minutes, seconds = divmod(duration_seconds, 60)
    logged_print(f"Total duration: {minutes} minutes {seconds} seconds")

if __name__ == "__main__":
    setup_logging()
    sys.excepthook = global_exception_handler
    main_menu()