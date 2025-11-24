# PowerShell Execution Policy - Quick Fix

## The Problem

Windows PowerShell has an execution policy that prevents scripts from running by default. This is a security feature.

## Quick Solutions

### Option 1: Bypass for Current Session (Recommended for Testing)

Run the script with bypass:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\get_local_ip.ps1
```

Or use the helper script:
```powershell
.\scripts\run_get_local_ip.ps1
```

### Option 2: Change Execution Policy for Current User (Permanent)

Run PowerShell as Administrator, then:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

This allows:
- ✅ Scripts you write locally
- ✅ Scripts signed by trusted publishers
- ❌ Blocks unsigned scripts from internet

**Then run:**
```powershell
.\scripts\get_local_ip.ps1
```

### Option 3: Change Execution Policy for Current Process Only

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\scripts\get_local_ip.ps1
```

This only affects the current PowerShell window.

### Option 4: Manual Alternative (No Script Needed)

Just run these commands directly:
```powershell
# Get local IP addresses
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*"
} | Select-Object IPAddress, InterfaceAlias

# Get public IP
(Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content.Trim()
```

## Recommended Approach

For **testing/development**, use **Option 1** (bypass for single command):
- ✅ No permanent changes
- ✅ Safe and reversible
- ✅ Works immediately

For **regular use**, use **Option 2** (RemoteSigned for CurrentUser):
- ✅ Permanent solution
- ✅ Still secure (blocks unsigned internet scripts)
- ✅ Allows your local scripts

## Security Note

- `Bypass` = No restrictions (use only for testing)
- `RemoteSigned` = Safe default (recommended)
- `Unrestricted` = Not recommended (less secure)

## For Other Scripts

All helper scripts can be run the same way:
```powershell
# Firewall configuration
powershell -ExecutionPolicy Bypass -File .\scripts\configure_windows_firewall.ps1

# Verify external access
powershell -ExecutionPolicy Bypass -File .\scripts\verify_external_access.ps1
```

