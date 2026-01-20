from setuptools import setup
from Cython.Build import cythonize
import os
import glob

# Identify plugin files to compile
plugin_pattern = "plugins/*.py"
files = glob.glob(plugin_pattern)
# Exclude __init__.py
plugin_files = [f for f in files if not f.endswith("__init__.py")]

setup(
    name="security_copilot_agent",
    ext_modules=cythonize(plugin_files, compiler_directives={'language_level': "3"}),
    zip_safe=False,
)
