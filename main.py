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
    Oculta la consola.
    - Windows: Usa API nativa (ShowWindow).
    - Posix (Linux/Mac): Relanza el proceso en background (start_new_session) si no es daemon.
    """
    if os.name == 'nt':
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE
                logging.info("Consola ocultada (Windows Mode).")
        except Exception as e:
            logging.error(f"No se pudo ocultar consola: {e}")
    else:
        # Posix Strategy: Detach & Relaunch
        if is_daemon:
            logging.info("Ejecutando en modo Daemon (Background).")
            return

        logging.info("Transicionando a segundo plano (Posix)...")
        # Preparamos el comando para relanzarnos a nosotros mismos
        cmd = [sys.executable]
        
        # Si corremos como script .py (no congelado), necesitamos pasar el script
        if not getattr(sys, 'frozen', False):
            # sys.argv[0] suele ser main.py
            cmd.append(sys.argv[0])
            
        cmd.append("--daemon")
        
        # Lanzar proceso hijo desconectado
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

    # Si es un subproceso específico (ej: runner ejecutado por el scheduler), no hacemos nada de GUI
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
            logging.error(f"Modo desconocido: {mode}")
        return

    # --- MODO PRINCIPAL (Sentinel) ---
    
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

    # 2. TRANSICIÓN A TRAY (Ocultar Consola o Relanzar)
    if not is_daemon:
        print("✅ Sistema configurado. Iniciando modo vigilancia...")
    
    hide_console(is_daemon) 

    # 3. INICIAR MOTORES
    logging.info("Arrancando Sentinel en background...")
    
    # Hilo del Sentinel (Lógica de seguridad en background)
    sentinel_thread = threading.Thread(target=sentinel.main_loop, daemon=True)
    sentinel_thread.start()

    # Hilo Principal (UI del Tray - Bloqueante)
    # Pystray necesita correr en el hilo principal
    tray_manager.run_tray()

if __name__ == "__main__":
    dispatch()
