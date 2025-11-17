#!/usr/bin/env python3
"""
Modbus HMI Simulator - pymodbus 3.11.3 compatible
"""

from pymodbus.client import ModbusTcpClient
import time
import logging

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)  # Changed to DEBUG for troubleshooting

class HMISimulator:
    def __init__(self, plc_host='127.0.0.1', plc_port=502):
        self.client = ModbusTcpClient(plc_host, port=plc_port)
        self.connected = False
        self.plc_host = plc_host
        self.plc_port = plc_port
        
    def connect(self):
        """Connect to PLC"""
        log.info(f"Attempting to connect to PLC at {self.plc_host}:{self.plc_port}...")
        self.connected = self.client.connect()
        
        if self.connected:
            log.info("=" * 60)
            log.info(f"✓ HMI CONNECTED to PLC at {self.plc_host}:{self.plc_port}")
            log.info("=" * 60)
        else:
            log.error("✗ Failed to connect to PLC")
            log.error("  Make sure the PLC is running on port 502")
            
        return self.connected
    
    def read_sensors(self):
        """Read all sensor values from PLC"""
        if not self.connected:
            log.error("Not connected to PLC")
            return None
        
        # Read 4 holding registers starting at address 0
        result = self.client.read_holding_registers(address=0, count=4)
        
        if result.isError():
            log.error(f"Error reading registers: {result}")
            return None
        
        # DEBUG: Show raw register values
        log.debug(f"Raw registers: {result.registers}")
        
        # The registers should be: [temp*10, pressure, motor_speed, valve]
        temp = result.registers[0] / 10.0  # Convert back to Celsius
        pressure = result.registers[1]
        motor_speed = result.registers[2]
        valve_state = result.registers[3]
        
        log.info(f"📊 Sensors - Temp: {temp:.1f}°C | Pressure: {pressure} PSI | "
                f"Motor: {motor_speed} RPM | Valve: {'🔓 OPEN' if valve_state else '🔒 CLOSED'}")
        
        return {
            'temperature': temp,
            'pressure': pressure,
            'motor_speed': motor_speed,
            'valve_state': valve_state
        }
    
    def write_motor_speed(self, speed):
        """Write motor speed command to PLC"""
        if not self.connected:
            log.error("Not connected to PLC")
            return False
        
        log.info(f"⚙️  Writing motor speed command: {speed} RPM")
        result = self.client.write_register(address=2, value=speed)
        
        if result.isError():
            log.error(f"Error writing register: {result}")
            return False
        
        log.info(f"✓ Successfully set motor speed to {speed} RPM")
        return True
    
    def open_safety_valve(self):
        """Open safety valve (emergency procedure)"""
        log.warning("⚠️  OPENING SAFETY VALVE - Emergency procedure!")
        result = self.client.write_register(address=3, value=1)
        return not result.isError()
    
    def close_safety_valve(self):
        """Close safety valve"""
        log.info("🔒 Closing safety valve")
        result = self.client.write_register(address=3, value=0)
        return not result.isError()
    
    def normal_operation(self):
        """Simulate normal HMI operations"""
        log.info("")
        log.info("Starting normal HMI operation cycle...")
        log.info("Reading sensors every 10 seconds...")
        log.info("Press Ctrl+C to stop")
        log.info("")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                log.info(f"--- Cycle {cycle} ---")
                
                # Read sensors every 10 seconds
                sensors = self.read_sensors()
                
                if sensors:
                    # Example control logic: adjust motor speed based on pressure
                    if sensors['pressure'] > 1100:
                        log.warning("⚠️  HIGH PRESSURE detected! Reducing motor speed...")
                        self.write_motor_speed(1400)
                    elif sensors['pressure'] < 900:
                        log.warning("⚠️  LOW PRESSURE detected! Increasing motor speed...")
                        self.write_motor_speed(1600)
                
                time.sleep(10)
                
            except KeyboardInterrupt:
                log.info("\n" + "=" * 60)
                log.info("Shutting down HMI...")
                log.info("=" * 60)
                break
            except Exception as e:
                log.error(f"Error in operation: {e}")
                time.sleep(5)
    
    def disconnect(self):
        """Disconnect from PLC"""
        self.client.close()
        log.info("HMI disconnected from PLC")

if __name__ == "__main__":
    hmi = HMISimulator()
    
    if hmi.connect():
        try:
            hmi.normal_operation()
        finally:
            hmi.disconnect()
    else:
        log.error("Could not establish connection to PLC")
        log.error("Exiting...")
