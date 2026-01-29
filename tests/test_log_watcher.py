
import pytest
import sys
import json
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
from galt.core.log_watcher import LogSentinel

# Helpers to generate mock logs
def generate_windows_log(count=5):
    """Generates a mock PowerShell output with recent disconnect events."""
    lines = []
    now = datetime.now()
    for i in range(count):
        t = (now - timedelta(seconds=i*5)).strftime("%m/%d/%Y %I:%M:%S %p")
        # Format: Id, TimeCreated, Message
        lines.append(f"8003 @ {{TimeCreated={t}; Message=WLAN AutoConfig detected limit connectivity}}")
    return "\n".join(lines)

def generate_linux_log(count=5):
    """Generates mock syslog lines with recent disconnects."""
    lines = []
    now = datetime.now()
    for i in range(count):
        # Syslog format often just time like 'Jan 26 10:00:00' or ISO
        t = (now - timedelta(seconds=i*5)).strftime("%Y-%m-%dT%H:%M:%S")
        lines.append(f"{t} host wpa_supplicant[123]: wlan0: CTRL-EVENT-DISCONNECTED bssid=xx reason=3")
    return "\n".join(lines)

@pytest.fixture
def sentinel():
    return LogSentinel()

def test_detect_deauth_loop_windows(sentinel):
    """Test detection of disconnect loop on Windows."""
    mock_output = generate_windows_log(5) # 5 events in ~25 seconds
    
    with patch("sys.platform", "win32"), \
         patch("subprocess.check_output", return_value=mock_output): # Return str
        
        findings = sentinel.scan()
        
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"
        assert "Inestabilidad crítica" in findings[0]["description"]
        assert "5 eventos" in findings[0]["result"]["details"]

def test_clean_windows(sentinel):
    """Test no findings when logs are clean or empty."""
    with patch("sys.platform", "win32"), \
         patch("subprocess.check_output", return_value=""): # Return str
        
        findings = sentinel.scan()
        assert len(findings) == 0

def test_detect_deauth_loop_linux_journalctl(sentinel):
    """Test detection on Linux via journalctl."""
    mock_output = generate_linux_log(5)
    
    with patch("sys.platform", "linux"), \
         patch("shutil.which", return_value="/usr/bin/journalctl"), \
         patch("subprocess.check_output", return_value=mock_output): # Return str
        
        findings = sentinel.scan()
        
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"
        assert "Disconnect" in findings[0]["result"]["details"] or "5 eventos" in findings[0]["result"]["details"]

def test_permission_error_graceful(sentinel):
    """Test graceful handling of permission errors."""
    with patch("sys.platform", "win32"), \
         patch("subprocess.check_output", side_effect=PermissionError("Access Denied")):
        
        findings = sentinel.scan()
        assert len(findings) == 0  # Should not crash, just return empty
