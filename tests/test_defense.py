import pytest
import platform
from core.defense import FirewallManager

class TestFirewallManager:
    
    def test_block_ip_windows(self, mock_subprocess, monkeypatch):
        """
        Verify that block_ip constructs the correct 'netsh' command on Windows.
        """
        # 1. Simulate Windows Environment
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        
        manager = FirewallManager()
        result = manager.block_ip("192.168.1.100")
        
        # 2. Assertions
        assert result is True
        
        # Check if subprocess.run was called
        assert mock_subprocess.called
        
        # Check the exact command arguments (Spy)
        args, _ = mock_subprocess.call_args
        command_list = args[0]
        
        assert command_list[0] == "netsh"
        assert f"name=GALT_BLOCK_192.168.1.100" in command_list
        assert f"remoteip=192.168.1.100" in command_list
        assert "action=block" in command_list

    def test_block_ip_linux(self, mock_subprocess, monkeypatch):
        """
        Verify that block_ip constructs the correct 'iptables' command on Linux.
        """
        # 1. Simulate Linux Environment
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        
        manager = FirewallManager()
        result = manager.block_ip("10.0.0.5")
        
        # 2. Assertions
        assert result is True
        
        args, _ = mock_subprocess.call_args
        command_list = args[0]
        
        assert command_list[0] == "iptables"
        assert "-A" in command_list
        assert "INPUT" in command_list
        assert "-j" in command_list
        assert "DROP" in command_list
        # Check IP placement
        assert command_list[command_list.index("-s") + 1] == "10.0.0.5"

    def test_unsupported_os(self, mock_subprocess, monkeypatch):
        """
        Verify graceful failure on unsupported OS.
        """
        monkeypatch.setattr(platform, "system", lambda: "MacOS") # MVP constraint
        
        manager = FirewallManager()
        result = manager.block_ip("1.2.3.4")
        
        assert result is False
        # Ensure no command was executed
        assert not mock_subprocess.called
