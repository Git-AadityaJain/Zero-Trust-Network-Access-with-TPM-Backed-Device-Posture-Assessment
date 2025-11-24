"""
Device enrollment and registration with backend
"""
from typing import Optional, Tuple
from datetime import datetime, timezone
import logging
import json
from pathlib import Path
import requests
from .signing import PostureSigner
from ..config.settings import config_manager

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
            
            # Step 2: Collect device information
            from ..modules.posture import collect_posture_report
            from ..modules.fingerprint import get_device_fingerprint
            from ..modules.os_info import get_os_info
            import hashlib
            
            initial_posture = collect_posture_report()
            os_info = get_os_info()
            fingerprint_data = get_device_fingerprint()
            
            # Get full fingerprint hash (64 chars for SHA256)
            fingerprint_str = fingerprint_data.get("fingerprint_hash", "unknown")
            if len(fingerprint_str) < 64:
                # If truncated, regenerate full hash
                mb_serial = fingerprint_data.get("motherboard_serial", "unknown")
                bios_serial = fingerprint_data.get("bios_serial", "unknown")
                system_uuid = fingerprint_data.get("system_uuid", "unknown")
                fingerprint_data_str = f"{mb_serial}:{bios_serial}:{system_uuid}"
                fingerprint_hash = hashlib.sha256(fingerprint_data_str.encode()).hexdigest()
            else:
                fingerprint_hash = fingerprint_str
            
            # Step 3: Prepare enrollment payload matching backend schema
            enrollment_payload = {
                "enrollment_code": enrollment_code,
                "device_name": os_info.get("hostname", "Unknown Device"),
                "fingerprint_hash": fingerprint_hash,
                "tpm_public_key": pub_key,
                "os_type": os_info.get("os_type", "Windows"),
                "os_version": os_info.get("os_version"),
                "device_model": os_info.get("device_model"),
                "manufacturer": os_info.get("manufacturer"),
                "initial_posture": initial_posture
            }
            
            # Step 4: Send enrollment request to backend
            url = f"{self.config.backend_url}/api/devices/enroll"
            logger.info(f"Sending enrollment request to {url}")
            
            response = requests.post(url, json=enrollment_payload, timeout=30)
            
            if response.status_code == 200 or response.status_code == 201:
                enrollment_response = response.json()
                device_id = enrollment_response.get("device_id")
                
                if not device_id:
                    logger.error("Backend did not return device_id")
                    return False, "Invalid enrollment response from backend"
                
                enrolled_at = datetime.now(timezone.utc).isoformat()
                logger.info(f"Device enrolled successfully with ID: {device_id}")
            elif response.status_code == 400:
                error_msg = response.json().get("detail", response.text)
                logger.error(f"Enrollment rejected: {error_msg}")
                return False, f"Enrollment rejected: {error_msg}"
            elif response.status_code == 403:
                logger.error("Invalid enrollment code")
                return False, "Invalid or expired enrollment code"
            elif response.status_code == 409:
                error_msg = response.json().get("detail", response.text)
                logger.error(f"Device already enrolled: {error_msg}")
                return False, f"Device already enrolled: {error_msg}"
            else:
                error_msg = response.text
                logger.error(f"Enrollment failed: HTTP {response.status_code} - {error_msg}")
                return False, f"Backend error: HTTP {response.status_code}"
            
            # Step 5: Save enrollment information locally
            enrollment_info = {
                "device_id": device_id,
                "backend_url": self.config.backend_url,
                "enrolled_at": enrolled_at,
                "tpm_public_key": pub_key
            }
            
            self._save_enrollment_info(enrollment_info)
            
            logger.info(f"Device enrollment completed. Device ID: {device_id}, Status: pending approval")
            return True, device_id
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Backend connection failed during enrollment: {e}")
            return False, f"Cannot connect to backend: {e}"
        except requests.exceptions.Timeout as e:
            logger.error(f"Backend request timeout: {e}")
            return False, "Backend request timeout"
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
    
    def _unenroll_device(self) -> bool:
        """
        Internal method to unenroll device (used only during re-enrollment)
        This removes local enrollment file and optionally deletes device from backend
        """
        try:
            device_info = None
            if self.enrollment_file.exists():
                # Read device info before deleting
                try:
                    with open(self.enrollment_file, 'r') as f:
                        device_info = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not read enrollment file: {e}")
                
                # Delete local enrollment file
                self.enrollment_file.unlink()
                logger.info("Local enrollment file removed")
            
            # Try to delete from backend if we have device info
            if device_info and device_info.get("device_id"):
                device_id = device_info.get("device_id")
                try:
                    # Use public unenroll endpoint (no auth required)
                    url = f"{self.config.backend_url}/api/devices/unenroll/{device_id}"
                    response = requests.delete(url, timeout=10)
                    if response.status_code == 204:
                        logger.info(f"Device {device_id} deleted from backend")
                    elif response.status_code == 403:
                        logger.warning(f"Device {device_id} is active and cannot be self-unenrolled. "
                                     f"Please delete manually from admin panel.")
                    else:
                        logger.warning(f"Could not delete device from backend (HTTP {response.status_code}). "
                                     f"Device may still exist in backend. Please delete manually from admin panel.")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Could not contact backend to delete device: {e}. "
                                 f"Device may still exist in backend. Please delete manually from admin panel.")
            
            logger.info("Device unenrolled successfully")
            return True
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
        
        if not device_id:
            return False, "Device ID not found in enrollment info"
        
        try:
            url = f"{self.config.backend_url}/api/devices/status/{device_id}"
            logger.info(f"Verifying enrollment status at {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                is_approved = status_data.get("is_approved", False)
                status = status_data.get("status", "unknown")
                
                if is_approved and status == "active":
                    logger.info(f"Device {device_id} is enrolled and active")
                    return True, None
                elif status == "pending":
                    logger.info(f"Device {device_id} is enrolled but pending approval")
                    return True, "Device pending admin approval"
                else:
                    return False, f"Device status: {status}"
            elif response.status_code == 404:
                return False, "Device not found on backend"
            else:
                error_msg = response.text
                return False, f"Backend error: HTTP {response.status_code} - {error_msg}"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to backend: {e}")
            return False, f"Cannot connect to backend: {e}"
        except requests.exceptions.Timeout:
            logger.error("Backend request timeout during verification")
            return False, "Backend request timeout"
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False, f"Verification error: {e}"
