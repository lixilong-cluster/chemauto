
'''
    logcreator module of ChemAuto program.
    Creating log file to monitor user input and program output 
    Developed by: Li Xilong
    Last Update: 2024-04-01
'''

import os
import logging
from datetime import datetime, timedelta

def setup_logging():
    # The same dir with .exe
    log_file = 'chemauto.log'
    if not os.path.exists(log_file):
        open(log_file, 'w').close()

    #Config log settings
    logging.basicConfig(filename=log_file, 
                        level=logging.INFO, 
                        format='%(asctime)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def clean_logs():
    log_file = 'chemauto.log'
    retention_period = timedelta(days=3)
    now = datetime.now()
    
    if os.path.exists(log_file):
        # Get the creation time of log file
        log_file_time = os.path.getmtime(log_file)
        # datetime.now() return a date but .getmtime() return a * seconds, transfer format before clac
        log_creation_time = datetime.fromtimestamp(log_file_time)
        if now - log_creation_time > retention_period:
            try:
                os.remove(log_file)
                #print(f"Old log file {log_file} has been removed due to exceeding retention period.\n")
            except Exception:
                pass

def logged_input(prompt):
    user_input = input(prompt)
    #Record both prompt and user_input
    logging.info(f"Input: {prompt}{user_input}")
    return user_input

def logged_print(*args, **kwargs):
    message = ' '.join(map(str, args))
    logging.info(message)
    print(*args, **kwargs)

def global_exception_handler(exctype, value, traceback):
    """
        Global exception handling function
    """
    # Using logging.exception to provide a complete record of the exception information, including the stack trace.
    logging.exception("Unhandled exception occurred", exc_info=(exctype, value, traceback))
    sys.exit(1)


if __name__ == "__main__":
    clean_logs()

    setup_logging()
    
