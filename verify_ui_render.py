
import json
import os
import time
from galt.ui.dashboard import get_html_template
from galt.core.config import get_storage_path

def verify_ui_hotfix():
    print("--- Verifying UI Hotfix (Force Conversion) ---")
    
    # Mock Current Data (Memory-based)
    mock_current_data = {
        "score": 90,
        "ai_analysis": "### Hotfix Test\n- Item 1\n- Item 2",
        "timestamp": time.time()
    }
    
    # Call Generate HTML
    # Note: We pass mock_current_data. It should be processed IMMEDIATELY 
    # and put at index 0 of history, regardless of file system.
    html = get_html_template(mock_current_data, [], "/logo.png")
    
    # Assertions
    print("Checking for Header Render...")
    if "<h3>Hotfix Test</h3>" in html:
        print("✅ HTML Header Rendered (From Memory Data)")
    else:
        print("❌ HTML Header Failed")
        
    print("Checking for List Render...")
    if "<ul>" in html or "<li>" in html:
         print("✅ HTML List Rendered")
    else:
         print("❌ HTML List Failed")

if __name__ == "__main__":
    verify_ui_hotfix()
