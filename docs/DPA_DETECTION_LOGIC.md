# DPA Detection Logic Explanation

This document explains how the DPA (Device Posture Agent) detects security features on Windows devices.

## 1. Antivirus Detection

**Command Used:**
```powershell
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object displayName, productState | ConvertTo-Json
```

**Logic:**
- Queries Windows Security Center for installed antivirus products
- Gets the `productState` value (hex number)
- Checks bit 12-15: `(productState & 0x1000) != 0` means antivirus is running
- Returns: `{"installed": True, "running": True/False, "product_name": "..."}`

**Backend Evaluation:**
- Checks: `antivirus.get("installed") == True AND antivirus.get("running") == True`
- If both are True → Antivirus is enabled ✓
- If either is False → Antivirus violation (-30 points)

**Example:**
- Windows Defender with `productState: 397568`
- `397568 & 0x1000 = 4096` (non-zero) → Running = True
- Result: `{"installed": True, "running": True, "product_name": "Windows Defender"}`

---

## 2. Firewall Detection

**Command Used:**
```cmd
netsh advfirewall show allprofiles state
```

**Logic:**
- Runs `netsh` command to check Windows Firewall status
- Parses output looking for "State" and "ON" keywords
- Checks all profiles (Domain, Private, Public)
- Returns: `{"firewall_enabled": True/False, "firewall_profile": "Domain/Private/Public"}`

**Backend Evaluation:**
- Checks: `firewall.get("firewall_enabled") == True`
- If True → Firewall is enabled ✓
- If False → Firewall violation (-25 points)

**Example Output:**
```
Domain Profile Settings: 
State                                 ON
```
- Code finds "state" and "on" → `firewall_enabled = True`

---

## 3. Disk Encryption (BitLocker) Detection

**Command Used:**
```powershell
Get-BitLockerVolume | Where-Object { $_.MountPoint -eq 'C:' } | Select-Object MountPoint, ProtectionStatus, VolumeStatus | ConvertTo-Json
```

**Logic:**
- Queries BitLocker status for C: drive
- Checks `ProtectionStatus` field (can be "On"/"Off" string or 1/0 integer)
- Handles both formats: string "On" or integer 1 = encrypted
- **Note:** Requires administrator privileges
- If command fails → defaults to `encryption_enabled = False`
- Returns: `{"encryption_enabled": True/False, "encryption_method": "BitLocker"/"None"}`

**Backend Evaluation:**
- Checks: `disk_encryption.get("encryption_enabled") == True`
- If True → Disk encryption is enabled ✓
- If False → Disk encryption violation (-25 points)

**Example:**
- `ProtectionStatus: "Off"` → `encryption_enabled = False`
- `ProtectionStatus: "On"` → `encryption_enabled = True`

---

## 4. Screen Lock Detection

**Command Used:**
```powershell
Get-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name ScreenSaveActive | Select-Object -ExpandProperty ScreenSaveActive
```

**Logic:**
- Reads Windows registry value for screensaver
- `ScreenSaveActive = 1` means screensaver (screen lock) is enabled
- `ScreenSaveActive = 0` means disabled
- Also checks Group Policy location as fallback
- Returns: `{"screen_lock_enabled": True/False, "timeout_seconds": 0-3600, "method": "Screensaver"/"Group Policy"}`

**Backend Evaluation:**
- Checks: `screen_lock.get("screen_lock_enabled") == True`
- If True → Screen lock is enabled ✓
- If False → Screen lock violation (-10 points)

**Example:**
- Registry value `1` → `screen_lock_enabled = True`
- Registry value `0` → `screen_lock_enabled = False`

---

## Compliance Scoring

The backend evaluates compliance based on these checks:

| Feature | Points | Violation Message |
|---------|--------|-------------------|
| Antivirus | -30 | "Antivirus not enabled" |
| Firewall | -25 | "Firewall not enabled" |
| Disk Encryption | -25 | "Disk encryption not enabled" |
| Screen Lock | -10 | "Screen lock not enabled" |
| OS Updates (>10 pending) | -10 | "{count} pending updates" |

**Compliance Threshold:** 70%
- Score ≥ 70% → **COMPLIANT**
- Score < 70% → **NON-COMPLIANT**

**Example Calculation:**
- All features enabled: 100% → COMPLIANT ✓
- Only disk encryption missing: 75% → COMPLIANT ✓
- Antivirus + Firewall missing: 45% → NON-COMPLIANT ✗

---

## Data Structure Sent to Backend

The DPA sends a nested structure:

```json
{
  "device_id": "uuid",
  "timestamp": "ISO8601",
  "os_info": {...},
  "antivirus": {
    "installed": true,
    "running": true,
    "product_name": "Windows Defender"
  },
  "firewall": {
    "firewall_enabled": true,
    "firewall_profile": "Domain"
  },
  "disk_encryption": {
    "encryption_enabled": false,
    "encryption_method": "None"
  },
  "screen_lock": {
    "screen_lock_enabled": true,
    "timeout_seconds": 0,
    "method": "Screensaver"
  },
  "fingerprint": {...}
}
```

**Backend extracts nested values:**
- `antivirus = posture_data.get("antivirus", {})`
- `firewall = posture_data.get("firewall", {})`
- `disk_encryption = posture_data.get("disk_encryption", {})`
- `screen_lock = posture_data.get("screen_lock", {})`

Then checks the specific fields within each nested object.

