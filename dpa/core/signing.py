from typing import Tuple, Optional
import json
import base64
from .tpm import TPMWrapper

class PostureSigner:
    def __init__(self, tpm_exe_path: Optional[str] = None):
        self.tpm = TPMWrapper(exe_path=tpm_exe_path)

    def register_device(self) -> Tuple[bool, Optional[str]]:
        return self.tpm.init_key()

    def sign(self, posture_report: dict) -> str:
        # Create canonical JSON (same format backend expects)
        report_json = json.dumps(posture_report, sort_keys=True)
        # Sign the raw JSON bytes, not base64-encoded
        # TPMSigner will base64-decode the input, so we pass base64-encoded JSON
        # But we need to ensure the backend verifies against the same data
        report_base64 = base64.b64encode(report_json.encode("utf-8")).decode("utf-8")
        success, signature = self.tpm.sign(report_base64)
        if not success:
            raise RuntimeError(f"TPM signing failed: {signature}")
        return signature
