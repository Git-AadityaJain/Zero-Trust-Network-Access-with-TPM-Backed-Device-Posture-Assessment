import sys
import os

# Add inner dpa folder to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "dpa")))

from modules.posture import collect_posture_report
from core.posture_submission import PostureSubmitter
from config.settings import config_manager

def test_posture_submission():
    posture_report = collect_posture_report()
    backend_url = config_manager.get().backend_url
    submitter = PostureSubmitter(backend_url)
    success = submitter.submit_posture(posture_report)
    if success:
        print("Posture submission test succeeded")
    else:
        print("Posture submission test failed")

if __name__ == "__main__":
    test_posture_submission()
