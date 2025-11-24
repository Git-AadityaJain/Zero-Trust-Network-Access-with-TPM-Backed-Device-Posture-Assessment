# Windows Firewall Configuration Script for ZTNA External Access
# Run as Administrator
#
# Why is this needed?
# Even though services run in Docker containers, when Docker exposes ports
# (e.g., "80:80" in docker-compose.yml), those ports are bound to the Windows
# host. Windows Firewall controls access to the host's ports, so we need
# rules to allow external connections to reach Docker-bound ports.
#
# See docs/DOCKER_WINDOWS_FIREWALL_EXPLANATION.md for details

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ZTNA Windows Firewall Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Configuring Windows Firewall rules..." -ForegroundColor Green
Write-Host ""

# Remove existing rules if they exist (to avoid duplicates)
$existingRule80 = Get-NetFirewallRule -DisplayName "ZTNA HTTP" -ErrorAction SilentlyContinue
$existingRule8080 = Get-NetFirewallRule -DisplayName "ZTNA Keycloak" -ErrorAction SilentlyContinue

if ($existingRule80) {
    Write-Host "Removing existing HTTP rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "ZTNA HTTP" -ErrorAction SilentlyContinue
}

if ($existingRule8080) {
    Write-Host "Removing existing Keycloak rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "ZTNA Keycloak" -ErrorAction SilentlyContinue
}

# Create firewall rules
try {
    # Port 80 - HTTP (Frontend/Backend via Nginx)
    Write-Host "Creating firewall rule for port 80 (HTTP)..." -ForegroundColor Cyan
    New-NetFirewallRule -DisplayName "ZTNA HTTP" `
        -Direction Inbound `
        -LocalPort 80 `
        -Protocol TCP `
        -Action Allow `
        -Description "ZTNA Platform - HTTP access for frontend and backend" `
        -ErrorAction Stop
    
    Write-Host "  ✓ Port 80 rule created successfully" -ForegroundColor Green
    
    # Port 8080 - Keycloak
    Write-Host "Creating firewall rule for port 8080 (Keycloak)..." -ForegroundColor Cyan
    New-NetFirewallRule -DisplayName "ZTNA Keycloak" `
        -Direction Inbound `
        -LocalPort 8080 `
        -Protocol TCP `
        -Action Allow `
        -Description "ZTNA Platform - Keycloak authentication service" `
        -ErrorAction Stop
    
    Write-Host "  ✓ Port 8080 rule created successfully" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Firewall Configuration Complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Firewall rules created:" -ForegroundColor Yellow
    Write-Host "  - Port 80:  HTTP (Frontend/Backend)" -ForegroundColor White
    Write-Host "  - Port 8080: Keycloak" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Configure router port forwarding (ports 80 and 8080)" -ForegroundColor White
    Write-Host "  2. Restart Docker services: cd infra && docker-compose restart" -ForegroundColor White
    Write-Host "  3. Test external access from another device" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create firewall rules" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

