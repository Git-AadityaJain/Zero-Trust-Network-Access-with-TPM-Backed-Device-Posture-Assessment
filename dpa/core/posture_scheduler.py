from typing import Optional
import time
import threading
import logging
from ..modules.posture import collect_posture_report
from .posture_submission import PostureSubmitter
from ..config.settings import config_manager

logger = logging.getLogger("dpa.posture_scheduler")

class PostureScheduler:
    def __init__(self, interval_seconds: int = 300, tpm_exe_path: Optional[str] = None):
        self.interval = interval_seconds
        self.submitter = PostureSubmitter(config_manager.get().backend_url, tpm_exe_path=tpm_exe_path)
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)

    def start(self):
        logger.info(f"Starting posture scheduler with interval {self.interval} seconds")
        self._stop_event.clear()
        self._thread.start()

    def stop(self):
        logger.info("Stopping posture scheduler")
        self._stop_event.set()
        self._thread.join()

    def _run_scheduler(self):
        while not self._stop_event.is_set():
            try:
                posture_report = collect_posture_report()
                # Device ID will be extracted from enrollment info in submit_posture
                success = self.submitter.submit_posture(posture_report)
                if success:
                    logger.info("Scheduled posture report submitted successfully")
                else:
                    logger.warning("Scheduled posture report submission failed - will retry on next interval")
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(self.interval)
