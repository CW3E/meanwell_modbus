#!/usr/bin/env python3

import minimalmodbus
from datetime import datetime
import string
import time
import os

# Modbus RTU device parameters
port = "COM1"
baudrate = 115200
databits = 8
parity = 'N'
stopbits = 1
address = 0x83  # Modbus device address

# Create a minimalmodbus instrument
instrument = minimalmodbus.Instrument(port, address)
instrument.serial.baudrate = baudrate
instrument.serial.bytesize = databits
instrument.serial.parity = parity
instrument.serial.stopbits = stopbits

print(instrument.serial)
print("")
print("Modbus address:",hex(instrument.address))
print("")

# Function Codes
READ_HOLDING_REGISTER = 0x03
READ_INPUT_REGISTER = 0x04
PRESET_SINGLE_REGISTER = 0x06

# Data Types
FAULT_STATUS = 0x40
READ_VIN = 0x50
READ_VOUT = 0x60
READ_IOUT = 0x61
CHG_STATUS = 0xB8
SYSTEM_STATUS = 0xC3
UPS_CONFIG = 0xD2
READ_VBAT = 0xD3
TIME_BUFFERING = 0xE4
UPS_DELAY_TIME = 0xE8
UPS_RESTART_TIME = 0xE9

def read_registers(instrument, register_address, number_of_bytes, functioncode):
    try:
        # Read bytes from the specified input register
        values = instrument.read_registers(register_address, number_of_bytes, functioncode)

        if (register_address == FAULT_STATUS):
            value = values[0]
        elif (register_address == READ_VIN):
            value = values[0]/100
        elif (register_address == READ_VOUT):
            value = values[0]/100
        elif (register_address == READ_IOUT):
            value = values[0]/100
        elif (register_address == CHG_STATUS):
            value = values[0]
        elif (register_address == SYSTEM_STATUS):
            value = values[0]
        elif (register_address == READ_VBAT):
            value = values[0]/100
        elif (register_address == UPS_CONFIG):
            value = values[0]
        elif (register_address == TIME_BUFFERING):
            value = values[0]
        elif (register_address == UPS_DELAY_TIME):
            value = values[0]
        elif (register_address == UPS_RESTART_TIME): 
            value = values[0]

        return value

    except Exception as e:
        print(f"{e}")
        return -99999 


def write_to_register(instrument, register_address, value):
    try:
        # Write one byte to the specified register
        instrument.write_register(register_address, value, functioncode=6)

    except Exception as e:
        print(f"An error occurred during writing: {e}")

def save_to_file(values, file_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = timestamp + ',' + values + '\n'

    with open(file_path, 'a') as file:
        file.write(line)
        file.close()

def main():

    # UPS_CONFIG
    # default: 0x09
    ups_config = 0x09
    # Turn off Wake_Up_EN
    ups_config = ups_config & 0b00000000
    # Enable time buffering
    ups_config = ups_config | 0b00000100
    # Set UPS_Delay_EN
    ups_config = ups_config | 0b00010000
    # Set UPS_Shutdown_EN
    ups_config = ups_config | 0b00100000
    # new value: 0x34
    write_to_register(instrument, UPS_CONFIG, ups_config)
    # read ups_config
    ups_config  = read_registers(instrument, UPS_CONFIG, 1, READ_HOLDING_REGISTER)
    bin_ups_config = bin(ups_config)
    print("0x%02X - UPS_Config: 0x%02X %s" % (UPS_CONFIG, ups_config, bin_ups_config))
    
    # TIME_BUFFERING
    # default: 600 minutes
    # Set to 600 minutes
    write_to_register(instrument, TIME_BUFFERING, 600)
    # read TIME_BUFFERING
    time_buffer = read_registers(instrument, TIME_BUFFERING, 1, READ_HOLDING_REGISTER)
    print("0x%02X - Time Buffer: %d min" % (TIME_BUFFERING, time_buffer))

    # Set UPS delay time to 180 seconds
    write_to_register(instrument, UPS_DELAY_TIME, 180)
    # Read UPS delay time
    Delay_time = read_registers(instrument, UPS_DELAY_TIME, 1, READ_HOLDING_REGISTER)
    print("0x%02X - Delay Time: %d sec" % (UPS_DELAY_TIME, Delay_time))
    
    # Read UPS restart time
    Restart_Time = read_registers(instrument, UPS_RESTART_TIME, 1, READ_HOLDING_REGISTER)
    print("0x%02X - Restart Time: %d sec" % (UPS_RESTART_TIME, Restart_Time))

    time.sleep(120)
    file_path = "D:\\modbus\\DRS-240_events.log" #'/Data/modbus/DRS-240_events.log'
    Status_out = "Startup,system_boot"
    save_to_file(Status_out, file_path)

if __name__ == "__main__":
    main()
