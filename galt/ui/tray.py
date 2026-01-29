import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import webbrowser
import os
import sys
# runner is imported but likely used as module. 
# tray.py uses runner.run_security_flow()
from galt.engine import orchestrator as runner
from plyer import notification
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

from galt.core.config import get_storage_path

def run_manual_scan(icon, item):
    """Ejecuta el escaneo en un hilo separado con notificaciones."""
    # 1. Feedback Inmediato
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_path, "app.ico")
    
    try:
        notification.notify(
            title='Galt.ai',
            message='🔄 Iniciando escaneo de seguridad...',
            app_name='Galt.ai',
            app_icon=icon_path if os.path.exists(icon_path) else None,
            timeout=3
        )
    except Exception as e:
        logging.error(f"Error notificando inicio: {e}")
    
    # 2. Función wrapper para el thread
    def _scan_thread():
        try:
            # Esto ejecutará el escaneo, generará el HTML y lanzará la notificación de FIN
            runner.run_security_flow() 
        except Exception as e:
            logging.error(f"Error en escaneo manual: {e}")

    # 3. Lanzar Thread
    threading.Thread(target=_scan_thread, daemon=True).start()

def open_dashboard(icon=None, item=None):
    """
    Abre el dashboard.html local usando el protocolo file:// absoluto.
    Evita abrir dominios de internet por error.
    """
    try:
        # 1. Construir ruta absoluta al archivo
        report_dir = get_storage_path("reports")
        dashboard_path = os.path.join(report_dir, "dashboard.html")
        
        # Check if dashboard.html exists, otherwise fallback to latest scan
        if os.path.exists(dashboard_path):
            latest_report = dashboard_path
        else:
            files = [f for f in os.listdir(report_dir) if f.endswith('.html')]
            if not files:
                logging.warning("No dashboard reports found.")
                return
            files.sort(key=lambda x: os.path.getmtime(os.path.join(report_dir, x)), reverse=True)
            latest_report = os.path.join(report_dir, files[0])
            
        logging.info(f"Abriendo Dashboard: {latest_report}")
        
        # 3. Convertir a URL de archivo (URI)
        from pathlib import Path
        file_url = Path(latest_report).as_uri()
        
        webbrowser.open(file_url)
        
    except Exception as e:
        logging.error(f"Error abriendo dashboard: {e}")

def on_action(icon, item):
    """Manejador genérico para el menú."""
    if str(item) == "Abrir Panel Web":
        open_dashboard()
    elif str(item) == "Escanear Ahora":
        run_manual_scan(icon, item)
    elif str(item) == "Salir":
        icon.stop()
        os._exit(0)

def run_tray():
    """Starts the system tray icon. BLOCKING."""
    image = load_icon()
    
    # DEFINICIÓN DEL MENÚ
    menu = pystray.Menu(
        # default=True habilita la acción por DOBLE CLICK (Bold en el menú)
        pystray.MenuItem("Abrir Panel Web", on_action, default=True),
        pystray.MenuItem("Escanear Ahora", on_action),
        pystray.MenuItem("Salir", on_action)
    )

    icon = pystray.Icon("GaltAI", image, "Galt.ai Security", menu)
    logging.info("Tray Icon started.")
    icon.run()
