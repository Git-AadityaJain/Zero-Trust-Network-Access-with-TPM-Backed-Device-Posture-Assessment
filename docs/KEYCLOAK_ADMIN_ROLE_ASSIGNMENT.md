# Keycloak Service Account - Admin Role Assignment

## Current Status

✅ **Service Account Has Required Permissions**

The service account (`ZTNA-Platform-realm`) has the following roles:
- `manage-users` - Allows creating, updating, deleting users and **assigning roles**
- `view-users` - View user details
- `query-users` - Search users
- `manage-realm` - General realm management
- `view-realm` - View realm settings

## Can Service Account Assign Admin Role?

**YES** - The service account **should** be able to assign the "admin" role because:
1. It has `manage-users` permission
2. `manage-users` allows assigning **any** realm-level role, including "admin"
3. The admin role exists and is accessible

## If You're Getting 403 Errors

If you encounter a 403 error when trying to assign the admin role, check:

### 1. Verify Service Account Permissions
```bash
docker exec ztna-backend python /app/scripts/check_service_account_roles_in_keycloak.py
```

### 2. Check if Admin Role Exists
The admin role should exist in the realm. Verify:
```bash
# Via Keycloak Admin Console
# Realm → Roles → Realm roles → Look for "admin"
```

### 3. Keycloak Fine-Grained Permissions

Some Keycloak configurations use fine-grained permissions that might restrict admin role assignment. Check:

**In Keycloak Admin Console:**
1. Go to: **Realm Settings → Roles → Realm roles → admin**
2. Check **Permissions** tab
3. Verify that role assignment is not restricted

### 4. Composite Roles

If the "admin" role is a composite role (contains other roles), ensure:
- All composite roles exist
- Service account has permission to assign composite roles

### 5. Alternative: Use Full Admin Account

If the service account cannot assign admin roles due to Keycloak restrictions, you can:

**Option A: Assign Admin Role Manually**
1. Create user via backend (this works)
2. Manually assign "admin" role via Keycloak Admin Console
3. Device will still be linked to user

**Option B: Grant Additional Permissions**
Add `realm-admin` role to service account (if available):
```bash
# This would require updating the assignment script
# to include realm-admin role
```

## Testing Admin Role Assignment

To test if the service account can assign admin role:

```bash
docker exec ztna-backend python /app/scripts/test_admin_role_assignment.py
```

## Workaround: Two-Step Process

If service account cannot assign admin role:

1. **Create user with device** (via device approval):
   - User is created
   - Device is linked
   - User gets "dpa-device" role

2. **Manually assign admin role**:
   - Login to Keycloak Admin Console
   - Go to Users → Find user → Role Mappings
   - Assign "admin" role

## Recommendation

The service account **should** work for assigning admin roles. If it doesn't:

1. **Check Keycloak logs** for specific error messages
2. **Verify fine-grained permissions** in Keycloak
3. **Test manually** via Keycloak Admin Console
4. **Use workaround** if needed (manual assignment)

## Current Implementation

The backend code at `backend/app/routers/device.py` (line 268-272) attempts to assign roles:

```python
if approval_data.assign_roles:
    await keycloak_service.assign_realm_roles_to_user(
        user_id=keycloak_user_id,
        role_names=approval_data.assign_roles
    )
```

This should work if:
- Service account has `manage-users` permission ✅
- Admin role exists ✅
- No fine-grained restrictions ❓

If it fails, the error will be logged and the device approval will fail with a Keycloak error.

