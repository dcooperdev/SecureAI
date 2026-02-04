import os
import json
import time
from galt.ui import dashboard

def verify_history():
    print("🧪 Verifying Dashboard History Logic...")
    
    # Mock Data
    dummy_data = {
        "score": 85,
        "timestamp_human": "2026-02-04 12:00:00",
        "timestamp_epoch": int(time.time()),
        "findings": [],
        "ai_analysis": {"summary": "Test Run"},
        "status": "scanning" # Test spinner
    }
    
    # Generate Dashboard
    output_path = dashboard.generate_dashboard(dummy_data, dummy_data["ai_analysis"])
    
    # 1. Verify Timestamped File
    vault_dir = os.path.join(os.path.dirname(os.path.dirname(dashboard.BASE_DIR)), 'vault', 'reports')
    filename = f"scan_{dummy_data['timestamp_epoch']}.json"
    file_path = os.path.join(vault_dir, filename)
    
    if os.path.exists(file_path):
        print(f"✅ Timestamped file created: {filename}")
    else:
        print(f"❌ Failed to create timestamped file: {file_path}")
        
    # 2. Verify History Index
    history_path = os.path.join(vault_dir, 'history.json')
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            history = json.load(f)
            
        if history[0]['file'] == filename:
            print(f"✅ History index updated. Latest: {history[0]['label']}")
        else:
            print(f"❌ History index not updated correctly. Top: {history[0]}")
    else:
        print("❌ History file not found.")

    # 3. Verify HTML Content
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "loadHistory" in content and "scan-indicator" in content:
        print("✅ HTML contains new JS and CSS.")
    else:
        print("❌ HTML missing new features.")

if __name__ == "__main__":
    verify_history()
