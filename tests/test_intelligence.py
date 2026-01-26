import pytest
import json
from unittest.mock import MagicMock
# Assuming logic to be tested is in bridge.py or runner.py, 
# but for the "Mock Everything" demo we will test the bridge logic specifically.
# Since bridge.py is a script, we might need to import the client or refactor it.
# For now, let's assume we are testing the Global Mock's ability to intercept genai.

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

def test_bridge_logic_safe():
    """
    Import bridge and ensure it doesn't crash or make real calls on import/execution.
    Note: bridge.py executes on import if not protected by if __name__ == "__main__".
    We checked bridge.py and it has the protection.
    """
    import bridge
    # If bridge had side effects, the global mocks should catch them.
    assert bridge.client is not None
