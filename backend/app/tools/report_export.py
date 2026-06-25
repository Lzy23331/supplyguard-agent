from typing import Any

from app.services.evidence_scoring_service import EvidenceScoringService


class ReportExportTool:
    name = "ReportExportTool"
    LEVEL_LABELS = {"low": "低风险", "medium": "中风险", "high": "高风险"}
    DIMENSION_LABELS = {
        "compliance": "合规风险",
        "business": "经营风险",
        "delivery": "交付风险",
        "completeness": "资料完整性",
        "reputation": "声誉风险",
    }
    SEVERITY_LABELS = {"info": "信息", "warning": "预警", "critical": "严重"}

    def __init__(self) -> None:
        self.evidence_scoring = EvidenceScoringService()

    def _dimension_table(self, risk: dict[str, Any]) -> str:
        lines = ["| 风险维度 | 分数 | 等级 | 判断依据 |", "| --- | ---: | --- | --- |"]
        for item in risk.get("dimensions", []):
            lines.append(
                f"| {self.DIMENSION_LABELS.get(item.get('dimension'), item.get('dimension'))} "
                f"| {item.get('score')} | {self.LEVEL_LABELS.get(item.get('level'), item.get('level'))} "
                f"| {item.get('rationale')} |"
            )
        return "\n".join(lines)

    def _triggered_rules(self, risk: dict[str, Any]) -> str:
        rules = risk.get("triggered_rules") or risk.get("hit_rules") or []
        if not rules:
            return "- 未命中加分规则。"
        lines = []
        for item in rules:
            rule_name = item.get("rule_name") or item.get("rule")
            score = item.get("score") or item.get("points")
            dimension = self.DIMENSION_LABELS.get(item.get("dimension"), item.get("dimension"))
            evidence = item.get("evidence_ids") or item.get("evidence_source") or item.get("reason")
            lines.append(f"- `{item.get('rule_id', rule_name)}` {rule_name}（{dimension}，{score}）：证据来源 {evidence}")
        return "\n".join(lines)

    def _keyword_text(self, item: dict[str, Any]) -> str:
        keywords = item.get("risk_keywords") or item.get("matched_risk_keywords") or (item.get("metadata_json") or {}).get("risk_keywords") or []
        if isinstance(keywords, str):
            keywords = [keywords]
        if not keywords or keywords == ["search_observation"]:
            return "无明显风险 / 普通搜索记录"
        return " / ".join(str(k) for k in keywords)

    def _scoring_text(self, item: dict[str, Any]) -> str:
        if item.get("source_type") == "web_search" or item.get("decision") or item.get("source_name") == "腾讯云联网搜索":
            metadata = item.get("metadata_json") or {}
            normalized = {
                **item,
                "source_type": item.get("source_type") or "web_search",
                "source_url": item.get("source_url") or item.get("url"),
                "content": item.get("content") or item.get("snippet") or "",
                "risk_keywords": item.get("risk_keywords") or item.get("matched_risk_keywords") or [],
                "metadata_json": {
                    **metadata,
                    "entity_match_score": item.get("entity_match_score", metadata.get("entity_match_score")),
                    "confidence": item.get("confidence", metadata.get("confidence")),
                    "should_use_for_scoring": item.get("should_use_for_scoring", metadata.get("should_use_for_scoring")),
                },
            }
            should_score, _ = self.evidence_scoring.should_score(normalized)
            return "是" if should_score else "否"
        scoring_value = item.get("should_use_for_scoring")
        if scoring_value is None:
            scoring_value = (item.get("metadata_json") or {}).get("should_use_for_scoring")
        return "是" if scoring_value in (True, 1, "1") else "否"

    def _is_scoring_web_search(self, item: dict[str, Any]) -> bool:
        if item.get("decision") != "score_evidence" and self._scoring_text(item) != "是":
            return False
        normalized = {
            **item,
            "source_type": item.get("source_type") or "web_search",
            "source_url": item.get("source_url") or item.get("url"),
            "content": item.get("content") or item.get("snippet") or "",
            "risk_keywords": item.get("risk_keywords") or item.get("matched_risk_keywords") or [],
            "metadata_json": {
                **(item.get("metadata_json") or {}),
                "entity_match_score": item.get("entity_match_score", (item.get("metadata_json") or {}).get("entity_match_score")),
                "should_use_for_scoring": item.get("decision") == "score_evidence" or (item.get("metadata_json") or {}).get("should_use_for_scoring"),
            },
        }
        should_score, _ = self.evidence_scoring.should_score(normalized)
        return should_score

    def _not_scoring_reason(self, item: dict[str, Any]) -> str:
        if item.get("decision") == "exclude":
            return item.get("excluded_reason") or item.get("decision_reason") or "已被质量评估排除"
        normalized = {
            **item,
            "source_type": item.get("source_type") or "web_search",
            "source_url": item.get("source_url") or item.get("url"),
            "content": item.get("content") or item.get("snippet") or "",
            "risk_keywords": item.get("risk_keywords") or item.get("matched_risk_keywords") or [],
            "metadata_json": {
                **(item.get("metadata_json") or {}),
                "entity_match_score": item.get("entity_match_score", (item.get("metadata_json") or {}).get("entity_match_score")),
                "should_use_for_scoring": item.get("decision") == "score_evidence" or (item.get("metadata_json") or {}).get("should_use_for_scoring"),
            },
        }
        should_score, reason = self.evidence_scoring.should_score(normalized)
        if should_score:
            return item.get("decision_reason") or "达到评分阈值"
        reason_map = {
            "observation_or_no_obvious_risk": "未发现明确风险或仅为普通观察记录",
            "missing_source_url": "缺少真实 URL",
            "entity_match_below_threshold": "主体匹配度未达到评分阈值",
            "confidence_below_threshold": "置信度未达到评分阈值",
            "no_risk_signal": "未命中明确风险关键词",
            "no_structured_risk_signal": "未提供结构化风险信号",
            "explicitly_not_for_scoring": "已标记为不参与评分",
        }
        return item.get("decision_reason") or reason_map.get(reason, reason)

    def _query_count(self, rows: list[dict[str, Any]], search_queries: list[dict[str, Any]] | None = None) -> int:
        queries = {row.get("query") for row in rows if row.get("query")}
        for item in search_queries or []:
            if isinstance(item, dict) and item.get("query"):
                queries.add(item["query"])
        return len(queries)

    def _evidence_lines(self, evidence: list[dict[str, Any]]) -> str:
        if not evidence:
            return "- 暂无证据。"
        lines = []
        for item in evidence:
            source_type = item.get("source_type") or ("mock_sample" if item.get("source") else "unknown")
            if source_type == "web_search":
                lines.append("\n".join([
                    "- 来源：腾讯云联网搜索",
                    f"  - 标题：{item.get('title')}",
                    f"  - URL：{item.get('source_url') or item.get('url') or '见联网搜索普通记录'}",
                    f"  - 摘要：{item.get('content') or item.get('snippet')}",
                    f"  - 风险关键词：{self._keyword_text(item)}",
                    f"  - 是否参与评分：{self._scoring_text(item)}",
                    f"  - 置信度：{item.get('confidence'):.2f}" if isinstance(item.get("confidence"), (int, float)) else "  - 置信度：未提供",
                ]))
                continue
            source_label = {
                "mock_sample": "模拟公开信息",
                "user_input": "用户输入材料",
                "uploaded_file": "上传文件",
                "mock_external": "模拟外部数据",
                "real_external": "真实外部数据",
                "external_api": "真实外部数据",
                "internal_record": "内部记录",
            }.get(source_type, source_type)
            quote = item.get("raw_text") or item.get("source_quote")
            quote_text = f"\n  - 原文摘录：{quote}" if quote else ""
            confidence = item.get("confidence")
            confidence_text = f"，置信度 {confidence:.2f}" if isinstance(confidence, (int, float)) else ""
            lines.append(
                f"- **{item.get('title')}** [{self.SEVERITY_LABELS.get(item.get('severity', 'info'), item.get('severity', 'info'))}]"
                f"（来源：{source_label}{confidence_text}）：{item.get('content')}{quote_text}"
            )
        return "\n".join(lines)

    def _web_rows_or_evidence(self, web_search_results: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if web_search_results:
            return web_search_results
        return [item for item in evidence if item.get("source_type") == "web_search"]

    def _web_search_coverage(self, rows: list[dict[str, Any]], search_queries: list[dict[str, Any]] | None = None) -> str:
        if not rows:
            return "\n".join([
                "- 搜索 Provider：腾讯云联网搜索",
                "- Provider 模式：未产生 web_search 搜索记录",
                f"- 搜索 query 数：{self._query_count(rows, search_queries)}",
                "- 保留搜索记录：0",
                "- 可评分风险证据：0",
                "- 普通展示记录：0",
                "- 排除记录：0",
            ])
        queries = {row.get("query") for row in rows if row.get("query")}
        for query_item in search_queries or []:
            if isinstance(query_item, dict) and query_item.get("query"):
                queries.add(query_item["query"])
        score_count = sum(1 for row in rows if self._is_scoring_web_search(row))
        display_count = sum(1 for row in rows if row.get("decision") == "display_only")
        exclude_count = sum(1 for row in rows if row.get("decision") == "exclude")
        provider_mode = next(((row.get("metadata_json") or {}).get("provider_mode") for row in rows if (row.get("metadata_json") or {}).get("provider_mode")), "real")
        return "\n".join([
            "- 搜索 Provider：腾讯云联网搜索",
            f"- Provider 模式：{provider_mode}",
            f"- 搜索 query 数：{len(queries)}",
            f"- 保留搜索记录：{len(rows)}",
            f"- 可评分风险证据：{score_count}",
            f"- 普通展示记录：{display_count}",
            f"- 被排除结果：{exclude_count}",
        ])

    def _scoring_web_search_lines(self, rows: list[dict[str, Any]]) -> str:
        items = [row for row in rows if self._is_scoring_web_search(row)]
        if not items:
            return "- 未发现可评分的明确风险证据。"
        lines = []
        for item in items:
            meta = item.get("metadata_json") or {}
            lines.append("\n".join([
                "- 来源：腾讯云联网搜索",
                f"  - 标题：{item.get('title')}",
                f"  - URL：{item.get('url') or item.get('source_url') or '未提供'}",
                f"  - 摘要：{item.get('snippet') or item.get('content')}",
                f"  - 风险关键词：{self._keyword_text(item)}",
                f"  - 主体匹配度：{item.get('entity_match_score'):.2f}" if isinstance(item.get("entity_match_score"), (int, float)) else "  - 主体匹配度：未记录",
                f"  - 来源可信度：{item.get('domain_trust_score'):.2f}" if isinstance(item.get("domain_trust_score"), (int, float)) else "  - 来源可信度：未记录",
                f"  - 参与评分原因：{item.get('decision_reason') or meta.get('decision_reason') or '达到评分阈值'}",
            ]))
        return "\n".join(lines)

    def _ordinary_web_search_lines(self, rows: list[dict[str, Any]], limit: int = 5) -> str:
        items = [row for row in rows if not self._is_scoring_web_search(row)]
        items = sorted(items, key=lambda row: (0 if row.get("url") or row.get("source_url") else 1, row.get("rank") or 999))
        if not items:
            return "- 无普通展示记录。"
        lines = []
        for index, item in enumerate(items[:limit], start=1):
            entity = item.get("entity_match_score")
            trust = item.get("domain_trust_score")
            lines.append("\n".join([
                f"{index}. 标题：{item.get('title')}",
                f"   URL：{item.get('url') or item.get('source_url') or '未提供'}",
                f"   摘要：{item.get('snippet') or item.get('content')}",
                f"   query：{item.get('query') or '未记录'}",
                f"   主体匹配度：{entity:.2f}" if isinstance(entity, (int, float)) else "   主体匹配度：未记录",
                f"   来源可信度：{trust:.2f}" if isinstance(trust, (int, float)) else "   来源可信度：未记录",
                f"   是否参与评分：{'是' if self._is_scoring_web_search(item) else '否'}",
                f"   不参与评分原因：{self._not_scoring_reason(item)}",
                f"   风险关键词：{self._keyword_text(item)}",
            ]))
        return "\n".join(lines)

    def _excluded_web_search_lines(self, rows: list[dict[str, Any]]) -> str:
        excluded = [row for row in rows if row.get("decision") == "exclude"]
        if not excluded:
            return "- 无被排除结果。"
        counts: dict[str, int] = {}
        for row in excluded:
            reason = row.get("excluded_reason") or row.get("decision_reason") or "unknown"
            counts[reason] = counts.get(reason, 0) + 1
        return "\n".join(f"- {reason}：{count} 条" for reason, count in counts.items())

    def _company_profile_lines(self, company_profile: list[dict[str, Any]]) -> str:
        if not company_profile:
            return "- 未从联网搜索摘要中抽取到可展示的企业基础信息；建议人工核验工商登记信息。"
        label_map = {
            "company_full_name": "企业名称",
            "website": "官网",
            "industry": "行业",
            "region": "地区",
            "unified_social_credit_code": "统一社会信用代码",
            "registered_capital": "注册资本",
            "established_date": "成立时间",
            "legal_representative": "法定代表人",
            "registered_address": "注册地址",
            "business_scope": "经营范围",
            "business_status": "经营状态",
        }
        lines = ["| 字段 | 值 | 置信度 | 来源 URL | 说明 |", "| --- | --- | ---: | --- | --- |"]
        for item in company_profile:
            confidence = item.get("confidence")
            confidence_text = f"{confidence:.2f}" if isinstance(confidence, (int, float)) else "未记录"
            source_url = item.get("source_url") or "未提供"
            note = item.get("reason") or "搜索摘要推断，需人工复核"
            lines.append(f"| {label_map.get(item.get('field_name'), item.get('field_name'))} | {item.get('field_value') or '未抽取'} | {confidence_text} | {source_url} | {note} |")
        lines.append("\n注：以上企业画像字段来自联网搜索标题、摘要和 URL 的结构化推断，不等同官方工商核验，必须保留人工复核。")
        return "\n".join(lines)
    def _risk_basis_lines(self, evidence: list[dict[str, Any]], web_rows: list[dict[str, Any]], risk: dict[str, Any]) -> str:
        actual_rules = [rule for rule in (risk.get("triggered_rules") or []) if rule.get("actual_risk")]
        info_rules = [rule for rule in (risk.get("triggered_rules") or []) if not rule.get("actual_risk")]
        scoring_web = [row for row in web_rows if self._is_scoring_web_search(row)]
        observation_web = [row for row in web_rows if row.get("decision") == "display_only"]
        lines = [
            f"- 实际风险规则命中：{len(actual_rules)} 条。",
            f"- 信息完整性/采购暴露类规则命中：{len(info_rules)} 条。",
            f"- 联网搜索可评分风险证据：{len(scoring_web)} 条。",
            f"- 联网搜索普通观察记录：{len(observation_web)} 条，仅展示，不参与评分。",
        ]
        if not actual_rules:
            lines.append("- 本次未发现制裁、失信、行政处罚、重大诉讼等明确高风险证据；评分主要反映信息完整性、采购金额暴露或人工复核需求。")
        else:
            lines.append("- 实际风险证据已按 URL、主体匹配、风险关键词和置信度过滤后参与评分。")
        lines.append("- 企业画像字段来自搜索摘要推断，不等同官方工商核验；关键结论仍需人工复核。")
        return "\n".join(lines)
    def _policy_lines(self, policies: list[dict[str, Any]]) -> str:
        if not policies:
            return "- 未检索到明确政策片段，建议人工复核政策库。"
        lines = []
        for item in policies:
            doc = item.get("doc_name") or item.get("document")
            section = item.get("section_title") or "相关条款"
            keywords = "、".join(item.get("matched_keywords") or item.get("keywords") or [])
            content = (item.get("content") or item.get("chunk") or "").strip().replace("\n", " ")
            excerpt = content[:220] + ("..." if len(content) > 220 else "")
            lines.append(f"- **{doc} / {section}**（关键词：{keywords or '无'}）：{excerpt}")
        return "\n".join(lines)

    def build_markdown(
        self,
        supplier: dict[str, Any],
        evidence: list[dict[str, Any]],
        risk: dict[str, Any],
        policies: list[dict[str, Any]],
        compliance_summary: dict[str, Any] | None = None,
        business_summary: dict[str, Any] | None = None,
        plan: dict[str, Any] | None = None,
        web_search_results: list[dict[str, Any]] | None = None,
        company_profile: list[dict[str, Any]] | None = None,
        search_queries: list[dict[str, Any]] | None = None,
        task_id: str | None = None,
    ) -> str:
        web_rows = self._web_rows_or_evidence(web_search_results or [], evidence)
        risk_level = self.LEVEL_LABELS.get(risk.get("risk_level"), risk.get("risk_level"))
        raw_score = risk.get("raw_score", risk.get("total_score"))
        total_score = risk.get("total_score")
        cap_note = ""
        if raw_score is not None and total_score is not None and raw_score > total_score:
            cap_note = f"\n\n该供应商原始累计风险分为 **{raw_score}**，超过评分上限，系统按规则将总分截断为 **{total_score} / 100**。"
        checks = "、".join((plan or {}).get("checks", [])) or "标准供应商准入尽调"
        compliance_rules = compliance_summary.get("key_rules", []) if compliance_summary else []
        business_rules = business_summary.get("triggered_rules", []) if business_summary else []

        if supplier.get("query_type") == "company_name" or supplier.get("company_name"):
            source_types = {item.get("source_type") for item in evidence}
            if web_rows:
                task_type = "真实企业名称查询任务（使用腾讯云联网搜索真实公开网页结果）"
            elif "mock_external" in source_types:
                task_type = "真实企业名称查询任务（腾讯云联网搜索不可用，已 fallback 到 mock provider）"
            else:
                task_type = "真实企业名称查询任务（外部 Provider 未返回有效证据，需人工复核）"
        else:
            task_type = "样例供应商快速演示任务" if supplier.get("sample_key") else "自定义供应商输入任务"

        return f"""# 供应商准入尽调报告
## 1. 基本信息
- 任务 ID：{task_id or supplier.get('task_id') or '未提供'}
- 供应商名称：**{supplier.get('name')}**
- 任务类型：{task_type}
- 官网：{supplier.get('website') or '未提供'}
- 行业：{supplier.get('industry') or '未提供'}
- 地区：{supplier.get('region') or '未提供'}
- 年采购金额：{supplier.get('annual_spend')}
- 合作类型：{supplier.get('cooperation_type') or '未提供'}
- 尽调范围：{checks}

## 2. 综合结论
- 内部风险等级：**{risk.get('risk_level')}**（前端展示：{risk_level}）
- 综合评分：**{total_score} / 100**
- 准入建议：**{risk.get('recommendation')}**{cap_note}

## 3. 风险评分
{self._dimension_table(risk)}

### 评分依据来源类型
{self._risk_basis_lines(evidence, web_rows, risk)}

命中规则：
{self._triggered_rules(risk)}

## 4. 合规风险分析
合规风险重点来自制裁名单、黑名单、出口管制、受益所有人透明度、行政处罚、商业贿赂或欺诈等信号。本次命中合规规则 {len(compliance_rules)} 条，需结合政策片段和证据链判断是否准入、升级审批或拒绝准入。

## 5. 经营与交付风险分析
经营与交付风险重点来自采购暴露、交付延期、合同争议、付款纠纷、资料缺失和补充材料情况。本次命中经营交付类规则 {len(business_rules)} 条，需判断供应商是否具备稳定履约能力。

## 6. 关键证据链
### 企业基础信息补全
{self._company_profile_lines(company_profile or [])}

### 联网搜索覆盖情况
{self._web_search_coverage(web_rows, search_queries)}

### 可评分风险证据
{self._scoring_web_search_lines(web_rows)}

### 联网搜索普通记录
{self._ordinary_web_search_lines(web_rows)}

### 被排除结果摘要
{self._excluded_web_search_lines(web_rows)}

### 全部任务证据（含不参与评分）
{self._evidence_lines(evidence)}

说明：用户材料证据仅基于用户主动提供内容；联网搜索结果来自公开网页标题、摘要和 URL，不等同官方工商核验，关键结论需人工复核；普通联网搜索记录仅用于展示覆盖情况，不进入规则评分；最终风险等级和准入建议由规则引擎基于可评分证据链统一计算。

## 7. 命中政策依据
{self._policy_lines(policies)}

## 8. 准入建议
{risk.get('recommendation')}

## 9. 人工复核建议
- low：资料完整且未发现关键风险时，可按标准准入并纳入年度复查。
- medium：建议补充材料，必要时由采购、法务或合规进行人工复核。
- high：建议拒绝准入或提交升级审批，并保留完整证据链与政策依据。
"""













