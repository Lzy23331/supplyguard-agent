from typing import Any

from app.agents.orchestrator import Orchestrator
from app.database import init_db
from app.repositories import create_task_record, get_report, get_task, list_events, list_evidence
from app.schemas import SupplierCreate
from app.services.seed_service import get_seeded_supplier, seed_suppliers


class TaskService:
    def create_task_from_sample(self, supplier_id: str) -> dict[str, Any]:
        init_db()
        seed_suppliers()
        supplier = get_seeded_supplier(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier not found: {supplier_id}")
        payload = SupplierCreate(
            name=supplier["name"],
            website=supplier.get("website"),
            industry=supplier.get("industry"),
            region=supplier.get("region"),
            annual_spend=supplier.get("annual_spend", 0),
            procurement_amount=supplier.get("procurement_amount"),
            cooperation_type=supplier.get("cooperation_type"),
            sample_key=supplier.get("sample_key"),
            business_status=supplier.get("business_status"),
            company_age_years=supplier.get("company_age_years"),
            profile_completeness=supplier.get("profile_completeness"),
            ownership_transparency=supplier.get("ownership_transparency"),
            urgency=supplier.get("urgency"),
        )
        task_id = create_task_record(payload)
        Orchestrator().run(task_id, supplier)
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def create_task_from_payload(self, supplier: SupplierCreate) -> dict[str, Any]:
        init_db()
        task_id = create_task_record(supplier)
        data = supplier.model_dump()
        if data.get("sample_key"):
            data["id"] = f"supplier_{data['sample_key']}_001"
        Orchestrator().run(task_id, data)
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return get_task(task_id)

    def get_events(self, task_id: str) -> list[dict[str, Any]]:
        return list_events(task_id)

    def get_report(self, task_id: str) -> str | None:
        return get_report(task_id)

    def get_evidence(self, task_id: str) -> list[dict[str, Any]]:
        return list_evidence(task_id)
