# Posture Per-Request Guide

This guide explains how to use posture checks per resource access request instead of scheduled periodic checks.

## Overview

By default, the DPA submits posture reports every 5 minutes via the scheduler. However, when resource access is enabled, you can switch to **per-request posture checks** where posture is submitted fresh with each resource access request.

## File Locations

### Posture Scheduler
- **Location**: `dpa/start_posture_scheduler.py`
- **Purpose**: Starts the automatic posture reporting scheduler (5-minute intervals)
- **Usage**: `python -m dpa.start_posture_scheduler`

### Access Request Handler
- **Location**: `dpa/core/access_request.py`
- **Purpose**: Handles resource access requests with fresh posture submission
- **Usage**: Via CLI or programmatically

### Access Request CLI
- **Location**: `dpa/cli/request_access_cli.py`
- **Purpose**: Command-line tool for requesting resource access
- **Usage**: `python -m dpa.cli.request_access_cli --device-id <id> --resource <resource> --auth-token <token>`

## Posture History Display

Posture history is displayed on the **Device Detail Page** (`/devices/{id}`):

1. Navigate to **Devices** → Click on a device
2. Scroll to the **"Recent Posture History"** section
3. View:
   - Compliance status (Compliant/Non-Compliant)
   - Compliance score (0-100%)
   - Timestamp of each check
   - Violations (if any)
   - Signature validity

The history shows the **10 most recent** posture checks, ordered by most recent first.

## Switching to Per-Request Posture Checks

### Step 1: Stop the Scheduled Scheduler

If the scheduler is running, stop it (Ctrl+C).

### Step 2: Use Access Request Handler

When requesting access to a resource, use the `AccessRequestHandler` which automatically:
1. Collects fresh posture data
2. Signs it with TPM
3. Includes it in the access request
4. Backend processes it immediately

### Example: Using the CLI

```powershell
# Request access to a resource
python -m dpa.cli.request_access_cli `
  --device-id 1 `
  --resource "server1" `
  --access-type "read" `
  --auth-token "YOUR_JWT_TOKEN"
```

### Example: Using Programmatically

```python
from dpa.core.access_request import AccessRequestHandler

handler = AccessRequestHandler(backend_url="https://your-ngrok-url.ngrok-free.app")

result = handler.request_access(
    device_id=1,
    resource="server1",
    access_type="read",
    auth_token="YOUR_JWT_TOKEN"
)

if result.get("allowed"):
    print(f"Access granted! Token: {result['token']}")
else:
    print(f"Access denied: {result['reason']}")
```

## How It Works

### Backend Processing

When an access request includes `posture_data` and `posture_signature`:

1. **Signature Verification**: Backend verifies the TPM signature
2. **Compliance Evaluation**: Evaluates posture against compliance rules
3. **Device Update**: Updates device's posture data and compliance status
4. **History Storage**: Stores posture check in history
5. **Policy Evaluation**: Uses fresh posture data for policy evaluation
6. **Access Decision**: Grants or denies access based on policies

### Benefits

- **Real-time Compliance**: Always uses the most current posture state
- **No Stale Data**: Eliminates the 5-minute delay between checks
- **On-Demand**: Only checks posture when access is actually needed
- **Reduced Load**: No continuous background reporting

## Backend API

The access request endpoint accepts:

```json
{
  "device_id": 1,
  "resource": "server1",
  "access_type": "read",
  "posture_data": {
    "antivirus_enabled": true,
    "firewall_enabled": true,
    "disk_encrypted": true,
    ...
  },
  "posture_signature": "base64_signature_string"
}
```

Response:

```json
{
  "allowed": true,
  "device_id": 1,
  "resource": "server1",
  "reason": "Access granted by policy evaluation",
  "token": "jwt_access_token"
}
```

## Migration from Scheduled to Per-Request

1. **Stop scheduler**: Stop `start_posture_scheduler.py` if running
2. **Update application code**: Replace scheduled checks with access request calls
3. **Test**: Verify posture is submitted with each access request
4. **Monitor**: Check device detail page for posture history updates

## Notes

- **Authentication Required**: Access requests require a valid JWT token
- **Device ID**: You need the backend device ID (integer), not the device_unique_id
- **TPM Required**: Posture signing requires TPM to be enabled and initialized
- **Fallback**: If posture data is not provided, backend uses stored posture data

