from dpa.core.signing import signing_service
import base64

def test_signing():
    payload = b"Test payload for unified signing"
    signature, method = signing_service.sign_payload(payload)

    print(f"Signing method used: {method}")
    print(f"Signature (truncated): {signature[:40]}...")

if __name__ == "__main__":
    test_signing()
