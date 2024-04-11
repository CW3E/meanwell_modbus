#!/usr/bin/env python3
#
# Douglas Alden - 13 Mar 2024
# 

import minimalmodbus
from datetime import datetime
import string
import os

# Modbus RTU device parameters
port = '/dev/ttyUSB0'
#port = '/dev/ttyS4'
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

def shutdown_IPC(): # Shutdown the computer
    ups_shutdown = 'sudo shutdown -h +1 "UPS System Shutdown"'
    file_path = '/Data/modbus/DRS-240_events.log'
    Status_out = "Shutdown,UPS System Shutdown"
    save_to_file(Status_out, file_path)

    os.system(ups_shutdown)
    
def main():

    # Power supply parameters

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
    # new value: 0x3D
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
    #write_to_register(instrument, UPS_DELAY_TIME, 180)
    # Read UPS delay time
    Delay_time = read_registers(instrument, UPS_DELAY_TIME, 1, READ_HOLDING_REGISTER)
    print("0x%02X - Delay Time: %d sec" % (UPS_DELAY_TIME, Delay_time))
    
    # Read UPS restart time
    Restart_Time = read_registers(instrument, UPS_RESTART_TIME, 1, READ_HOLDING_REGISTER)
    print("0x%02X - Restart Time: %d sec" % (UPS_RESTART_TIME, Restart_Time))

    # Power Supply Status
    V_out = read_registers(instrument, READ_VOUT, 2, READ_INPUT_REGISTER)
    I_out = read_registers(instrument, READ_IOUT, 2, READ_INPUT_REGISTER)
    V_Bat = read_registers(instrument, READ_VBAT, 2, READ_INPUT_REGISTER)
    
    # Check if AC is still online
    ac_status = read_registers(instrument, FAULT_STATUS, 1, READ_HOLDING_REGISTER)
    if (ac_status != -99999): # Value was read
        ac_status = (ac_status >> 5) & 0x01
        if (ac_status == 0):
            ac_status = "AC OK"
        else:
            ac_status = "AC DOWN"
    
    # Check if timeout buffer has been reached.
    chg_status = read_registers(instrument, CHG_STATUS, 1, READ_HOLDING_REGISTER)
    if (chg_status != -99999):  # Value was read
        message = "0x%02X - Charge Status: " % (CHG_STATUS)
        battery_detect = (chg_status >> 11) & 0x01
        if (battery_detect == 0):
            message = message + "Battery Detected"
        else :
            message = message + "No Battery"
        buffer_timeout = (chg_status >> 12) & 0x01
        if (buffer_timeout == 0) :
            message = message + ", No Timeout"
        else :
            message = message + ", Timeout Reached"

        print(message)
    
    # Check if DC output is
    system_status = read_registers(instrument, SYSTEM_STATUS, 1, READ_HOLDING_REGISTER)
    if (system_status != -99999):  # Value was read
        dc_ok = (system_status & 0b00000010) >> 1
        chg_ups_status = (system_status & 0b10000000) >> 7
            
    print("")
    print(f"System stats")
    print(f"      V Out:", V_out, "V")
    print(f"      I Out:", I_out, "A")
    print(f"     Batt V:", V_Bat, "V")
    print(f"   AC Input:", ac_status)
    
    if (chg_ups_status == 1):
        print(f"Operating Mode: UPS")
    else:
        print(f"Operating Mode: Charging")
    
    if (dc_ok == 1):
        print(f"Secondary DD output voltage status: NORMAL")
    else:
        print(f"Secondary DD output voltage status: TOO LOW")

    Status_out = "%.2f,%.2f,%.2f,%s,%d,%d,%d" % (V_out, I_out, V_Bat, ac_status, chg_ups_status, dc_ok, buffer_timeout)
#    Status_out = "%.2f,%.2f,%.2f,%s,%d" % (V_out, I_out, V_Bat, ac_status, dc_ok)

    file_path = '/Data/modbus/DRS-240_status.txt'
    save_to_file(Status_out, file_path)    
    # Close the serial connection
    instrument.serial.close()
    
    # If the buffer_timeout has been reached or the low battery alarm is set shutdown the computer
    if (buffer_timeout | (dc_ok == 0)):
        file_path = '/Data/modbus/DRS-240_events.log'
        if (buffer_timeout):
            Status_out = "Shutdown,buffer_timeout"
            save_to_file(Status_out, file_path)
        if (dc_ok == 0):
            Status_out = "Shutdown,low_battery"
            save_to_file(Status_out, file_path)

        shutdown_IPC()
    

if __name__ == "__main__":
    main()
