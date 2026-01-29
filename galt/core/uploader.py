import hashlib
import time
from typing import Dict, Any

def generate_event_id(plugin_name: str, time_window: str, host_id: str) -> str:
    """
    Generates a unique event ID using SHA256 of plugin_name + time_window + host_id.
    """
    raw_str = f"{plugin_name}{time_window}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def upload_event(event_data: Dict[str, Any], local_only: bool = False) -> None:
    """
    Uploads the event or prints it if local_only is True.
    """
    if local_only:
        import json
        print(json.dumps(event_data, indent=2, default=str))
    else:
        # Mock Upload
        pass
