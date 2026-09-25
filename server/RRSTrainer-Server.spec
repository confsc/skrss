# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
server_dir = os.path.abspath(os.getcwd())
logic_dir = os.path.join(server_dir, 'logic')
ui_dir = os.path.join(server_dir, 'ui')
shared_dir = os.path.join(project_root, 'shared')
client_data_dir = os.path.join(project_root, 'client', 'data')

pathex = [
    logic_dir,
    ui_dir,
    shared_dir,
    server_dir,
]

datas = [
    (shared_dir, 'shared'),
    (client_data_dir, 'data'),
]

hiddenimports = [
    'config',
    'server_api',
    'database',
    'broadcast',
    'main_window',
    'json',
    'sqlite3',
    'datetime',
    'threading',
    'socket',
    'time',
    'random',
    'flask',
    'werkzeug',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',
    'blinker',
]

hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('werkzeug')
hiddenimports += collect_submodules('jinja2')
hiddenimports += collect_submodules('markupsafe')

a = Analysis(
    ['main.py'],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='RRSTrainer-Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
