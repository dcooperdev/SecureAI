import importlib.util
import os
import sys
import pathlib
from typing import Optional, Any, Dict
from galt.core.constants import CURRENT_CONTRACT_VERSION

def validate_plugin(plugin_module: Any) -> Optional[str]:
    """
    Validates the plugin module against the contract.
    Returns an error string if invalid, None if valid.
    """
    if not hasattr(plugin_module, "PLUGIN_META"):
        return "Missing PLUGIN_META"
    
    meta: Dict[str, Any] = getattr(plugin_module, "PLUGIN_META")
    required_keys = ["name", "version", "requires_admin", "contract_version"]
    for key in required_keys:
        if key not in meta:
            return f"PLUGIN_META missing key: {key}"

    # Strict Type Enforcement
    if not isinstance(meta["name"], str):
        return "Invalid type: 'name' must be str"
    if not isinstance(meta["version"], str):
        return "Invalid type: 'version' must be str"
    if not isinstance(meta["requires_admin"], bool):
        return "Invalid type: 'requires_admin' must be bool"

    # Strict Contract Version Check (must be EXACTLY 1.0)
    # Prompt says "Ensure loader rejects plugins with contract_version != 1.0"
    if meta["contract_version"] != CURRENT_CONTRACT_VERSION:
        return f"Contract Version mismatch: {meta['contract_version']} != {CURRENT_CONTRACT_VERSION}"
        
    if not hasattr(plugin_module, "run"):
        return "Plugin missing 'run' function"
        
    return None

def load_plugin(path: str) -> Optional[Any]:
    """
    Dynamically loads a plugin from a file path using safe namespace isolation.
    """
    p_path = pathlib.Path(path)
    # Helper to strip extension for name
    raw_name = p_path.stem
    
    # Namespace Isolation
    isolated_name = f"plugin_{raw_name}"
    
    try:
        spec = importlib.util.spec_from_file_location(isolated_name, str(p_path))
        if not spec or not spec.loader:
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[isolated_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        # Logging could go here
        return None
