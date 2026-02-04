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

# --- Extended Utility Functions ---

def get_mac_address(ip):
    """Resolve MAC address using local ARP table."""
    try:
        # Windows: arp -a <ip>
        if platform.system().lower() == "windows":
            cmd = ["arp", "-a", ip]
            output = subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW).decode("cp850", errors="ignore") # cp850 specific to some windows locales, or just 'mbcs'
            import re
            # Pattern for MAC address (Windows format: 00-11-22...)
            matches = re.findall(r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})", output)
            if matches:
                return matches[0].replace("-", ":").upper()
        else:
            # Linux/Mac implementation (skipped for this Windows-focused MVP, assuming usage on PC-David)
            pass
    except Exception:
        pass
    return "N/A"

def get_default_gateway():
    """Get default gateway IP."""
    try:
        # Windows specific
        output = subprocess.check_output("ipconfig", creationflags=subprocess.CREATE_NO_WINDOW).decode("cp850", errors="ignore")
        import re
        # Look for "Default Gateway . . . . . . . . . : 192.168.1.1"
        # Adapting to Spanish/English: "Puerta de enlace predeterminada" or "Default Gateway"
        lines = output.split('\n')
        for line in lines:
            if "0.0.0.0" in line: continue 
            if "Gateway" in line or "enlace" in line:
                match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                if match:
                    return match.group(1)
    except:
        pass
    return None

def calculate_risk(open_ports, hostname):
    """Determine risk level text."""
    risk_score = 0
    critical_ports = {445: 'SMB', 3389: 'RDP', 5432: 'DB', 22: 'SSH'}
    
    exposed = []
    for p in open_ports:
        if p in critical_ports:
            risk_score += 10
            exposed.append(critical_ports[p])
    
    if risk_score >= 10:
        return f"HIGH ({', '.join(exposed)})"
    elif open_ports:
        return f"MEDIUM ({len(open_ports)} ports)"
    return "LOW"

def scan_target(ip, common_ports, results, lock, gateway_ip):
    if ping_host(ip):
        hostname = resolve_hostname(ip)
        open_ports = scan_ports(ip, common_ports)
        mac = get_mac_address(ip)
        
        is_gw = (ip == gateway_ip)
        risk_label = calculate_risk(open_ports, hostname)
        if is_gw: risk_label = "GATEWAY (Critical)"

        with lock:
            results.append({
                "ip_address": ip, # Renamed from 'ip' to match UI
                "hostname": hostname or "Unknown",
                "mac_address": mac,
                "open_ports": open_ports,
                "is_gateway": is_gw,
                "risk_label": risk_label,
                "status": "ONLINE"
            })

def main():
    parser = argparse.ArgumentParser(description="Galt.ai Network Discovery Sensor")
    parser.add_argument("--local-only", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    PLUGIN_NAME = "sensor_network_discovery"
    
    # "Fingerprinting de Servicios (Top Ports)"
    COMMON_PORTS = [21, 22, 80, 443, 445, 3389, 5432, 8080, 27017, 139]

    local_ip, subnet_base = get_local_ip_and_subnet()
    gateway_ip = get_default_gateway()
    
    discovered_hosts = []
    lock = threading.Lock()
    
    # Threaded Ping Sweep
    # Limiting to 254 hosts
    targets = [f"{subnet_base}.{i}" for i in range(1, 255)]
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        for ip in targets:
            executor.submit(scan_target, ip, COMMON_PORTS, discovered_hosts, lock, gateway_ip)
            
    # Analysis
    severity = "INFO"
    impact_hint = f"Discovered {len(discovered_hosts)} active hosts."
    
    # Sort by IP for cleanliness
    try:
        discovered_hosts.sort(key=lambda x: int(x['ip_address'].split('.')[-1]))
    except: pass

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
            "local_ip": local_ip,
            "gateway_ip": gateway_ip
        }
    }
    
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
