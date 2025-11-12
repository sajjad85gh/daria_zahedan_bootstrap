# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Executable name
exe_name = 'DariaBond1Flash'

a = Analysis(
    ['daria_bond_flash.py'],  # Your main script name
    pathex=[],
    binaries=[],
    datas=[
        ('rom_checksums.txt', '.'),  # Include checksums file
    ],
    hiddenimports=[
        'tqdm',
        'hashlib',
        'pathlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
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
    icon=None,
)