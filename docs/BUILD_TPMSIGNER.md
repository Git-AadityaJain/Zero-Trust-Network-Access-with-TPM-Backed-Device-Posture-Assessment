# Building TPMSigner.exe

## Prerequisites

### 1. Install .NET 6.0 SDK

**Required:** .NET 6.0 SDK (not just runtime) for building

**Download:** https://dotnet.microsoft.com/download/dotnet/6.0

**Or via winget:**
```powershell
winget install Microsoft.DotNet.SDK.6
```

**Verify installation:**
```powershell
dotnet --version
```
Should show version 6.x.x or higher.

## Building TPMSigner.exe

### Method 1: Using build.bat (Recommended)

**From project root:**
```powershell
cd TPMSigner
.\build.bat
```

**Or from TPMSigner directory:**
```powershell
cd TPMSigner
build.bat
```

This will:
1. Check for .NET SDK
2. Clean previous builds
3. Build Release x64 version
4. Copy TPMSigner.exe to parent directory (`../TPMSigner.exe`)

### Method 2: Using dotnet CLI directly

**From TPMSigner directory:**
```powershell
cd TPMSigner

# Clean previous builds
dotnet clean

# Build and publish
dotnet publish -c Release -r win-x64 --self-contained false /p:PublishSingleFile=true
```

**Output location:**
```
TPMSigner\bin\Release\net6.0-windows\win-x64\publish\TPMSigner.exe
```

**Copy to dpa directory:**
```powershell
copy bin\Release\net6.0-windows\win-x64\publish\TPMSigner.exe ..\dpa\TPMSigner.exe
```

### Method 3: Using Visual Studio

1. Open `dpa.sln` in Visual Studio
2. Right-click `TPMSigner` project → **Publish**
3. Configure:
   - Target: `Folder`
   - Target location: `bin\Release\net6.0-windows\win-x64\publish`
   - Deployment mode: `Self-Contained` = **False**
   - Target runtime: `win-x64`
4. Click **Publish**

## Expected Output

After successful build, you should have:
- `TPMSigner.exe` in the project root (if using build.bat)
- Or in `TPMSigner\bin\Release\net6.0-windows\win-x64\publish\TPMSigner.exe`

## Verifying the Build

### Test TPMSigner

```powershell
# Check status
.\TPMSigner.exe status

# Initialize key (if needed)
.\TPMSigner.exe init-key

# Test signing
.\TPMSigner.exe sign "dGVzdA=="
```

### Expected Output

**Status (key exists):**
```json
{"tpm_available": true, "key_exists": true}
```

**Status (no key):**
```json
{"tpm_available": true, "key_exists": false}
```

**Init Key:**
```
[OUTPUT_START]
<base64-public-key>
[OUTPUT_END]
```

**Sign:**
```
[OUTPUT_START]
<base64-signature>
[OUTPUT_END]
```

## Troubleshooting

### "dotnet: command not found"

**Solution:** Install .NET 6.0 SDK from https://dotnet.microsoft.com/download

### "The target framework 'net6.0-windows' was not found"

**Solution:** Install .NET 6.0 SDK (not just runtime)

### Build succeeds but TPMSigner.exe not found

**Check output location:**
```powershell
# Default location after build.bat
..\TPMSigner.exe

# Or after dotnet publish
TPMSigner\bin\Release\net6.0-windows\win-x64\publish\TPMSigner.exe
```

### "TPM key initialization failed"

**Possible causes:**
1. TPM not available on system
2. Insufficient permissions (run as administrator)
3. TPM not enabled in BIOS

**Solution:**
- Check TPM status in Windows: `tpm.msc`
- Enable TPM in BIOS if disabled
- Run as administrator if permission issues

### "Signing failed: Key does not exist"

**Solution:** Initialize the key first:
```powershell
.\TPMSigner.exe init-key
```

## File Locations

After building, place TPMSigner.exe in one of these locations:

1. **Project root:** `TPMSigner.exe` (default for build.bat)
2. **DPA directory:** `dpa\TPMSigner.exe` (DPA default location)
3. **Custom location:** Set `TPM_SIGNER_EXE_PATH` environment variable

## Integration with DPA

Once built, the DPA will automatically find TPMSigner.exe if it's in:
- `dpa/TPMSigner.exe` (default)

Or set the path:
```powershell
$env:TPM_SIGNER_EXE_PATH = "E:\Code Projects\ztna-project\TPMSigner.exe"
```

## Quick Build Command

**One-liner from project root:**
```powershell
cd TPMSigner; .\build.bat; cd ..
```

This builds and places TPMSigner.exe in the project root.

