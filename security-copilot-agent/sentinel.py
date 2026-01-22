import time
import subprocess
import os
import json
import sys

# Force UTF-8 encoding for stdout on Windows to handle emojis
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
from datetime import datetime

VAULT_FILE = "vault/security_state.json"

def get_current_score():
    if not os.path.exists(VAULT_FILE):
        return None
    try:
        with open(VAULT_FILE, "r") as f:
            data = json.load(f)
            return data.get("score")
    except:
        return None

def main():
    print("👁️  GALT.AI SENTINEL: INICIANDO VIGILANCIA AUTÓNOMA")
    print("--------------------------------------------------")
    
    interval = 60 # 60 minutes
    
    # Check if testing mode
    if "--test" in sys.argv:
        interval = 5 
        print("   [TEST MODE] Intervalo reducido a 5s.")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n⏰ [{timestamp}] Ejecutando orquestador de seguridad...")
            
            score_before = get_current_score()
            
            # Execute Runner
            result = subprocess.run([sys.executable, "runner.py", "--auto"], capture_output=True, text=True, encoding='utf-8')
            
            # Print Runner Output (filtered or full)
            print(result.stdout)
            if result.stderr:
                print(f"ERROR LOG:\n{result.stderr}")
                
            score_after = get_current_score()
            
            # Comparative Logic (Green/Red)
            if score_before is not None and score_after is not None:
                if score_after > score_before:
                    print(f"\n🟢 ¡MEJORA DETECTADA! La postura de seguridad ha subido de {score_before} a {score_after}.")
                    print("   🥂 ¡Brindamos! Se han mitigado vulnerabilidades.")
                elif score_after < score_before:
                    print(f"\n🔴 ¡ALERTA DE RIESGO! La postura ha bajado de {score_before} a {score_after}.")
                    print("   😭 ¡Lloramos! Nuevas amenazas detectadas.")
                else:
                    # If runner output contains "Postura estable", confirmed no change.
                    pass
            elif score_before is None and score_after is not None:
                print(f"\n🔵 LÍNEA BASE ESTABLECIDA. Score inicial: {score_after}/100")
            
            print(f"💤 Durmiendo {interval} segundos...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Sentinel detenido por el usuario.")

if __name__ == "__main__":
    main()
