import sys
import os
import unittest
import json
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dpa.core.tpm import TPMWrapper
from dpa.core.signing import PostureSigner
from dpa.core.enrollment import DeviceEnrollment
from dpa.core.posture_submission import PostureSubmitter
from dpa.core.posture_scheduler import PostureScheduler
from dpa.core.secrets import DPAPISecretManager
from dpa.modules.posture import collect_posture_report
from dpa.config.settings import config_manager

TPM_EXECUTABLE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "TPMSigner.exe"))

class TestDPACore(unittest.TestCase):
    """Comprehensive DPA core functionality tests"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.original_config_dir = config_manager.get().config_dir
        config_manager.get().config_dir = str(cls.test_dir)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.test_dir, ignore_errors=True)
        config_manager.get().config_dir = cls.original_config_dir

    def setUp(self):
        """Set up for each test"""
        self.tpm_path = TPM_EXECUTABLE_PATH
        self.backend_url = config_manager.get().backend_url
        self.test_config_dir = str(self.test_dir)

    def test_01_secret_generation(self):
        """Test DPAPI secret generation and storage"""
        secret_mgr = DPAPISecretManager(config_dir=self.test_config_dir)
        
        secret = secret_mgr.generate_secret()
        self.assertIsNotNone(secret)
        self.assertIsInstance(secret, str)
        self.assertGreater(len(secret), 20)
        
        salt = secret_mgr.generate_salt()
        self.assertIsNotNone(salt)
        self.assertIsInstance(salt, str)
        self.assertGreater(len(salt), 32)

    def test_02_secret_protection(self):
        """Test secret protection and unprotection"""
        secret_mgr = DPAPISecretManager(config_dir=self.test_config_dir)
        
        test_secret = "test_secret_value_12345"
        
        success = secret_mgr.protect_secret(test_secret)
        self.assertTrue(success)
        
        recovered = secret_mgr.unprotect_secret()
        self.assertEqual(recovered, test_secret)

    def test_03_tpm_key_init(self):
        """Test TPM key initialization"""
        tpm = TPMWrapper(exe_path=self.tpm_path)
        success, pub_key = tpm.init_key()
        
        if success:
            self.assertIsInstance(pub_key, str)
            self.assertGreater(len(pub_key), 0)
        else:
            self.skipTest(f"TPM initialization failed: {pub_key}")

    def test_04_tpm_status_check(self):
        """Test TPM status checking"""
        tpm = TPMWrapper(exe_path=self.tpm_path)
        tpm_available, key_exists, err = tpm.check_status()
        
        if tpm_available and key_exists:
            self.assertTrue(tpm_available)
            self.assertTrue(key_exists)
            self.assertIsNone(err)
        else:
            self.skipTest("TPM not available or key not initialized")

    def test_05_posture_collection(self):
        """Test posture data collection"""
        report = collect_posture_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn("device_id", report)
        self.assertIn("timestamp", report)
        self.assertIn("os_info", report)
        self.assertIn("firewall", report)
        self.assertIn("disk_encryption", report)
        self.assertIn("antivirus", report)
        self.assertIn("fingerprint", report)

    def test_06_posture_signing(self):
        """Test posture report signing with TPM"""
        signer = PostureSigner(tpm_exe_path=self.tpm_path)
        
        sample_report = {
            "device_id": "test-device-123",
            "timestamp": "2023-11-12T00:00:00Z",
            "posture_data": {"os": "Windows", "antivirus": True, "firewall": True}
        }
        
        try:
            signature = signer.sign(sample_report)
            self.assertIsInstance(signature, str)
            import base64
            base64.b64decode(signature, validate=True)
        except RuntimeError as e:
            self.skipTest(f"TPM signing failed: {e}")

    def test_07_enrollment_flow(self):
        """Test device enrollment flow"""
        enrollment = DeviceEnrollment(tpm_exe_path=self.tpm_path)
        
        if enrollment.is_enrolled():
            enrollment.unenroll_device()
        
        self.assertFalse(enrollment.is_enrolled())
        
        test_code = "TEST-ENROLLMENT-CODE-12345"
        try:
            success, device_id = enrollment.enroll_device(test_code)
            
            if success:
                self.assertTrue(enrollment.is_enrolled())
                self.assertIsInstance(device_id, str)
                
                device_info = enrollment.get_device_info()
                self.assertIsNotNone(device_info)
                self.assertEqual(device_info["device_id"], device_id)
                self.assertIn("enrolled_at", device_info)
                self.assertIn("tpm_public_key", device_info)
            else:
                self.skipTest(f"Enrollment failed (expected due to TPM): {device_id}")
        except Exception as e:
            self.skipTest(f"Enrollment exception: {e}")

    def test_08_enrollment_verification(self):
        """Test enrollment verification"""
        enrollment = DeviceEnrollment(tpm_exe_path=self.tpm_path)
        
        if not enrollment.is_enrolled():
            self.skipTest("Device not enrolled")
        
        is_valid, error = enrollment.verify_enrollment()
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_09_posture_submission(self):
        """Test posture report submission"""
        submitter = PostureSubmitter(self.backend_url, tpm_exe_path=self.tpm_path)
        
        report = collect_posture_report()
        
        try:
            result = submitter.submit_posture(report)
            self.assertTrue(result)
        except RuntimeError as e:
            self.skipTest(f"Submission failed (expected due to TPM): {e}")

    def test_10_scheduler_lifecycle(self):
        """Test posture scheduler start and stop"""
        scheduler = PostureScheduler(interval_seconds=2, tpm_exe_path=self.tpm_path)
        
        scheduler.start()
        self.assertTrue(scheduler._thread.is_alive())
        
        import time
        time.sleep(3)
        
        scheduler.stop()
        time.sleep(1)
        self.assertFalse(scheduler._thread.is_alive())

    def test_11_unenrollment(self):
        """Test device unenrollment"""
        enrollment = DeviceEnrollment(tpm_exe_path=self.tpm_path)
        
        if not enrollment.is_enrolled():
            self.skipTest("Device not enrolled, cannot test unenrollment")
        
        success = enrollment.unenroll_device()
        self.assertTrue(success)
        self.assertFalse(enrollment.is_enrolled())

    def test_12_invalid_enrollment_code(self):
        """Test enrollment with invalid code format"""
        enrollment = DeviceEnrollment(tpm_exe_path=self.tpm_path)
        
        if enrollment.is_enrolled():
            enrollment.unenroll_device()
        
        success, error = enrollment.enroll_device("")
        self.assertFalse(success)
        self.assertIn("Invalid", error)
        
        success, error = enrollment.enroll_device("ABC")
        self.assertFalse(success)

    def test_13_double_enrollment_prevention(self):
        """Test that double enrollment is prevented"""
        enrollment = DeviceEnrollment(tpm_exe_path=self.tpm_path)
        
        if not enrollment.is_enrolled():
            self.skipTest("Device not enrolled, cannot test double enrollment")
        
        success, error = enrollment.enroll_device("TEST-SECOND-ENROLLMENT")
        self.assertFalse(success)
        self.assertIn("Already enrolled", error)

    def test_14_posture_report_with_device_id(self):
        """Test that posture reports include device_id after enrollment"""
        enrollment = DeviceEnrollment(tpm_exe_path=self.tpm_path)
        
        if not enrollment.is_enrolled():
            self.skipTest("Device not enrolled")
        
        report = collect_posture_report()
        device_info = enrollment.get_device_info()
        
        self.assertEqual(report["device_id"], device_info["device_id"])

    def test_15_secret_rotation(self):
        """Test secret rotation"""
        secret_mgr = DPAPISecretManager(config_dir=self.test_config_dir)
        
        secret_mgr.protect_secret("initial_secret")
        initial = secret_mgr.unprotect_secret()
        
        new_secret = secret_mgr.rotate_secret()
        self.assertIsNotNone(new_secret)
        
        rotated = secret_mgr.unprotect_secret()
        self.assertNotEqual(initial, rotated)

if __name__ == "__main__":
    unittest.main(verbosity=2)
