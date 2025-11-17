#!/usr/bin/env python3
"""
Modbus PLC Simulator - pymodbus 3.11.3
Using ModbusDeviceContext for proper data store setup
"""

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusDeviceContext,
    ModbusServerContext
)
from pymodbus.server import StartTcpServer
import logging
import random
import time
from threading import Thread

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

# Create data blocks for all register types
di_block = ModbusSequentialDataBlock(0, [0]*100)  # Discrete Inputs
co_block = ModbusSequentialDataBlock(0, [0]*100)  # Coils
ir_block = ModbusSequentialDataBlock(0, [0]*100)  # Input Registers
hr_block = ModbusSequentialDataBlock(1, [0]*100)  # Holding Registers (start at 1 for ModbusDeviceContext)

# Set initial PLC values in holding registers - START AT ADDRESS 1
values = [250, 1000, 1500, 0]  # temp, pressure, motor, valve
hr_block.setValues(1, values)  # Write to address 1 (will be read as address 0)

# Create device context - this wraps all the data blocks properly
device_context = ModbusDeviceContext(
    di=di_block,
    co=co_block,
    ir=ir_block,
    hr=hr_block
)

# Create server context with the device
context = ModbusServerContext(devices=device_context, single=True)

log.info("=" * 60)
log.info("PLC INITIALIZED - Modbus Server Ready")
log.info("=" * 60)
log.info("Unit ID: 1")
log.info("Register 0: Temperature = 250 (25.0°C)")
log.info("Register 1: Pressure = 1000 PSI")
log.info("Register 2: Motor Speed = 1500 RPM")
log.info("Register 3: Safety Valve = 0 (Closed)")
log.info("=" * 60)

def simulate_sensors():
    """Update sensor values to simulate real PLC"""
    iteration = 0
    while True:
        iteration += 1
        temp = random.randint(240, 260)
        pressure = random.randint(950, 1050)
        motor = random.randint(1450, 1550)
        
        # Read current valve state (address 4, which maps to register 3)
        current_values = hr_block.getValues(1, 4)
        valve = current_values[3]
        
        # Write all 4 values at once starting at address 1
        hr_block.setValues(1, [temp, pressure, motor, valve])
        
        # DEBUG: Read back what we just wrote
        if iteration % 12 == 0:
            stored = hr_block.getValues(1, 4)
            log.info(f"📊 Writing: Temp={temp}, Press={pressure}, Motor={motor}, Valve={valve}")
            log.info(f"📊 Stored at addresses [1-4]: {stored}")
        
        time.sleep(5)

# Start sensor simulation in background
Thread(target=simulate_sensors, daemon=True).start()

log.info("\nStarting Modbus TCP Server on 0.0.0.0:502")
log.info("Press Ctrl+C to stop\n")

# Start the server
try:
    StartTcpServer(context=context, address=("0.0.0.0", 502))
except KeyboardInterrupt:
    log.info("\nShutting down PLC...")
