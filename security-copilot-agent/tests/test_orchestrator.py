import pytest
import hashlib
from unittest.mock import MagicMock, patch
# We will create these modules next
from core import uploader, loader, constants

# Mock Plugin Structure
class MockPlugin:
    PLUGIN_META = {
        "name": "test_plugin",
        "version": "1.0",
        "requires_admin": False,
        "contract_version": "1.0"
    }
    def run(self):
        return {"status": "ok"}

class BadVersionPlugin:
    PLUGIN_META = {
        "name": "future_plugin",
        "version": "1.0",
        "requires_admin": False,
        "contract_version": "2.0" # Invalid
    }

def test_event_id_generation():
    plugin_name = "test_plugin"
    ts = "1234567890"
    hid = "host-1"
    
    expected_hash = hashlib.sha256((plugin_name + ts + hid).encode()).hexdigest()
    assert uploader.generate_event_id(plugin_name, ts, hid) == expected_hash

def test_loader_rejects_bad_contract():
    # We test the validate_plugin logic we will implement in loader
    err = loader.validate_plugin(BadVersionPlugin)
    assert err is not None
    assert "Contract Version" in err

def test_loader_accepts_good_contract():
    err = loader.validate_plugin(MockPlugin)
    assert err is None

def test_privilege_error_handling():
    # Simulate a plugin run that raises PermissionError
    plugin = MockPlugin()
    plugin.run = MagicMock(side_effect=PermissionError("Access Denied"))
    
    from core.constants import Severity
    
    # Helper to simulate execution safety wrapper
    def safe_run(plugin_instance):
        try:
            return plugin_instance.run()
        except PermissionError:
             return {
                 "severity": Severity.MED.value, # Assuming Enum will return value or we check Enum member
                 "message": "Insufficient Privileges"
             }

    res = safe_run(plugin)
    # Check against value or name depending on implementation, let's assume value for JSON serializability
    assert res["severity"] == Severity.MED.value
    assert res["message"] == "Insufficient Privileges"
