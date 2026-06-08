import json
from app.config import get_settings


def list_sample_suppliers() -> list[dict]:
    path = get_settings().project_root / "data" / "sample_suppliers" / "suppliers.json"
    samples = json.loads(path.read_text(encoding="utf-8"))
    return [
        {
            "sample_key": item["sample_key"],
            "risk_profile": item["risk_profile"],
            "name": item["name"],
            "website": item["website"],
            "industry": item["industry"],
            "region": item["region"],
            "annual_spend": item["annual_spend"],
            "cooperation_type": item["cooperation_type"],
            "summary": item["summary"],
        }
        for item in samples
    ]

