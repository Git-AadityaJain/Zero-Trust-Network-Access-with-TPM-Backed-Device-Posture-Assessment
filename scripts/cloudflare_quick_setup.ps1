# Cloudflare Tunnel Quick Setup Script
# This script automates the initial Cloudflare Tunnel setup process

param(
    [string]$Domain = "",
    [switch]$SkipDns = $false
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Cloudflare Tunnel Quick Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared is installed
try {
    $cloudflaredVersion = cloudflared --version 2>&1
    Write-Host "✓ cloudflared is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ cloudflared is not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install cloudflared first:" -ForegroundColor Yellow
    Write-Host "  winget install --id Cloudflare.cloudflared" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor White
    Write-Host "  choco install cloudflared" -ForegroundColor White
    exit 1
}

# Step 1: Login
Write-Host ""
Write-Host "Step 1: Login to Cloudflare" -ForegroundColor Yellow
Write-Host "This will open your browser for authentication..." -ForegroundColor White
$login = Read-Host "Have you already logged in? (y/n)"
if ($login -ne "y") {
    Write-Host "Running: cloudflared tunnel login" -ForegroundColor Cyan
    cloudflared tunnel login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Login failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Login successful" -ForegroundColor Green
} else {
    Write-Host "✓ Skipping login" -ForegroundColor Green
}

# Step 2: Create tunnel
Write-Host ""
Write-Host "Step 2: Create Tunnel" -ForegroundColor Yellow
$tunnelExists = cloudflared tunnel list 2>&1 | Select-String "ztna"
if ($tunnelExists) {
    Write-Host "✓ Tunnel 'ztna' already exists" -ForegroundColor Green
    $tunnelInfo = cloudflared tunnel info ztna 2>&1
    $tunnelIdMatch = $tunnelInfo | Select-String -Pattern "ID:\s+([a-f0-9-]+)"
    if ($tunnelIdMatch) {
        $tunnelId = $tunnelIdMatch.Matches[0].Groups[1].Value
        Write-Host "  Tunnel ID: $tunnelId" -ForegroundColor White
    }
} else {
    Write-Host "Creating tunnel 'ztna'..." -ForegroundColor Cyan
    $tunnelOutput = cloudflared tunnel create ztna 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to create tunnel" -ForegroundColor Red
        Write-Host $tunnelOutput -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Tunnel created" -ForegroundColor Green
    
    # Extract tunnel ID
    $tunnelIdMatch = $tunnelOutput | Select-String -Pattern "Created tunnel\s+([a-f0-9-]+)"
    if ($tunnelIdMatch) {
        $tunnelId = $tunnelIdMatch.Matches[0].Groups[1].Value
        Write-Host "  Tunnel ID: $tunnelId" -ForegroundColor White
    } else {
        # Try to get it from tunnel list
        $tunnelInfo = cloudflared tunnel info ztna 2>&1
        $tunnelIdMatch = $tunnelInfo | Select-String -Pattern "ID:\s+([a-f0-9-]+)"
        if ($tunnelIdMatch) {
            $tunnelId = $tunnelIdMatch.Matches[0].Groups[1].Value
        }
    }
}

if (-not $tunnelId) {
    Write-Host "⚠ Could not determine tunnel ID. Please check manually:" -ForegroundColor Yellow
    Write-Host "  cloudflared tunnel list" -ForegroundColor White
    $tunnelId = Read-Host "Enter tunnel ID manually"
}

# Step 3: DNS Configuration
if (-not $SkipDns) {
    Write-Host ""
    Write-Host "Step 3: DNS Configuration" -ForegroundColor Yellow
    
    if (-not $Domain) {
        $Domain = Read-Host "Enter your domain (e.g., app.yourdomain.com)"
    }
    
    if ($Domain) {
        Write-Host "Creating DNS record for: $Domain" -ForegroundColor Cyan
        cloudflared tunnel route dns ztna $Domain
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ DNS record created" -ForegroundColor Green
        } else {
            Write-Host "⚠ DNS record creation failed. You may need to create it manually in Cloudflare Dashboard" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ Skipping DNS configuration" -ForegroundColor Yellow
        Write-Host "  You can create DNS records later using:" -ForegroundColor White
        Write-Host "  cloudflared tunnel route dns ztna yourdomain.com" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "Step 3: DNS Configuration (Skipped)" -ForegroundColor Yellow
    if (-not $Domain) {
        $Domain = Read-Host "Enter your domain for configuration file"
    }
}

# Step 4: Create config file
Write-Host ""
Write-Host "Step 4: Create Configuration File" -ForegroundColor Yellow

if ($Domain) {
    Write-Host "Running setup script..." -ForegroundColor Cyan
    & "$PSScriptRoot\setup_cloudflare_tunnel.ps1" -TunnelId $tunnelId -Domain $Domain
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Configuration file created" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to create configuration file" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠ No domain provided. Skipping config file creation." -ForegroundColor Yellow
    Write-Host "  Run manually: .\scripts\setup_cloudflare_tunnel.ps1 -TunnelId `"$tunnelId`" -Domain `"yourdomain.com`"" -ForegroundColor White
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update application configuration:" -ForegroundColor White
Write-Host "   - Update infra/.env with your domain" -ForegroundColor Gray
Write-Host "   - Update realm-export.json with your domain" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Restart Docker services:" -ForegroundColor White
Write-Host "   cd infra" -ForegroundColor Gray
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the tunnel:" -ForegroundColor White
Write-Host "   cloudflared tunnel run ztna" -ForegroundColor Gray
Write-Host ""
Write-Host "   Or install as Windows Service:" -ForegroundColor White
Write-Host "   cloudflared service install" -ForegroundColor Gray
Write-Host "   cloudflared service start" -ForegroundColor Gray
Write-Host ""
if ($Domain) {
    Write-Host "Your application will be available at:" -ForegroundColor Green
    Write-Host "  https://$Domain" -ForegroundColor White
    Write-Host "  https://$Domain/auth (Keycloak)" -ForegroundColor White
}
Write-Host ""

