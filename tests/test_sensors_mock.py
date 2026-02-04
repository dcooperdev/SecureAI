import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import json
from contextlib import contextmanager
import subprocess

# --- TEST SYSTEM SENSOR ---
def test_system_sensor():
    with patch("platform.system", return_value="Windows"), \
         patch("platform.release", return_value="10"), \
         patch("platform.version", return_value="10.0.19045"), \
         patch("platform.machine", return_value="AMD64"), \
         patch("platform.node", return_value="TEST-NODE"), \
         patch("socket.gethostname", return_value="TEST-PC"), \
         patch("psutil.users", return_value=[MagicMock(name="TestUser")]), \
         patch("psutil.boot_time", return_value=1600000000), \
         patch("psutil.net_if_addrs", return_value={}), \
         patch("psutil.virtual_memory") as mock_mem:
        
        mock_mem.return_value.total = 16000000000
        mock_mem.return_value.available = 8000000000
        
        from galt.sensors import system
        
        with patch("sys.stdout") as mock_stdout:
            system.main()
            
            output = ""
            for call in mock_stdout.write.call_args_list:
                output += call.args[0]
            
            assert '"plugin": "sensor_sistema"' in output
            assert '"hostname": "TEST-NODE"' in output

# --- TEST VULN SENSOR ---
def test_vuln_sensor():
    # Mock socket to simulate open/closed ports
    with patch("socket.socket") as mock_sock:
        mock_instance = MagicMock()
        mock_sock.return_value = mock_instance
        
        # Scenario: Port 445 Open, others closed
        def side_effect(address):
            ip, port = address
            if port == 445: return 0
            return 1
            
        mock_instance.connect_ex.side_effect = side_effect
        
        from galt.sensors import vuln
        
        with patch("sys.stdout") as mock_stdout:
            # Fix: Mock sys.argv to avoid SystemExit from argparse
            with patch("sys.argv", ["vuln.py", "--local-only"]):
                 vuln.main()

            output = ""
            for call in mock_stdout.write.call_args_list:
                 output += call.args[0]
            
            assert '445' in output
            assert '"plugin": "sensor_vulnerabilidades"' in output

# --- TEST PROCESSES SENSOR ---
def test_processes_sensor():
    mock_proc = MagicMock()
    mock_proc.info = {'pid': 1234, 'name': 'malware.exe', 'username': 'System'}
    # Fix for process.name() call in code
    mock_proc.name.return_value = 'malware.exe'
    mock_proc.username.return_value = 'System'
    mock_proc.status.return_value = 'running'
    mock_proc.exe.return_value = 'c:\\malware.exe'
    
    # Fix: Ensure raddr.ip is a string for JSON serialization
    mock_conn = MagicMock()
    mock_conn.laddr = MagicMock(port=445)
    mock_conn.raddr = MagicMock()
    mock_conn.raddr.ip = "192.168.1.50" 
    mock_conn.pid = 1234
    mock_conn.status = "ESTABLISHED"
    
    with patch("psutil.process_iter", return_value=[mock_proc]), \
         patch("psutil.Process", return_value=mock_proc), \
         patch("psutil.net_connections", return_value=[mock_conn]), \
         patch("sys.argv", ["processes.py", "--local-only"]):
         
         from galt.sensors import processes
         
         with patch("sys.stdout") as mock_stdout:
             processes.main()
             
             output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
             
             assert '"plugin": "sensor_procesos"' in output
             assert '"process":' in output
             assert 'malware.exe' in output

# --- TEST NETWORK SCAN (THREADED PING) ---
def test_network_scan_sensor():
    # Mock subprocess for ping success
    # Ping returns 0 (Success) for 192.168.1.50, else raise CalledProcessError
    def ping_side_effect(args, **kwargs):
        if "192.168.1.50" in args:
            return 0
        raise subprocess.CalledProcessError(1, args)

    with patch("subprocess.check_call", side_effect=ping_side_effect), \
         patch("socket.gethostbyaddr", return_value=("test-host.local", [], [])), \
         patch("socket.socket") as mock_socket, \
         patch("sys.argv", ["network_scan.py", "--local-only"]):
             
             # Mock socket connect_ex for ports (all open for speed/test)
             mock_socket.return_value.connect_ex.return_value = 0
             # Mock getsockname for local ip discovery
             mock_socket.return_value.getsockname.return_value = ("192.168.1.10", 0)

             from galt.sensors import network_scan
             
             # Limit the target range in main to avoid 254 threads during test?
             # We can mock ThreadPoolExecutor to verify logic without waiting, 
             # OR we can just let it run fast since we mocked PING.
             # Better: Mock generating targets to be small list
             
             with patch("galt.sensors.network_scan.ThreadPoolExecutor") as MockExecutor:
                 # Mock the context manager of executor
                 mock_executor_instance = MagicMock()
                 MockExecutor.return_value.__enter__.return_value = mock_executor_instance
                 
                 # We can allow submit to call the callback immediately or just ignore it.
                 # To verify logic, we want scan_target to run.
                 # But scan_target requires arguments.
                 # Let's just run main() and assume it submits jobs.
                 # We can't easily capture the result unless we mock what submit does.
                 
                 # Strategy: Mock scan_target to just append to results list passed to it?
                 # main() passes 'discovered_hosts' list to scan_target.
                 # If we intercept submit, we can execute the function.
                 
                 def immediate_submit(fn, *args, **kwargs):
                     # args[2] is results list in scan_target(ip, common_ports, results, lock)
                     # Let's just simulate a hit manually in the results list?
                     # Or let it run if fn is the real function.
                     if fn.__name__ == 'scan_target':
                         # args: ip, common_ports, results, lock
                         results_list = args[2]
                         # Check if this IP is our target "192.168.1.50"
                         ip = args[0]
                         if ip == "192.168.1.50":
                             results_list.append({
                                 "ip": ip,
                                 "hostname": "test-host",
                                 "open_ports": [80],
                                 "status": "ONLINE"
                             })
                     return MagicMock()

                 mock_executor_instance.submit.side_effect = immediate_submit

                 with patch("sys.stdout") as mock_stdout:
                     network_scan.main()
                     
                     output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
                     
                     assert '"plugin": "sensor_network_discovery"' in output
                     assert '"local_ip": "192.168.1.10"' in output
                     # Verify we found the host injected via side_effect
                     assert '"ip": "192.168.1.50"' in output

# --- TEST NETWORK BASIC ---
def test_network_basic_sensor():
    with patch("socket.socket") as mock_sock, \
         patch("socket.gethostname", return_value="MyPC"):
         
         mock_sock.return_value.getsockname.return_value = ("10.0.0.5", 0)
         
         from galt.sensors import network_basic
         
         with patch("sys.stdout") as mock_stdout:
             network_basic.main()
             output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
             
             # Fix assertion: correct plugin name found in source
             assert '"plugin": "sensor_network_basic"' in output
             assert '"local_ip": "10.0.0.5"' in output
