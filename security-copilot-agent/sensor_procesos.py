import psutil
import json
import time
import argparse
import platform
import hashlib
import socket

# --- Utility Functions ---

def generate_event_id(plugin_name: str, time_window: str, host_id: str) -> str:
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_process_info(pid):
    try:
        proc = psutil.Process(pid)
        return {
            "name": proc.name(),
            "pid": pid,
            "username": proc.username(),
            "status": proc.status(),
            "exe": proc.exe()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def main():
    parser = argparse.ArgumentParser(description="Galt.ai Process Sensor")
    parser.add_argument("--local-only", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    PLUGIN_NAME = "sensor_procesos"
    
    # Critical ports to monitor
    CRITICAL_PORTS = {
        21: "FTP",
        22: "SSH", 
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        135: "RPC",
        139: "NetBIOS",
        443: "HTTPS",
        445: "SMB",
        1433: "MSSQL",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        8080: "HTTP-Alt",
        27017: "MongoDB"
    }

    active_processes = []
    
    try:
        # Get all network connections
        connections = psutil.net_connections(kind='inet')
        
        for conn in connections:
            # We are interested in listening ports or established connections on critical ports
            if conn.status == psutil.CONN_LISTEN or conn.status == psutil.CONN_ESTABLISHED:
                local_port = conn.laddr.port
                
                if local_port in CRITICAL_PORTS:
                    proc_info = get_process_info(conn.pid)
                    
                    if proc_info:
                        entry = {
                            "port": local_port,
                            "service": CRITICAL_PORTS[local_port],
                            "status": conn.status,
                            "process": proc_info,
                            "remote_ip": conn.raddr.ip if conn.raddr else None
                        }
                        active_processes.append(entry)

    except Exception as e:
        # In case of permission errors or other psutil failures
        pass

    # Analysis
    severity = "INFO"
    impact_hint = "No critical processes found on monitored ports."
    
    suspicious_processes = []
    
    for item in active_processes:
        proc = item['process']
        port = item['port']
        
        # Simple heuristic analysis
        # Example: cmd.exe or powershell.exe listening on ports is suspicious
        if proc['name'].lower() in ['cmd.exe', 'powershell.exe', 'netcat.exe', 'nc.exe']:
            severity = "HIGH"
            suspicious_processes.append(f"{proc['name']} on port {port}")
            
        # Example: SVchost on non-standard ports (very basic check)
        # Note: This is just a basic filler for the AI to analyze deeply
        
        # High value targets
        if port in [3389, 445, 22]:
            if severity != "HIGH": severity = "MEDIUM"

    if suspicious_processes:
        impact_hint = f"Suspicious processes detected: {', '.join(suspicious_processes)}"
    elif active_processes:
        impact_hint = f"Verified {len(active_processes)} processes on critical ports."

    timestamp = str(int(time.time()))
    host_id = platform.node()
    event_id = generate_event_id(PLUGIN_NAME, timestamp, host_id)
    
    payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "plugin": PLUGIN_NAME,
        "result": {
            "severity": severity,
            "data": active_processes,
            "impact_hint": impact_hint
        }
    }
    
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
