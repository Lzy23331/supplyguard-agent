from app.evidence_providers.base import EvidenceProvider
from app.evidence_providers.provider_manager import EvidenceProviderManager
from app.database import init_db
from app.repositories import create_task_record, list_events
from app.schemas import SupplierCreate


class FailingProvider(EvidenceProvider):
    name = "FailingProvider"
    source_type = "mock_external"

    def search(self, supplier):
        raise RuntimeError("provider offline")


def test_provider_manager_collects_external_and_internal_evidence():
    init_db()
    task_id = create_task_record(SupplierCreate(name="Northbridge Electronics Trading LLC."))
    evidence = EvidenceProviderManager().collect(task_id, {"name": "Northbridge Electronics Trading LLC."})

    assert evidence
    assert {item["source_type"] for item in evidence} >= {"mock_external", "internal_record"}
    assert all(item["content"] and item["title"] and item["raw_text"] for item in evidence)


def test_provider_manager_failure_writes_warning_event():
    init_db()
    task_id = create_task_record(SupplierCreate(name="Northbridge Electronics Trading LLC."))
    evidence = EvidenceProviderManager(providers=[FailingProvider()]).collect(task_id, {"name": "Northbridge Electronics Trading LLC."})

    assert evidence == []
    events = list_events(task_id)
    assert any(event["event_type"] == "provider_warning" and "provider offline" in event["summary"] for event in events)
