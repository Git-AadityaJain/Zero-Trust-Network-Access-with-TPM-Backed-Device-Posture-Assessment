# External Access Verification Script
# Tests if the ZTNA platform is accessible externally

param(
    [string]$PublicIP = "152.58.31.27"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ZTNA External Access Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing access to: $PublicIP" -ForegroundColor Yellow
Write-Host ""

$tests = @(
    @{
        Name = "Frontend (HTTP)"
        URL = "http://$PublicIP"
        ExpectedStatus = 200
    },
    @{
        Name = "Backend API Health"
        URL = "http://$PublicIP/api/health"
        ExpectedStatus = 200
    },
    @{
        Name = "Keycloak"
        URL = "http://$PublicIP:8080"
        ExpectedStatus = 200
    },
    @{
        Name = "Keycloak Admin Console"
        URL = "http://$PublicIP:8080/admin"
        ExpectedStatus = 200
    }
)

$results = @()

foreach ($test in $tests) {
    Write-Host "Testing: $($test.Name)..." -ForegroundColor Cyan
    Write-Host "  URL: $($test.URL)" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $test.URL -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        $status = $response.StatusCode
        
        if ($status -eq $test.ExpectedStatus) {
            Write-Host "  ✓ SUCCESS (Status: $status)" -ForegroundColor Green
            $results += @{
                Test = $test.Name
                Status = "PASS"
                StatusCode = $status
            }
        } else {
            Write-Host "  ⚠ WARNING (Status: $status, Expected: $($test.ExpectedStatus))" -ForegroundColor Yellow
            $results += @{
                Test = $test.Name
                Status = "WARN"
                StatusCode = $status
            }
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  ✗ FAILED (Status: $statusCode)" -ForegroundColor Red
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            Test = $test.Name
            Status = "FAIL"
            StatusCode = $statusCode
            Error = $_.Exception.Message
        }
    }
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$passed = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$warned = ($results | Where-Object { $_.Status -eq "WARN" }).Count
$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

foreach ($result in $results) {
    $icon = switch ($result.Status) {
        "PASS" { "✓" }
        "WARN" { "⚠" }
        "FAIL" { "✗" }
    }
    $color = switch ($result.Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
    }
    Write-Host "  $icon $($result.Test): $($result.Status)" -ForegroundColor $color
}

Write-Host ""
Write-Host "Total: $passed passed, $warned warnings, $failed failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failed -gt 0) {
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Verify router port forwarding is configured" -ForegroundColor White
    Write-Host "  2. Check Windows Firewall rules (run scripts/configure_windows_firewall.ps1)" -ForegroundColor White
    Write-Host "  3. Ensure Docker services are running: docker ps" -ForegroundColor White
    Write-Host "  4. Check service logs: docker logs ztna-nginx, docker logs ztna-backend, docker logs ztna-keycloak" -ForegroundColor White
    Write-Host ""
    exit 1
} else {
    Write-Host "✓ All tests passed! External access is configured correctly." -ForegroundColor Green
    Write-Host ""
    exit 0
}

