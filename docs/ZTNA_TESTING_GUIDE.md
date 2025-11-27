# ZTNA Architecture Testing Guide

## Overview

This guide provides step-by-step instructions for testing the new ZTNA architecture where:
- Browser only communicates with backend (not DPA)
- DPA agent continuously reports posture to backend
- Backend verifies TPM signatures and maintains device state
- Webapp checks device state from backend

## Prerequisites

1. **Backend Services Running**:
   ```bash
   cd backend
   docker-compose up -d  # Or your preferred method
   ```

2. **DPA Agent Running**:
   ```bash
   # Start DPA posture scheduler (reports posture every 5 minutes)
   python dpa/start_posture_scheduler.py
   ```

3. **Frontend Running**:
   ```bash
   cd frontend
   npm start
   ```

4. **Device Enrolled**:
   - Device must be enrolled with TPM key
   - Device must be approved and active
   - Device must have recent posture reports

## Test Flow

### 1. Initial Setup

1. **Enroll a Device** (if not already enrolled):
   ```bash
   python dpa/cli/enroll_cli.py --enrollment-code YOUR_CODE
   ```

2. **Verify Device Enrollment**:
   - Check backend logs for enrollment success
   - Verify device appears in admin dashboard
   - Device status should be "active"

3. **Start DPA Posture Scheduler**:
   ```bash
   python dpa/start_posture_scheduler.py
   ```
   - This will report posture every 5 minutes
   - Check logs to verify posture submissions

### 2. Test Login and Device Verification

1. **Open Frontend**:
   - Navigate to `http://localhost:3000` (or your frontend URL)
   - Click "Login"

2. **Login with Keycloak**:
   - Enter credentials
   - Complete OIDC flow
   - Should redirect to User Dashboard

3. **Verify Policy Decision**:
   - After login, frontend calls `POST /api/access/decision`
   - Check browser console for response
   - Should see policy decision with:
     - `allowed: true/false`
     - `risk_level: "low" | "medium" | "high" | "critical"`
     - `has_dpa: true/false`
     - `tpm_key_match: true/false`
     - `is_compliant: true/false`

4. **Verify Device State Check**:
   - Frontend calls `GET /api/users/me/current-device-state`
   - Should return device state information
   - Check browser console for response

### 3. Test Resource Access

1. **List Resources**:
   - User Dashboard should display available resources
   - Resources are filtered by:
     - User role (admin/user/public)
     - Device compliance
     - TPM key verification

2. **Download Resource**:
   - Click "Download" on a resource
   - Backend verifies:
     - OIDC token valid
     - Device state from DB
     - TPM signature valid
     - Device compliant
   - Should succeed if all checks pass

### 4. Test Compromised Credentials Protection

#### Scenario 1: No Enrolled Device
1. **Create a new user** (or use existing user with no devices)
2. **Login** with that user
3. **Expected Result**:
   - Policy decision: `allowed: false`
   - Risk level: `"high"`
   - Reason: "No enrolled devices found"
   - Resources should not be accessible

#### Scenario 2: Stale Posture
1. **Stop DPA posture scheduler**
2. **Wait 15+ minutes** (or manually update `last_posture_check` in DB)
3. **Login** and try to access resources
4. **Expected Result**:
   - Policy decision: `allowed: false` or `risk_level: "medium"`
   - Reason: "DPA agent not reporting recently"
   - Resources should not be accessible

#### Scenario 3: Invalid TPM Key
1. **Manually change TPM public key** in database (simulate key change)
2. **DPA continues reporting** with old TPM key
3. **Backend verifies signature** → fails
4. **Expected Result**:
   - Policy decision: `allowed: false`
   - Risk level: `"critical"`
   - Reason: "TPM key verification failed"
   - `tpm_key_match: false`

#### Scenario 4: Non-Compliant Device
1. **Manually set device compliance** to false in database
2. **Login** and try to access resources
3. **Expected Result**:
   - Policy decision: `allowed: false`
   - Risk level: `"high"`
   - Reason: "Device is not compliant"
   - Resources should not be accessible

### 5. Test Continuous Posture Reporting

1. **Monitor Backend Logs**:
   ```bash
   docker-compose logs -f ztna-backend
   ```

