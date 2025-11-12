"""
Test DPAPI secret management and HMAC signing
"""
import base64
from dpa.core.secrets import DPAPISecretManager
from dpa.core.signing_hmac import HMACSigningService
from dpa.utils.logger import logger


def test_dpapi_secrets():
    """Test DPAPI secret management"""
    logger.info("=== Testing DPAPI Secret Management ===")
    
    manager = DPAPISecretManager()
    
    # Test 1: Generate secret
    logger.info("\n--- Test 1: Generate Secret ---")
    secret = manager.generate_secret()
    if secret:
        logger.info(f"✓ Secret generated (length: {len(secret)})")
    else:
        logger.error("✗ Failed to generate secret")
        return
    
    # Test 2: Protect and unprotect secret
    logger.info("\n--- Test 2: Protect and Unprotect Secret ---")
    if manager.protect_secret(secret):
        logger.info("✓ Secret protected with DPAPI")
    else:
        logger.error("✗ Failed to protect secret")
        return
    
    unprotected = manager.unprotect_secret()
    if unprotected == secret:
        logger.info("✓ Secret unprotected successfully and matches original")
    else:
        logger.error("✗ Unprotected secret does not match original")
        return
    
    # Test 3: Generate and protect salt
    logger.info("\n--- Test 3: Generate and Protect Salt ---")
    salt = manager.generate_salt()
    if salt:
        logger.info(f"✓ Salt generated (length: {len(salt)})")
    else:
        logger.error("✗ Failed to generate salt")
        return
    
    if manager.protect_salt(salt):
        logger.info("✓ Salt protected with DPAPI")
    else:
        logger.error("✗ Failed to protect salt")
        return
    
    unprotected_salt = manager.unprotect_salt()
    if unprotected_salt == salt:
        logger.info("✓ Salt unprotected successfully and matches original")
    else:
        logger.error("✗ Unprotected salt does not match original")
        return
    
    logger.info("\n=== DPAPI Secret Management Test Complete ===")


def test_hmac_signing():
    """Test HMAC signing service"""
    logger.info("\n=== Testing HMAC Signing Service ===")
    
    service = HMACSigningService()
    
    # Test 1: Sign payload
    logger.info("\n--- Test 1: Sign Payload ---")
    test_payload = b"This is a test payload for signing"
    signature = service.sign_payload(test_payload)
    
    if signature:
        logger.info(f"✓ Payload signed (signature length: {len(signature)})")
        logger.info(f"  Signature: {signature[:50]}...")
    else:
        logger.error("✗ Failed to sign payload")
        return
    
    # Test 2: Verify valid signature
    logger.info("\n--- Test 2: Verify Valid Signature ---")
    is_valid = service.verify_signature(test_payload, signature)
    
    if is_valid:
        logger.info("✓ Signature verification successful")
    else:
        logger.error("✗ Signature verification failed")
        return
    
    # Test 3: Verify with modified payload (should fail)
    logger.info("\n--- Test 3: Verify Modified Payload (Should Fail) ---")
    modified_payload = b"This is a MODIFIED test payload for signing"
    is_valid = service.verify_signature(modified_payload, signature)
    
    if not is_valid:
        logger.info("✓ Correctly rejected modified payload")
    else:
        logger.error("✗ Should have rejected modified payload")
        return
    
    # Test 4: Verify with wrong signature (should fail)
    logger.info("\n--- Test 4: Verify with Wrong Signature (Should Fail) ---")
    wrong_signature = base64.b64encode(b"wrong_signature").decode('utf-8')
    is_valid = service.verify_signature(test_payload, wrong_signature)
    
    if not is_valid:
        logger.info("✓ Correctly rejected wrong signature")
    else:
        logger.error("✗ Should have rejected wrong signature")
        return
    
    # Test 5: Get salt
    logger.info("\n--- Test 5: Get Salt ---")
    salt = service.get_salt()
    if salt:
        logger.info(f"✓ Salt retrieved (length: {len(salt)})")
    else:
        logger.error("✗ Failed to get salt")
        return
    
    logger.info("\n=== HMAC Signing Service Test Complete ===")


if __name__ == "__main__":
    test_dpapi_secrets()
    test_hmac_signing()
