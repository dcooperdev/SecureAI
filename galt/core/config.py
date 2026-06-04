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
    """Configures silent logging to STDERR."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )
    # Mute noisy logs from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

def get_storage_path(subdir=""):
    """
    Returns an absolute and writable data path.
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
    
    # Ensure the directory exists
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception as e:
            # If logging fails here it is critical, so we print directly to stderr
            print(f"Error creating directory {target_dir}: {e}", file=sys.stderr)
    
    return target_dir

from dotenv import load_dotenv

# Load variables from ProgramData/Home
storage_path = get_storage_path()
env_path = os.path.join(storage_path, ".env")
load_dotenv(env_path)

# FALLBACK: Load from current directory (useful for development/testing)
local_env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(local_env_path):
    load_dotenv(local_env_path)

def get_api_key():
    return os.getenv("GOOGLE_API_KEY")

def save_api_key(key):
    # 1. Save to disk
    try:
        with open(env_path, "w") as f:
            f.write(f"GOOGLE_API_KEY={key}\n")
    except Exception as e:
        logging.error(f"Could not write .env: {e}")

    # 2. Update memory environment (CRITICAL for main.py to see it immediately)
    os.environ["GOOGLE_API_KEY"] = key
    
    # 3. Reload dotenv if necessary
    load_dotenv(env_path, override=True)
