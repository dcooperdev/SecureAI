import sys
import multiprocessing
import logging
import json
import os
from galt.core.config import setup_logging
# Import modules explicitly for PyInstaller analysis
from galt.engine import scheduler as sentinel
from galt.engine import orchestrator as runner
from galt.sensors import processes as sensor_procesos
from galt.sensors import network_basic as sensor_red
from galt.sensors import system as sensor_sistema
from galt.sensors import vuln as sensor_vulnerabilidades
from galt.sensors import network_scan as sensor_network_discovery
from galt.core.config import get_api_key
from galt.engine import onboarding

import ctypes
import threading
from galt.ui import tray as tray_manager

import subprocess

def hide_console(is_daemon=False):
    """
    Hides the console.
    - Windows: Uses native API (ShowWindow).
    - Posix (Linux/Mac): Relaunches the process in the background (start_new_session) if it is not a daemon.
    """
    if os.name == 'nt':
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE
                logging.info("Console hidden (Windows Mode).")
        except Exception as e:
            logging.error(f"Could not hide console: {e}")
    else:
        # Posix Strategy: Detach & Relaunch
        if is_daemon:
            logging.info("Running in Daemon mode (Background).")
            return

        logging.info("Transitioning to background (Posix)...")
        # Prepare command to relaunch ourselves
        cmd = [sys.executable]
        
        # If running as .py script (not frozen), we need to pass the script
        if not getattr(sys, 'frozen', False):
            # sys.argv[0] is usually main.py
            cmd.append(sys.argv[0])
            
        cmd.append("--daemon")
        
        # Launch disconnected child process
        subprocess.Popen(
            cmd, 
            start_new_session=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        sys.exit(0)

def dispatch():
    # Vital fix for Windows infinite loop with PyInstaller
    multiprocessing.freeze_support()
    setup_logging()

    # --- DAEMON CHECK ---
    is_daemon = False
    if "--daemon" in sys.argv:
        is_daemon = True
        sys.argv.remove("--daemon")

    # If it is a specific subprocess (e.g. runner executed by scheduler), we do not run GUI
    if len(sys.argv) > 1 and sys.argv[1] != "sentinel":
        mode = sys.argv[1]
        
        # CLEANUP ARGUMENTS for underlying modules
        sys.argv.pop(0)

        if mode == "runner":
            runner.run_security_flow()
        elif mode == "sensor_procesos": sensor_procesos.main()
        elif mode == "sensor_red": sensor_red.main()
        elif mode == "sensor_sistema": sensor_sistema.main()
        elif mode == "sensor_vulnerabilidades": sensor_vulnerabilidades.main()
        elif mode == "sensor_network_discovery": sensor_network_discovery.main()
        else:
            logging.error(f"Unknown mode: {mode}")
        return

    # --- MAIN MODE (Sentinel) ---
    
    # 1. ONBOARDING — show GUI dialog or CLI fallback depending on context.
    # Daemons skip this: the parent process must have already completed setup.
    if not get_api_key():
        if is_daemon:
            logging.error("Daemon started without API Key. Aborting.")
            sys.exit(1)

        if not onboarding.prompt_for_key():
            logging.error("Onboarding cancelled by user.")
            sys.exit(1)

    # Sanity-check the stored key is still valid
    current_key = get_api_key()
    if current_key and not onboarding.validate_key(current_key):
        if is_daemon:
            logging.error("Daemon: stored API Key is invalid.")
            sys.exit(1)

        if not onboarding.prompt_for_key():
            sys.exit(1)

    # 2. TRAY TRANSITION (Hide Console or Relaunch)
    if not is_daemon:
        print("✅ System configured. Starting surveillance mode...")
    
    hide_console(is_daemon) 

    # 3. START ENGINES
    logging.info("Starting Sentinel in background...")
    
    # Sentinel Thread (Background security logic)
    sentinel_thread = threading.Thread(target=sentinel.main_loop, daemon=True)
    sentinel_thread.start()

    # Main Thread (Tray UI - Blocking)
    # Pystray needs to run in the main thread
    tray_manager.run_tray()

if __name__ == "__main__":
    dispatch()
