import socket
import json
import time
import argparse
import platform
import hashlib
from typing import Dict, Any, List

# --- Utility Functions (Duplicated from core to stay standalone or we can import) ---
# For modularity as requested "Evolucionar a plataforma modular", we SHOULD import if possible,
# but the prompt says "Requisito: Debe ser ejecutable de forma independiente". 
# Importing relative paths might be tricky if run directly unless PYTHONPATH is set.
# To be safe and standalone, I'll include minimal helpers or try strict imports if present.

def generate_event_id(plugin_name: str, time_window: str, host_id: str) -> str:
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def scan_ports(target_ip: str, ports: List[int]) -> List[int]:
    open_ports = []
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0) # 1 sec timeout
        result = sock.connect_ex((target_ip, port))
        if result == 0:
            open_ports.append(port)
        sock.close()
    return open_ports

def main():
    parser = argparse.ArgumentParser(description="Galt.ai Vulnerability Sensor")
    parser.add_argument("--local-only", action="store_true", help="Print to stdout (Default behavior for this sensor)")
    args = parser.parse_args()

    # Configuration
    TARGET_IP = "127.0.0.1"
    TARGET_PORTS = [80, 445, 3389, 3306, 5432, 27017]
    PLUGIN_NAME = "sensor_vulnerabilidades"
    
    # Execution
    open_ports = scan_ports(TARGET_IP, TARGET_PORTS)
    
    # Analysis
    severity = "LOW"
    impact_hint = "No critical ports found."
    
    if 3389 in open_ports or 445 in open_ports or 5900 in open_ports:
        severity = "HIGH"
        impact_hint = "CRITICAL: Remote Access (RDP/VNC) or SMB ports detected open locally. High Ransomware Risk."
    elif 3306 in open_ports:
        severity = "MEDIUM"
        impact_hint = "Database port (MySQL) exposed."
    elif 80 in open_ports:
        severity = "MEDIUM"
        impact_hint = "Web server port open."
        
    if open_ports:
        impact_hint = f"Open ports detected: {open_ports}. " + impact_hint

    # Construction
    timestamp = str(int(time.time()))
    host_id = platform.node()
    event_id = generate_event_id(PLUGIN_NAME, timestamp, host_id)
    
    payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "plugin": PLUGIN_NAME,
        "result": {
            "severity": severity,
            "data": open_ports,
            "impact_hint": impact_hint
        }
    }
    
    # Output (Always stdout for now as per 'local-only' requirement logic in runner)
    # The runner expects pretty printed or at least valid parts.
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
