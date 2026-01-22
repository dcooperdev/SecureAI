import PyInstaller.__main__
import os
import shutil
import sys

# --- FIX CRÍTICO: FORZAR UTF-8 EN WINDOWS ---
# Esto evita el error "UnicodeEncodeError: charmap codec..."
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
# --------------------------------------------

# Limpiar builds anteriores
if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

# Definir separador de datos según OS (Windows usa ;)
sep = ";" if os.name == 'nt' else ":"

# Configuración de PyInstaller
args = [
    'sentinel.py',                          # Script principal
    '--name=GaltAI_Agent',                  # Nombre del EXE
    '--onefile',                            # Un solo archivo
    '--noconfirm',                          # No preguntar
    '--clean',                              # Limpiar caché
    # Incluir sensores
    f'--add-data=sensor_procesos.py{sep}.',
    f'--add-data=sensor_red.py{sep}.',
    f'--add-data=sensor_sistema.py{sep}.',
    f'--add-data=sensor_vulnerabilidades.py{sep}.',
    f'--add-data=sensor_network_discovery.py{sep}.',
    f'--add-data=runner.py{sep}.',
    # Incluir .env.example (¡Asegurate de haberlo creado!)
    f'--add-data=.env.example{sep}.',
    '--console',
]

# Agregar icono si existe
if os.path.exists("app.ico"):
    print("✨ Icono encontrado: app.ico")
    args.append('--icon=app.ico')
else:
    print("ℹ️  No se encontró app.ico, usando icono por defecto.")

# Ejecutar PyInstaller
print("🚀 Iniciando compilación de Galt.ai Agent...")
PyInstaller.__main__.run(args)

print("✅ Compilación exitosa. El ejecutable está en /dist/GaltAI_Agent.exe")