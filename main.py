import sys
import multiprocessing
import logging
import json
import os
# Import modules explicitly for PyInstaller analysis
import platform

def get_storage_path(subdir=""):
    """
    Retorna una ruta absoluta y escribible para datos.
    Windows: C:\ProgramData\GaltAI\{subdir}
    Mac/Linux: /Users/{user}/.galt/{subdir}
    """
    system = platform.system()
    if system == "Windows":
        base = os.getenv('PROGRAMDATA', os.getenv('APPDATA'))
        root_dir = os.path.join(base, "GaltAI")
    else:
        root_dir = os.path.join(os.path.expanduser("~"), ".galt")
    
    target_dir = os.path.join(root_dir, subdir)
    
    # Asegurar que el directorio exista
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creando directorio {target_dir}: {e}")
    
    return target_dir
import sentinel
import runner
import sensor_procesos
import sensor_red
import sensor_sistema
import sensor_vulnerabilidades
import sensor_network_discovery

# --- IO SANITATION: SILENT MODE ---
# Configurar logging para que vaya a STDERR. 
# STDOUT debe quedar LIBRE exclusivamente para payloads JSON.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

def dispatch():
    # Vital fix for Windows infinite loop with PyInstaller
    multiprocessing.freeze_support()

    if len(sys.argv) == 1:
        # Default behavior: Sentinel Mode
        sentinel.main()
        return

    mode = sys.argv[1]

    # CLEANUP ARGUMENTS for underlying modules
    # sys.argv is currently ['main.py', 'sensor_procesos', '--local-only']
    # We remove 'main.py' so sys.argv becomes ['sensor_procesos', '--local-only']
    # Argparse inside sensors will treat 'sensor_procesos' as the script name (argv[0]) and parse the rest.
    sys.argv.pop(0)

    if mode == "sentinel":
        sentinel.main()
    elif mode == "runner":
        runner.run_security_flow()
    
    # --- SENSOR DISPATCH ---
    elif mode == "sensor_procesos": sensor_procesos.main()
    elif mode == "sensor_red": sensor_red.main()
    elif mode == "sensor_sistema": sensor_sistema.main()
    elif mode == "sensor_vulnerabilidades": sensor_vulnerabilidades.main()
    elif mode == "sensor_network_discovery": sensor_network_discovery.main()
    
    else:
        # Fallback
        logging.warning(f"Modo desconocido '{mode}'. Iniciando Sentinel.")
        sentinel.main()

if __name__ == "__main__":
    dispatch()
