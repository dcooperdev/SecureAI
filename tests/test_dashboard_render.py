import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
import json

# Setup mocks for config
@pytest.fixture
def mock_config():
    with patch("galt.ui.dashboard.get_storage_path", return_value="C:\\ProgramData\\GaltAI") as mock:
        yield mock

@pytest.fixture
def mock_fs():
    with patch("builtins.open", mock_open(read_data="<html>/*PYTHON_INJECTION_POINT*/ null</html>")) as m_open, \
         patch("os.path.exists", return_value=True) as m_exists, \
         patch("os.makedirs") as m_mkdirs:
         yield m_open, m_exists, m_mkdirs

def test_generate_dashboard_success(mock_config, mock_fs):
    from galt.ui import dashboard
    
    scan_results = {
        "score": 80,
        "timestamp_human": "Now",
        "open_ports": [80]
    }
    ai_analysis = {"summary": "Safe"}
    
    # We need to patch shutil because it's imported inside the function sometimes? 
    # Or just used? Let's check source code if copied.
    # dashboard.py: 
    # VAULT_FILE = ...
    # It writes to OUTPUT_FILE and VAULT_FILE.
    
    path = dashboard.generate_dashboard(scan_results, ai_analysis)
    
    # Verify file operations
    m_open, _, _ = mock_fs
    
    # Should read template, write html, write json
    assert m_open.call_count >= 3 
    
    # Check if correct content was written
    handle = m_open()
    # Writes happen to handle.write(). 
    # We can check the arguments of the write calls.
    
    written_data = []
    for call in handle.write.call_args_list:
        written_data.append(call.args[0])
    
    full_text = "".join(written_data)
    
    # Check injection
    # If injection point was "/*PYTHON_INJECTION_POINT*/ null", it replaced explicitly.
    # The result should contain the JSON data.
    assert '"score": 80' in full_text
    assert '"summary": "Safe"' in full_text
    # We asserted 'const INITIAL_DATA' assuming regex, but if simple replace was used:
    # '<html>{"score": 80...}</html>'
    # So we simply check valid JSON content presence.
    
    # Verify return path
    assert "dashboard.html" in path

def test_generate_dashboard_template_missing(mock_config):
    from galt.ui import dashboard
    
    with patch("os.path.exists", return_value=False): # Template missing
        path = dashboard.generate_dashboard({}, {})
        assert path is None

def test_fallback_injection_regex(mock_config):
    # Test fallback regex replacement if marker is missing
    template_content = "<html><script>const INITIAL_DATA = {fallback: true};</script></html>"
    
    with patch("builtins.open", mock_open(read_data=template_content)) as m_open, \
         patch("os.path.exists", return_value=True), \
         patch("os.makedirs"):
        
        from galt.ui import dashboard
        dashboard.generate_dashboard({"score": 99}, {})
        
        handle = m_open()
        written = "".join([c.args[0] for c in handle.write.call_args_list])
        
        assert '"score": 99' in written
        assert 'fallback: true' not in written # Should be replaced
