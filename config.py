import os
import sys
import platform
import logging

def setup_logging():
    """Configura logging silencioso hacia STDERR."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )

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
            # Si falla logging aquí, es crítico, así que imprimimos a stderr directo
            print(f"Error creando directorio {target_dir}: {e}", file=sys.stderr)
    
    return target_dir
    return target_dir

from dotenv import load_dotenv

# Cargar variables desde el ProgramData/Home
storage_path = get_storage_path()
env_path = os.path.join(storage_path, ".env")
load_dotenv(env_path)

def get_api_key():
    return os.getenv("GOOGLE_API_KEY")

def save_api_key(key):
    # 1. Guardar en disco
    try:
        with open(env_path, "w") as f:
            f.write(f"GOOGLE_API_KEY={key}\n")
    except Exception as e:
        logging.error(f"No se pudo escribir .env: {e}")

    # 2. Actualizar entorno en memoria (CRÍTICO para que main.py lo vea ya mismo)
    os.environ["GOOGLE_API_KEY"] = key
    
    # 3. Recargar dotenv si es necesario
    load_dotenv(env_path, override=True)
