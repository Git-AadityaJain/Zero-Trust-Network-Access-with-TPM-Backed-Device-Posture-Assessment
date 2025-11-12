from typing import Optional
import logging
from .signing import PostureSigner

# Backend integration - uncomment when backend is ready
# import requests

logger = logging.getLogger("dpa.posture_submission")

class PostureSubmitter:
    def __init__(self, backend_url: str, tpm_exe_path: Optional[str] = None):
        self.backend_url = backend_url.rstrip("/")
        self.signer = PostureSigner(tpm_exe_path=tpm_exe_path)

    def submit_posture(self, posture_report: dict) -> bool:
        try:
            signature = self.signer.sign(posture_report)
            payload = {
                "report": posture_report,
                "signature": signature
            }
            
            # BACKEND INTEGRATION - Uncomment when backend is ready
            """
            url = f"{self.backend_url}/api/device/posture"
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                logger.info("Posture report submitted successfully")
                return True
            else:
                logger.error(f"Submission failed: {response.status_code} - {response.text}")
                return False
            """
            
            # TEMPORARY: Simulate successful submission
            logger.info(f"SIMULATION: Posture report signed and ready for submission")
            logger.debug(f"Signature: {signature[:20]}...")
            return True
            
        # BACKEND INTEGRATION - Uncomment when backend is ready
        # except requests.exceptions.ConnectionError as e:
        #     logger.error(f"Backend connection failed: {e}")
        #     return False
        # except requests.exceptions.Timeout:
        #     logger.error("Backend request timeout")
        #     return False
        except Exception as e:
            logger.error(f"Submission exception: {e}")
            raise
