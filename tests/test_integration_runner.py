import pytest
from unittest.mock import MagicMock, patch
from galt.engine import orchestrator as runner

# FIX: Point to 'generate_dashboard' which is the real name in your code
@patch('galt.engine.orchestrator.dashboard_generator.generate_dashboard')
@patch('galt.engine.orchestrator.status_manager.update_status')
@patch('subprocess.Popen')
@patch('builtins.open')
def test_run_security_flow_structure(mock_open, mock_subprocess, mock_update_status, mock_generate_dashboard):
    """
    Test Integration: verifies the main flow mocking external dependencies.
    Ensures that the system reports SCANNING at start and IDLE/ERROR at the end.
    """
    # 1. Configure Mocks
    # Simulate that generator returns a file path
    mock_generate_dashboard.return_value = "c:\\mock\\report.html"
    
    # Simulate that sensors (subprocess) return empty JSON "[]"
    process_mock = MagicMock()
    process_mock.communicate.return_value = ('[]', '')
    mock_subprocess.return_value = process_mock

    # Simulate command line arguments so it does not ask for manual input
    with patch('argparse.ArgumentParser.parse_args') as mock_args:
        args = MagicMock()
        args.auto = True # Automatic mode to skip questions
        mock_args.return_value = args

        # 2. RUN RUNNER
        print("DEBUG: Starting runner.run_security_flow() under test...")
        runner.run_security_flow()

        # 3. VERIFICATIONS
        # Extract all states sent to update_status
        # call_args_list returns a list of calls. args[0] is the state.
        states_called = []
        if mock_update_status.call_count > 0:
            states_called = [call.args[0] for call in mock_update_status.call_args_list]
        
        print(f"DEBUG: States reported by the runner: {states_called}")

        # Validations
        # Verify that at least it tried to set to SCANNING
        assert "SCANNING" in states_called, f"ERROR: SCANNING state not reported. States: {states_called}"
        
        # Verify that it finished (IDLE or ERROR are acceptable as end)
        finished_correctly = "IDLE" in states_called or "ERROR" in states_called
        assert finished_correctly, f"ERROR: Flow did not finish in resting state. States: {states_called}"