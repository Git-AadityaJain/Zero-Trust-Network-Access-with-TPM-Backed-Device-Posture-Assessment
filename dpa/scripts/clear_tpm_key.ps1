# PowerShell script to clear TPM key and local enrollment data
# Run as Administrator

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Clearing TPM Key and Enrollment Data" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   TPM key deletion requires admin privileges" -ForegroundColor Yellow
    Write-Host "   Please run PowerShell as Administrator" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Delete TPM Key Container
Write-Host ""
Write-Host "1. Deleting TPM Key Container..." -ForegroundColor Yellow

try {
    # Use certutil to delete the key container
    # The key container name is "DPA_TPM_Key" (from TPMSigner Program.cs)
    $keyContainerName = "DPA_TPM_Key"
    
    # Method 1: Using certutil (if available)
    $certutilPath = "certutil"
    if (Get-Command $certutilPath -ErrorAction SilentlyContinue) {
        Write-Host "   Attempting to delete key container using certutil..." -ForegroundColor Gray
        $result = & certutil -csp "Microsoft Enhanced RSA and AES Cryptographic Provider" -key -delete $keyContainerName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ Key container deleted via certutil" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  certutil method failed (key may not exist or already deleted)" -ForegroundColor Yellow
        }
    }
    
    # Method 2: Using .NET to delete key container
    Write-Host "   Attempting to delete key container using .NET..." -ForegroundColor Gray
    try {
        $csharpCode = @"
using System;
using System.Security.Cryptography;

public class DeleteTPMKey {
    public static string Delete() {
        try {
            var cspParams = new CspParameters {
                KeyContainerName = "DPA_TPM_Key",
                Flags = CspProviderFlags.UseMachineKeyStore
            };
            
            using (var rsa = new RSACryptoServiceProvider(cspParams)) {
                rsa.PersistKeyInCsp = false;
                rsa.Clear();
            }
            
            return "SUCCESS";
        } catch (Exception ex) {
            return "ERROR: " + ex.Message;
        }
    }
}
"@
        
        # Compile and run C# code
        Add-Type -TypeDefinition $csharpCode -Language CSharp -ErrorAction Stop
        $result = [DeleteTPMKey]::Delete()
        
        if ($result -eq "SUCCESS") {
            Write-Host "   ✓ Key container deleted" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $result" -ForegroundColor Yellow
            if ($result -like "*not found*" -or $result -like "*does not exist*") {
                Write-Host "      Key may not exist (this is OK)" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "   ⚠️  Could not delete key container: $_" -ForegroundColor Yellow
        Write-Host "      Key may not exist or already deleted (this is OK)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not delete key container: $_" -ForegroundColor Yellow
    Write-Host "      Key may not exist (this is OK)" -ForegroundColor Gray
}

# Step 2: Clear Local Enrollment Data
Write-Host ""
Write-Host "2. Clearing Local Enrollment Data..." -ForegroundColor Yellow

$enrollmentFile = "$env:PROGRAMDATA\ZTNA\enrollment.json"
$configFile = "$env:PROGRAMDATA\ZTNA\config.json"
$secretFile = "$env:PROGRAMDATA\ZTNA\secret.dat"
$saltFile = "$env:PROGRAMDATA\ZTNA\salt.dat"

$filesCleared = 0

if (Test-Path $enrollmentFile) {
    Remove-Item $enrollmentFile -Force
    Write-Host "   ✓ Deleted enrollment.json" -ForegroundColor Green
    $filesCleared++
} else {
    Write-Host "   - enrollment.json not found (already cleared)" -ForegroundColor Gray
}

if (Test-Path $secretFile) {
    Remove-Item $secretFile -Force
    Write-Host "   ✓ Deleted secret.dat" -ForegroundColor Green
    $filesCleared++
} else {
    Write-Host "   - secret.dat not found" -ForegroundColor Gray
}

if (Test-Path $saltFile) {
    Remove-Item $saltFile -Force
    Write-Host "   ✓ Deleted salt.dat" -ForegroundColor Green
    $filesCleared++
} else {
    Write-Host "   - salt.dat not found" -ForegroundColor Gray
}

# Note: config.json is kept (contains backend_url, etc.)
Write-Host "   - config.json kept (contains backend URL configuration)" -ForegroundColor Gray

# Step 3: Verify TPM Key is Cleared
Write-Host ""
Write-Host "3. Verifying TPM Key Status..." -ForegroundColor Yellow

if (Test-Path "dpa\TPMSigner.exe") {
    $statusResult = & "dpa\TPMSigner.exe" status 2>&1
    if ($LASTEXITCODE -eq 2) {
        Write-Host "   ✓ TPM key does not exist (cleared successfully)" -ForegroundColor Green
    } elseif ($LASTEXITCODE -eq 0) {
        Write-Host "   ⚠️  TPM key still exists" -ForegroundColor Yellow
        Write-Host "      You may need to run this script as Administrator" -ForegroundColor Yellow
    } else {
        Write-Host "   ⚠️  Could not check TPM status" -ForegroundColor Yellow
    }
} else {
    Write-Host "   - TPMSigner.exe not found (cannot verify)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Files cleared: $filesCleared" -ForegroundColor $(if ($filesCleared -gt 0) { "Green" } else { "Gray" })
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run enrollment again: python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE" -ForegroundColor White
Write-Host "2. A new TPM key will be generated during enrollment" -ForegroundColor White
Write-Host ""

