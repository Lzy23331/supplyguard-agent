from __future__ import annotations

import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class PDFReportService:
    name = "PDFReportService"

    def __init__(self) -> None:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    def render(self, markdown: str, *, task_id: str) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title=f"SupplyGuard Report {task_id}",
        )
        styles = getSampleStyleSheet()
        base = ParagraphStyle(
            "SupplyGuardBase",
            parent=styles["Normal"],
            fontName="STSong-Light",
            fontSize=9.5,
            leading=15,
            textColor=colors.HexColor("#243042"),
            wordWrap="CJK",
        )
        h1 = ParagraphStyle("SupplyGuardH1", parent=base, fontSize=18, leading=24, spaceAfter=8, textColor=colors.HexColor("#172033"))
        h2 = ParagraphStyle("SupplyGuardH2", parent=base, fontSize=13, leading=19, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#1f4e79"))
        small = ParagraphStyle("SupplyGuardSmall", parent=base, fontSize=8.5, leading=13, textColor=colors.HexColor("#475569"))
        story = []
        normalized = markdown.replace("\r\n", "\n")
        if f"任务 ID：{task_id}" not in normalized:
            normalized = normalized.replace("## 1. 基本信息", f"## 1. 基本信息\n- 任务 ID：{task_id}", 1)
        for raw in normalized.splitlines():
            line = raw.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
            if line.startswith("# "):
                story.append(Paragraph(self._escape(line[2:]), h1))
                continue
            if line.startswith("## "):
                story.append(Paragraph(self._escape(line[3:]), h2))
                continue
            if line.startswith("### "):
                story.append(Paragraph(self._escape(line[4:]), h2))
                continue
            if line.startswith("|"):
                story.append(Paragraph(self._escape(self._table_line(line)), small))
                continue
            story.append(Paragraph(self._escape(self._clean_markdown(line)), base))
        doc.build(story)
        return buffer.getvalue()

    def _table_line(self, line: str) -> str:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            return ""
        return " | ".join(cells)

    def _clean_markdown(self, line: str) -> str:
        line = re.sub(r"^[-*]\s+", "• ", line)
        line = re.sub(r"^\d+\.\s+", "• ", line)
        line = line.replace("**", "")
        line = re.sub(r"`([^`]+)`", r"\1", line)
        return line

    def _escape(self, text: str) -> str:
        return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
