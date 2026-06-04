
import os
import ast
import re
import glob
import sys
from pathlib import Path

# --- CONFIGURATION ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. ZONE ALIVE (SACRED)
ENTRY_POINTS = [
    'main.py', 
    'runner.py', 
    'sentinel.py', 
    'dashboard_generator.py', 
    'tray_manager.py', 
    'onboarding.py', 
    'build_windows.py',
    'setup.py',
    'config.py',
    'bridge.py',
    'sensor_red.py'
]

SACRED_DIRS = [
    'tests',
    'mock'
]

EXCLUDE_DIRS = [
    '.git', 
    '.venv', 
    '.agent',
    '__pycache__', 
    '.pytest_cache', 
    'build', 
    'dist', 
    'installer',
    '.github'
]

PLUGIN_PATTERN = re.compile(r"(sensor_|plugin_).*\.py$")
ASSET_EXTENSIONS = {'.png', '.ico', '.jpg', '.svg', '.css', '.html', '.js'}

# Library mapping to import names (Basic)
REQ_MAPPING = {
    "Pillow": "PIL",
    "google-genai": "google.genai",
    "google-generativeai": "google.generativeai",
    "google-api-core": "google.api_core",
    "google-auth": "google.auth",
    "python-dotenv": "dotenv",
    "pywin32": "win32api", # Approximate
    "pytest-mock": "pytest_mock"
}

# --- HELPERS ---

def get_imports_from_file(filepath):
    """Parses a Python file and extracts imported module names."""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            root = ast.parse(f.read(), filename=filepath)
        
        for node in ast.walk(root):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        # print(f"Warning: Could not parse {filepath}: {e}")
        pass
    return imports

def resolve_import_to_file(import_name, current_file_path):
    """
    Attempts to map an import name (e.g., 'core.utils') to a physical file.
    Returns the absolute path if found, or None.
    """
    # 1. Check relative to root
    # e.g. import core -> core.py or core/__init__.py
    parts = import_name.split('.')
    potential_path = os.path.join(ROOT_DIR, *parts)
    
    # Check .py
    if os.path.isfile(potential_path + '.py'):
        return potential_path + '.py'
    
    # Check package (__init__.py)
    if os.path.isdir(potential_path) and os.path.isfile(os.path.join(potential_path, '__init__.py')):
        return os.path.join(potential_path, '__init__.py')

    return None

def scan_string_references(target_filename, search_dirs):
    """Checks if a filename is mentioned as a string in config files."""
    basename = os.path.basename(target_filename)
    name_no_ext = os.path.splitext(basename)[0]
    
    found = False
    
    for root, dirs, files in os.walk(ROOT_DIR):
        if any(d in root for d in EXCLUDE_DIRS):
            continue
            
        for file in files:
            if file == basename: continue # Don't find self
            
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if basename in content or name_no_ext in content:
                        return True
            except:
                pass
    return False

# --- MAIN LOGIC ---

