# Troubleshooting Guide

This guide covers common issues and their solutions for the ZTNA Platform.

## Table of Contents

1. [Device Enrollment Issues](#device-enrollment-issues)
2. [TPM Key Issues](#tpm-key-issues)
3. [Database Issues](#database-issues)
4. [Network & Connectivity](#network--connectivity)
5. [Authentication Issues](#authentication-issues)
6. [Posture Reporting Issues](#posture-reporting-issues)

---

## Device Enrollment Issues

### "Device already enrolled" Error

**Problem:** Enrollment fails with "Device with this hardware fingerprint already enrolled"

**Cause:** A device with the same hardware fingerprint already exists in the database.

**Solution:**

1. **Check your device fingerprint:**
   ```powershell
   python -c "from dpa.modules.fingerprint import get_device_fingerprint; fp = get_device_fingerprint(); print('Fingerprint:', fp['fingerprint_hash'])"
   ```

2. **Delete existing device from database:**
   ```bash
   docker exec -it ztna-db psql -U ztnauser -d ztna -c "DELETE FROM devices WHERE fingerprint_hash = 'YOUR_FINGERPRINT_HASH';"
   ```

3. **Re-enroll the device:**
   ```powershell
   python -m dpa.cli.enroll_cli --backend-url https://your-backend-url.com --enrollment-code YOUR_CODE
   ```

### Empty Hardware Identifiers

**Problem:** Motherboard, BIOS, and UUID fields are empty, causing fingerprint collisions.

**Cause:** WMIC output parsing issue (fixed in latest version).

**Solution:** Ensure you're using the latest version of `dpa/modules/fingerprint.py` which properly parses WMIC output.

**Verify fix:**
```powershell
python -c "from dpa.modules.fingerprint import get_device_fingerprint; import json; fp = get_device_fingerprint(); print(json.dumps(fp, indent=2))"
```

Should show actual hardware identifiers, not empty strings.

### DNS Resolution Errors During Enrollment

**Problem:** `NameResolutionError` when enrolling remote device.

**Solution:**

1. **Change DNS server on remote device:**
   - Use Google DNS: `8.8.8.8`, `8.8.4.4`
   - Or Cloudflare DNS: `1.1.1.1`, `1.0.0.1`

2. **Verify connectivity:**
   ```powershell
   nslookup your-backend-url.com
   Test-NetConnection -ComputerName your-backend-url.com -Port 443
   ```

3. **Use IP address temporarily** (if DNS continues to fail):
   ```powershell
   python -m dpa.cli.enroll_cli --backend-url https://IP_ADDRESS --enrollment-code YOUR_CODE
   ```

---

## TPM Key Issues

### TPM Key Not Found

**Problem:** `TPMSigner.exe status` shows `"key_exists": false`

**Solution:**

1. **Initialize TPM key:**
   ```powershell
   .\dpa\TPMSigner.exe init-key
   ```

2. **Verify key exists:**
   ```powershell
   .\dpa\TPMSigner.exe status
   ```

### TPM Key Deletion

**To clear TPM key and re-initialize:**

```powershell
# Delete TPM key container
$code = @"
using System;
using System.Security.Cryptography;
public class DeleteTPMKey {
    public static string Delete() {
        try {
            var csp = new CspParameters {
                KeyContainerName = "DPA_TPM_Key",
                Flags = CspProviderFlags.UseMachineKeyStore
            };
            using (var rsa = new RSACryptoServiceProvider(csp)) {
                rsa.PersistKeyInCsp = false;
                rsa.Clear();
            }
            return "SUCCESS";
        } catch { return "ERROR"; }
    }
}
"@
Add-Type -TypeDefinition $code -Language CSharp
[DeleteTPMKey]::Delete()

# Delete enrollment files
Remove-Item "$env:PROGRAMDATA\ZTNA\enrollment.json" -ErrorAction SilentlyContinue
Remove-Item "$env:PROGRAMDATA\ZTNA\secret.dat" -ErrorAction SilentlyContinue
Remove-Item "$env:PROGRAMDATA\ZTNA\salt.dat" -ErrorAction SilentlyContinue

# Re-initialize
.\dpa\TPMSigner.exe init-key
```

### Update TPM Key for Existing Device

**If you re-initialized TPM key but device is already enrolled:**

1. **Get new TPM public key:**
   ```powershell
   .\dpa\TPMSigner.exe init-key
   # Copy the base64 public key from output
   ```

2. **Update device record in database:**
   ```bash
   docker exec -it ztna-db psql -U ztnauser -d ztna
   ```
   ```sql
   UPDATE devices 
   SET tpm_public_key = 'YOUR_NEW_PEM_PUBLIC_KEY'
   WHERE fingerprint_hash = 'YOUR_FINGERPRINT_HASH';
   ```

---

## Database Issues

### Delete Device from Database

**Using SQL:**
```bash
docker exec -it ztna-db psql -U ztnauser -d ztna -c "DELETE FROM devices WHERE fingerprint_hash = 'YOUR_FINGERPRINT_HASH';"
```

**Or interactively:**
```bash
docker exec -it ztna-db psql -U ztnauser -d ztna
```
```sql
SELECT id, device_name, fingerprint_hash, status FROM devices;
DELETE FROM devices WHERE id = DEVICE_ID;
```

### Database Connection Errors

**Problem:** Backend can't connect to database.

**Solution:**

1. **Check PostgreSQL is running:**
   ```bash
   docker-compose ps
   docker-compose logs postgres
   ```

2. **Verify credentials in `backend/.env`:**
   ```
   POSTGRES_USER=ztnauser
   POSTGRES_PASSWORD=supersecret
   POSTGRES_DB=ztna
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   ```

3. **Restart services:**
   ```bash
   docker-compose restart backend postgres
   ```

---

## Network & Connectivity

### CORS Errors

**Problem:** Frontend can't access backend API due to CORS.

**Solution:**

1. **Check CORS_ORIGIN in `backend/.env`:**
   ```
   CORS_ORIGIN=http://localhost:3000,https://your-domain.com
   ```

2. **Restart backend:**
   ```bash
   docker-compose restart backend
   ```

### External Access (ngrok/Cloudflare)

**Problem:** Keycloak redirects not working with external URL.

**Solution:**

1. **Update Keycloak client redirect URIs:**
   - Access: `https://your-url.com/auth/admin`
   - Go to **Clients** → **admin-frontend**
   - Add to **Valid Redirect URIs**: `https://your-url.com/callback`
   - Add to **Web Origins**: `https://your-url.com`

2. **Rebuild frontend** (env vars are bundled at build time):
   ```bash
   docker-compose build frontend && docker-compose up -d
   ```

---

## Authentication Issues

### Keycloak Service Account Permissions

**Problem:** `403 Forbidden` when backend tries to assign roles.

**Solution:** Run the service account role assignment script:

```bash
docker-compose exec backend python scripts/assign_service_account_roles.py
```

### Invalid Token Errors

**Problem:** API returns 401 Unauthorized.

**Solution:**

1. **Check token expiration** - Tokens expire after 15 minutes
2. **Refresh token** - Frontend should auto-refresh
3. **Check Keycloak is accessible** - Verify `/auth` endpoint works
4. **Verify OIDC configuration** in `backend/.env`

---

## Posture Reporting Issues

### Posture Not Updating

**Problem:** Device posture not updating in dashboard.

**Solution:**

1. **Check DPA is running:**
   ```powershell
   # Check if posture scheduler is running
   Get-Process python | Where-Object {$_.CommandLine -like "*start_posture_scheduler*"}
   ```

2. **Check DPA logs:**
   ```powershell
   # Look for posture submission logs
   # Check for errors in posture collection
   ```

3. **Verify backend connectivity:**
   ```powershell
   # Test backend URL
   Invoke-WebRequest -Uri "https://your-backend-url.com/api/health"
   ```

4. **Check device status:**
   - Device must be in "active" status
   - Device must be enrolled and approved
   - TPM key must match database

### Signature Verification Failed

**Problem:** Backend rejects posture reports due to signature verification failure.

**Solution:**

1. **Verify TPM key matches:**
   - Check device's TPM public key matches database
   - Re-enroll if key was re-initialized

2. **Check TPMSigner is working:**
   ```powershell
   .\dpa\TPMSigner.exe status
   ```

3. **Verify signature format** - Backend expects RSA-PSS with SHA256

---

## Getting Help

If you encounter issues not covered here:

1. **Check logs:**
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   docker-compose logs keycloak
   ```

2. **Review API documentation:**
   - Backend: `http://localhost:8000/docs`
   - Check request/response formats

3. **Verify configuration:**
   - Environment variables
   - Database connectivity
   - Network connectivity

4. **Open an issue** with:
   - Error messages
   - Logs
   - Steps to reproduce
   - Environment details

