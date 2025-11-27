# DPA Remote Device Enrollment Setup

## Issue: Module Import Error

If you get this error:
```
ModuleNotFoundError: _path_ attribute not found on 'dpa.cli.enroll_cli' while trying to find 'dpa.cli.enroll_cli.py'
```

**Solution**: Remove the `.py` extension when using `python -m`

## Correct Command

### ❌ Wrong:
```bash
python -m dpa.cli.enroll_cli.py --backend-url https://... --enrollment-code ...
```

### ✅ Correct:
```bash
python -m dpa.cli.enroll_cli --backend-url https://... --enrollment-code ...
```

## Alternative: Run Directly

You can also run the script directly:
```bash
python dpa/cli/enroll_cli.py --backend-url https://... --enrollment-code ...
```

## Setup Required on Remote Device

### 1. Install Python Dependencies

```bash
# Navigate to project directory
cd ztna-project

# Activate virtual environment (if using one)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r dpa/requirements.txt
```

### 2. Install .NET Runtime (for TPMSigner.exe)

**Windows:**
```powershell
# Install .NET 8.0 Runtime
winget install Microsoft.DotNet.Runtime.8
```

Or download from: https://dotnet.microsoft.com/download/dotnet/8.0

### 3. Verify TPMSigner.exe

Ensure `TPMSigner.exe` is in the `dpa/` directory:
```bash
# Check if file exists
dir dpa\TPMSigner.exe  # Windows
ls dpa/TPMSigner.exe   # Linux/Mac
```

If missing, copy it from `TPMSigner/bin/Release/net8.0-windows/win-x64/publish/TPMSigner.exe`

### 4. Run Enrollment

```bash
# From project root directory
python -m dpa.cli.enroll_cli --backend-url https://609b9c24fbd6.ngrok-free.app --enrollment-code txqtmKJkuQ656BbPRefvGPHMaqjjdkez
```

## Complete Setup Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated (optional but recommended)
- [ ] DPA dependencies installed (`pip install -r dpa/requirements.txt`)
- [ ] .NET 8.0 Runtime installed (for TPMSigner.exe)
- [ ] TPMSigner.exe present in `dpa/` directory
- [ ] Running from project root directory
- [ ] Backend URL is accessible (test with browser/curl)

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'dpa'"

**Solution**: Make sure you're running from the project root directory:
```bash
# Should be in: ztna-project/
# Not in: ztna-project/dpa/
```

### Issue: "TPMSigner.exe not found"

**Solution**: 
1. Build TPMSigner: `cd TPMSigner && build.bat` (Windows)
2. Copy to dpa directory: `copy TPMSigner\bin\Release\net8.0-windows\win-x64\publish\TPMSigner.exe dpa\`

### Issue: ".NET Runtime not found"

**Solution**: Install .NET 8.0 Runtime:
```powershell
winget install Microsoft.DotNet.Runtime.8
```

### Issue: "Cannot connect to backend"

**Solution**:
1. Verify backend URL is accessible: `curl https://609b9c24fbd6.ngrok-free.app/api/health`
2. Check if ngrok tunnel is active
3. Verify backend is running
4. Check firewall/network settings

## Quick Start Command

```bash
# 1. Activate venv (if using)
venv\Scripts\activate

# 2. Run enrollment
python -m dpa.cli.enroll_cli --backend-url https://609b9c24fbd6.ngrok-free.app --enrollment-code YOUR_CODE
```

## Notes

- The backend URL should **NOT** have a trailing slash
- The enrollment code is case-sensitive
- Enrollment requires admin privileges (for TPM access)
- The device must have a TPM chip (for TPM-based enrollment)

