# Get Local IP Address for Port Forwarding Configuration

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ZTNA Local IP Address" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get network adapters with IPv4 addresses
$adapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*" -and
    $_.PrefixOrigin -ne "WellKnown"
} | Select-Object IPAddress, InterfaceAlias, PrefixLength

if ($adapters) {
    Write-Host "Local IP Addresses (use for router port forwarding):" -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($adapter in $adapters) {
        Write-Host "  IP Address: $($adapter.IPAddress)" -ForegroundColor Green
        Write-Host "  Interface:  $($adapter.InterfaceAlias)" -ForegroundColor Gray
        Write-Host "  Subnet:     $($adapter.IPAddress)/$($adapter.PrefixLength)" -ForegroundColor Gray
        Write-Host ""
    }
    
    $primaryIP = ($adapters | Select-Object -First 1).IPAddress
    Write-Host "Primary IP (recommended for port forwarding): $primaryIP" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Router Port Forwarding Configuration:" -ForegroundColor Yellow
    Write-Host "  External Port 80   → Internal: $primaryIP:80" -ForegroundColor White
    Write-Host "  External Port 8080 → Internal: $primaryIP:8080" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "No network adapters found with IPv4 addresses." -ForegroundColor Red
    Write-Host ""
}

# Get public IP
Write-Host "Public IP Address:" -ForegroundColor Yellow
try {
    $publicIP = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing -TimeoutSec 5).Content.Trim()
    Write-Host "  $publicIP" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "  Could not determine public IP" -ForegroundColor Yellow
    Write-Host ""
}

