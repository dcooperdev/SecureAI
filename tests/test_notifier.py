
import pytest
import sys
import pathlib
from unittest.mock import patch, MagicMock
from core.notifier import Notifier

@pytest.fixture
def notifier():
    return Notifier()

def test_notify_windows_with_click(notifier):
    """Verify Windows uses XML Toast with protocol activation for click actions."""
    with patch("sys.platform", "win32"), \
         patch("subprocess.run") as mock_run, \
         patch("pathlib.Path.absolute") as mock_abs:
        
        # Mock Path so we can verify URI conversion
        mock_p = MagicMock()
        mock_p.as_uri.return_value = "file:///C:/Report.html"
        mock_abs.return_value = mock_p
        
        notifier.send_notification("Title", "Message", click_action="report.html")
        
        assert mock_run.called
        args = mock_run.call_args[0][0]
        # Verify PowerShell command construction
        assert args[0] == "powershell.exe"
        
        # Verify XML components
        script = args[2]
        assert '[Windows.UI.Notifications.ToastNotificationManager]' in script
        assert '<toast launch="file:///C:/Report.html" activationType="protocol">' in script
        assert '<text>Title</text>' in script
        assert '<text>Message</text>' in script

def test_notify_windows_simple(notifier):
    """Verify Windows falls back to simple toast/balloon if no click action (or verify default XML)."""
    with patch("sys.platform", "win32"), \
         patch("subprocess.run") as mock_run:
        
        notifier.send_notification("Title", "Message")
        
        # Just check it calls powershell
        assert mock_run.called
        assert "powershell.exe" in mock_run.call_args[0][0][0]

def test_notify_linux(notifier):
    """Verify Linux uses notify-send."""
    with patch("sys.platform", "linux"), \
         patch("shutil.which", return_value="/usr/bin/notify-send"), \
         patch("subprocess.run") as mock_run:
        
        notifier.send_notification("Title", "Message")
        
        mock_run.assert_called_with(
            ["notify-send", "Title", "Message"], 
            check=True
        )

def test_notify_macos(notifier):
    """Verify macOS uses osascript."""
    with patch("sys.platform", "darwin"), \
         patch("subprocess.run") as mock_run:
        
        notifier.send_notification("Title", "Message")
        
        args = mock_run.call_args[0][0]
        assert args[0] == "osascript"
        assert 'display notification "Message" with title "Title"' in args[2]

def test_notify_fallback_on_error(notifier, capsys):
    """Verify fallback to console print if subprocess fails."""
    with patch("sys.platform", "linux"), \
         patch("shutil.which", return_value="/usr/bin/notify-send"), \
         patch("subprocess.run", side_effect=Exception("Error")):
        
        notifier.send_notification("Title", "Message")
        
        # Check console output
        captured = capsys.readouterr()
        assert "[🔔] Galt: Title - Message" in captured.out
