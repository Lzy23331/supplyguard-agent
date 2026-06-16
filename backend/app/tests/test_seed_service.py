from app.database import init_db, get_db
from app.services.seed_service import seed_suppliers


def test_seed_suppliers_upserts_three_samples():
    init_db()
    seed_suppliers()
    with get_db() as conn:
        rows = conn.execute("SELECT id, sample_key, expected_risk_level FROM suppliers ORDER BY sample_key").fetchall()
    sample_keys = {row["sample_key"] for row in rows}
    assert {"low", "medium", "high"}.issubset(sample_keys)
    assert any(row["id"] == "supplier_low_001" for row in rows)
