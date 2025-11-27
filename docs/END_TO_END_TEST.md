# End-to-End Testing Guide - TPM Device Attestation

## Prerequisites Checklist

Before testing, ensure:

- [ ] **Backend running** at `http://localhost:8000`
- [ ] **Keycloak running** at `http://localhost:8080`
- [ ] **Frontend running** at `http://localhost:3000`
- [ ] **DPA API server running** at `http://localhost:8081`
- [ ] **TPMSigner.exe available** (built and accessible)
- [ ] **Device enrolled** with TPM key registered
- [ ] **User account** with enrolled device

## Quick Start Testing

### Step 1: Verify All Services

**Terminal 1 - Check Backend:**
```bash
curl http://localhost:8000/health
```

**Terminal 2 - Check DPA API:**
```bash
curl http://localhost:8081/health
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

### Step 2: Test Challenge Signing

**Test DPA API challenge signing:**
```powershell
$body = @{challenge="test-challenge-123"} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8081/sign-challenge" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
```

Should return:
```json
{
  "signature": "base64-encoded-signature...",
  "message": "Challenge signed successfully with device TPM"
}
```

### Step 3: Test Through Frontend

1. **Open browser** to `http://localhost:3000`
2. **Login** with a user that has an enrolled device
3. **Navigate to User Dashboard** (`/user-dashboard`)
4. **Open DevTools** (F12) → Console tab
5. **Watch for:**
   - Challenge request
   - Challenge signing
   - Token issuance
   - Resources loading

## Expected Flow

### Console Output (Success):
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

### Network Tab (Success):
1. `POST /api/tokens/challenge` → 200 OK
2. `POST http://localhost:8081/sign-challenge` → 200 OK
3. `POST /api/tokens/issue` → 200 OK
4. `GET /api/resources/list` → 200 OK

## Troubleshooting

### Issue: DPA API not responding
**Solution:** Ensure DPA API server is running:
```bash
cd dpa
python start_api_server.py
```

### Issue: TPM not available
**Check:**
```powershell
# Test TPMSigner directly
.\TPMSigner\bin\Release\net6.0-windows\win-x64\publish\TPMSigner.exe status
```

### Issue: Challenge signing fails
**Check:**
1. Is device enrolled?
2. Is TPM key initialized?
3. Is TPMSigner.exe accessible?

### Issue: Token issuance fails
**Check backend logs** for:
- Invalid signature error
- Expired challenge error
- Device not found error

## Success Criteria

✅ All services running
✅ DPA API health check passes
✅ Challenge signing works
✅ Token issuance succeeds
✅ Resources accessible
✅ No errors in console
✅ All network requests return 200 OK

