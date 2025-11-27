# Frontend Testing Steps - TPM Device Attestation

## Prerequisites Checklist

Before starting, ensure all services are running:

- [ ] **Backend API** running at `http://localhost:8000`
- [ ] **Keycloak** running at `http://localhost:8080`
- [ ] **DPA API Server** running at `http://localhost:8081`
- [ ] **Frontend** running at `http://localhost:3000`
- [ ] **TPM Key** initialized (you've done this!)
- [ ] **Device enrolled** with TPM key registered

## Step-by-Step Testing Guide

### Step 1: Verify All Services Are Running

**Check Backend:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```

**Check DPA API:**
```powershell
Invoke-WebRequest -Uri http://localhost:8081/health -UseBasicParsing
```

Expected DPA API response:
```json
{
  "status": "healthy",
  "enrolled": true,
  "tpm_available": true,
  "message": "DPA API is running"
}
```

**Check Keycloak:**
```powershell
Invoke-WebRequest -Uri http://localhost:8080/realms/master/.well-known/openid-configuration -UseBasicParsing | Select-Object StatusCode
```

**Check Frontend:**
Open browser to `http://localhost:3000` - should load without errors

---

### Step 2: Start Frontend (if not running)

```powershell
cd frontend
npm start
```

Wait for the browser to open automatically at `http://localhost:3000`

---

### Step 3: Login to Frontend

1. **Navigate to** `http://localhost:3000`
2. **Click "Login"** or "Login with Keycloak"
3. **Enter credentials:**
   - Username: `admin`
   - Password: `adminsecure123`
4. **Complete login** - you should be redirected to the dashboard

---

### Step 4: Navigate to User Dashboard

1. **Click on "User Dashboard"** in the navigation menu
   - Or navigate directly to `http://localhost:3000/user-dashboard`
2. **Open Browser DevTools** (Press `F12`)
3. **Go to Console tab** - keep this open to see logs
4. **Go to Network tab** - to monitor API calls

---

### Step 5: Observe the TPM Attestation Flow

When the User Dashboard loads, watch for these events in the Console:

**Expected Console Output (Success):**
```
1. Requesting challenge for device...
2. Challenge received: <challenge-string>
3. Signing challenge with DPA...
4. Challenge signed successfully
5. Requesting token with signed challenge...
6. Token issued successfully
7. Loading resources...
8. Resources loaded successfully
```

**Expected Network Requests (in Network tab):**

1. **POST** `/api/tokens/challenge`
   - Status: `200 OK`
   - Request: `{ "device_id": <number> }`
   - Response: `{ "challenge": "...", "expires_in_seconds": 300 }`

2. **POST** `http://localhost:8081/sign-challenge`
   - Status: `200 OK`
   - Request: `{ "challenge": "..." }`
   - Response: `{ "signature": "...", "message": "..." }`

3. **POST** `/api/tokens/issue`
   - Status: `200 OK`
   - Request: `{ "device_id": ..., "challenge": "...", "challenge_signature": "...", "resource": "*" }`
   - Response: `{ "token": "...", "device_id": ..., "is_compliant": true, ... }`

4. **GET** `/api/resources/list`
   - Status: `200 OK`
   - Request Headers: `Authorization: Bearer <device_token>`
   - Response: `{ "resources": [...], "message": "..." }`

---

### Step 6: Verify Resource Access

After successful token issuance, you should see:

1. **Resources displayed** in the dashboard
2. **Resource list** showing available files:
   - Company Policy Document.pdf
   - Employee Handbook.pdf
   - Training Materials.zip
   - Confidential Report.docx

3. **Download buttons** for each resource
4. **Role badges** showing access levels (Admin Only, User Access, Public)

---

### Step 7: Test Resource Download

1. **Click "Download"** on any resource
2. **Observe Network tab** for:
   - **GET** `/api/resources/download/<resource_id>`
   - Status: `200 OK`
   - Response: JSON with download confirmation

3. **Check Console** for success messages

---

### Step 8: Test Error Scenarios

#### Test 1: Stop DPA API Server

1. **Stop the DPA API server** (Ctrl+C in its terminal)
2. **Refresh the User Dashboard** page
3. **Expected Error:**
   ```
   Failed to sign challenge with DPA. 
   Please ensure the DPA agent is running...
   ```
4. **Restart DPA API** and refresh again - should work

#### Test 2: Expired Challenge

1. **Wait 5+ minutes** after getting a challenge
2. **Try to use the token** (refresh page)
3. **Expected:** New challenge is automatically requested

#### Test 3: Invalid Device

1. **Try accessing with unenrolled device**
2. **Expected:** Error message about device enrollment required

---

## Success Criteria Checklist

- [ ] All services running and accessible
- [ ] Login successful
- [ ] User Dashboard loads without errors
- [ ] Challenge request succeeds (200 OK)
- [ ] Challenge signing succeeds (200 OK)
- [ ] Token issuance succeeds (200 OK)
- [ ] Resources load successfully (200 OK)
- [ ] Resources displayed in UI
- [ ] Download buttons functional
- [ ] No errors in console
- [ ] All network requests return 200 OK

---

## Troubleshooting

### Issue: DPA API Not Responding

**Symptoms:**
- Console error: "Failed to connect to DPA API"
- Network request to `localhost:8081` fails

**Solution:**
```powershell
cd dpa
python start_api_server.py
```

### Issue: Challenge Signing Fails

**Symptoms:**
- DPA API returns error
- Console shows "TPM signing failed"

**Check:**
1. Is device enrolled? Check: `http://localhost:8081/health` → `enrolled: true`
2. Is TPM available? Check: `http://localhost:8081/health` → `tpm_available: true`
3. Check DPA API server logs for errors

**Solution:**
- Ensure TPM key is initialized (you've done this)
- Verify device is enrolled with TPM key

### Issue: Token Issuance Fails (401 Unauthorized)

**Symptoms:**
- Backend rejects token request
- Error: "Invalid TPM signature"

**Possible Causes:**
- Challenge expired (must use within 5 minutes)
- Challenge already used (can only use once)
- Signature doesn't match device's TPM key

**Solution:**
- Refresh page to get new challenge
- Ensure device's TPM public key matches backend

### Issue: Resources Not Loading

**Symptoms:**
- Resources list is empty
- Error: "Access denied"

**Check:**
1. Is device enrolled? (`is_enrolled: true`)
2. Is device active? (`status: "active"`)
3. Is device compliant? (`is_compliant: true`)

**Solution:**
- Ensure device is enrolled, active, and compliant
- Check backend logs for specific error

---

## Testing Different User Roles

### Admin User
- Should see all resources (including admin-only)
- Should have "Admin Access" badge

### Regular User
- Should see user-accessible resources
- Should NOT see admin-only resources
- Download should work for accessible resources

---

## Next Steps After Testing

Once frontend testing is successful:

1. ✅ Test with different devices
2. ✅ Test error scenarios
3. ✅ Test with expired challenges
4. ✅ Verify security (stolen credentials can't access)
5. ✅ Test role-based access control
6. ✅ Test resource download functionality

---

## Quick Reference Commands

**Start DPA API Server:**
```powershell
cd dpa
python start_api_server.py
```

**Check DPA Health:**
```powershell
Invoke-WebRequest -Uri http://localhost:8081/health -UseBasicParsing | ConvertFrom-Json
```

**Check Backend Health:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing | ConvertFrom-Json
```

**View DPA API Logs:**
- Check the terminal where DPA API server is running

**View Backend Logs:**
- Check backend terminal or Docker logs

---

## Notes

- **Challenges expire after 5 minutes** - if you wait too long, refresh the page
- **Challenges can only be used once** - each token request needs a new challenge
- **TPM signing requires admin privileges** - ensure TPMSigner.exe has proper permissions
- **Device must be enrolled** - unenrolled devices cannot access resources

