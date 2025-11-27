# Creating an Admin User with DPA Device

## Overview

This guide explains how to create a second admin user and bind it to a DPA (Device Posture Agent) device.

## Process

### Step 1: Enroll Device with DPA

On the machine where you want to bind the admin user:

```bash
# Enroll the device
python dpa/cli/enroll_cli.py --enrollment-code YOUR_ENROLLMENT_CODE
```

This will:
- Initialize TPM key
- Submit device enrollment request
- Create a pending device in the backend

### Step 2: Approve Device and Create Admin User

As an existing admin, approve the device and create the new admin user:

**Via Admin Dashboard:**
1. Navigate to Devices page
2. Find the pending device
3. Click "Approve"
4. Fill in the form:
   - **Username**: Desired username (e.g., `admin2`)
   - **Email**: User's email address
   - **First Name**: User's first name
   - **Last Name**: User's last name
   - **Temporary Password**: Initial password (user will need to change this)
   - **Assign Roles**: `["admin", "dpa-device"]` ⚠️ **Important: Include "admin" role**

**Via API (if using curl/Postman):**

```bash
PATCH /api/devices/{device_id}/approve
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "username": "admin2",
  "email": "admin2@example.com",
  "first_name": "Admin",
  "last_name": "Two",
  "temporary_password": "SecurePassword123!",
  "assign_roles": ["admin", "dpa-device"]
}
```

### Step 3: Verify Setup

1. **Check Device Status**:
   - Device should be "active"
   - Device should be linked to the new user

2. **Check User in Keycloak**:
   - User should exist in Keycloak
   - User should have "admin" and "dpa-device" roles

3. **Login as New Admin**:
   - Use the temporary password
   - Change password on first login
   - Should have admin access

4. **Verify DPA Connection**:
   - Start DPA posture scheduler on the device
   - Verify posture reports are being submitted
   - Check device state in User Dashboard

## Important Notes

### Role Assignment

When approving the device, make sure to include **both** roles:
- `"admin"` - For admin access to the system
- `"dpa-device"` - For device posture agent functionality

**Example:**
```json
{
  "assign_roles": ["admin", "dpa-device"]
}
```

### Alternative: Assign Device to Existing Admin User

If you already have an admin user and just want to bind a device:

1. **Enroll device** (same as Step 1)
2. **Assign device to existing user**:

```bash
PATCH /api/devices/{device_id}/assign
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "user_id": <existing_admin_user_id>
}
```

This will:
- Link device to existing user
- Update device status to "active"
- **Note**: This does NOT assign roles - user must already have them

## Troubleshooting

### Issue: "Failed to assign roles: 403"

**Solution**: Run the service account roles script:
```bash
docker exec ztna-backend python /app/scripts/assign_service_account_roles.py
```

### Issue: Device not showing in user's devices

**Check**:
- Device status is "active"
- Device is linked to user (`user_id` is set)
- User is logged in with correct account

### Issue: Admin role not working

**Check**:
- User has "admin" role in Keycloak
- Role is assigned at realm level (not client level)
- User token includes admin role in claims

### Issue: DPA not reporting

**Check**:
- DPA posture scheduler is running
- Device is enrolled and active
- TPM key is initialized
- Backend is accessible from device

## Verification Commands

### Check Device Status
```bash
GET /api/devices/{device_id}
Authorization: Bearer <admin_token>
```

### Check User Roles
```bash
GET /api/users/{user_id}
Authorization: Bearer <admin_token>
```

### Check Device Posture
```bash
GET /api/posture/device/{device_id}/latest
Authorization: Bearer <admin_token>
```

## Next Steps

After creating the admin user:
1. **Change Password**: User should change temporary password on first login
2. **Start DPA**: Run `python dpa/start_posture_scheduler.py` on the device
3. **Verify Access**: Login and verify admin dashboard access
4. **Test Device State**: Check that device state is reported correctly

