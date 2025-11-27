# Fix Keycloak Hostname Configuration for ngrok
# This script extracts the hostname from EXTERNAL_KEYCLOAK_URL and sets KC_HOSTNAME

param(
    [string]$NgrokUrl = ""
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fix Keycloak Hostname Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Read infra/.env to get EXTERNAL_KEYCLOAK_URL
$envFile = "infra\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: infra/.env not found. Run update_ngrok_urls.ps1 first." -ForegroundColor Red
    exit 1
}

$envContent = Get-Content $envFile
$keycloakUrl = ""

foreach ($line in $envContent) {
    if ($line -match '^\s*EXTERNAL_KEYCLOAK_URL\s*=\s*(.+)') {
        $keycloakUrl = $matches[1].Trim()
        break
    }
}

if (-not $keycloakUrl) {
    Write-Host "ERROR: EXTERNAL_KEYCLOAK_URL not found in infra/.env" -ForegroundColor Red
    exit 1
}

# Extract hostname from URL (remove https:// and /auth path)
$hostname = $keycloakUrl -replace '^https?://', '' -replace '/auth.*$', '' -replace '/$', ''

Write-Host "Extracted hostname: $hostname" -ForegroundColor Yellow
Write-Host ""

# Update docker-compose.yml to set KC_HOSTNAME
$composeFile = "infra\docker-compose.yml"
if (-not (Test-Path $composeFile)) {
    Write-Host "ERROR: infra/docker-compose.yml not found" -ForegroundColor Red
    exit 1
}

$composeContent = Get-Content $composeFile -Raw

# Check if KC_HOSTNAME is already set
if ($composeContent -match 'KC_HOSTNAME=') {
    # Update existing KC_HOSTNAME
    $composeContent = $composeContent -replace 'KC_HOSTNAME=\$\{KC_HOSTNAME:.*?\}', "KC_HOSTNAME=`${KC_HOSTNAME:-$hostname}"
    Write-Host "Updated KC_HOSTNAME in docker-compose.yml" -ForegroundColor Green
} else {
    # Add KC_HOSTNAME after KC_PROXY_HEADERS
    $composeContent = $composeContent -replace '(KC_PROXY_HEADERS=xforwarded)', "`$1`n      - KC_HOSTNAME=$hostname"
    Write-Host "Added KC_HOSTNAME to docker-compose.yml" -ForegroundColor Green
}

Set-Content -Path $composeFile -Value $composeContent -NoNewline

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Configuration updated!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart Keycloak:" -ForegroundColor White
Write-Host "   cd infra" -ForegroundColor Gray
Write-Host "   docker-compose restart keycloak" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Wait 30-60 seconds for Keycloak to start" -ForegroundColor White
Write-Host ""
Write-Host "3. Clear browser cache and try again" -ForegroundColor White
Write-Host ""

