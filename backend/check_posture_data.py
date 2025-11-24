"""Quick script to check stored posture data"""
import asyncio
import json
import sys
sys.path.insert(0, '/app')

from app.db import get_db
from app.services.posture_service import PostureService

async def main():
    async for db in get_db():
        # Get latest posture for device ID 4 (adjust if needed)
        latest = await PostureService.get_latest_posture(db, 4)
        if latest:
            print("=" * 60)
            print("Latest Posture Data Structure:")
            print("=" * 60)
            print(json.dumps(latest.posture_data, indent=2))
            print()
            print("=" * 60)
            print("Key Values:")
            print("=" * 60)
            print(f"Antivirus: {latest.posture_data.get('antivirus', 'NOT FOUND')}")
            print(f"Firewall: {latest.posture_data.get('firewall', 'NOT FOUND')}")
            print(f"Disk Encryption: {latest.posture_data.get('disk_encryption', 'NOT FOUND')}")
            print()
            print(f"Compliance Score: {latest.compliance_score}%")
            print(f"Is Compliant: {latest.is_compliant}")
            print(f"Violations: {latest.violations}")
        else:
            print("No posture records found for device ID 4")
        break

if __name__ == "__main__":
    asyncio.run(main())

