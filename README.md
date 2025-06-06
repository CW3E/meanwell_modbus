# meanwell_modbus
Python code for interfacing with Meanwell DRS series power supplies using Modbus commands.
## RS-485 Interface
The Meanwell DRS Series has a RS-485 interface that can be used to read and write Modbus registers. To access the RS-485 interface, connect a ethernet cable to the RJ45 jack on the DRS and pull out Pins 6 (Data +), 7 (Data -), and 8 (GND) and connect them to an RS-485 interface.  RS-485 port settings on computer: 115200, 8N1. Connect to a RS-232 serial port on the rugged computer using an Advantech Isolated RS-422/485 to RS-232 Converter BB-4WSD9OTB.
## Modbus
While developing this code I used a free Windows [Modbus RTU/TCP Tester](https://www.gineers.com/en/downloads.php)
I found it extremely helpful for testing commands and seeing responses.
### Setup python
This code uses the [minmodbus python library](https://pypi.org/project/minimalmodbus/)

### Python code
**DRS-240_startup.py** - Run by task scheduler (triggered 5min after startup) at startup to log system startup.

Usage: DRS-240_startup.py <COM port> <timer (in minutes)>    # example: DRS-240_startup.py COM1 600


Note: once the UPS timer value is set via the startup script, the UPS must be power cycled (w/ battery disconnected) for new time to take effect

The startup script outputs startup data such a boot time and UPS settings to the event log "D:\\modbus\\Meanwell_UPS_events.log"



**DRS-240_monitor.py** - Run by task scheduler (triggered 8min after startup) every 2min indefinitely. 

Usage: DRS-240_monitor.py <COM port>   # example: DRS-240_monitor.py COM1

The monitor script outputs a status output line in the status log file "D:\\modbus\\Meanwell_UPS_status.log". Will provide UPS capability when DRS is connected to a battery and shutdown system if T1 times out. [Meanwell DRS Manual](https://www.meanwell.com/Upload/PDF/DRS-240,480.pdf) has information on T1, T2, and T3.

When T1 times out, the momitor script outputs shudown time to the event log "D:\\modbus\\Meanwell_UPS_events.log"

Status_out line format:  V_out, I_out, V_Bat, V_in, T_amb, AC_status, Battery_Detect, Chg_UPS_Status, DC_OK, Timeout

The monitor script also outputs a telemetry status line to the file of values and status bits to be included with telemetered data

Telemetry_status_out line format: "%.2f,%.2f,%.2f,%.1f,%.1f,%02X" % (V_out, I_out, V_Bat, V_in, T_amb, status_byte)

status_byte = 0x00 status  ->    0   0   0   0     0   0   0   0 
          Status bit index:      8   7   6   5     4   3   2   1
		  
		  1: AC status: Bit is 0 if AC input is OK and 1 if AC input is down
		  2: Battery detect: Bit is 0 if battery is detected and 1 if no battery is detected
		  3: Buffer timeout: Bit is 0 if there's no timeout and 1 if a timeout is reached
		  4: DC OK: Bit is 1 if output DC voltage is good and 0 if output DC voltage is bad 
		  5: UPS Status: Bit is 1 if UPS is in UPS mode and 0 if UPS is in charging mode
		  6: unused
		  7: unused
		  8: unused


### Modbus RTU device parameters
default port = "COM1"
default address = 0x83  # Modbus device address
default timer = 600 minutes

### Log files
STATUS_LOG_FILE path: "D:\\modbus\\Meanwell_UPS_status.log"
EVENTS_LOG_FILE path: "D:\\modbus\\Meanwell_UPS_events.log"
telemetry_file_path: "D:\\modbus\\Meanwell_UPS_Telemetry_Data.csv"
MAX_LOG_SIZE: 6613800 bytes  -> ~2 months status logging per file w/5 backup files = 1 year logging