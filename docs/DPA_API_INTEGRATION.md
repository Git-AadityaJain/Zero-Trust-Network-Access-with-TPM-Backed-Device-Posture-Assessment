# DPA Local API Integration

## Overview

The DPA (Device Posture Agent) now exposes a local HTTP API server that allows the frontend to request TPM-signed challenges for device attestation. This enables the full challenge-response flow for preventing stolen credential attacks.

## Starting the DPA API Server

### Prerequisites

1. **DPA Dependencies Installed**:
   ```bash
   cd dpa
   pip install -r requirements.txt
   ```

2. **Device Must Be Enrolled**: The device must be enrolled with a TPM key registered.

### Starting the Server

**Option 1: From project root (recommended)**
```bash
# From project root
python dpa/start_api_server.py
```

**Option 2: From dpa directory**
```bash
cd dpa
python start_api_server.py
```

**With custom options:**
```bash
python dpa/start_api_server.py --host 127.0.0.1 --port 8081 --log-level info
```

**Default Configuration:**
- Host: `127.0.0.1` (localhost only - for security)
- Port: `8081`
- Log Level: `info`

The server will start and listen for requests from the frontend.

## API Endpoints

### 1. Health Check

**GET** `/health`

Returns the status of the DPA API, including enrollment and TPM availability.

**Response:**
```json
{
  "status": "healthy",
  "enrolled": true,
  "tpm_available": true,
  "message": "DPA API is running"
}
```

### 2. Sign Challenge

**POST** `/sign-challenge`

Signs a challenge string with the device's TPM for device attestation.

**Request:**
```json
{
  "challenge": "challenge-string-from-backend"
}
```

**Response:**
```json
{
  "signature": "base64-encoded-tpm-signature",
  "message": "Challenge signed successfully with device TPM"
}
```

**Error Responses:**

- `403 Forbidden`: Device is not enrolled
- `500 Internal Server Error`: TPM signing failed or TPM not available

### 3. Root Endpoint

**GET** `/`

Returns API information and available endpoints.

## Frontend Integration

The frontend is already configured to use the DPA API. The `tokenService.js` file includes:

```javascript
export const signChallengeWithDPA = async (challenge) => {
  const dpaApiUrl = process.env.REACT_APP_DPA_API_URL || 'http://localhost:8081/sign-challenge';
  // ... calls DPA API
};
```

### Configuration

You can configure the DPA API URL via environment variable:

```bash
# In frontend/.env
REACT_APP_DPA_API_URL=http://localhost:8081/sign-challenge
```

## Testing the Integration

### 1. Start DPA API Server

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

### 2. Test Health Endpoint

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

### 3. Test Challenge Signing

```bash
curl -X POST http://localhost:8081/sign-challenge \
  -H "Content-Type: application/json" \
  -d '{"challenge": "test-challenge-123"}'
```

Expected response:
```json
{
  "signature": "base64-encoded-signature...",
  "message": "Challenge signed successfully with device TPM"
}
```

### 4. Test Through Frontend

1. **Start DPA API**: `python dpa/start_api_server.py`
2. **Start Frontend**: `npm start` (in frontend directory)
3. **Login** as a user with an enrolled device
4. **Navigate to User Dashboard** (`/user-dashboard`)
5. **Check browser console** - should see:
   - Challenge requested from backend
   - Challenge signed via DPA API
   - Token issued successfully
   - Resources loaded

## Security Considerations

1. **Localhost Only**: The server binds to `127.0.0.1` by default, only accepting local connections
2. **CORS Protection**: Only allows requests from `localhost:3000` (frontend)
3. **Enrollment Required**: Challenge signing requires device enrollment
4. **TPM Verification**: Signatures are cryptographically verified by the backend

## Troubleshooting

### "Failed to connect to DPA API"

**Solution**: Ensure the DPA API server is running:
```bash
python dpa/start_api_server.py
```

### "Device is not enrolled"

**Solution**: Enroll the device first:
```bash
python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE
```

### "TPM signing failed"

**Possible causes:**
1. TPM not available on the system
2. TPM key not initialized
3. TPM driver issues

**Solution**: 
- Check TPM status: `python -c "from dpa.core.tpm import TPMWrapper; t = TPMWrapper(); print(t.check_status())"`
- Re-initialize TPM key if needed

### CORS Errors

**Solution**: Ensure the frontend is running on `http://localhost:3000` and the DPA API allows this origin (already configured).

### Port Already in Use

**Solution**: Use a different port:
```bash
python start_api_server.py --port 8082
```

Then update frontend environment variable:
```bash
REACT_APP_DPA_API_URL=http://localhost:8082/sign-challenge
```

## Development Notes

### File Structure

```
dpa/
├── api/
│   ├── __init__.py
│   └── server.py          # FastAPI server
├── start_api_server.py    # Server startup script
└── requirements.txt        # Updated with FastAPI/uvicorn
```

### Dependencies Added

- `fastapi>=0.104.0`: Web framework for API
- `uvicorn[standard]>=0.24.0`: ASGI server

### Integration Flow

1. **Frontend** requests challenge from backend → `POST /api/tokens/challenge`
2. **Frontend** calls DPA API → `POST http://localhost:8081/sign-challenge`
3. **DPA** signs challenge with TPM → Returns signature
4. **Frontend** requests token with signature → `POST /api/tokens/issue`
5. **Backend** verifies signature → Issues token if valid

## Next Steps

1. ✅ DPA API server created
2. ✅ Frontend integration updated
3. ✅ Documentation complete
4. ⚠️ Test end-to-end flow
5. ⚠️ Consider adding authentication to DPA API (optional, since it's localhost-only)

## Production Considerations

For production deployment:

1. **Add Authentication**: Consider adding API key or token authentication
2. **HTTPS**: Use HTTPS even for localhost (self-signed cert)
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **Logging**: Enhanced logging for security auditing
5. **Process Management**: Use systemd/service manager to keep server running

