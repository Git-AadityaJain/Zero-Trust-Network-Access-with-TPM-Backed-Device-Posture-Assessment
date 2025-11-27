# Testing TPM Device Attestation

This guide explains how to test the TPM-based device attestation feature.

## Prerequisites

1. **Enrolled Device**: A device must be enrolled with a TPM public key stored
2. **Backend Running**: Backend API at `http://localhost:8000`
3. **Keycloak Running**: Keycloak at `http://localhost:8080`
4. **User Account**: A user account with an enrolled device

## Testing Methods

### Method 1: Automated Test Script

Run the automated test script:

```bash
cd backend
python tests/test_tpm_attestation.py
```

Or with a Keycloak token:

```bash
python tests/test_tpm_attestation.py YOUR_KEYCLOAK_TOKEN
```

**What it tests:**
- ✅ Challenge endpoint (`/api/tokens/challenge`)
- ✅ Token issuance with signature requirement
- ✅ Invalid signature rejection
- ⚠️ Uses mock signature (will fail - expected)

**Note**: The script uses a mock signature for demonstration. Real testing requires the DPA to sign challenges.

### Method 2: Manual API Testing (with DPA)

#### Step 1: Get Authentication Token

```bash
# Using Keycloak
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=admin-frontend" \
  -d "username=YOUR_USERNAME" \
  -d "password=YOUR_PASSWORD"
```

Save the `access_token` from the response.

#### Step 2: Get User's Devices

```bash
curl -X GET http://localhost:8000/api/users/me/devices \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Find a device with `is_enrolled: true` and `status: "active"`. Note the `id`.

#### Step 3: Request Challenge

```bash
curl -X POST http://localhost:8000/api/tokens/challenge \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": YOUR_DEVICE_ID}'
```

Response:
```json
{
  "challenge": "random-challenge-string",
  "expires_in_seconds": 300,
  "message": "Challenge generated..."
}
```

Save the `challenge` value.

#### Step 4: Sign Challenge with DPA

**Option A: If DPA exposes local API**

```bash
curl -X POST http://localhost:8081/sign-challenge \
  -H "Content-Type: application/json" \
  -d '{"challenge": "YOUR_CHALLENGE_STRING"}'
```

Response:
```json
{
  "signature": "base64-encoded-tpm-signature"
}
```

**Option B: Use DPA Python API directly**

```python
from dpa.core.signing import PostureSigner

signer = PostureSigner()
challenge_data = {"challenge": "YOUR_CHALLENGE_STRING"}
signature = signer.sign(challenge_data)
print(signature)
```

#### Step 5: Request Token with Signed Challenge

```bash
curl -X POST http://localhost:8000/api/tokens/issue \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": YOUR_DEVICE_ID,
    "challenge": "YOUR_CHALLENGE_STRING",
    "challenge_signature": "YOUR_SIGNATURE",
    "resource": "*",
    "expires_in_minutes": 15
  }'
```

**Success Response (200):**
```json
{
  "token": "jwt-device-access-token",
  "expires_in_minutes": 15,
  "device_id": 1,
  "device_name": "My Device",
  "is_compliant": true,
  "message": "Token issued successfully after device attestation"
}
```

**Failure Response (401):**
```json
{
  "detail": "Invalid TPM signature. The challenge must be signed by the device's TPM."
}
```

#### Step 6: Use Token for Resource Access

```bash
curl -X GET http://localhost:8000/api/resources/list \
  -H "Authorization: Bearer YOUR_DEVICE_TOKEN"
```

Should return list of resources if token is valid.

### Method 3: Frontend Testing

1. **Start the frontend** (if not already running)
2. **Login** as a user with an enrolled device
3. **Navigate to User Dashboard** (`/user-dashboard`)
4. **Check browser console** for:
   - Challenge request
   - DPA signing attempt
   - Token issuance
   - Resource loading

**Expected Flow:**
1. Frontend requests challenge → ✅
2. Frontend calls DPA to sign → ⚠️ (if DPA not integrated, will show error)
3. Frontend requests token with signature → ✅ (if signature valid)
4. Resources load → ✅

### Method 4: Testing Error Cases

#### Test 1: Invalid Signature

```bash
# Use a random string as signature
curl -X POST http://localhost:8000/api/tokens/issue \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": YOUR_DEVICE_ID,
    "challenge": "VALID_CHALLENGE",
    "challenge_signature": "invalid_signature",
    "resource": "*"
  }'
```

**Expected:** `401 Unauthorized` with message about invalid signature

#### Test 2: Expired Challenge

```bash
# Wait 5+ minutes after getting challenge, then try to use it
# Or manually set an old challenge
```

**Expected:** `401 Unauthorized` with message about expired challenge

#### Test 3: Reused Challenge

```bash
# Use the same challenge twice
# First request should succeed
# Second request should fail
```

**Expected:** Second request returns `401 Unauthorized`

#### Test 4: Wrong Device's Signature

```bash
# Get challenge for Device A
# Sign with Device B's TPM
# Try to use Device A's challenge with Device B's signature
```

**Expected:** `401 Unauthorized` (signature won't match Device A's public key)

## Verification Checklist

- [ ] Challenge endpoint returns valid challenge
- [ ] Challenge expires after 5 minutes
- [ ] Challenge can only be used once
- [ ] Valid TPM signature allows token issuance
- [ ] Invalid signature is rejected
- [ ] Expired challenge is rejected
- [ ] Reused challenge is rejected
- [ ] Wrong device's signature is rejected
- [ ] Issued token works for resource access
- [ ] Token contains correct device_id and user info

## Troubleshooting

### "Device does not have a TPM public key"

**Solution:** Ensure the device was enrolled with TPM key registration. Check device enrollment process.

### "Invalid TPM signature"

**Possible causes:**
1. Signature format doesn't match expected format
2. Wrong device's TPM was used to sign
3. Challenge was modified before signing
4. DPA signing implementation doesn't match backend verification

**Solution:** Verify DPA signing matches backend's expected format:
- Create dict: `{"challenge": challenge_string}`
- Convert to canonical JSON (sorted keys)
- Base64 encode JSON
- Sign with TPM
- Return base64-encoded signature

### "Invalid or expired challenge"

**Possible causes:**
1. Challenge expired (5 minutes)
2. Challenge already used
3. Challenge doesn't match device

**Solution:** Request a new challenge and use it immediately.

### Frontend shows "DPA challenge signing not implemented"

**Solution:** Implement DPA local API endpoint for challenge signing. See `docs/TPM_DEVICE_ATTESTATION.md` for details.

## Integration with DPA

✅ **DPA API Integration Complete!**

The DPA now exposes a local API server. See `docs/DPA_API_INTEGRATION.md` for full details.

### Quick Start

1. **Start DPA API Server**:
   ```bash
   cd dpa
   python start_api_server.py
   ```

2. **Frontend is already configured** to use `http://localhost:8081/sign-challenge`

3. **Test the integration**:
   - Start DPA API server
   - Start frontend
   - Login and navigate to User Dashboard
   - Challenge signing should work automatically

## Next Steps

1. ✅ Backend implementation complete
2. ⚠️ DPA local API for challenge signing (to be implemented)
3. ⚠️ Frontend DPA integration (to be implemented)
4. ✅ Test script available
5. ✅ Documentation complete

Once DPA integration is complete, the full flow can be tested end-to-end through the frontend.

