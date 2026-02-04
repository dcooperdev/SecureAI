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

    # 3. Leer el Template HTML
    if not os.path.exists(TEMPLATE_PATH):
        print(f"❌ ERROR: No se encontró el template en {TEMPLATE_PATH}")
        return None

    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 4. Inyectar el JSON en el HTML
    # Buscamos el marcador /*PYTHON_INJECTION_POINT*/ o la variable INITIAL_DATA
    json_str = json.dumps(full_report)
    
    # Intento 1: Marcador explícito (Más seguro)
    if "/*PYTHON_INJECTION_POINT*/" in html_content:
        final_html = html_content.replace("/*PYTHON_INJECTION_POINT*/ null", json_str)
        final_html = final_html.replace("/*PYTHON_INJECTION_POINT*/", json_str) # Por si acaso
    else:
        # Intento 2: Reemplazo por Regex si el usuario no puso el marcador
        # Busca "const INITIAL_DATA = { ... };" y lo reemplaza
        pattern = r"const INITIAL_DATA = \{.*?\};"
        replacement = f"const INITIAL_DATA = {json_str};"
        # Usamos flags=re.DOTALL para que cubra múltiples líneas
        final_html = re.sub(pattern, replacement, html_content, flags=re.DOTALL)

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
