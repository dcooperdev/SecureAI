import psutil
import json
import time
import argparse
import platform
import hashlib
import socket
import subprocess
import re

# --- Utility Functions ---

def generate_event_id(plugin_name: str, time_window: str, host_id: str) -> str:
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_process_name_by_pid_fallback(pid):
    """
    Fallback to 'tasklist' command to get process name if psutil fails (AccessDenied).
    """
    try:
        # tasklist /FI "PID eq 1234" /FO CSV /NH
        cmd = f'tasklist /FI "PID eq {pid}" /FO CSV /NH'
        output = subprocess.check_output(cmd, shell=True).decode(errors='ignore').strip()
        # Output format: "Image Name","PID","Session Name","Session#","Mem Usage"
        # Example: "svchost.exe","1234","Services","0","12,345 K"
        if output and '"' in output:
            parts = output.split('","')
            if len(parts) > 0:
                return parts[0].replace('"', '')
    except Exception:
        pass
    return "Unknown (System/Protected)"

def get_process_info(pid):
    if pid is None: return None
    try:
        proc = psutil.Process(pid)
        return {
            "name": proc.name(),
            "pid": pid,
            "username": proc.username(),
            "status": proc.status(),
            "exe": proc.exe()
        }
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return None
    except psutil.AccessDenied:
        # Fallback to tasklist for name
        name = get_process_name_by_pid_fallback(pid)
        return {
            "name": name,
            "pid": pid,
            "username": "SYSTEM/Protected", # Assumption for AccessDenied
            "status": "running",
            "exe": "AccessDenied"
        }

def get_netstat_map():
    """
    Parses 'netstat -ano' to get a mapping of {port: pid} for TCP/UDP listening ports.
    """
    mapping = {}
    try:
        # Run netstat -ano
        output = subprocess.check_output("netstat -ano", shell=True).decode(errors='ignore')
        # Regex to capture protocol, local address, (ignored remote), state (optional), PID
        # TCP    0.0.0.0:135            0.0.0.0:0              LISTENING       984
        # UDP    0.0.0.0:123                                   *:*                                     1234
        lines = output.splitlines()
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = re.split(r'\s+', line)
            if len(parts) >= 4:
                proto = parts[0]
                local_addr = parts[1]
                
                # We need the PID, which is usually the last element
                # But sometimes state is missing for UDP
                pid_str = parts[-1]
                
                if not pid_str.isdigit(): continue
                
                pid = int(pid_str)
                
                # Parse port from 0.0.0.0:135 or [::]:135
                if ':' in local_addr:
                    port_str = local_addr.rsplit(':', 1)[-1]
                    if port_str.isdigit():
                        port = int(port_str)
                        mapping[port] = pid
    except Exception as e:
        # Silently fail if netstat fails, we rely on psutil
        pass
    return mapping

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
    netstat_lookup = None # Lazy load
    
    try:
        # Get all network connections via psutil first
        connections = psutil.net_connections(kind='inet')
        
        # We also want to check ports that psutil MIGHT have missed (unlikely but possible with permissions)
        # So let's build a set of found ports
        found_ports = set()
        
        for conn in connections:
            if conn.status == psutil.CONN_LISTEN or conn.status == psutil.CONN_ESTABLISHED:
                local_port = conn.laddr.port
                
                if local_port in CRITICAL_PORTS:
                    found_ports.add(local_port)
                    pid = conn.pid
                    
                    # Deep Network Scan: Fallback if PID is missing
                    if pid is None:
                        if netstat_lookup is None: netstat_lookup = get_netstat_map()
                        pid = netstat_lookup.get(local_port)
                    
                    proc_info = get_process_info(pid)
                    
                    if proc_info:
                        entry = {
                            "port": local_port,
                            "service": CRITICAL_PORTS[local_port],
                            "status": conn.status,
                            "process": proc_info,
                            "remote_ip": conn.raddr.ip if conn.raddr else None
                        }
                        active_processes.append(entry)
        
        # Double verification: Check if we missed any critical port that netstat sees
        # This is useful if psutil didn't list the connection at all due to permissions
        if netstat_lookup is None: netstat_lookup = get_netstat_map()
        
        for port, pid in netstat_lookup.items():
            if port in CRITICAL_PORTS and port not in found_ports:
                # We found a shadow listener!
                proc_info = get_process_info(pid)
                if proc_info:
                    entry = {
                        "port": port,
                        "service": CRITICAL_PORTS[port],
                        "status": "LISTEN (netstat)", # netstat usually implies Listen for these if TCP
                        "process": proc_info,
                        "remote_ip": None,
                        "source": "netstat_deep_scan"
                    }
                    active_processes.append(entry)

    except Exception as e:
        pass

    # Analysis
    severity = "INFO"
    impact_hint = "No critical processes found on monitored ports."
    
    suspicious_processes = []
    
    for item in active_processes:
        proc = item['process']
        port = item['port']
        name = proc['name'].lower()
        
        # Simple heuristic analysis
        if name in ['cmd.exe', 'powershell.exe', 'netcat.exe', 'nc.exe']:
            severity = "HIGH"
            suspicious_processes.append(f"{proc['name']} on port {port}")
            
        # High value targets
        if port in [3389, 445, 22, 5432]:
            if severity != "HIGH": severity = "MEDIUM"
            if name == "unknown (system/protected)":
                suspicious_processes.append(f"Hidden System Process on Critical Port {port}")

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
