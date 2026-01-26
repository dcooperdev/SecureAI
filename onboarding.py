import tkinter as tk
from tkinter import simpledialog, messagebox
from config import save_api_key
import sys
import logging

from google import genai
from google.api_core.exceptions import GoogleAPIError

def validate_key(key):
    """Intenta una llamada mínima para verificar la API Key."""
    if not key or len(key) < 20: return False
    try:
        client = genai.Client(api_key=key)
        # Optimized: Fetch only the first item to verify auth, don't consume all pages
        next(iter(client.models.list(config={"page_size": 1})), None)
        return True
    except Exception as e:
        # Catching generic exception because auth errors can vary
        logging.warning(f"API Key validation failed: {e}")
        return False

def prompt_for_key(force_cli=False):
    """
    Solicita la API Key.
    Prioriza CLI si es interactivo, sino usa GUI.
    """
    logging.info("Iniciando Onboarding...")
    
    # 1. Modo CLI (Consola)
    if sys.stdin.isatty() or force_cli:
        print("\n" + "="*50)
        print("⚠️  CONFIGURACIÓN REQUERIDA DE GALT.AI  ⚠️")
        print("="*50)
        print("No se detectó una API Key válida de Google Gemini.")
        print("Para continuar, necesitas una llave de: https://aistudio.google.com/\n")
        
        while True:
            try:
                key = input("🔑 Ingresa tu API Key (o Ctrl+C para salir): ").strip()
                if not key: continue
                
                print("Validando llave...", end="\r")
                if validate_key(key):
                    print("✅ Llave válida! Guardando config...")
                    save_api_key(key)
                    return True
                else:
                    print("❌ Llave inválida o error de conexión. Intenta de nuevo.")
            except KeyboardInterrupt:
                print("\nOperación cancelada.")
                return False
            except EOFError:
                return False

    # 2. Modo GUI (Tkinter) - Fallback
    root = tk.Tk()
    root.withdraw() # Ocultar la ventana base fea
    
    # TRUCO: Hacer que la ventana sea invisible pero "TopMost"
    root.attributes('-topmost', True)
    root.lift()
    root.focus_force()
    
    while True:
        key = simpledialog.askstring(
            "Configuración Galt.ai", 
            "⚠️ CONFIGURACIÓN REQUERIDA ⚠️\n\nGoogle Gemini API Key no detectada o inválida.\nPara generar reportes con IA, ingresa tu llave aquí:",
            parent=root
        )
        
        if not key:
            root.destroy()
            return False
            
        clean_key = key.strip()
        if validate_key(clean_key):
            save_api_key(clean_key)
            root.destroy()
            return True
        else:
            retry = messagebox.askretrycancel("Error", "La API Key ingresada no es válida.\n¿Reintentar?", parent=root)
            if not retry:
                root.destroy()
                return False

def prompt_for_key_console():
    """Wrapper para forzar modo consola explícitamente."""
    return prompt_for_key(force_cli=True)

if __name__ == "__main__":
    prompt_for_key()
