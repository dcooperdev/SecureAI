import time
import subprocess
import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from config import get_storage_path

# Force UTF-8 on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()
vault_dir = get_storage_path("vault")
VAULT_FILE = os.path.join(vault_dir, "security_state.json")

# --- CONFIGURACIÓN COMERCIAL ---
# En el futuro, esto vendrá de Firebase Remote Config
DEFAULT_TIER = "PRO" # Cambiar a 'FREE' para probar la restricción
CLIENT_ID = os.getenv("GALT_CLIENT_ID", "UNKNOWN_CLIENT")

def get_current_score():
    if not os.path.exists(VAULT_FILE): return None
    try:
        with open(VAULT_FILE, "r") as f:
            return json.load(f).get("score")
    except: return None

def check_remote_config(client_id):
    """
    Simula la consulta a la nube (Firebase) para obtener el plan del usuario.
    Retorna: (intervalo_segundos, nombre_plan, mensaje_estado)
    """
    # TODO: Aquí irá: response = requests.get(f"https://api.galt.ai/config/{client_id}")
    
    # Lógica de Simulación "Pionera"
    tier = os.getenv("SUBSCRIPTION_TIER", DEFAULT_TIER).upper()
    
    if tier == "PRO" or tier == "PIONEER":
        return 3600, tier, "🟢 PROTECCIÓN ACTIVA (Alta Frecuencia)"
    elif tier == "FREE":
        return 86400, tier, "🟡 PROTECCIÓN BÁSICA (1 vez al día)"
    elif tier == "EXPIRED":
        return 0, tier, "🔴 SUSCRIPCIÓN VENCIDA. Escaneo detenido."
    else:
        # Fallback seguro
        return 86400, "UNKNOWN", "⚪ MODO SEGURO (Default)"

def main():
    print(f"👁️  GALT.AI SENTINEL: VIGILANCIA ACTIVA")
    print(f"    Cliente ID: {CLIENT_ID}")
    print("--------------------------------------")
    
    # Modo Test: Sobrescribe todo para desarrollo rápido
    if "--test" in sys.argv: 
        print("   [TEST MODE] Intervalo forzado: 10 segundos")
        interval = 10
        plan_name = "TEST_DEV"
        status_msg = "🧪 MODO PRUEBAS"
    else:
        # Primera sincronización
        interval, plan_name, status_msg = check_remote_config(CLIENT_ID)

    print(f"   PLAN DETECTADO: {plan_name}")
    print(f"   ESTADO: {status_msg}")
    print(f"   FRECUENCIA: {interval} segundos")
    print("--------------------------------------\n")

    if interval == 0:
        print("❌ El servicio está detenido por falta de licencia activa.")
        print("   Contacta a soporte o renueva tu suscripción.")
        return

    try:
        while True:
            # 1. Chequeo de Licencia antes de cada ronda (Remote Sync)
            # Esto permite "apagar" o "mejorar" el servicio en caliente sin reiniciar
            if "--test" not in sys.argv:
                new_interval, new_plan, _ = check_remote_config(CLIENT_ID)
                if new_interval != interval:
                    print(f"\n🔄 ACTUALIZACIÓN REMOTA: Cambio a plan {new_plan}. Nuevo intervalo: {new_interval}s")
                    interval = new_interval
                
                if interval == 0:
                    print("\n⛔ SUSCRIPCIÓN FINALIZADA. Deteniendo Sentinel.")
                    break

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n⏰ [{timestamp}] Escaneando perímetro ({plan_name})...")
            
            score_before = get_current_score()
            
            # 2. Ejecución del Agente
            # Llamamos al mismo ejecutable en modo "runner"
            cmd = [sys.executable, "runner"]
            
            # Pasar flag --auto si corresponde
            if "--auto" in sys.argv or interval > 60: 
                cmd.append("--auto")

            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print("❌ Error en Runner:")
                print(result.stderr)
            else:
                for line in result.stdout.splitlines():
                    if any(x in line for x in ["Score:", "DRIFT", "Modo Silencioso", "REPORTE", "DASHBOARD", "Abriendo"]):
                        print(f"   > {line.strip()}")

            score_after = get_current_score()
            
            if score_before is not None and score_after is not None:
                if score_after > score_before:
                    print(f"   🟢 MEJORA: {score_before} -> {score_after} 🥂")
                elif score_after < score_before:
                    print(f"   🔴 ALERTA: {score_before} -> {score_after} 😭")
            
            # 3. Dormir (Smart Sleep)
            # Imprimimos el próximo check para ansiedad del usuario
            next_run = round(interval / 60, 1)
            print(f"💤 Durmiendo... Próximo escaneo en {next_run} minutos.")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Sentinel detenido.")

if __name__ == "__main__":
    main()