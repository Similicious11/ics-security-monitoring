#!/usr/bin/env python3
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusDeviceContext

# Create blocks
hr_block = ModbusSequentialDataBlock(0, [0]*10)

# Write test values
hr_block.setValues(0, [100, 200, 300, 400])
print(f"Direct block read [0-3]: {hr_block.getValues(0, 4)}")

# Create device context
device = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(0, [0]*10),
    co=ModbusSequentialDataBlock(0, [0]*10),
    ir=ModbusSequentialDataBlock(0, [0]*10),
    hr=hr_block
)

# Try to read through device context
print(f"\nReading through device context:")
try:
    # Function code 3 = holding registers, address 0, count 4
    values = device.getValues(3, 0, 4)
    print(f"getValues(fc=3, addr=0, count=4): {values}")
except Exception as e:
    print(f"Error: {e}")

# Try address 1
try:
    values = device.getValues(3, 1, 4)
    print(f"getValues(fc=3, addr=1, count=4): {values}")
except Exception as e:
    print(f"Error: {e}")
