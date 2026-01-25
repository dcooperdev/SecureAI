from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hiddenimports = collect_all('google.genai')
datas += copy_metadata('google-genai')
