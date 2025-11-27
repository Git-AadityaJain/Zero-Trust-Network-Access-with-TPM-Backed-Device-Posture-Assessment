# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building ZTNA DPA executable
"""

block_cipher = None

# Find TPMSigner.exe relative to this file
import os
from pathlib import Path

spec_dir = Path(__file__).parent
project_root = spec_dir.parent
tpm_signer_path = project_root / "TPMSigner.exe"
dpa_tpm_signer = spec_dir / "TPMSigner.exe"

# Use TPMSigner.exe from dpa directory if available, otherwise from project root
tpm_binary = None
if dpa_tpm_signer.exists():
    tpm_binary = str(dpa_tpm_signer)
elif tpm_signer_path.exists():
    tpm_binary = str(tpm_signer_path)

a = Analysis(
    ['start_api_server.py'],
    pathex=[str(spec_dir)],
    binaries=[
        (tpm_binary, '.') if tpm_binary else None,
    ] if tpm_binary else [],
    datas=[
        # Include config directory if it exists
        # ('config', 'config'),
    ],
    hiddenimports=[
        'dpa.core.signing',
        'dpa.core.enrollment',
        'dpa.core.tpm',
        'dpa.core.posture_submission',
        'dpa.core.posture_scheduler',
        'dpa.config.settings',
        'dpa.modules.posture',
        'dpa.modules.fingerprint',
        'dpa.modules.os_info',
        'dpa.modules.antivirus',
        'dpa.modules.disk_encryption',
        'dpa.modules.firewall',
        'dpa.modules.screen_lock',
        'fastapi',
        'uvicorn',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pydantic',
        'requests',
        'cryptography',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'pandas',
        'numpy',
    ],
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
    name='ZTNA-DPA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for windowless service
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x64',
    codesign_identity=None,
    entitlements_file=None,
    # icon='dpa.ico'  # Uncomment and add icon file if available
)

