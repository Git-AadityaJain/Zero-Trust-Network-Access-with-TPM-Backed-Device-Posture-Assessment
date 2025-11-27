# Fix .NET Runtime Issue for TPMSigner

## Problem
TPMSigner.exe requires .NET 6.0 runtime, but your system only has .NET 10.0 installed.

**Error:**
```
You must install or update .NET to run this application.
Framework: 'Microsoft.NETCore.App', version '6.0.0' (x64)
```

## Solution Options

### Option 1: Install .NET 6.0 Runtime (Quick Fix) ⚡

**Download and install .NET 6.0 Runtime:**
- Direct link: https://dotnet.microsoft.com/download/dotnet/6.0
- Or use winget:
  ```powershell
  winget install Microsoft.DotNet.Runtime.6
  ```

**Verify installation:**
```powershell
dotnet --list-runtimes
```
Should now show:
```
Microsoft.NETCore.App 6.0.x [C:\Program Files\dotnet\shared\Microsoft.NETCore.App]
Microsoft.NETCore.App 10.0.0 [C:\Program Files\dotnet\shared\Microsoft.NETCore.App]
```

**Restart DPA API server after installation:**
```powershell
cd dpa
python start_api_server.py
```

---

### Option 2: Rebuild TPMSigner for .NET 8.0/10.0 (Better Long-term) 🔧

Since you have .NET 10.0, we can rebuild TPMSigner to use a newer framework.

#### Step 1: Update TPMSigner.csproj

Change the target framework from `net6.0-windows` to `net8.0-windows` or `net10.0-windows`:

**Edit `TPMSigner/TPMSigner.csproj`:**
```xml
<PropertyGroup>
  <OutputType>Exe</OutputType>
  <TargetFramework>net8.0-windows</TargetFramework>  <!-- Changed from net6.0-windows -->
  <PlatformTarget>x64</PlatformTarget>
  <RuntimeIdentifier>win-x64</RuntimeIdentifier>
  <SelfContained>false</SelfContained>
  <PublishSingleFile>true</PublishSingleFile>
  <PublishReadyToRun>true</PublishReadyToRun>
  <IncludeNativeLibrariesForSelfExtract>true</IncludeNativeLibrariesForSelfExtract>
</PropertyGroup>
```

#### Step 2: Rebuild TPMSigner

```powershell
cd TPMSigner
dotnet clean
dotnet publish -c Release -r win-x64 --self-contained false /p:PublishSingleFile=true
```

#### Step 3: Copy to DPA Directory

```powershell
# Copy the new build
copy bin\Release\net8.0-windows\win-x64\publish\TPMSigner.exe ..\dpa\TPMSigner.exe

# Or if using net10.0-windows
copy bin\Release\net10.0-windows\win-x64\publish\TPMSigner.exe ..\dpa\TPMSigner.exe
```

#### Step 4: Verify

```powershell
cd ..
.\dpa\TPMSigner.exe status
```

Should work without .NET 6.0 runtime!

---

## Recommended: Quick Fix (Option 1)

For immediate testing, **Option 1 is fastest** - just install .NET 6.0 runtime (it's small, ~50MB).

For production, consider **Option 2** to use a newer framework version.

---

## After Fixing

Once the .NET issue is resolved:

1. **Restart DPA API server:**
   ```powershell
   cd dpa
   python start_api_server.py
   ```

2. **Verify TPM is working:**
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8081/health -UseBasicParsing | ConvertFrom-Json
   ```

   Should show:
   ```json
   {
     "status": "healthy",
     "enrolled": true,
     "tpm_available": true,
     "message": "DPA API is running"
   }
   ```

3. **Continue with frontend testing** as per `FRONTEND_TEST_STEPS.md`

