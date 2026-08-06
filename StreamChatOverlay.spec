# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Kumpulkan requests dan semua dependensinya secara paksa
requests_datas,     requests_binaries,     requests_hiddenimports     = collect_all('requests')
urllib3_datas,      urllib3_binaries,      urllib3_hiddenimports      = collect_all('urllib3')
certifi_datas,      certifi_binaries,      certifi_hiddenimports      = collect_all('certifi')
charset_datas,      charset_binaries,      charset_hiddenimports      = collect_all('charset_normalizer')
idna_datas,         idna_binaries,         idna_hiddenimports         = collect_all('idna')
pyttsx3_datas,      pyttsx3_binaries,      pyttsx3_hiddenimports      = collect_all('pyttsx3')
comtypes_datas,     comtypes_binaries,     comtypes_hiddenimports     = collect_all('comtypes')

all_datas = (
    requests_datas + urllib3_datas + certifi_datas +
    charset_datas + idna_datas + pyttsx3_datas + comtypes_datas
)
all_binaries = (
    requests_binaries + urllib3_binaries + certifi_binaries +
    charset_binaries + idna_binaries + pyttsx3_binaries + comtypes_binaries
)
all_hiddenimports = (
    requests_hiddenimports + urllib3_hiddenimports + certifi_hiddenimports +
    charset_hiddenimports + idna_hiddenimports + pyttsx3_hiddenimports +
    comtypes_hiddenimports + [
        'pyttsx3.drivers.sapi5',
        'win32com',
        'win32com.client',
    ]
)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StreamChatOverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StreamChatOverlay',
)
