# Quick Test Guide: Single-Session-Per-User

## Quick Manual Test (5 minutes)

### Test Steps

1. **Open Browser A (Chrome)**
   ```
   - Go to: https://unimplied-untranscendental-denita.ngrok-free.dev
   - Click Login
   - Enter credentials: admin-user / <password>
   - Verify: You see the dashboard
   ```

2. **Open Browser B (Firefox or Incognito)**
   ```
   - Go to: https://unimplied-untranscendental-denita.ngrok-free.dev
   - Click Login
   - Enter SAME credentials: admin-user / <password>
   - Verify: You see the dashboard
   ```

3. **Go Back to Browser A**
   ```
   - Refresh the page (F5)
   - Expected: You are redirected to login page
   - This means Browser A session was terminated ✅
   ```

4. **Check Browser B**
   ```
   - Refresh the page (F5)
   - Expected: You are still logged in
   - This means Browser B session is still active ✅
   ```

## Success Criteria

✅ **Feature works if:**
- Browser A gets logged out after Browser B logs in
- Browser B remains logged in
- Only one session is active at a time

## Check Backend Logs

Look for these messages in backend logs:
```
INFO: Enforced single session for user <user_id>: logged out X of Y sessions
```

## Check Browser Console

Open DevTools (F12) > Console, look for:
```
Enforced single session: logged out X other session(s)
```

## If It Doesn't Work

1. Check browser console for errors
2. Check backend logs for Keycloak errors
3. Verify the frontend is calling `/api/session/enforce-single`
4. Check network tab in DevTools for the API call


