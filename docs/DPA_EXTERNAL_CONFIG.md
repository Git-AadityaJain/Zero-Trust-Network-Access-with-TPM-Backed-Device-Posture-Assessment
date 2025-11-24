# DPA External Access Configuration

This guide explains how to configure the DPA (Device Posture Agent) to communicate with the backend from external networks.

## Configuration Methods

The DPA can be configured to use an external backend URL in several ways:

### Method 1: Environment Variable (Recommended)

Set the `ZTNA_BACKEND_URL` environment variable:

**Windows (PowerShell):**
```powershell
$env:ZTNA_BACKEND_URL = "https://your-ngrok-url.ngrok.io/api"
```

**Windows (CMD):**
```cmd
set ZTNA_BACKEND_URL=https://your-ngrok-url.ngrok.io/api
```

**Linux/Mac:**
```bash
export ZTNA_BACKEND_URL=https://your-ngrok-url.ngrok.io/api
```

### Method 2: Configuration File

Create or update `dpa/config/config.ini`:

```ini
[backend]
url = https://your-ngrok-url.ngrok.io/api
```

### Method 3: Command Line Argument

When running DPA commands, specify the backend URL:

```bash
python -m dpa.cli.enroll_cli --backend-url https://your-ngrok-url.ngrok.io/api
```

## Testing External DPA Connection

### 1. Test Backend Connectivity

```bash
# Test if backend is reachable
curl https://your-ngrok-url.ngrok.io/api/health

# Should return: {"status":"healthy","service":"ZTNA Backend API","version":"0.1.0"}
```

### 2. Test Device Enrollment

```bash
# Enroll device with external backend
python -m dpa.cli.enroll_cli --backend-url https://your-ngrok-url.ngrok.io/api --code YOUR_ENROLLMENT_CODE
```

### 3. Test Posture Submission

The DPA automatically uses the configured backend URL for posture submissions. Verify in logs:

```bash
# Check DPA logs for backend URL
# Should show: "Submitting posture to https://your-ngrok-url.ngrok.io/api/posture/submit"
```

## DPA Configuration Priority

The DPA checks for backend URL in this order:

1. Command line argument (`--backend-url`)
2. Environment variable (`ZTNA_BACKEND_URL`)
3. Configuration file (`dpa/config/config.ini`)
4. Default: `http://localhost/api` (for local development)

## Code Reference

The DPA configuration is managed in:
- `dpa/config/settings.py` - Configuration management
- `dpa/core/enrollment.py` - Enrollment uses `config.backend_url`
- `dpa/core/posture_submission.py` - Posture submission uses `config.backend_url`

## Troubleshooting

### Issue: DPA can't connect to backend
**Check:**
- Backend URL is correct and accessible
- Firewall allows outbound HTTPS connections
- ngrok tunnel is active (if using ngrok)
- SSL certificate is valid

### Issue: Enrollment fails
**Check:**
- Backend URL includes `/api` path
- Enrollment code is valid
- Device fingerprint is unique
- Backend logs for errors

### Issue: Posture submission fails
**Check:**
- Device is enrolled and approved
- Device signature is valid
- Backend endpoint is accessible
- Network connectivity from DPA location

## Security Considerations

- Use HTTPS for all external connections
- Verify SSL certificates
- Consider IP whitelisting for production
- Monitor for unauthorized access attempts
- Use authentication tokens if implemented

