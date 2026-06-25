from app.agents.base import AgentContext, BaseAgent
from app.services.file_service import get_parsed_text
from app.tools.evidence_extraction_tool import EvidenceExtractionTool
from app.tools.evidence_store import EvidenceStoreTool


class MaterialAnalysisAgent(BaseAgent):
    name = "MaterialAnalysisAgent"

    def __init__(self) -> None:
        self.extract_tool = EvidenceExtractionTool()
        self.store_tool = EvidenceStoreTool()

    def run(self, context: AgentContext) -> AgentContext:
        try:
            supplier = context["supplier"]
            material_text = (supplier.get("material_text") or context.get("material_text") or "").strip()
            upload_ids = supplier.get("upload_ids") or context.get("upload_ids") or []
            if not material_text and not upload_ids:
                self.event(
                    context["task_id"],
                    "agent_skipped",
                    "completed",
                    "未提供用户材料，跳过材料分析。",
                )
                return context

            self.started(context, "开始分析用户粘贴材料并抽取风险证据。")
            evidence = []
            if material_text:
                evidence.extend(self.extract_tool.extract_evidence_from_text(
                    supplier_profile=supplier,
                    material_text=material_text,
                    task_id=context["task_id"],
                    source_type="user_input",
                    source_name="用户粘贴材料",
                ))
            self.tool_called(
                context,
                self.extract_tool.name,
                {"material_length": len(material_text), "supplier_id": supplier.get("id")},
                f"已从用户材料抽取 {len(evidence)} 条候选证据。",
            )
            for upload_id in upload_ids:
                record, parsed_text = get_parsed_text(upload_id)
                if not record:
                    self.event(context["task_id"], "file_warning", "warning", f"上传材料 {upload_id} 不存在，已跳过。")
                    continue
                if not parsed_text:
                    self.event(
                        context["task_id"],
                        "file_warning",
                        "warning",
                        f"上传材料 {record.get('original_filename') or upload_id} 解析不可用：{record.get('error_message') or record.get('status')}",
                    )
                    continue
                self.event(
                    context["task_id"],
                    "file_parsed",
                    "completed",
                    f"FileParserTool parsed uploaded file: {record.get('original_filename') or record.get('filename')}",
                    tool_name="FileParserTool",
                    tool_input={"upload_id": upload_id, "file_type": record.get("file_type")},
                    tool_output_summary=f"解析文本 {len(parsed_text)} 字符。",
                )
                file_evidence = self.extract_tool.extract_evidence_from_text(
                    supplier_profile=supplier,
                    material_text=parsed_text,
                    task_id=context["task_id"],
                    source_type="uploaded_file",
                    source_name=record.get("original_filename") or "上传文件",
                    source_url=record.get("file_path"),
                )
                evidence.extend(file_evidence)
                self.event(
                    context["task_id"],
                    "tool_called",
                    "completed",
                    f"EvidenceExtractionTool extracted {len(file_evidence)} evidence items from uploaded_file。",
                    tool_name=self.extract_tool.name,
                    tool_input={"upload_id": upload_id, "source_type": "uploaded_file"},
                    tool_output_summary=f"上传文件证据 {len(file_evidence)} 条。",
                )
            self.store_tool.save_many(context["task_id"], evidence)
            self.tool_called(
                context,
                self.store_tool.name,
                {"task_id": context["task_id"], "source_type": "user_input", "evidence_count": len(evidence)},
                f"已写入 {len(evidence)} 条用户材料证据。",
            )
            context["evidence"] = [*context.get("evidence", []), *evidence]
            context["evidence_items"] = context["evidence"]
            self.completed(context, f"用户材料分析完成，新增 {len(evidence)} 条证据。")
            return context
        except Exception as exc:  # pragma: no cover
            self.failed(context, f"用户材料分析失败：{exc}")
            raise
