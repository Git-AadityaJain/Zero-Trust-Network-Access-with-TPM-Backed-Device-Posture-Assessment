# Keycloak Logout Configuration Guide

## Problem Analysis

The logout endpoint is returning **HTTP 400 Bad Request** with the following symptoms:
- Logout URL: `/auth/realms/master/protocol/openid-connect/logout`
- Parameters: `id_token_hint`, `post_logout_redirect_uri`, `client_id`
- Error: Keycloak rejects the logout request

## Root Causes

### 1. **Post Logout Redirect URI Not Configured in Keycloak**
The `post_logout_redirect_uri` parameter must be **exactly** configured in Keycloak client settings. Even if it's in the export file, it needs to be active in the running Keycloak instance.

### 2. **Client Authentication Method Mismatch**
The client is configured as:
- `publicClient: true` (correct for PKCE flow)
- `clientAuthenticatorType: "client-secret"` (incorrect - should not be used for public clients)

### 3. **Invalid or Expired ID Token**
The ID token might be expired or invalid when logout is called.

## Required Keycloak Configuration

### For `admin-frontend` Client in `master` Realm:

#### 1. **Post Logout Redirect URIs** (CRITICAL)
Navigate to: **Clients → admin-frontend → Settings → Advanced Settings**

Or via Client Attributes:
- **Attribute Name**: `post.logout.redirect.uris`
- **Attribute Value**: Comma-separated list of allowed logout redirect URIs:
  ```
  http://localhost:3000/login,http://localhost/login,http://152.58.31.27/login,https://b64e34aa6da9.ngrok-free.app/login,https://609b9c24fbd6.ngrok-free.app/login
  ```

**Current Required Value:**
```
https://609b9c24fbd6.ngrok-free.app/login
```

#### 2. **Client Settings Verification**

**Access Type / Client authentication:**
- ✅ Should be: **Public** (not Confidential)
- ❌ Should NOT have: Client Secret configured

**Valid Redirect URIs:**
- Must include: `https://609b9c24fbd6.ngrok-free.app/callback`

**Web Origins:**
- Must include: `https://609b9c24fbd6.ngrok-free.app`

**Advanced Settings:**
- **Access Token Lifespan**: Default (or as needed)
- **ID Token Lifespan**: Default (or as needed)
- **PKCE Code Challenge Method**: `S256` ✅

## Step-by-Step Configuration in Keycloak Admin Console

### Option 1: Via Admin Console UI

1. **Login to Keycloak Admin Console**
   - URL: `https://609b9c24fbd6.ngrok-free.app/auth/admin`
   - Realm: `master`

2. **Navigate to Client Settings**
   - Go to: **Clients** → **admin-frontend**

3. **Configure Post Logout Redirect URIs**
   - Click on **Settings** tab
   - Scroll down to **Advanced Settings** section
   - Find **Post Logout Redirect URIs** field
   - Add: `https://609b9c24fbd6.ngrok-free.app/login`
   - Click **Save**

4. **Verify Client Type**
   - Ensure **Access Type** is set to **public**
   - **Client authentication** should be **Off**

5. **Verify Redirect URIs**
   - **Valid Redirect URIs** should include:
     - `https://609b9c24fbd6.ngrok-free.app/callback`

6. **Verify Web Origins**
   - **Web Origins** should include:
     - `https://609b9c24fbd6.ngrok-free.app`
   - Or use `+` to allow all origins (less secure)

### Option 2: Via Keycloak Admin REST API

```bash
# Get admin token
ADMIN_TOKEN=$(curl -X POST "https://609b9c24fbd6.ngrok-free.app/auth/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=YOUR_ADMIN_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Get client ID (internal UUID)
CLIENT_ID=$(curl -X GET "https://609b9c24fbd6.ngrok-free.app/auth/admin/realms/master/clients?clientId=admin-frontend" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq -r '.[0].id')

# Update client with post logout redirect URIs
curl -X PUT "https://609b9c24fbd6.ngrok-free.app/auth/admin/realms/master/clients/$CLIENT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "post.logout.redirect.uris": "http://localhost:3000/login,http://localhost/login,http://152.58.31.27/login,https://b64e34aa6da9.ngrok-free.app/login,https://609b9c24fbd6.ngrok-free.app/login"
    }
  }'
```

### Option 3: Update Realm Export and Re-import

If you have access to the realm export file:

1. **Edit `realm-export.json`**
   - Find the `admin-frontend` client configuration
   - Ensure `attributes.post.logout.redirect.uris` includes the ngrok URL

2. **Re-import the realm**
   ```bash
   # Via Keycloak Admin Console: Import → Select realm-export.json → Import
   ```

## Verification Steps

### 1. Check Current Configuration
```bash
# Get admin token and check client configuration
curl -X GET "https://609b9c24fbd6.ngrok-free.app/auth/admin/realms/master/clients?clientId=admin-frontend" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.[0].attributes."post.logout.redirect.uris"'
```

### 2. Test Logout URL
The logout URL should work without 400 error:
```
https://609b9c24fbd6.ngrok-free.app/auth/realms/master/protocol/openid-connect/logout?id_token_hint=<ID_TOKEN>&post_logout_redirect_uri=https%3A%2F%2F609b9c24fbd6.ngrok-free.app%2Flogin&client_id=admin-frontend
```

### 3. Check Keycloak Logs
After attempting logout, check for:
- ✅ Successful logout: Should redirect to `/login`
- ❌ Error 400: Configuration issue
- ❌ Error 401: Authentication issue
- ❌ Error 403: Permission issue

## Common Issues and Solutions

### Issue 1: "Invalid redirect URI"
**Solution**: Ensure the `post_logout_redirect_uri` exactly matches one of the configured URIs in Keycloak (case-sensitive, must include protocol).

### Issue 2: "Client authentication failed"
**Solution**: For public clients, ensure:
- `publicClient: true`
- No client secret configured
- `clientAuthenticatorType` should not be `client-secret` for public clients

### Issue 3: "Invalid token"
**Solution**: 
- Ensure ID token is not expired
- Verify token was issued by the same Keycloak instance
- Check token signature is valid

### Issue 4: "Missing required parameter"
**Solution**: Ensure all three parameters are present:
- `id_token_hint` (optional but recommended)
- `post_logout_redirect_uri` (required when using redirect)
- `client_id` (required when using `post_logout_redirect_uri`)

## Current Configuration Status

Based on `realm-export.json`:

✅ **Redirect URIs**: Configured
✅ **Web Origins**: Configured  
✅ **Post Logout Redirect URIs**: Configured in export file
❓ **Active in Keycloak**: Needs verification

## Next Steps

1. **Verify configuration in Keycloak Admin Console**
   - Check if `post.logout.redirect.uris` attribute exists and includes the ngrok URL

2. **If missing, add it via Admin Console**
   - Navigate to Clients → admin-frontend → Settings → Advanced Settings
   - Add: `https://609b9c24fbd6.ngrok-free.app/login`

3. **Test logout flow**
   - Login → Logout → Should redirect to `/login` without errors

4. **Check Keycloak logs**
   - Look for any additional error messages that might indicate other issues

## Additional Notes

- The `post.logout.redirect.uris` attribute accepts comma-separated values
- URIs must match exactly (including protocol, domain, and path)
- For development, you can use `+` to allow all origins (not recommended for production)
- The `id_token_hint` helps Keycloak identify the session but is optional
- When `post_logout_redirect_uri` is used, `client_id` is required

