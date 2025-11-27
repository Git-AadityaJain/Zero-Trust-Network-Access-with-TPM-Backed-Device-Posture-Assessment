# app/services/challenge_service.py

"""
Challenge service for TPM-based device attestation
Generates and validates challenges to ensure requests come from genuine enrolled devices
"""

import secrets
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# In-memory challenge store (in production, use Redis or similar)
_challenge_store: Dict[str, Dict] = {}


class ChallengeService:
    """Service for managing TPM attestation challenges"""
    
    # Challenge expiration time (5 minutes)
    CHALLENGE_EXPIRY_SECONDS = 300
    
    @staticmethod
    def generate_challenge(device_unique_id: str) -> str:
        """
        Generate a challenge (nonce) for device attestation
        
        Args:
            device_unique_id: Unique identifier for the device
            
        Returns:
            Base64-encoded challenge string
        """
        # Generate a random nonce
        nonce = secrets.token_bytes(32)
        challenge = secrets.token_urlsafe(32)
        
        # Store challenge with metadata
        _challenge_store[challenge] = {
            "device_unique_id": device_unique_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=ChallengeService.CHALLENGE_EXPIRY_SECONDS),
            "used": False
        }
        
        logger.info(f"Generated challenge for device {device_unique_id}, expires in {ChallengeService.CHALLENGE_EXPIRY_SECONDS}s")
        
        return challenge
    
    @staticmethod
    def verify_challenge(challenge: str, device_unique_id: str) -> bool:
        """
        Verify that a challenge is valid and matches the device
        
        Args:
            challenge: The challenge string
            device_unique_id: Expected device unique ID
            
        Returns:
            True if challenge is valid and matches device, False otherwise
        """
        if challenge not in _challenge_store:
            logger.warning(f"Challenge not found: {challenge[:20]}...")
            return False
        
        challenge_data = _challenge_store[challenge]
        
        # Check expiration
        if datetime.utcnow() > challenge_data["expires_at"]:
            logger.warning(f"Challenge expired: {challenge[:20]}...")
            del _challenge_store[challenge]
            return False
        
        # Check if already used
        if challenge_data["used"]:
            logger.warning(f"Challenge already used: {challenge[:20]}...")
            return False
        
        # Check device match
        if challenge_data["device_unique_id"] != device_unique_id:
            logger.warning(
                f"Challenge device mismatch: expected {device_unique_id}, "
                f"got {challenge_data['device_unique_id']}"
            )
            return False
        
        # Mark as used
        challenge_data["used"] = True
        
        logger.info(f"Challenge verified successfully for device {device_unique_id}")
        return True
    
    @staticmethod
    def consume_challenge(challenge: str) -> bool:
        """
        Mark a challenge as consumed (after successful token issuance)
        
        Args:
            challenge: The challenge string
            
        Returns:
            True if challenge was found and consumed, False otherwise
        """
        if challenge in _challenge_store:
            _challenge_store[challenge]["used"] = True
            # Optionally remove after a delay to prevent replay attacks
            return True
        return False
    
    @staticmethod
    def cleanup_expired_challenges():
        """Remove expired challenges from store (call periodically)"""
        now = datetime.utcnow()
        expired = [
            challenge for challenge, data in _challenge_store.items()
            if now > data["expires_at"]
        ]
        for challenge in expired:
            del _challenge_store[challenge]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired challenges")


