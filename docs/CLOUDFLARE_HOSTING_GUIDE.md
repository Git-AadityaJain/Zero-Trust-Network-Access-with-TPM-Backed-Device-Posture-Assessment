# Cloudflare Tunnel Hosting Guide

## 🎯 Overview

This guide will help you host your ZTNA application using Cloudflare Tunnel (cloudflared). This method allows you to expose your Docker containers to the internet without:
- Port forwarding on your router
- Public IP address
- Opening firewall ports
- Upstream router configuration

**How it works:**
- Cloudflare Tunnel creates a secure connection from your local machine to Cloudflare's network
- Traffic flows: `Internet → Cloudflare → Tunnel → Your Local Containers`
- All traffic is encrypted and secure by default

## 📋 Prerequisites

1. **Cloudflare Account** (free tier works)
   - Sign up at: https://dash.cloudflare.com/sign-up
   
2. **Domain Name** (choose one option)
   - Option A: Use your own domain (add it to Cloudflare)
   - Option B: Use No-IP free domain (see `docs/NOIP_DOMAIN_SETUP.md`)
   - Option C: Use Cloudflare's temporary domain (e.g., `yourname.trycloudflare.com` - changes each time)

3. **Docker containers running locally**
   - Your application should be running via `docker-compose up`

## 🚀 Step-by-Step Setup

### Quick Start (Automated)

For a faster setup, use the automated script:

```powershell
.\scripts\cloudflare_quick_setup.ps1 -Domain "yourdomain.com"
```

This script will:
- Check if cloudflared is installed
- Guide you through login
- Create the tunnel
- Configure DNS
- Create configuration file

**Then continue from Step 6** (Update Application Configuration).

### Manual Setup

If you prefer to set up manually or need more control:

### Step 1: Install cloudflared

**Windows (PowerShell as Administrator):**
```powershell
# Download and install cloudflared
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "$env:ProgramFiles\cloudflared\cloudflared.exe"
```

**Or use Chocolatey:**
```powershell
choco install cloudflared
```

**Or use winget:**
```powershell
winget install --id Cloudflare.cloudflared
```

**Verify installation:**
```powershell
cloudflared --version
```

**If you get "command not found" error:**
- **Option 1:** Close and reopen PowerShell (PATH updates require new session)
- **Option 2:** Refresh PATH in current session:
  ```powershell
  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
  cloudflared --version
  ```

### Step 2: Login to Cloudflare

```powershell
cloudflared tunnel login
```

This will:
1. Open your browser
2. Ask you to select your Cloudflare account
3. Authorize the tunnel
4. Save credentials to `%USERPROFILE%\.cloudflared\*.json`

### Step 3: Create a Tunnel

```powershell
cloudflared tunnel create ztna
```

