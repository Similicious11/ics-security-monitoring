#!/usr/bin/env python3
"""Test to verify datastore addressing"""

from pymodbus.datastore import ModbusSequentialDataBlock

# Create a block starting at address 0
block = ModbusSequentialDataBlock(0, [0]*10)

# Write values to addresses 0-3
print("Writing [100, 200, 300, 400] to addresses 0-3...")
block.setValues(0, [100, 200, 300, 400])

# Read back from addresses 0-3
values = block.getValues(0, 4)
print(f"Read from addresses 0-3: {values}")

# Try reading with address+1
print("\nTrying address offset test...")
block2 = ModbusSequentialDataBlock(1, [0]*10)
block2.setValues(1, [100, 200, 300, 400])
values2 = block2.getValues(1, 4)
print(f"Block starting at 1, reading from 1-4: {values2}")
