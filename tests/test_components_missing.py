import pytest
from unittest.mock import MagicMock, patch
import sys
import subprocess
from galt.engine import scheduler
from galt.engine import onboarding

# --- SCHEDULER TESTS ---
def test_scheduler_main_loop_flow():
    # Test valid flow: config -> run -> sleep -> break
    
    with patch("galt.engine.scheduler.check_remote_config") as m_config, \
         patch("galt.engine.scheduler.subprocess.run") as m_run, \
         patch("time.sleep", side_effect=StopIteration), \
         patch("sys.stdout"), \
         patch("galt.engine.scheduler.get_current_score", side_effect=[100, 95]):
         
         # Config returns: interval, plan, status
         m_config.return_value = (10, "TEST", "Active")
         
         # Mock subprocess output
         m_run.return_value = MagicMock(returncode=0, stdout="Score: 95\nDRIFT DETECTADO")
         
         # Run
         try:
             scheduler.main_loop()
         except StopIteration:
             pass
         
         # Verify runner was called
         m_run.assert_called_once()
         cmd = m_run.call_args[0][0]
         # Should call python -m galt.engine.orchestrator or runner
         assert "galt.engine.orchestrator" in cmd or "runner" in cmd[0]

def test_scheduler_test_mode():
    # Test --test flag path
    with patch("sys.argv", ["main.py", "--test"]), \
         patch("galt.engine.scheduler.subprocess.run") as m_run, \
         patch("time.sleep", side_effect=StopIteration), \
         patch("sys.stdout") as m_stdout:
         
         try:
             scheduler.main_loop()
         except StopIteration:
             pass
         
         output = "".join([c.args[0] for c in m_stdout.write.call_args_list if c.args])
         assert "MODO PRUEBAS" in output

def test_scheduler_expired_license():
    # Test interval 0 -> Exit
    with patch("galt.engine.scheduler.check_remote_config", return_value=(0, "EXPIRED", "Expired")), \
         patch("sys.stdout") as m_stdout:
         
         scheduler.main_loop()
         
         # Should print error and return immediately (no sleep, no loop)
         output = "".join([c.args[0] for c in m_stdout.write.call_args_list if c.args])
         assert "falta de licencia" in output

# --- ONBOARDING TESTS ---
def test_onboarding_console_success():
    # Test console input flow with valid key
    with patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", side_effect=["test_api_key"]), \
         patch("galt.engine.onboarding.validate_key", return_value=True) as m_val, \
         patch("galt.engine.onboarding.save_api_key") as m_save, \
         patch("builtins.print"):
         
         result = onboarding.prompt_for_key()
         
         assert result is True
         m_val.assert_called_with("test_api_key")
         m_save.assert_called_with("test_api_key")

def test_onboarding_console_retry_then_fail():
    # Test invalid key retry logic (loop)
    # Side effect: Invalid Key, then EOFError (simulate user exit or cancel)
    with patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", side_effect=["bad_key", EOFError]), \
         patch("galt.engine.onboarding.validate_key", return_value=False), \
         patch("builtins.print"):
         
         try:
             result = onboarding.prompt_for_key()
             assert result is False
         except EOFError:
             pass

def test_validate_key_logic():
    # Test actual validate_key function
    # Patch the module 'genai' inside onboarding
    with patch("galt.engine.onboarding.genai") as m_genai:
        # Configure successful client call
        m_client_instance = MagicMock()
        m_genai.Client.return_value = m_client_instance
        
        # Configure models.list() to return an iterable
        # It needs to be an iterator that yields at least one item
        m_client_instance.models.list.return_value = iter(["model1"])
        
        # Key must be > 20 chars
        valid_key = "valid_key_longer_than_20_chars_for_testing"
        
        # Capture logging to debug exception
        with patch("galt.engine.onboarding.logging.warning") as m_warn:
            result = onboarding.validate_key(valid_key)
            if not result and m_warn.called:
                print(f"DEBUG FAIL REASON: {m_warn.call_args}")
            assert result == True
        
        # Failure case
        m_genai.Client.side_effect = Exception("Auth Error")
        assert onboarding.validate_key("invalid_key") == False
