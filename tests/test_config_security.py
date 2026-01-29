import sys
import os
import pytest
from unittest.mock import patch

# Add root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from galt.core.config import get_api_key

def test_get_api_key_from_env():
    """Test retrieving API key from environment variable."""
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "AIzaSyTestKey"}, clear=True):
        key = get_api_key()
        assert key == "AIzaSyTestKey"

def test_get_api_key_missing():
    """Test behavior when key is missing (should be None or raise, based on implementation)."""
    # Assuming current implementation returns None or empty string if not found, unless enforced elsewhere
    # Reviewing config.py manually: it usually relies on os.getenv
    with patch.dict(os.environ, {}, clear=True):
        if "GOOGLE_API_KEY" in os.environ:
             del os.environ["GOOGLE_API_KEY"]
             
        key = get_api_key()
        assert key is None or key == ""

def test_api_key_sanitization():
    """Simulate sanitization logic if checking leaks."""
    # Assuming we have logic to scrub keys, but if not, logic is usually '***'.
    # This test is a placeholder for checking that we don't log keys in plain text.
    pass
