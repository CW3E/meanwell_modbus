#!/usr/bin/env python3
#
# Douglas Alden - 13 Mar 2024
# Generic version for Windows logger systems - HKW - 18 Apr 2025
# Branch: RADMet_UPS - Version: 1.0

import minimalmodbus
from datetime import datetime
import string
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Modbus RTU device parameters
default_port = "COM1"
default_address = 0x83  # Modbus device address

# Create a minimalmodbus instrument
instrument = minimalmodbus.Instrument(default_port, default_address)

# Function Codes
READ_HOLDING_REGISTER = 0x03
READ_INPUT_REGISTER = 0x04
PRESET_SINGLE_REGISTER = 0x06

# Data Types
FAULT_STATUS = 0x40
READ_VIN = 0x50
READ_VOUT = 0x60
READ_IOUT = 0x61
READ_TEMP = 0x62
CHG_STATUS = 0xB8
SYSTEM_STATUS = 0xC3
UPS_CONFIG = 0xD2
READ_VBAT = 0xD3
TIME_BUFFERING = 0xE4
UPS_DELAY_TIME = 0xE8
UPS_RESTART_TIME = 0xE9

STATUS_LOG_FILE = "D:\\modbus\\Meanwell_UPS_status.log"
EVENTS_LOG_FILE = "D:\\modbus\\Meanwell_UPS_events.log"
MAX_LOG_SIZE = 6613800  #2 months status logging per file w/5 backup files = 1 year logging

telemetry_file_path = "D:\\modbus\\Meanwell_UPS_Telemetry_Data.csv"

formatter1 = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s","%Y-%m-%d %H:%M:%S")
handler1 = RotatingFileHandler(EVENTS_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=1, encoding='utf-8')
handler1.setFormatter(formatter1)
events_logger = logging.getLogger("RotatingLogger1")
events_logger.setLevel(logging.INFO)
events_logger.addHandler(handler1)

formatter2 = logging.Formatter("%(asctime)s - %(message)s","%Y-%m-%d %H:%M:%S")
handler2 = RotatingFileHandler(STATUS_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=5, encoding='utf-8')
handler2.setFormatter(formatter2)
status_logger = logging.getLogger("RotatingLogger2")
status_logger.addHandler(handler2)

def read_registers(register_address, number_of_bytes, functioncode):
    global instrument
    try:
        # Read bytes from the specified input register
        values = instrument.read_registers(register_address, number_of_bytes, functioncode)

        if (register_address == FAULT_STATUS):
            value = values[0]
        elif (register_address == READ_VIN):
            value = values[0]/10
        elif (register_address == READ_VOUT):
            value = values[0]/100
        elif (register_address == READ_IOUT):
            value = values[0]/100
        elif (register_address == READ_TEMP):
            value = values[0]/10
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
        events_logger.exception(f"{e}")
        return -99999 

