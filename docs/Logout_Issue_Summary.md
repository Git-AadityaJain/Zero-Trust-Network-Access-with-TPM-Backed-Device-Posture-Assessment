# Keycloak Logout Issue - Summary & Solution

## Issue Description

**Symptom**: HTTP 400 Bad Request when attempting to logout
- Logout URL: `https://609b9c24fbd6.ngrok-free.app/auth/realms/master/protocol/openid-connect/logout`
- Error in console: `Failed to load resource: the server responded with a status of 400`
- Keycloak logs show: `REFRESH_TOKEN_ERROR` with `invalid_token`

## Root Cause

The **Post Logout Redirect URI** is not properly configured in the active Keycloak instance, even though it exists in the `realm-export.json` file.

**Required Configuration:**
- **Attribute**: `post.logout.redirect.uris`
- **Value**: `https://609b9c24fbd6.ngrok-free.app/login`
- **Location**: Keycloak Admin Console → Clients → admin-frontend → Settings → Advanced Settings

## Quick Fix Options

### Option 1: Via Keycloak Admin Console (Recommended)

1. **Access Keycloak Admin Console**
   ```
   https://609b9c24fbd6.ngrok-free.app/auth/admin
   ```

2. **Navigate to Client Settings**
   - Realm: `master`
   - Clients → `admin-frontend` → Settings tab

3. **Configure Post Logout Redirect URIs**
   - Scroll to **Advanced Settings** section
   - Find **Post Logout Redirect URIs** field (or look for `post.logout.redirect.uris` in attributes)
   - Add: `https://609b9c24fbd6.ngrok-free.app/login`
   - Click **Save**

4. **Verify Configuration**
   - Ensure the URI is saved
   - Test logout functionality

### Option 2: Via Python Script

Run the provided script to automatically update the configuration:

```bash
# Set environment variables (if needed)
export KEYCLOAK_URL="https://609b9c24fbd6.ngrok-free.app/auth"
export KEYCLOAK_ADMIN_USER="admin"
export KEYCLOAK_ADMIN_PASSWORD="adminsecure123"

# Run the script
python scripts/update_keycloak_logout_uris.py
```

### Option 3: Via Keycloak REST API

```bash
# Get admin token
ADMIN_TOKEN=$(curl -X POST "https://609b9c24fbd6.ngrok-free.app/auth/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=YOUR_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Get client UUID
CLIENT_UUID=$(curl -X GET "https://609b9c24fbd6.ngrok-free.app/auth/admin/realms/master/clients?clientId=admin-frontend" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')

# Get current config
curl -X GET "https://609b9c24fbd6.ngrok-free.app/auth/admin/realms/master/clients/$CLIENT_UUID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" > client_config.json

# Update attributes (edit client_config.json to add post.logout.redirect.uris)
# Then PUT it back
curl -X PUT "https://609b9c24fbd6.ngrok-free.app/auth/admin/realms/master/clients/$CLIENT_UUID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d @client_config.json
```

## Required Configuration Checklist

### For `admin-frontend` Client:

- [x] **Client ID**: `admin-frontend`
- [x] **Access Type**: Public (not Confidential)
- [x] **Valid Redirect URIs**: Must include `https://609b9c24fbd6.ngrok-free.app/callback`
- [x] **Web Origins**: Must include `https://609b9c24fbd6.ngrok-free.app`
- [ ] **Post Logout Redirect URIs**: **MUST INCLUDE** `https://609b9c24fbd6.ngrok-free.app/login` ⚠️

### Current Status (from realm-export.json):

✅ **Redirect URIs**: Configured
✅ **Web Origins**: Configured
✅ **Post Logout Redirect URIs**: Configured in export file
❌ **Active in Keycloak**: **NEEDS VERIFICATION/FIX**

## Verification Steps

After updating the configuration:

1. **Check Keycloak Admin Console**
   - Verify `post.logout.redirect.uris` attribute exists
   - Verify it includes the ngrok URL

2. **Test Logout**
   - Login to the application
   - Click logout
   - Should redirect to `/login` without 400 error

3. **Check Browser Console**
   - Should not see 400 errors
   - Should see successful redirect

4. **Check Keycloak Logs**
   - Should not see `REFRESH_TOKEN_ERROR`
   - Should see successful logout

## Additional Notes

### Why This Happens

- The `realm-export.json` file contains the configuration, but it's only active if the realm was imported from that file
- If Keycloak was configured manually or through a different method, the export file may not reflect the active configuration
- The attribute `post.logout.redirect.uris` must be explicitly set in Keycloak for logout to work

### Logout URL Parameters

The logout URL requires these parameters:
- `id_token_hint`: The ID token (optional but recommended)
- `post_logout_redirect_uri`: Must match exactly what's configured in Keycloak
- `client_id`: Required when using `post_logout_redirect_uri`

### Common Mistakes

1. **URI Mismatch**: The URI must match exactly (including protocol, domain, path)
2. **Missing Attribute**: The `post.logout.redirect.uris` attribute must exist
3. **Wrong Client**: Ensure you're configuring the correct client (`admin-frontend`)
4. **Wrong Realm**: Ensure you're in the `master` realm

## Related Files

- **Configuration Guide**: `docs/Keycloak_Logout_Configuration_Guide.md`
- **Update Script**: `scripts/update_keycloak_logout_uris.py`
- **Realm Export**: `realm-export.json`
- **Logout Service**: `frontend/src/services/oidcService.js` (lines 358-419)

## Next Steps

1. ✅ Update Keycloak configuration (choose one of the options above)
2. ✅ Verify configuration is saved
3. ✅ Test logout functionality
4. ✅ Monitor for any additional errors

If issues persist after configuration update, check:
- Keycloak server logs for detailed error messages
- Browser network tab for exact error response
- Token expiration times
- Client authentication method (should be Public, not Confidential)

