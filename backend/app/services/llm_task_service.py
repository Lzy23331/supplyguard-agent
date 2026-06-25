import json
import time
from typing import Any

from app.config import get_settings
from app.llm.llm_factory import create_llm_client
from app.llm.mock_client import MockLLMClient
from app.llm.prompts.intake_plan_prompt import SYSTEM_PROMPT as INTAKE_SYSTEM_PROMPT
from app.llm.prompts.intake_plan_prompt import build_user_prompt as build_intake_user_prompt
from app.llm.prompts.query_rewrite_prompt import SYSTEM_PROMPT as QUERY_REWRITE_SYSTEM_PROMPT
from app.llm.prompts.query_rewrite_prompt import build_user_prompt as build_query_rewrite_user_prompt
from app.llm.prompts.search_query_plan_prompt import SYSTEM_PROMPT as SEARCH_QUERY_PLAN_SYSTEM_PROMPT
from app.llm.prompts.search_query_plan_prompt import build_user_prompt as build_search_query_plan_user_prompt
from app.llm.schemas.llm_outputs import validate_intake_plan, validate_policy_queries, validate_search_query_plan
from app.services.llm_audit_service import log_llm_call


def _summary(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)[:1000]


def _fallback_allowed() -> bool:
    return bool(get_settings().llm_fallback_to_mock)


def generate_intake_plan(db, task_id: str, supplier_profile: dict[str, Any], agent_name: str = "IntakeAgent") -> dict:
    system_prompt = INTAKE_SYSTEM_PROMPT
    user_prompt = build_intake_user_prompt(supplier_profile)
    start = time.perf_counter()
    bundle = create_llm_client()
    try:
        data = bundle.client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt, task_type="intake_plan")
        plan = validate_intake_plan(data)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_llm_call(
            db,
            task_id,
            agent_name,
            "intake_plan",
            bundle.actual_model_mode,
            bundle.model_name,
            "intake_plan_prompt",
            _summary(supplier_profile),
            _summary(plan),
            True,
            bundle.fallback_used,
            bundle.fallback_reason,
            latency_ms=latency_ms,
        )
        return plan
    except Exception as exc:
        if not _fallback_allowed():
            latency_ms = int((time.perf_counter() - start) * 1000)
            log_llm_call(
                db,
                task_id,
                agent_name,
                "intake_plan",
                bundle.actual_model_mode,
                bundle.model_name,
                "intake_plan_prompt",
                _summary(supplier_profile),
                None,
                False,
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise
        fallback_data = MockLLMClient().complete_json(system_prompt=system_prompt, user_prompt=user_prompt, task_type="intake_plan")
        plan = validate_intake_plan(fallback_data)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_llm_call(
            db,
            task_id,
            agent_name,
            "intake_plan",
            "mock",
            "mock-llm",
            "intake_plan_prompt",
            _summary(supplier_profile),
            _summary(plan),
            True,
            True,
            f"Fallback after LLM failure: {exc}",
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        return plan


def rewrite_policy_queries(
    db,
    task_id: str | None,
    supplier_profile: dict[str, Any],
    evidence_keywords: list[str],
    agent_name: str = "RAGPolicyTool",
) -> list[str]:
    system_prompt = QUERY_REWRITE_SYSTEM_PROMPT
    user_prompt = build_query_rewrite_user_prompt(supplier_profile, evidence_keywords)
    start = time.perf_counter()
    bundle = create_llm_client()
    try:
        data = bundle.client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type="policy_query_rewrite",
        )
        queries = validate_policy_queries(data)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_llm_call(
            db,
            task_id,
            agent_name,
            "policy_query_rewrite",
            bundle.actual_model_mode,
            bundle.model_name,
            "query_rewrite_prompt",
            _summary({"supplier_profile": supplier_profile, "evidence_keywords": evidence_keywords}),
            _summary({"queries": queries}),
            True,
            bundle.fallback_used,
            bundle.fallback_reason,
            latency_ms=latency_ms,
        )
        return queries
    except Exception as exc:
        if not _fallback_allowed():
            latency_ms = int((time.perf_counter() - start) * 1000)
            log_llm_call(
                db,
                task_id,
                agent_name,
                "policy_query_rewrite",
                bundle.actual_model_mode,
                bundle.model_name,
                "query_rewrite_prompt",
                _summary({"supplier_profile": supplier_profile, "evidence_keywords": evidence_keywords}),
                None,
                False,
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise
        fallback_data = MockLLMClient().complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type="policy_query_rewrite",
        )
        queries = validate_policy_queries(fallback_data)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_llm_call(
            db,
            task_id,
            agent_name,
            "policy_query_rewrite",
            "mock",
            "mock-llm",
            "query_rewrite_prompt",
            _summary({"supplier_profile": supplier_profile, "evidence_keywords": evidence_keywords}),
            _summary({"queries": queries}),
            True,
            True,
            f"Fallback after LLM failure: {exc}",
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        return queries


def generate_search_query_plan(
    db,
    task_id: str | None,
    supplier_profile: dict[str, Any],
    agent_name: str = "SearchQueryPlannerAgent",
) -> list[dict[str, str]]:
    system_prompt = SEARCH_QUERY_PLAN_SYSTEM_PROMPT
    user_prompt = build_search_query_plan_user_prompt(supplier_profile)
    company_name = supplier_profile.get("company_name") or supplier_profile.get("name") or ""
    start = time.perf_counter()
    bundle = create_llm_client()
    try:
        data = bundle.client.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type="search_query_plan",
        )
        queries = validate_search_query_plan(data, company_name)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_llm_call(
            db,
            task_id,
            agent_name,
            "search_query_plan",
            bundle.actual_model_mode,
            bundle.model_name,
            "search_query_plan_prompt",
            _summary(supplier_profile),
            _summary({"queries": queries}),
            True,
            bundle.fallback_used,
            bundle.fallback_reason,
            latency_ms=latency_ms,
        )
        return queries
    except Exception as exc:
        if not _fallback_allowed():
            latency_ms = int((time.perf_counter() - start) * 1000)
            log_llm_call(
                db,
                task_id,
                agent_name,
                "search_query_plan",
                bundle.actual_model_mode,
                bundle.model_name,
                "search_query_plan_prompt",
                _summary(supplier_profile),
                None,
                False,
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise
        fallback_data = MockLLMClient().complete_json(system_prompt=system_prompt, user_prompt=user_prompt, task_type="search_query_plan")
        queries = validate_search_query_plan(fallback_data, company_name)
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_llm_call(
            db,
            task_id,
            agent_name,
            "search_query_plan",
            "mock",
            "mock-llm",
            "search_query_plan_prompt",
            _summary(supplier_profile),
            _summary({"queries": queries}),
            True,
            True,
            f"Fallback after LLM failure: {exc}",
            error_message=str(exc),
            latency_ms=latency_ms,
        )
        return queries
