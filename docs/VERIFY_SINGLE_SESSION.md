# How to Verify Single-Session Feature is Working

## Quick Check: Is the Feature Being Called?

### 1. Check Browser Console

After logging in, open DevTools (F12) > Console and look for:
```
Authentication successful, enforcing single session
Enforced single session: logged out X other session(s)
```

**If you DON'T see these messages:**
- The frontend code might not be updated
- The frontend container needs to be rebuilt

### 2. Check Network Tab

1. Open DevTools (F12) > Network tab
2. Log in
3. Filter by "enforce-single"
4. Look for: `POST /api/session/enforce-single`

**If you DON'T see this request:**
- The frontend is not calling the endpoint
- Check if the frontend container was rebuilt after code changes

### 3. Check Backend Logs

```powershell
docker logs ztna-backend --tail 100 | Select-String -Pattern "session|enforce" -CaseSensitive:$false
```

**Expected logs:**
```
INFO: Enforced single session for user <user_id>: logged out X of Y sessions
```

**If you DON'T see these logs:**
- The endpoint is not being called
- Check frontend code and rebuild

### 4. Check Nginx Logs

```powershell
docker logs ztna-nginx --tail 100 | Select-String -Pattern "/api/session" -CaseSensitive:$false
```

**Expected:**
```
POST /api/session/enforce-single HTTP/1.1" 200
```

## Rebuild Frontend Container

If the feature isn't working, rebuild the frontend:

```bash
cd infra
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

## Manual Test Steps

1. **Browser A**: Log in
2. **Browser B**: Log in (same user)
3. **Browser A**: Refresh → Should redirect to login
4. **Browser B**: Refresh → Should still be logged in

## Troubleshooting

### Issue: No logs in backend
- **Cause**: Frontend not calling endpoint
- **Fix**: Rebuild frontend container

### Issue: 404 on `/api/session/enforce-single`
- **Cause**: Backend router not registered
- **Fix**: Check `backend/app/main.py` includes session router

### Issue: 401 Unauthorized
- **Cause**: Invalid or expired token
- **Fix**: Get fresh token by logging in again

### Issue: Sessions not being terminated
- **Cause**: Session ID not in token, or Keycloak API issue
- **Fix**: Check backend logs for Keycloak errors


