import tkinter as tk
from tkinter import simpledialog, messagebox
from config import save_api_key
import sys

def prompt_for_key():
    """Lanza una ventana nativa pidiendo la API Key."""
    # Evitar ventana principal vacía
    root = tk.Tk()
    root.withdraw() 
    
    # Asegurar que la ventana aparezca al frente
    root.attributes('-topmost', True)
    
    key = simpledialog.askstring(
        "Galt.ai Setup", 
        "Bienvenido a Galt.ai Security.\n\nPara generar reportes con IA, necesitamos tu Google Gemini API Key.\nPor favor, ingrésala aquí:",
        parent=root
    )
    
    if key:
        save_api_key(key.strip())
        messagebox.showinfo("Galt.ai", "Configuración guardada exitosamente.")
        root.destroy()
        return True
    else:
        messagebox.showwarning("Galt.ai", "Sin API Key, los reportes serán limitados (sin análisis IA).")
        root.destroy()
        return False

if __name__ == "__main__":
    prompt_for_key()
