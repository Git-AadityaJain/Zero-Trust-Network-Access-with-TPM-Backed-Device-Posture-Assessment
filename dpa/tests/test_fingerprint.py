"""
Test fingerprint collection module
"""
from dpa.modules.fingerprint import FingerprintCollector
from dpa.utils.logger import logger


def test_fingerprint():
    """Test fingerprint generation and verification"""
    logger.info("=== Testing Fingerprint Module ===")
    
    collector = FingerprintCollector()
    
    # Test 1: Collect hardware identifiers
    logger.info("\n--- Test 1: Hardware Identifier Collection ---")
    identifiers = collector.collect_hardware_identifiers()
    
    for key, value in identifiers.items():
        status = "✓" if value else "✗"
        logger.info(f"{status} {key}: {value if value else 'Not available'}")
    
    # Test 2: Generate fingerprint
    logger.info("\n--- Test 2: Fingerprint Generation ---")
    result = collector.generate_fingerprint()
    
    logger.info(f"Fingerprint Hash: {result['fingerprint_hash']}")
    logger.info(f"Salt: {result['salt']}")
    
    # Test 3: Verify fingerprint consistency
    logger.info("\n--- Test 3: Fingerprint Consistency ---")
    is_consistent = collector.verify_fingerprint(
        fingerprint_hash=result['fingerprint_hash'],
        salt=result['salt']
    )
    
    if is_consistent:
        logger.info("✓ Fingerprint is consistent")
    else:
        logger.error("✗ Fingerprint changed unexpectedly")
    
    # Test 4: Test with different salt (should fail)
    logger.info("\n--- Test 4: Fingerprint with Different Salt ---")
    is_different_salt = collector.verify_fingerprint(
        fingerprint_hash=result['fingerprint_hash'],
        salt="differentSalt123456"
    )
    
    if not is_different_salt:
        logger.info("✓ Correctly detected fingerprint mismatch with different salt")
    else:
        logger.error("✗ Should have detected fingerprint mismatch")
    
    logger.info("\n=== Fingerprint Test Complete ===")


if __name__ == "__main__":
    test_fingerprint()
