#!/usr/bin/env python3
"""
Get TPM public key in PEM format for database update
"""
import sys
import base64
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dpa.core.tpm import TPMWrapper
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def get_tpm_public_key_pem():
    """Get TPM public key and convert to PEM format"""
    try:
        tpm = TPMWrapper()
        success, pub_key_base64 = tpm.register_device()
        
        if not success:
            print(f"ERROR: {pub_key_base64}", file=sys.stderr)
            return None
        
        # Decode base64
        key_bytes = base64.b64decode(pub_key_base64)
        
        # Load as DER (SubjectPublicKeyInfo format)
        public_key = serialization.load_der_public_key(
            key_bytes,
            backend=default_backend()
        )
        
        # Convert to PEM
        pem_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem_key.decode('utf-8').strip()
    
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    pem_key = get_tpm_public_key_pem()
    if pem_key:
        print(pem_key)
    else:
        sys.exit(1)

