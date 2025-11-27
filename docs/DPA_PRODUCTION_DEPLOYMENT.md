# DPA Production Deployment Guide

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Client Device │         │  Backend Server  │         │  Web Frontend   │
│                 │         │                  │         │  (Browser)      │
│  ┌───────────┐  │ HTTPS   │  ┌────────────┐  │  HTTPS  │  ┌───────────┐  │
│  │ DPA.exe   │◄─┼─────────┼─►│  FastAPI   │◄─┼─────────┼─►│  React    │  │
│  │ (Admin)   │  │         │  │  Backend   │  │         │  │  App      │  │
│  └───────────┘  │         │  └────────────┘  │         │  └───────────┘  │
│       │         │         │                  │         │        │         │
│       │ TPM     │         │                  │         │        │         │
│       ▼         │         │                  │         │        │         │
│  ┌───────────┐  │         │                  │         │        │         │
│  │ TPMSigner │  │         │                  │         │        │         │
│  │   .exe    │  │         │                  │         │        │         │
│  └───────────┘  │         │                  │         │        │         │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Key Components

1. **DPA.exe** - Main executable running on client machine with admin privileges
2. **TPMSigner.exe** - TPM signing utility (embedded or separate)
3. **Backend Server** - Central server handling authentication and authorization
4. **Web Frontend** - Browser-based UI for users

## Deployment Strategy

### Option 1: Standalone Executable (Recommended)

Package DPA as a single executable using PyInstaller or similar.

#### Advantages:
- ✅ No Python installation required on client machines
- ✅ Single file deployment
- ✅ Easy distribution via MSI/installer
- ✅ Can run as Windows Service

#### Implementation:

**1. Create PyInstaller Spec File** (`dpa/dpa.spec`):

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['start_api_server.py'],
    pathex=[],
    binaries=[
        ('TPMSigner.exe', '.'),
    ],
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=[
        'dpa.core.signing',
        'dpa.core.enrollment',
        'dpa.core.tpm',
        'dpa.config.settings',
        'fastapi',
        'uvicorn',
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
    icon='dpa.ico'  # Optional: add icon file
)
```

**2. Build Script** (`dpa/build_exe.bat`):

```batch
@echo off
echo Building ZTNA DPA Executable...
echo.

REM Check if PyInstaller is installed
python -m pip install pyinstaller

REM Build executable
pyinstaller dpa.spec --clean --noconfirm

REM Copy to output directory
if not exist "dist\release" mkdir "dist\release"
copy "dist\ZTNA-DPA.exe" "dist\release\"
copy "TPMSigner.exe" "dist\release\"

echo.
echo Build complete! Executable: dist\release\ZTNA-DPA.exe
pause
```

**3. Build Command:**

```powershell
cd dpa
python -m pip install pyinstaller
pyinstaller dpa.spec --clean --noconfirm
```

### Option 2: Windows Service

Run DPA as a Windows Service for automatic startup and background operation.

**Service Implementation** (`dpa/service_wrapper.py`):

```python
import win32serviceutil
import win32service
import servicemanager
import socket
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dpa.api.server import start_server

class ZTNADPAService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZTNA-DPA"
    _svc_display_name_ = "ZTNA Device Posture Agent"
    _svc_description_ = "Zero Trust Network Access Device Posture Agent Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        try:
            start_server(host="127.0.0.1", port=8081, log_level="info")
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ZTNADPAService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ZTNADPAService)
```

**Install Service:**

```powershell
# Install
python service_wrapper.py install

# Start
python service_wrapper.py start

# Stop
python service_wrapper.py stop

# Remove
python service_wrapper.py remove
```

## Configuration Management

### 1. Configuration File Location

DPA stores configuration in: `C:\ProgramData\ZTNA\config.json`

```json
{
  "backend_url": "https://your-backend-server.com/api",
  "tpm_enabled": true,
  "reporting_interval": 300,
  "device_name": "COMPUTER-NAME"
}
```

### 2. Configuration Methods (Priority Order)

1. **Command Line Arguments** (highest priority)
2. **Environment Variables**
3. **Configuration File**
4. **Default Values**

### 3. Initial Configuration

**During Installation:**

```powershell
# Create config directory
New-Item -ItemType Directory -Force -Path "C:\ProgramData\ZTNA"

# Set backend URL
$config = @{
    backend_url = "https://your-backend-server.com/api"
    tpm_enabled = $true
    reporting_interval = 300
} | ConvertTo-Json

$config | Out-File -FilePath "C:\ProgramData\ZTNA\config.json" -Encoding UTF8
```

## Security Considerations

### 1. DPA API Server Security

**Current Implementation:**
- Runs on `127.0.0.1:8081` (localhost only)
- Only accepts connections from localhost
- ✅ **This is correct for production**

**DO NOT expose DPA API to network!** It should only be accessible from:
- `localhost` / `127.0.0.1`
- The same machine running the browser

### 2. Frontend-DPA Communication

**Challenge:** Browser (frontend) needs to communicate with DPA API on client machine.

**Solution Options:**

#### Option A: Localhost Only (Recommended)
- Frontend accessed via `http://localhost:3000` or local network
- DPA API on `http://localhost:8081`
- ✅ Simple, secure
- ❌ Requires local network access

