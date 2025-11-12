"""
CLI for device enrollment
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dpa.core.enrollment import DeviceEnrollment
from dpa.utils.logger import setup_logger

def main():
    setup_logger()
    enrollment = DeviceEnrollment()
    
    # Check if already enrolled
    if enrollment.is_enrolled():
        device_info = enrollment.get_device_info()
        print(f"Device is already enrolled!")
        print(f"Device ID: {device_info.get('device_id')}")
        print(f"Enrolled at: {device_info.get('enrolled_at')}")
        print()
        choice = input("Do you want to re-enroll? This will unenroll first. (yes/no): ").strip().lower()
        if choice == 'yes':
            enrollment.unenroll_device()
            print("Device unenrolled. Proceeding with enrollment...")
        else:
            print("Enrollment cancelled.")
            return
    
    # Get enrollment code from user
    print("=== Device Enrollment ===")
    print("Please enter the enrollment code provided by your administrator.")
    enrollment_code = input("Enrollment Code: ").strip()
    
    if not enrollment_code:
        print("Error: Enrollment code cannot be empty.")
        return
    
    print("\nEnrolling device...")
    print("This may take a moment as TPM key is being initialized...")
    
    success, result = enrollment.enroll_device(enrollment_code)
    
    if success:
        print(f"\n✓ Enrollment successful!")
        print(f"Device ID: {result}")
        print("\nYour device is now registered and will begin submitting posture reports.")
    else:
        print(f"\n✗ Enrollment failed!")
        print(f"Error: {result}")
        print("\nPlease contact your administrator for assistance.")

if __name__ == "__main__":
    main()
