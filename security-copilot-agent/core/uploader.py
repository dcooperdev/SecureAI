import hashlib
import time

def generate_event_id(plugin_name: str, timestamp: str, host_id: str) -> str:
    """
    Generates a unique event ID using SHA256 of plugin_name + timestamp + host_id.
    """
    raw_str = f"{plugin_name}{timestamp}{host_id}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def upload_event(event_data: dict, local_only: bool = False):
    """
    Uploads the event or prints it if local_only is True.
    """
    if local_only:
        import json
        print(json.dumps(event_data, indent=2, default=str)) # default=str for Enum serialization
    else:
        # PII Check (Double check, though orchestration should have sanitized)
        # TODO: Implement Firebase Bridge
        # For now, we mock the upload
        pass
