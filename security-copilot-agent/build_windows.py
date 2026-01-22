import PyInstaller.__main__
import os
import shutil

# Limpiar builds anteriores
if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

# Definir separador de datos según OS (Windows usa ;)
sep = ";" if os.name == 'nt' else ":"

# Configuración de PyInstaller
args = [
    'sentinel.py',                      # Script principal (El Vigilante)
    '--name=GaltAI_Agent',              # Nombre del EXE
    '--onefile',                        # Un solo archivo gigante
    '--noconfirm',                      # No preguntar si sobrescribe
    '--clean',                          # Limpiar caché
    # Incluir los sensores y archivos clave
    f'--add-data=sensor_procesos.py{sep}.',
    f'--add-data=sensor_red.py{sep}.',
    f'--add-data=sensor_sistema.py{sep}.',
    f'--add-data=sensor_vulnerabilidades.py{sep}.',
    f'--add-data=sensor_network_discovery.py{sep}.',
    f'--add-data=runner.py{sep}.',
    # Incluir .env.example si existe
    f'--add-data=.env.example{sep}.',
    # '--windowed',                     # DESCOMENTAR PARA QUE NO SALGA LA CONSOLA NEGRA (PROD)
    '--console',                        # MANTENER PARA DEBUG (BETA)
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
