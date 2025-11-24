# Troubleshooting DNS Record Conflict

## Problem
Error: "An A, AAAA, or CNAME record with that host already exists"

This happens when Cloudflare already has a DNS record for your domain.

## Solution: Check and Delete Existing Records

### Step 1: Check if Domain is in Cloudflare

1. Go to Cloudflare Dashboard: https://dash.cloudflare.com
2. Check if `ztna-app.ddns.net` (or `ddns.net`) is listed in your sites
3. If it is, click on it

### Step 2: Check DNS Records

1. In the Cloudflare Dashboard, go to **DNS** → **Records**
2. Look for any records for `ztna-app.ddns.net`:
   - A records
   - AAAA records  
   - CNAME records
3. **Delete any existing records** for `ztna-app.ddns.net`

### Step 3: Retry Tunnel Route

After deleting the conflicting records, run:
```powershell
cloudflared tunnel route dns ztna ztna-app.ddns.net
```

## Alternative: Use a Different Subdomain

If you want to keep the existing record, use a different subdomain:
```powershell
cloudflared tunnel route dns ztna app.ztna-app.ddns.net
```

Then update your configuration to use `app.ztna-app.ddns.net` instead.

