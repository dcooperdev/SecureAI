# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('sensor_*.py', '.'), ('runner.py', '.'), ('sentinel.py', '.'), ('config.py', '.'), ('.env.example', '.'), ('app.ico', '.'), ('logo.png', '.'), ('core', 'core'), ('reports', 'reports')],
    hiddenimports=['dotenv', 'google', 'google.genai', 'google.api_core', 'google.auth', 'google.ai', 'grpc', 'google', 'google.generativeai', 'google.generativeai.types', 'google.generativeai.notebook', 'requests', 'idna', 'urllib3', 'certifi'],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GaltAI_Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.ico'],
)