This creates a tunnel named "ztna" and outputs a Tunnel ID (looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**Save the Tunnel ID!** You'll need it for configuration.

### Step 4: Configure DNS (Choose One Method)

#### Method A: Using Your Own Domain or No-IP Domain

1. **Add your domain to Cloudflare** (if not already added)
   - Go to Cloudflare Dashboard → Add a Site
   - Enter your domain (e.g., `yourdomain.com` or `yourname.ddns.net`)
   - Follow the instructions to add your domain
   - Update your domain's nameservers at your registrar (or No-IP if using No-IP)
   - **For No-IP setup:** See `docs/NOIP_DOMAIN_SETUP.md` for detailed instructions

2. **Wait for DNS propagation:**
   - Cloudflare will show "Active" status when ready
   - Usually takes 1-2 hours, can take up to 24 hours

3. **Create DNS record for your app:**
   ```powershell
   cloudflared tunnel route dns ztna yourdomain.com
   ```
   Replace `yourdomain.com` with your actual domain (e.g., `yourname.ddns.net`).

4. **Optional: Create subdomain for Keycloak** (if you want separate subdomain):
   ```powershell
   cloudflared tunnel route dns ztna auth.yourdomain.com
   ```

#### Method B: Using Cloudflare's Free Domain (Quick Start)

If you don't have a domain, Cloudflare can provide a temporary subdomain:

```powershell
cloudflared tunnel --url http://localhost:80
```

This will give you a temporary URL like: `https://xxxx-xxxx-xxxx.trycloudflare.com`

**Note:** This is temporary and changes each time. For permanent hosting, use Method A or C.

#### Method C: Cloudflare Tunnel DNS Routing (For No-IP and domains without nameserver access)

**This is the recommended method for No-IP domains!** It works without nameserver changes or CNAME records.

1. **Create DNS record using Cloudflare Tunnel:**
   ```powershell
   cloudflared tunnel route dns ztna yourname.ddns.net
   ```
   Replace `yourname.ddns.net` with your No-IP hostname.

2. **What this does:**
   - Automatically adds your domain to Cloudflare (if not already added)
   - Creates the necessary DNS records
   - No nameserver changes needed!
   - No CNAME records needed!

3. **Verify it worked:**
   ```powershell
   cloudflared tunnel route dns list
   ```
   Should show your domain.

**This method is perfect for:**
- No-IP free domains (which don't allow nameserver changes)
- Any domain where you can't change nameservers
- Quick setup without manual DNS configuration

### Step 5: Configure Tunnel

Create the tunnel configuration file:

**Location:** `%USERPROFILE%\.cloudflared\config.yml`

**For single domain (nginx routes everything):**
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: %USERPROFILE%\.cloudflared\YOUR_TUNNEL_ID.json

ingress:
  # Main application (nginx handles routing)
  - hostname: yourdomain.com
    service: http://localhost:80
  # Catch-all (must be last)
  - service: http_status:404
```

**For separate subdomains:**
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: %USERPROFILE%\.cloudflared\YOUR_TUNNEL_ID.json

ingress:
  # Frontend
  - hostname: yourdomain.com
    service: http://localhost:80
  # Keycloak (separate subdomain)
  - hostname: auth.yourdomain.com
    service: http://localhost:8080
  # Catch-all (must be last)
  - service: http_status:404
```

**Replace:**
- `YOUR_TUNNEL_ID` with the tunnel ID from Step 3
- `yourdomain.com` with your actual domain

**Or use the helper script:**
```powershell
.\scripts\setup_cloudflare_tunnel.ps1 -TunnelId "YOUR_TUNNEL_ID" -Domain "yourdomain.com"
```

### Step 6: Update Application Configuration

Update your application to use the Cloudflare domain instead of localhost.

**Update `infra/.env` (create if it doesn't exist):**
```env
EXTERNAL_FRONTEND_URL=https://yourdomain.com
EXTERNAL_KEYCLOAK_URL=https://yourdomain.com/auth
EXTERNAL_CORS_ORIGINS=https://yourdomain.com,http://localhost:3000
```

**Update `infra/nginx/conf.d/default.conf`:**
```nginx
server {
    listen 80;
    server_name localhost yourdomain.com;
    # ... rest of config
}
```

**Update `realm-export.json`:**
- Find all instances of old URLs/IPs
- Replace with: `https://yourdomain.com`
- Update redirect URIs, web origins, etc.

### Step 7: Update Keycloak Configuration

1. **Access Keycloak Admin Console:**
   - Local: `http://localhost:8080/admin`
   - Or via tunnel: `https://yourdomain.com/auth/admin`

2. **Login:** `admin` / `adminsecure123`

3. **Navigate:** Clients → admin-frontend

4. **Update:**
   - **Valid Redirect URIs:** `https://yourdomain.com/callback`
   - **Web Origins:** `https://yourdomain.com`
   - **Post Logout Redirect URIs:** `https://yourdomain.com/login`

5. **Save**

### Step 8: Restart Docker Services

```powershell
cd "E:\Code Projects\ztna-project\infra"
docker-compose down
docker-compose up -d
```

### Step 9: Start the Tunnel

**Run tunnel manually:**
```powershell
cloudflared tunnel run ztna
```

**Or run as Windows Service (recommended for production):**

1. **Install as service:**
   ```powershell
   cloudflared service install
   ```

2. **Start service:**
   ```powershell
   cloudflared service start
   ```

3. **Check status:**
   ```powershell
   cloudflared service status
   ```

**Or add to docker-compose (optional):**

You can add cloudflared as a service in your `docker-compose.yml`:

```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: ztna-cloudflared
    command: tunnel run
    volumes:
      - $HOME/.cloudflared:/etc/cloudflared
    depends_on:
      - nginx
    networks:
      - ztna-network
```

### Step 10: Test Your Application

1. **Open browser:** `https://yourdomain.com`
2. **Should see:** Your login page
3. **Test authentication:** Login should work via Keycloak
4. **Test from different network:** Access from mobile data or different WiFi

## 🔧 Advanced Configuration

### Running Tunnel as Docker Service

Add to `infra/docker-compose.yml`:

```yaml
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: ztna-cloudflared
    restart: unless-stopped
    command: tunnel --config /etc/cloudflared/config.yml run
    volumes:
      - $HOME/.cloudflared:/etc/cloudflared:ro
    depends_on:
      - nginx
    networks:
      - ztna-network
```

**Note:** On Windows, you may need to adjust the volume path:
```yaml
volumes:
  - C:/Users/YOUR_USERNAME/.cloudflared:/etc/cloudflared:ro
```

### Using Environment Variables

Create `infra/.env`:
```env
CLOUDFLARE_TUNNEL_ID=your-tunnel-id
CLOUDFLARE_DOMAIN=yourdomain.com
EXTERNAL_FRONTEND_URL=https://${CLOUDFLARE_DOMAIN}
EXTERNAL_KEYCLOAK_URL=https://${CLOUDFLARE_DOMAIN}/auth
EXTERNAL_CORS_ORIGINS=https://${CLOUDFLARE_DOMAIN},http://localhost:3000
```

### HTTPS/SSL

Cloudflare Tunnel automatically provides HTTPS! No SSL certificate configuration needed.

- All traffic is encrypted between Cloudflare and your tunnel
- Cloudflare provides free SSL certificates
- Your domain will be accessible via `https://` automatically

## 🔍 Troubleshooting

### Problem: Tunnel won't start

**Check:**
- ✅ Credentials file exists: `%USERPROFILE%\.cloudflared\*.json`
- ✅ Config file exists: `%USERPROFILE%\.cloudflared\config.yml`
- ✅ Tunnel ID is correct in config
- ✅ Docker containers are running (`docker ps`)

**View logs:**
```powershell
cloudflared tunnel run ztna --loglevel debug
```

### Problem: Can't access website

**Checklist:**
- ✅ Tunnel is running (`cloudflared tunnel list`)
- ✅ DNS records are correct (check Cloudflare Dashboard)
- ✅ Docker containers are running
- ✅ Nginx is accessible locally: `http://localhost:80`
- ✅ Application config updated with correct domain

**Test locally first:**
```powershell
# Test nginx
curl http://localhost:80

# Test frontend
curl http://localhost:3000

# Test backend
curl http://localhost:8000/health
```

### Problem: Keycloak redirect issues

**Solutions:**
1. Update Keycloak client configuration (Step 7)
2. Update `realm-export.json` with correct URLs
3. Restart Keycloak container
4. Clear browser cache/cookies

### Problem: CORS errors

**Check:**
- ✅ `EXTERNAL_CORS_ORIGINS` in `.env` includes your domain
- ✅ Backend CORS middleware is configured correctly
- ✅ Domain uses `https://` (not `http://`)

### Problem: Tunnel disconnects

**Solutions:**
- Run tunnel as Windows Service (more stable)
- Or add to docker-compose with `restart: unless-stopped`
- Check network connectivity
- Check Cloudflare Dashboard for tunnel status

## 📝 Quick Reference

### Common Commands

```powershell
# List tunnels
cloudflared tunnel list

# View tunnel info
cloudflared tunnel info ztna

# Delete tunnel
cloudflared tunnel delete ztna

# Run tunnel
cloudflared tunnel run ztna

# Run with debug logs
cloudflared tunnel run ztna --loglevel debug

# Service management
cloudflared service install
cloudflared service start
cloudflared service stop
cloudflared service uninstall
```

### File Locations

- **Config:** `%USERPROFILE%\.cloudflared\config.yml`
- **Credentials:** `%USERPROFILE%\.cloudflared\*.json`
- **Logs:** Check Windows Event Viewer or console output

## 🎯 Summary

**What Cloudflare Tunnel does:**
- Creates secure connection from your local machine to Cloudflare
- Routes internet traffic to your local Docker containers
- Provides free HTTPS/SSL automatically
- No port forwarding or public IP needed

**Your application is accessible at:**
- `https://yourdomain.com` (main app)
- `https://yourdomain.com/auth` (Keycloak, via nginx)
- `https://yourdomain.com/api` (backend API, via nginx)

**Benefits:**
- ✅ No router configuration needed
- ✅ Works behind any firewall/NAT
- ✅ Free HTTPS/SSL
- ✅ DDoS protection (Cloudflare)
- ✅ Secure by default

That's it! Your application is now accessible from anywhere on the internet. 🚀

