import PyInstaller.__main__
import os
import shutil
import sys

# Force UTF-8 for Windows Console
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError: pass

if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")

sep = ";" if os.name == 'nt' else ":"

args = [
    'main.py',                              # <--- NUEVO MAIN
    '--name=GaltAI_Agent',
    '--onefile',
    '--noconfirm',
    '--clean',
    '--hidden-import=dotenv',
    '--hidden-import=google',
    '--hidden-import=google.genai',
    '--hidden-import=google.api_core',
    '--hidden-import=google.auth',
    '--hidden-import=google.ai',
    '--hidden-import=grpc',               # Usually needed by google.api_core
    # Incluimos todo el código fuente como data por seguridad
    f'--add-data=sensor_*.py{sep}.',
    f'--add-data=runner.py{sep}.',
    f'--add-data=sentinel.py{sep}.',
    f'--add-data=config.py{sep}.',
    f'--add-data=.env.example{sep}.',
    '--console',
]

if os.path.exists("app.ico"): args.append('--icon=app.ico')

print("🚀 Compilando Galt.ai Hybrid Monolith...", file=sys.stderr)
PyInstaller.__main__.run(args)
print("✅ Compilación exitosa.", file=sys.stderr)