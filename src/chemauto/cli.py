'''
    Main module of ChemAuto.
    Developed by: Li Xilong
'''

import os
import sys
import subprocess
import time
import uuid
from datetime import datetime
from chemauto.infra.logging import (
    clean_logs,
    setup_logging,
    logged_input,
    logged_print,
    global_exception_handler,
)

VERSION = "7.1.2"
RELEASE_DATE = "2026.07.15"


def _launch_gui():
    from chemauto.infra.paths import get_user_data_dir

    ready_file = get_user_data_dir() / f"gui-ready-{uuid.uuid4().hex}.flag"
    try:
        ready_file.unlink(missing_ok=True)
    except Exception:
        pass

    logged_print("Launching ChemAuto GUI as an independent process...")
    logged_print("Initial loading may take a few seconds. Please wait...")
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--gui", "--ready-file", str(ready_file)]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        launcher = pythonw if os.path.exists(pythonw) else sys.executable
        command = [launcher, "-m", "chemauto.gui.log_browser", "--ready-file", str(ready_file)]
        creationflags = 0

    proc = subprocess.Popen(command, creationflags=creationflags)
    deadline = time.monotonic() + 45.0
    while time.monotonic() < deadline:
        if ready_file.exists():
            try:
                ready_file.unlink()
            except Exception:
                pass
            logged_print("GUI process started. The CMD menu remains available.")
            return
        code = proc.poll()
        if code is not None:
            raise RuntimeError(f"GUI process exited before the window was ready (exit code {code}).")
        time.sleep(0.10)

    logged_print("GUI process was launched, but startup confirmation timed out. The CMD menu remains available.")


def main_menu():
    clean_logs()
    setup_logging()
    logged_print(
        f"\nChemAuto - An Automated Analysis Software for Cluster Chemistry."
        f"\nVersion: {VERSION}"
        f"\nRelease Date: {RELEASE_DATE}"
        "\nDeveloper: Li Xilong"
        "\nHomepage: https://github.com/lixilong-cluster/chemauto"
        "\nUser manual:"
    )
    start_time = datetime.now()
    logged_print(f"\nProgram started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    while True:
        choice = logged_input(
            "\n 0. Open ChemAuto GUI."
            "\n 1. Log files analysis."
            "\n 2. Extract structures."
            "\n 3. Create .gjf files."
            "\n 4. Generate PES plotting data."
            "\n 5. Generate DOS in OGG and OPJU formats."
            "\n 6. Convert .gjf to .xyz or extract optimized structure from .log."
            "\n 7. Generate atomic term symbols."
            "\n 8. Open Reference Search (independent program)."
            "\n q. Quit.\n"
        ).strip().lower()

        if choice == '0':
            try:
                _launch_gui()
            except Exception as exc:
                logged_print(f"Error launching GUI: {exc}")
        elif choice == '1':
            from chemauto.features.analyzer import GaussianLogAnalyzer
            GaussianLogAnalyzer().run()
        elif choice == '2':
            from chemauto.features.extractor import StructExtractor
            StructExtractor().run()
        elif choice == '3':
            from chemauto.features.generator import GjfGenerator
            GjfGenerator().run()
        elif choice == '4':
            from chemauto.features.pes_exporter import PesExporter
            PesExporter().run()
        elif choice == '5':
            from chemauto.features.dos_plotter import AutoDOS
            AutoDOS().run()
        elif choice == '6':
            from chemauto.features.xyz_converter import Converter
            Converter().run()
        elif choice == '7':
            from chemauto.features.term_gen import AtomicTermSymbolGenerator
            AtomicTermSymbolGenerator().run()
        elif choice == '8':
            try:
                from chemauto.core.reference_search_launcher import launch_reference_search
                launch_reference_search()
                logged_print("Reference Search started as an independent program.")
            except Exception as exc:
                logged_print(f"Error launching Reference Search: {exc}")
        elif choice == 'q':
            logged_print("Exiting the program.")
            break
        else:
            logged_print("Invalid choice. Please choose again.")

    end_time = datetime.now()
    logged_print(f"Program ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    duration_seconds = int((end_time - start_time).total_seconds())
    minutes, seconds = divmod(duration_seconds, 60)
    logged_print(f"Total duration: {minutes} minutes {seconds} seconds")


def main():
    setup_logging()
    sys.excepthook = global_exception_handler
    main_menu()


if __name__ == "__main__":
    main()
