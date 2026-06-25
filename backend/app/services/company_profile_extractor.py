from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlparse

from app.config import get_settings
from app.database import get_db
from app.services.llm_audit_service import log_llm_call


class CompanyProfileExtractor:
    name = "CompanyProfileExtractor"
    PROFILE_FIELDS = [
        "company_full_name",
        "website",
        "industry",
        "region",
        "unified_social_credit_code",
        "registered_capital",
        "established_date",
        "legal_representative",
        "registered_address",
        "business_scope",
        "business_status",
    ]
    INDUSTRY_HINTS = [
        ("汽车", "汽车制造 / 新能源汽车"),
        ("新能源", "新能源"),
        ("通讯", "通信设备 / 通讯技术"),
        ("电子元器件", "电子元器件"),
        ("半导体", "半导体"),
        ("软件", "软件和信息技术服务"),
        ("贸易", "贸易"),
        ("医药", "医药"),
        ("物流", "物流运输"),
    ]
    REGION_PATTERN = re.compile(r"(北京市|上海市|天津市|重庆市|广东省|浙江省|江苏省|山东省|四川省|湖北省|湖南省|福建省|安徽省|河南省|河北省|陕西省|深圳市|广州市|杭州市|南京市|苏州市|成都市|武汉市|西安市)")
    CREDIT_CODE_PATTERN = re.compile(r"[0-9A-Z]{18}")

    def extract(self, *, task_id: str, company_name: str, search_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        candidates = self._candidate_results(search_results)
        fields: dict[str, dict[str, Any]] = {}
        for row in candidates[:8]:
            self._merge(fields, self._extract_from_row(row, company_name))
        self._ensure_minimal_company_name(fields, company_name, candidates)
        rows = self._complete_missing_fields(fields, company_name, candidates)
        self._log_llm_fallback(task_id, company_name, candidates, rows)
        return rows

    def _candidate_results(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        usable = [row for row in rows if row.get("url") and not row.get("is_duplicate") and row.get("decision") != "exclude"]
        return sorted(
            usable,
            key=lambda row: (
                row.get("entity_match_score") or 0,
                row.get("domain_trust_score") or 0,
                1 if row.get("decision") == "display_only" else 0,
                -(row.get("rank") or 99),
            ),
            reverse=True,
        )

    def _extract_from_row(self, row: dict[str, Any], company_name: str) -> dict[str, dict[str, Any]]:
        text = " ".join(str(row.get(key) or "") for key in ["title", "snippet", "url", "query"])
        url = row.get("url")
        query = row.get("query")
        base_conf = min(0.92, max(0.45, 0.55 * float(row.get("entity_match_score") or 0) + 0.45 * float(row.get("domain_trust_score") or 0)))
        result: dict[str, dict[str, Any]] = {}

        if company_name and company_name in text:
            result["company_full_name"] = self._field("company_full_name", company_name, max(0.75, base_conf), url, query, "搜索结果命中完整企业名称")
        credit = self._first(self.CREDIT_CODE_PATTERN.findall(text))
        if credit:
            result["unified_social_credit_code"] = self._field("unified_social_credit_code", credit, 0.82, url, query, "标题或摘要包含统一社会信用代码")
        for marker, field in [("注册资本", "registered_capital"), ("成立日期", "established_date"), ("成立时间", "established_date"), ("法定代表人", "legal_representative"), ("注册地址", "registered_address"), ("经营范围", "business_scope")]:
            value = self._after_marker(text, marker)
            if value:
                result[field] = self._field(field, value, min(0.78, base_conf + 0.08), url, query, f"摘要包含{marker}")
        status = self._business_status(text, row)
        if status:
            result["business_status"] = self._field("business_status", status, min(0.75, base_conf + 0.05), url, query, "摘要包含经营状态关键词")
        region = self._region(text)
        if region:
            result["region"] = self._field("region", region, min(0.72, base_conf + 0.05), url, query, "标题或摘要包含地区信息")
        industry = self._industry(text)
        if industry:
            result["industry"] = self._field("industry", industry, min(0.72, base_conf + 0.05), url, query, "标题或摘要包含行业关键词")
        website = self._website(row, text, company_name)
        if website:
            result["website"] = self._field("website", website, min(0.7, base_conf + 0.05), url, query, "搜索结果疑似企业官网或主体网站")
        return result

    def _complete_missing_fields(self, fields: dict[str, dict[str, Any]], company_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        source = rows[0] if rows else {}
        completed: list[dict[str, Any]] = []
        for name in self.PROFILE_FIELDS:
            if name in fields:
                completed.append(fields[name])
                continue
            completed.append(
                {
                    "field_name": name,
                    "field_value": None,
                    "confidence": 0.0,
                    "source_type": "web_search_profile",
                    "source_name": "腾讯云联网搜索",
                    "source_url": source.get("url"),
                    "query": source.get("query"),
                    "extraction_method": "rule_fallback",
                    "requires_manual_verification": True,
                    "reason": "未能从联网搜索标题、摘要、URL 或 query 中可靠抽取该字段",
                    "metadata_json": {"manual_verification_note": "字段缺失，不代表企业存在实际风险；建议人工核验工商登记信息"},
                }
            )
        return completed
    def _field(self, name: str, value: str, confidence: float, url: str | None, query: str | None, reason: str) -> dict[str, Any]:
        return {
            "field_name": name,
            "field_value": value.strip()[:500],
            "confidence": round(float(confidence), 2),
            "source_type": "web_search_profile",
            "source_name": "腾讯云联网搜索",
            "source_url": url,
            "query": query,
            "extraction_method": "rule_fallback",
            "requires_manual_verification": True,
            "reason": reason,
            "metadata_json": {"manual_verification_note": "搜索摘要推断，不等同官方工商核验"},
        }

    def _merge(self, fields: dict[str, dict[str, Any]], extracted: dict[str, dict[str, Any]]) -> None:
        for key, value in extracted.items():
            if key not in fields or (value.get("confidence") or 0) > (fields[key].get("confidence") or 0):
                fields[key] = value

    def _ensure_minimal_company_name(self, fields: dict[str, dict[str, Any]], company_name: str, rows: list[dict[str, Any]]) -> None:
        if "company_full_name" not in fields and company_name:
            source = rows[0] if rows else {}
            fields["company_full_name"] = self._field("company_full_name", company_name, 0.6 if rows else 0.4, source.get("url"), source.get("query"), "由任务输入企业名称生成，需人工确认")

    def _website(self, row: dict[str, Any], text: str, company_name: str) -> str | None:
        url = row.get("url")
        if not url:
            return None
        domain = urlparse(url).netloc.lower().removeprefix("www.")
        low_value_sites = ("qcc.com", "tianyancha.com", "aiqicha.baidu.com", "creditchina.gov.cn", "court.gov.cn", "qq.com", "163.com", "sina.com.cn")
        if any(site in domain for site in low_value_sites):
            return None
        if "官网" in text or "官方网站" in text or (company_name[:2] and company_name[:2].lower() in domain):
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else url
        return None

    def _after_marker(self, text: str, marker: str) -> str | None:
        pattern = re.compile(re.escape(marker) + r"[:：\s]*([^，。；;|]{2,80})")
        match = pattern.search(text)
        return match.group(1).strip() if match else None

    def _business_status(self, text: str, row: dict[str, Any]) -> str | None:
        negation_terms = ["未被列入", "一切正常", "生产经营一切正常", "非制裁名单", "不影响公司正常业务", "回应", "澄清"]
        if any(term in text for term in negation_terms):
            return None
        for status in ["存续", "在业", "开业", "正常"]:
            if status in text:
                return status
        for status in ["迁出", "注销", "吊销", "经营异常"]:
            if status in text:
                if row.get("decision") != "score_evidence":
                    return None
                if (row.get("entity_match_score") or 0) < 0.65 or (row.get("domain_trust_score") or 0) < 0.65:
                    return None
                if row.get("entity_relation_type") not in {None, "exact_target", "likely_target"}:
                    return None
                return status
        return None

    def _region(self, text: str) -> str | None:
        match = self.REGION_PATTERN.search(text)
        return match.group(1) if match else None

    def _industry(self, text: str) -> str | None:
        for keyword, label in self.INDUSTRY_HINTS:
            if keyword in text:
                return label
        return None

    def _first(self, values: list[str]) -> str | None:
        return values[0] if values else None

    def _hash_results(self, company_name: str, rows: list[dict[str, Any]]) -> str:
        payload = company_name + "|" + "|".join(f"{r.get('title')}|{r.get('snippet')}|{r.get('url')}" for r in rows[:8])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _log_llm_fallback(self, task_id: str, company_name: str, rows: list[dict[str, Any]], extracted: list[dict[str, Any]]) -> None:
        settings = get_settings()
        result_hash = self._hash_results(company_name, rows)
        with get_db() as conn:
            log_llm_call(
                conn,
                task_id=task_id,
                agent_name="CompanyProfileExtractionAgent",
                llm_task_type="company_profile_extraction",
                model_mode=settings.model_mode,
                model_name=settings.openai_model,
                prompt_name="company_profile_rule_fallback_v1",
                input_summary=f"company={company_name}; search_result_hash={result_hash}; candidates={len(rows[:8])}",
                output_summary=f"rule_fields={len(extracted)}; fields={[item.get('field_name') for item in extracted]}",
                success=True,
                fallback_used=True,
                fallback_reason="规则抽取优先；当前未启用画像 LLM 批量抽取，避免额外 token/API 消耗。",
                error_message=None,
                latency_ms=None,
            )


