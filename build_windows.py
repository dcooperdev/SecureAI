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
    'main.py',                              # <--- NEW MAIN
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
    # FIX: Google Namespace Packages (Required for CI/CD builds)
    '--hidden-import=google',
    '--hidden-import=google.generativeai',
    '--hidden-import=google.generativeai.types',
    '--hidden-import=google.generativeai.notebook',
    # Common missing networking deps in CI
    '--hidden-import=requests',
    '--hidden-import=idna',
    '--hidden-import=urllib3',
    '--hidden-import=certifi',
    '--additional-hooks-dir=hooks',
    '--runtime-hook=runtime_hook.py',     # <--- FORCE RUNTIME IMPORT
    # Include all source code as data for security
    f'--add-data=.env.example{sep}.',
    f'--add-data=app.ico{sep}.',
    f'--add-data=logo.png{sep}.',
    f'--add-data=galt{sep}galt',
    '--console',
]

if os.path.exists("app.ico"): args.append('--icon=app.ico')

print("🚀 Building Galt.ai Hybrid Monolith...", file=sys.stderr)
PyInstaller.__main__.run(args)
print("✅ Compilation successful.", file=sys.stderr)