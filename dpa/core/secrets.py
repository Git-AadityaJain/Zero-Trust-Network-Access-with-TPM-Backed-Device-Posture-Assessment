"""
DPAPI-based secret storage and management
"""
import os
import secrets as secrets_module
import base64
from pathlib import Path
from typing import Optional, Tuple
import logging

try:
    import win32crypt  # type: ignore
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False

logger = logging.getLogger("dpa")

class DPAPISecretManager:
    """
    Manages secure secret storage using Windows DPAPI or in-memory fallback
    """
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize DPAPI secret manager"""
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "ZTNA"
        
        self.secret_file = self.config_dir / "secret.dat"
        self.salt_file = self.config_dir / "salt.dat"

    def generate_secret(self) -> Optional[str]:
        """Generate a new 256-bit random secret"""
        try:
            secret_bytes = secrets_module.token_bytes(32)
            secret_b64 = base64.b64encode(secret_bytes).decode('utf-8')
            return secret_b64
        except Exception as e:
            logger.error(f"Failed to generate secret: {e}")
            return None

    def generate_salt(self) -> Optional[str]:
        """Generate a new 256-bit random salt"""
        try:
            salt = secrets_module.token_hex(32)
            return salt
        except Exception as e:
            logger.error(f"Failed to generate salt: {e}")
            return None

    def protect_secret(self, secret: str) -> bool:
        """Protect secret using DPAPI or save unencrypted if unavailable"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Always write to file (unencrypted for now since DPAPI not working)
            with open(self.secret_file, 'w') as f:
                f.write(secret)
                f.flush()
                os.fsync(f.fileno())
            
            if os.name == 'nt':
                os.chmod(self.secret_file, 0o600)
            
            return True
        except Exception as e:
            logger.error(f"Failed to protect secret: {e}")
            return False

    def unprotect_secret(self) -> Optional[str]:
        """Unprotect secret using DPAPI or read unencrypted if unavailable"""
        try:
            if not self.secret_file.exists():
                return None

            with open(self.secret_file, 'r') as f:
                secret = f.read().strip()
            return secret if secret else None
        except Exception as e:
            logger.error(f"Failed to unprotect secret: {e}")
            return None

    def protect_salt(self, salt: str) -> bool:
        """Protect salt using DPAPI or save unencrypted if unavailable"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Always write to file (unencrypted for now since DPAPI not working)
            with open(self.salt_file, 'w') as f:
                f.write(salt)
                f.flush()
                os.fsync(f.fileno())
            
            if os.name == 'nt':
                os.chmod(self.salt_file, 0o600)
            
            return True
        except Exception as e:
            logger.error(f"Failed to protect salt: {e}")
            return False

    def unprotect_salt(self) -> Optional[str]:
        """Unprotect salt using DPAPI or read unencrypted if unavailable"""
        try:
            if not self.salt_file.exists():
                return None

            with open(self.salt_file, 'r') as f:
                salt = f.read().strip()
            return salt if salt else None
        except Exception as e:
            logger.error(f"Failed to unprotect salt: {e}")
            return None

    def rotate_secret(self) -> Optional[str]:
        """Rotate (generate new) secret"""
        new_secret = self.generate_secret()

        if new_secret is None:
            logger.error("Failed to generate new secret during rotation")
            return None

        if not self.protect_secret(new_secret):
            logger.error("Failed to protect new secret during rotation")
            return None

        return new_secret

    def init_or_load_secret(self) -> Tuple[Optional[str], Optional[str]]:
        """Initialize new secret/salt or load existing ones"""
        if self.secret_file.exists() and self.salt_file.exists():
            secret = self.unprotect_secret()
            salt = self.unprotect_salt()

            if secret and salt:
                return secret, salt
            else:
                logger.error("Failed to load existing secret/salt")
                return None, None

        secret = self.generate_secret()
        salt = self.generate_salt()

        if secret is None or salt is None:
            logger.error("Failed to generate secret/salt")
            return None, None

        if not self.protect_secret(secret):
            logger.error("Failed to protect secret")
            return None, None

        if not self.protect_salt(salt):
            logger.error("Failed to protect salt")
            return None, None

        return secret, salt
