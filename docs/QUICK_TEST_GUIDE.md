# Quick Test Guide - TPM Device Attestation

## 🚀 Quick Start

### Option 1: Automated Test Script (Recommended)

```bash
cd backend
python tests/test_tpm_attestation.py
```

This will:
- ✅ Test challenge endpoint
- ✅ Test token issuance flow
- ✅ Test invalid signature rejection
- ⚠️ Uses mock signature (will fail verification - expected)

### Option 2: Manual API Testing

#### 1. Get Authentication Token

```bash
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=admin-frontend" \
  -d "username=admin" \
  -d "password=adminsecure123"
```

Copy the `access_token` from response.

#### 2. Get Your Device ID

```bash
curl -X GET http://localhost:8000/api/users/me/devices \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Find an enrolled device and note its `id`.

#### 3. Request Challenge

```bash
curl -X POST http://localhost:8000/api/tokens/challenge \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_id": YOUR_DEVICE_ID}'
```

Copy the `challenge` from response.

#### 4. Sign Challenge (with DPA)

**Start DPA API Server first:**
```bash
cd dpa
python start_api_server.py
```

**Then sign challenge via API:**
```bash
curl -X POST http://localhost:8081/sign-challenge \
  -H "Content-Type: application/json" \
  -d '{"challenge": "YOUR_CHALLENGE"}'
```

**Or use Python directly:**
```python
from dpa.core.signing import PostureSigner
signer = PostureSigner()
signature = signer.sign({"challenge": "YOUR_CHALLENGE"})
print(signature)
```

#### 5. Request Token

```bash
curl -X POST http://localhost:8000/api/tokens/issue \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": YOUR_DEVICE_ID,
    "challenge": "YOUR_CHALLENGE",
    "challenge_signature": "YOUR_SIGNATURE",
    "resource": "*"
  }'
```

**Success (200):** Returns device access token
**Failure (401):** Invalid signature or expired challenge

#### 6. Use Token for Resources

```bash
curl -X GET http://localhost:8000/api/resources/list \
  -H "Authorization: Bearer YOUR_DEVICE_TOKEN"
```

## ✅ Expected Results

### Successful Flow
1. Challenge generated → `200 OK` with challenge string
2. Challenge signed → DPA returns signature
3. Token issued → `200 OK` with JWT token
4. Resources accessible → `200 OK` with resource list

### Failure Cases
- **Invalid signature** → `401 Unauthorized`
- **Expired challenge** → `401 Unauthorized`
- **Reused challenge** → `401 Unauthorized`
- **No TPM key** → `400 Bad Request`

## 🔍 Verification Checklist

- [ ] Challenge endpoint works
- [ ] Challenge expires after 5 minutes
- [ ] Valid signature → Token issued
- [ ] Invalid signature → Rejected
- [ ] Expired challenge → Rejected
- [ ] Token works for resource access

## 📚 Full Documentation

- **Comprehensive Testing**: `docs/TESTING_TPM_ATTESTATION.md`
- **Implementation Details**: `docs/TPM_DEVICE_ATTESTATION.md`

## ⚠️ Important Notes

1. **DPA Integration Required**: For real testing, DPA must expose challenge signing endpoint
2. **Mock Signatures Won't Work**: Test script uses mock signatures that will fail verification
3. **Device Must Have TPM Key**: Device must be enrolled with TPM public key stored
4. **Challenges Expire**: Challenges expire after 5 minutes and can only be used once

