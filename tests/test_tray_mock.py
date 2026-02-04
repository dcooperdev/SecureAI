import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock pystray and PIL before importing tray
@pytest.fixture
def mock_tray_libs():
    with patch.dict("sys.modules", {
        "pystray": MagicMock(),
        "PIL": MagicMock(),
        "PIL.Image": MagicMock()
    }):
        yield

def test_tray_initialization(mock_tray_libs):
    if "galt.ui.tray" in sys.modules:
        del sys.modules["galt.ui.tray"]
        
    from galt.ui import tray
    
    mock_icon = MagicMock()
    with patch("pystray.Icon", return_value=mock_icon) as m_icon_cls, \
         patch("PIL.Image.open"), \
         patch("PIL.Image.new"), \
         patch("galt.ui.tray.get_storage_path", return_value="C:\\Mock"):
         
         # Test load_icon logic
         img = tray.load_icon()
         assert img is not None
         
         # Test run_tray (mocking icon.run to avoid blocking)
         tray.run_tray()
         m_icon_cls.assert_called()
         mock_icon.run.assert_called()

def test_tray_actions(mock_tray_libs):
    if "galt.ui.tray" in sys.modules:
        del sys.modules["galt.ui.tray"]
    from galt.ui import tray
    
    # Mock open_dashboard
    with patch("webbrowser.open") as m_web, \
         patch("os.path.exists", return_value=True), \
         patch("galt.ui.tray.get_storage_path", return_value="C:\\Mock"):
        tray.open_dashboard()
        m_web.assert_called()
        
    # Mock run_manual_scan
    with patch("threading.Thread") as m_thread, \
         patch("galt.ui.tray.notification.notify"):
         
         mock_icon = MagicMock()
         tray.run_manual_scan(mock_icon, "Escanear Ahora")
         m_thread.assert_called()
         m_thread.return_value.start.assert_called()
