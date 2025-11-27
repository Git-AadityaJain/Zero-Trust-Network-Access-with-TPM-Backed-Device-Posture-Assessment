# Check Device Fingerprint and TPM Status
# Run from project root directory

Write-Host "=== Device Fingerprint & TPM Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Check fingerprint
Write-Host "1. Hardware Fingerprint:" -ForegroundColor Yellow
try {
    $fpJson = python -c "from dpa.modules.fingerprint import get_device_fingerprint; import json; print(json.dumps(get_device_fingerprint(), indent=2))" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $fp = $fpJson | ConvertFrom-Json
        Write-Host "   Fingerprint Hash: $($fp.fingerprint_hash)" -ForegroundColor Green
        Write-Host "   Motherboard Serial: $($fp.motherboard_serial)" -ForegroundColor Gray
        Write-Host "   BIOS Serial: $($fp.bios_serial)" -ForegroundColor Gray
        Write-Host "   System UUID: $($fp.system_uuid)" -ForegroundColor Gray
    } else {
        Write-Host "   ERROR: Failed to get fingerprint" -ForegroundColor Red
        Write-Host $fpJson -ForegroundColor Red
    }
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check TPM key status
Write-Host "2. TPM Key Status:" -ForegroundColor Yellow
if (Test-Path ".\dpa\TPMSigner.exe") {
    try {
        $tpmStatus = .\dpa\TPMSigner.exe status 2>&1
        if ($tpmStatus -match 'key_exists.*true') {
            Write-Host "   TPM Key: EXISTS" -ForegroundColor Green
        } elseif ($tpmStatus -match 'key_exists.*false') {
            Write-Host "   TPM Key: NOT FOUND" -ForegroundColor Yellow
        } else {
            Write-Host "   TPM Status: $tpmStatus" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ERROR: Could not check TPM status" -ForegroundColor Red
    }
} else {
    Write-Host "   TPMSigner.exe not found" -ForegroundColor Yellow
}

Write-Host ""

# Check enrollment files
Write-Host "3. Enrollment Files:" -ForegroundColor Yellow
$enrollmentPath = "$env:PROGRAMDATA\ZTNA"
if (Test-Path $enrollmentPath) {
    $files = Get-ChildItem $enrollmentPath -ErrorAction SilentlyContinue
    if ($files) {
        foreach ($file in $files) {
            Write-Host "   Found: $($file.Name)" -ForegroundColor Green
        }
    } else {
        Write-Host "   No enrollment files found" -ForegroundColor Gray
    }
} else {
    Write-Host "   Enrollment directory does not exist" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Check Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Copy the fingerprint_hash above" -ForegroundColor Gray
Write-Host "2. Delete device with this fingerprint from backend admin panel" -ForegroundColor Gray
Write-Host "3. Re-enroll the device" -ForegroundColor Gray

