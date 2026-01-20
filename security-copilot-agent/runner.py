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
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

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
        # Check if findings changed even if score is same (unlikely with this math, but possible)
        # For this requirement: "Si el Score Actual es IGUAL... terminar silenciosamente"
        print(f"\n⏸️  Postura estable ({security_score}/100). Sin cambios detectados.")
        return

    print(f"\n🧠 Galt.ai Intelligence: Analizando {len(all_data)} hallazgos con Gemini 2.5 Flash...")
    print(f"📊 Security Score Calculado: {security_score}/100 (Anterior: {previous_score})")

    # 4. Configuración del CISO Virtual (System Prompt)
    SYSTEM_PROMPT = f"""
    ROL: Eres Galt.ai, un CISO de Élite (Chief Information Security Officer) virtual.
    TONO: Pragmático, directo, enfocado en el riesgo de negocio. Profesioal y autoritario en seguridad.
    
    CONTEXTO DE CAMBIO: {change_context}
    SCORE ANTERIOR: {previous_score}
    SCORE ACTUAL: {security_score}
    
    OBJETIVO: Analizar la telemetría y explicar la evolución de la seguridad.
    
    ESTRUCTURA OBLIGATORIA DEL REPORTE (Markdown):
    
    1.  **Evolución de Seguridad**:
        - Explica INMEDIATAMENTE qué cambió. ¿Por qué subió o bajó el score?
        - Compara con el estado anterior.
        
    2.  **Security Score**: 
        - Genera una barra visual (Ej: ████████░░ {security_score}/100).
        - USA EL PUNTAJE PROVISTO ({security_score}/100).
        
    3.  **Advertencia Crítica** (Solo si hay Severidad HIGH):
        - Usa una alerta roja/negrita. Explica el riesgo inminente.
        
    4.  **Análisis de Impacto de Negocio**:
        - Financiero, Operativo, Reputacional.
        
    5.  **Plan de Acción Técnico**:
        - Pasos de remediación.
        
    6.  **Detalle de Hallazgos**:
        - Tabla o lista.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=f"{SYSTEM_PROMPT}\n\nTELEMETRÍA ACTUAL:\n{json.dumps(all_data)}"
        )
        
        report_text = response.text
        print("\n" + "—"*60 + "\n" + report_text + "\n" + "—"*60)
        
        path = save_report(report_text)
        print(f"\n✅ REPORTE GUARDADO: {path}")
        
        # --- UPDATE VAULT ---
        new_state = {
            "timestamp": str(int(datetime.now().timestamp())),
            "score": security_score,
            "findings": current_findings_summary
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
        else:
            print(f"❌ Error desconocido en IA: {e}")

if __name__ == "__main__":
    run_security_flow()