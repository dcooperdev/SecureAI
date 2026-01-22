import psutil
import json
import time
import argparse
import platform
import hashlib
import subprocess
import re
import sys

# --- Utility Functions ---

def generate_event_id(plugin_name: str, time_window: str, host_id: str) -> str:
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_process_name_by_pid_fallback(pid):
    """
    Cross-platform fallback to get process name if psutil fails.
    """
    system = platform.system()
    try:
        if system == "Windows":
            # tasklist /FI "PID eq 1234" /FO CSV /NH
            cmd = f'tasklist /FI "PID eq {pid}" /FO CSV /NH'
            output = subprocess.check_output(cmd, shell=True).decode(errors='ignore').strip()
            if output and '"' in output:
                parts = output.split('","')
                if len(parts) > 0:
                    return parts[0].replace('"', '')
        else: # Linux / macOS
            # ps -p 1234 -o comm=
            cmd = ['ps', '-p', str(pid), '-o', 'comm=']
            output = subprocess.check_output(cmd).decode(errors='ignore').strip()
            if output:
                return output
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
        name = get_process_name_by_pid_fallback(pid)
        return {
            "name": name,
            "pid": pid,
            "username": "SYSTEM/Protected",
            "status": "running",
            "exe": "AccessDenied"
        }

def get_netstat_map():
    """
    Cross-platform native port-to-PID mapping.
    """
    mapping = {}
    system = platform.system()
    
    try:
        if system == "Windows":
            output = subprocess.check_output("netstat -ano", shell=True).decode(errors='ignore')
            lines = output.splitlines()
            for line in lines:
                line = line.strip()
                parts = re.split(r'\s+', line)
                if len(parts) >= 4 and parts[-1].isdigit():
                    pid = int(parts[-1])
                    local_addr = parts[1]
                    if ':' in local_addr:
                        port_str = local_addr.rsplit(':', 1)[-1]
                        if port_str.isdigit():
                            mapping[int(port_str)] = pid

        elif system == "Linux":
            # Use 'ss -lntp' (Socket Statistics) which is standard on modern Linux
            output = subprocess.check_output(["ss", "-lntp"], stderr=subprocess.DEVNULL).decode(errors='ignore')
            for line in output.splitlines():
                if "LISTEN" in line:
                    match = re.search(r':(\d+)\s+.*pid=(\d+)', line)
                    if match:
                        port = int(match.group(1))
                        pid = int(match.group(2))
                        mapping[port] = pid

        elif system == "Darwin": # macOS
            # Use lsof. macOS netstat doesn't show PIDs.
            output = subprocess.check_output(["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"], stderr=subprocess.DEVNULL).decode(errors='ignore')
            for line in output.splitlines()[1:]: # Skip header
                parts = re.split(r'\s+', line)
                if len(parts) >= 9:
                    pid = parts[1]
                    address_part = parts[-2] if "LISTEN" in parts[-1] else parts[-1] 
                    if ':' in address_part:
                        port_str = address_part.rsplit(':', 1)[-1]
                        if port_str.isdigit() and pid.isdigit():
                            mapping[int(port_str)] = int(pid)

    except Exception:
        pass
    return mapping

def main():
    parser = argparse.ArgumentParser(description="Galt.ai Process Sensor")
    parser.add_argument("--local-only", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    PLUGIN_NAME = "sensor_procesos"
    CRITICAL_PORTS = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
        135: "RPC", 139: "NetBIOS", 443: "HTTPS", 445: "SMB", 1433: "MSSQL",
        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-Alt",
        27017: "MongoDB"
    }

    active_processes = []
    netstat_lookup = None 
    target_pids = set()
    
    try:
        connections = psutil.net_connections(kind='inet')
        found_ports = set()
        
        # Pass 1: Listeners via psutil
        for conn in connections:
            if conn.status == psutil.CONN_LISTEN or conn.status == psutil.CONN_ESTABLISHED:
                local_port = conn.laddr.port
                if local_port in CRITICAL_PORTS:
                    found_ports.add(local_port)
                    pid = conn.pid
                    if pid is None:
                        if netstat_lookup is None: netstat_lookup = get_netstat_map()
                        pid = netstat_lookup.get(local_port)
                    
                    if pid: target_pids.add(pid)
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
        
        # Pass 2: Shadow Listeners via Native Command
        if netstat_lookup is None: netstat_lookup = get_netstat_map()
        for port, pid in netstat_lookup.items():
            if port in CRITICAL_PORTS and port not in found_ports:
                if pid: target_pids.add(pid)
                proc_info = get_process_info(pid)
                if proc_info:
                    active_processes.append({
                        "port": port,
                        "service": CRITICAL_PORTS[port],
                        "status": "LISTEN (Native)",
                        "process": proc_info,
                        "remote_ip": None,
                        "source": "native_deep_scan"
                    })

        # Pass 3: Outbound from targets
        def is_external(ip):
            if not ip: return False
            if ip.startswith(("127.", "10.", "192.168.", "169.254.")): return False
            if ip.startswith("172.") and 16 <= int(ip.split('.')[1]) <= 31: return False
            return True

        for conn in connections:
            if conn.status == psutil.CONN_ESTABLISHED and conn.pid in target_pids:
                 remote_ip = conn.raddr.ip if conn.raddr else None
                 if remote_ip and is_external(remote_ip):
                     proc_info = get_process_info(conn.pid)
                     if proc_info:
                         active_processes.append({
                             "port": conn.laddr.port,
                             "service": "OUTBOUND_TRAFFIC",
                             "status": "ESTABLISHED (External)",
                             "process": proc_info,
                             "remote_ip": remote_ip
                         })

    except Exception:
        pass

    severity = "INFO"
    impact_hint = "No critical processes found."
    if active_processes:
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
