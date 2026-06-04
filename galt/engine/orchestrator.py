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
    """Guarda la telemetría estructurada en JSON para futura migración a Firebase."""
    reports_dir = get_storage_path("reports/data")
    if not os.path.exists(reports_dir): os.makedirs(reports_dir)
    filename = os.path.join(reports_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

from galt.ui import dashboard as dashboard_generator


def run_security_flow():
    # INICIO
    status_manager.update_status("SCANNING", "Iniciando análisis...")
    
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
                "ai_analysis": {"summary": "Análisis en curso..."},
                "findings": []
            }, f, indent=4)
    except Exception as e:
        print(f"⚠️ Could not write initial scanning state: {e}", file=sys.stderr)
    
    # 0. Argument Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Modo automático (sin pop-ups a menos que sea crítico)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🛡️  GALT.AI v2: PLATAFORMA INTEGRAL CISO")
    print("="*60)

    # Mapeo: Nombre del Modulo -> Clave del Dispatcher (Legacy/Frozen)
    sensor_map = {
        "galt.sensors.processes": "sensor_procesos",
        "galt.sensors.network_basic": "sensor_red",
        "galt.sensors.system": "sensor_sistema",
        "galt.sensors.vuln": "sensor_vulnerabilidades",
        "galt.sensors.network_scan": "sensor_network_discovery"
    }

    # En modo compilado/monolito, usamos las claves del dispatcher
    print(f"🔎 Autodiscovery: Iniciando sensores modulares (Dispatcher Mode).\n", file=sys.stderr)

    all_data = []

    # 2. Execution & Aggregation
    for module_name, dispatch_key in sensor_map.items():
        print(f"🚀 Ejecutando módulo: {module_name}...", file=sys.stderr)
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
            print(f"   ✅ Datos recolectados: {count_new} eventos.", file=sys.stderr)
        except Exception as e:
            print(f"   ❌ Fallo en {dispatch_key}: {e}", file=sys.stderr)
            continue

    if not all_data:
        status_manager.update_status("IDLE", "No se detectaron datos")
        return

    # 2.1 Internal Sensors (Log Sentinel)
    try:
        from galt.core.log_watcher import LogSentinel
        print(f"🚀 Ejecutando módulo interno: LogSentinel...", file=sys.stderr)
        sentinel = LogSentinel()
        log_findings = sentinel.scan()
        if log_findings:
            all_data.extend(log_findings)
            print(f"   ✅ LogSentinel: {len(log_findings)} anomalías detectadas.", file=sys.stderr)
    except Exception as e:
        print(f"   ⚠️ Fallo en LogSentinel: {e}", file=sys.stderr)

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
        change_context = "Iniciando línea base de seguridad."
        drift_detected = True # First run is always significant
    elif security_score != previous_score:
        drift_detected = True
        change_context = f"CAMBIO DE POSTURA: Score pasó de {previous_score} a {security_score}."
    else:
        change_context = "Postura estable. Sin cambios en el Score."

    # 5. AI Analysis (via Bridge)
    print(f"\n🧠 Galt.ai Intelligence: Analizando con Bridge (Smart Cache)...")
    print(f"📊 Score: {security_score}/100 (Anterior: {previous_score})")

    bridge = Bridge(data_dir=vault_dir)
    analysis_result = bridge.get_analysis(all_data, security_score)
    
    ai_json = analysis_result.get("json_report", {})
    ai_status = analysis_result.get("ai_status", "offline") # online, cached, offline

    print(f"   ℹ️ Estado AI: {ai_status.upper()}")
    if analysis_result.get("error"):
         print(f"   ⚠️ Error interno Bridge: {analysis_result['error']}", file=sys.stderr)



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
                print(f"   ✅ Dashboard principal actualizado: {latest_path}")
            else:
                 print(f"   ✅ Dashboard generado en: {dashboard_path}")
        
        # --- 6. NOTIFICACIÓN FINAL ---
        # --- 6. NOTIFICACIÓN FINAL (NATIVA) ---
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
                title='Galt.ai Finalizado',
                message=f'Análisis de Seguridad completo.\nScore: {security_score}/100\nClick para ver detalles.',
                click_action=click_target
            )
            print(f"🔔 Notificación Interactiva enviada (Target: {click_target})")
        except Exception as e:
            print(f"Error enviando notificación: {e}")

        if dashboard_path:
             print(f"\n✅ REPORTE GENERADO: {dashboard_path}")
        else:
             print("\n❌ Error generando reporte HTML.")
             
        print("   Usa el icono del System Tray para verlo.")
        
        # 7. Update Vault & Check Drift
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time()), "score": security_score, "findings": all_data}, f)

        # Drift Logic
        drift_detected = (security_score != previous_score) if previous_score is not None else True
        
        if drift_detected:
            print("\n🚨 DRIFT DETECTADO: Score ha cambiado.")
        else:
            print("\n🤫 Postura estable.")

        # Optional: Auto-open if critical?
        # For now, we rely on notifications. 
        # should_open = drift_detected and security_score < 50
        
        # FIN EXITOSO
        status_manager.update_status("IDLE", "Análisis completado", score=security_score)
        
    except Exception as e:
        # FIN CON ERROR
        status_manager.update_status("IDLE", "Error en análisis")
        print(f"❌ Error en flujo Reporte/Guardado: {e}")

if __name__ == "__main__":
    run_security_flow()