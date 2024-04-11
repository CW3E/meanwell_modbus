#!/bin/bash

cd "/Data/modbus/scripts"

source modbusData/bin/activate

./DRS-240_monitor.py

deactivate
