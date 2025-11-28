# Single-Session-Per-User Enforcement

## Overview

This document describes the single-session-per-user security feature that limits each user to only one active session at a time. When a user logs in from a new device or browser, all their other active sessions are automatically terminated.

## How It Works

### Architecture

1. **Frontend (Callback Handler)**
   - After successful OIDC authentication, the frontend calls the backend API endpoint
   - Location: `frontend/src/pages/CallbackPage.jsx`
   - Endpoint: `POST /api/session/enforce-single`

2. **Backend (Session Management)**
   - The backend endpoint uses Keycloak Admin API to:
     - Get all active sessions for the user
     - Identify the current session (from JWT token)
     - Logout all other sessions
   - Location: `backend/app/routers/session.py`

3. **Keycloak Service**
   - Provides methods to manage user sessions
   - Methods:
     - `get_user_sessions(user_id)` - Get all active sessions
     - `logout_user_session(user_id, session_id)` - Logout specific session
     - `logout_other_user_sessions(user_id, current_session_id)` - Logout all except current
   - Location: `backend/app/services/keycloak_service.py`

## API Endpoints

### POST `/api/session/enforce-single`

Enforces single-session-per-user by logging out all other sessions.

**Authentication:** Required (Bearer token)

**Request:**
```http
POST /api/session/enforce-single
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "8c4f3028f-3e58-4549-ad9d-612005d163e1",
  "session_count": 3,
  "logged_out_count": 2,
  "message": "Logged out 2 other session(s). Only one session is now active."
}
```

### GET `/api/session/info`

Get information about current user's active sessions.

**Authentication:** Required (Bearer token)

**Request:**
```http
GET /api/session/info
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": "8c4f3028f-3e58-4549-ad9d-612005d163e1",
  "session_count": 1,
  "logged_out_count": 0,
  "message": "User has 1 active session(s)"
}
```

## Implementation Details

### Session ID Extraction

The session ID (`sid`) is extracted from the JWT token payload. Keycloak includes the session ID in the token when the session is created.

**Token Payload Structure:**
```json
{
  "sub": "user-id",
  "sid": "session-id",
  "exp": 1234567890,
  ...
}
```

### Session Logout Process

1. User logs in successfully
2. Frontend receives access token and user info
3. Frontend calls `POST /api/session/enforce-single` with the access token
4. Backend extracts user ID and session ID from token
5. Backend queries Keycloak for all user sessions
6. Backend logs out all sessions except the current one
7. User continues with only the new session active

### Error Handling

- If session ID cannot be extracted from token, all sessions are logged out (user must re-login)
- If Keycloak API fails, the error is logged but login continues
- Network errors are handled gracefully to not block the login flow

## Security Benefits

1. **Prevents Concurrent Access**
   - Users cannot be logged in from multiple devices simultaneously
   - Reduces risk of unauthorized access if credentials are compromised

2. **Session Hijacking Protection**
   - If a session is hijacked, logging in from a legitimate device terminates the hijacked session
   - Forces attackers to maintain continuous access

3. **Compliance**
   - Helps meet security requirements for single-session enforcement
   - Provides audit trail of session terminations

## Configuration

### Keycloak Settings

No special Keycloak configuration is required. The feature uses Keycloak's standard session management API.

### Backend Configuration

The backend uses the existing Keycloak service configuration:
- `OIDC_ISSUER` - Keycloak realm URL
- `OIDC_CLIENT_ID` - Service account client ID
- `OIDC_CLIENT_SECRET` - Service account secret

### Frontend Configuration

The frontend uses the existing API URL:
- `REACT_APP_API_URL` - Backend API URL

## Testing

### Manual Testing

1. Log in from Browser A
2. Verify you can access the dashboard
3. Log in from Browser B (same user)
4. Verify Browser A session is terminated (refresh page, should redirect to login)
5. Verify Browser B session is active

### API Testing

```bash
# Get session info
curl -X GET "https://your-api.com/api/session/info" \
  -H "Authorization: Bearer <token>"

# Enforce single session
curl -X POST "https://your-api.com/api/session/enforce-single" \
  -H "Authorization: Bearer <token>"
```

## Troubleshooting

### Sessions Not Being Terminated

1. Check backend logs for Keycloak API errors
2. Verify service account has proper permissions
3. Check that session ID is present in JWT token
4. Verify Keycloak Admin API is accessible

### Frontend Not Calling Endpoint

1. Check browser console for errors
2. Verify `REACT_APP_API_URL` is set correctly
3. Check network tab for API call
4. Verify access token is valid

### Multiple Sessions Still Active

1. Verify the enforce-single endpoint is being called
2. Check Keycloak logs for session logout events
3. Verify user ID and session ID are correct
4. Check for timing issues (sessions may take a moment to terminate)

## Future Enhancements

1. **Configurable Policy**
   - Allow admins to configure session limits per user/role
   - Support for "allow N concurrent sessions"

2. **Session Notifications**
   - Notify users when their session is terminated
   - Email/SMS alerts for new logins

3. **Session History**
   - Track session creation and termination events
   - Provide audit logs for compliance

4. **Device Management**
   - Allow users to view and manage active sessions
   - Support for "trusted devices" that don't terminate other sessions

## Related Files

- `backend/app/routers/session.py` - Session management endpoints
- `backend/app/services/keycloak_service.py` - Keycloak session operations
- `backend/app/security/oidc.py` - Token validation and session ID extraction
- `frontend/src/pages/CallbackPage.jsx` - Frontend callback handler
- `scripts/enable_single_session.py` - Configuration script

