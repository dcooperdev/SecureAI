import json
import os
import time
from config import get_storage_path

def get_status_file_path():
    return os.path.join(get_storage_path("reports"), "live_status.js")

def update_status(state, message="Sistema en espera", score="--"):
    """
    Escribe un archivo JS válido.
    state: 'IDLE' | 'SCANNING' | 'ERROR'
    """
    # Guardamos timestamp para evitar cache y para mostrar hora de update
    payload = {
        "state": state,
        "message": message,
        "score": str(score),
        "timestamp": time.strftime("%H:%M:%S")
    }
    
    # Escribimos una llamada a función global window.updateStatus(...)
    # Esto evita problemas de CORS que tendría un JSON puro.
    js_content = f"window.updateDashboardState({json.dumps(payload)});"
    
    try:
        report_dir = get_storage_path("reports")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
            
        with open(get_status_file_path(), "w", encoding="utf-8") as f:
            f.write(js_content)
    except Exception as e:
        print(f"Error escribiendo estado: {e}")

# Estado inicial al importar
# update_status("IDLE", "Sistema listo")
