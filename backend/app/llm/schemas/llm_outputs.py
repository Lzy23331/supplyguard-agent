from pydantic import BaseModel, Field, field_validator

from app.llm.base import LLMOutputValidationError


def _clean_list(items: list[object], *, maximum: int | None = None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if value and value not in seen:
            seen.add(value)
            cleaned.append(value)
    return cleaned[:maximum] if maximum else cleaned


class IntakePlanOutput(BaseModel):
    focus_areas: list[str]
    suggested_tools: list[str]
    risk_hypotheses: list[str]
    questions_for_review: list[str]

    @field_validator("focus_areas", "suggested_tools", "risk_hypotheses", "questions_for_review")
    @classmethod
    def non_empty_string_list(cls, value: list[object]) -> list[str]:
        cleaned = _clean_list(value)
        if not cleaned:
            raise ValueError("field must contain at least one string")
        return cleaned


class PolicyQueryRewriteOutput(BaseModel):
    queries: list[str] = Field(default_factory=list)

    @field_validator("queries")
    @classmethod
    def clean_queries(cls, value: list[object]) -> list[str]:
        return _clean_list(value, maximum=6)


def validate_intake_plan(data: dict) -> dict:
    try:
        return IntakePlanOutput.model_validate(data).model_dump()
    except Exception as exc:
        raise LLMOutputValidationError(f"Invalid intake_plan output: {exc}") from exc


def validate_policy_queries(data: dict) -> list[str]:
    try:
        output = PolicyQueryRewriteOutput.model_validate(data)
    except Exception as exc:
        raise LLMOutputValidationError(f"Invalid policy_query_rewrite output: {exc}") from exc
    if len(output.queries) < 3:
        raise LLMOutputValidationError("policy_query_rewrite output must contain at least 3 queries")
    return output.queries[:6]


class SearchQueryItem(BaseModel):
    query: str
    purpose: str = "due_diligence"


class SearchQueryPlanOutput(BaseModel):
    queries: list[SearchQueryItem] = Field(default_factory=list)

    @field_validator("queries")
    @classmethod
    def clean_query_items(cls, value: list[object]) -> list[SearchQueryItem]:
        cleaned: list[SearchQueryItem] = []
        seen: set[str] = set()
        for item in value:
            try:
                query_item = SearchQueryItem.model_validate(item)
            except Exception:
                continue
            query = query_item.query.strip()
            if query and query not in seen:
                seen.add(query)
                cleaned.append(SearchQueryItem(query=query, purpose=query_item.purpose.strip() or "due_diligence"))
        return cleaned[:8]


def validate_search_query_plan(data: dict, company_name: str) -> list[dict[str, str]]:
    try:
        output = SearchQueryPlanOutput.model_validate(data)
    except Exception as exc:
        raise LLMOutputValidationError(f"Invalid search_query_plan output: {exc}") from exc
    items = []
    seen: set[str] = set()
    for item in output.queries:
        query = item.query.strip()
        if company_name not in query:
            query = f"{company_name} {query}"
        if query not in seen:
            seen.add(query)
            items.append({"query": query, "purpose": item.purpose})
    if len(items) < 5:
        raise LLMOutputValidationError("search_query_plan output must contain at least 5 queries")
    return items[:8]
