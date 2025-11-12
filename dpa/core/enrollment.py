"""
Device enrollment and registration with backend
"""
from typing import Optional, Tuple
from datetime import datetime, timezone
import logging
import json
from pathlib import Path
from .signing import PostureSigner
from ..config.settings import config_manager

# Backend integration - uncomment when backend is ready
# import requests

logger = logging.getLogger("dpa.enrollment")

class DeviceEnrollment:
    """
    Handles one-time device enrollment with backend
    """
    def __init__(self, tpm_exe_path: Optional[str] = None):
        self.signer = PostureSigner(tpm_exe_path=tpm_exe_path)
        self.config = config_manager.get()
        self.enrollment_file = Path(self.config.config_dir) / "enrollment.json"
        
    def is_enrolled(self) -> bool:
        """Check if device is already enrolled"""
        return self.enrollment_file.exists()
    
    def get_device_info(self) -> Optional[dict]:
        """Get stored device enrollment information"""
        if not self.is_enrolled():
            return None
        try:
            with open(self.enrollment_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read enrollment info: {e}")
            return None
    
    def enroll_device(self, enrollment_code: str) -> Tuple[bool, Optional[str]]:
        """
        Enroll device with backend using enrollment code
        
        Args:
            enrollment_code: One-time enrollment code from admin
            
        Returns:
            (success, device_id_or_error)
        """
        if self.is_enrolled():
            logger.warning("Device already enrolled")
            existing_info = self.get_device_info()
            return False, f"Already enrolled with device_id: {existing_info.get('device_id')}"
        
        # Validate enrollment code format
        if not enrollment_code or len(enrollment_code) < 8:
            return False, "Invalid enrollment code format"
        
        try:
            # Step 1: Initialize TPM key and get public key
            logger.info("Initializing TPM key during enrollment")
            success, pub_key = self.signer.register_device()
            if not success:
                logger.error(f"TPM key initialization failed: {pub_key}")
                return False, f"TPM initialization failed: {pub_key}"
            
            logger.info("TPM key initialized successfully")
            
            # Step 2: Prepare enrollment payload
            from ..modules.posture import collect_posture_report
            initial_posture = collect_posture_report()
            
            enrollment_payload = {
                "enrollment_code": enrollment_code,
                "tpm_public_key": pub_key,
                "initial_posture": initial_posture
            }
            
            # Step 3: Send enrollment request to backend
            # BACKEND INTEGRATION - Uncomment when backend is ready
            """
            url = f"{self.config.backend_url}/api/device/enroll"
            logger.info(f"Sending enrollment request to {url}")
            
            response = requests.post(url, json=enrollment_payload, timeout=30)
            
            if response.status_code == 200:
                enrollment_response = response.json()
                device_id = enrollment_response.get("device_id")
                
                if not device_id:
                    logger.error("Backend did not return device_id")
                    return False, "Invalid enrollment response from backend"
                
                enrolled_at = enrollment_response.get("enrolled_at")
            elif response.status_code == 400:
                error_msg = response.json().get("detail", response.text)
                logger.error(f"Enrollment rejected: {error_msg}")
                return False, f"Enrollment rejected: {error_msg}"
            elif response.status_code == 403:
                logger.error("Invalid enrollment code")
                return False, "Invalid or expired enrollment code"
            else:
                logger.error(f"Enrollment failed: HTTP {response.status_code}")
                return False, f"Backend error: HTTP {response.status_code}"
            """
            
            # TEMPORARY: Simulate successful backend response for testing
            import uuid
            device_id = str(uuid.uuid4())
            enrolled_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            logger.info(f"SIMULATION: Device enrolled with ID {device_id}")
            
            # Step 4: Save enrollment information locally
            enrollment_info = {
                "device_id": device_id,
                "backend_url": self.config.backend_url,
                "enrolled_at": enrolled_at,
                "tpm_public_key": pub_key
            }
            
            self._save_enrollment_info(enrollment_info)
            
            logger.info(f"Device enrolled successfully with ID: {device_id}")
            return True, device_id
                
        # BACKEND INTEGRATION - Uncomment when backend is ready
        # except requests.exceptions.ConnectionError as e:
        #     logger.error(f"Backend connection failed during enrollment: {e}")
        #     return False, f"Cannot connect to backend: {e}"
        # except requests.exceptions.Timeout as e:
        #     logger.error(f"Backend request timeout: {e}")
        #     return False, "Backend request timeout"
        except Exception as e:
            logger.error(f"Enrollment exception: {e}")
            return False, f"Enrollment error: {e}"
    
    def _save_enrollment_info(self, enrollment_info: dict):
        """Save enrollment information to disk with restricted permissions"""
        try:
            self.enrollment_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with secure permissions
            with open(self.enrollment_file, 'w') as f:
                json.dump(enrollment_info, f, indent=2)
            
            # Set file permissions to read-only for current user
            import os
            if os.name == 'nt':  # Windows
                os.chmod(self.enrollment_file, 0o600)
            
            logger.info(f"Enrollment info saved to {self.enrollment_file}")
        except Exception as e:
            logger.error(f"Failed to save enrollment info: {e}")
            raise
    
    def unenroll_device(self) -> bool:
        """
        Unenroll device (for testing or device replacement)
        WARNING: This will require re-enrollment
        """
        try:
            if self.enrollment_file.exists():
                self.enrollment_file.unlink()
                logger.info("Device unenrolled successfully")
                return True
            else:
                logger.warning("Device was not enrolled")
                return False
        except Exception as e:
            logger.error(f"Failed to unenroll device: {e}")
            return False
    
    def verify_enrollment(self) -> Tuple[bool, Optional[str]]:
        """
        Verify enrollment status with backend
        
        Returns:
            (enrolled, error_message)
        """
        if not self.is_enrolled():
            return False, "Device not enrolled locally"
        
        device_info = self.get_device_info()
        device_id = device_info.get("device_id")
        
        # BACKEND INTEGRATION - Uncomment when backend is ready
        """
        try:
            url = f"{self.config.backend_url}/api/device/{device_id}/status"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get("enrolled"):
                    return True, None
                else:
                    return False, "Device not found or inactive on backend"
            elif response.status_code == 404:
                return False, "Device not found on backend"
            else:
                return False, f"Backend error: HTTP {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to backend"
        except Exception as e:
            return False, f"Verification error: {e}"
        """
        
        # TEMPORARY: Simulate successful verification
        logger.info(f"SIMULATION: Verified enrollment for device {device_id}")
        return True, None
