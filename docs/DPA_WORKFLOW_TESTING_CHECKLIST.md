# DPA Workflow Testing Checklist

This document outlines all components of the DPA workflow that need to be tested.

## ✅ Completed Tests

1. **Device Enrollment** - ✅ Working
   - DPA can enroll with enrollment code
   - Device appears in backend as "pending"
   - TPM key initialization works

2. **Posture Scheduler** - ✅ Working
   - Automatic posture reporting every 5 minutes
   - Posture data correctly collected and submitted
   - Compliance evaluation working correctly

---

## 🔲 Remaining Tests

### 3. Device Approval & User Binding

**Test Steps:**
1. Admin logs into frontend
2. Navigate to "Devices" → "Pending Devices"
3. Find your enrolled device
4. Click "Approve"
5. Fill in user details:
   - Username
   - Email
   - First Name / Last Name
   - Temporary Password
   - Assign Roles: Check `dpa-device` role
6. Click "Approve Device"

**Expected Results:**
- Device status changes from "pending" to "active"
- User is created in Keycloak
- User is created in backend database
- Device is linked to the user
- User gets `dpa-device` role assigned
- Device can now submit posture reports

**Verification:**
- Check Keycloak Admin Console → Users → Find the new user
- Verify user has `dpa-device` role
- Check backend database: `devices` table shows `user_id` linked
- Check backend database: `users` table has new user record

---

### 4. Role Revocation (Non-Compliant Device)

**Test Steps:**
1. Ensure device is enrolled, approved, and active
2. Ensure device is currently compliant (score ≥ 70%)
3. Make device non-compliant by:
   - Disabling Windows Firewall, OR
   - Disabling Windows Defender, OR
   - Disabling Screen Lock
4. Wait for next posture report (or manually trigger)
5. Check that device becomes non-compliant (score < 70%)

**Expected Results:**
- Posture report shows non-compliant status
- Backend automatically revokes `dpa-device` role from user
- User loses access to resources requiring `dpa-device` role
- Audit log entry created for role revocation

**Verification:**
- Check Keycloak Admin Console → Users → Find user → Role Mappings
- Verify `dpa-device` role is removed
- Check backend logs for "Revoking dpa-device role" message
- Check audit logs for "role_revoked_non_compliant" action

---

### 5. Role Restoration (Device Becomes Compliant)

**Test Steps:**
1. Device is currently non-compliant (role was revoked)
2. Fix the compliance issue:
   - Re-enable Windows Firewall, OR
   - Re-enable Windows Defender, OR
   - Re-enable Screen Lock
3. Wait for next posture report (or manually trigger)
4. Check that device becomes compliant (score ≥ 70%)

**Expected Results:**
- Posture report shows compliant status
- Backend automatically restores `dpa-device` role to user
- User regains access to resources requiring `dpa-device` role
- Audit log entry created for role restoration

**Verification:**
- Check Keycloak Admin Console → Users → Find user → Role Mappings
- Verify `dpa-device` role is restored
- Check backend logs for "Restoring dpa-device role" message
- Check audit logs for "role_restored_compliant" action

---

### 6. Access Request with Fresh Posture (Per-Request Posture Check)

**Test Steps:**
1. Device is enrolled, approved, and active
2. User has `dpa-device` role
3. Get JWT token for the user (login via frontend or Keycloak)
4. Use DPA CLI to request access to a resource:
   ```powershell
   python -m dpa.cli.request_access_cli \
     --device-id <DEVICE_ID> \
     --resource "server1" \
     --access-type "read" \
     --auth-token <JWT_TOKEN>
   ```

**Expected Results:**
- DPA collects fresh posture data
- DPA signs posture data with TPM
- Access request includes fresh posture data
- Backend evaluates fresh posture before granting access
- If compliant → Access granted, JWT token issued
- If non-compliant → Access denied
- Posture history updated with fresh posture check

**Verification:**
- Check backend logs for "Fresh posture data submitted and processed"
- Check device's posture history (should show new entry)
- Check access logs for the access request
- Verify JWT token is issued (if compliant) or access denied (if non-compliant)

**Note:** This requires:
- A resource/policy to be configured in the system
- User to have proper authentication token
- Device to be linked to the user

---

### 7. Device Re-Enrollment

**Test Steps:**
1. Device is enrolled (can be pending, active, or rejected)
2. On the device, run:
   ```powershell
   python -m dpa.cli.enroll_cli
   ```
3. When prompted "Do you want to re-enroll?", type "yes"
4. Enter a new enrollment code when prompted

**Expected Results:**
- Previous enrollment is automatically cleaned up (local file removed)
- Device is deleted from backend database (if pending/rejected)
- New enrollment proceeds with the new code
- TPM key can be reused or re-initialized

**Verification:**
- Check `C:\ProgramData\ZTNA\enrollment.json` is updated with new device ID
- Check backend database: old device is removed (if pending/rejected)
- New enrollment completes successfully

**Note:** 
- Re-enrollment automatically handles cleanup of previous enrollment
- Active devices cannot be re-enrolled via DPA (security measure). Admin must delete them first.
- There is no standalone "unenroll" command - only re-enrollment is available

---

### 8. Device Rejection

**Test Steps:**
1. Enroll a new device (or use existing pending device)
2. Admin logs into frontend
3. Navigate to "Devices" → "Pending Devices"
4. Find the device
5. Click "Reject"
6. Enter rejection reason
7. Click "Reject Device"

**Expected Results:**
- Device status changes from "pending" to "rejected"
- Device can be re-enrolled by DPA agent (which cleans up previous enrollment)
- Audit log entry created

**Verification:**
- Check device status in frontend
- Check audit logs for "device_rejected" action
- Device can be re-enrolled by DPA (which removes previous enrollment)

---

## Testing Order Recommendation

1. **Device Enrollment** ✅ (Already tested)
2. **Posture Scheduler** ✅ (Already tested)
3. **Device Approval & User Binding** (Next to test)
4. **Role Revocation** (Test after approval)
5. **Role Restoration** (Test after revocation)
6. **Access Request with Posture** (Requires policies/resources configured)
7. **Device Re-Enrollment** (Can test anytime)
8. **Device Rejection** (Can test anytime)

---

## Quick Test Commands

### Check Device Status
```powershell
# On device
python -m dpa.cli.enroll_cli
# Will show if enrolled and device ID
```

### Manually Submit Posture Report
```powershell
# On device
python -m dpa.start_posture_scheduler
# Wait for first report, then Ctrl+C
```

### Request Resource Access
```powershell
# On device (requires JWT token)
python -m dpa.cli.request_access_cli \
  --device-id <ID> \
  --resource "test-resource" \
  --auth-token <TOKEN>
```

### Check Backend Logs
```bash
cd infra
docker-compose logs backend --tail 50 | grep -i "posture\|compliance\|role"
```

---

## Common Issues & Solutions

### Issue: Role not revoked/restored
**Solution:** Check backend logs for Keycloak API errors. Verify Keycloak service is running and accessible.

### Issue: Access request fails
**Solution:** 
- Verify JWT token is valid and not expired
- Check device is linked to user
- Verify policies/resources are configured
- Check device is active and enrolled

### Issue: Posture not updating
**Solution:**
- Check DPA is running and can reach backend
- Verify device is approved (active status)
- Check signature verification is passing
- Review backend logs for errors

---

## Next Steps After Testing

Once all tests pass:
1. Document any issues found
2. Update configuration if needed
3. Create production deployment guide
4. Set up monitoring/alerts for compliance violations

