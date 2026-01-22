import time
import subprocess
import os
import json
import sys
from datetime import datetime

# Force UTF-8 on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

VAULT_FILE = "vault/security_state.json"

def get_current_score():
    if not os.path.exists(VAULT_FILE): return None
    try:
        with open(VAULT_FILE, "r") as f:
            return json.load(f).get("score")
    except: return None

def main():
    print("👁️  GALT.AI SENTINEL: VIGILANCIA ACTIVA")
    print("--------------------------------------")
    
    interval = 60 # Segundos
    if "--test" in sys.argv: interval = 10

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ [{timestamp}] Escaneando perímetro...")
            
            score_before = get_current_score()
            
            # EJECUCIÓN CON FLAG --auto (Modo Silencioso)
            # Esto evita que se abra el navegador a menos que haya cambios
            result = subprocess.run(
                [sys.executable, "runner.py", "--auto"], 
                capture_output=True, 
                text=True, 
                encoding='utf-8'
            )
            
            # Mostrar salida resumida o logs de error
            if result.returncode != 0:
                print("❌ Error en Runner:")
                print(result.stderr)
            else:
                # Filtrar salida para mostrar solo líneas clave
                for line in result.stdout.splitlines():
                    if "Score:" in line or "DRIFT" in line or "Modo Silencioso" in line:
                        print(f"   > {line.strip()}")

            score_after = get_current_score()
            
            # Notificaciones de Consola (Brindamos o Lloramos)
            if score_before is not None and score_after is not None:
                if score_after > score_before:
                    print(f"   🟢 MEJORA: {score_before} -> {score_after} 🥂")
                elif score_after < score_before:
                    print(f"   🔴 ALERTA: {score_before} -> {score_after} 😭")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Sentinel detenido.")

if __name__ == "__main__":
    main()