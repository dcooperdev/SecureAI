import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import webbrowser
import os
import sys
import threading
import logging

def create_image():
    """Generates a dynamic Cyber Shield icon."""
    # Create a 64x64 image with transparent background
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    # Draw a shield shape (simplified as a rounded triangle/rectangle)
    # Colors: Galt.ai theme (Blue/Cyan)
    dc.rectangle((16, 16, 48, 48), fill=(0, 150, 255))
    dc.ellipse((20, 20, 44, 44), fill=(255, 255, 255))
    
    return image

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
    
    icon = pystray.Icon("GaltAI", create_image(), "Galt.ai Sentinel", menu)
    
    logging.info("Tray Icon started.")
    icon.run()
