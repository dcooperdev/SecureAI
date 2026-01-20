import argparse
import sys
import os
import time
import platform
import pathlib
from typing import Any, Dict
from core import loader, sanitizer, uploader

def main() -> None:
    parser = argparse.ArgumentParser(description="Security Copilot Agent (Hardened)")
    parser.add_argument("--local-only", action="store_true", help="Print events to stdout instead of uploading")
    args = parser.parse_args()

    # 1. Pipeline Setup (Discovery)
    base_dir = pathlib.Path(__file__).parent.absolute()
    plugins_dir = base_dir / "plugins"
    
    # Discovery of plugin files
    # We look for .py and .pyd/so
    plugin_files = []
    if plugins_dir.exists():
        for f in plugins_dir.iterdir():
            if f.suffix in ['.py', '.pyd', '.so'] and not f.name.startswith("__"):
                plugin_files.append(f)

    # 2. Execution Loop
    for p_path in plugin_files:
        try:
            # Step A: Safe Load
             # Convert path object to str for our loader
            plugin_module = loader.load_plugin(str(p_path))
            if not plugin_module:
                continue

            # Step B: Contract Validation
            err = loader.validate_plugin(plugin_module)
            if err:
                print(f"[WARN] Skipping {p_path.name}: {err}", file=sys.stderr)
                continue
            
            # Step C: Execution Sandbox
            try:
                # Run the plugin
                raw_result = plugin_module.run()
            except Exception as e:
                # Catch-all for plugin crashes to prevent orchestrator death
                print(f"[ERROR] Plugin {plugin_module.PLUGIN_META['name']} crashed: {e}", file=sys.stderr)
                continue

            # Step D: Consolidation (Deep Sanitization)
            sanitized_result = deep_sanitize(raw_result)
            
            # Step E: Event Identification
            ts = str(int(time.time()))
            hid = platform.node()
             # Use safe host name redactor? NO, we generate ID based on REAL host, 
             # but we might redact the payload later.
             # The ID should be stable.
            event_id = uploader.generate_event_id(plugin_module.PLUGIN_META["name"], ts, hid)
            
            final_payload = {
                "event_id": event_id,
                "timestamp": ts,
                "host_id": hid, # Potentially sensitive, but usually required for correlation. 
                                # Sanitizer might redact it in the BODY, but here it's metadata.
                                # Master prompt: "Consolidation: Sanitize findings..."
                "plugin": plugin_module.PLUGIN_META["name"],
                "result": sanitized_result
            }
            
            # Sanitize metadata if strictly required, but usually IDs are kept. 
            # If we sanitize host_id here, it might break correlation. 
            # We'll allow host_id in metadata but sanitized in 'result'.

            # Step F: Delivery
            uploader.upload_event(final_payload, local_only=args.local_only)

        except Exception as e:
            print(f"[FATAL] Orchestrator error on {p_path.name}: {e}", file=sys.stderr)

def deep_sanitize(obj: Any) -> Any:
    """
    Recursively applies sanitization to strings in dictionaries and lists.
    """
    if isinstance(obj, str):
        return sanitizer.sanitize(obj)
    elif isinstance(obj, dict):
        return {k: deep_sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_sanitize(i) for i in obj]
    else:
        return obj

if __name__ == "__main__":
    main()
