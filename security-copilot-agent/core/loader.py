import importlib.util
import os
import sys
from .constants import CURRENT_CONTRACT_VERSION, Severity

def validate_plugin(plugin_module):
    """
    Validates the plugin module against the contract.
    Returns an error string if invalid, None if valid.
    """
    if not hasattr(plugin_module, "PLUGIN_META"):
        return "Missing PLUGIN_META"
    
    meta = plugin_module.PLUGIN_META
    required_keys = ["name", "version", "requires_admin", "contract_version"]
    for key in required_keys:
        if key not in meta:
            return f"PLUGIN_META missing key: {key}"
            
    if meta["contract_version"] > CURRENT_CONTRACT_VERSION:
        return f"Contract Version {meta['contract_version']} is higher than supported {CURRENT_CONTRACT_VERSION}"
        
    if not hasattr(plugin_module, "run"):
        return "Plugin missing 'run' function"
        
    return None

def load_plugin(path: str):
    """
    Dynamically loads a plugin from a file path.
    """
    name = os.path.basename(path).replace(".py", "").replace(".pyd", "") # support compiled binary
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        return None
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
