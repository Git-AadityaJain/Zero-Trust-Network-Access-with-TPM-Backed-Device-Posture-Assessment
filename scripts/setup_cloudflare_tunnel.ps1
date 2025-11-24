# Cloudflare Tunnel Setup Helper Script
# This script helps create the Cloudflare Tunnel configuration

param(
    [Parameter(Mandatory=$true)]
    [string]$TunnelId,
    
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [string]$KeycloakSubdomain = ""
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Cloudflare Tunnel Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$configDir = "$env:USERPROFILE\.cloudflared"
$configFile = "$configDir\config.yml"
$credentialsFile = "$configDir\$TunnelId.json"

# Expand environment variables in paths
$credentialsFile = [System.Environment]::ExpandEnvironmentVariables($credentialsFile)

# Create directory if it doesn't exist
if (-not (Test-Path $configDir)) {
    Write-Host "Creating directory: $configDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Check if credentials file exists
if (-not (Test-Path $credentialsFile)) {
    Write-Host "Warning: Credentials file not found: $credentialsFile" -ForegroundColor Yellow
    Write-Host "Make sure you've run: cloudflared tunnel login" -ForegroundColor Yellow
    Write-Host ""
}

# Create config content
if ($KeycloakSubdomain) {
    # Two separate subdomains
    # Use Windows-style path for credentials file
    $credentialsPath = $credentialsFile.Replace('\', '/')
    $configContent = @"
tunnel: $TunnelId
credentials-file: $credentialsPath

ingress:
  # Frontend
  - hostname: $Domain
    service: http://localhost:80
  # Keycloak
  - hostname: $KeycloakSubdomain
    service: http://localhost:8080
  # Catch-all
  - service: http_status:404
"@
} else {
    # Single domain with nginx routing (simpler)
    # Use Windows-style path for credentials file
    $credentialsPath = $credentialsFile.Replace('\', '/')
    $configContent = @"
tunnel: $TunnelId
credentials-file: $credentialsPath

ingress:
  # Frontend (nginx routes /auth to Keycloak)
  - hostname: $Domain
    service: http://localhost:80
  # Catch-all
  - service: http_status:404
"@
}

try {
    Set-Content -Path $configFile -Value $configContent
    Write-Host "Configuration file created: $configFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Yellow
    Write-Host "  - Tunnel ID: $TunnelId" -ForegroundColor White
    Write-Host "  - Domain: $Domain" -ForegroundColor White
    if ($KeycloakSubdomain) {
        Write-Host "  - Keycloak: $KeycloakSubdomain" -ForegroundColor White
    } else {
        Write-Host "  - Keycloak: $Domain/auth (via nginx)" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Add DNS records in Cloudflare Dashboard" -ForegroundColor White
    Write-Host "2. Start tunnel: cloudflared tunnel run ztna" -ForegroundColor White
    Write-Host "3. Update application configuration with: $Domain" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "Failed to create config file: $_" -ForegroundColor Red
    exit 1
}

