from typing import Optional
import logging
import requests
from .signing import PostureSigner
from ..config.settings import config_manager

logger = logging.getLogger("dpa.posture_submission")

class PostureSubmitter:
    def __init__(self, backend_url: Optional[str] = None, tpm_exe_path: Optional[str] = None):
        config = config_manager.get()
        self.backend_url = (backend_url or config.backend_url).rstrip("/")
        self.signer = PostureSigner(tpm_exe_path=tpm_exe_path)
        self.config = config

    def submit_posture(self, posture_report: dict, device_id: Optional[str] = None) -> bool:
        """
        Submit posture data to backend
        
        Args:
            posture_report: Complete posture data dictionary
            device_id: Device unique ID (UUID). If not provided, will try to get from enrollment info
            
        Returns:
            bool: True if submission successful, False otherwise
        """
        try:
            # Get device_id from enrollment info if not provided
            if not device_id:
                from .enrollment import DeviceEnrollment
                enrollment = DeviceEnrollment()
                if enrollment.is_enrolled():
                    device_info = enrollment.get_device_info()
                    device_id = device_info.get("device_id") if device_info else None
                
                if not device_id:
                    logger.error("Device ID not found. Device must be enrolled first.")
                    return False
            
            # Sign the posture report
            signature = self.signer.sign(posture_report)
            
            # Prepare payload matching backend schema
            payload = {
                "device_id": device_id,
                "posture_data": posture_report,
                "signature": signature
            }
            
            # Submit to backend
            url = f"{self.backend_url}/api/posture/submit"
            logger.info(f"Submitting posture to {url}")
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                is_compliant = response_data.get("is_compliant", False)
                logger.info(f"Posture report submitted successfully. Compliant: {is_compliant}")
                return True
            elif response.status_code == 404:
                logger.error("Device not found on backend")
                return False
            elif response.status_code == 403:
                logger.error("Device not approved or inactive")
                return False
            elif response.status_code == 401:
                logger.error("Invalid signature - TPM key may not match")
                return False
            else:
                error_msg = response.text
                logger.error(f"Submission failed: HTTP {response.status_code} - {error_msg}")
                return False
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Backend connection failed: {e}")
            return False
        except requests.exceptions.Timeout:
            logger.error("Backend request timeout")
            return False
        except Exception as e:
            logger.error(f"Submission exception: {e}")
            raise
