# CORS Fix for DPA API

## Issue
The frontend running on ngrok (`https://609b9c24fbd6.ngrok-free.app`) cannot access the DPA API at `localhost:8081` due to:
1. CORS restrictions
2. Browser security (HTTPS page trying to access HTTP localhost)

## Solution Applied
Updated `dpa/api/server.py` to allow all origins for development.

## Next Steps

### Option 1: Restart DPA API Server (Recommended)
1. Stop the current DPA API server (Ctrl+C)
2. Restart it:
   ```powershell
   cd dpa
   python start_api_server.py
   ```
3. The CORS fix will now allow requests from any origin

### Option 2: Access Frontend Locally
Instead of using ngrok, access the frontend locally:
- `http://localhost:3000` (if running locally)
- This will allow direct access to `localhost:8081`

### Option 3: Expose DPA API via ngrok (Advanced)
If you need to access from ngrok frontend:
1. Expose DPA API via ngrok:
   ```powershell
   ngrok http 8081
   ```
2. Update frontend environment variable:
   ```powershell
   # In frontend/.env or docker-compose.yml
   REACT_APP_DPA_API_URL=https://your-ngrok-url.ngrok-free.app/sign-challenge
   ```

## Testing
After restarting the DPA API server, try accessing the User Dashboard again. The CORS error should be resolved.

## Note
The current CORS configuration allows all origins (`*`). For production, you should restrict this by setting the `DPA_CORS_ORIGINS` environment variable:
```powershell
$env:DPA_CORS_ORIGINS = "https://your-domain.com,https://another-domain.com"
python dpa/start_api_server.py
```

