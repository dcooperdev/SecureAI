from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('google.api_core')
