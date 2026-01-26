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

def hide_console():
    """Oculta la ventana de consola en Windows usando la API de Win32."""
    if os.name == 'nt':
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 0) # 0 = SW_HIDE
                logging.info("Consola ocultada. Entrando en modo sigiloso.")
        except Exception as e:
            logging.error(f"No se pudo ocultar consola: {e}")

def dispatch():
    # Vital fix for Windows infinite loop with PyInstaller
    multiprocessing.freeze_support()
    setup_logging()

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
    
    # 1. VALIDACIÓN / ONBOARDING (Consola Visible)
    if not get_api_key():
        print("\n⚠️  GALT.AI: Configuración Inicial Requerida")
        # El usuario interactúa aquí con la ventana negra
        if not onboarding.prompt_for_key_console():
            print("❌ Cancelado por el usuario.")
            sys.exit(1)
            
    # Validar que la llave sea funcional (sanity check)
    current_key = get_api_key()
    if current_key and not onboarding.validate_key(current_key):
         print("⚠️  La llave guardada parece inválida. Re-iniciando onboarding...")
         if not onboarding.prompt_for_key_console():
            sys.exit(1)

    # 2. TRANSICIÓN A TRAY (Ocultar Consola)
    print("✅ Sistema configurado. Iniciando modo vigilancia...")
    hide_console() 

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
