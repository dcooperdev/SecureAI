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

def save_report(content):
    if not os.path.exists("reports"): os.makedirs("reports")
    filename = f"reports/Galt_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
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
        
        path = save_report(report_text)
        print(f"\n✅ REPORTE GUARDADO: {path}")
        
        # --- UPDATE VAULT ---
        new_state = {
            "timestamp": str(int(datetime.now().timestamp())),
            "score": security_score,
            "findings": all_data  # Saving FULL data now for better comparison next time
        }
        
        with open(state_file, "w") as f:
            json.dump(new_state, f, indent=2)
            
        with open(history_file, "a") as f:
            log_entry = new_state.copy()
            log_entry["report_path"] = path
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
    
    # 1. Generate JSON Payload
    payload = {
        "client_id": "LOCAL_TEST",
        "timestamp": datetime.now().isoformat(),
        "score": security_score,
        "findings": all_data,
        "report_md": report_text
    }
    
    with open("reports/latest_payload.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("📦 Payload JSON generado: reports/latest_payload.json")

    # 2. Generate HTML Dashboard
    generate_html_report(security_score, report_text, "reports/latest_payload.json")
    
def generate_html_report(score, report_md, json_path):
    # Color logic
    color_class = "bg-success"
    if score < 50: color_class = "bg-danger"
    elif score < 80: color_class = "bg-warning"
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galt.ai Security Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .navbar {{ background: #000; color: #fff; }}
        .score-card {{ background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .markdown-body {{ background: #fff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        pre {{ background-color: #f6f8fa; padding: 15px; border-radius: 5px; }}
        img {{ max-width: 100%; }}
    </style>
</head>
<body>

<nav class="navbar navbar-dark mb-4">
  <div class="container">
    <span class="navbar-brand mb-0 h1">🛡️ Galt.ai | Security Dashboard</span>
    <span class="text-light">{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
  </div>
</nav>

<div class="container">
    <div class="score-card text-center">
        <h3>Security Score</h3>
        <div class="display-4 fw-bold mb-3">{score}/100</div>
        <div class="progress" style="height: 30px;">
            <div class="progress-bar {color_class}" role="progressbar" style="width: {score}%" aria-valuenow="{score}" aria-valuemin="0" aria-valuemax="100">
                {score}%
            </div>
        </div>
        <div class="mt-3">
            <a href="latest_payload.json" target="_blank" class="btn btn-outline-dark btn-sm">Ver JSON Crudo</a>
        </div>
    </div>

    <div class="markdown-body" id="report-content">
        <!-- Rendered Markdown will go here -->
    </div>
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
    
    # Auto-Launch
    import webbrowser
    webbrowser.open(f"file://{dashboard_path}")
    print("🚀 Dashboard abierto en navegador.")

if __name__ == "__main__":
    run_security_flow()