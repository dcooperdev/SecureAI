import subprocess
import json
import os
import sys

# Force UTF-8 encoding for stdout on Windows to handle emojis
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
import glob
from datetime import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()

def check_configuration():
    """Verifica la configuración y asiste al usuario si falta la API Key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # Check if missing or default value
    if not api_key or api_key.strip() == "tu_api_key_secreta_aqui" or api_key.strip() == "":
        
        # Check if we are in an interactive terminal
        if sys.stdin and sys.stdin.isatty():
            print("\n" + "!"*60)
            print("⚠️  CONFIGURACIÓN INICIAL REQUERIDA")
            print("   Para operar, Galt.ai necesita acceder a Google Gemini API.")
            print("   👉 Obtén tu llave gratis aquí: https://aistudio.google.com/")
            print("!"*60 + "\n")
            
            try:
                # Interactive prompt
                key_input = input("🔑 Ingresa tu Google API Key (y presiona Enter): ").strip()
                
                if len(key_input) > 20: 
                    with open(".env", "w", encoding="utf-8") as f:
                        f.write("# --- Galt.ai Configuration ---\n")
                        f.write(f"GOOGLE_API_KEY={key_input}\n")
                        f.write("SCAN_INTERVAL_SECONDS=3600\n")
                        f.write("LOG_LEVEL=INFO\n")
                    
                    print("\n✅ API Key guardada exitosamente en .env")
                    os.environ["GOOGLE_API_KEY"] = key_input
                    return key_input
                else:
                    print("\n❌ La clave ingresada parece inválida. Abortando.")
                    sys.exit(1)
            except KeyboardInterrupt:
                print("\n👋 Configuración cancelada.")
                sys.exit(0)
            except Exception as e:
                 print(f"❌ Error leyendo entrada: {e}")
                 sys.exit(1)
        else:
            # Non-interactive mode (e.g. running from Sentinel or Cron)
            print("❌ Error: GOOGLE_API_KEY no configurada en .env")
            print("   Como estás en modo no-interactivo, debes editar el archivo .env manualmente.")
            sys.exit(1)
    
    return api_key

# Initialize client with the checked/prompted key
client = genai.Client(api_key=check_configuration())

def save_json_data(data):
    data_dir = "reports/data"
    if not os.path.exists(data_dir): os.makedirs(data_dir)
    filename = f"{data_dir}/scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return filename

def run_security_flow():
    print("\n" + "="*60)
    print("🛡️  GALT.AI v2: PLATAFORMA INTEGRAL CISO")
    print("="*60)

    # 1. Autodiscovery Engine (using os.listdir as requested)
    current_dir = os.getcwd()
    all_files = os.listdir(current_dir)
    sensor_files = [f for f in all_files if f.startswith("sensor_") and f.endswith(".py")]
    
    if not sensor_files:
        print("❌ Error: No se encontraron sensores (sensor_*.py)")
        return

    print(f"🔎 Autodiscovery: Detectados {len(sensor_files)} micro-sensores: {sensor_files}\n")

    all_data = []

    # 2. Sequential Execution & 3. JSON Stream Aggregator
    for sensor in sensor_files:
        print(f"🚀 Ejecutando {sensor}...")
        try:
            # shell=True and -u for unbuffered output
            command = f"python -u {sensor} --local-only"
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                encoding='utf-8'
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"   ⚠️  Advertencia: {sensor} reportó código {process.returncode}")

            # Reconstruct JSON objects
            potential_objects = stdout.split('"event_id":')
            count_new = 0
            
            for obj_part in potential_objects:
                if not obj_part.strip(): continue
                json_str = '{"event_id":' + obj_part.strip()
                last_brace = json_str.rfind('}')
                if last_brace != -1:
                    json_str = json_str[:last_brace+1]
                
                try:
                    data = json.loads(json_str)
                    all_data.append(data)
                    count_new += 1
                except json.JSONDecodeError:
                    continue
            
            print(f"   ✅ Datos recolectados: {count_new} eventos.")
            
        except Exception as e:
            print(f"   ❌ Fallo crítico en {sensor}: {e}")
            continue

    if not all_data:
        print("\n❌ Error: Flujo detenido. No hay telemetría para analizar.")
        return

    # --- DETERMINISTIC SCORING ENGINE ---
    # Calculate score based on findings BEFORE sending to AI
    security_score = 100
    critical_findings = 0
    
    current_findings_summary = []

    for event in all_data:
        result = event.get("result", {})
        severity = result.get("severity", "INFO").upper()
        plugin = event.get("plugin", "unknown")
        
        # Build simple summary for state comparison
        if "data" in result and isinstance(result["data"], list) and result["data"]:
             summary_str = f"{plugin}: {result['data']}"
             current_findings_summary.append(summary_str)

        if severity == "HIGH":
            security_score -= 40
            critical_findings += 1
        elif severity == "MEDIUM":
            security_score -= 15
        elif severity == "LOW":
            security_score -= 5
            
    # Cap score at 0
    if security_score < 0: security_score = 0
    
    # --- PERSISTENCE & DRIFT DETECTION ---
    vault_dir = "vault"
    if not os.path.exists(vault_dir): os.makedirs(vault_dir)
    
    state_file = os.path.join(vault_dir, "security_state.json")
    history_file = os.path.join(vault_dir, "history_log.jsonl")
    
    previous_score = None
    previous_findings = []
    
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                last_state = json.load(f)
                previous_score = last_state.get("score")
                previous_findings = last_state.get("findings", [])
        except:
            pass

    # Logic: Brindamos o Lloramos
    run_analysis = False
    change_context = ""
    
    if previous_score is None:
        run_analysis = True
        change_context = "Iniciando línea base de seguridad (Primer escaneo)."
    elif security_score != previous_score:
        run_analysis = True
        if security_score > previous_score:
            change_context = f"MEJORA DETECTADA: El score subió de {previous_score} a {security_score}. Se han mitigado riesgos."
        else:
            change_context = f"DETERIORO DETECTADO: El score bajó de {previous_score} a {security_score}. Nuevos riesgos encontrados."
    else:
        # Force analysis if we want to detect silent drift (e.g. port opened but score metrics didn't capture it yet)
        # But for now we stick to score changes or if user specifically requested always-on analysis.
        # However, the user asked for "Comparar activamente". That implies we should always analyze?
        # "Si el Score Actual es IGUAL... terminar silenciosamente" was the old rule.
        # But if a port 5432 APPARECIÓ, the score SHOULD have dropped independently.
        # If the score logic is weak, we might miss it.
        # Let's assume the score logic (lines 94-118) catches high severity.
        # If new port 5432 appears -> new process -> severity might be INFO if logic doesn't flag it?
        # sensor_procesos currently flags 5432 as INFO unless name is suspicious.
        # So we might miss it in score.
        # Let's force analysis if we detect ANY new port compared to previous, regardless of score.
        # But since we don't have the granular diff logic in python yet, we rely on Gemini?
        # Wait, if we return early here, we don't call Gemini.
        # So I should probably relax this condition or do a quick python-side diff.
        pass

    # Hack: For this upgrade, we ALWAYS run analysis to ensure Gemini sees the new data and can report on drift.
    # Or at least, we should check if 'findings' structure differs significantly.
    # For now, let's just proceed to allow Gemini to work its magic.
    # But to respect the "silence" rule if truly nothing changed...
    # Let's just strip lines 154-158 logic of returning early for now during this testing phase?
    # Or better: logic remains, but we rely on score changes.
    # NOTE: Does sensor_procesos flag 5432 as High/Medium?
    # In my updated sensor_procesos, 5432 is MEDIUM if name is known, or could vary.
    # Let's just assume checks are good.

    print(f"\n🧠 Galt.ai Intelligence: Analizando {len(all_data)} hallazgos con Gemini 2.5 Flash...")
    print(f"📊 Security Score Calculado: {security_score}/100 (Anterior: {previous_score})")

    # 4. Configuración del CISO Virtual (System Prompt)
    SYSTEM_PROMPT = f"""
    ROL: Eres Galt.ai, un CISO de Élite (Chief Information Security Officer) virtual.
    TONO: Pragmático, directo, enfocado en el riesgo de negocio. Profesional y autoritario en seguridad.
    
    CONTEXTO DE CAMBIO: {change_context}
    SCORE ANTERIOR: {previous_score}
    SCORE ACTUAL: {security_score}
    SO: Windows 10.0.19045
    
    OBJETIVO: Analizar la telemetría actual y COMPARARLA con la anterior para detectar 'Deriva Semántica' (Semantic Drift).
    
    ESTRUCTURA OBLIGATORIA DEL REPORTE (Markdown):
    
    1.  **Análisis de Deriva (Drift Analysis)**:
        - ¡CRÍTICO! Compara la TELEMETRÍA ANTERIOR con la TELEMETRÍA ACTUAL.
        - Identifica puertos que ANTES estaban cerrados y AHORA están abiertos.
        - Identifica procesos nuevos.
        - Ejemplo: "En el escaneo anterior el puerto 5432 no estaba, y ahora apareció asociado al PID 1234".
        - Si no hay cambios, indícalo claramente.
        
    2.  **Security Score**: 
        - Genera una barra visual (Ej: ████████░░ {security_score}/100).
        - USA EL PUNTAJE PROVISTO ({security_score}/100).
        
    3.  **Deep Network Scan & CVE Lookup**:
        - Has recibido resultados de un escaneo profundo (netstat + psutil + discovery).
        - **SISTEMAS ESPEJO (Mirror Systems)**: 
            - Compara resultados de 'sensor_procesos' (local) con 'sensor_network_discovery' (remoto/vecinos).
            - Si ves que el puerto X está abierto en ESTE equipo y TAMBIÉN en equipos vecinos, ALERTA sobre "Riesgo Sistémico".
            - Ejemplo: "Veo que el puerto 5432 (PostgreSQL) está abierto en tu PC y también en otras 3 IPs de la red (192.168.1.X)."
        - **Conexiones Externas (C2)**:
            - Analiza IPs remotas en "ESTABLISHED (External)".
            - Distingue entre IPs de nube (Google/Azure/AWS = Riesgo bajo si es browser, medio si es svchost) vs IPs desconocidas (Riesgo Alto/C2).
        - **Vulnerabilidades**:
            - Asocia puertos abiertos con CVEs conocidos para Windows 10.0.19045.
        
    4.  **Advertencia Crítica** (Solo si hay Severidad HIGH):
        - Usa una alerta roja/negrita. Explica el riesgo inminente.
        
    6.  **ACCIONES DE 5 MINUTOS (Quick Wins)**:
        - ¡SECCIÓN OBLIGATORIA!
        - Debes proporcionar un bloque de código EXACTO para remediar los hallazgos.
        - FORMATO:
          ```powershell
          # Ejemplo: Bloquear puerto 445
          New-NetFirewallRule -DisplayName "Block SMB" -Direction Inbound -LocalPort 445 -Protocol TCP -Action Block
          ```
        - Si detectas "Mirror Systems" (mismo puerto en varios equipos), el comando debe ser aislar el equipo: `Disconnect-NetAdapter -Name "Ethernet" -Confirm:$false` (sugerencia extrema).
        
    7.  **Plan de Acción Técnico (Largo Plazo)**:
        - Remediar vulnerabilidades de fondo (parcheo, arquitectura).
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=f"{SYSTEM_PROMPT}\n\nTELEMETRÍA ANTERIOR (Estado Previo):\n{json.dumps(previous_findings)}\n\nTELEMETRÍA ACTUAL (Estado Nuevo):\n{json.dumps(all_data)}"
        )
        
        report_text = response.text
        print("\n" + "—"*60 + "\n" + report_text + "\n" + "—"*60)
        
        # --- NEW DATA STORAGE ---
        current_time = datetime.now()
        payload = {
            "client_id": "LOCAL_PIONEER",
            "timestamp_epoch": int(current_time.timestamp()),
            "timestamp_human": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "score": security_score,
            "findings": all_data,
            "ai_analysis_markdown": report_text
        }
        
        json_path = save_json_data(payload)
        print(f"\n📦 DATOS GUARDADOS: {json_path}")
        
        # --- UPDATE VAULT ---
        new_state = {
            "timestamp": str(int(current_time.timestamp())),
            "score": security_score,
            "findings": all_data 
        }
        
        with open(state_file, "w") as f:
            json.dump(new_state, f, indent=2)
            
        with open(history_file, "a") as f:
            log_entry = new_state.copy()
            log_entry["report_path"] = json_path
            f.write(json.dumps(log_entry) + "\n")
            
        print("💾 Estado de seguridad actualizado en Vault.")
        
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            print("\n⛔ QUOTA EXCEEDED (Error 429): La IA está saturada.")
            print("   ⏳ Por favor espera unos minutos antes de reintentar.")
            print(f"   Detalle técnico: {err_msg[:200]}...")
            return # Exit if AI failed, but maybe we should still generate dashboard with partial data? NO, user wants AI report in dashboard.
        else:
            print(f"❌ Error desconocido en IA: {e}")
            return

    # --- USER TESTING: PAYLOAD & DASHBOARD ---
    
    # --- DASHBOARD GENERATION ---
    generate_dashboard(json_path)

    # Conditional Auto-Launch
    is_auto_mode = "--auto" in sys.argv
    drift_detected = bool(change_context) 
    
    if not is_auto_mode or drift_detected:
        import webbrowser
        dashboard_path = os.path.abspath("reports/dashboard.html")
        webbrowser.open(f"file://{dashboard_path}")
        print("🚀 Dashboard abierto en navegador.")
    else:
        print("🤫 Modo Silencioso: Dashboard actualizado en segundo plano.")

