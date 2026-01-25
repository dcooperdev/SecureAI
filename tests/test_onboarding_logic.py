import sys
import os
import logging
sys.path.append(os.getcwd())

# Mock logging to avoid clutter
logging.basicConfig(level=logging.CRITICAL)

from onboarding import validate_key

def test_validation():
    print("Testing validate_key...")
    
    # 1. Test None/Empty
    if validate_key(None) is not False: 
        print("FAIL: None should be False")
    if validate_key("") is not False: 
        print("FAIL: Empty string should be False")
        
    # 2. Test Short Key
    if validate_key("short") is not False: 
        print("FAIL: Short key should be False")
        
    # 3. Test Invalid Format Key (but long enough)
    # This effectively tests the Google API call failure handling
    bad_key = "AIzaSyAd2lhgVDc9CmQX7gXBlTrUj9LAkysApRk_INVALID_SUFFIX"
    print(f"Testing bad key: {bad_key}")
    result = validate_key(bad_key)
    print(f"Result for bad key: {result}")
    
    if result is True:
        print("FAIL: Bad key should return False (unless Google API is down/mocked)")
    else:
        print("SUCCESS: Bad key returned False")

if __name__ == "__main__":
    test_validation()
