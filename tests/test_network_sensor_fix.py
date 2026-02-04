import json
import os
import platform
from unittest.mock import patch, MagicMock
from galt.sensors import network_scan

def test_sensor_risk_calculation():
    # Test Calculate Risk
    assert "HIGH" in network_scan.calculate_risk([445], "pc-test")
    assert "HIGH" in network_scan.calculate_risk([3389], "pc-test")
    assert "MEDIUM" in network_scan.calculate_risk([80], "pc-test")
    assert "LOW" in network_scan.calculate_risk([], "pc-test")

def test_sensor_output_format():
    # Mock subprocess to avoid real ping/arp
    with patch("subprocess.check_call", return_value=True): # Ping success
         with patch("subprocess.check_output") as mock_exec:
             
             # Mock ARP output
             if platform.system().lower() == 'windows':
                 mock_exec.return_value = b"Internet Address      Physical Address      Type\r\n192.168.1.5           00-11-22-33-44-55     dynamic"
             
             # Mock Socket for ports
             with patch("socket.socket") as mock_sock:
                 mock_sock.return_value.connect_ex.return_value = 0 # Port open
                 
                 # Run logic on single target directly to verify structure
                 results = []
                 lock = MagicMock()
                 # Calling helper directly
                 network_scan.scan_target("192.168.1.5", [80], results, lock, "192.168.1.1")
                 
                 assert len(results) == 1
                 item = results[0]
                 
                 assert "ip_address" in item
                 assert item["ip_address"] == "192.168.1.5"
                 assert "mac_address" in item
                 assert "risk_label" in item
                 assert "is_gateway" in item

if __name__ == "__main__":
    test_sensor_risk_calculation()
    test_sensor_output_format()
    print("✅ Network Sensor Logic Verified")
