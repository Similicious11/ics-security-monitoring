#!/usr/bin/env python3
"""
ICS Security Monitoring - Modbus Anomaly Detection
Analyzes pcap files for malicious activity in Modbus traffic
"""

from scapy.all import rdpcap, TCP
from scapy.contrib.modbus import ModbusADUResponse, ModbusADURequest
import sys
from collections import defaultdict
from datetime import datetime

# Define normal operating ranges for our ICS environment
NORMAL_RANGES = {
    'temperature': (200, 300),      # 20.0-30.0°C (stored as x10)
    'pressure': (900, 1100),        # 900-1100 PSI
    'motor_speed': (1400, 1600),    # 1400-1600 RPM
    'valve_state': (0, 1)           # 0=Closed, 1=Open
}

# Thresholds for attack detection
WRITE_THRESHOLD = 5  # More than 5 writes in capture = suspicious
DOS_THRESHOLD = 50   # More than 50 packets from single source = DoS

class ModbusAnomalyDetector:
    def __init__(self, pcap_file):
        self.pcap_file = pcap_file
        self.packets = []
        self.anomalies = []
        self.stats = {
            'total_packets': 0,
            'modbus_packets': 0,
            'read_requests': 0,
            'write_requests': 0,
            'out_of_range_values': 0,
            'suspicious_writes': 0
        }
        self.write_operations = defaultdict(int)
        self.source_ips = defaultdict(int)
        
    def load_pcap(self):
        """Load and parse pcap file"""
        print(f"[*] Loading pcap file: {self.pcap_file}")
        try:
            self.packets = rdpcap(self.pcap_file)
            self.stats['total_packets'] = len(self.packets)
            print(f"[+] Loaded {len(self.packets)} packets")
        except Exception as e:
            print(f"[!] Error loading pcap: {e}")
            sys.exit(1)
    
    def analyze_packet(self, pkt):
        """Analyze individual Modbus packet"""
        if not pkt.haslayer(TCP):
            return
        
        # Track source IPs for DoS detection
        if hasattr(pkt, 'src'):
            self.source_ips[pkt.src] += 1
        
        # Check for Modbus layer
        if pkt.haslayer(ModbusADURequest):
            self.stats['modbus_packets'] += 1
            modbus = pkt[ModbusADURequest]
            
            # Function Code 3 = Read Holding Registers
            if modbus.funcCode == 3:
                self.stats['read_requests'] += 1
            
            # Function Code 6 = Write Single Register
            elif modbus.funcCode == 6:
                self.stats['write_requests'] += 1
                register = modbus.registerAddr if hasattr(modbus, 'registerAddr') else 'unknown'
                value = modbus.registerValue if hasattr(modbus, 'registerValue') else 0
                
                self.write_operations[register] += 1
                
                # Check for out-of-range writes
                self.check_write_anomaly(register, value, pkt)
        
        # Check responses for out-of-range sensor values
        elif pkt.haslayer(ModbusADUResponse):
            self.stats['modbus_packets'] += 1
            self.check_response_values(pkt)
    
    def check_write_anomaly(self, register, value, pkt):
        """Detect suspicious write operations"""
        anomaly = None
        timestamp = datetime.fromtimestamp(float(pkt.time)).strftime('%H:%M:%S.%f')[:-3]
        
        if register == 0:  # Temperature register
            min_val, max_val = NORMAL_RANGES['temperature']
            if value < min_val or value > max_val:
                anomaly = {
                    'type': 'OUT_OF_RANGE_WRITE',
                    'severity': 'CRITICAL',
                    'time': timestamp,
                    'register': 'Temperature',
                    'value': value / 10.0,
                    'expected_range': f"{min_val/10.0}-{max_val/10.0}°C",
                    'description': f"Dangerous temperature value written: {value/10.0}°C"
                }
        
        elif register == 1:  # Pressure register
            min_val, max_val = NORMAL_RANGES['pressure']
            if value < min_val or value > max_val:
                anomaly = {
                    'type': 'OUT_OF_RANGE_WRITE',
                    'severity': 'CRITICAL',
                    'time': timestamp,
                    'register': 'Pressure',
                    'value': value,
                    'expected_range': f"{min_val}-{max_val} PSI",
                    'description': f"Dangerous pressure value written: {value} PSI"
                }
        
        elif register == 2:  # Motor speed register
            if value == 0:
                anomaly = {
                    'type': 'MOTOR_SHUTDOWN',
                    'severity': 'HIGH',
                    'time': timestamp,
                    'register': 'Motor Speed',
                    'value': value,
                    'description': "Motor shutdown detected (speed set to 0)"
                }
            elif value < NORMAL_RANGES['motor_speed'][0] or value > NORMAL_RANGES['motor_speed'][1]:
                anomaly = {
                    'type': 'OUT_OF_RANGE_WRITE',
                    'severity': 'MEDIUM',
                    'time': timestamp,
                    'register': 'Motor Speed',
                    'value': value,
                    'expected_range': f"{NORMAL_RANGES['motor_speed'][0]}-{NORMAL_RANGES['motor_speed'][1]} RPM",
                    'description': f"Abnormal motor speed written: {value} RPM"
                }
        
        elif register == 3:  # Safety valve register
            if value == 1:
                anomaly = {
                    'type': 'UNAUTHORIZED_VALVE_OPERATION',
                    'severity': 'CRITICAL',
                    'time': timestamp,
                    'register': 'Safety Valve',
                    'value': value,
                    'description': "Safety valve opened - potential unauthorized access"
                }
        
        if anomaly:
            self.anomalies.append(anomaly)
            self.stats['out_of_range_values'] += 1
    
    def check_response_values(self, pkt):
        """Check response packets for out-of-range sensor readings"""
        # This would require deeper packet parsing
        # For now, we focus on write detection
        pass
    
    def detect_dos(self):
        """Detect potential DoS attacks based on traffic patterns"""
        for src_ip, count in self.source_ips.items():
            if count > DOS_THRESHOLD:
                anomaly = {
                    'type': 'POTENTIAL_DOS',
                    'severity': 'HIGH',
                    'source': src_ip,
                    'packet_count': count,
                    'description': f"Excessive traffic from {src_ip}: {count} packets (threshold: {DOS_THRESHOLD})"
                }
                self.anomalies.append(anomaly)
    
    def detect_excessive_writes(self):
        """Detect excessive write operations"""
        total_writes = sum(self.write_operations.values())
        if total_writes > WRITE_THRESHOLD:
            self.stats['suspicious_writes'] = total_writes
            anomaly = {
                'type': 'EXCESSIVE_WRITES',
                'severity': 'MEDIUM',
                'write_count': total_writes,
                'description': f"Excessive write operations detected: {total_writes} writes (threshold: {WRITE_THRESHOLD})"
            }
            self.anomalies.append(anomaly)
    
    def analyze(self):
        """Run full analysis on pcap"""
        print("\n[*] Analyzing Modbus traffic...")
        
        for pkt in self.packets:
            self.analyze_packet(pkt)
        
        # Run additional detection rules
        self.detect_dos()
        self.detect_excessive_writes()
        
        print(f"[+] Analysis complete\n")
    
    def print_report(self):
        """Generate and print security report"""
        print("=" * 80)
        print("ICS SECURITY ANALYSIS REPORT")
        print("=" * 80)
        print(f"PCAP File: {self.pcap_file}")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        print("\n[TRAFFIC STATISTICS]")
        print(f"  Total Packets: {self.stats['total_packets']}")
        print(f"  Modbus Packets: {self.stats['modbus_packets']}")
        print(f"  Read Operations: {self.stats['read_requests']}")
        print(f"  Write Operations: {self.stats['write_requests']}")
        
        print("\n[SECURITY FINDINGS]")
        if not self.anomalies:
            print("  ✓ No anomalies detected - Traffic appears normal")
        else:
            print(f"  ⚠ {len(self.anomalies)} ANOMALIES DETECTED\n")
            
            # Group by severity
            critical = [a for a in self.anomalies if a.get('severity') == 'CRITICAL']
            high = [a for a in self.anomalies if a.get('severity') == 'HIGH']
            medium = [a for a in self.anomalies if a.get('severity') == 'MEDIUM']
            
            if critical:
                print(f"  🔴 CRITICAL ({len(critical)}):")
                for anomaly in critical:
                    print(f"     [{anomaly.get('time', 'N/A')}] {anomaly['description']}")
                    if 'register' in anomaly:
                        print(f"        Register: {anomaly['register']}, Value: {anomaly['value']}")
            
            if high:
                print(f"\n  🟠 HIGH ({len(high)}):")
                for anomaly in high:
                    print(f"     {anomaly['description']}")
            
            if medium:
                print(f"\n  🟡 MEDIUM ({len(medium)}):")
                for anomaly in medium:
                    print(f"     {anomaly['description']}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS:")
        if self.anomalies:
            print("  • Investigate unauthorized write operations immediately")
            print("  • Review access logs for the time periods of anomalies")
            print("  • Verify physical security of HMI stations")
            print("  • Consider implementing Modbus protocol authentication")
            print("  • Enable network segmentation between IT and OT networks")
        else:
            print("  • Continue monitoring for anomalous behavior")
            print("  • Maintain baseline traffic patterns")
        print("=" * 80 + "\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 detect_anomalies.py <pcap_file>")
        print("Example: python3 detect_anomalies.py ../captures/attack_traffic.pcap")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    
    detector = ModbusAnomalyDetector(pcap_file)
    detector.load_pcap()
    detector.analyze()
    detector.print_report()

if __name__ == "__main__":
    main()
