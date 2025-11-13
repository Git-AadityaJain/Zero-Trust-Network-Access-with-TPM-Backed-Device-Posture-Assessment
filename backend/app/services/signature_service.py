# app/services/signature_service.py

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64
import json
from typing import Tuple

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
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )
            
            # Decode signature
            signature = base64.b64decode(signature_base64)
            
            # Reconstruct canonical JSON (same as DPA)
            canonical_json = json.dumps(report, sort_keys=True)
            message = canonical_json.encode()
            
            # Verify RSA-PSS signature with SHA256
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True, ""
            
        except InvalidSignature:
            return False, "Invalid signature - report may be tampered"
        except Exception as e:
            return False, f"Signature verification failed: {str(e)}"
