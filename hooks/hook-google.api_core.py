from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hiddenimports = collect_all('google.api_core')
datas += copy_metadata('google-api-core')
