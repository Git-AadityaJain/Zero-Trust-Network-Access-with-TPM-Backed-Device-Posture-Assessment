# Manual Testing Guide: Single-Session-Per-User Feature

## Overview

This guide provides step-by-step instructions for manually testing the single-session-per-user enforcement feature.

## Prerequisites

1. Frontend is running and accessible
2. Backend is running and accessible
3. Keycloak is running and accessible
4. You have a test user account (e.g., `admin-user`)

## Test Scenario 1: Basic Single Session Enforcement

### Step 1: Initial Login (Browser A)

1. Open **Browser A** (e.g., Chrome)
2. Navigate to the frontend URL: `https://unimplied-untranscendental-denita.ngrok-free.dev`
3. Click "Login" or navigate to `/login`
4. Enter credentials:
   - Username: `admin-user` (or your test user)
   - Password: (your password)
5. Complete the login flow
6. **Verify**: You are redirected to the dashboard
7. **Verify**: You can access protected pages

### Step 2: Second Login (Browser B)

1. Open **Browser B** (e.g., Firefox or Chrome Incognito)
2. Navigate to the same frontend URL
3. Click "Login" or navigate to `/login`
4. Enter the **same credentials** as Step 1
5. Complete the login flow
6. **Verify**: You are redirected to the dashboard
7. **Verify**: You can access protected pages

### Step 3: Verify Session Termination (Browser A)

1. Go back to **Browser A**
2. Refresh the page (F5 or Ctrl+R)
3. **Expected Result**: You should be redirected to the login page
4. **Verify**: The session in Browser A has been terminated

### Step 4: Verify Active Session (Browser B)

1. Go to **Browser B**
2. Refresh the page (F5 or Ctrl+R)
3. **Expected Result**: You should still be logged in
4. **Verify**: You can still access the dashboard
5. **Verify**: Only Browser B session is active

## Test Scenario 2: Multiple Concurrent Sessions

### Step 1: Create Multiple Sessions

1. Open **Browser A** and log in
2. Open **Browser B** and log in (same user)
3. Open **Browser C** (or another incognito window) and log in (same user)

### Step 2: Verify Only Last Session Remains

1. Check which browser was used for the **last login**
2. Refresh all three browsers
3. **Expected Result**:
   - The browser used for the last login should still be active
   - The other two browsers should be redirected to login

## Test Scenario 3: API Endpoint Testing

### Step 1: Get Access Token

1. Log in through the frontend
2. Open browser DevTools (F12)
3. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Navigate to **Local Storage** > your domain
5. Copy the `access_token` value

### Step 2: Test Session Info Endpoint

```bash
curl -X GET "https://unimplied-untranscendental-denita.ngrok-free.dev/api/session/info" \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:**
```json
{
  "user_id": "8c4f3028f-3e58-4549-ad9d-612005d163e1",
  "session_count": 1,
  "logged_out_count": 0,
  "message": "User has 1 active session(s)"
}
```

### Step 3: Test Enforce Single Session Endpoint

```bash
curl -X POST "https://unimplied-untranscendental-denita.ngrok-free.dev/api/session/enforce-single" \
  -H "Authorization: Bearer <access_token>"
```

**Expected Response:**
```json
{
  "user_id": "8c4f3028f-3e58-4549-ad9d-612005d163e1",
  "session_count": 1,
  "logged_out_count": 0,
  "message": "User already has only one active session"
}
```

## Test Scenario 4: Using Test Script

### Step 1: Run Test Script

```bash
python scripts/test_single_session.py
```

### Step 2: Follow Prompts

1. Enter username to test (default: `admin-user`)
2. Review current session count
3. Optionally provide access token for API testing

### Step 3: Review Results

The script will:
- Show current active sessions
- Test API endpoints (if token provided)
- Verify session enforcement
- Provide manual testing instructions

## Verification Checklist

### ✅ Frontend Behavior

- [ ] Login works correctly
- [ ] After login, user is redirected to dashboard
- [ ] No errors in browser console
- [ ] Session enforcement happens automatically (no user action needed)

### ✅ Session Termination

- [ ] Old sessions are terminated when new login occurs
- [ ] Terminated sessions redirect to login page
- [ ] Only the most recent session remains active
- [ ] Session termination happens within seconds

### ✅ API Endpoints

- [ ] `GET /api/session/info` returns correct session count
- [ ] `POST /api/session/enforce-single` logs out other sessions
- [ ] API responses include correct user ID and session counts
- [ ] Error handling works correctly

### ✅ Backend Logs

- [ ] Logs show "Enforced single session" messages
- [ ] Session count is logged correctly
- [ ] Logged out count matches expected value
- [ ] No errors in backend logs

### ✅ Keycloak Integration

- [ ] Keycloak Admin API calls succeed
- [ ] Sessions are retrieved correctly
- [ ] Sessions are logged out correctly
- [ ] Session ID is extracted from JWT token

## Troubleshooting

### Issue: Sessions Not Being Terminated

**Symptoms:**
- Multiple browsers remain logged in
- Old sessions don't redirect to login

**Debugging Steps:**
1. Check browser console for errors
2. Check backend logs for Keycloak API errors
3. Verify access token is valid
4. Check if session ID is present in JWT token
5. Verify Keycloak Admin API permissions

**Solution:**
- Ensure service account has proper permissions
- Verify `sid` field is in JWT token
- Check network connectivity to Keycloak

### Issue: API Endpoint Returns 401

**Symptoms:**
- API calls return 401 Unauthorized
- "Invalid or expired token" errors

**Debugging Steps:**
1. Verify access token is not expired
2. Check token format (should be valid JWT)
3. Verify token includes required claims

**Solution:**
- Get a fresh access token by logging in again
- Ensure token is copied completely (no truncation)

### Issue: Session Count Always Shows 1

**Symptoms:**
- Session info always shows 1 session
- No sessions are logged out

**Debugging Steps:**
1. Verify multiple sessions actually exist in Keycloak
2. Check if sessions are from different clients
3. Verify user ID matches across sessions

**Solution:**
- Use Keycloak Admin Console to verify sessions
- Check if sessions are from different clients (may not be visible)
- Ensure testing with same user account

## Expected Behavior Summary

| Action | Expected Result |
|--------|----------------|
| Login from Browser A | Session created, user logged in |
| Login from Browser B (same user) | Browser A session terminated, Browser B active |
| Refresh Browser A | Redirected to login page |
| Refresh Browser B | Still logged in |
| Call enforce-single API | Other sessions logged out |
| Check session info | Shows correct session count |

## Success Criteria

✅ **Feature is working correctly if:**
1. Only one session per user can be active at a time
2. New login automatically terminates old sessions
3. API endpoints return correct information
4. No errors in logs or console
5. User experience is smooth (no noticeable delay)

## Notes

- Session termination happens automatically after login
- No manual action required from users
- The feature works transparently in the background
- Session enforcement is logged for audit purposes


