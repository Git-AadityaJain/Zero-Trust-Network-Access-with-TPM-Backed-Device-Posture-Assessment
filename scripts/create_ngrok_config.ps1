# Create ngrok Configuration File for Multiple Tunnels
# Usage: .\scripts\create_ngrok_config.ps1 -Authtoken "YOUR_TOKEN"

param(
    [Parameter(Mandatory=$true)]
    [string]$Authtoken
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Create ngrok Configuration File" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check for Microsoft Store installation first
$storePackagePath = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Filter "*ngrok*" -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
if ($storePackagePath) {
    $configDir = Join-Path $storePackagePath.FullName "LocalState"
    $configFile = Join-Path $configDir "ngrok.yml"
    Write-Host "Detected Microsoft Store installation" -ForegroundColor Cyan
} else {
    # Default ngrok config location for Windows
    $configDir = "$env:USERPROFILE\.ngrok2"
    $configFile = "$configDir\ngrok.yml"
}

# Alternative location (some installations use this)
$altConfigDir = "$env:APPDATA\ngrok"
$altConfigFile = "$altConfigDir\ngrok.yml"

Write-Host "Creating ngrok configuration file..." -ForegroundColor Cyan
Write-Host ""

# Create directory if it doesn't exist
if (-not (Test-Path $configDir)) {
    Write-Host "Creating directory: $configDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Create config file content
# Single tunnel on port 80 - nginx routes /auth to Keycloak
$configContent = @"
version: "2"
authtoken: $Authtoken
tunnels:
  ztna:
    addr: 80
    proto: http
"@

try {
    # Write to primary location
    Set-Content -Path $configFile -Value $configContent
    Write-Host "Configuration file created: $configFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Yellow
    Write-Host "  - Single tunnel: port 80 (nginx routes /auth to Keycloak)" -ForegroundColor White
    Write-Host ""
    Write-Host "To start the tunnel, run:" -ForegroundColor Yellow
    Write-Host "  ngrok start ztna" -ForegroundColor Cyan
    Write-Host "  OR" -ForegroundColor Gray
    Write-Host "  ngrok http 80" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "Failed to create config file: $_" -ForegroundColor Red
    exit 1
}

# Also try alternative location (some ngrok versions use this)
if (-not (Test-Path $altConfigDir)) {
    try {
        New-Item -ItemType Directory -Path $altConfigDir -Force | Out-Null
        Set-Content -Path $altConfigFile -Value $configContent
        Write-Host "Also created config file at: $altConfigFile" -ForegroundColor Green
    } catch {
        Write-Host "Could not create alternative config file (this is OK)" -ForegroundColor Yellow
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Make sure Docker services are running" -ForegroundColor Yellow
Write-Host "2. Start ngrok tunnel: ngrok start ztna" -ForegroundColor Yellow
Write-Host "3. Copy the HTTPS URL ngrok displays (e.g., https://abc123.ngrok.io)" -ForegroundColor Yellow
Write-Host "4. Update configuration using update_ngrok_urls.ps1 script" -ForegroundColor Yellow
Write-Host "   Note: Use the same URL for both frontend and keycloak (keycloak is at /auth)" -ForegroundColor Gray
Write-Host ""

