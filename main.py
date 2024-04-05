'''
    main module of ChemAuto program. Main entry point of the program.
    Developed by: Li Xilong
    Last update : 2024-04-05
'''
import sys
from datetime import datetime
from logcreator import *
from analyzer import GaussianLogAnalyzer
from extractor import StructExtractor
from generator import GjfGenerator
from exporter import PesExporter
from pylinkor import AutoDOS

def main_menu():
    clean_logs()
    setup_logging()
    logged_print('ChemAuto - An Automated Analysis Software for Cluster Chemistry. \nVersion: 5.2 \nRelease Date: 2024.04.05 \nDeveloper: Li Xilong \nHomepage:https://github.com/lixilong-cluster/chemauto \nUser mannul:')
    start_time = datetime.now()
    logged_print(f"\nProgram started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    while True:
        choice = logged_input("\n 1. Log files analysis. \n 2. Extract Structures. \n 3. Create gjf files. \n 4. Generate PES plotting data. \n 5. Generate DOS in ogg format.\n ")
        if choice == '1':
            analyzer = GaussianLogAnalyzer()
            analyzer.run()
        elif choice == '2':
            extractor = StructExtractor()
            extractor.run()
        elif choice == '3':
            generator = GjfGenerator()
            generator.run()
        elif choice == '4':
            plotter = PesExporter()
            plotter.run()
        elif choice == '5':
            dos_generator = AutoDOS()
            dos_generator.run()
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
