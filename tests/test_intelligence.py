import pytest
import json
import os
from unittest.mock import MagicMock, patch
from galt.engine.bridge import Bridge
from google import genai 

def test_ai_mocking_active(mock_genai):
    """
    Verify that the Global Mock intercepts google.genai calls 
    and returns our pre-defined 'Mocked AI Analysis'.
    """
    client = genai.Client(api_key="DUMMY_KEY")
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents="Analyze this."
    )
    
    # Assert we got the mock response
    assert "Mocked AI Analysis" in response.text
    
    # Assert we didn't actually hit Google
    # The fixture yields the mock class, so we can check if it was instantiated
    assert mock_genai.called

def test_bridge_initialization(tmp_path):
    """
    Test that Bridge initializes correctly and creates the data directory.
    """
    # Use a temporary directory for the bridge data
    test_vault = tmp_path / "vault"
    
    # Patch load_dotenv to avoid side effects
    with patch('galt.engine.bridge.load_dotenv'):
        bridge = Bridge(data_dir=str(test_vault))
        
        assert os.path.exists(test_vault)
        assert bridge.data_dir == str(test_vault)
        # client might be None if no API key in env, but attribute should exist
        assert hasattr(bridge, 'client') 

def test_bridge_smart_caching(tmp_path, mock_genai):
    """
    Test the Safe/Smart Caching logic in Bridge.get_analysis
    """
    test_vault = tmp_path / "vault"
    
    with patch('galt.engine.bridge.load_dotenv'):
        # Mock env to ensure client is created (mocked by conftest/mock_genai)
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "TEST_KEY"}):
             bridge = Bridge(data_dir=str(test_vault))
             
             # 1. First Run (No History) -> Should call AI
             findings = [{"port": 80, "service": "http"}]
             score = 80
             
             result = bridge.get_analysis(findings, score)
             
             assert result["ai_status"] == "online"
             assert "Mocked AI Analysis" in result["markdown"]
             assert result["used_cache"] is False

             # 2. Second Run (Same Data) -> Should use Cache
             # The first run should have saved the state
             result_2 = bridge.get_analysis(findings, score)
             
             assert result_2["ai_status"] == "cached"
             assert result_2["used_cache"] is True
             assert result_2["markdown"] == result["markdown"]
             
             # 3. Third Run (Changed Data) -> Should call AI
             findings_changed = [{"port": 80, "service": "http"}, {"port": 443}]
             result_3 = bridge.get_analysis(findings_changed, score) # Score same, content changed
             
             assert result_3["ai_status"] == "online"
             assert result_3["used_cache"] is False
             
             # 4. Fourth Run (Improved Score) -> Should call AI
             score_improved = 90
             result_4 = bridge.get_analysis(findings_changed, score_improved)
             
             assert result_4["ai_status"] == "online"
             
