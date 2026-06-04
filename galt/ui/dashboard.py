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
        "ai_status": scan_results.get('ai_status', "online" if ai_analysis_data else "offline"),
        "ai_analysis": ai_analysis_data or {},
        "findings": scan_results.get('findings', [])
    }

    # 2. Guardar JSON Puro (para historial/vault)
    os.makedirs(os.path.dirname(VAULT_FILE), exist_ok=True)
    with open(VAULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=4)

    # NEW: Save Timestamped Copy for History (JSON + JS for Serverless)
    timestamp_epoch = scan_results.get('timestamp_epoch', 0)
    report_filename_base = f"scan_{timestamp_epoch}"
    
    # 1. Save JSON (Archive)
    json_path = os.path.join(os.path.dirname(VAULT_FILE), report_filename_base + ".json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=4)

    # 2. Save JS (Serverless Access) - JSONP Pattern
    # This calls a global function 'receiveHistoryData' defined in viewer.html
    js_path = os.path.join(os.path.dirname(VAULT_FILE), report_filename_base + ".js")
    js_content_history = f"window.receiveHistoryData({json.dumps(full_report, indent=4)});"
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content_history)
        
    # [DEV MODE FIX] Mirror History JS
    dev_vault = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'vault', 'reports')
    if os.path.exists(dev_vault) and os.path.abspath(dev_vault) != os.path.abspath(os.path.dirname(js_path)):
        dev_js_path = os.path.join(dev_vault, report_filename_base + ".js")
        with open(dev_js_path, 'w', encoding='utf-8') as f:
            f.write(js_content_history)
        print(f"✅ [DEV] History Mirror Updated: {dev_js_path}")

    # NEW: Update Index using the JS file for the UI
    update_history_index(full_report, report_filename_base + ".js")

    # 3. Leer el Template HTML
    # 3. Create Serverless JS Loader (Data-as-Script)
    # This bypasses CORS by allowing the HTML to load this as a standard script.
    loader_path = os.path.join(os.path.dirname(VAULT_FILE), 'galt_loader.js')
    
    # Read history for the loader
    history_path = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'vault', 'reports', 'history.json')
    history_data = []
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                history_data = json.load(f)
        except:
            history_data = []

    # Write JS File
    js_content = f"""
window.GALT_LATEST_REPORT = {json.dumps(full_report, indent=4)};
window.GALT_HISTORY_INDEX = {json.dumps(history_data, indent=4)};
console.log("✅ Galt Data Loaded from JS!");
"""
    with open(loader_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"✅ Data Loader Updated: {loader_path}")

    # [DEV MODE FIX] Also write to local project source if it exists
    # This allows opening galt/ui/templates/viewer.html locally to work
    dev_vault = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'vault', 'reports')
    if os.path.exists(dev_vault) and os.path.abspath(dev_vault) != os.path.abspath(os.path.dirname(loader_path)):
        dev_loader_path = os.path.join(dev_vault, 'galt_loader.js')
        with open(dev_loader_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"✅ [DEV] Data Loader Mirror Updated: {dev_loader_path}")

    # Return the static template path (Viewer)
    # The viewer now loads the data dynamically from the JS file we just wrote.
    if not os.path.exists(TEMPLATE_PATH):
        print(f"❌ ERROR: No se encontró el template en {TEMPLATE_PATH}")
        return None
        
    return TEMPLATE_PATH

if __name__ == "__main__":
    # Prueba rápida
    dummy_data = {"score": 99, "ai_analysis": {"summary": "Test"}}
    generate_dashboard(dummy_data, dummy_data['ai_analysis'])
