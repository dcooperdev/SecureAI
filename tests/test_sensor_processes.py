import pytest
import sys
import subprocess
import psutil
from unittest.mock import MagicMock
from galt.sensors import processes

# --- CONSTANTS: REAL COMMAND OUTPUTS ---

# Windows: tasklist /FI "PID eq 1234" /FO CSV /NH
MOCK_WIN_TASKLIST = '"imagename.exe","1234","Console","0","1,234 K"'

# Linux: ss -lntp
# Format: State Recv-Q Send-Q Local Address:Port Peer Address:Port Process
MOCK_LINUX_SS = """State      Recv-Q Send-Q Local Address:Port               Peer Address:Port              
LISTEN     0      128          0.0.0.0:80                  0.0.0.0:*                   users:(("nginx",pid=1234,fd=6))
LISTEN     0      128          0.0.0.0:22                  0.0.0.0:*                   users:(("sshd",pid=5678,fd=3))
"""

# Linux: ps -p 1234 -o comm=
MOCK_LINUX_PS_COMM = "nginx"

# macOS: lsof -iTCP -sTCP:LISTEN -P -n
# Format: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
MOCK_MAC_LSOF = """COMMAND   PID USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
nginx    1234 root    6u  IPv4 0x12345678      0t0  TCP *:80 (LISTEN)
sshd     5678 root    3u  IPv6 0x87654321      0t0  TCP *:22 (LISTEN)
"""

# Windows: netstat -ano
MOCK_WIN_NETSTAT = """
  Proto  Local Address          Foreign Address        State           PID
  TCP    0.0.0.0:80             0.0.0.0:0              LISTENING       1234
  TCP    0.0.0.0:445            0.0.0.0:0              LISTENING       4
"""

# --- FIXTURES ---

@pytest.fixture
def mock_modules(mocker):
    """Mock wmi and pywin32 modules to prevent ImportErrors on non-Windows systems."""
    mocker.patch.dict(sys.modules, {'wmi': MagicMock(), 'win32api': MagicMock(), 'win32con': MagicMock()})

@pytest.fixture
def mock_subprocess(mocker):
    return mocker.patch("subprocess.check_output")

@pytest.fixture
def mock_platform(mocker):
    return mocker.patch("platform.system")

# --- TESTS ---

@pytest.mark.parametrize("os_name, mock_output, expected_map", [
    ("Windows", MOCK_WIN_NETSTAT, {80: 1234, 445: 4}),
    ("Linux", MOCK_LINUX_SS, {80: 1234, 22: 5678}),
    ("Darwin", MOCK_MAC_LSOF, {80: 1234, 22: 5678}),
])
def test_get_netstat_map_by_os(mock_modules, mock_subprocess, mock_platform, os_name, mock_output, expected_map):
    """
    Test native port-to-PID mapping across different OSs using real output samples.
    """
    mock_platform.return_value = os_name
    
    # Configure subprocess mock based on OS command expectation
    # The code calls subprocess.check_output differently per OS
    if os_name == "Windows":
        mock_subprocess.return_value = mock_output.encode("cp850") # Encode as bytes as check_output returns bytes
    else:
        # Linux/Mac usually utf-8
        mock_subprocess.return_value = mock_output.encode("utf-8")
        
    result = processes.get_netstat_map()
    
    assert result == expected_map
    
    # Verify the correct command was called (Basic check)
    if os_name == "Windows":
        mock_subprocess.assert_called_with("netstat -ano", shell=True)
    elif os_name == "Linux":
        # Check if called with list
        args, _ = mock_subprocess.call_args
        assert args[0] == ["ss", "-lntp"]
    elif os_name == "Darwin":
        args, _ = mock_subprocess.call_args
        assert args[0] == ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"]


def test_get_process_name_fallback_windows(mock_modules, mock_subprocess, mock_platform):
    """Test fallback to tasklist on Windows."""
    mock_platform.return_value = "Windows"
    mock_subprocess.return_value = MOCK_WIN_TASKLIST.encode("utf-8")
    
    name = processes.get_process_name_by_pid_fallback(1234)
    assert name == "imagename.exe"
    
    # Validate command construction
    cmd = mock_subprocess.call_args[0][0]
    assert 'tasklist /FI "PID eq 1234"' in cmd

def test_get_process_name_fallback_linux(mock_modules, mock_subprocess, mock_platform):
    """Test fallback to ps on Linux."""
    mock_platform.return_value = "Linux"
    mock_subprocess.return_value = MOCK_LINUX_PS_COMM.encode("utf-8")
    
    name = processes.get_process_name_by_pid_fallback(1234)
    assert name == "nginx"

def test_get_process_name_fallback_failure(mock_modules, mock_subprocess, mock_platform):
    """Test graceful handling when fallback command fails."""
    mock_platform.return_value = "Linux"
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "cmd")
    
    name = processes.get_process_name_by_pid_fallback(9999)
    assert name == "Unknown (System/Protected)"

def test_get_process_info_access_denied(mock_modules, mocker):
    """Test AccessDenied handling with fallback."""
    # Mock psutil.Process to raise AccessDenied
    mock_proc_class = mocker.patch("psutil.Process")
    mock_proc_class.side_effect = psutil.AccessDenied(pid=1234)
    
    # Mock fallback to return a name
    mocker.patch("galt.sensors.processes.get_process_name_by_pid_fallback", return_value="SystemProcess")
    
    info = processes.get_process_info(1234)
    
    assert info["pid"] == 1234
    assert info["name"] == "SystemProcess"
    assert info["username"] == "SYSTEM/Protected"
    assert info["exe"] == "AccessDenied"

def test_get_process_info_no_such_process(mock_modules, mocker):
    """Test NoSuchProcess handling."""
    mock_proc_class = mocker.patch("psutil.Process")
    mock_proc_class.side_effect = psutil.NoSuchProcess(pid=9999)
    
    info = processes.get_process_info(9999)
    assert info is None

def test_main_execution_flow(mock_modules, mocker):
    """Test the main function logic aggregating everything."""
    # Mock Connections: 1 Listener, 1 Outbound
    mock_listen = MagicMock()
    mock_listen.laddr.port = 80
    mock_listen.status = "LISTEN"
    mock_listen.pid = 1234
    mock_listen.raddr = None # Listeners usually have empty raddr

    mock_outbound = MagicMock()
    mock_outbound.laddr.port = 54321
    mock_outbound.status = "ESTABLISHED"
    mock_outbound.pid = 1234
    mock_outbound.raddr = MagicMock()
    mock_outbound.raddr.ip = "93.184.216.34" # Example External IP
    
    mocker.patch("psutil.net_connections", return_value=[mock_listen, mock_outbound])
    
    # Mock process info success
    mocker.patch("galt.sensors.processes.get_process_info", return_value={
        "name": "nginx", "pid": 1234, "username": "www-data", "status": "running", "exe": "/usr/sbin/nginx"
    })
    
    # Capture stdout
    mock_stdout = mocker.patch("sys.stdout")
    
    # FIX: Patch sys.argv using the correct mock path and arguments
    mocker.patch("sys.argv", ["processes.py", "--local-only"])
    processes.main()
    
    # Check output - Concatenate all writes
    output_str = "".join([call.args[0] for call in mock_stdout.write.call_args_list])
    import json
    output = json.loads(output_str)
    
    assert output["plugin"] == "sensor_procesos"
    # Basic validation of structure
    assert "result" in output
    data = output["result"]["data"]
    
    # Check Listener
    assert any(d["port"] == 80 for d in data)
    # Check Outbound
    assert any(d.get("remote_ip") == "93.184.216.34" for d in data)
