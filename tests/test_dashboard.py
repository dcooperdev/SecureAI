import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add root path to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from galt.ui import dashboard as dashboard_generator

@pytest.fixture
def mock_get_storage_path():
    with patch("galt.ui.dashboard.get_storage_path") as mock:
        mock.return_value = "mock/path"
        yield mock

@pytest.fixture
def mock_glob():
    with patch("galt.ui.dashboard.glob.glob") as mock:
        mock.return_value = []
        yield mock

def test_render_dashboard_idle(mock_get_storage_path, mock_glob):
    """Verifica la generación básica del dashboard en estado IDLE."""
    current_data = {
        "score": 85,
        "ai_analysis": "Test Analysis"
    }
    logo_path = "C:/fake/logo.png"
    
    # We mock open to avoid file system reads being a problem or json load errors
    # But dashboard_generator tries to read files if glob finds them.
    # We mocked glob to return [], so it won't try to open anything for history.
    
    html = dashboard_generator.get_html_template(current_data, [], logo_path)
    
    assert "<!DOCTYPE html>" in html
    assert "Galt.ai Security Center" in html
    assert "Test Analysis" in html
    assert "file:///C:/fake/logo.png" in html or "file:///C:\\fake\\logo.png" in html.replace("/", "\\")

def test_render_dashboard_scanning():
    """Verifica que el HTML incluye la inyección de script de refresco (o clases) para scanning."""
    # Como el estado de 'scanning' en la v3 se maneja via JS (live_status.js) 
    # y clases CSS dinámicas, aquí verificamos que la estructura HTML y CSS 
    # necesaria para soportar eso exista.
    
    current_data = {"score": 0}
    html = dashboard_generator.get_html_template(current_data, [], "logo.png")
    
    # Check for scanning overlay existence
    assert "class=\"overlay-msg\"" in html
    assert "🔄 ANALIZANDO..." in html
    # Check for Scanning JS logic
    assert "window.updateDashboardState" in html
    assert "live_status.js" in html
