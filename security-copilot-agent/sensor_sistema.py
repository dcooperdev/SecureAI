import platform
import json
import time
import socket
import getpass
import os
import hashlib
import sys
import argparse

def generate_event_id(plugin_name, time_window, host_id):
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def get_active_users():
    # Cross-platform way to get at least the current user
    try:
        current_user = getpass.getuser()
        # On Windows, 'query user' gives more info but requires parsing. 
        # For this MVP/Suite, we return the running user and list env vars if relevant/safe.
        # We will return a list for extensibility.
        return [current_user]
    except:
        return ["unknown"]

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-only", action="store_true")
    args, unknown = parser.parse_known_args()

    PLUGIN_NAME = "sensor_sistema"
    timestamp = str(int(time.time()))
    host_id = platform.node()

    # System Info Collection
    sys_info = {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "hostname": host_id,
        "active_users": get_active_users(),
        "processor": platform.processor()
    }

    payload = {
        "event_id": generate_event_id(PLUGIN_NAME, timestamp, host_id),
        "timestamp": timestamp,
        "plugin": PLUGIN_NAME,
        "result": {
            "severity": "INFO",
            "data": sys_info,
            "impact_hint": "Inventory of host system details."
        }
    }

    # Print JSON to stdout for the runner
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    run()