#### Option B: Browser Extension
- Create browser extension that communicates with local DPA API
- Extension has privileged access to localhost
- ✅ Works with remote frontend
- ❌ Requires extension development

#### Option C: Desktop App Wrapper
- Package frontend as Electron/CEF app
- Can directly access localhost APIs
- ✅ Full control
- ❌ More complex deployment

#### Option D: Backend Proxy (Not Recommended)
- Backend proxies requests to DPA
- ❌ Security risk (exposes DPA to network)
- ❌ Complex networking

### 3. TPM Key Security

- TPM keys are hardware-bound (cannot be extracted)
- Keys stored in TPM, not in files
- ✅ Secure by design

### 4. Network Security

- All backend communication over HTTPS
- Verify SSL certificates
- Use certificate pinning if needed

## Installation Package

### MSI Installer Structure

```
ZTNA-DPA-Installer/
├── ZTNA-DPA.exe          # Main executable
├── TPMSigner.exe         # TPM signing utility
├── config.json.template  # Configuration template
├── install.ps1           # Installation script
└── uninstall.ps1         # Uninstallation script
```

### Installation Script (`install.ps1`):

```powershell
# Run as Administrator
param(
    [Parameter(Mandatory=$true)]
    [string]$BackendUrl
)

# Create installation directory
$installDir = "C:\Program Files\ZTNA\DPA"
New-Item -ItemType Directory -Force -Path $installDir

# Copy files
Copy-Item "ZTNA-DPA.exe" -Destination $installDir
Copy-Item "TPMSigner.exe" -Destination $installDir

# Create config
$configDir = "C:\ProgramData\ZTNA"
New-Item -ItemType Directory -Force -Path $configDir

$config = @{
    backend_url = $BackendUrl
    tpm_enabled = $true
    reporting_interval = 300
} | ConvertTo-Json

$config | Out-File -FilePath "$configDir\config.json" -Encoding UTF8

# Install as Windows Service (optional)
# & "$installDir\ZTNA-DPA.exe" install

# Start service
# & "$installDir\ZTNA-DPA.exe" start

Write-Host "Installation complete!"
```

## Deployment Checklist

### Pre-Deployment

- [ ] Build executable with PyInstaller
- [ ] Test executable on clean Windows machine
- [ ] Verify TPM functionality
- [ ] Test backend connectivity
- [ ] Create installation package
- [ ] Prepare configuration templates

### Deployment

- [ ] Distribute executable to client machines
- [ ] Install with admin privileges
- [ ] Configure backend URL
- [ ] Enroll device with enrollment code
- [ ] Verify DPA API is running (`http://localhost:8081/health`)
- [ ] Test challenge signing
- [ ] Verify posture reporting

### Post-Deployment

- [ ] Monitor DPA logs
- [ ] Verify device enrollment in backend
- [ ] Test resource access from frontend
- [ ] Monitor for errors

## Troubleshooting

### DPA Won't Start

**Check:**
1. Running with admin privileges?
2. Port 8081 available?
3. TPM available and initialized?
4. Configuration file valid?

**Logs Location:**
- Windows Event Viewer (if running as service)
- Console output (if running manually)
- `C:\ProgramData\ZTNA\logs\` (if logging to file)

### Can't Connect to Backend

**Check:**
1. Backend URL correct in config?
2. Network connectivity?
3. Firewall allows outbound HTTPS?
4. SSL certificate valid?

### TPM Not Available

**Check:**
1. TPM enabled in BIOS?
2. TPM initialized?
3. TPMSigner.exe accessible?
4. Running with admin privileges?

## Best Practices

1. **Always run DPA with admin privileges** (required for TPM access)
2. **Use HTTPS for all backend communication**
3. **Keep DPA API on localhost only** (never expose to network)
4. **Monitor logs regularly**
5. **Update DPA executable when backend API changes**
6. **Use certificate pinning for production**
7. **Implement automatic updates** (optional)

## Example Deployment Flow

```powershell
# 1. Build executable
cd dpa
python build_exe.bat

# 2. Create installation package
# Copy dist/release/* to installer package

# 3. On client machine (as admin):
.\install.ps1 -BackendUrl "https://ztna-server.company.com/api"

# 4. Enroll device
.\ZTNA-DPA.exe enroll --code ENROLLMENT_CODE

# 5. Verify
Invoke-WebRequest -Uri http://localhost:8081/health
```

## Next Steps

1. Create PyInstaller spec file
2. Build executable
3. Test on clean machine
4. Create installer package
5. Deploy to test machines
6. Monitor and iterate

