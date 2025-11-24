# End-to-End Testing Guide

This guide walks you through testing the complete DPA enrollment and posture reporting flow.

## ⚠️ Important: Testing with ngrok

**After ngrok integration, the frontend is configured to use ngrok URLs. You MUST access the application via the ngrok URL, NOT localhost.**

### Quick Reference

| Component | URL (with ngrok) | URL (localhost - won't work for frontend) |
|-----------|------------------|-------------------------------------------|
| Frontend | `https://YOUR-NGROK-URL.ngrok-free.app` | ❌ `http://localhost:3000` |
| Backend API | `https://YOUR-NGROK-URL.ngrok-free.app/api` | ✅ `http://localhost:8000/api` |
| Keycloak Admin | `https://YOUR-NGROK-URL.ngrok-free.app/auth/admin` | ❌ `http://localhost:8080` |
| DPA Backend URL | `https://YOUR-NGROK-URL.ngrok-free.app` | ✅ `http://localhost:8000` (if on same machine) |

**Replace `YOUR-NGROK-URL` with your actual ngrok URL (e.g., `abc123.ngrok-free.app`)**

## Prerequisites

1. **Services Running**: Ensure all Docker services are running
2. **ngrok Running**: ngrok tunnel must be active
3. **Admin Access**: You need admin credentials to access the frontend
4. **DPA Installed**: Device Posture Agent should be installed on your test device
5. **TPM Enabled**: Your device should have TPM 2.0 enabled

### Get Your ngrok URL

1. **Start ngrok tunnel:**
   ```bash
   ngrok start ztna
   ```

2. **Note your ngrok URL** (e.g., `https://abc123.ngrok-free.app`)

3. **Access the application via ngrok URL**, not localhost

## Step 1: Start All Services

```bash
# Navigate to infra directory
cd infra

# Start all services
docker-compose up -d

# Wait for services to be ready (especially Keycloak - takes 30-60 seconds)
docker-compose ps

# Check logs if needed
docker-compose logs -f
```

### Step 1a: Start ngrok Tunnel

```bash
# Start ngrok (if not already running)
ngrok start ztna
```

**Note your ngrok URL** (e.g., `https://abc123.ngrok-free.app`)

**Verify Services:**
- Frontend: `https://YOUR-NGROK-URL.ngrok-free.app` (NOT localhost:3000)
- Backend API: `https://YOUR-NGROK-URL.ngrok-free.app/api` or `http://localhost:8000/docs`
- Keycloak Admin: `https://YOUR-NGROK-URL.ngrok-free.app/auth/admin` (NOT localhost:8080)

## Step 2: Login to Admin Dashboard

**⚠️ IMPORTANT: Use ngrok URL, not localhost!**

1. Open browser: `https://YOUR-NGROK-URL.ngrok-free.app` (replace with your actual ngrok URL)
2. You may see ngrok's browser warning page - click "Visit Site"
3. Click "Login with Keycloak"
4. You'll be redirected to Keycloak login (via ngrok: `https://YOUR-NGROK-URL.ngrok-free.app/auth/realms/master/protocol/openid-connect/auth`)
5. Login with:
   - **Username**: `admin`
   - **Password**: `adminsecure123`
6. After login, you'll be redirected back to the dashboard
7. You should see the Dashboard

## Step 3: Create Enrollment Code

1. In the dashboard, navigate to **Enrollment Codes** in the sidebar (or go to: `https://YOUR-NGROK-URL.ngrok-free.app/enrollment`)
2. Click **"Create Enrollment Code"**
3. Fill in the form:
   - **Description**: "Test enrollment code" (optional)
   - **Max Uses**: 1 (for single device)
   - **Expires In (Hours)**: 24 (or your preferred duration)
4. Click **"Create"**
5. **Copy the generated enrollment code** from the success message - you'll need it for device enrollment
   - The code is automatically generated (32-character random string)
   - Example: `aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5`

## Step 4: Enroll Device (DPA)

On your test device with DPA installed:

**⚠️ IMPORTANT: Use ngrok URL for backend, not localhost!**

Replace `YOUR-NGROK-URL` with your actual ngrok URL (e.g., `abc123.ngrok-free.app`)

### Option A: Using Environment Variable (Recommended)

```powershell
# Set backend URL to ngrok URL
$env:DPA_BACKEND_URL = "https://YOUR-NGROK-URL.ngrok-free.app"

# Run enrollment
python -m dpa.cli.enroll_cli --enrollment-code YOUR_ENROLLMENT_CODE
```

### Option B: Using CLI Argument

```powershell
python -m dpa.cli.enroll_cli --backend-url https://YOUR-NGROK-URL.ngrok-free.app --enrollment-code YOUR_ENROLLMENT_CODE
```

### Option C: Using Config File

1. Edit `C:\ProgramData\ZTNA\config.json`:
   ```json
   {
     "backend_url": "https://YOUR-NGROK-URL.ngrok-free.app",
     "tpm_enabled": true,
     "reporting_interval": 300
   }
   ```
2. Run enrollment:
   ```powershell
   python -m dpa.cli.enroll_cli --enrollment-code YOUR_ENROLLMENT_CODE
   ```

**Note**: If you're testing on the same machine as the backend, you can use `http://localhost:8000` for the backend URL, but the frontend must still use ngrok URL.

**Expected Output:**
```
=== Device Enrollment ===
Backend URL: https://YOUR-NGROK-URL.ngrok-free.app
Please enter the enrollment code provided by your administrator.
Enrollment Code: YOUR_ENROLLMENT_CODE

Enrolling device...
This may take a moment as TPM key is being initialized...

✓ Enrollment successful!
Device ID: <uuid>
Your device is now registered and will begin submitting posture reports.
```

**Note**: The device will be in `pending` status until admin approval.

## Step 5: Verify Device in Dashboard

1. Go to **Devices** page: `https://YOUR-NGROK-URL.ngrok-free.app/devices`
2. You should see your device with status `pending`
3. Click on the device to view details
4. Verify:
   - Device name matches your computer
   - OS information is correct
   - Status is `pending`
   - Initial posture data is visible

## Step 6: Approve Device and Create User

1. Go to **Pending Devices**: `https://YOUR-NGROK-URL.ngrok-free.app/devices/pending`
2. Find your device and click **"Approve"**
3. Fill in the approval form:
   - **Username**: `test-device-user` (or your preferred username)
   - **Email**: `test-device@example.com`
   - **First Name**: `Test`
   - **Last Name**: `Device`
   - **Temporary Password**: `TempPass123!`
   - **Assign Roles**: Check `dpa-device` (should be checked by default)
4. Click **"Approve Device"**

**Expected Result:**
- Device status changes to `active`
- User is created in Keycloak
- User is assigned `dpa-device` role
- Device is linked to the user

## Step 7: Verify User and Role in Keycloak

1. Go to Keycloak Admin: `https://YOUR-NGROK-URL.ngrok-free.app/auth/admin`
2. You may need to click through ngrok's browser warning
3. Login with: `admin` / `adminsecure123`
4. Navigate to: **Users** → Find your test user
5. Click on the user → **Role Mappings** tab
6. Verify `dpa-device` role is assigned under **Assigned Roles**

## Step 8: Submit Posture Report (Compliant)

The DPA should automatically submit posture reports every 5 minutes (300 seconds). You can also manually trigger it:

### Option A: Wait for Automatic Submission

The DPA scheduler will automatically submit posture reports at the configured interval.

### Option B: Manual Submission (for testing)

Create a test script:

```python
# test_posture_submit.py
from dpa.core.posture_submission import PostureSubmitter
from dpa.modules.posture import collect_posture_report

# Collect posture data
posture_report = collect_posture_report()

# Submit to backend (use ngrok URL)
submitter = PostureSubmitter(backend_url="https://YOUR-NGROK-URL.ngrok-free.app")
success = submitter.submit_posture(posture_report)

if success:
    print("✓ Posture report submitted successfully")
else:
    print("✗ Posture submission failed")
```

Run:
```powershell
python test_posture_submit.py
```

**Note**: Replace `YOUR-NGROK-URL` with your actual ngrok URL.

**Expected Result:**
- Posture report is accepted
- Device compliance status is evaluated
- If compliant: `dpa-device` role is maintained
- Posture history is stored

## Step 9: Verify Posture Report in Dashboard

1. Go to **Devices** page: `https://YOUR-NGROK-URL.ngrok-free.app/devices`
2. Find your device
3. Verify:
   - **Compliance Status**: Shows `Compliant` or `Non-Compliant`
   - **Last Posture Check**: Shows recent timestamp
4. Click on device to view details
5. Check posture history (if available in UI)

## Step 10: Test Non-Compliant Posture (Role Revocation)

To test role revocation, you need to simulate a non-compliant device. This requires modifying the posture data or disabling security features.

### Option A: Disable Security Features Temporarily

1. **Disable Windows Firewall** (temporarily for testing)
2. **Disable Antivirus** (if possible, temporarily)
3. Wait for next posture submission (or trigger manually)
4. The device should become non-compliant

### Option B: Modify Posture Data (Advanced)

**Note**: Modifying posture data will invalidate the TPM signature. It's better to actually disable security features temporarily.

If you want to test with modified data, you'll need to bypass signature verification (not recommended for production testing).

**Expected Result:**
- Posture report shows `is_compliant: false`
- Device compliance status updates to `Non-Compliant`
- **`dpa-device` role is revoked from Keycloak user**
- Check Keycloak Admin → User → Role Mappings → `dpa-device` should be removed

## Step 11: Verify Role Revocation

1. Go to Keycloak Admin: `https://YOUR-NGROK-URL.ngrok-free.app/auth/admin`
2. Navigate to: **Users** → Find your test user
3. Click on user → **Role Mappings** tab
4. Verify `dpa-device` role is **NOT** in **Assigned Roles** (should be in **Available Roles**)

## Step 12: Test Role Restoration (Compliant Again)

1. **Re-enable security features**:
   - Enable Windows Firewall
   - Enable Antivirus
2. Wait for next posture submission (or trigger manually)
3. Device should become compliant again

**Expected Result:**
- Posture report shows `is_compliant: true`
- Device compliance status updates to `Compliant`
- **`dpa-device` role is restored to Keycloak user**
- Check Keycloak Admin → User → Role Mappings → `dpa-device` should be back in **Assigned Roles**

## Step 13: Verify Complete Flow

### Check Dashboard
1. Go to Dashboard: `https://YOUR-NGROK-URL.ngrok-free.app`
2. Verify statistics:
   - Total Devices: 1
   - Compliant: 1 (or 0 if non-compliant)
   - Non-Compliant: 0 (or 1 if non-compliant)

### Check Device Details
1. Go to Devices: `https://YOUR-NGROK-URL.ngrok-free.app/devices`
2. Click on your device
3. Verify:
   - Status: `active`
   - Compliance: `Compliant` or `Non-Compliant`
   - Last Posture Check: Recent timestamp
   - Posture History: Multiple entries

### Check Posture History API
```bash
# Get device ID from dashboard, then:
curl -X GET "https://YOUR-NGROK-URL.ngrok-free.app/api/posture/device/{device_id}/history" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Note**: Replace `YOUR-NGROK-URL` with your actual ngrok URL.

## Troubleshooting

### Device Enrollment Fails

1. **Check enrollment code**:
   - Verify code is correct
   - Check if code is expired or already used
   - Verify code exists in backend

2. **Check backend connection**:
   ```powershell
   # Using ngrok URL
   curl https://YOUR-NGROK-URL.ngrok-free.app/health
   
   # Or if testing on same machine
   curl http://localhost:8000/health
   ```

3. **Check DPA logs**:
   - Look for error messages in enrollment output
   - Check TPM initialization errors

### Posture Submission Fails

1. **Check device status**:
   - Device must be `active` and `is_enrolled = true`
   - Verify device is approved

2. **Check signature**:
   - TPM key must match the one stored during enrollment
   - Verify TPM is working: `.\TPMSigner.exe status`

3. **Check backend logs**:
   ```bash
   cd infra
   docker-compose logs backend | grep posture
   ```

### Role Not Revoked

1. **Check compliance evaluation**:
   - Verify `is_compliant` is actually `false` in response
   - Check backend logs for role revocation messages

2. **Check Keycloak connection**:
   - Verify Keycloak service is accessible
   - Check backend logs for Keycloak errors

3. **Check user exists**:
   - Verify device has `user_id` set
   - Verify user has `keycloak_id` set

## Success Criteria

✅ Device enrolls successfully with enrollment code  
✅ Device appears in dashboard with `pending` status  
✅ Admin can approve device and create user  
✅ User is assigned `dpa-device` role in Keycloak  
✅ Device submits posture reports successfully  
✅ Posture reports are visible in dashboard  
✅ Non-compliant posture revokes `dpa-device` role  
✅ Compliant posture restores `dpa-device` role  
✅ Dashboard shows correct compliance statistics  

## Next Steps

After successful testing:
1. Test with multiple devices
2. Test with different compliance scenarios
3. Test role revocation with different violations
4. Test policy evaluation with posture data
5. Test remote access via ngrok/Cloudflare

---

**Happy Testing! 🚀**