def run_audit():
    print(f"🔎 Starting Galt Project Forensic Audit in: {ROOT_DIR}\n")
    
    # 1. Discover All Files
    all_py_files = set()
    all_assets = set()
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter Excludes
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            path = os.path.join(root, file)
            if file.endswith('.py'):
                all_py_files.add(path)
            elif os.path.splitext(file)[1] in ASSET_EXTENSIONS:
                all_assets.add(path)

    print(f"📂 Total Python Files: {len(all_py_files)}")
    print(f"🖼️  Total Assets: {len(all_assets)}")
    
    # 2. Build Reachability Graph
    reachable_files = set()
    queue = []
    
    # Seed queue with Entry Points
    for ep in ENTRY_POINTS:
        p = os.path.join(ROOT_DIR, ep)
        if os.path.exists(p):
            queue.append(p)
            reachable_files.add(p)
    

    # Add Sacred Dirs (Tests, Hooks)
    SACRED_DIRS.append('hooks')
    
    for sacred in SACRED_DIRS:
        for root, dirs, files in os.walk(os.path.join(ROOT_DIR, sacred)):
            for file in files:
                if file.endswith('.py'):
                    p = os.path.join(root, file)
                    reachable_files.add(p) 
                    queue.append(p)

    # Crawl
    while queue:
        current_file = queue.pop(0)
        imports = get_imports_from_file(current_file)
        for imp in imports:
            resolved = resolve_import_to_file(imp, current_file)
            if resolved and resolved not in reachable_files:
                reachable_files.add(resolved)
                queue.append(resolved)

    # 3. Identify Plugins (Sacred Exception)
    for f in all_py_files:
        if PLUGIN_PATTERN.search(os.path.basename(f)):
            reachable_files.add(f)

    # 4. Determine Dead Code
    dead_code = []
    suspect_code = []
    
    # Known Duplicates / Legacy overrides
    KNOWN_DEAD = {
        os.path.join(ROOT_DIR, 'reports', 'dashboard_generator.py'),
        os.path.join(ROOT_DIR, 'debug_narrator.py'),
        os.path.join(ROOT_DIR, 'list_models.py')
    }
    
    for f in all_py_files:
        if f == os.path.abspath(__file__): continue # Skip self
        
        if f in KNOWN_DEAD:
            dead_code.append(f)
            continue
            
        if f not in reachable_files:
            # Check for plugins legacy
            if 'net_scanner' in f or 'sys_scanner' in f:
                suspect_code.append(f)
                continue
                
            # Last Check: String references
            if scan_string_references(f, [ROOT_DIR]):
                suspect_code.append(f)
            else:
                dead_code.append(f)

    # 5. Asset Introspection
    dead_assets = []
    for asset in all_assets:
        asset_name = os.path.basename(asset)
        found = False
        # Search everywhere
        for root, dirs, files in os.walk(ROOT_DIR):
            if any(d in root for d in EXCLUDE_DIRS): continue
            for file in files:
                # Don't check the asset itself
                if os.path.abspath(os.path.join(root, file)) == asset: continue
                
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        if asset_name in f.read():
                            found = True
                            break
                except:
                    pass
            if found: break
        
        if not found:
            dead_assets.append(asset)

    # --- REPORTING ---
    
    print("\n" + "="*60)
    print("📊 INTROSPECTION REPORT")
    print("="*60)
    
    # Red: Brain Dead
    if dead_code or dead_assets:
        print("\n🔴 BRAIN DEAD (CONFIRMED TO DELETE)")
        for f in dead_code:
            print(f"   [CODE] {os.path.relpath(f, ROOT_DIR)}")
        for f in dead_assets:
            print(f"   [ASSET]  {os.path.relpath(f, ROOT_DIR)}")
    else:
        print("\n🔴 BRAIN DEAD: None found. Clean code!")

    # Orange: Suspects
    if suspect_code:
        print("\n🟠 SUSPECTS (REQUIRE REVIEW - Have string references)")
        for f in suspect_code:
            print(f"   {os.path.relpath(f, ROOT_DIR)}")

    # Yellow: Technical Debt (Imports vs Requirements)
    # Extract external imports from all reachable code
    all_external_imports = set()
    for f in reachable_files:
        imps = get_imports_from_file(f)
        for i in imps:
            # If not local, it's external
            if not resolve_import_to_file(i, f):
                all_external_imports.add(i)
                
    # Read requirements
    reqs = set()
    if os.path.exists(os.path.join(ROOT_DIR, 'requirements.txt')):
        with open(os.path.join(ROOT_DIR, 'requirements.txt'), 'r') as f:
            for line in f:
                line = line.strip().split(';')[0].split('==')[0].strip() # Clean
                if line:
                    reqs.add(line)
    
    unused_reqs = []
    for r in reqs:
        # Check mapping
        mapped  = REQ_MAPPING.get(r, r)
        # Check specific submodules for things like google-genai
        found = False
        if mapped in all_external_imports:
            found = True
        else:
            # Check prefixes (e.g. google in google.genai)
            for ext in all_external_imports:
                if ext.startswith(mapped) or (mapped.startswith("google") and ext.startswith("google")):
                   found = True
        
        if not found:
            unused_reqs.append(r)

    print("\n🟡 TECHNICAL DEBT (Requirements.txt vs Imports)")
    if unused_reqs:
        print("   Libraries in requirements.txt that do not seem to be imported:")
        for r in unused_reqs:
            print(f"   - {r}")
    else:
        print("   All dependencies seem to be in use.")

if __name__ == '__main__':
    run_audit()
