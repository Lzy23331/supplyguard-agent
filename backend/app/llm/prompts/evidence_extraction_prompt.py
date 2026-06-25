import json
from typing import Any

SYSTEM_PROMPT = """你是供应商准入尽调证据抽取助手。
只能基于用户提供的 material_text 抽取风险证据，不得编造材料中没有的风险。
每条证据必须包含 source_quote。如果没有风险，返回 {"evidence_items": []}。
不能输出最终风险等级，不能输出最终风险分数。输出必须是 JSON。"""


def build_user_prompt(supplier_profile: dict[str, Any], material_text: str) -> str:
    return json.dumps(
        {"supplier_profile": supplier_profile, "material_text": material_text},
        ensure_ascii=False,
    )
