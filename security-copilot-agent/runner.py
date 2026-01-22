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

load_dotenv()

# --- CONFIGURACIÓN Y UTILIDADES ---

def check_configuration():
    """Verifica la configuración y asiste al usuario si falta la API Key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key.strip() == "tu_api_key_secreta_aqui" or api_key.strip() == "":
        if sys.stdin and sys.stdin.isatty():
            print("\n" + "!"*60)
            print("⚠️  CONFIGURACIÓN INICIAL REQUERIDA")
            print("   Para operar, Galt.ai necesita acceder a Google Gemini API.")
            print("   👉 Obtén tu llave gratis aquí: https://aistudio.google.com/")
            print("!"*60 + "\n")
            try:
                key_input = input("🔑 Ingresa tu Google API Key (y presiona Enter): ").strip()
                if len(key_input) > 20: 
                    with open(".env", "w", encoding="utf-8") as f:
                        f.write("# --- Galt.ai Configuration ---\n")
                        f.write(f"GOOGLE_API_KEY={key_input}\n")
                        f.write("SCAN_INTERVAL_SECONDS=3600\n")
                        f.write("LOG_LEVEL=INFO\n")
                    os.environ["GOOGLE_API_KEY"] = key_input
                    return key_input
                else:
                    sys.exit(1)
            except Exception:
                 sys.exit(1)
        else:
            print("❌ Error: GOOGLE_API_KEY no configurada en .env")
            sys.exit(1)
    return api_key

client = genai.Client(api_key=check_configuration())

def save_json_data(data):
    """Guarda la telemetría estructurada en JSON para futura migración a Firebase."""
    if not os.path.exists("reports/data"): os.makedirs("reports/data")
    filename = f"reports/data/scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

def generate_dashboard_html(score, report_md, json_path, client_id="LOCAL_PIONEER"):
    """Genera un Dashboard HTML moderno y lo guarda localmente."""
    
    # Determinar color según score
    score_color = "#dc3545" # Rojo
    if score >= 80: score_color = "#198754" # Verde
    elif score >= 50: score_color = "#ffc107" # Amarillo

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Galt.ai Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .score-circle {{
                width: 150px; height: 150px; border-radius: 50%;
                background: conic-gradient({score_color} {score}%, #2c2c2c 0);
                display: flex; align-items: center; justify-content: center;
                margin: 0 auto; box-shadow: 0 0 20px {score_color}40;
            }}
            .score-inner {{
                width: 130px; height: 130px; border-radius: 50%;
                background-color: #121212; display: flex; flex-direction: column;
                align-items: center; justify-content: center;
            }}
            .score-number {{ font-size: 3rem; font-weight: bold; color: {score_color}; line-height: 1; }}
            .score-label {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }}
            .card {{ background-color: #1e1e1e; border: 1px solid #333; }}
            pre {{ background: #111; padding: 15px; border-radius: 5px; border: 1px solid #333; }}
            code {{ color: #d63384; }}
            .markdown-body h1, .markdown-body h2 {{ border-bottom: 1px solid #333; padding-bottom: 0.3em; margin-top: 1.5em; color: #fff; }}
            .markdown-body h3 {{ color: #adb5bd; margin-top: 1.2em; }}
            .markdown-body ul {{ padding-left: 20px; }}
            .markdown-body strong {{ color: #fff; }}
            .alert-critical {{ border-left: 5px solid #dc3545; background-color: #2c0b0e; padding: 15px; }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark border-bottom border-secondary mb-4">
            <div class="container">
                <a class="navbar-brand fw-bold" href="#">🛡️ Galt.ai <span class="badge bg-primary ms-2" style="font-size:0.6em">BETA</span></a>
                <span class="navbar-text text-light small">{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
            </div>
        </nav>

        <div class="container">
            <div class="row mb-5 text-center">
                <div class="col-md-12">
                    <div class="score-circle mb-3">
                        <div class="score-inner">
                            <span class="score-number">{score}</span>
                            <span class="score-label">SCORE</span>
                        </div>
                    </div>
                    <h2 class="fw-light">Postura de Seguridad</h2>
                    <p class="text-muted">ID Cliente: {client_id}</p>
                </div>
            </div>

            <div class="row">
                <div class="col-lg-8 mx-auto">
                    <div class="card shadow-sm mb-4">
                        <div class="card-header bg-transparent border-bottom border-secondary py-3">
                            <h5 class="mb-0">📋 Análisis de Inteligencia Artificial</h5>
                        </div>
                        <div class="card-body">
                            <div id="report-content" class="markdown-body">
                                </div>
                        </div>
                    </div>

                    <div class="text-center mb-5">
                         <a href="../{json_path}" target="_blank" class="btn btn-outline-secondary btn-sm">
                            📄 Ver Datos Crudos (JSON)
                         </a>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script>
            const markdownText = `{report_md.replace('`', '\`').replace('$', '\$')}`; 
            document.getElementById('report-content').innerHTML = marked.parse(markdownText);
        </script>
    </body>
    </html>
    """
    
    path = "reports/dashboard.html"
    if not os.path.exists("reports"): os.makedirs("reports")
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

    # 1. Autodiscovery
    current_dir = os.getcwd()
    sensor_files = [f for f in os.listdir(current_dir) if f.startswith("sensor_") and f.endswith(".py")]
    
    if not sensor_files:
        print("❌ Error: No se encontraron sensores.")
        return

    print(f"🔎 Autodiscovery: Detectados {len(sensor_files)} micro-sensores.\n")

    all_data = []

    # 2. Execution & Aggregation
    for sensor in sensor_files:
        print(f"🚀 Ejecutando {sensor}...")
        try:
            command = f'"{sys.executable}" -u {sensor} --local-only'
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, encoding='utf-8')
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
            print(f"   ✅ Datos recolectados: {count_new} eventos.")
        except Exception as e:
            print(f"   ❌ Fallo en {sensor}: {e}")
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
    vault_dir = "vault"
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

    SYSTEM_PROMPT = f"""
    ROL: CISO Virtual Galt.ai.
    CONTEXTO: {change_context}
    SCORE: {security_score}/100
    
    INSTRUCCIONES:
    1. Compara la telemetría actual con la anterior.
    2. Si el score bajó, explica POR QUÉ (qué puerto/proceso apareció).
    3. Si detectas 'Sistemas Espejo' (mismo puerto abierto en local y red), alerta sobre Riesgo Sistémico.
    4. Proporciona comandos PowerShell exactos en la sección 'ACCIONES DE 5 MINUTOS'.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"{SYSTEM_PROMPT}\n\nPREVIO:\n{json.dumps(previous_findings)}\n\nACTUAL:\n{json.dumps(all_data)}"
        )
        report_text = response.text
        
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
        dashboard_path = generate_dashboard_html(security_score, report_text, json_path)
        
        print(f"\n✅ REPORTE JSON: {json_path}")
        print(f"✅ DASHBOARD HTML: {dashboard_path}")
        
        # 7. Update Vault
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time()), "score": security_score, "findings": all_data}, f)

        # 8. UX Logic (Silent Sentinel vs Pop-up)
        should_open = False
        
        if not args.auto:
            should_open = True # Manual run -> Open always
        elif drift_detected:
            should_open = True # Drift detected -> Open alert
            print("\n🚨 DRIFT DETECTADO: Abriendo dashboard automáticamente.")
        else:
            print("\n🤫 Modo Silencioso: Sin cambios críticos. Dashboard actualizado en background.")

        if should_open:
            print("🌐 Abriendo Dashboard en navegador...")
            webbrowser.open(f"file://{dashboard_path}")

    except Exception as e:
        print(f"❌ Error en flujo AI/Reporte: {e}")

if __name__ == "__main__":
    run_security_flow()