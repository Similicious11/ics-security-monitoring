#!/usr/bin/env python3
from pymodbus.datastore import ModbusSequentialDataBlock

# Test 1: Block starting at address 0
print("Test 1: Block starting at 0")
block = ModbusSequentialDataBlock(0, [0]*10)
block.setValues(0, [100])
block.setValues(1, [200])
block.setValues(2, [300])
block.setValues(3, [400])

print(f"Address 0: {block.getValues(0, 1)}")
print(f"Address 1: {block.getValues(1, 1)}")
print(f"Address 2: {block.getValues(2, 1)}")
print(f"Address 3: {block.getValues(3, 1)}")
print(f"All [0-3]: {block.getValues(0, 4)}")

# Test 2: Try address 1
print("\nTest 2: What's at address 1?")
print(f"validate(1): {block.validate(1, 1)}")
print(f"Values[1]: {block.values[1] if len(block.values) > 1 else 'N/A'}")
