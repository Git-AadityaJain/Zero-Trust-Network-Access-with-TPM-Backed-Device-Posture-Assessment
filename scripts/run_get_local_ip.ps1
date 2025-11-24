# Alternative: Run get_local_ip.ps1 with bypass
# This script bypasses execution policy for just this command

# Option 1: Bypass execution policy for this session only
powershell -ExecutionPolicy Bypass -File ".\scripts\get_local_ip.ps1"

