"""Re-evaluate the latest posture record with updated compliance logic"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.db import get_db
from app.services.posture_service import PostureService
from app.services.device_service import DeviceService

async def main():
    async for db in get_db():
        # Get latest posture for device ID 4
        latest = await PostureService.get_latest_posture(db, 4)
        if not latest:
            print("No posture records found")
            return
        
        print("=" * 60)
        print("Re-evaluating Latest Posture Record")
        print("=" * 60)
        print(f"Record ID: {latest.id}")
        print(f"Checked At: {latest.checked_at}")
        print()
        
        # Re-evaluate with new logic
        is_compliant, score, violations = PostureService.evaluate_compliance(latest.posture_data)
        
        print("New Evaluation Results:")
        print(f"  Compliant: {is_compliant}")
        print(f"  Score: {score}%")
        print(f"  Violations: {violations}")
        print()
        
        print("Old Record Values:")
        print(f"  Compliant: {latest.is_compliant}")
        print(f"  Score: {latest.compliance_score}%")
        print(f"  Violations: {latest.violations}")
        print()
        
        # Update the record
        latest.is_compliant = is_compliant
        latest.compliance_score = score
        latest.violations = violations
        
        await db.commit()
        await db.refresh(latest)
        
        print("✓ Record updated with new evaluation")
        print()
        print("Updated Record:")
        print(f"  Compliant: {latest.is_compliant}")
        print(f"  Score: {latest.compliance_score}%")
        print(f"  Violations: {latest.violations}")
        
        break

if __name__ == "__main__":
    asyncio.run(main())

