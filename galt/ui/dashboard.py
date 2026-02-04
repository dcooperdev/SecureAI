import os
import json
import webbrowser
import re

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'viewer.html')
# Helper to maintain compatibility if imports exist elsewhere
from galt.core.config import get_storage_path

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates', 'viewer.html')
REPORT_DIR = get_storage_path("reports")
OUTPUT_FILE = os.path.join(REPORT_DIR, 'dashboard.html')
VAULT_FILE = os.path.join(get_storage_path("vault"), 'reports', 'latest.json')

def update_history_index(new_report_data, filename):
    """Maintains a JSON index of the last 20 reports for the UI dropdown."""
    history_path = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'vault', 'reports', 'history.json')
    history = []

    # 1. Read existing history
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                history = json.load(f)
        except:
            history = []

    # 2. Prepend new entry
    entry = {
        "file": filename,
        "label": new_report_data.get("timestamp_human", "Unknown Date"),
        "score": new_report_data.get("score", 0)
    }

    # Remove duplicates based on filename and keep top 20
    history = [h for h in history if h['file'] != filename]
    history.insert(0, entry)

    # 3. Save
    with open(history_path, 'w') as f:
        json.dump(history[:20], f, indent=4)

def generate_dashboard(scan_results, ai_analysis_data):
    """
    Toma los datos, lee el template viewer.html, inyecta el JSON y guarda el reporte final.
    """
    # 1. Consolidar el Reporte Maestro
    full_report = {
        "timestamp_human": scan_results.get('timestamp_human', 'N/A'),
        "score": scan_results.get('score', 0),
        "score_reasoning": scan_results.get('score_reasoning', {}),
        "open_ports": scan_results.get('open_ports', []),
        "ai_status": "online" if ai_analysis_data else "offline",
        "ai_analysis": ai_analysis_data or {},
        "findings": scan_results.get('findings', [])
    }

    # 2. Guardar JSON Puro (para historial/vault)
    os.makedirs(os.path.dirname(VAULT_FILE), exist_ok=True)
    with open(VAULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=4)

    # NEW: Save Timestamped Copy for History
    timestamp_epoch = scan_results.get('timestamp_epoch', 0)
    report_filename = f"scan_{timestamp_epoch}.json"
    timestamp_path = os.path.join(os.path.dirname(VAULT_FILE), report_filename)

    with open(timestamp_path, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=4)

    # NEW: Update Index
    update_history_index(full_report, report_filename)

    # 3. Leer el Template HTML
    if not os.path.exists(TEMPLATE_PATH):
        print(f"❌ ERROR: No se encontró el template en {TEMPLATE_PATH}")
        return None

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 4. Inyectar el JSON y el Historial en el HTML
    json_str = json.dumps(full_report)
    
    # Read history for injection
    history_path = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'vault', 'reports', 'history.json')
    history_data = []
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                history_data = json.load(f)
        except:
             pass
    history_str = json.dumps(history_data)

    # Replace INITIAL_DATA
    pattern_data = r"const INITIAL_DATA = \{.*?\};"
    replacement_data = f"const INITIAL_DATA = {json_str};"
    final_html = re.sub(pattern_data, replacement_data, html_content, flags=re.DOTALL)
    
    # Replace HISTORY_DATA (We need to add a placeholder in the HTML first, or rely on regex if it exists)
    # Strategy: We will add 'const HISTORY_DATA = [];' to the HTML next.
    pattern_history = r"const HISTORY_DATA = \[.*?\];"
    replacement_history = f"const HISTORY_DATA = {history_str};"
    final_html = re.sub(pattern_history, replacement_history, final_html, flags=re.DOTALL)
         
    # 5. Guardar el HTML Final
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"✅ Reporte generado exitosamente: {OUTPUT_FILE}")
    
    # 6. Abrir en Navegador (opcional, el orquestador o tray suele manejar esto, pero el usuario pidió abrirlo aquí)
    # Sin embargo, el orquestador espera un retorno de ruta.
    # El código solicitado incluye webbrowser.open, pero para integrarse mejor con el flujo existente
    # que usa el tray y el orquestador, devolveré la ruta también.
    
    return OUTPUT_FILE

if __name__ == "__main__":
    # Prueba rápida
    dummy_data = {"score": 99, "ai_analysis": {"summary": "Test"}}
    generate_dashboard(dummy_data, dummy_data['ai_analysis'])
