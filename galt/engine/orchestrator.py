import subprocess
import json
import os
import sys
import argparse
import time
import hashlib

# Force UTF-8 encoding for stdout on Windows to handle emojis
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
from datetime import datetime

from google import genai
from dotenv import load_dotenv
from galt.core.config import get_storage_path, get_api_key
from galt.ui.narrator import OfflineNarrator
from galt.ui.formatter import GaltReportFormatter
from galt.core import status as status_manager
from galt.engine.bridge import Bridge

load_dotenv()

# --- UTILITIES AND CONFIGS ---

api_key = get_api_key()

def get_client_id() -> str:
    """
    Generates a stable, anonymous machine ID derived from the hostname and
    current username. The result is a deterministic short hash that persists
    across restarts without storing any sensitive data.
    """
    import platform
    raw = f"{platform.node()}:{os.getenv('USERNAME', os.getenv('USER', 'unknown'))}"
    return "GALT-" + hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

def save_json_data(data):
    """Saves structured telemetry to JSON for future migration to Firebase."""
    reports_dir = get_storage_path("reports/data")
    if not os.path.exists(reports_dir): os.makedirs(reports_dir)
    filename = os.path.join(reports_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

from galt.ui import dashboard as dashboard_generator


def run_security_flow():
    # START
    status_manager.update_status("SCANNING", "Starting analysis...")
    
    # FIX: Initialize 'latest.json' with scanning state so UI spinner activates
    try:
        vault_dir = get_storage_path("vault")
        reports_dir = os.path.join(vault_dir, "reports")
        if not os.path.exists(reports_dir): os.makedirs(reports_dir)
        latest_file = os.path.join(reports_dir, 'latest.json')
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "scanning",
                "timestamp_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "score": 0,
                "ai_status": "offline",
                "ai_analysis": {"summary": "Analysis in progress..."},
                "findings": []
            }, f, indent=4)
    except Exception as e:
        print(f"⚠️ Could not write initial scanning state: {e}", file=sys.stderr)
    
    # 0. Argument Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Automatic mode (no pop-ups unless critical)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🛡️  GALT.AI v2: COMPREHENSIVE CISO PLATFORM")
    print("="*60)

    # Mapping: Module Name -> Dispatcher Key (Legacy/Frozen)
    sensor_map = {
        "galt.sensors.processes": "sensor_procesos",
        "galt.sensors.network_basic": "sensor_red",
        "galt.sensors.system": "sensor_sistema",
        "galt.sensors.vuln": "sensor_vulnerabilidades",
        "galt.sensors.network_scan": "sensor_network_discovery"
    }

    # In compiled/monolith mode, we use the dispatcher keys
    print(f"🔎 Autodiscovery: Starting modular sensors (Dispatcher Mode).\n", file=sys.stderr)

    all_data = []

    # 2. Execution & Aggregation
    for module_name, dispatch_key in sensor_map.items():
        print(f"🚀 Running module: {module_name}...", file=sys.stderr)
        try:
            # DUAL MODE: Frozen vs Source
            if getattr(sys, 'frozen', False):
                # Compiled: GaltAI.exe [dispatch_key]
                command = [sys.executable, dispatch_key, "--local-only"]
            else:
                # Source: python -m galt.sensors.xxx
                command = [sys.executable, "-m", module_name, "--local-only"]
            
            process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = process.communicate()
            
            # Reconstruct JSON objects
            potential_objects = stdout.split('"event_id":')
            count_new = 0
            for obj_part in potential_objects:
                if not obj_part.strip(): continue
                json_str = '{"event_id":' + obj_part.strip()
                last_brace = json_str.rfind('}')
                if last_brace != -1: json_str = json_str[:last_brace+1]
                try:
                    data = json.loads(json_str)
                    all_data.append(data)
                    count_new += 1
                except json.JSONDecodeError: continue
            print(f"   ✅ Data collected: {count_new} events.", file=sys.stderr)
        except Exception as e:
            print(f"   ❌ Failure in {dispatch_key}: {e}", file=sys.stderr)
            continue

    if not all_data:
        status_manager.update_status("IDLE", "No data detected")
        return

    # 2.1 Internal Sensors (Log Sentinel)
    try:
        from galt.core.log_watcher import LogSentinel
        print(f"🚀 Running internal module: LogSentinel...", file=sys.stderr)
        sentinel = LogSentinel()
        log_findings = sentinel.scan()
        if log_findings:
            all_data.extend(log_findings)
            print(f"   ✅ LogSentinel: {len(log_findings)} anomalies detected.", file=sys.stderr)
    except Exception as e:
        print(f"   ⚠️ Failure in LogSentinel: {e}", file=sys.stderr)

    # 3. Scoring
    security_score = 100
    for event in all_data:
        severity = event.get("result", {}).get("severity", "INFO").upper()
        if severity == "HIGH": security_score -= 40
        elif severity == "MEDIUM": security_score -= 15
        elif severity == "LOW": security_score -= 5
    if security_score < 0: security_score = 0
    
    # 4. Persistence & Drift
    vault_dir = get_storage_path("vault")
    if not os.path.exists(vault_dir): os.makedirs(vault_dir)
    state_file = os.path.join(vault_dir, "security_state.json")
    
    previous_score = None
    previous_findings = []
    
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                last_state = json.load(f)
                previous_score = last_state.get("score")
                previous_findings = last_state.get("findings", [])
        except: pass

    drift_detected = False
    change_context = ""
    
    if previous_score is None:
        change_context = "Starting security baseline."
        drift_detected = True # First run is always significant
    elif security_score != previous_score:
        drift_detected = True
        change_context = f"POSTURE CHANGE: Score changed from {previous_score} to {security_score}."
    else:
        change_context = "Stable posture. No changes in Score."

    # 5. AI Analysis (via Bridge)
    print(f"\n🧠 Galt.ai Intelligence: Analyzing with Bridge (Smart Cache)...")
    print(f"📊 Score: {security_score}/100 (Previous: {previous_score})")

    bridge = Bridge(data_dir=vault_dir)
    analysis_result = bridge.get_analysis(all_data, security_score)
    
    ai_json = analysis_result.get("json_report", {})
    ai_status = analysis_result.get("ai_status", "offline") # online, cached, offline

    print(f"   ℹ️ AI Status: {ai_status.upper()}")
    if analysis_result.get("error"):
         print(f"   ⚠️ Internal Bridge Error: {analysis_result['error']}", file=sys.stderr)



    try:
        # 6. Save Data & Dashboard
        # Prepare Open Ports Data (Decoupled UI Logic)
        open_ports = set()
        for f in all_data:
            res = f.get("result", {})
            plugin = f.get("plugin", "")
            
            # Vulns & Processes
            if plugin in ["sensor_vulnerabilidades", "sensor_procesos"]:
                data = res.get("data", [])
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, int): open_ports.add(item)
                        elif isinstance(item, dict) and "port" in item: open_ports.add(item["port"])
            
            # Network Discovery
            if plugin == "sensor_network_discovery":
                data = res.get("data", [])
                if isinstance(data, list):
                    for host in data:
                        h_ports = host.get("open_ports", [])
                        if isinstance(h_ports, list):
                            for p in h_ports: open_ports.add(p)

        final_payload = {
            "client_id": get_client_id(),
            "timestamp_epoch": int(time.time()),
            "timestamp_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": security_score,
            "findings": all_data,
            "open_ports": list(open_ports), # Explicitly passed for UI
            "ai_analysis": ai_json, # JSON OBJECT
            "ai_status": ai_status
        }
        
        json_path = save_json_data(final_payload)
        
        # GENERATE DASHBOARD (Template Injection Mode)
        dashboard_path = dashboard_generator.generate_dashboard(
            scan_results=final_payload,
            ai_analysis_data=ai_json
        )
        
        # 2. Save/Overwrite "Latest" (For Tray/Auto-Reload)
        if dashboard_path:
            reports_dir = os.path.dirname(dashboard_path)
            latest_path = os.path.join(reports_dir, "dashboard.html")
            
            # Only copy if paths are different [Fix for WinError 32]
            if os.path.abspath(dashboard_path).lower() != os.path.abspath(latest_path).lower():
                import shutil
                shutil.copy2(dashboard_path, latest_path)
                print(f"   ✅ Main dashboard updated: {latest_path}")
            else:
                 print(f"   ✅ Dashboard generated in: {dashboard_path}")
        
        # --- FINAL NOTIFICATION ---
        try:
            from galt.core.notifier import Notifier
            notifier = Notifier()
            
            # Determine icon path safely
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            # Notifier implementation handles icons internally or system default, 
            # but we pass the message. The new Notifier.send_notification 
            # takes (title, message).
            
            # Determine click URI (prefer latest static 'dashboard.html' if copy succeeded)
            click_target = latest_path if 'latest_path' in locals() and latest_path else (dashboard_path if dashboard_path else None)

            notifier.send_notification(
                title='Galt.ai Finished',
                message=f'Security scan complete.\nScore: {security_score}/100\nClick to view details.',
                click_action=click_target
            )
            print(f"🔔 Interactive notification sent (Target: {click_target})")
        except Exception as e:
            print(f"Error sending notification: {e}")

        if dashboard_path:
             print(f"\n✅ REPORT GENERATED: {dashboard_path}")
        else:
             print("\n❌ Error generating HTML report.")
             
        print("   Use the System Tray icon to view it.")
        
        # 7. Update Vault & Check Drift
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time()), "score": security_score, "findings": all_data}, f)

        # Drift Logic
        drift_detected = (security_score != previous_score) if previous_score is not None else True
        
        if drift_detected:
            print("\n🚨 DRIFT DETECTED: Score has changed.")
        else:
            print("\n🤫 Stable posture.")

        # Optional: Auto-open if critical?
        # For now, we rely on notifications. 
        # should_open = drift_detected and security_score < 50
        
        # SUCCESSFUL FINISH
        status_manager.update_status("IDLE", "Analysis completed", score=security_score)
        
    except Exception as e:
        # FINISH WITH ERROR
        status_manager.update_status("IDLE", "Error in analysis")
        print(f"❌ Error in Report/Save flow: {e}")

if __name__ == "__main__":
    run_security_flow()