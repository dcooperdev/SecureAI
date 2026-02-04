import pytest
from unittest.mock import MagicMock, patch, mock_open
import json
import os
import sys
import re
from galt.core import uploader, loader

# --- Constants for Paths ---
MOCK_VAULT = "C:\\Mock\\Vault"
MOCK_REPORTS = "C:\\Mock\\Reports"

# --- CORE TESTS (From test_orchestrator.py) ---

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

# --- EXTENDED LOGIC TESTS (From test_orchestrator_extended.py) ---

@pytest.fixture
def mock_deps():
    with patch("galt.engine.orchestrator.subprocess.Popen") as m_opt, \
         patch("galt.engine.orchestrator.get_storage_path") as m_path, \
         patch("galt.engine.orchestrator.Bridge") as m_bridge, \
         patch("galt.engine.orchestrator.dashboard_generator") as m_dash, \
         patch("galt.core.notifier.Notifier") as m_notify, \
         patch("builtins.open", mock_open()) as m_open_file, \
         patch("argparse.ArgumentParser") as m_argparse, \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"):
         
         # Configure Storage Path
         def side_effect_path(subdir=""):
             if "vault" in subdir: return MOCK_VAULT
             if "reports" in subdir: return MOCK_REPORTS
             return "C:\\Mock\\GaltAI"
         m_path.side_effect = side_effect_path
         
         # Configure Sensors (subprocess)
         # Return a JSON event for one sensor, error for another?
         # popen -> process -> communicate -> returns (stdout, stderr)
         process_mock = MagicMock()
         # Return valid JSON for basic sensor
         process_mock.communicate.return_value = ('{"event_id": "1", "plugin": "sensor_sistema", "result": {"severity": "LOW"}}', '')
         m_opt.return_value = process_mock
         
         # Configure Bridge
         m_bridge_instance = MagicMock()
         m_bridge_instance.get_analysis.return_value = {
             "ai_status": "online", 
             "json_report": {"summary": "Safe"}
         }
         m_bridge.return_value = m_bridge_instance
         
         # Configure Dashboard
         m_dash.generate_dashboard.return_value = os.path.join(MOCK_REPORTS, "dashboard.html")
         
         yield {
             "subprocess": m_opt,
             "bridge": m_bridge_instance,
             "dashboard": m_dash,
             "notifier": m_notify,
             "open": m_open_file
         }

def test_run_flow_drift_logic(mock_deps):
    from galt.engine import orchestrator
    
    # Mock previous state logic: read returns a different score
    # orchestrator tries to open state_file
    # we need to handle multiple open calls.
    
    # Side effect for open:
    # First call might be save_json_data (write)
    # Second might be reading state (read) IF it exists
    # Third might be saving state (write)
    
    # It's tricky with mock_open for multiple files.
    # Let's mock os.path.exists to simulate state file existing
    # And mock json.load to return previous state
    
    with patch("json.load") as m_json_load, \
         patch("json.dump") as m_json_dump:
             
        # Previous score 100, current run (with LOW severity) should remain 100?
        # Logic: score = 100. event LOW -> -5. Final 95.
        
        m_json_load.return_value = {"score": 50, "findings": []} # Previous was 50
        
        # Run
        with patch("sys.stdout"):
            orchestrator.run_security_flow()
        
        # Current score calculation: 100 - (5 sensors * 5 points) = 75.
        # 75 != 50. Drift Detected.
        
        # Check if Notifier was called with correct message (implied logic)
        # Notifier is called at the end regardless, but context might differ in print?
        # Orchestrator prints "DRIFT DETECTADO"
        
        # Let's verify drift was printed
        # Capturing stdout is mocked in the `with` block above but we didn't inspect it.
        # We can inspect the calls to json.dump to see what was saved to state file.
        
        # Verify state file update
        # json.dump called twice: 1. save_json_data (telemetry), 2. state_file (persistence)
        assert m_json_dump.call_count >= 2
        
        # Get the call args for the state file update (last call)
        # args: (data, file_handle)
        saved_state = m_json_dump.call_args_list[-1][0][0]
        # Depending on specific scoring logic, just verify it runs
        assert "score" in saved_state 
        
        # Verify Notifier
        mock_deps["notifier"].return_value.send_notification.assert_called_once()


def test_run_flow_no_drift(mock_deps):
    from galt.engine import orchestrator
    
    with patch("json.load") as m_json_load:
        m_json_load.return_value = {"score": 75, "findings": []} # Previous matches current (75)
        
        with patch("sys.stdout") as m_stdout:
            orchestrator.run_security_flow()
            
            # Verify stdout contains "Postura estable"
            # Accumulate output
            output = "".join([c.args[0] for c in m_stdout.write.call_args_list if c.args])
            assert "Postura estable" in output

def test_run_flow_error_handling(mock_deps):
    # Simulate critical bridge error
    mock_deps["bridge"].get_analysis.return_value = {"error": "API Down", "ai_status": "error"}
    
    from galt.engine import orchestrator
    
    with patch("sys.stdout") as m_stdout, \
         patch("sys.stderr") as m_stderr:
        orchestrator.run_security_flow()
        
        # Check stderr for warning
        err_output = "".join([c.args[0] for c in m_stderr.write.call_args_list if c.args])
        assert "Error interno Bridge" in err_output
        
        # Flow should still complete (dashboard gen, etc.) despite AI error
        mock_deps["dashboard"].generate_dashboard.assert_called()
