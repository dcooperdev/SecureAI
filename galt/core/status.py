import json
import os
import time
from galt.core.config import get_storage_path

def get_status_file_path():
    return os.path.join(get_storage_path("reports"), "live_status.js")

def update_status(state, message="System idle", score="--"):
    """
    Writes a valid JS file.
    state: 'IDLE' | 'SCANNING' | 'ERROR'
    """
    # Save timestamp to avoid caching and to show update time
    payload = {
        "state": state,
        "message": message,
        "score": str(score),
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    # Write a call to a global function window.updateDashboardState(...)
    # This avoids CORS issues that a pure JSON would have.
    js_content = f"window.updateDashboardState({json.dumps(payload)});"
    
    try:
        report_dir = get_storage_path("reports")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        with open(get_status_file_path(), "w", encoding="utf-8") as f:
            f.write(js_content)
    except Exception as e:
        print(f"Error writing status: {e}")

# Initial state on import
# update_status("IDLE", "System ready")