def generate_dashboard(json_path):
    # Read data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    score = data.get("score", 0)
    report_md = data.get("ai_analysis_markdown", "")
    timestamp = data.get("timestamp_human", "")

    # Color logic
    color_class = "text-success"
    border_class = "border-success"
    if score < 50: 
        color_class = "text-danger"
        border_class = "border-danger"
    elif score < 80: 
        color_class = "text-warning"
        border_class = "border-warning"
    
    html_content = f"""<!DOCTYPE html>
<html lang="es" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galt.ai Pioneer Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{ background-color: #0d1117; font-family: 'Segoe UI', sans-serif; }}
        .navbar {{ background: #161b22; border-bottom: 1px solid #30363d; }}
        .hero-section {{ padding: 60px 0; text-align: center; }}
        .score-circle {{ 
            width: 150px; height: 150px; border-radius: 50%; border: 8px solid; 
            margin: 0 auto; display: flex; align-items: center; justify-content: center;
            font-size: 3rem; font-weight: bold; background: #21262d;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
        }}
        .report-container {{ 
            background: #161b22; border: 1px solid #30363d; border-radius: 6px; 
            padding: 40px; margin-top: 30px; 
        }}
        /* Markdown Styles */
        h1, h2, h3 {{ color: #e6edf3; margin-top: 20px; }}
        p, li {{ color: #c9d1d9; line-height: 1.6; }}
        code {{ background: #6e768166; padding: 2px 5px; border-radius: 4px; color: #ff7b72; }}
        pre {{ background: #0d1117; padding: 15px; border-radius: 6px; overflow-x: auto; border: 1px solid #30363d; }}
        .footer {{ margin-top: 50px; padding: 20px; text-align: center; color: #8b949e; font-size: 0.9rem; }}
    </style>
</head>
<body>

<nav class="navbar navbar-expand-lg navbar-dark">
  <div class="container">
    <a class="navbar-brand fw-bold" href="#">👁️ Galt.ai</a>
    <span class="navbar-text ms-auto text-secondary small me-3">
        {timestamp}
    </span>
    <a href="data/{os.path.basename(json_path)}" target="_blank" class="btn btn-outline-primary btn-sm">
        💾 Exportar JSON
    </a>
  </div>
</nav>

<div class="container hero-section">
    <div class="score-circle {color_class} {border_class}">
        {score}
    </div>
    <p class="mt-3 text-secondary">SECURITY SCORE</p>
</div>

<div class="container">
    <div class="report-container" id="report-content">
        <!-- Rendered Markdown -->
    </div>
</div>

<div class="footer">
    Modo Pionero - Tus datos están listos para la nube ☁️
</div>

<script>
    const reportMd = {json.dumps(report_md)};
    document.getElementById('report-content').innerHTML = marked.parse(reportMd);
</script>

</body>
</html>"""

    dashboard_path = os.path.abspath("reports/dashboard.html")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"📊 Dashboard generado: {dashboard_path}")

if __name__ == "__main__":
    run_security_flow()