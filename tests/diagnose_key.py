import os
import sys
import platform
# Add project root to path
sys.path.append(os.getcwd())

from config import get_storage_path, env_path, get_api_key

def diagnose():
    print("--- DIAGNOSTIC START ---")
    print(f"CWD: {os.getcwd()}")
    print(f"Computed env_path: {env_path}")
    
    if os.path.exists(env_path):
        print(f"File {env_path} EXISTS.")
        try:
            with open(env_path, 'r') as f:
                content = f.read().strip()
            print(f"Content: {content}")
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print(f"File {env_path} DOES NOT EXIST.")

    # Check local .env
    local_env = os.path.join(os.getcwd(), ".env")
    if os.path.exists(local_env):
        print(f"Local .env {local_env} EXISTS.")
        with open(local_env, 'r') as f:
            print(f"Local Content: {f.read().strip()}")
    else:
        print(f"Local .env {local_env} DOES NOT EXIST.")

    # Check Env Var
    key = get_api_key()
    print(f"get_api_key() returned: '{key}'")
    print(f"Type: {type(key)}")
    
    if key:
        print(f"Length: {len(key)}")
        if str(key).strip() == "":
            print("Key is whitespace/empty.")
        else:
            print("Key is NOT empty.")
    else:
        print("Key is None/False.")
        
    print("--- DIAGNOSTIC END ---")

if __name__ == "__main__":
    diagnose()
