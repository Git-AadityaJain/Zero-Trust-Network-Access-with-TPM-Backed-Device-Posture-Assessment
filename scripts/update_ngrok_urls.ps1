# Update ngrok URLs in Configuration Files
# Usage: .\scripts\update_ngrok_urls.ps1 -NgrokUrl "https://abc123.ngrok.io"
# For single tunnel setup where Keycloak is routed through /auth
#
# This script will:
# 1. Update infra/.env with external URLs
# 2. Update backend/.env CORS_ORIGIN
# 3. Update Keycloak hostname in docker-compose.yml (fixes HTTPS issues)
# 4. Update realm-export.json with new redirect URIs
#
# After running this script, restart services to apply changes.

param(
    [Parameter(Mandatory=$true)]
    [string]$NgrokUrl
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Update ngrok URLs in Configuration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Remove trailing slashes
$NgrokUrl = $NgrokUrl.TrimEnd('/')

# For single tunnel, frontend and keycloak use the same URL
# Keycloak is accessed via /auth path
$FrontendUrl = $NgrokUrl
$KeycloakUrl = "$NgrokUrl/auth"

Write-Host "ngrok URL: $NgrokUrl" -ForegroundColor Yellow
Write-Host "Frontend URL: $FrontendUrl" -ForegroundColor Gray
Write-Host "Keycloak URL: $KeycloakUrl (via /auth)" -ForegroundColor Gray
Write-Host ""

# Validate URL
if (-not ($NgrokUrl -match '^https?://')) {
    Write-Host "ERROR: ngrok URL must start with http:// or https://" -ForegroundColor Red
    exit 1
}

$ErrorCount = 0

# File 1: Update infra/.env
Write-Host "Updating infra/.env..." -ForegroundColor Cyan
$envFile = "infra\.env"

if (Test-Path $envFile) {
    try {
        $lines = Get-Content $envFile
        $updated = $false
        $newLines = @()
        
        foreach ($line in $lines) {
            # Skip comments and empty lines, but preserve them
            if ($line -match '^\s*#' -or $line -match '^\s*$') {
                $newLines += $line
                continue
            }
            
            # Update EXTERNAL_FRONTEND_URL (uncomment if commented)
            if ($line -match '^\s*#?\s*EXTERNAL_FRONTEND_URL\s*=') {
                $newLines += "EXTERNAL_FRONTEND_URL=$FrontendUrl"
                $updated = $true
            }
            # Update EXTERNAL_KEYCLOAK_URL (uncomment if commented)
            elseif ($line -match '^\s*#?\s*EXTERNAL_KEYCLOAK_URL\s*=') {
                $newLines += "EXTERNAL_KEYCLOAK_URL=$KeycloakUrl"
                $updated = $true
            }
            # Update EXTERNAL_CORS_ORIGINS (uncomment if commented, keep localhost)
            elseif ($line -match '^\s*#?\s*EXTERNAL_CORS_ORIGINS\s*=') {
                $newLines += "EXTERNAL_CORS_ORIGINS=$FrontendUrl,http://localhost:3000,http://localhost"
                $updated = $true
            }
            else {
                $newLines += $line
            }
        }
        
        # If no existing entries found, append them
        if (-not $updated) {
            $newLines += ""
            $newLines += "# External Access Configuration (Updated by update_ngrok_urls.ps1)"
            $newLines += "EXTERNAL_FRONTEND_URL=$FrontendUrl"
            $newLines += "EXTERNAL_KEYCLOAK_URL=$KeycloakUrl"
            $newLines += "EXTERNAL_CORS_ORIGINS=$FrontendUrl,http://localhost:3000,http://localhost"
        }
        
        Set-Content -Path $envFile -Value $newLines
        Write-Host "  [OK] Updated infra/.env" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to update infra/.env: $_" -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "  [WARNING] infra/.env not found, creating it..." -ForegroundColor Yellow
    try {
        $envContent = @"
# External Access Configuration
# Updated by update_ngrok_urls.ps1
EXTERNAL_FRONTEND_URL=$FrontendUrl
EXTERNAL_KEYCLOAK_URL=$KeycloakUrl
EXTERNAL_CORS_ORIGINS=$FrontendUrl,http://localhost:3000,http://localhost
"@
        Set-Content -Path $envFile -Value $envContent
        Write-Host "  [OK] Created infra/.env" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to create infra/.env: $_" -ForegroundColor Red
        $ErrorCount++
    }
}

# File 2: Update backend/.env CORS_ORIGIN
Write-Host "Updating backend/.env CORS_ORIGIN..." -ForegroundColor Cyan
$backendEnvFile = "backend\.env"

if (Test-Path $backendEnvFile) {
    try {
        $lines = Get-Content $backendEnvFile
        $updated = $false
        $newLines = @()
        
        foreach ($line in $lines) {
            # Skip comments and empty lines, but preserve them
            if ($line -match '^\s*#' -or $line -match '^\s*$') {
                $newLines += $line
                continue
            }
            
            # Update CORS_ORIGIN (add ngrok URL, keep localhost)
            if ($line -match '^\s*CORS_ORIGIN\s*=') {
                $existingOrigins = ($line -split '=', 2)[1].Trim()
                if ($existingOrigins -notmatch [regex]::Escape($FrontendUrl)) {
                    if ($existingOrigins) {
                        $newLines += "CORS_ORIGIN=$FrontendUrl,$existingOrigins"
                    } else {
                        $newLines += "CORS_ORIGIN=$FrontendUrl,http://localhost:3000,http://localhost"
                    }
                    $updated = $true
                } else {
                    $newLines += $line
                }
            }
            else {
                $newLines += $line
            }
        }
        
        Set-Content -Path $backendEnvFile -Value $newLines
        if ($updated) {
            Write-Host "  [OK] Updated backend/.env CORS_ORIGIN" -ForegroundColor Green
        } else {
            Write-Host "  [INFO] CORS_ORIGIN already includes ngrok URL" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARNING] Failed to update backend/.env: $_" -ForegroundColor Yellow
        Write-Host "  [INFO] You may need to manually update CORS_ORIGIN in backend/.env" -ForegroundColor Gray
    }
} else {
    Write-Host "  [WARNING] backend/.env not found" -ForegroundColor Yellow
}

# File 3: Update Keycloak hostname in docker-compose.yml
Write-Host "Updating Keycloak hostname in docker-compose.yml..." -ForegroundColor Cyan
$composeFile = "infra\docker-compose.yml"

if (Test-Path $composeFile) {
    try {
        # Extract hostname from ngrok URL (remove https:// and any path)
        $hostname = $NgrokUrl -replace '^https?://', '' -replace '/.*$', ''
        
        Write-Host "  Extracted hostname: $hostname" -ForegroundColor Gray
        
        $composeContent = Get-Content $composeFile -Raw
        
        # Check if KC_HOSTNAME is already set
        if ($composeContent -match 'KC_HOSTNAME=\$\{KC_HOSTNAME:-([^}]+)\}') {
            # Update existing KC_HOSTNAME
            $composeContent = $composeContent -replace 'KC_HOSTNAME=\$\{KC_HOSTNAME:-[^}]+\}', "KC_HOSTNAME=`${KC_HOSTNAME:-$hostname}"
            Write-Host "  [OK] Updated KC_HOSTNAME in docker-compose.yml" -ForegroundColor Green
        } elseif ($composeContent -match 'KC_HOSTNAME=') {
            # Update any other format
            $composeContent = $composeContent -replace 'KC_HOSTNAME=[^\n]+', "KC_HOSTNAME=`${KC_HOSTNAME:-$hostname}"
            Write-Host "  [OK] Updated KC_HOSTNAME in docker-compose.yml" -ForegroundColor Green
        } else {
            # Add KC_HOSTNAME after KC_PROXY_HEADERS
            $composeContent = $composeContent -replace '(KC_PROXY_HEADERS=xforwarded)', "`$1`n      - KC_HOSTNAME=`${KC_HOSTNAME:-$hostname}"
            Write-Host "  [OK] Added KC_HOSTNAME to docker-compose.yml" -ForegroundColor Green
        }
        
        Set-Content -Path $composeFile -Value $composeContent -NoNewline
    } catch {
        Write-Host "  [ERROR] Failed to update docker-compose.yml: $_" -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "  [WARNING] infra/docker-compose.yml not found" -ForegroundColor Yellow
}

# File 4: Update realm-export.json
Write-Host "Updating realm-export.json..." -ForegroundColor Cyan
$realmFile = "realm-export.json"

if (Test-Path $realmFile) {
    try {
        # Read JSON as raw text first to preserve formatting
        $realmJson = Get-Content $realmFile -Raw
        
        # Parse JSON
        $realmContent = $realmJson | ConvertFrom-Json
        
        # Find admin-frontend client
        $adminFrontend = $realmContent.clients | Where-Object { $_.clientId -eq "admin-frontend" }
        
        if ($adminFrontend) {
            Write-Host "  Found admin-frontend client" -ForegroundColor Gray
            
            $changed = $false
            
            # Update redirectUris
            if (-not $adminFrontend.redirectUris) {
                $adminFrontend.redirectUris = @()
            }
            $callbackUrl = "$FrontendUrl/callback"
            if ($adminFrontend.redirectUris -notcontains $callbackUrl) {
                $adminFrontend.redirectUris += $callbackUrl
                Write-Host "  [OK] Added redirect URI: $callbackUrl" -ForegroundColor Green
                $changed = $true
            } else {
                Write-Host "  [INFO] Redirect URI already exists: $callbackUrl" -ForegroundColor Yellow
            }
            
            # Update webOrigins
            if (-not $adminFrontend.webOrigins) {
                $adminFrontend.webOrigins = @()
            }
            if ($adminFrontend.webOrigins -notcontains $FrontendUrl) {
                $adminFrontend.webOrigins += $FrontendUrl
                Write-Host "  [OK] Added web origin: $FrontendUrl" -ForegroundColor Green
                $changed = $true
            } else {
                Write-Host "  [INFO] Web origin already exists: $FrontendUrl" -ForegroundColor Yellow
            }
            
            # Update post.logout.redirect.uris
            if (-not $adminFrontend.attributes) {
                $adminFrontend.attributes = @{}
            }
            $logoutUris = $adminFrontend.attributes.'post.logout.redirect.uris'
            if ($logoutUris) {
                $uriList = $logoutUris -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
            } else {
                $uriList = @()
            }
            $logoutUrl = "$FrontendUrl/login"
            if ($uriList -notcontains $logoutUrl) {
                $uriList += $logoutUrl
                $adminFrontend.attributes.'post.logout.redirect.uris' = ($uriList | Where-Object { $_ }) -join ','
                Write-Host "  [OK] Added post-logout redirect URI: $logoutUrl" -ForegroundColor Green
                $changed = $true
            } else {
                Write-Host "  [INFO] Post-logout redirect URI already exists: $logoutUrl" -ForegroundColor Yellow
            }
            
            # Save back to file only if changed
            if ($changed) {
                # Convert to JSON (Keycloak will accept this format)
                $jsonContent = $realmContent | ConvertTo-Json -Depth 100 -Compress:$false
                Set-Content -Path $realmFile -Value $jsonContent -Encoding UTF8
                Write-Host "  [OK] Updated realm-export.json" -ForegroundColor Green
                Write-Host "  [INFO] Note: JSON formatting may differ from original, but is valid" -ForegroundColor Gray
            } else {
                Write-Host "  [INFO] No changes needed in realm-export.json" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [WARNING] admin-frontend client not found in realm-export.json" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERROR] Failed to update realm-export.json: $_" -ForegroundColor Red
        Write-Host "  [INFO] Error details: $($_.Exception.Message)" -ForegroundColor Gray
        $ErrorCount++
    }
} else {
    Write-Host "  [WARNING] realm-export.json not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "[SUCCESS] Configuration files updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Rebuild and restart Docker services:" -ForegroundColor White
    Write-Host "   cd infra" -ForegroundColor Gray
    Write-Host "   docker-compose build frontend" -ForegroundColor Gray
    Write-Host "   docker-compose restart keycloak nginx" -ForegroundColor Gray
    Write-Host "   docker-compose up -d" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Note: Frontend must be rebuilt because environment variables are" -ForegroundColor Gray
    Write-Host "         bundled at build time. Keycloak and nginx are restarted to" -ForegroundColor Gray
    Write-Host "         apply the new hostname configuration." -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Wait 30-60 seconds for Keycloak to fully start" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Clear browser cache (Ctrl+Shift+Delete) and access:" -ForegroundColor White
    Write-Host "   - Frontend: $FrontendUrl" -ForegroundColor Gray
    Write-Host "   - Keycloak Admin: $FrontendUrl/auth/admin" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Note: Keycloak hostname is automatically configured. If you still see" -ForegroundColor Gray
    Write-Host "         HTTP/HTTPS issues, you may need to manually set the Frontend URL" -ForegroundColor Gray
    Write-Host "         in Keycloak Admin Console → Realm Settings → General" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[ERROR] Some errors occurred. Please check the output above." -ForegroundColor Red
    exit 1
}

