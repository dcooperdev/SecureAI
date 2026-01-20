import pytest
import sys
import re
from unittest.mock import MagicMock, patch
from core import uploader, loader

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

def test_event_id_format():
    # Strict: verify SHA256 hex format (64 chars)
    plugin_name = "test"
    ts = "123"
    hid = "host"
    eid = uploader.generate_event_id(plugin_name, ts, hid)
    
    assert len(eid) == 64
    assert re.match(r'^[a-f0-9]{64}$', eid), "Event ID must be a valid SHA256 hex digest"

def test_idempotency_event_id():
    p_name = "net_scanner"
    ts = "1000"
    host = "host_x"
    id1 = uploader.generate_event_id(p_name, ts, host)
    id2 = uploader.generate_event_id(p_name, ts, host)
    assert id1 == id2
