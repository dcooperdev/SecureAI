import os
import sys
import logging
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import save_api_key, get_api_key, env_path

def test_config_reload():
    print(f"Testing config reload...")
    print(f"Env path: {env_path}")
    
    # 1. Clear existing key
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]
    
    # 2. Save a dummy key
    dummy_key = "TEST_KEY_12345"
    print(f"Saving key: {dummy_key}")
    save_api_key(dummy_key)
    
    # 3. Check os.environ immediately
    current_env = os.environ.get("GOOGLE_API_KEY")
    print(f"Current os.environ['GOOGLE_API_KEY']: {current_env}")
    
    if current_env != dummy_key:
        print("FAIL: os.environ not updated immediately!")
        return False
        
    # 4. Check file content
    with open(env_path, "r") as f:
        content = f.read()
    print(f"File content: {content.strip()}")
    
    if f"GOOGLE_API_KEY={dummy_key}" not in content:
        print("FAIL: File not written correctly!")
        return False

    # 5. Check via get_api_key()
    retrieved_key = get_api_key()
    print(f"Retrieved via get_api_key(): {retrieved_key}")
    
    if retrieved_key != dummy_key:
        print("FAIL: get_api_key() returned wrong value!")
        return False
        
    print("SUCCESS: Config reload works as expected.")
    return True

def setup_logging():
    logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    setup_logging()
    test_config_reload()
