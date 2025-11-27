# TPM-Based Device Attestation

## Overview

This feature implements TPM (Trusted Platform Module)-based device attestation to prevent stolen credential attacks. Even if an attacker steals a user's login credentials, they cannot access protected resources without the physical device and its TPM.

## How It Works

### Challenge-Response Flow

1. **User requests access token** → Frontend calls `/api/tokens/challenge`
2. **Backend generates challenge** → Returns a unique, time-limited nonce
3. **DPA signs challenge** → Device's TPM signs the challenge (proves device authenticity)
4. **Frontend requests token** → Sends challenge + signature to `/api/tokens/issue`
5. **Backend verifies signature** → Validates TPM signature against device's public key
6. **Token issued** → Only if signature is valid (proves genuine device)

### Security Benefits

- **Prevents credential theft**: Stolen passwords alone are insufficient
- **Device binding**: Access requires the specific enrolled device
- **TPM verification**: Cryptographic proof of device authenticity
- **Replay protection**: Challenges expire after 5 minutes and can only be used once

## Implementation Details

### Backend Components

#### 1. Challenge Service (`backend/app/services/challenge_service.py`)
- Generates unique challenges (nonces)
- Stores challenges with expiration (5 minutes)
- Validates challenges and prevents reuse
- In-memory storage (consider Redis for production)

#### 2. Signature Service (`backend/app/services/signature_service.py`)
- `verify_challenge_signature()`: Verifies TPM signature on challenges
- Uses device's stored TPM public key
- Matches DPA's signing format (canonical JSON → base64 → sign)

#### 3. Token Router (`backend/app/routers/token.py`)
- **`POST /api/tokens/challenge`**: Generates challenge for device
- **`POST /api/tokens/issue`**: Issues token after TPM verification
  - Requires: `challenge`, `challenge_signature`
  - Validates challenge is valid and not expired
  - Verifies TPM signature matches device's public key
  - Only issues token if all checks pass

### Frontend Components

#### Token Service (`frontend/src/api/tokenService.js`)
- `requestChallenge(deviceId)`: Requests challenge from backend
- `signChallengeWithDPA(challenge)`: **TODO** - Calls DPA to sign challenge
- `issueToken(deviceId, challenge, signature, ...)`: Requests token with signed challenge

#### User Dashboard (`frontend/src/pages/UserDashboard.jsx`)
- Updated `requestAccessToken()` to use challenge-response flow
- Handles DPA signing errors gracefully
- Shows clear error messages for attestation failures

## DPA Integration Required

The frontend needs to communicate with the DPA agent to sign challenges. The DPA should expose a local API endpoint:

### Proposed DPA Endpoint

```
POST http://localhost:8081/sign-challenge
Content-Type: application/json

{
  "challenge": "base64-encoded-challenge-string"
}

Response:
{
  "signature": "base64-encoded-tpm-signature"
}
```

### DPA Signing Process

The DPA should:
1. Receive challenge string
2. Create dict: `{"challenge": challenge_string}`
3. Convert to canonical JSON (sorted keys): `json.dumps({"challenge": challenge}, sort_keys=True)`
4. Base64 encode the JSON
5. Sign with TPM: `tpm.sign(base64_encoded_json)`
6. Return base64-encoded signature

This matches the format expected by `SignatureService.verify_challenge_signature()`.

## Current Status

✅ **Backend**: Fully implemented
- Challenge generation and validation
- TPM signature verification
- Token issuance with attestation requirement

⚠️ **Frontend**: Partially implemented
- Challenge request flow
- Token request with challenge/signature
- **Missing**: DPA local API integration for signing

## Testing

See `docs/TESTING_TPM_ATTESTATION.md` for comprehensive testing guide.

### Quick Test

Run the automated test script:

```bash
cd backend
python tests/test_tpm_attestation.py
```

### Manual Testing Flow

1. **Enroll a device** (ensures TPM key is stored)
2. **Login as user** with enrolled device
3. **Access User Dashboard** → Should request challenge
4. **DPA signs challenge** (when DPA API is implemented)
5. **Token issued** → Resources accessible

### Testing Without DPA

The test script includes mock signature generation for testing the flow, but it will fail signature verification (as expected). For full end-to-end testing, DPA integration is required.

**⚠️ Warning**: Never disable TPM verification in production!

## Security Considerations

1. **Challenge Expiration**: Challenges expire after 5 minutes
2. **One-Time Use**: Challenges are marked as used after verification
3. **TPM Key Storage**: Device's TPM public key must be stored securely
4. **Signature Format**: Must match DPA's signing format exactly
5. **Replay Attacks**: Prevented by challenge expiration and one-time use

## Future Enhancements

1. **Redis Storage**: Replace in-memory challenge store with Redis for scalability
2. **Challenge Cleanup**: Periodic cleanup of expired challenges
3. **Rate Limiting**: Limit challenge requests per device/IP
4. **Audit Logging**: Log all attestation attempts (successful and failed)
5. **Optional Resource-Level Verification**: Add TPM signature to resource access requests

## Related Files

- `backend/app/services/challenge_service.py` - Challenge management
- `backend/app/services/signature_service.py` - TPM signature verification
- `backend/app/routers/token.py` - Token endpoints with attestation
- `frontend/src/api/tokenService.js` - Frontend token service
- `frontend/src/pages/UserDashboard.jsx` - User dashboard with attestation flow

