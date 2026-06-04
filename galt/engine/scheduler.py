import time
import subprocess
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from galt.core.config import get_storage_path

# Force UTF-8 on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()
vault_dir = get_storage_path("vault")
VAULT_FILE = os.path.join(vault_dir, "security_state.json")

# --- COMMERCIAL CONFIGURATION ---
# In the future, this will come from Firebase Remote Config
DEFAULT_TIER = "PRO" # Change to 'FREE' to test restriction
CLIENT_ID = os.getenv("GALT_CLIENT_ID", "UNKNOWN_CLIENT")

def get_current_score():
    if not os.path.exists(VAULT_FILE): return None
    try:
        with open(VAULT_FILE, "r") as f:
            return json.load(f).get("score")
    except: return None

def check_remote_config(client_id):
    """
    Simulates querying the cloud (Firebase) to get the user plan.
    Returns: (interval_seconds, plan_name, status_message)
    """
    # TODO: Here will be: response = requests.get(f"https://api.galt.ai/config/{client_id}")
    
    # Simulation logic "Pioneer"
    tier = os.getenv("SUBSCRIPTION_TIER", DEFAULT_TIER).upper()
    
    if tier == "PRO" or tier == "PIONEER":
        return 3600, tier, "🟢 ACTIVE PROTECTION (High Frequency)"
    elif tier == "FREE":
        return 86400, tier, "🟡 BASIC PROTECTION (Once a day)"
    elif tier == "EXPIRED":
        return 0, tier, "🔴 SUBSCRIPTION EXPIRED. Scan stopped."
    else:
        # Fallback safe
        return 86400, "UNKNOWN", "⚪ SAFE MODE (Default)"

def main_loop():
    print(f"👁️  GALT.AI SENTINEL: ACTIVE SURVEILLANCE")
    print(f"    Client ID: {CLIENT_ID}")
    print("--------------------------------------")
    
    # Test Mode: Overwrites everything for quick development
    if "--test" in sys.argv: 
        print("   [TEST MODE] Forced interval: 10 seconds")
        interval = 10
        plan_name = "TEST_DEV"
        status_msg = "🧪 TEST MODE"
    else:
        # First synchronization
        interval, plan_name, status_msg = check_remote_config(CLIENT_ID)

    print(f"   PLAN DETECTED: {plan_name}")
    print(f"   STATUS: {status_msg}")
    print(f"   FREQUENCY: {interval} seconds")
    print("--------------------------------------\n")

    if interval == 0:
        print("❌ Service is stopped due to lack of active license.")
        print("   Contact support or renew your subscription.")
        return

    try:
        while True:
            # 1. License Check before each round (Remote Sync)
            # This allows "turning off" or "improving" the service live without restarting
            if "--test" not in sys.argv:
                new_interval, new_plan, _ = check_remote_config(CLIENT_ID)
                if new_interval != interval:
                    print(f"\n🔄 REMOTE UPDATE: Changed to plan {new_plan}. New interval: {new_interval}s")
                    interval = new_interval
                
                if interval == 0:
                    print("\n⛔ SUBSCRIPTION EXPIRED. Stopping Sentinel.")
                    break

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ [{timestamp}] Scanning perimeter ({plan_name})...")
            
            score_before = get_current_score()
            
            # 2. Agent Execution
            # We call the same executable in "runner" mode or the module
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "runner"]
            else:
                 cmd = [sys.executable, "-m", "galt.engine.orchestrator"]
            
            # Pass --auto flag if applicable
            if "--auto" in sys.argv or interval > 60: 
                cmd.append("--auto")

            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print("❌ Error in Runner:")
                print(result.stderr)
            else:
                for line in result.stdout.splitlines():
                    if any(x in line for x in ["Score:", "DRIFT", "Silent Mode", "Modo Silencioso", "REPORT", "REPORTE", "DASHBOARD", "Abriendo", "Opening"]):
                        print(f"   > {line.strip()}")

            score_after = get_current_score()
            
            if score_before is not None and score_after is not None:
                if score_after > score_before:
                    print(f"   🟢 IMPROVEMENT: {score_before} -> {score_after} 🥂")
                elif score_after < score_before:
                    print(f"   🔴 ALERT: {score_before} -> {score_after} 😭")
            
            # 3. Sleep (Smart Sleep)
            # Print the next check to ease user anxiety
            next_run = round(interval / 60, 1)
            print(f"💤 Sleeping... Next scan in {next_run} minutes.")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Sentinel stopped.")

if __name__ == "__main__":
    main_loop()