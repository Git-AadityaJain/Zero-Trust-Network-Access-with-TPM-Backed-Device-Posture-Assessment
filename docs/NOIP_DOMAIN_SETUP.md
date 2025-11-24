# No-IP Domain Setup Guide

## 🎯 Overview

No-IP provides free dynamic DNS hostnames that you can use with Cloudflare Tunnel. This is perfect if you don't have your own domain name.

**What you'll get:**
- A free subdomain like: `yourname.ddns.net` or `yourname.zapto.org`
- Dynamic DNS updates (if needed)
- Works perfectly with Cloudflare Tunnel

## 📋 Prerequisites

- Email address (for account creation)
- Internet connection

## 🚀 Step-by-Step Setup

### Step 1: Create No-IP Account

1. **Go to No-IP website:**
   - Visit: https://www.noip.com/sign-up

2. **Fill in the registration form:**
   - **Username:** Choose a username (this will be part of your domain)
   - **Email:** Your email address
   - **Password:** Create a strong password
   - **Accept terms** and click **"Free Sign Up"**

3. **Verify your email:**
   - Check your email inbox
   - Click the verification link from No-IP
   - Your account will be activated

### Step 2: Create a Free Hostname

1. **Login to No-IP:**
   - Go to: https://www.noip.com/login
   - Enter your username and password

2. **Navigate to Dynamic DNS:**
   - After login, you'll see the dashboard
   - Click on **"Dynamic DNS"** in the top menu
   - Or go directly to: https://my.noip.com/dynamic-dns

3. **Create a Hostname:**
   - Click **"Create Hostname"** button

4. **Fill in the hostname details:**
   - **Hostname:** Choose a name (e.g., `ztna-app`)
   - **Domain:** Select from free domains:
     - `ddns.net` (most popular)
     - `zapto.org`
     - `hopto.org`
     - `duckdns.org`
     - `bounceme.net`
     - `serveftp.com`
     - `serveminecraft.net`
   
   **Example:** `ztna-app.ddns.net`
   
   - **IPv4 Address:** Leave as default (or enter your current IP if you know it)
   - **Record Type:** Select **"A"** (default)
   
5. **Click "Create Hostname"**

6. **Verify hostname is created:**
   - You should see your new hostname in the list
   - Status should show as "Active"

### Step 3: (Optional) Install No-IP DUC Client

**Note:** With Cloudflare Tunnel, you typically don't need the No-IP DUC (Dynamic Update Client) because Cloudflare Tunnel handles the connection. However, if you want to keep your No-IP hostname updated with your current IP (for other purposes), you can install it.

**Skip this step if you're only using Cloudflare Tunnel.**

**Windows:**
1. Download DUC from: https://www.noip.com/download
2. Install and run the application
3. Login with your No-IP credentials
4. Select your hostname
5. The client will automatically update your IP

### Step 4: Use Cloudflare Tunnel DNS Routing (Recommended)

**Important:** No-IP free domains typically don't allow nameserver changes, and you can't create CNAME records that reference themselves. The solution is to use **Cloudflare Tunnel's DNS routing feature**, which manages DNS records automatically without requiring nameserver changes.

**You don't need to add your domain to Cloudflare as a site!** Cloudflare Tunnel can create and manage DNS records directly.

**Skip to the Cloudflare Tunnel setup:**
- See: `docs/CLOUDFLARE_HOSTING_GUIDE.md`
- Follow Steps 1-3 (Install, Login, Create Tunnel)
- Then use Step 4 Method C (Cloudflare Tunnel DNS Routing) below

### Step 5: (Alternative) Add Domain to Cloudflare (If Nameservers Can Be Changed)

