#!/usr/bin/env python3

from datetime import datetime
import string
import time

def save_to_file(values, file_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = timestamp + ',' + values + '\n'

    with open(file_path, 'a') as file:
        file.write(line)
        file.close()

def main():
    time.sleep(120)
    file_path = '/Data/modbus/DRS-240_events.log'
    Status_out = "Startup,system_boot"
    save_to_file(Status_out, file_path)

if __name__ == "__main__":
    main()
