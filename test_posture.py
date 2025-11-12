import json
from dpa.modules.posture import collect_posture_report

def test_collect_posture():
    report = collect_posture_report()
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    test_collect_posture()
