#!/bin/bash

cd "/Data/modbus/scripts"

source modbusData/bin/activate

./DRS-240_startup.py

deactivate
