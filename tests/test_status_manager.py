import sys
import os
import json
import pytest
from unittest.mock import patch, mock_open

# Add root path to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import status_manager

def test_update_status_scanning(tmp_path):
    """Verifica que escribe el archivo JS correcto para estado SCANNING."""
    
    # Mock get_storage_path to return a tmp dir
    fake_reports_dir = tmp_path / "reports"
    fake_reports_dir.mkdir()
    
    with patch("status_manager.get_storage_path", return_value=str(fake_reports_dir)):
        status_manager.update_status("SCANNING", "Test Message")
        
        status_file = fake_reports_dir / "live_status.js"
        assert status_file.exists()
        
        content = status_file.read_text(encoding="utf-8")
        
        # Check structure: window.updateDashboardState({...});
        assert content.startswith("window.updateDashboardState(")
        assert content.endswith(");")
        
        # Extract JSON part
        json_part = content.replace("window.updateDashboardState(", "").replace(");", "")
        data = json.loads(json_part)
        
        assert data["state"] == "SCANNING"
        assert data["message"] == "Test Message"
        assert "timestamp" in data

def test_update_status_idle(tmp_path):
    """Verifica estado IDLE."""
    fake_reports_dir = tmp_path / "reports"
    fake_reports_dir.mkdir()
    
    with patch("status_manager.get_storage_path", return_value=str(fake_reports_dir)):
        status_manager.update_status("IDLE", "Done", 99)
        
        content = (fake_reports_dir / "live_status.js").read_text(encoding="utf-8")
        assert '"state": "IDLE"' in content
        assert '"score": "99"' in content
