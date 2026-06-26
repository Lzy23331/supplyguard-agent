import time
from typing import Any

from app.config import get_settings
from app.database import get_db
from app.llm.llm_factory import create_llm_client
from app.services.llm_audit_service import log_llm_call


class LLMReportPolishService:
    name = "LLMReportPolishService"

    SYSTEM_PROMPT = """你是供应商准入尽调报告编辑。请只优化中文表达、段落衔接和专业语气，不得新增事实、不得删除URL、不得改变风险分数、风险等级、任务ID、证据数量、表格结构或章节标题。保留 Markdown 格式。"""

    def polish(self, *, task_id: str, markdown: str, context: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
        settings = get_settings()
        if not settings.enable_llm_report_polish:
            return markdown, {"enabled": False, "used": False, "reason": "disabled"}
        input_limit = max(1000, int(settings.max_report_polish_input_chars or 6000))
        prompt = self._build_prompt(markdown[:input_limit], context or {})
        start = time.perf_counter()
        bundle = create_llm_client()
        if bundle.actual_model_mode == "mock":
            return markdown, {
                "enabled": True,
                "used": False,
                "model_mode": bundle.actual_model_mode,
                "model_name": bundle.model_name,
                "fallback_used": bundle.fallback_used,
                "reason": bundle.fallback_reason or "mock client does not rewrite final report",
            }
        try:
            polished = bundle.client.complete_text(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=prompt,
                task_type="report_polish",
                timeout_seconds=settings.report_polish_timeout_seconds,
            ).strip()
            latency_ms = int((time.perf_counter() - start) * 1000)
            if not self._is_safe_polish(markdown, polished, task_id):
                self._log(task_id, bundle, prompt, polished, False, latency_ms, "unsafe_polish_rejected")
                return markdown, {"enabled": True, "used": False, "reason": "unsafe_polish_rejected", "latency_ms": latency_ms}
            self._log(task_id, bundle, prompt, polished, True, latency_ms, None)
            return polished, {
                "enabled": True,
                "used": True,
                "model_mode": bundle.actual_model_mode,
                "model_name": bundle.model_name,
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            self._log(task_id, bundle, prompt, None, False, latency_ms, str(exc))
            if not settings.llm_fallback_to_mock:
                raise
            return markdown, {"enabled": True, "used": False, "reason": str(exc), "latency_ms": latency_ms}

    def _build_prompt(self, markdown: str, context: dict[str, Any]) -> str:
        return "\n".join([
            "请润色以下供应商尽调 Markdown 报告。",
            "硬性要求：保留全部章节标题、任务ID、URL、分数、风险等级、证据数量和表格；只优化语言流畅度和专业表达。",
            f"上下文：{context}",
            "--- 报告开始 ---",
            markdown,
            "--- 报告结束 ---",
        ])

    def _is_safe_polish(self, original: str, polished: str, task_id: str) -> bool:
        if not polished or len(polished) < len(original) * 0.45:
            return False
        required_fragments = [task_id, "## 1. 基本信息", "## 2. 综合结论", "## 6. 关键证据链"]
        return all(fragment in polished for fragment in required_fragments if fragment)

    def _log(self, task_id: str, bundle, prompt: str, output: str | None, success: bool, latency_ms: int, error_message: str | None) -> None:
        with get_db() as db:
            log_llm_call(
                db,
                task_id,
                "ReportPolishAgent",
                "report_polish",
                bundle.actual_model_mode,
                bundle.model_name,
                "report_polish_prompt",
                prompt[:1200],
                (output or "")[:1200] if output else None,
                success,
                bundle.fallback_used,
                bundle.fallback_reason,
                error_message=error_message,
                latency_ms=latency_ms,
            )