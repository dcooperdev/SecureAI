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
