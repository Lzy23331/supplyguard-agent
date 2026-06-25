import json
from typing import Any

SYSTEM_PROMPT = """你是政策检索 query 生成助手。你只能根据 supplier_profile 和 evidence_keywords 生成政策检索 query。
你不能编造政策内容，不能输出风险等级，不能决定准入结论。
输出必须是 JSON，字段必须为 queries。"""


def build_user_prompt(supplier_profile: dict[str, Any], evidence_keywords: list[str]) -> str:
    return json.dumps(
        {"supplier_profile": supplier_profile, "evidence_keywords": evidence_keywords},
        ensure_ascii=False,
    )
