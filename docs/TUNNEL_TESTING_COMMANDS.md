# Cloudflare Tunnel Testing Commands

This document provides commands to manually test and verify your Cloudflare Tunnel setup.

## 📋 Prerequisites

Make sure you're in PowerShell or Command Prompt with appropriate permissions.

---

## 1. Test Local Services (Docker & Nginx)

### Check if Docker containers are running:
```powershell
docker ps
```

**Expected:** Should show all containers (nginx, frontend, backend, keycloak, postgres, keycloak-db) with status "Up"

### Check specific container status:
```powershell
docker ps --filter "name=ztna-nginx"
docker ps --filter "name=ztna-frontend"
docker ps --filter "name=ztna-backend"
docker ps --filter "name=ztna-keycloak"
```

### View container logs (if issues):
```powershell
docker logs ztna-nginx
docker logs ztna-frontend
docker logs ztna-backend
docker logs ztna-keycloak
```

### Test nginx on localhost:80:
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:80" -UseBasicParsing

# Or using curl (if available)
curl http://localhost:80

# Or test health endpoint
curl http://localhost:80/health
```

**Expected:** Should return HTTP 200 with HTML content or "healthy"

### Test nginx with specific headers:
```powershell
Invoke-WebRequest -Uri "http://localhost:80" -Headers @{"Host"="ztna-app.ddns.net"} -UseBasicParsing
```

### Test backend API directly:
```powershell
curl http://localhost:8000/health
```

### Test frontend directly:
```powershell
curl http://localhost:3000
```

### Test Keycloak directly:
```powershell
curl http://localhost:8080
```

### Check if port 80 is listening:
```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 80 -ErrorAction SilentlyContinue

# Or using netstat
netstat -an | findstr ":80"
```

**Expected:** Should show port 80 is LISTENING

---

## 2. Test Cloudflare Tunnel Configuration

### Check if cloudflared is installed:
```powershell
cloudflared --version
```

**Expected:** Should show version number (e.g., "cloudflared version 2024.x.x")

### Check if logged in:
```powershell
cloudflared tunnel list
```

**Expected:** Should list your tunnels without authentication errors

### View tunnel information:
```powershell
cloudflared tunnel info ztna
```

**Expected:** Should show tunnel details (ID, name, created date)

### Check tunnel configuration file:
```powershell
# View config file location
$configPath = "$env:USERPROFILE\.cloudflared\config.yml"
Get-Content $configPath

# Or in CMD
type %USERPROFILE%\.cloudflared\config.yml
```

**Expected:** Should show valid YAML with:
- `tunnel: <tunnel-id>`
- `credentials-file: <path>`
- `ingress:` section with your domain and `service: http://localhost:80`

### Check credentials file exists:
```powershell
# List all credential files
Get-ChildItem "$env:USERPROFILE\.cloudflared\*.json"

# Or in CMD
dir %USERPROFILE%\.cloudflared\*.json
```

**Expected:** Should show at least one `.json` file (credentials file)

### Validate config file syntax:
```powershell
cloudflared tunnel ingress validate
```

**Expected:** Should show "Valid" or list any configuration errors

---

## 3. Test DNS Configuration

### List DNS routes configured for tunnel:
```powershell
# Check DNS routes via Cloudflare Dashboard or use:
cloudflared tunnel route ip list

# Or check specific tunnel routes (if supported):
cloudflared tunnel route list ztna
```

**Expected:** Should list your domain(s) associated with the tunnel

**Alternative:** Check via Cloudflare Dashboard or use DNS resolution test below

### Test DNS resolution (from your machine):
```powershell
# Replace with your actual domain
nslookup ztna-app.ddns.net

# Or using PowerShell
Resolve-DnsName ztna-app.ddns.net
```

**Expected:** Should resolve to a Cloudflare IP (usually starts with 104.x.x.x or 172.x.x.x)

### Test DNS from external service:
```powershell
# Using online DNS checker (open in browser)
Start-Process "https://dnschecker.org/#A/ztna-app.ddns.net"
```

**Expected:** Should show DNS records pointing to Cloudflare

### Check Cloudflare Dashboard DNS records:
```powershell
# Open Cloudflare dashboard
Start-Process "https://dash.cloudflare.com"
```

**Manual check:** Go to your domain → DNS → Records, should see CNAME record for your tunnel

---

## 4. Test Tunnel Connectivity

### Check if tunnel is currently running:
```powershell
# List running tunnels
cloudflared tunnel list

# Check tunnel status in Cloudflare
cloudflared tunnel info ztna
```

### Test tunnel with temporary URL (quick test):
```powershell
cloudflared tunnel --url http://localhost:80
```

**Expected:** Should output a temporary URL like `https://xxxx-xxxx-xxxx.trycloudflare.com`
**Note:** This is a quick test - if this works, your tunnel can connect. Press Ctrl+C to stop.

### Run tunnel in foreground (to see logs):
```powershell
cloudflared tunnel run ztna
```

**Expected:** Should show:
- "Connecting to Cloudflare..."
- "Connected to Cloudflare"
- "Route propagating, it may take up to 1 minute for your new route to become available"

**Keep this running** and test in another terminal window.

