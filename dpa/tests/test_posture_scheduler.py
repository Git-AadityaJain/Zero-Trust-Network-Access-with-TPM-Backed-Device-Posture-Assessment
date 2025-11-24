import time
from dpa.core.posture_scheduler import PostureScheduler

def test_scheduler():
    scheduler = PostureScheduler(interval_seconds=60)  # every 60 seconds for test
    scheduler.start()
    time.sleep(180)  # run scheduler for 3 minutes
    scheduler.stop()

if __name__ == "__main__":
    test_scheduler()
