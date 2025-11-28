# Single-Session Feature Testing Checklist

## ✅ Pre-Test Verification

1. **Backend Endpoint Exists**
   - [ ] Check: `docker logs ztna-backend | grep "session"`
   - [ ] Verify router is registered in `backend/app/main.py`
   - [ ] Endpoint should be: `POST /api/session/enforce-single`

2. **Frontend Code Updated**
   - [ ] Check: `docker exec ztna-frontend cat /app/src/pages/CallbackPage.jsx | grep "enforce-single"`
   - [ ] Should see the fetch call to `/api/session/enforce-single`

3. **Frontend Rebuilt**
   - [ ] Run: `cd infra && docker-compose build frontend`
   - [ ] Run: `docker restart ztna-frontend`

## 🧪 Test Steps

### Step 1: Browser A Login
1. Open Browser A (Chrome)
2. Navigate to frontend URL
3. Log in with test user
4. **Check Browser Console (F12)**
   - Should see: `"Authentication successful, enforcing single session"`
   - Should see: `"Calling enforce-single endpoint: ..."`
   - Should see: `"Enforce-single response status: 200"` or error

### Step 2: Browser B Login
1. Open Browser B (Firefox/Incognito)
2. Navigate to frontend URL
3. Log in with **SAME** user
4. **Check Browser Console (F12)**
   - Should see: `"✅ Enforced single session: logged out 1 other session(s)"`

### Step 3: Verify Session Termination
1. Go back to Browser A
2. Refresh page (F5)
3. **Expected**: Redirected to login page
4. **If NOT redirected**: Feature is not working

### Step 4: Verify Active Session
1. Go to Browser B
2. Refresh page (F5)
3. **Expected**: Still logged in
4. **If logged out**: Feature is working but wrong session was kept

## 🔍 Debugging

### If No Console Messages
- **Problem**: Frontend code not updated
- **Fix**: Rebuild frontend container

### If 404 Error
- **Problem**: Backend endpoint not registered
- **Fix**: Check `backend/app/main.py` includes session router

### If 401 Error
- **Problem**: Token invalid or expired
- **Fix**: This is normal - token might be expired, but should still work

### If 500 Error
- **Problem**: Backend error
- **Fix**: Check backend logs: `docker logs ztna-backend --tail 50`

### If Sessions Not Terminated
- **Problem**: Keycloak API issue or session ID not in token
- **Fix**: Check backend logs for Keycloak errors

## 📊 Expected Logs

### Browser Console
```
Authentication successful, enforcing single session
Calling enforce-single endpoint: https://.../api/session/enforce-single
Enforce-single response status: 200
✅ Enforced single session: logged out 1 other session(s)
```

### Backend Logs
```
INFO: Enforced single session for user <user_id>: logged out 1 of 2 sessions
```

### Nginx Logs
```
POST /api/session/enforce-single HTTP/1.1" 200
```

## 🚨 Common Issues

1. **API URL Wrong**
   - Check: `REACT_APP_API_URL` in frontend container
   - Should be: `https://unimplied-untranscendental-denita.ngrok-free.dev/api`

2. **Double /api/api**
   - Fixed in latest code
   - Rebuild frontend if still seeing this

3. **Redirect Happens Too Fast**
   - Code uses async IIFE, so it doesn't block
   - This is intentional - session enforcement happens in background

4. **No Session ID in Token**
   - Keycloak should include `sid` in JWT
   - If missing, all sessions will be logged out (user must re-login)

