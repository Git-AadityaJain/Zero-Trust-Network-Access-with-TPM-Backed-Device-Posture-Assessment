"""Update all recent posture records with new compliance evaluation"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.db import get_db
from app.services.posture_service import PostureService
from sqlalchemy import select
from app.models.posture_history import PostureHistory

async def main():
    async for db in get_db():
        # Get all posture records for device ID 4, ordered by most recent
        query = (
            select(PostureHistory)
            .where(PostureHistory.device_id == 4)
            .order_by(PostureHistory.checked_at.desc())
            .limit(10)
        )
        result = await db.execute(query)
        records = list(result.scalars().all())
        
        print(f"Found {len(records)} posture records to update")
        print("=" * 60)
        
        updated_count = 0
        for record in records:
            # Re-evaluate with new logic
            is_compliant, score, violations = PostureService.evaluate_compliance(record.posture_data)
            
            # Only update if different
            if (record.is_compliant != is_compliant or 
                record.compliance_score != score or 
                record.violations != violations):
                
                print(f"\nRecord ID {record.id} (checked at {record.checked_at}):")
                print(f"  Old: Compliant={record.is_compliant}, Score={record.compliance_score}%, Violations={len(record.violations)}")
                print(f"  New: Compliant={is_compliant}, Score={score}%, Violations={len(violations)}")
                
                record.is_compliant = is_compliant
                record.compliance_score = score
                record.violations = violations
                updated_count += 1
        
        if updated_count > 0:
            await db.commit()
            print(f"\n✓ Updated {updated_count} records")
        else:
            print("\n✓ All records are already up to date")
        
        break

if __name__ == "__main__":
    asyncio.run(main())

