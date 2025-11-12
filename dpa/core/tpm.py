import subprocess
import logging
import os
import base64
import re
from typing import Tuple, Optional

logger = logging.getLogger("dpa.tpm")

class TPMWrapper:
    def __init__(self, exe_path: Optional[str] = None):
        if exe_path:
            self.exe_path = exe_path
        else:
            self.exe_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "TPMSigner.exe")

        if not os.path.isfile(self.exe_path):
            logger.error(f"TPMSigner executable not found at: {self.exe_path}")

    def init_key(self) -> Tuple[bool, Optional[str]]:
        try:
            result = subprocess.run(
                [self.exe_path, "init-key"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                logger.error(f"init-key failed: {result.stderr.strip()}")
                return False, result.stderr.strip()

            pub_key = self._parse_output(result.stdout)
            return True, pub_key
        except Exception as e:
            logger.error(f"init-key exception: {e}")
            return False, str(e)

    def check_status(self) -> Tuple[bool, bool, Optional[str]]:
        try:
            result = subprocess.run(
                [self.exe_path, "status"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode not in (0, 2):
                logger.error(f"status failed: {result.stderr.strip()}")
                return False, False, result.stderr.strip()

            tpm_available = '"tpm_available": true' in result.stdout.lower()
            key_exists = '"key_exists": true' in result.stdout.lower()

            return tpm_available, key_exists, None
        except Exception as e:
            logger.error(f"status exception: {e}")
            return False, False, str(e)

    def sign(self, base64_payload: str) -> Tuple[bool, Optional[str]]:
        try:
            result = subprocess.run(
                [self.exe_path, "sign", base64_payload],
                capture_output=True, text=True, timeout=15
            )
            full_output = result.stdout + "\n" + result.stderr

            logger.debug(f"TPM sign output: {full_output}")

            if result.returncode != 0:
                return False, result.stderr.strip()

            signature = self._parse_output(result.stdout)
            if signature and self._is_valid_base64(signature):
                return True, signature

            cleaned_sig = self._extract_base64_signature(full_output)
            if cleaned_sig:
                return True, cleaned_sig

            return False, "Invalid TPM signature output"
        except Exception as e:
            logger.error(f"sign exception: {e}")
            return False, str(e)

    def _parse_output(self, stdout: str) -> Optional[str]:
        try:
            start = stdout.index("[OUTPUT_START]") + len("[OUTPUT_START]")
            end = stdout.index("[OUTPUT_END]")
            return stdout[start:end].strip()
        except ValueError:
            logger.error("Output markers not found in TPM CLI output")
            return None

    def _is_valid_base64(self, s: str) -> bool:
        try:
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False

    def _extract_base64_signature(self, output: str) -> Optional[str]:
        candidates = re.findall(r"[A-Za-z0-9+/=]{16,}", output)
        for candidate in candidates:
            if self._is_valid_base64(candidate):
                return candidate
        return None
