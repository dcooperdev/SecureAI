import subprocess
import json
import os
import sys
import webbrowser
import argparse
import time

# Force UTF-8 encoding for stdout on Windows to handle emojis
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
from datetime import datetime
from google import genai
from dotenv import load_dotenv
from config import get_storage_path, get_api_key

load_dotenv()

# --- CONFIGURACIÓN Y UTILIDADES ---

# --- CONFIGURACIÓN Y UTILIDADES ---

api_key = get_api_key()
# Configure client safely - if no key, calls will fail and be caught in the try/except block later
if api_key:
    client = genai.Client(api_key=api_key)
else:
    # Objeto dummy o manejaremos error en uso
    class DummyClient:
        class models:
            def generate_content(*args, **kwargs):
                raise ValueError("API Key no configurada")
    client = DummyClient()

def save_json_data(data):
    """Guarda la telemetría estructurada en JSON para futura migración a Firebase."""
    reports_dir = get_storage_path("reports/data")
    if not os.path.exists(reports_dir): os.makedirs(reports_dir)
    filename = os.path.join(reports_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

import dashboard_generator
from plyer import notification

# ...

def generate_dashboard_html(score, report_md, json_path, client_id="LOCAL_PIONEER"):
    """Genera un Dashboard HTML moderno usando el generador externo y lo guarda."""
    try:
        # Determine assets path
        # Build mode: sys._MEIPASS | Script mode: current dir
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_path, "logo.png")
        
        # Prepare Data
        data = {
            "score": score,
            "client_id": client_id,
            "ai_analysis": report_md # This needs markdown to html conversion if we want rich text, 
                                     # but for now we inject raw or pre-render in runner if needed.
                                     # Actually, let's keep it simple.
        }
        
        # We need to convert markdown report_md to HTML for better display? 
        # For this step, we just wrap it in a pre or div.
        # But wait, dashboard_generator injects it directly.
        
        # Generate History Links
        storage = get_storage_path("reports")
        history_links = dashboard_generator.generate_history_html(storage)
        
        # Generate Content
        html_content = dashboard_generator.get_html_template(data, history_links, logo_path)
        
        # Save
        reports_dir = get_storage_path("reports")
        if not os.path.exists(reports_dir): os.makedirs(reports_dir)
        
        filename = os.path.join(reports_dir, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return filename
    except Exception as e:
        print(f"Error generando dashboard: {e}")
        return None
    """
    

    
    reports_dir = get_storage_path("reports")
    path = os.path.join(reports_dir, "dashboard.html")
    if not os.path.exists(reports_dir): os.makedirs(reports_dir)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return os.path.abspath(path)

def run_security_flow():
    # 0. Argument Parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Modo automático (sin pop-ups a menos que sea crítico)")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("🛡️  GALT.AI v2: PLATAFORMA INTEGRAL CISO")
    print("="*60)

    # Mapeo: Nombre de archivo -> Clave del Dispatcher en main.py
    sensor_map = {
        "sensor_procesos.py": "sensor_procesos",
        "sensor_red.py": "sensor_red",
        "sensor_sistema.py": "sensor_sistema",
        "sensor_vulnerabilidades.py": "sensor_vulnerabilidades",
        "sensor_network_discovery.py": "sensor_network_discovery"
    }

    # En modo compilado/monolito, usamos las claves del dispatcher
    print(f"🔎 Autodiscovery: Iniciando sensores modulares (Dispatcher Mode).\n", file=sys.stderr)

    all_data = []

    # 2. Execution & Aggregation
    for sensor_file, dispatch_key in sensor_map.items():
        print(f"🚀 Ejecutando módulo: {dispatch_key}...", file=sys.stderr)
        try:
            # LLAMADA AL DISPATCHER: GaltAI.exe [sensor_key] --local-only
            # Use specific dispatch key instead of filename
            command = [sys.executable, dispatch_key, "--local-only"]
            
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

    if not all_data: return

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

    # 5. AI Analysis
    print(f"\n🧠 Galt.ai Intelligence: Analizando con Gemini 2.0 Flash...")
    print(f"📊 Score: {security_score}/100 (Anterior: {previous_score})")

    SYSTEM_PROMPT = (
        "ROL: CISO Virtual Galt.ai.\n"
        f"CONTEXTO: {change_context}\n"
        f"SCORE: {security_score}/100\n"
        "\n"
        "INSTRUCCIONES:\n"
        "1. Compara la telemetría actual con la anterior.\n"
        "2. Si el score bajó, explica POR QUÉ (qué puerto/proceso apareció).\n"
        "3. Si detectas 'Sistemas Espejo' (mismo puerto abierto en local y red), alerta sobre Riesgo Sistémico.\n"
        "4. Proporciona comandos PowerShell exactos en la sección 'ACCIONES DE 5 MINUTOS'.\n"
    )
    
    report_text = "⚠️ **Análisis de IA no disponible.**\n\nNo se pudo conectar con Gemini AI. Revise su conexión a internet o su API Key.\nSe muestran los datos crudos a continuación."
    
    try:
        if not os.getenv("GOOGLE_API_KEY"):
             raise ValueError("Sin API Key configurada.")
             
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"{SYSTEM_PROMPT}\n\nPREVIO:\n{json.dumps(previous_findings)}\n\nACTUAL:\n{json.dumps(all_data)}"
        )
        report_text = response.text
    except Exception as e:
        print(f"⚠️ Error generando análisis AI: {e}", file=sys.stderr)
        report_text += f"\n\nError técnico: {e}"

    try:
        # 6. Save Data & Dashboard
        final_payload = {
            "client_id": "LOCAL_PIONEER_TEST",
            "timestamp_epoch": int(time.time()),
            "timestamp_human": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": security_score,
            "findings": all_data,
            "ai_analysis_markdown": report_text
        }
        
        json_path = save_json_data(final_payload)
        # --- 6. NOTIFICACIÓN FINAL ---
        # En lugar de abrir el navegador invasivamente, enviamos una notificación nativa
        try:
            from plyer import notification 
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "app.ico")
            
            notification.notify(
                title='Galt.ai Finalizado',
                message=f'Análisis de Seguridad completo.\nScore: {security_score}/100',
                app_icon=icon_path if os.path.exists(icon_path) else None,
                timeout=10
            )
            print("🔔 Notificación enviada.")
        except Exception as e:
            print(f"Error enviando notificación: {e}")

        # No abrimos el navegador automáticamente. El usuario lo hará desde el Tray.
        print(f"\n✅ REPORTE GENERADO: {json_path}")
        print("   Usa el icono del System Tray para verlo.")
        
        # 7. Update Vault
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time()), "score": security_score, "findings": all_data}, f)

            print("\n🚨 DRIFT DETECTADO: Abriendo dashboard automáticamente.")
        else:
            print("\n🤫 Modo Silencioso: Sin cambios críticos. Dashboard actualizado en background.")

        if should_open:
            print(f"   Abriendo reporte: {dashboard_path}")
            try:
                # Forzar ruta absoluta para el navegador
                webbrowser.open(f"file://{os.path.abspath(dashboard_path)}")
            except Exception as e:
                print(f"Error abriendo navegador: {e}")

    except Exception as e:
        print(f"❌ Error en flujo Reporte/Guardado: {e}")

if __name__ == "__main__":
    run_security_flow()