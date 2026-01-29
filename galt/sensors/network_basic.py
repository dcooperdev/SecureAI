import json
import time
import platform
import socket
import hashlib

def generate_event_id(plugin_name, time_window, host_id):
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    PLUGIN_NAME = "sensor_network_basic"
    timestamp = str(int(time.time()))
    host_id = platform.node()
    
    local_ip = get_local_ip()
    hostname = socket.gethostname()
    
    event_id = generate_event_id(PLUGIN_NAME, timestamp, host_id)
    
    result = {
        "local_ip": local_ip,
        "hostname": hostname,
        "severity": "INFO",
        "description": f"Host is active at {local_ip}"
    }
    
    payload = {
        "event_id": event_id,
        "timestamp": timestamp,
        "plugin": PLUGIN_NAME,
        "result": result
    }
    
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
