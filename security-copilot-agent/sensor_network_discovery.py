import socket
import threading
import json
import time
import argparse
import platform
import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor

# --- Utility Functions ---

def generate_event_id(plugin_name: str, time_window: str, host_id: str) -> str:
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_local_ip_and_subnet():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Assume /24 for simplicity in this MVP
        subnet_base = ".".join(local_ip.split(".")[:3])
        return local_ip, subnet_base
    except Exception:
        return "127.0.0.1", "127.0.0"

def ping_host(ip):
    # Cross-platform ping
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '200', ip] # 200ms timeout
    try:
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def resolve_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        # Try NetBIOS via nbtstat on Windows if socket resolution fails? 
        # For MVP, just return None or try aggressive lookup?
        return None

def scan_ports(ip, ports):
    open_ports = []
    for port in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3) # Fast timeout
        try:
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
        except:
            pass
        finally:
            s.close()
    return open_ports

def scan_target(ip, common_ports, results, lock):
    if ping_host(ip):
        hostname = resolve_hostname(ip)
        open_ports = scan_ports(ip, common_ports)
        
        # Only report if interesting (ports open or hostname found) or just report all active?
        # User wants "Mirror Systems", so we need to know if they have ports open.
        
        with lock:
            results.append({
                "ip": ip,
                "hostname": hostname,
                "open_ports": open_ports,
                "status": "ONLINE"
            })

def main():
    parser = argparse.ArgumentParser(description="Galt.ai Network Discovery Sensor")
    parser.add_argument("--local-only", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    PLUGIN_NAME = "sensor_network_discovery"
    
    # "Fingerprinting de Servicios (Top Ports)"
    COMMON_PORTS = [21, 22, 80, 443, 445, 3389, 5432, 8080, 27017, 139] # Added 139, 27017, 5432 as requested

    local_ip, subnet_base = get_local_ip_and_subnet()
    
    discovered_hosts = []
    lock = threading.Lock()
    
    # Threaded Ping Sweep
    # Limiting to 254 hosts
    targets = [f"{subnet_base}.{i}" for i in range(1, 255)]
    # Filter out current host? Or duplicate?
    # Better to keep it to see if we see ourselves correctly
    
    # We use a large thread pool for speed
    with ThreadPoolExecutor(max_workers=50) as executor:
        for ip in targets:
            executor.submit(scan_target, ip, COMMON_PORTS, discovered_hosts, lock)
            
    # Analysis
    severity = "INFO"
    impact_hint = f"Discovered {len(discovered_hosts)} active hosts in subnet {subnet_base}.0/24."
    
    # Identifying Mirror Systems logic will happen in the Runner/AI (comparing results), 
    # but we can flag high risk local services here too.
    
    suspicious_neighbors = []
    for host in discovered_hosts:
        if 445 in host['open_ports'] or 3389 in host['open_ports'] or 5432 in host['open_ports']:
            suspicious_neighbors.append(host['ip'])
            
    if suspicious_neighbors:
        impact_hint += f" {len(suspicious_neighbors)} neighbors exposing critical ports."

    timestamp = str(int(time.time()))
    host_id = platform.node()
    event_id = generate_event_id(PLUGIN_NAME, timestamp, host_id)
    
    payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "plugin": PLUGIN_NAME,
        "result": {
            "severity": severity,
            "data": discovered_hosts,
            "impact_hint": impact_hint,
            "local_ip": local_ip # Useful for AI context
        }
    }
    
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
