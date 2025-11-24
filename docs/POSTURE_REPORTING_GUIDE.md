# Posture Reporting Guide

This document explains when posture checks are sent and where they are displayed in the system.

**Note**: For per-request posture checks (when accessing resources), see [POSTURE_PER_REQUEST_GUIDE.md](./POSTURE_PER_REQUEST_GUIDE.md).

## When is the First Posture Check Sent?

### Prerequisites

1. **Device Must Be Enrolled**: Device must complete enrollment successfully
2. **Device Must Be Approved**: Admin must approve the device (status changes from `pending` to `active`)
3. **Posture Scheduler Must Be Running**: The DPA posture scheduler needs to be started

### Timing

- **Default Interval**: 300 seconds (5 minutes)
- **First Check**: The scheduler sends the first posture report immediately when started, then every 5 minutes thereafter
- **Configurable**: You can change the interval via:
  - Environment variable: `DPA_REPORTING_INTERVAL` (in seconds)
  - Config file: `C:\ProgramData\ZTNA\config.json` → `reporting_interval`

### Starting the Posture Scheduler

The posture scheduler is **NOT automatically started** after enrollment. You need to start it manually:

**Option 1: Using Python Script**

```python
# start_posture_scheduler.py
from dpa.core.posture_scheduler import PostureScheduler
from dpa.utils.logger import setup_logger
import time

setup_logger()

# Get interval from config (default: 300 seconds = 5 minutes)
from dpa.config.settings import config_manager
interval = config_manager.get().reporting_interval

# Start scheduler
scheduler = PostureScheduler(interval_seconds=interval)
scheduler.start()

print(f"Posture scheduler started with {interval} second interval")
print("Press Ctrl+C to stop...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.stop()
    print("\nPosture scheduler stopped")
```

Run:
```powershell
python start_posture_scheduler.py
```

**Option 2: Manual Submission (for testing)**

```python
# manual_posture_submit.py
from dpa.core.posture_submission import PostureSubmitter
from dpa.modules.posture import collect_posture_report
from dpa.config.settings import config_manager

# Collect posture data
posture_report = collect_posture_report()

# Submit to backend
submitter = PostureSubmitter(backend_url=config_manager.get().backend_url)
success = submitter.submit_posture(posture_report)

if success:
    print("✓ Posture report submitted successfully")
else:
    print("✗ Posture submission failed")
```

Run:
```powershell
python manual_posture_submit.py
```

## File Locations

### Posture Scheduler Script
- **Location**: `dpa/start_posture_scheduler.py`
- **Purpose**: Starts automatic posture reporting at configured intervals
- **Usage**: `python -m dpa.start_posture_scheduler`

## Where is Posture Data Displayed?

### 1. Dashboard (`/dashboard`)

**Location**: Main admin dashboard

**Displays**:
- **Compliant Devices Count**: Number of devices with `is_compliant = true`
- **Non-Compliant Devices Count**: Number of devices with `is_compliant = false`
- **Total Devices**: All enrolled devices

**Visual**: Stat cards with icons and counts

### 2. Devices List Page (`/devices`)

**Location**: Devices management page

**Displays**:
- **Compliance Badge**: Green "Compliant" or Red "Non-Compliant" badge for each device
- **Last Seen**: Timestamp of last posture check (if available)

**Visual**: Badge in the "Compliance" column of the devices table

### 3. Device Detail Page (`/devices/{id}`)

**Location**: Individual device details page

**Displays**:
- **Compliance Status**: Badge showing "Compliant" or "Non-Compliant"
- **Last Posture Check**: Timestamp of the most recent posture submission
  - Format: Localized date/time (e.g., "11/24/2025, 7:15:30 AM")
  - Shows "Never" if no posture check has been submitted yet

**Visual**: 
- Compliance badge in the header
- "Last Posture Check" field in the "System Information" section

### 4. Posture History (Backend Only - No Frontend UI Yet)

**Backend Endpoint**: `GET /api/posture/device/{device_id}/history`

**Note**: This endpoint exists but there's currently no frontend page to display posture history. The data is stored in the database and can be accessed via API.

## Posture Data Flow

```
1. Device Enrolled (status: pending)
   ↓
2. Admin Approves Device (status: active)
   ↓
3. Posture Scheduler Started (manually)
   ↓
4. First Posture Report Sent (immediately)
   ↓
5. Backend Evaluates Compliance
   ↓
6. Device Compliance Status Updated
   ↓
7. UI Displays Updated Status
   ↓
8. Subsequent Reports Every 5 Minutes (default)
```

## Important Notes

### ⚠️ Device Must Be Approved First

Posture reports will **fail** if the device is still in `pending` status. The backend returns:
- `403 Forbidden`: "Device is not approved or inactive"

### ⚠️ Scheduler Must Be Running

The posture scheduler does **NOT** start automatically. You must:
1. Start it manually after enrollment
2. Keep it running (it runs in a background thread)
3. Restart it if the DPA process is restarted

### ⚠️ First Report Timing

- **Immediate**: First report is sent as soon as scheduler starts
- **Subsequent**: Every 5 minutes (or configured interval)
- **No Delay**: There's no initial delay - first report happens immediately

## Configuration

### Change Reporting Interval

**Via Environment Variable:**
```powershell
$env:DPA_REPORTING_INTERVAL = "60"  # 60 seconds = 1 minute
```

**Via Config File:**
Edit `C:\ProgramData\ZTNA\config.json`:
```json
{
  "reporting_interval": 60,
  "backend_url": "https://your-ngrok-url.ngrok-free.app"
}
```

## Troubleshooting

### Posture Reports Not Appearing

1. **Check Device Status**: Device must be `active` (not `pending`)
2. **Check Scheduler**: Is the posture scheduler running?
3. **Check Backend URL**: Is `DPA_BACKEND_URL` set correctly?
4. **Check Logs**: Look for errors in DPA logs
5. **Check Backend**: Verify backend is receiving requests (check backend logs)

### "Last Posture Check" Shows "Never"

- Device hasn't submitted any posture reports yet
- Scheduler may not be running
- Device may not be approved yet
- Backend connection may be failing

### Compliance Status Not Updating

- Wait for next scheduled report (5 minutes default)
- Manually trigger a posture submission
- Check backend logs for compliance evaluation errors

