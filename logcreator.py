
'''
    logcreator module of ChemAuto program.
    Creating log file to monitor user input and program output 
    Developed by: Li Xilong
    Last Update: 2024-06-27

    Update history：
        2024-06-27
            # change the logic of log cleaning
            # Keep only the log entries with timestamps within the last three days and all the entries following them. 
            # Log entries before this period will be deleted.
'''

import os
import sys
import logging
from datetime import datetime, timedelta

LOG_FILE = 'chemauto.log'
RETENTION_DAYS = 3

def setup_logging():
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    logging.basicConfig(filename=LOG_FILE, 
                        level=logging.INFO, 
                        format='%(asctime)s - %(message)s', 
                        datefmt='%Y-%m-%d %H:%M:%S')

def clean_logs():
    retention_period = timedelta(days=RETENTION_DAYS)
    now = datetime.now()
    lines_to_keep = []
    log_cleanup_started = False

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            lines = f.readlines()

        for line in lines:
            try:
                log_time_str = line.split(' - ')[0]
                log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                if now - log_time <= retention_period:
                    log_cleanup_started = True
                if log_cleanup_started:
                    lines_to_keep.append(line)
            except ValueError:
                if log_cleanup_started:
                    lines_to_keep.append(line)
            except Exception as e:
                logging.error(f"Error parsing log line: {line}. Exception: {e}")
                if log_cleanup_started:
                    lines_to_keep.append(line)

        with open(LOG_FILE, 'w') as f:
            f.writelines(lines_to_keep)

def logged_input(prompt):
    user_input = input(prompt)
    logging.info(f"Input: {prompt}{user_input}")
    return user_input

def logged_print(*args, **kwargs):
    message = ' '.join(map(str, args))
    logging.info(message)
    print(*args, **kwargs)

def global_exception_handler(exctype, value, traceback):
    logging.exception("Unhandled exception occurred", exc_info=(exctype, value, traceback))
    sys.exit(1)

if __name__ == "__main__":
    sys.excepthook = global_exception_handler
    clean_logs()
    setup_logging()
    
