# app/services/signature_service.py

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64
import json
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SignatureService:
    @staticmethod
    def verify_tpm_signature(
        report: dict,
        signature_base64: str,
        public_key_pem: str
    ) -> Tuple[bool, str]:
        """
        Verify TPM signature on posture report
        Returns: (is_valid, error_message)
        """
        try:
            # Try to load as PEM first
            try:
                public_key = serialization.load_pem_public_key(
                    public_key_pem.encode(),
                    backend=default_backend()
                )
            except Exception as pem_error:
                # If PEM fails, try DER (base64 SPKI)
                logger.info(f"PEM load failed, trying DER format. PEM error: {pem_error}")
                try:
                    key_bytes = base64.b64decode(public_key_pem)
                    logger.info(f"Decoded base64 key, bytes length: {len(key_bytes)}")
                    public_key = serialization.load_der_public_key(
                        key_bytes,
                        backend=default_backend()
                    )
                    logger.info("Successfully loaded public key as DER format")
                except Exception as der_error:
                    logger.error(f"Both PEM and DER loading failed. PEM error: {pem_error}, DER error: {der_error}")
                    return False, f"Could not load public key: {pem_error}"
            
            # Decode signature
            signature = base64.b64decode(signature_base64)
            
            # Reconstruct canonical JSON (same as DPA)
            # Note: TPMSigner signs the base64-decoded JSON bytes
            # So we need to verify against the raw JSON bytes, not base64
            canonical_json = json.dumps(report, sort_keys=True)
            message = canonical_json.encode()
            
            # Verify RSA signature with PKCS#1 v1.5 padding and SHA256
            # This matches TPMSigner's SignData() which uses PKCS#1 v1.5
            public_key.verify(
                signature,
                message,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            return True, ""
            
        except InvalidSignature:
            return False, "Invalid signature - report may be tampered"
        except Exception as e:
            return False, f"Signature verification failed: {str(e)}"
    
    @staticmethod
    def _normalize_public_key(public_key_str: str) -> str:
        """
        Normalize public key format - convert base64 SPKI to PEM if needed
        """
        if not public_key_str:
            return public_key_str
        
        public_key_str = public_key_str.strip()
        
        # If already in PEM format, return as-is
        if public_key_str.startswith("-----BEGIN"):
            logger.debug("Public key already in PEM format")
            return public_key_str
        
        # Try to convert from base64 SPKI to PEM
        try:
            logger.debug(f"Attempting to convert public key from base64 SPKI to PEM. Key length: {len(public_key_str)}, First 50 chars: {public_key_str[:50]}")
            
            # Decode base64
            key_bytes = base64.b64decode(public_key_str)
            logger.debug(f"Decoded base64, key bytes length: {len(key_bytes)}")
            
            # Load as DER (SPKI format)
            public_key = serialization.load_der_public_key(
                key_bytes,
                backend=default_backend()
            )
            logger.debug("Successfully loaded DER public key")
            
            # Convert to PEM format
            pem_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            pem_str = pem_key.decode('utf-8').strip()
            logger.debug(f"Successfully converted to PEM format. PEM length: {len(pem_str)}")
            return pem_str
        except Exception as e:
            logger.error(f"Failed to normalize public key format: {e}", exc_info=True)
            # Return original if conversion fails
            return public_key_str
    
    @staticmethod
    async def verify_posture_signature(
        device,
        posture_data: Dict[str, Any],
        signature: str
    ) -> bool:
        """
        Verify posture report signature using device's TPM public key stored in database
        
        Args:
            device: Device object with tpm_public_key from database
            posture_data: Posture data dictionary from DPA
            signature: Base64-encoded signature from DPA
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not device.tpm_public_key:
            logger.error(f"Device {device.device_unique_id} has no TPM public key stored")
            return False
        
        # Normalize public key format (convert base64 SPKI to PEM if needed)
        logger.info(f"Verifying signature for device {device.device_unique_id}")
        logger.info(f"Original public key (first 50 chars): {device.tpm_public_key[:50] if device.tpm_public_key else 'None'}")
        logger.info(f"Is PEM format? {device.tpm_public_key.strip().startswith('-----BEGIN') if device.tpm_public_key else False}")
        
        normalized_key = SignatureService._normalize_public_key(device.tpm_public_key)
        logger.info(f"Normalized public key (first 50 chars): {normalized_key[:50] if normalized_key else 'None'}")
        logger.info(f"Is normalized PEM format? {normalized_key.strip().startswith('-----BEGIN') if normalized_key else False}")
        
        is_valid, error_msg = SignatureService.verify_tpm_signature(
            report=posture_data,
            signature_base64=signature,
            public_key_pem=normalized_key
        )
        
        if not is_valid:
            logger.warning(
                f"Invalid signature for device {device.device_unique_id}: {error_msg}"
            )
            # Log first 200 chars of the key for debugging
            logger.warning(f"Public key (first 200 chars): {normalized_key[:200] if normalized_key else 'None'}")
        else:
            logger.info(f"Signature verified successfully for device {device.device_unique_id}")
        
        return is_valid
    
    @staticmethod
    async def verify_challenge_signature(
        device,
        challenge: str,
        signature: str
    ) -> bool:
        """
        Verify TPM signature on a challenge string
        
        This is used for device attestation during token issuance.
        The challenge is signed by the device's TPM, proving the request
        comes from the genuine enrolled device.
        
        The DPA signs the challenge by:
        1. Creating a dict: {"challenge": challenge_string}
        2. Converting to canonical JSON (sorted keys)
        3. Base64-encoding the JSON
        4. Signing the base64-encoded JSON with TPM
        
        Args:
            device: Device object with tpm_public_key from database
            challenge: The challenge string that was signed
            signature: Base64-encoded TPM signature of the challenge
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        if not device.tpm_public_key:
            logger.error(f"Device {device.device_unique_id} has no TPM public key stored")
            return False
        
        # Normalize public key format
        normalized_key = SignatureService._normalize_public_key(device.tpm_public_key)
        
        # Create the challenge data dict (matching DPA's signing format)
        # The DPA will create this same dict, convert to JSON, base64-encode, then sign
        challenge_data = {"challenge": challenge}
        
        logger.info(f"Verifying challenge signature for device {device.device_unique_id}")
        logger.debug(f"Challenge data: {challenge_data}")
        
        is_valid, error_msg = SignatureService.verify_tpm_signature(
            report=challenge_data,
            signature_base64=signature,
            public_key_pem=normalized_key
        )
        
        if not is_valid:
            logger.warning(
                f"Invalid challenge signature for device {device.device_unique_id}: {error_msg}"
            )
        else:
            logger.info(f"Challenge signature verified successfully for device {device.device_unique_id}")
        
        return is_valid