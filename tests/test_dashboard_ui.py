import pytest
import os
import json
from reports.dashboard_generator import get_html_template

@pytest.fixture
def mock_clean_data():
    return {
        "score": 95,
        "ai_analysis": None,  # Force fallback
        "findings": [],
        "ui_date_full": "2026-01-26 14:00:00"
    }

@pytest.fixture
def mock_threat_data():
    return {
        "score": 45,
        "ai_analysis": None,
        "findings": [
            {"module": "sensor_network_discovery", "result": {"severity": "HIGH", "details": "Unknown IP"}},
            {"module": "sensor_sistema", "result": {"severity": "MEDIUM", "details": "Old OS"}}
        ],
        "ui_date_full": "2026-01-26 14:00:00"
    }

def test_score_color_critical(mock_threat_data):
    """Test 1: Traffic Light Score - Critical (Red)"""
    mock_threat_data['score'] = 45 
    html = get_html_template(mock_threat_data, [], "logo.png")
    
    # Assert the data is correctly embedded in the JS payload
    # Check for compact JSON format or ensure values exist
    assert '"score": 45' in html or '"score":45' in html
    
    # Assert the CSS logic for colors is present in the script
    assert "if(score >= 90) return '#2dce89';" in html
    assert "return '#f5365c';" in html

def test_score_color_secure(mock_clean_data):
    """Test 1b: Traffic Light Score - Secure (Green)"""
    mock_clean_data['score'] = 95
    html = get_html_template(mock_clean_data, [], "logo.png")
    
    assert '"score": 95' in html or '"score":95' in html

def test_fallback_mode_visuals(mock_threat_data):
    """Test 2: Fallback Rendering - Icons & Hidden Raw Data"""
    # Ensure data is present for JS to render
    html = get_html_template(mock_threat_data, [], "logo.png")
    
    assert '"details": "Unknown IP"' in html or '"details":"Unknown IP"' in html
    assert '"details": "Old OS"' in html or '"details":"Old OS"' in html
    
    # Assert Structural Elements exist
    assert 'id="score-val"' in html
    assert 'class="score-big"' in html
    assert 'id="fallback-container"' in html
    
    # Assert JS Logic for rendering is present
    assert 'function renderFallbackMode(findings)' in html
    assert 'fa-wifi' in html  # Check for mapping logic
    assert 'fa-microchip' in html

def test_empty_state(mock_clean_data):
    """Test 3: Empty State - System Secure"""
    html = get_html_template(mock_clean_data, [], "logo.png")
    
    # Assert JS Logic for empty state is present
    assert 'findings.length === 0' in html
    assert 'Sistema Seguro' in html
    assert 'fa-shield-halved' in html
