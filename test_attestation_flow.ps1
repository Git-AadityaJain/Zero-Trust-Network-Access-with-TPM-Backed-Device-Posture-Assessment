# Test TPM Device Attestation Flow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TPM Device Attestation Flow Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check DPA API Health
Write-Host "Step 1: Checking DPA API Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8081/health" -Method GET
    Write-Host "DPA API is running" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Gray
    Write-Host "  Enrolled: $($health.enrolled)" -ForegroundColor Gray
    Write-Host "  TPM Available: $($health.tpm_available)" -ForegroundColor Gray
    if (-not $health.enrolled) {
        Write-Host "WARNING: Device is not enrolled!" -ForegroundColor Yellow
    }
    if (-not $health.tpm_available) {
        Write-Host "WARNING: TPM is not available!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "DPA API is not running!" -ForegroundColor Red
    Write-Host "  Start it with: python dpa/start_api_server.py" -ForegroundColor Gray
    exit 1
}
Write-Host ""

# Step 2: Test Challenge Signing
Write-Host "Step 2: Testing Challenge Signing..." -ForegroundColor Yellow
$testChallenge = "test-challenge-$(Get-Date -Format 'yyyyMMddHHmmss')"
try {
    $body = @{challenge=$testChallenge} | ConvertTo-Json
    $signResponse = Invoke-RestMethod -Uri "http://localhost:8081/sign-challenge" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    Write-Host "Challenge signed successfully!" -ForegroundColor Green
    $challengePreview = $testChallenge.Substring(0, [Math]::Min(20, $testChallenge.Length))
    Write-Host "  Challenge: $challengePreview..." -ForegroundColor Gray
    if ($signResponse.signature) {
        $sigPreview = $signResponse.signature.Substring(0, [Math]::Min(30, $signResponse.signature.Length))
        Write-Host "  Signature: $sigPreview..." -ForegroundColor Gray
    }
} catch {
    Write-Host "Challenge signing failed!" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "  1. TPMSigner.exe not found or not accessible" -ForegroundColor Gray
    Write-Host "  2. TPM key not initialized" -ForegroundColor Gray
    Write-Host "  3. TPM not available on system" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Set TPM path: `$env:TPM_SIGNER_EXE_PATH = 'path\to\TPMSigner.exe'" -ForegroundColor Gray
    exit 1
}
Write-Host ""

# Step 3: Check Backend Health
Write-Host "Step 3: Checking Backend Health..." -ForegroundColor Yellow
try {
    $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
    Write-Host "Backend is running" -ForegroundColor Green
} catch {
    Write-Host "Backend is not running (optional for this test)" -ForegroundColor Yellow
    Write-Host "  Start it with: make up" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DPA API: Running" -ForegroundColor Green
Write-Host "Challenge Signing: Working" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Ensure frontend is running" -ForegroundColor Gray
Write-Host "2. Login to frontend with enrolled device user" -ForegroundColor Gray
Write-Host "3. Navigate to User Dashboard" -ForegroundColor Gray
Write-Host "4. Watch browser console for challenge signing flow" -ForegroundColor Gray
