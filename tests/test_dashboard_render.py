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
    # Mock open for reading config/history/template and writing JS/JSON
    mock_open_obj = mock_open(read_data='[]') 
    with patch("builtins.open", mock_open_obj) as m_open, \
         patch("os.path.exists", return_value=True) as m_exists, \
         patch("os.makedirs") as m_mkdirs:
         yield m_open, m_exists, m_mkdirs

def test_generate_dashboard_success(mock_config, mock_fs):
    from galt.ui import dashboard
    
    scan_results = {
        "score": 80,
        "timestamp_human": "Now",
        "open_ports": [80],
        "timestamp_epoch": 12345
    }
    ai_analysis = {"summary": "Safe"}
    
    path = dashboard.generate_dashboard(scan_results, ai_analysis)
    
    # Verify file operations
    m_open, _, _ = mock_fs
    
    # Needs to write:
    # 1. vault/reports/latest.json
    # 2. vault/reports/scan_12345.json
    # 3. vault/reports/scan_12345.js (History)
    # 4. vault/reports/galt_loader.js (Loader)
    # 5. history.json index
    # Plus potential dev mirrors.
    assert m_open.call_count >= 4
    
    # Check if we wrote the JS Loader correctly
    handle = m_open()
    written_data = []
    for call in handle.write.call_args_list:
        written_data.append(call.args[0])
    
    full_text = "".join(written_data)
    
    # Check for JS Content
    assert 'window.GALT_LATEST_REPORT' in full_text
    assert '"score": 80' in full_text
    assert 'window.GALT_HISTORY_INDEX' in full_text
    
    # Verify return path is the static template
    assert "viewer.html" in path

def test_generate_dashboard_template_missing(mock_config):
    from galt.ui import dashboard
    
    with patch("os.path.exists", return_value=False): # Template missing
        path = dashboard.generate_dashboard({}, {})
        # Depending on logic, it might return None if template not found
        assert path is None

