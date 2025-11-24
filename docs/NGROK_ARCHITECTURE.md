# ngrok Tunneling Architecture

This document explains how ngrok tunneling works and how remote devices communicate with the backend.

## Overview

ngrok creates a secure tunnel from the internet to your local machine, allowing remote devices to access your local services without exposing your network directly.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTERNET / REMOTE DEVICE                     │
│                                                                  │
│  Remote Device (DPA)                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DPA Agent                                                │  │
│  │  - Enrollment Request                                      │  │
│  │  - Posture Reports                                        │  │
│  │  Backend URL: https://b64e34aa6da9.ngrok-free.app         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           │ HTTPS                                │
│                           ▼                                      │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────────┐
│                    ngrok Cloud Service                           │
│  (ngrok.io infrastructure)                                        │
│  - Receives HTTPS requests                                      │
│  - Forwards to your local ngrok client                          │
│  - Provides SSL/TLS termination                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Encrypted Tunnel
                           │ (ngrok protocol)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR LOCAL MACHINE                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ngrok Client (running locally)                         │  │
│  │  Command: ngrok start ztna                               │  │
│  │  Config: tunnels.ztna.addr = 80                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           │ HTTP (localhost:80)                  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Network (ztna-network)                           │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  nginx (Port 80)                                    │  │  │
│  │  │  - Reverse proxy                                    │  │  │
│  │  │  - Routes requests to services                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │         │                                                  │  │
│  │         │ Routes based on path                            │  │
│  │         ├──────────────────────────────────────────────┐ │  │
│  │         │                                                │ │  │
│  │         ▼                                                ▼ │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  Frontend    │  │  Backend     │  │  Keycloak   │   │  │
│  │  │  :3000       │  │  :8000       │  │  :8080      │   │  │
│  │  │              │  │              │  │             │   │  │
│  │  │  /           │  │  /api        │  │  /auth       │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow: Remote Device → Backend

### Example: Device Enrollment Request

1. **Remote Device (DPA)**
   ```
   DPA sends: POST https://b64e34aa6da9.ngrok-free.app/api/devices/enroll
   ```

2. **ngrok Cloud Service**
   - Receives HTTPS request at `b64e34aa6da9.ngrok-free.app`
   - Establishes encrypted tunnel to your local ngrok client
   - Forwards request through tunnel

3. **Local ngrok Client**
   - Receives request through encrypted tunnel
   - Forwards to `localhost:80` (as configured in `ngrok.yml`)

4. **nginx (Port 80)**
   - Receives request at `localhost:80`
   - Matches path `/api/devices/enroll` → routes to `backend:8000`
   - Forwards request to backend container

5. **Backend (Port 8000)**
   - Processes enrollment request
   - Returns response

6. **Response Path (Reverse)**
   - Backend → nginx → ngrok client → ngrok cloud → Remote device

## nginx Routing Configuration

nginx acts as a reverse proxy, routing requests based on URL paths:

| Path | Destination | Service |
|------|-------------|---------|
| `/` | `frontend:3000` | React frontend |
| `/api/*` | `backend:8000` | FastAPI backend |
| `/auth/*` | `keycloak:8080` | Keycloak (with path rewriting) |

### Key nginx Configuration

```nginx
# Backend API routes
location /api {
    proxy_pass http://backend;  # → backend:8000
}

# Frontend routes
location / {
    proxy_pass http://frontend;  # → frontend:3000
}

# Keycloak routes
location /auth/ {
    proxy_pass http://keycloak/;  # → keycloak:8080 (strips /auth prefix)
}
```

## ngrok Configuration

### Configuration File Location
- Windows: `%USERPROFILE%\.ngrok2\ngrok.yml` or `%LOCALAPPDATA%\Packages\*\LocalState\ngrok.yml`

### Configuration Content
```yaml
version: "2"
authtoken: YOUR_NGROK_TOKEN
tunnels:
  ztna:
    addr: 80          # Forward to localhost:80 (nginx)
    proto: http
```

### Starting ngrok
```bash
ngrok start ztna
```

This creates a tunnel that:
- Listens on ngrok's cloud infrastructure
- Forwards all requests to `localhost:80` (your nginx)
- Provides a public HTTPS URL (e.g., `https://b64e34aa6da9.ngrok-free.app`)

## Why This Architecture?

### Single Tunnel Design
- **One ngrok tunnel** forwards to port 80 (nginx)
- **nginx routes** requests to appropriate services based on path
- **Simpler setup** - no need for multiple tunnels
- **Cost-effective** - free ngrok plan supports one tunnel

### Benefits
1. **No Port Forwarding**: No need to configure router/firewall
2. **HTTPS by Default**: ngrok provides SSL/TLS certificates
3. **Dynamic URLs**: Works even with dynamic IP addresses
4. **Secure**: Encrypted tunnel between ngrok cloud and your machine
5. **Easy Testing**: Remote devices can access your local development environment

## Security Considerations

### ngrok Security
- **Encrypted Tunnel**: All traffic between ngrok cloud and your machine is encrypted
- **HTTPS**: ngrok provides SSL/TLS termination
- **Authentication**: Requires ngrok authtoken

### Application Security
- **Backend Authentication**: Backend still requires proper authentication
- **CORS**: Backend handles CORS for allowed origins
- **Keycloak**: Handles OAuth/OIDC authentication

### Important Notes
⚠️ **Free ngrok URLs are temporary** - they change when you restart ngrok
⚠️ **Free ngrok has rate limits** - may not be suitable for production
⚠️ **ngrok URLs are public** - anyone with the URL can access (if they bypass ngrok warning)

## Testing Remote Device Connection

### 1. Verify ngrok is Running
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels
```

### 2. Test from Remote Device
```bash
# Test backend health endpoint
curl https://YOUR-NGROK-URL.ngrok-free.app/api/health

# Should return:
# {"status":"healthy","service":"ZTNA Backend API","version":"0.1.0"}
```

### 3. Configure DPA on Remote Device
```powershell
# Set backend URL to ngrok URL
$env:DPA_BACKEND_URL = "https://YOUR-NGROK-URL.ngrok-free.app"

# Or update config file
# C:\ProgramData\ZTNA\config.json
{
  "backend_url": "https://YOUR-NGROK-URL.ngrok-free.app"
}
```

## Troubleshooting

### Issue: Remote device can't connect
- **Check**: Is ngrok running? (`ngrok start ztna`)
- **Check**: Is nginx running? (`docker-compose ps`)
- **Check**: Is backend running? (`curl http://localhost:8000/health`)

### Issue: 502 Bad Gateway
- **Check**: Docker services are running (`docker-compose ps`)
- **Check**: nginx can reach backend (`docker-compose exec nginx curl http://backend:8000/health`)

### Issue: CORS errors
- **Check**: Backend CORS configuration includes ngrok URL
- **Check**: `EXTERNAL_CORS_ORIGINS` in `infra/.env` includes ngrok URL

## Production Considerations

For production, consider:
- **Static Domain**: Use ngrok paid plan for static domain
- **Custom Domain**: Configure custom domain with ngrok
- **Alternative**: Use Cloudflare Tunnel (free, supports custom domains)
- **Alternative**: Deploy to cloud (AWS, Azure, GCP) with proper networking

