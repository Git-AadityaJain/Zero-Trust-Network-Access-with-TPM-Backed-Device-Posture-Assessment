# TPMSigner.exe Setup

## Overview

The DPA uses `TPMSigner.exe` to interact with the TPM (Trusted Platform Module) for cryptographic operations. This executable must be available for challenge signing to work.

## Default Location

The DPA looks for `TPMSigner.exe` at:
```
dpa/TPMSigner.exe
```

## If TPMSigner.exe is in a Different Location

If your `TPMSigner.exe` is located elsewhere (e.g., `dpa/TPMSigner/bin/Release/TPMSigner.exe`), you can specify the path via environment variable:

### Option 1: Environment Variable

**Windows PowerShell:**
```powershell
$env:TPM_SIGNER_EXE_PATH = "E:\Code Projects\ztna-project\dpa\TPMSigner\bin\Release\TPMSigner.exe"
python dpa/start_api_server.py
```

**Windows CMD:**
```cmd
set TPM_SIGNER_EXE_PATH=E:\Code Projects\ztna-project\dpa\TPMSigner\bin\Release\TPMSigner.exe
python dpa/start_api_server.py
```

**Linux/WSL:**
```bash
export TPM_SIGNER_EXE_PATH="/path/to/TPMSigner.exe"
python dpa/start_api_server.py
```

### Option 2: Modify Code

You can also modify `dpa/api/server.py` to hardcode the path:

```python
def get_signer() -> PostureSigner:
    global signer
    if signer is None:
        tpm_path = r"E:\Code Projects\ztna-project\dpa\TPMSigner\bin\Release\TPMSigner.exe"
        signer = PostureSigner(tpm_exe_path=tpm_path)
    return signer
```

## Verifying TPMSigner Works

### Test TPM Status

```python
from dpa.core.tpm import TPMWrapper

# With default path
tpm = TPMWrapper()

# Or with custom path
tpm = TPMWrapper(exe_path=r"E:\Code Projects\ztna-project\dpa\TPMSigner\bin\Release\TPMSigner.exe")

tpm_available, key_exists, error = tpm.check_status()
print(f"TPM Available: {tpm_available}")
print(f"Key Exists: {key_exists}")
if error:
    print(f"Error: {error}")
```

### Test Challenge Signing

Once TPMSigner is configured, test the API:

```powershell
# PowerShell
$body = @{challenge="test-123"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8081/sign-challenge" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
```

## Common Issues

### "TPMSigner executable not found"

**Solution:** 
1. Locate your `TPMSigner.exe` file
2. Set `TPM_SIGNER_EXE_PATH` environment variable
3. Or copy `TPMSigner.exe` to `dpa/TPMSigner.exe`

### "TPM signing failed"

**Possible causes:**
1. TPM not available on system
2. TPM key not initialized
3. TPMSigner.exe permissions issue

**Solution:**
- Check TPM status: `tpm.check_status()`
- Initialize TPM key if needed
- Run as administrator if required

### TPM Available but Key Doesn't Exist

**Solution:** Initialize the TPM key:

```python
from dpa.core.signing import PostureSigner

signer = PostureSigner()
success, pub_key = signer.register_device()
if success:
    print(f"TPM key initialized: {pub_key[:50]}...")
else:
    print(f"Failed: {pub_key}")
```

## For Testing Without TPM

If you're testing without a real TPM, you can:

1. **Use mock signatures** (for backend testing only)
2. **Skip TPM verification** in test mode (not recommended for production)
3. **Use software TPM emulator** (if available)

**Note:** For production, real TPM hardware is required for security.

## Integration with DPA API Server

The DPA API server automatically uses the `TPM_SIGNER_EXE_PATH` environment variable if set. No code changes needed - just set the environment variable before starting the server.

```powershell
# Set path and start server
$env:TPM_SIGNER_EXE_PATH = "E:\Code Projects\ztna-project\dpa\TPMSigner\bin\Release\TPMSigner.exe"
python dpa/start_api_server.py
```

The server will log if TPMSigner is found or not on startup.

