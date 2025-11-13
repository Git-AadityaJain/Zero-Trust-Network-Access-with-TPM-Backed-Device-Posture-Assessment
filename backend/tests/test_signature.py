# test_signature.py

from app.services.signature_service import SignatureService

# Example usage
report = {"device_id": "123", "posture": {"firewall": "enabled"}}
signature = "base64_encoded_signature_here"
public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----"""

is_valid, error = SignatureService.verify_tpm_signature(report, signature, public_key)
print(f"Valid: {is_valid}, Error: {error}")
