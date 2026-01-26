import sys
import multiprocessing
import logging
import json
import os
from config import setup_logging
# Import modules explicitly for PyInstaller analysis
import sentinel
import runner
import sensor_procesos
import sensor_red
import sensor_sistema
import sensor_vulnerabilidades
import sensor_network_discovery
from config import get_api_key
import onboarding

import ctypes
import threading
import tray_manager

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
    
    # 1. VALIDACIÓN / ONBOARDING (Consola Visible si no es daemon)
    # Si somos daemon, asumimos que el padre ya hizo el onboarding o fallará silenciosamente (lo cual es correcto)
    if not get_api_key():
        if is_daemon:
            logging.error("Daemon iniciado sin API Key. Abortando.")
            sys.exit(1)
            
        print("\n⚠️  GALT.AI: Configuración Inicial Requerida")
        # El usuario interactúa aquí con la ventana negra
        if not onboarding.prompt_for_key_console():
            print("❌ Cancelado por el usuario.")
            sys.exit(1)
            
    # Validar que la llave sea funcional (sanity check)
    current_key = get_api_key()
    if current_key and not onboarding.validate_key(current_key):
         if is_daemon:
             logging.error("Daemon: API Key inválida.")
             sys.exit(1)
             
         print("⚠️  La llave guardada parece inválida. Re-iniciando onboarding...")
         if not onboarding.prompt_for_key_console():
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
