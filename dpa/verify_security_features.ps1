# PowerShell script to manually verify security features
# Run this in PowerShell (as Administrator for some checks)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Security Features Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Antivirus
Write-Host "1. ANTIVIRUS STATUS:" -ForegroundColor Yellow
Write-Host "   Command: Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct"
Write-Host ""
try {
    $av = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -First 1
    if ($av) {
        Write-Host "   ✓ Product: $($av.displayName)" -ForegroundColor Green
        Write-Host "   ✓ Product State: $($av.productState) (hex)" -ForegroundColor Green
        $running = ($av.productState -band 0x1000) -ne 0
        Write-Host "   Status: $(if ($running) {'Running'} else {'Not Running'})" -ForegroundColor $(if ($running) {'Green'} else {'Red'})
    } else {
        Write-Host "   ✗ No antivirus detected" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Error checking antivirus: $_" -ForegroundColor Red
}
Write-Host ""

# 2. Check Firewall
Write-Host "2. FIREWALL STATUS:" -ForegroundColor Yellow
Write-Host "   Command: netsh advfirewall show allprofiles state"
Write-Host ""
try {
    $fw = netsh advfirewall show allprofiles state
    Write-Host $fw
    $enabled = $fw -match "ON"
    Write-Host ""
    Write-Host "   Status: $(if ($enabled) {'Enabled'} else {'Disabled'})" -ForegroundColor $(if ($enabled) {'Green'} else {'Red'})
} catch {
    Write-Host "   ✗ Error checking firewall: $_" -ForegroundColor Red
}
Write-Host ""

# 3. Check BitLocker
Write-Host "3. BITLOCKER STATUS:" -ForegroundColor Yellow
Write-Host "   Command: Get-BitLockerVolume | Select-Object MountPoint, ProtectionStatus"
Write-Host ""
try {
    $bitlocker = Get-BitLockerVolume | Where-Object { $_.MountPoint -eq "C:" }
    if ($bitlocker) {
        Write-Host "   Mount Point: $($bitlocker.MountPoint)" -ForegroundColor Green
        Write-Host "   Protection Status: $($bitlocker.ProtectionStatus)" -ForegroundColor Green
        Write-Host "   Volume Status: $($bitlocker.VolumeStatus)" -ForegroundColor Green
        $encrypted = $bitlocker.ProtectionStatus -eq "On"
        Write-Host "   Status: $(if ($encrypted) {'Encrypted'} else {'Not Encrypted'})" -ForegroundColor $(if ($encrypted) {'Green'} else {'Red'})
    } else {
        Write-Host "   ✗ BitLocker not configured for C: drive" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Error checking BitLocker: $_" -ForegroundColor Red
    Write-Host "   Note: BitLocker may require Administrator privileges" -ForegroundColor Yellow
}
Write-Host ""

# 4. Check Screen Lock (Screensaver)
Write-Host "4. SCREEN LOCK STATUS:" -ForegroundColor Yellow
Write-Host "   Command: Get-ItemProperty for ScreenSaveActive"
Write-Host ""
try {
    $screenLock = Get-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name ScreenSaveActive -ErrorAction SilentlyContinue
    if ($screenLock) {
        Write-Host "   ScreenSaveActive: $($screenLock.ScreenSaveActive)" -ForegroundColor Green
        Write-Host "   Status: $(if ($screenLock.ScreenSaveActive -eq 1) {'Enabled'} else {'Disabled'})" -ForegroundColor $(if ($screenLock.ScreenSaveActive -eq 1) {'Green'} else {'Yellow'})
    } else {
        Write-Host "   ⚠ Screen lock setting not found in registry" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠ Could not check screen lock: $_" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Verification Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