2. **Watch for Posture Submissions**:
   - Every 5 minutes, DPA should submit posture
   - Backend should verify TPM signature
   - Backend should update device state

3. **Verify Signature Verification**:
   - Check logs for: "Signature verified successfully"
   - If signature fails, check logs for error

4. **Verify Device State Updates**:
   - `last_posture_check` should update
   - `last_seen_at` should update
   - `is_compliant` should reflect current posture

## API Endpoints to Test

### 1. Policy Decision
```bash
POST /api/access/decision
Authorization: Bearer <OIDC_TOKEN>
Content-Type: application/json

{
  "resource": "*",
  "context": {
    "time": "2025-11-27T10:00:00Z",
    "source": "webapp"
  }
}
```

**Expected Response**:
```json
{
  "allowed": true,
  "reason": "Access granted. Device verified and compliant.",
  "has_dpa": true,
  "tpm_key_match": true,
  "is_compliant": true,
  "device_id": 1,
  "device_name": "My Device",
  "risk_level": "low",
  "requires_step_up": false
}
```

### 2. Device State Check
```bash
GET /api/users/me/current-device-state
Authorization: Bearer <OIDC_TOKEN>
```

**Expected Response**:
```json
{
  "has_dpa": true,
  "tpm_key_match": true,
  "is_compliant": true,
  "is_enrolled": true,
  "device_id": 1,
  "device_name": "My Device",
  "device_unique_id": "uuid-here",
  "last_posture_time": "2025-11-27T10:00:00Z",
  "last_seen_at": "2025-11-27T10:00:00Z",
  "compliance_score": 95,
  "violations": null,
  "posture_data": {...},
  "message": "Device is enrolled, compliant, and TPM key matches. Access granted."
}
```

### 3. List Resources
```bash
GET /api/resources/list
Authorization: Bearer <OIDC_TOKEN>
```

**Expected Response**:
```json
{
  "resources": [
    {
      "id": "employee-handbook.pdf",
      "name": "Employee Handbook.pdf",
      "type": "document",
      "size": "1.8 MB",
      "role": "user"
    },
    ...
  ],
  "message": "Resources retrieved successfully"
}
```

### 4. Download Resource
```bash
GET /api/resources/download/{resource_id}
Authorization: Bearer <OIDC_TOKEN>
```

**Expected Response**:
```json
{
  "message": "Download initiated for Employee Handbook.pdf",
  "resource": {...},
  "device_id": "uuid-here",
  "device_name": "My Device",
  "user": "username",
  "note": "This is a demo response..."
}
```

## Troubleshooting

### Issue: "No devices found"
**Solution**: 
- Ensure device is enrolled
- Check device is linked to user account
- Verify device status is "active"

### Issue: "TPM key verification failed"
**Solution**:
- Check latest posture history has `signature_valid: true`
- Verify TPM public key in database matches device's TPM
- Check DPA is using correct TPM key

### Issue: "DPA agent not reporting"
**Solution**:
- Ensure DPA posture scheduler is running
- Check DPA can reach backend API
- Verify device is enrolled
- Check DPA logs for errors

### Issue: "Device is not compliant"
**Solution**:
- Check device posture data
- Review compliance violations
- Ensure device meets security requirements
- Check policy evaluation logs

### Issue: Policy Decision Returns 403
**Solution**:
- Verify OIDC token is valid
- Check user has enrolled devices
- Verify device state in database
- Check backend logs for specific error

## Success Criteria

✅ **Login Flow**:
- User can login with Keycloak
- Policy decision is requested after login
- Device state is checked
- Appropriate UI feedback is shown

✅ **Resource Access**:
- Resources are listed based on device state
- Downloads work when device is verified
- Access is denied when device is not ready

✅ **Security**:
- Compromised credentials cannot access resources
- TPM key verification works correctly
- Device compliance is enforced
- Stale posture is detected

✅ **Continuous Reporting**:
- DPA reports posture every 5 minutes
- Backend verifies signatures
- Device state is updated
- Access decisions reflect current state

## Next Steps

After successful testing:
1. Monitor production logs for policy decisions
2. Set up alerts for critical risk levels
3. Review access logs for suspicious activity
4. Fine-tune policy rules based on usage patterns

