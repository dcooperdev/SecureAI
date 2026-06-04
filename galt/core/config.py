import os
import sys
import platform
import logging

# Default model — can be overridden by GALT_LLM_MODEL in the env file.
# gemini-3.5-flash: latest stable Flash generation — best JSON instruction-following
# and security domain knowledge. Free tier included.
_DEFAULT_LLM_MODEL = "gemini-3.5-flash"

def get_llm_model() -> str:
    """Returns the configured LLM model, falling back to the default."""
    return os.getenv("GALT_LLM_MODEL", _DEFAULT_LLM_MODEL)

def save_llm_model(model: str) -> None:
    """Persists the chosen LLM model to the env file alongside the API key."""
    env_path = os.path.join(get_storage_path(), ".env")
    # Read existing lines (keeps API key and other vars intact)
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = [l for l in f.readlines() if not l.startswith("GALT_LLM_MODEL=")]
    lines.append(f"GALT_LLM_MODEL={model}\n")
    try:
        with open(env_path, "w") as f:
            f.writelines(lines)
    except Exception as e:
        logging.error(f"Could not write model to .env: {e}")
    os.environ["GALT_LLM_MODEL"] = model

def setup_logging():
    """Configura logging silencioso hacia STDERR."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    # Silenciar logs ruidosos de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

def get_storage_path(subdir=""):
    """
    Retorna una ruta absoluta y escribible para datos.
    Windows: C:\\ProgramData\\GaltAI\\{subdir}
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

from dotenv import load_dotenv

# Cargar variables desde el ProgramData/Home
storage_path = get_storage_path()
env_path = os.path.join(storage_path, ".env")
load_dotenv(env_path)

# FALLBACK: Cargar desde el directorio actual (útil para desarrollo/test)
local_env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(local_env_path):
    load_dotenv(local_env_path)

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