def save_to_file(values, telemetry_file_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = timestamp + ',' + values

    with open(telemetry_file_path, 'w') as file:
        file.write(line)
        file.close()

def shutdown_IPC(): # Shutdown the computer
    ups_shutdown = 'shutdown -s -t 60 -c "UPS System Shutdown"' 
    Status_out = "Shutdown,UPS System Shutdown"
    events_logger.warning(Status_out)
    os.system(ups_shutdown)

def main() :
    global instrument
    try :

        # Read port number from command line arguments
        if len(sys.argv) != 2:
            sys.exit(0)

        # Meanwell DRS-240-12 or DRS-480-24 DC UPS is connected to the rugged computer using an Advantech Isolated RS-422/485 to RS-232 Converter BB-4WSD9OTB.
 
        comPort = sys.argv[1]

        if comPort != default_port:
            instrument = minimalmodbus.Instrument(comPort, default_address)

        instrument.serial.baudrate = 115200
        instrument.serial.bytesize = 8
        instrument.serial.parity = 'N'
        instrument.serial.stopbits = 1

        status_byte = 0b00000000

        # Power Supply Status
        V_out = read_registers(READ_VOUT, 2, READ_INPUT_REGISTER)
        I_out = read_registers(READ_IOUT, 2, READ_INPUT_REGISTER)
        V_Bat = read_registers(READ_VBAT, 2, READ_INPUT_REGISTER)
        V_in = read_registers(READ_VIN, 1, READ_INPUT_REGISTER)
        T_amb = read_registers(READ_TEMP, 1, READ_INPUT_REGISTER)

        # Check if AC is still online
        ac_status = read_registers(FAULT_STATUS, 1, READ_HOLDING_REGISTER)
        if (ac_status != -99999): # Value was read
            ac_status = (ac_status >> 5) & 0x01
            status_byte = status_byte | ac_status
            if (ac_status == 0):
                AC_status = "AC OK"
            else:
                AC_status = "AC DOWN"
        else:
            AC_status = "NAN"  #communication failure

        # Check if timeout buffer has been reached.
        chg_status = read_registers(CHG_STATUS, 1, READ_HOLDING_REGISTER)
        if (chg_status != -99999):  # Value was read
            battery_detect = (chg_status >> 11) & 0x01
            status_byte = status_byte | ((battery_detect << 1)& 0x02)
            if (battery_detect == 0):
                Battery_Detect = "Battery"
            else :
                Battery_Detect = "No Batt"
            buffer_timeout = (chg_status >> 12) & 0x01
            status_byte = status_byte | ((buffer_timeout << 2)& 0x04)
            if (buffer_timeout == 0) :
                Timeout = "No Timeout"
            else :
                Timeout = "Timeout Reached"
        else:
            Battery_Detect = "NAN"  #communication failure
            Timeout =  "NAN"
            buffer_timeout = 0


        # Check if DC output is
        system_status = read_registers(SYSTEM_STATUS, 1, READ_HOLDING_REGISTER)
        if (system_status != -99999):  # Value was read
            dc_ok = (system_status & 0b00000010) >> 1
            chg_ups_status = (system_status & 0b10000000) >> 7
            status_byte = status_byte | ((dc_ok << 3)& 0x08) | ((chg_ups_status << 4)& 0x10)
            if (chg_ups_status == 1):
                Chg_UPS_Status = "UPS Mode"
            else:
                Chg_UPS_Status = "Charge Mode"            
            
            if (dc_ok == 1):
                DC_OK = "DC V_out good"
            else:
                DC_OK = "DC V_out low"

        else:
            Chg_UPS_Status =  "NAN"  #communication failure
            DC_OK =  "NAN"
            dc_ok = 1


        Status_out = "Vout = %.2f V, Iout = %.2f A, Vbat = %.2f V, Vin = %.1f V, Temp = %.1f C, %s, %s, %s, %s, %s" % (V_out, I_out, V_Bat, V_in, T_amb, AC_status, Battery_Detect, Chg_UPS_Status, DC_OK, Timeout)
        status_logger.warning(Status_out)

        telemetry_status_out = "%.2f,%.2f,%.2f,%.1f,%.1f,%02X" % (V_out, I_out, V_Bat, V_in, T_amb, status_byte)

        save_to_file(telemetry_status_out, telemetry_file_path)

        # Close the serial connection
        instrument.serial.close()

        # If the buffer_timeout has been reached or the low battery alarm is set shutdown the computer
        if (buffer_timeout | (dc_ok == 0)):
            #file_path = "D:\\modbus\\DRS-240_events.log"
            if (buffer_timeout):
                Status_out = "Shutdown,buffer_timeout"
                events_logger.warning(Status_out)

            if (dc_ok == 0):
                Status_out = "Shutdown,low_battery"
                events_logger.warning(Status_out)


            shutdown_IPC()


    except KeyboardInterrupt :
        events_logger.exception("keyboard_interrupt")
    except Exception as e:
        events_logger.exception(f"{e}")
    sys.exit(0)

if __name__ == "__main__":
    main()
