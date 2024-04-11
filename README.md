# meanwell_modbus
Python code for interfacing with Meanwell DRS series power supplies using Modbus commands.
## RS-485 Interface
The Meanwell DRS Series has a RS-485 interface that can be used to read and write Modbus registers. To access the RS-485 interface, connect a ethernet cable to the RJ45 jack on the DRS and pull out Pins 6 (Data +), 7 (Data -), and 8 (GND) and connect them to an RS-485 interface.  RS-485 port settings on computer: 115200, 8N1. I am using an [Advantech USOPTL4 USB to RS-422/485 (Terminal Block) Isolated Converter](https://www.advantech.com/en/products/67a879ff-aef9-4715-8a4a-6c2763567851/bb-usoptl4/mod_f7c5f008-bf57-4b2b-8e42-603e788f3a4b).
## Modbus
While developing this code I used a free Windows [Modbus RTU/TCP Tester](https://www.gineers.com/en/downloads.php)
I found it extremely helpful for testing commands and seeing responses.
### Setup virtual environment
A virtual environment was setup on a computer running Linux for modbususer.
This code uses the [minmodbus python library](https://pypi.org/project/minimalmodbus/)
```
sudo apt install -y virtualenv
mkdir -p /Data/modbus/scripts
cd Data/dl4-met/scripts
virtualenv modbusData
```
### Add modbususer to dialout
In order to access the Advantech USOPTL4, modbususer must be added to the dialout group.
```
sudo usermod -a -G dialout modbususer
```
### Activate virtual environment and install the required packages
```
source modbusData/bin/activate
pip install --upgrade pip
pip install minimalmodbus
deactivate
```
### Shell scripts
The shell scripts monitor.sh and startup.sh start the virtual environment, call a python script, and then deactivate the environment.

### Python code
**DRS-240_startup.py** - Called in cronjob at startup to log system startup.

**DRS-240_monitor.py** - Called at interval in cronjob. Outputs voltages, current, AC status, on battery status, DRS T1 timeout. Will provide UPS capability when DRS is connected to a battery and shutdown system if T1 times out. [Meanwell DRS Manual](https://www.meanwell.com/Upload/PDF/DRS-240,480.pdf) has information on T1, T2, and T3.
