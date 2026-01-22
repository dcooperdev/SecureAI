import pytest
from core import loader
from core.constants import CURRENT_CONTRACT_VERSION

# Mock Objects
class ValidPlugin:
    PLUGIN_META = {
        "name": "valid",
        "version": "1.0",
        "requires_admin": False,
        "contract_version": CURRENT_CONTRACT_VERSION
    }
    def run(self): pass

class MalformedTypesPlugin:
    PLUGIN_META = {
        "name": 123, # Wrong type
        "version": 1.0, # Wrong type (should be str)
        "requires_admin": "False", # Wrong type (should be bool)
        "contract_version": CURRENT_CONTRACT_VERSION
    }
    def run(self): pass

class OldPlugin:
    PLUGIN_META = {
        "name": "old",
        "version": "0.1",
        "requires_admin": False,
        "contract_version": "0.9"
    }
    def run(self): pass

class FuturePlugin:
    PLUGIN_META = {
        "name": "future",
        "version": "1.0",
        "requires_admin": False,
        "contract_version": "99.0"
    }
    def run(self): pass

def test_contract_enforcement_valid():
    err = loader.validate_plugin(ValidPlugin)
    assert err is None

def test_contract_enforcement_reject_types():
    # Strict Type Checking
    # We need to update loader.py to support this, 
    # but TDD says write test first.
    err = loader.validate_plugin(MalformedTypesPlugin)
    assert err is not None
    assert "Invalid type" in err or "must be" in err

def test_contract_enforcement_reject_old():
    err = loader.validate_plugin(OldPlugin)
    assert err is not None
    assert "Contract Version" in err

def test_contract_enforcement_reject_future():
    err = loader.validate_plugin(FuturePlugin)
    assert err is not None
    assert "Contract Version" in err

def test_missing_meta():
    class EmptyPlugin: pass
    err = loader.validate_plugin(EmptyPlugin)
    assert "Missing PLUGIN_META" in err
