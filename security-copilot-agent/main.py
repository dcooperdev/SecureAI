import argparse
import sys
import os
import time
import platform
from core import loader, sanitizer, uploader

def main():
    parser = argparse.ArgumentParser(description="Security Copilot Agent")
    parser.add_argument("--local-only", action="store_true", help="Print events to stdout instead of uploading")
    args = parser.parse_args()

    # Define plugins directory
    # Assuming main.py is in the root of security-copilot-agent/.. wait, the structure is
    # security-copilot-agent/main.py
    # security-copilot-agent/plugins/
    base_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(base_dir, "plugins")
    
    # Discovery
    # We look for .py files or .pyd (compiled) files
    # For now, let's just scan the directory
    plugin_files = [
        os.path.join(plugins_dir, f) 
        for f in os.listdir(plugins_dir) 
        if (f.endswith(".py") or f.endswith(".pyd")) and not f.startswith("__")
    ]

    for p_path in plugin_files:
        try:
            # 1. Load
            plugin = loader.load_plugin(p_path)
            if not plugin:
                continue

            # Validate
            err = loader.validate_plugin(plugin)
            if err:
                print(f"Skipping {p_path}: {err}", file=sys.stderr)
                continue
            
            # 2. Run
            # Helper to safely run
            try:
                result = plugin.run()
            except PermissionError:
                # Fallback as per requirements
                from security_copilot_agent.core.constants import Severity
                result = {
                    "severity": Severity.MED,
                    "message": "Insufficient Privileges",
                    "impact_hint": "Access denied during scan."
                }
            except Exception as e:
                print(f"Plugin {plugin.PLUGIN_META['name']} failed: {e}", file=sys.stderr)
                continue

            # 3. Sanitize
            # Recursively sanitize strings in the result dictionary?
            # Requirement says "replace ... in all output strings".
            # We'll treat the whole result as a string for JSON dumping, or walk the dict.
            # Easiest is to sanitize string values.
            # But uploader expects a dict.
            # Let's sanitize a serialized version or walk the dict.
            # The prompt says "Sanitize: Use regex to replace ... in all output strings".
            # Logic: sanitize(str(result))? No, that breaks the dict.
            # Better: deep walk.
            
            def deep_sanitize(obj):
                if isinstance(obj, str):
                    return sanitizer.sanitize(obj)
                elif isinstance(obj, dict):
                    return {k: deep_sanitize(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [deep_sanitize(i) for i in obj]
                else:
                    return obj
            
            sanitized_result = deep_sanitize(result)

            # 4. Event ID
            # "The uploader must generate a unique event_id"
            # We call uploader.generate_event_id before uploading
            # The prompt says: "The uploader must generate..."
            # So maybe uploader.upload_event handles it? 
            # Or we generate it and pass it to upload?
            # Prompt: "Event ID: The uploader must generate..."
            # Let's do it here or in uploader. 
            # If we do it in uploader.upload_event, we need to modify the data.
            # Let's generate it here for clarity.
            
            ts = str(int(time.time()))
            hid = platform.node()
            event_id = uploader.generate_event_id(plugin.PLUGIN_META["name"], ts, hid)
            
            final_payload = {
                "event_id": event_id,
                "timestamp": ts,
                "host_id": hid,
                "plugin": plugin.PLUGIN_META["name"],
                "result": sanitized_result
            }

            # 5. Upload/Print
            uploader.upload_event(final_payload, local_only=args.local_only)

        except Exception as e:
            print(f"Error processing {p_path}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
