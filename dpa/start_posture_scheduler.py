"""
Posture Scheduler - Starts automatic posture reporting

This script starts the DPA posture scheduler which automatically submits
posture reports to the backend at configured intervals.

Usage:
    python -m dpa.start_posture_scheduler

Or run directly:
    python dpa/start_posture_scheduler.py
"""
import sys
import os
import time
import signal

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dpa.core.posture_scheduler import PostureScheduler
from dpa.utils.logger import setup_logger
from dpa.config.settings import config_manager
from dpa.core.enrollment import DeviceEnrollment

def main():
    """Main entry point for posture scheduler"""
    setup_logger()
    
    # Check if device is enrolled
    enrollment = DeviceEnrollment()
    if not enrollment.is_enrolled():
        print("❌ Device is not enrolled. Please enroll first:")
        print("   python -m dpa.cli.enroll_cli --enrollment-code YOUR_CODE")
        sys.exit(1)
    
    device_info = enrollment.get_device_info()
    print("=" * 60)
    print("DPA Posture Scheduler")
    print("=" * 60)
    print(f"Device ID: {device_info.get('device_id', 'Unknown')}")
    print(f"Backend URL: {config_manager.get().backend_url}")
    
    # Get interval from config (default: 300 seconds = 5 minutes)
    interval = config_manager.get().reporting_interval
    print(f"Reporting Interval: {interval} seconds ({interval // 60} minutes)")
    print("=" * 60)
    print()
    print("Starting posture scheduler...")
    print("Press Ctrl+C to stop")
    print()
    
    # Start scheduler
    scheduler = PostureScheduler(interval_seconds=interval)
    scheduler.start()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nStopping posture scheduler...")
        scheduler.stop()
        print("Posture scheduler stopped.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