**Only use this method if your No-IP domain allows nameserver changes (most free domains don't):**

1. **Go to Cloudflare Dashboard:**
   - Visit: https://dash.cloudflare.com
   - Login to your Cloudflare account

2. **Add a Site:**
   - Click **"Add a Site"** button
   - Enter your No-IP domain (e.g., `ztna-app.ddns.net`)
   - Click **"Add site"**

3. **Select Plan:**
   - Choose **"Free"** plan
   - Click **"Continue"**

4. **Get Nameservers:**
   - Cloudflare will show you two nameservers
   - Example:
     - `alice.ns.cloudflare.com`
     - `bob.ns.cloudflare.com`
   - **Copy these nameservers!**

5. **Update Nameservers at No-IP:**
   - Go back to No-IP: https://my.noip.com
   - Navigate to **"Account"** → **"Domain Registration"** or **"Manage Domains"**
   - Find your domain (e.g., `ddns.net`)
   - Look for **"Nameservers"** or **"DNS Settings"**
   - Replace with Cloudflare's nameservers
   - Click **"Save"**

6. **Wait for DNS Propagation:**
   - Usually takes 1-2 hours
   - Cloudflare will show "Active" status when ready

**Note:** If you can't change nameservers, use Step 4 (Cloudflare Tunnel DNS Routing) instead.

### Step 6: Verify Setup

**If using Cloudflare Tunnel DNS Routing (Method C):**
- DNS records are created automatically when you run `cloudflared tunnel route dns`
- No manual verification needed
- Test after tunnel is running

**If using nameserver method:**
1. **Check DNS Status:**
   - In Cloudflare Dashboard, go to your site
   - Status should show **"Active"** (green checkmark)
   - If it shows "Pending", wait a bit longer

2. **Test DNS Resolution:**
   ```powershell
   nslookup yourname.ddns.net
   ```
   Should return Cloudflare IP addresses.

## 🔗 Next Steps

Once your No-IP hostname is created:

1. **Continue with Cloudflare Tunnel setup:**
   - See: `docs/CLOUDFLARE_HOSTING_GUIDE.md`
   - Follow Steps 1-3: Install cloudflared, Login, Create Tunnel
   - **Use Method C (Cloudflare Tunnel DNS Routing)** in Step 4
   - This will automatically create DNS records without needing nameserver changes

2. **Configure DNS routing (this creates DNS records automatically):**
   ```powershell
   cloudflared tunnel route dns ztna yourname.ddns.net
   ```
   **Note:** This command will:
   - Add your domain to Cloudflare automatically (if not already added)
   - Create the necessary DNS records
   - No nameserver changes needed!

3. **Update application configuration:**
   - Use `https://yourname.ddns.net` in your `.env` files
   - Update Keycloak redirect URIs

## 🔍 Troubleshooting

### Problem: Can't change nameservers at No-IP

**Solution:**
- **This is normal!** Most free No-IP domains don't support nameserver changes
- **Use Cloudflare Tunnel DNS Routing instead** (Method C in Cloudflare guide)
- Run: `cloudflared tunnel route dns ztna yourname.ddns.net`
- This automatically creates DNS records without needing nameserver changes
- **You don't need to add the domain to Cloudflare as a site first!**

### Problem: "CNAME cannot reference itself" error

**Solution:**
- This happens when trying to create a CNAME pointing to the same domain
- **Don't use CNAME method** - use Cloudflare Tunnel DNS Routing instead
- Run: `cloudflared tunnel route dns ztna yourname.ddns.net`
- This is the correct method for No-IP domains

### Problem: Domain not showing as Active in Cloudflare

**Check:**
- Nameservers are correctly updated at No-IP
- Wait 24 hours for full propagation
- Check Cloudflare Dashboard for any error messages

### Problem: DNS not resolving

**Solutions:**
1. Wait longer (DNS propagation can take time)
2. Clear DNS cache:
   ```powershell
   ipconfig /flushdns
   ```
3. Check nameservers are correct
4. Verify domain is active in both No-IP and Cloudflare

### Problem: No-IP account suspended

**Free accounts require:**
- Confirming your hostname every 30 days
- Logging in periodically
- Click "Confirm" on the hostname in No-IP dashboard

**To reactivate:**
- Login to No-IP
- Go to Dynamic DNS
- Click "Confirm" on your hostname

## 📝 Quick Reference

### No-IP Dashboard
- **Login:** https://my.noip.com
- **Dynamic DNS:** https://my.noip.com/dynamic-dns
- **Account Settings:** https://my.noip.com/account

### Free Domain Options
- `ddns.net` - Most popular
- `zapto.org`
- `hopto.org`
- `duckdns.org`
- `bounceme.net`
- `serveftp.com`
- `serveminecraft.net`

### Important Notes

1. **Free accounts require confirmation every 30 days**
   - Login to No-IP monthly
   - Click "Confirm" on your hostname
   - Set a reminder!

2. **No-IP free domains may have limitations:**
   - Some don't support nameserver changes
   - May have restrictions on DNS records
   - Check No-IP documentation for your specific domain

3. **Cloudflare Tunnel works without nameserver changes:**
   - You can use Cloudflare's DNS routing feature
   - See Cloudflare hosting guide for details

## 🎯 Summary

**What you've accomplished:**
- ✅ Created No-IP account
- ✅ Created free hostname (e.g., `yourname.ddns.net`)
- ✅ Added domain to Cloudflare
- ✅ Updated nameservers (if supported)
- ✅ Domain ready for Cloudflare Tunnel

**Your domain:** `https://yourname.ddns.net`

**Next:** Continue with Cloudflare Tunnel setup using this domain!

