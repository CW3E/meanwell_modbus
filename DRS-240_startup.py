#!/usr/bin/env python3
#
# Douglas Alden - 13 Mar 2024
# Generic version for Windows logger systems - HKW - 18 Apr 2025
# Branch: RADMet_UPS - Version: 1.0

import minimalmodbus
from datetime import datetime
import string
import time
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# Modbus RTU device parameters
default_port = "COM1"
default_address = 0x83  # Modbus device address
default_timer = 600

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

EVENTS_LOG_FILE = "D:\\modbus\\Meanwell_UPS_events.log"
MAX_LOG_SIZE = 6613800

formatter1 = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s","%Y-%m-%d %H:%M:%S") 

handler1 = RotatingFileHandler(EVENTS_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=1, encoding='utf-8')
handler1.setFormatter(formatter1)
events_logger = logging.getLogger("RotatingLogger1")
events_logger.setLevel(logging.INFO)
events_logger.addHandler(handler1)


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


def write_to_register(register_address, value):
    global instrument
    try:
        # Write one byte to the specified register
        instrument.write_register(register_address, value, functioncode=6)

    except Exception as e:
        events_logger.exception(f"An error occurred during writing: {e}")


def main() :
    global instrument
    try :

        # Read port number from command line arguments
        if len(sys.argv) != 3:
            sys.exit(0)

        # Meanwell DRS-240-12 or DRS-480-24 DC UPS is connected to the rugged computer using an Advantech Isolated
        # RS-422/485 to RS-232 Converter BB-4WSD9OTB.

        comPort = sys.argv[1]
        timer_length = int(sys.argv[2])

        if comPort != default_port:
            instrument = minimalmodbus.Instrument(comPort, default_address)
        events_logger.info('Program Start: Port - %s, Address - 0x%02X',comPort, default_address);

        instrument.serial.baudrate = 115200
        instrument.serial.bytesize = 8
        instrument.serial.parity = 'N'
        instrument.serial.stopbits = 1

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
        write_to_register(UPS_CONFIG, ups_config)
        # read ups_config
        ups_config  = read_registers(UPS_CONFIG, 1, READ_HOLDING_REGISTER)
        bin_ups_config = bin(ups_config)

        events_logger.info("0x%02X - UPS_Config: 0x%02X %s" % (UPS_CONFIG, ups_config, bin_ups_config))

        # TIME_BUFFERING
        # default: 600 minutes
        # Set T1 time buffer duration
        if (timer_length < 600) and  (timer_length >= 60):
            write_to_register(TIME_BUFFERING, timer_length)
        else:
            write_to_register(TIME_BUFFERING, default_timer)

        # read TIME_BUFFERING
        time_buffer = read_registers(TIME_BUFFERING, 1, READ_HOLDING_REGISTER)
        events_logger.info("0x%02X - Time Buffer: %d min" % (TIME_BUFFERING, time_buffer))

        # Set UPS delay time to 180 seconds
        write_to_register(UPS_DELAY_TIME, 180)
        # Read UPS delay time
        Delay_time = read_registers(UPS_DELAY_TIME, 1, READ_HOLDING_REGISTER)
        events_logger.info("0x%02X - Delay Time: %d sec" % (UPS_DELAY_TIME, Delay_time))

        # Read UPS restart time
        Restart_Time = read_registers(UPS_RESTART_TIME, 1, READ_HOLDING_REGISTER)
        events_logger.info("0x%02X - Restart Time: %d sec" % (UPS_RESTART_TIME, Restart_Time))

        time.sleep(120)
        file_path = "D:\\modbus\\DRS-240_events.log"
        Status_out = "Startup,system_boot"
        events_logger.warning(Status_out)


    except KeyboardInterrupt :
        events_logger.exception("keyboard_interrupt")
    except Exception as e:
        events_logger.exception(f"{e}")
    sys.exit(0)

if __name__ == "__main__":
    main()
