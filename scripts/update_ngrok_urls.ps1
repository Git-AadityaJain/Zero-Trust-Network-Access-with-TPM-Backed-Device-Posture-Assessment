# Update ngrok URLs in Configuration Files
# Usage: .\scripts\update_ngrok_urls.ps1 -NgrokUrl "https://abc123.ngrok.io"
# For single tunnel setup where Keycloak is routed through /auth

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
        $content = Get-Content $envFile -Raw
        
        # Update EXTERNAL_FRONTEND_URL
        $content = $content -replace 'EXTERNAL_FRONTEND_URL=.*', "EXTERNAL_FRONTEND_URL=$FrontendUrl"
        
        # Update EXTERNAL_KEYCLOAK_URL
        $content = $content -replace 'EXTERNAL_KEYCLOAK_URL=.*', "EXTERNAL_KEYCLOAK_URL=$KeycloakUrl"
        
        # Update EXTERNAL_CORS_ORIGINS (keep localhost)
        $content = $content -replace 'EXTERNAL_CORS_ORIGINS=.*', "EXTERNAL_CORS_ORIGINS=$FrontendUrl,http://localhost:3000"
        
        Set-Content -Path $envFile -Value $content -NoNewline
        Write-Host "  [OK] Updated infra/.env" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to update infra/.env: $_" -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "  [WARNING] infra/.env not found, creating it..." -ForegroundColor Yellow
    try {
        $envContent = "# External Access Configuration`n"
        $envContent += "EXTERNAL_FRONTEND_URL=$FrontendUrl`n"
        $envContent += "EXTERNAL_KEYCLOAK_URL=$KeycloakUrl`n"
        $envContent += "EXTERNAL_CORS_ORIGINS=$FrontendUrl,http://localhost:3000`n"
        Set-Content -Path $envFile -Value $envContent
        Write-Host "  [OK] Created infra/.env" -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Failed to create infra/.env: $_" -ForegroundColor Red
        $ErrorCount++
    }
}

# File 2: Update realm-export.json
Write-Host "Updating realm-export.json..." -ForegroundColor Cyan
$realmFile = "realm-export.json"

if (Test-Path $realmFile) {
    try {
        $realmContent = Get-Content $realmFile -Raw | ConvertFrom-Json
        
        # Find admin-frontend client
        $adminFrontend = $realmContent.clients | Where-Object { $_.clientId -eq "admin-frontend" }
        
        if ($adminFrontend) {
            Write-Host "  Found admin-frontend client" -ForegroundColor Gray
            
            # Update redirectUris
            if (-not $adminFrontend.redirectUris) {
                $adminFrontend.redirectUris = @()
            }
            $callbackUrl = "$FrontendUrl/callback"
            if ($adminFrontend.redirectUris -notcontains $callbackUrl) {
                $adminFrontend.redirectUris += $callbackUrl
                Write-Host "  [OK] Added redirect URI: $callbackUrl" -ForegroundColor Green
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
            } else {
                Write-Host "  [INFO] Web origin already exists: $FrontendUrl" -ForegroundColor Yellow
            }
            
            # Update post.logout.redirect.uris
            if (-not $adminFrontend.attributes) {
                $adminFrontend.attributes = @{}
            }
            $logoutUris = $adminFrontend.attributes.'post.logout.redirect.uris'
            if ($logoutUris) {
                $uriList = $logoutUris -split ',' | ForEach-Object { $_.Trim() }
            } else {
                $uriList = @()
            }
            $logoutUrl = "$FrontendUrl/login"
            if ($uriList -notcontains $logoutUrl) {
                $uriList += $logoutUrl
                $adminFrontend.attributes.'post.logout.redirect.uris' = $uriList -join ','
                Write-Host "  [OK] Added post-logout redirect URI: $logoutUrl" -ForegroundColor Green
            } else {
                Write-Host "  [INFO] Post-logout redirect URI already exists: $logoutUrl" -ForegroundColor Yellow
            }
            
            # Save back to file
            $realmContent | ConvertTo-Json -Depth 100 | Set-Content -Path $realmFile
            Write-Host "  [OK] Updated realm-export.json" -ForegroundColor Green
        } else {
            Write-Host "  [WARNING] admin-frontend client not found in realm-export.json" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERROR] Failed to update realm-export.json: $_" -ForegroundColor Red
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
    Write-Host "1. Update Keycloak Admin Console manually:" -ForegroundColor White
    Write-Host "   - Access: $FrontendUrl/auth/admin" -ForegroundColor Gray
    Write-Host "   - Login: admin / adminsecure123" -ForegroundColor Gray
    Write-Host "   - Go to: Clients → admin-frontend" -ForegroundColor Gray
    Write-Host "   - Add to Valid Redirect URIs: $FrontendUrl/callback" -ForegroundColor Gray
    Write-Host "   - Add to Web Origins: $FrontendUrl" -ForegroundColor Gray
    Write-Host "   - Add to Post Logout Redirect URIs: $FrontendUrl/login" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Restart Docker services:" -ForegroundColor White
    Write-Host "   cd infra" -ForegroundColor Gray
    Write-Host "   docker-compose down" -ForegroundColor Gray
    Write-Host "   docker-compose up -d" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[ERROR] Some errors occurred. Please check the output above." -ForegroundColor Red
    exit 1
}

