# Frontend Testing Guide - TPM Device Attestation

This guide walks you through testing the complete TPM device attestation flow through the frontend.

## Prerequisites

1. ✅ **Backend running** at `http://localhost:8000`
2. ✅ **Keycloak running** at `http://localhost:8080`
3. ✅ **Frontend running** at `http://localhost:3000`
4. ✅ **DPA API server running** at `http://localhost:8081`
5. ✅ **Device enrolled** with TPM key registered

## Step-by-Step Testing

### Step 1: Start All Services

**Terminal 1 - Backend:**
```bash
cd backend
# Already running via docker-compose or manually
```

**Terminal 2 - DPA API Server:**
```bash
cd dpa
python start_api_server.py
```

You should see:
```
============================================================
DPA Local API Server
============================================================
Starting server on 127.0.0.1:8081
Log level: info
============================================================
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm start
```

### Step 2: Verify DPA API is Running

Open browser and navigate to:
```
http://localhost:8081/health
```

Expected response:
```json
{
  "status": "healthy",
  "enrolled": true,
  "tpm_available": true,
  "message": "DPA API is running"
}
```

If `enrolled: false`, enroll the device first:
```bash
python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE
```

### Step 3: Login to Frontend

1. Navigate to `http://localhost:3000`
2. Login with a user account that has an enrolled device
3. You should be redirected to the dashboard

### Step 4: Access User Dashboard

1. Navigate to `/user-dashboard` (or click "User Dashboard" in navigation)
2. Open browser DevTools (F12) → Console tab
3. Watch for the following flow:

**Expected Console Output:**
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

### Step 5: Verify Resource Access

1. Resources should appear in the dashboard
2. You should be able to see available resources
3. Download buttons should work (for demo resources)

## Expected Behavior

### ✅ Success Flow

1. **Challenge Request** → Backend returns challenge
2. **DPA Signing** → DPA API signs challenge with TPM
3. **Token Issuance** → Backend verifies signature and issues token
4. **Resource Access** → Resources load successfully

### ❌ Failure Cases

#### Case 1: DPA API Not Running

**Error in Console:**
```
Failed to connect to DPA API. Please ensure the DPA agent is running
```

**Solution:** Start DPA API server (`python dpa/start_api_server.py`)

#### Case 2: Device Not Enrolled

**Error in Console:**
```
Device is not enrolled. Please enroll the device first.
```

**Solution:** Enroll the device using enrollment code

#### Case 3: Invalid TPM Signature

**Error in Console:**
```
Invalid TPM signature. The challenge must be signed by the device's TPM.
```

**Possible Causes:**
- Wrong device's TPM used
- TPM key mismatch
- Signature format error

**Solution:** Ensure device is enrolled and TPM key matches backend

#### Case 4: Expired Challenge

**Error in Console:**
```
Invalid or expired challenge. Please request a new challenge.
```

**Solution:** Challenge expired (5 minutes). Refresh the page to get a new challenge.

## Browser DevTools Inspection

### Network Tab

Watch for these requests:

1. **POST** `/api/tokens/challenge`
   - Status: `200 OK`
   - Response: `{ challenge: "...", expires_in_seconds: 300 }`

2. **POST** `http://localhost:8081/sign-challenge`
   - Status: `200 OK`
   - Response: `{ signature: "...", message: "..." }`

3. **POST** `/api/tokens/issue`
   - Status: `200 OK` (if signature valid)
   - Status: `401 Unauthorized` (if signature invalid)
   - Response: `{ token: "...", device_id: ..., ... }`

4. **GET** `/api/resources/list`
   - Status: `200 OK`
   - Response: `{ resources: [...], message: "..." }`

### Console Tab

Look for:
- ✅ Success messages
- ❌ Error messages
- ⚠️ Warning messages

## Troubleshooting

### DPA API Connection Issues

**Problem:** Frontend can't connect to DPA API

**Check:**
1. Is DPA API server running? (`http://localhost:8081/health`)
2. Is CORS configured correctly? (Should allow `localhost:3000`)
3. Check browser console for CORS errors

**Solution:**
```bash
# Restart DPA API server
cd dpa
python start_api_server.py
```

### Challenge Signing Fails

**Problem:** DPA API returns error when signing

**Check:**
1. Is device enrolled? (`http://localhost:8081/health` → `enrolled: true`)
2. Is TPM available? (`http://localhost:8081/health` → `tpm_available: true`)
3. Check DPA API server logs for errors

**Solution:**
```bash
# Check enrollment
python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE

# Check TPM status
python -c "from dpa.core.tpm import TPMWrapper; t = TPMWrapper(); print(t.check_status())"
```

### Token Issuance Fails

**Problem:** Backend rejects token request

**Check:**
1. Is signature valid? (Check backend logs)
2. Is challenge expired? (Must use within 5 minutes)
3. Is challenge reused? (Can only use once)

**Solution:**
- Refresh page to get new challenge
- Check backend logs for specific error
- Verify device's TPM public key matches backend

## Testing Different Scenarios

### Scenario 1: Valid Flow

1. ✅ Device enrolled
2. ✅ DPA API running
3. ✅ TPM available
4. ✅ Expected: Full flow works, resources accessible

### Scenario 2: DPA API Down

1. ✅ Device enrolled
2. ❌ DPA API not running
3. ✅ Expected: Error message, no token issued

### Scenario 3: Device Not Enrolled

1. ❌ Device not enrolled
2. ✅ DPA API running
3. ✅ Expected: Error message about enrollment

### Scenario 4: TPM Not Available

1. ✅ Device enrolled
2. ✅ DPA API running
3. ❌ TPM not available
4. ✅ Expected: Error when signing challenge

## Verification Checklist

- [ ] DPA API server starts successfully
- [ ] Health endpoint returns `enrolled: true`
- [ ] Health endpoint returns `tpm_available: true`
- [ ] Frontend can connect to DPA API
- [ ] Challenge signing works
- [ ] Token issuance succeeds
- [ ] Resources load successfully
- [ ] Error messages are clear and helpful

## Next Steps

Once frontend testing is successful:

1. ✅ Test with different devices
2. ✅ Test error scenarios
3. ✅ Test with expired challenges
4. ✅ Test with invalid signatures
5. ✅ Verify security (stolen credentials can't access)

## Related Documentation

- **DPA API Integration**: `docs/DPA_API_INTEGRATION.md`
- **TPM Attestation**: `docs/TPM_DEVICE_ATTESTATION.md`
- **Testing Guide**: `docs/TESTING_TPM_ATTESTATION.md`
- **Quick Test Guide**: `docs/QUICK_TEST_GUIDE.md`

