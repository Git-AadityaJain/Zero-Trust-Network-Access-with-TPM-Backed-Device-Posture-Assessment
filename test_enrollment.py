import sys
sys.path.insert(0, r"C:\Users\Admin\DPA\ztna-project\dpa\dpa")

from core.enrollment import enrollment_service

def test_enroll():
    success = enrollment_service.enroll_device()
    if success:
        print("Enrollment test succeeded")
    else:
        print("Enrollment test failed")

if __name__ == "__main__":
    test_enroll()
