import tkinter as tk
from tkinter import simpledialog, messagebox
from config import save_api_key
import sys

def prompt_for_key():
    """Lanza una ventana modal forzada en primer plano."""
    logging.info("Iniciando Onboarding GUI...")
    
    root = tk.Tk()
    root.withdraw() # Ocultar la ventana base fea
    
    # TRUCO: Hacer que la ventana sea invisible pero "TopMost" para que el dialog herede eso
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    
    # Usar el diálogo estándar
    key = simpledialog.askstring(
        "Configuración Galt.ai", 
        "⚠️ CONFIGURACIÓN REQUERIDA ⚠️\n\nGoogle Gemini API Key no detectada.\nPara generar reportes con IA, ingresa tu llave aquí:",
        parent=root
    )
    
    # Destruir la raíz de tkinter para liberar memoria
    root.destroy()
    
    if key and key.strip():
        clean_key = key.strip()
        save_api_key(clean_key)
        logging.info("API Key guardada correctamente.")
        return True
    else:
        logging.warning("El usuario canceló el ingreso de la API Key.")
        return False

if __name__ == "__main__":
    prompt_for_key()
