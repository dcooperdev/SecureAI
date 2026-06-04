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
    """Loads app.ico (Windows) or logo.png (Others) from the correct path."""
    # PyInstaller support (temporary route _MEI)
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    
    icon_path_win = os.path.join(base_path, "app.ico")
    icon_path_png = os.path.join(base_path, "logo.png")
    
    if os.path.exists(icon_path_win):
        return Image.open(icon_path_win)
    elif os.path.exists(icon_path_png):
        return Image.open(icon_path_png)
    else:
        # Fallback: Generate red square if assets fail
        return Image.new('RGB', (64, 64), color = 'red')

from galt.core.config import get_storage_path

def run_manual_scan(icon, item):
    """Runs the scan in a separate thread with notifications."""
    # 1. Immediate Feedback
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_path, "app.ico")
    
    try:
        notification.notify(
            title='Galt.ai',
            message='🔄 Starting security scan...',
            app_name='Galt.ai',
            app_icon=icon_path if os.path.exists(icon_path) else None,
            timeout=3
        )
    except Exception as e:
        logging.error(f"Error notifying start: {e}")
    
    # 2. Wrapper function for the thread
    def _scan_thread():
        try:
            # This will run the scan, generate the HTML, and launch the FINISH notification
            runner.run_security_flow() 
        except Exception as e:
            logging.error(f"Error in manual scan: {e}")

    # 3. Launch Thread
    threading.Thread(target=_scan_thread, daemon=True).start()

def open_dashboard(icon=None, item=None):
    """
    Opens the local dashboard in the browser. It first looks for the report file
    in the storage directory and, if it does not exist, opens the local viewer that loads
    the data from `vault/reports/galt_loader.js`.
    """
    try:
        report_dir = get_storage_path("reports")
        dashboard_path = os.path.join(report_dir, "dashboard.html")
        debug_console_path = os.path.join(report_dir, "debug_console.html")
        package_viewer = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "viewer.html")

        if os.path.exists(dashboard_path):
            latest_report = dashboard_path
        elif os.path.exists(debug_console_path):
            latest_report = debug_console_path
        elif os.path.exists(package_viewer):
            latest_report = package_viewer
        else:
            if os.path.isdir(report_dir):
                files = [f for f in os.listdir(report_dir) if f.endswith('.html')]
                if files:
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(report_dir, x)), reverse=True)
                    latest_report = os.path.join(report_dir, files[0])
                else:
                    logging.warning("No dashboard reports found.")
                    return
            else:
                logging.warning("Reports directory does not exist: %s", report_dir)
                return

        logging.info(f"Opening Dashboard: {latest_report}")
        from pathlib import Path
        file_url = Path(latest_report).as_uri()
        webbrowser.open(file_url)
    except Exception as e:
        logging.error(f"Error opening dashboard: {e}")


def on_action(icon, item):
    """Generic handler for the menu."""
    if str(item) == "Open Web Panel":
        open_dashboard()
    elif str(item) == "Scan Now":
        run_manual_scan(icon, item)
    elif str(item) == "Exit":
        icon.stop()
        os._exit(0)

def run_tray():
    """Starts the system tray icon. BLOCKING."""
    image = load_icon()
    
    # MENU DEFINITION
    menu = pystray.Menu(
        # default=True enables double click action (Bold in menu)
        pystray.MenuItem("Open Web Panel", on_action, default=True),
        pystray.MenuItem("Scan Now", on_action),
        pystray.MenuItem("Exit", on_action)
    )

    icon = pystray.Icon("GaltAI", image, "Galt.ai Security", menu)
    logging.info("Tray Icon started.")
    icon.run()
