# Simple script to clear TPM key and enrollment data
# Run as Administrator

Write-Host "Clearing TPM Key and Enrollment Data..." -ForegroundColor Cyan

# Step 1: Delete TPM Key Container
Write-Host "`n1. Deleting TPM Key Container..." -ForegroundColor Yellow

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

try {
    Add-Type -TypeDefinition $csharpCode -Language CSharp
    $result = [DeleteTPMKey]::Delete()
    if ($result -eq "SUCCESS") {
        Write-Host "   ✓ TPM key deleted" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $result" -ForegroundColor Yellow
        Write-Host "      (Key may not exist - this is OK)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  Could not delete key: $_" -ForegroundColor Yellow
    Write-Host "      (Key may not exist - this is OK)" -ForegroundColor Gray
}

# Step 2: Clear Local Files
Write-Host "`n2. Clearing Local Enrollment Files..." -ForegroundColor Yellow

$files = @(
    "$env:PROGRAMDATA\ZTNA\enrollment.json",
    "$env:PROGRAMDATA\ZTNA\secret.dat",
    "$env:PROGRAMDATA\ZTNA\salt.dat"
)

$cleared = 0
foreach ($file in $files) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "   ✓ Deleted $(Split-Path $file -Leaf)" -ForegroundColor Green
        $cleared++
    }
}

if ($cleared -eq 0) {
    Write-Host "   - No files to delete (already cleared)" -ForegroundColor Gray
}

Write-Host "`n✓ Cleanup complete!" -ForegroundColor Green
Write-Host "`nNext: Run enrollment again to create new TPM key" -ForegroundColor Yellow