### Run tunnel with debug logging:
```powershell
# Try with logfile flag (if supported):
cloudflared tunnel run ztna --logfile tunnel.log

# Or just run normally and check output:
cloudflared tunnel run ztna
```

**Expected:** More detailed logs showing connection status, requests, etc.

### Test tunnel URL from browser:
```
# Replace with your actual domain
https://ztna-app.ddns.net
```

**Expected:** Should load your application

### Test tunnel URL with curl:
```powershell
# Replace with your actual domain
curl https://ztna-app.ddns.net

# Test health endpoint
curl https://ztna-app.ddns.net/health

# Test with verbose output
curl -v https://ztna-app.ddns.net
```

**Expected:** Should return HTTP 200 with content

### Test from external network (using online tool):
```powershell
# Open online HTTP checker
Start-Process "https://www.isitdownrightnow.com/ztna-app.ddns.net.html"
```

---

## 5. Test Network & Firewall

### Check Windows Firewall rules for port 80:
```powershell
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*80*" -or $_.DisplayName -like "*HTTP*"}
```

### Check if cloudflared is allowed through firewall:
```powershell
Get-NetFirewallApplicationFilter | Where-Object {$_.Program -like "*cloudflared*"}
```

### Test if localhost:80 is accessible from tunnel perspective:
```powershell
# Test from within a container (if needed)
docker exec ztna-nginx curl http://localhost:80
```

### Check network connectivity:
```powershell
# Test if you can reach Cloudflare
Test-NetConnection -ComputerName cloudflare.com -Port 443

# Test DNS resolution
Test-NetConnection -ComputerName ztna-app.ddns.net -Port 443
```

---

## 6. Test Application Endpoints

### Test frontend:
```powershell
curl http://localhost:80
curl https://ztna-app.ddns.net
```

### Test backend API:
```powershell
curl http://localhost:80/api/health
curl https://ztna-app.ddns.net/api/health
```

### Test Keycloak:
```powershell
curl http://localhost:80/auth
curl https://ztna-app.ddns.net/auth
```

### Test with specific Host header:
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:80" -Headers @{"Host"="ztna-app.ddns.net"} -UseBasicParsing

# Using curl
curl -H "Host: ztna-app.ddns.net" http://localhost:80
```

---

## 7. Troubleshooting Commands

### View detailed tunnel logs:
```powershell
cloudflared tunnel run ztna --loglevel debug 2>&1 | Tee-Object -FilePath tunnel-debug.log
```

### Check tunnel connection status:
```powershell
# In Cloudflare Dashboard
Start-Process "https://one.dash.cloudflare.com"
```

Navigate to: Zero Trust → Networks → Tunnels → Your Tunnel

### Verify nginx configuration:
```powershell
# Test nginx config syntax (from within container)
docker exec ztna-nginx nginx -t
```

### Check nginx access logs:
```powershell
docker exec ztna-nginx cat /var/log/nginx/access.log
```

### Check nginx error logs:
```powershell
docker exec ztna-nginx cat /var/log/nginx/error.log
```

### Restart services (if needed):
```powershell
cd "E:\Code Projects\ztna-project\infra"
docker-compose restart nginx
docker-compose restart
```

---

## 8. Quick Health Check Script

Run these commands in sequence for a complete check:

```powershell
Write-Host "=== Docker Containers ===" -ForegroundColor Cyan
docker ps --filter "name=ztna"

Write-Host "`n=== Local Services ===" -ForegroundColor Cyan
curl http://localhost:80/health

Write-Host "`n=== Cloudflare Tunnel ===" -ForegroundColor Cyan
cloudflared tunnel list

Write-Host "`n=== DNS Configuration ===" -ForegroundColor Cyan
cloudflared tunnel route dns list

Write-Host "`n=== DNS Resolution ===" -ForegroundColor Cyan
Resolve-DnsName ztna-app.ddns.net

Write-Host "`n=== Tunnel Config ===" -ForegroundColor Cyan
Get-Content "$env:USERPROFILE\.cloudflared\config.yml"
```

---

## Common Issues & Solutions

### Issue: "Tunnel not found"
**Solution:** 
```powershell
cloudflared tunnel list
# If empty, create tunnel:
cloudflared tunnel create ztna
```

### Issue: "Credentials file not found"
**Solution:**
```powershell
cloudflared tunnel login
```

### Issue: "Connection refused" when accessing tunnel URL
**Check:**
1. Is tunnel running? (`cloudflared tunnel run ztna`)
2. Is nginx accessible locally? (`curl http://localhost:80`)
3. Is DNS configured? (`cloudflared tunnel route dns list`)

### Issue: "502 Bad Gateway"
**Check:**
1. Are Docker containers running? (`docker ps`)
2. Is nginx running? (`docker logs ztna-nginx`)
3. Can you access localhost:80? (`curl http://localhost:80`)

### Issue: "DNS not resolving"
**Check:**
1. DNS route exists? (`cloudflared tunnel route dns list`)
2. Wait 1-2 minutes for DNS propagation
3. Check Cloudflare Dashboard for DNS records

---

## Notes

- Replace `ztna-app.ddns.net` with your actual domain
- Some commands require PowerShell, others work in CMD
- Keep tunnel running (`cloudflared tunnel run ztna`) while testing
- DNS changes can take 1-2 minutes to propagate
- Use `--loglevel debug` for detailed troubleshooting

