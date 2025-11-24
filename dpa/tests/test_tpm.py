from dpa.core.tpm import TPMWrapper
from dpa.utils.logger import logger
import base64

def test_tpm():
    tpm = TPMWrapper(exe_path=r"C:\Users\Admin\DPA\ztna-project\dpa\TPMSigner\bin\Release\TPMSigner.exe")

    success, pubkey = tpm.init_key()
    if success:
        logger.info(f"TPM key initialized successfully. Public key (snippet): {pubkey[:30]}...")
    else:
        logger.error(f"Failed to initialize TPM key: {pubkey}")

    tpm_available, key_exists, err = tpm.check_status()
    logger.info(f"TPM available: {tpm_available}, Key exists: {key_exists}, Error: {err}")

    sample_payload = "Hello TPM!"
    sample_b64 = base64.b64encode(sample_payload.encode()).decode()

    success, signature = tpm.sign(sample_b64)
    if success:
        logger.info(f"Payload signed successfully. Signature length: {len(signature)}")
    else:
        logger.error(f"Failed to sign payload: {signature}")

if __name__ == "__main__":
    test_tpm()
