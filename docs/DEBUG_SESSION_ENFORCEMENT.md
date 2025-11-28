# Debugging Session Enforcement Feature

## Current Status
The feature code is in place, but logs are not appearing in the browser console.

## Added Debug Logging

I've added extensive logging to help identify the issue. After rebuilding and restarting, you should see:

### Expected Console Logs (in order):

1. `🔵 handleCallback result received: result exists`
2. `🔵 Result structure: ['access_token', 'userInfo']`
3. `🔵 Checking result structure: { hasResult: true, hasUserInfo: true, hasAccessToken: true }`
4. `Authentication successful, enforcing single session`
5. `Calling enforce-single endpoint: https://.../api/session/enforce-single`
6. `Enforce-single response status: 200`
7. `✅ Enforced single session: logged out X other session(s)`

## What to Check

### If you see NO logs at all:
- The callback handler might not be executing
- Check if you're actually going through the callback flow
- Verify the URL contains `?code=...` parameter

### If you see logs 1-3 but NOT 4:
- The result structure check is failing
- Check what `result` actually contains
- The condition `result && result.userInfo && result.access_token` is false

### If you see logs 1-4 but NOT 5:
- There's an error before the fetch call
- Check for JavaScript errors in console

### If you see logs 1-5 but NOT 6-7:
- The API call is failing
- Check Network tab for the request
- Look for CORS errors or 404/500 responses

## Testing Steps

1. **Clear browser cache** or use incognito
2. **Open DevTools** (F12) before logging in
3. **Go to Console tab**
4. **Log in**
5. **Watch for the blue circle logs** (🔵)
6. **Check what logs appear** and report back

## Common Issues

### Issue: No logs appear
**Possible causes:**
- Frontend not rebuilt properly
- Code not reaching callback handler
- Different code path being taken

**Fix:**
- Verify code in container: `docker exec ztna-frontend cat /app/src/pages/CallbackPage.jsx | grep "handleCallback result"`
- Rebuild frontend: `cd infra && docker-compose build --no-cache frontend`
- Restart: `docker restart ztna-frontend`

### Issue: Result structure wrong
**Possible causes:**
- `handleCallback` returning different structure
- Early return happening

**Fix:**
- Check `frontend/src/context/AuthContext.jsx` - `handleCallback` should return `{ access_token, userInfo }`
- Check `frontend/src/services/oidcService.js` - `handleCallback` should return same structure

### Issue: API call fails
**Possible causes:**
- Wrong URL
- CORS issue
- Backend not running
- Endpoint not registered

**Fix:**
- Check Network tab for actual request
- Verify backend is running: `docker ps | grep backend`
- Check endpoint exists: `docker logs ztna-backend | grep "session"`

## Next Steps

After testing with the new logging:
1. Report which logs you see (1-7)
2. Share any errors from console
3. Share Network tab screenshot if API call fails
4. Share backend logs if available

This will help identify exactly where the issue is.

