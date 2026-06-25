from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import init_db
from app.services.demo_case_service import DemoCaseService


def main() -> None:
    init_db()
    service = DemoCaseService()
    for case in service.list_cases():
        detail = service.run_case(case["case_id"])
        print(f"seeded {case['case_id']} -> {detail.get('task_id') or detail.get('id')}")


if __name__ == "__main__":
    main()
