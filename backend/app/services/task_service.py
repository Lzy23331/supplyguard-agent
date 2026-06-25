from typing import Any

from app.agents.orchestrator import Orchestrator
from app.database import init_db
from app.repositories import create_task_record, get_report, get_task, list_events, list_evidence
from app.schemas import SupplierCreate
from app.services.company_query_service import CompanyQueryService
from app.services.seed_service import get_seeded_supplier, seed_suppliers


class TaskService:
    def _sample_payload_and_data(self, supplier_id: str) -> tuple[SupplierCreate, dict[str, Any]]:
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
            procurement_amount=supplier.get("procurement_amount") or supplier.get("annual_spend", 0),
            cooperation_type=supplier.get("cooperation_type"),
            sample_key=supplier.get("sample_key"),
            business_status=supplier.get("business_status"),
            company_age_years=supplier.get("company_age_years"),
            profile_completeness=supplier.get("profile_completeness"),
            ownership_transparency=supplier.get("ownership_transparency"),
            urgency=supplier.get("urgency"),
            summary=supplier.get("summary"),
            tags=supplier.get("tags", []),
            expected_risk_level=supplier.get("expected_risk_level"),
        )
        return payload, supplier

    def create_pending_task_from_sample(self, supplier_id: str, material_text: str | None = None, upload_ids: list[str] | None = None) -> dict[str, Any]:
        payload, _ = self._sample_payload_and_data(supplier_id)
        task_id = create_task_record(payload, material_text=material_text, upload_ids=upload_ids)
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def create_task_from_sample(self, supplier_id: str, material_text: str | None = None, upload_ids: list[str] | None = None) -> dict[str, Any]:
        payload, supplier = self._sample_payload_and_data(supplier_id)
        task_id = create_task_record(payload, material_text=material_text, upload_ids=upload_ids)
        supplier = {**supplier, "material_text": material_text, "upload_ids": upload_ids or []}
        Orchestrator().run(task_id, supplier)
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def _payload_to_supplier_data(self, supplier: SupplierCreate) -> dict[str, Any]:
        data = supplier.model_dump()
        if data.get("procurement_amount") is None:
            data["procurement_amount"] = data.get("annual_spend") or 0
        if data.get("annual_spend") is None:
            data["annual_spend"] = data.get("procurement_amount") or 0
        if data.get("tags") is None:
            data["tags"] = []
        if data.get("sample_key"):
            data["id"] = f"supplier_{data['sample_key']}_001"
        return data

    def create_pending_task_from_payload(self, supplier: SupplierCreate, material_text: str | None = None, upload_ids: list[str] | None = None) -> dict[str, Any]:
        init_db()
        task_id = create_task_record(supplier, material_text=material_text, upload_ids=upload_ids)
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def create_task_from_payload(self, supplier: SupplierCreate, material_text: str | None = None, upload_ids: list[str] | None = None) -> dict[str, Any]:
        init_db()
        task_id = create_task_record(supplier, material_text=material_text, upload_ids=upload_ids)
        data = self._payload_to_supplier_data(supplier)
        data["material_text"] = material_text
        data["upload_ids"] = upload_ids or []
        Orchestrator().run(task_id, data)
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def create_pending_task_from_company_query(
        self,
        company_name: str,
        procurement_amount: float | None = None,
        cooperation_type: str | None = None,
        material_text: str | None = None,
        upload_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        init_db()
        payload = CompanyQueryService().placeholder_payload(company_name, procurement_amount, cooperation_type)
        task_id = create_task_record(
            payload,
            material_text=material_text,
            upload_ids=upload_ids,
            query_type="company_name",
            company_name=company_name,
        )
        task = get_task(task_id)
        if not task:
            raise RuntimeError("Task was not created")
        return task

    def create_task_from_company_query(
        self,
        company_name: str,
        procurement_amount: float | None = None,
        cooperation_type: str | None = None,
        material_text: str | None = None,
        upload_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        task = self.create_pending_task_from_company_query(
            company_name=company_name,
            procurement_amount=procurement_amount,
            cooperation_type=cooperation_type,
            material_text=material_text,
            upload_ids=upload_ids,
        )
        supplier = {
            **task["supplier"],
            "query_type": "company_name",
            "company_name": company_name,
            "procurement_amount": procurement_amount or task["supplier"].get("procurement_amount") or 0,
            "cooperation_type": cooperation_type,
            "material_text": material_text,
            "upload_ids": upload_ids or [],
        }
        Orchestrator().run(task["id"], supplier)
        created = get_task(task["id"])
        if not created:
            raise RuntimeError("Task was not created")
        return created

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        return get_task(task_id)

    def get_events(self, task_id: str) -> list[dict[str, Any]]:
        return list_events(task_id)

    def get_report(self, task_id: str) -> str | None:
        return get_report(task_id)

    def get_evidence(self, task_id: str) -> list[dict[str, Any]]:
        return list_evidence(task_id)
