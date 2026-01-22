import subprocess
import re
from typing import Dict, Any, List
from core.constants import Severity, CURRENT_CONTRACT_VERSION

PLUGIN_META = {
    "name": "net_scanner",
    "version": "1.0",
    "requires_admin": False,
    "contract_version": CURRENT_CONTRACT_VERSION
}

def run() -> Dict[str, Any]:
    """
    Executes a local network discovery using ARP scan.
    """
    try:
        # Run arp -a
        # In production, we might want to use a more robust library, but requirement is ARP or subprocess
        # 'arp -a' works on both Windows and Linux usually.
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0:
            if "Permission" in result.stderr:
                 raise PermissionError("ARP capability blocked")
            return {
                "severity": Severity.LOW.value,
                "impact_hint": "ARP scan returned non-zero. Network might be unreachable.",
                "data": []
            }

        output = result.stdout
        devices = parse_arp_output(output)
        
        return {
            "severity": Severity.LOW.value, # Information gathering
            "impact_hint": f"Discovered {len(devices)} devices on local network.",
            "data": devices
        }

    except PermissionError:
        return {
            "severity": Severity.MED.value,
            "impact_hint": "Missing network privileges. We cannot detect unauthorized devices (rogue access points) on your local network.",
            "message": "Insufficient Privileges"
        }
    except Exception as e:
        # Graceful degradation
        return {
            "severity": Severity.LOW.value, 
            "message": f"Network scan failed safely: {str(e)}",
            "impact_hint": "Network discovery unavailable."
        }

def parse_arp_output(output: str) -> List[Dict[str, str]]:
    devices = []
    # Simple regex for IP and MAC
    # 192.168.1.1       ab-cd-ef-12-34-56
    for line in output.splitlines():
        line = line.strip()
        if not line: continue
        
        # Heuristic: Find IP and Mac
        # IP: \d+\.\d+\.\d+\.\d+
        # Mac: (?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
        mac_match = re.search(r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
        
        if ip_match and mac_match:
            devices.append({
                "ip": ip_match.group(),
                "mac": mac_match.group()
            })
    return devices
