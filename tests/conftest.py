import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_subprocess():
    """
    Global mock for subprocess calls to prevent system modification.
    Returns a magic mock that simulates a successful process execution (returncode=0).
    """
    with patch("subprocess.run") as mock_run, \
         patch("subprocess.check_output") as mock_check, \
         patch("os.system") as mock_system:
        
        # Configure default success behavior
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Subprocess Success"
        mock_run.return_value.stderr = ""
        
        mock_check.return_value = b"Subprocess Success"
        mock_system.return_value = 0
        
        yield mock_run

@pytest.fixture(autouse=True)
def mock_requests():
    """
    Global mock for requests to prevent HTTP traffic.
    """
    with patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post:
        
        # Configure default response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "mocked", "data": []}
        mock_resp.text = "Mocked Response"
        
        mock_get.return_value = mock_resp
        mock_post.return_value = mock_resp
        
        yield {"get": mock_get, "post": mock_post}

@pytest.fixture(autouse=True)
def mock_genai():
    """
    Global mock for Google GenAI to prevent API quota usage.
    Mocks both google.genai and google.generativeai logic.
    """
    # Create a mock client structure that allows client.models.generate_content(...)
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Mocked AI Analysis: System appears secure."
    
    msg_chain = MagicMock()
    msg_chain.generate_content.return_value = mock_response
    
    mock_client_instance.models = msg_chain
    mock_client_instance.generative_model.return_value = msg_chain

    with patch("google.genai.Client", return_value=mock_client_instance) as mock_cls, \
         patch("google.generativeai.GenerativeModel") as mock_legacy_model:
             
        mock_legacy_model.return_value.generate_content.return_value = mock_response
        yield mock_cls

@pytest.fixture(autouse=True)
def mock_scapy():
    """
    Global mock for Scapy to prevent network sniffing/injection.
    """
    with patch.dict("sys.modules", {"scapy.all": MagicMock(), "scapy": MagicMock()}):
        yield
