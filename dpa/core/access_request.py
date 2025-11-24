"""
Access Request Handler - Submits posture with resource access requests

This module handles resource access requests that include fresh posture data.
When a resource access is requested, it collects current posture, signs it,
and includes it in the access request.
"""
from typing import Optional, Dict, Any
import logging
import requests
from .signing import PostureSigner
from ..modules.posture import collect_posture_report
from ..config.settings import config_manager
from .enrollment import DeviceEnrollment

logger = logging.getLogger("dpa.access_request")


class AccessRequestHandler:
    """Handles resource access requests with posture submission"""
    
    def __init__(self, backend_url: Optional[str] = None, tpm_exe_path: Optional[str] = None):
        config = config_manager.get()
        self.backend_url = (backend_url or config.backend_url).rstrip("/")
        self.signer = PostureSigner(tpm_exe_path=tpm_exe_path)
        self.config = config
    
    def request_access(
        self,
        device_id: int,
        resource: str,
        access_type: str = "read",
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request access to a resource with fresh posture data
        
        Args:
            device_id: Device ID (integer, from backend)
            resource: Resource identifier (e.g., "server1", "database1")
            access_type: Type of access ("read", "write", "execute")
            auth_token: JWT token for authentication (required)
            
        Returns:
            dict: Access response with 'allowed', 'token', 'reason', etc.
        """
        try:
            # Collect fresh posture data
            logger.info("Collecting fresh posture data for access request")
            posture_report = collect_posture_report()
            
            # Sign the posture report
            signature = self.signer.sign(posture_report)
            
            # Prepare access request payload
            payload = {
                "device_id": device_id,
                "resource": resource,
                "access_type": access_type,
                "posture_data": posture_report,
                "posture_signature": signature
            }
            
            # Submit access request with posture
            url = f"{self.backend_url}/api/access/request"
            logger.info(f"Requesting access to {resource} with fresh posture data")
            
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Access request successful: {result.get('allowed', False)}")
                return result
            elif response.status_code == 403:
                error_data = response.json()
                logger.warning(f"Access denied: {error_data.get('detail', 'Unknown reason')}")
                return {
                    "allowed": False,
                    "reason": error_data.get("detail", "Access denied"),
                    "error": error_data
                }
            else:
                error_msg = response.text
                logger.error(f"Access request failed: HTTP {response.status_code} - {error_msg}")
                return {
                    "allowed": False,
                    "reason": f"Request failed: HTTP {response.status_code}",
                    "error": error_msg
                }
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Backend connection failed: {e}")
            return {
                "allowed": False,
                "reason": "Cannot connect to backend",
                "error": str(e)
            }
        except requests.exceptions.Timeout:
            logger.error("Backend request timeout")
            return {
                "allowed": False,
                "reason": "Request timeout",
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"Access request exception: {e}")
            return {
                "allowed": False,
                "reason": f"Request failed: {str(e)}",
                "error": str(e)
            }

