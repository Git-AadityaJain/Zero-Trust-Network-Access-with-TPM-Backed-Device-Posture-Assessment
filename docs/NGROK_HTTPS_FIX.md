# Fixing HTTPS/Mixed Content Issues with ngrok

## Problem
When accessing Keycloak admin console through ngrok, you may see:
- CSP (Content Security Policy) violations
- Mixed content errors (HTTP resources on HTTPS page)
- Timeout errors in the admin console

## Root Cause
Keycloak is generating HTTP URLs even though requests come through HTTPS (ngrok). This happens because:
1. Keycloak doesn't know its frontend URL is HTTPS
2. Keycloak needs to be configured to trust proxy headers

## Solution

### 1. Update infra/.env with HTTPS Keycloak URL

After running `update_ngrok_urls.ps1`, make sure `infra/.env` has:
```
EXTERNAL_KEYCLOAK_URL=https://your-domain.ngrok-free.app/auth
```

### 2. Restart Keycloak Container

Keycloak reads `KC_HOSTNAME_URL` from environment variables at startup. After updating `infra/.env`:

```bash
cd infra
docker-compose restart keycloak
```

Or rebuild:
```bash
docker-compose up -d --force-recreate keycloak
```

### 3. Verify Configuration

Check that Keycloak is using the correct frontend URL:
```bash
docker-compose exec keycloak env | grep KC_HOSTNAME
```

Should show:
```
KC_HOSTNAME_URL=https://your-domain.ngrok-free.app/auth
```

### 4. Clear Browser Cache

Clear your browser cache and cookies for the ngrok domain, then try accessing the admin console again.

## Alternative: Manual Keycloak Configuration

If the above doesn't work, you can manually set the frontend URL in Keycloak:

1. Access Keycloak Admin: `https://your-domain.ngrok-free.app/auth/admin`
2. Go to **Realm Settings** → **General**
3. Set **Frontend URL** to: `https://your-domain.ngrok-free.app/auth`
4. Save

## Troubleshooting

### Check Keycloak Logs
```bash
docker-compose logs keycloak | grep -i hostname
```

### Verify Proxy Headers
The nginx configuration should set:
- `X-Forwarded-Proto: https`
- `X-Forwarded-Host: your-domain.ngrok-free.app`

### Test Keycloak Well-Known Endpoint
```bash
curl -H "X-Forwarded-Proto: https" \
     -H "X-Forwarded-Host: your-domain.ngrok-free.app" \
     https://your-domain.ngrok-free.app/auth/realms/master/.well-known/openid-configuration
```

Check that all URLs in the response use `https://` not `http://`.

