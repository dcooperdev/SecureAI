import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import webbrowser
import os
import sys
import threading
import logging

def load_icon():
    """Carga app.ico (Windows) o logo.png (Otros) desde la ruta correcta."""
    # Soporte para PyInstaller (ruta temporal _MEI)
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    
    icon_path_win = os.path.join(base_path, "app.ico")
    icon_path_png = os.path.join(base_path, "logo.png")
    
    if os.path.exists(icon_path_win):
        return Image.open(icon_path_win)
    elif os.path.exists(icon_path_png):
        return Image.open(icon_path_png)
    else:
        # Fallback: Generar cuadrado rojo si fallan los assets
        return Image.new('RGB', (64, 64), color = 'red')

def on_scan(icon, item):
    """Trigger a manual scan (conceptually)."""
    # In a real event system, we would signal the sentinel thread.
    # For now, we just log it or maybe run a one-off runner.
    logging.info("User requested Manual Scan from Tray.")
    # This implies we might want to trigger `runner.run_security_flow()` 
    # but strictly speaking, the sentinel is running on a loop.
    # We could force a run if we had a shared event object.
    pass

def on_view_report(icon, item):
    """Open the latest report or dashboard in browser."""
    # Assuming reports are in "reports" folder or a dashboard URL
    # For MVP, let's open the website or a local file
    webbrowser.open("https://galt.ai/dashboard") 

def on_exit(icon, item):
    """Clean exit."""
    logging.info("Exiting via Tray...")
    icon.stop()
    os._exit(0) # Force kill all threads

def run_tray():
    """Starts the system tray icon. BLOCKING."""
    menu = (
        item('Escanear Ahora', on_scan),
        item('Ver Reporte', on_view_report),
        item('Salir', on_exit)
    )
    
    icon = pystray.Icon("GaltAI", load_icon(), "Galt.ai Sentinel", menu)
    
    logging.info("Tray Icon started.")
    icon.run()
