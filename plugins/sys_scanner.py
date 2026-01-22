import platform
import os
from core.constants import Severity

PLUGIN_META = {
    "name": "system_scanner",
    "version": "1.0",
    "requires_admin": False,
    "contract_version": "1.0"
}

def run():
    # Example logic: Scan generic system info
    try:
        # Simulate a sensitive path finding
        # In a real scanner, we might look at files
        user_path = os.path.expanduser("~")
        
        return {
            "severity": Severity.LOW,
            "impact_hint": "Basic system information for inventory.",
            "data": {
                "os": platform.system(),
                "release": platform.release(),
                "user_home": user_path # this will need sanitization
            }
        }
    except PermissionError:
        # This catch is technically redundant if the orchestrator handles it, 
        # but the prompt says "If a plugin fails... IT must catch it" 
        # Wait, "If a plugin fails... it must catch it and return a MED severity result"
        # So the plugin itself is responsible? Or the orchestrator?
        # Prompt: "Privilege Handling: If a plugin fails due to PermissionError, it must catch it and return a MED severity result stating 'Insufficient Privileges'."
        # This implies the plugin wraps its logic.
        return {
            "severity": Severity.MED,
            "message": "Insufficient Privileges",
            "impact_hint": "Scanner blocked from accessing required resources."
        }
