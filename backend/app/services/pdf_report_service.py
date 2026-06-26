from __future__ import annotations

import re
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class PDFReportService:
    name = "PDFReportService"

    def __init__(self) -> None:
        self.font_name = self._register_chinese_font()

    def _register_chinese_font(self) -> str:
        candidates = [
            ("MicrosoftYaHei", Path("C:/Windows/Fonts/msyh.ttc")),
            ("SimHei", Path("C:/Windows/Fonts/simhei.ttf")),
            ("DengXian", Path("C:/Windows/Fonts/Deng.ttf")),
            ("SimSun", Path("C:/Windows/Fonts/simsun.ttc")),
            ("NotoSansCJK", Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")),
            ("WenQuanYiZenHei", Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")),
        ]
        for name, font_path in candidates:
            if not font_path.exists():
                continue
            try:
                pdfmetrics.registerFont(TTFont(name, str(font_path)))
                return name
            except Exception:
                continue
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"

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
            fontName=self.font_name,
            fontSize=9.5,
            leading=15,
            textColor=colors.HexColor("#243042"),
            wordWrap="CJK",
        )
        h1 = ParagraphStyle("SupplyGuardH1", parent=base, fontSize=18, leading=24, spaceAfter=8, textColor=colors.HexColor("#172033"))
        h2 = ParagraphStyle("SupplyGuardH2", parent=base, fontSize=13, leading=19, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#1f4e79"))
        small = ParagraphStyle("SupplyGuardSmall", parent=base, fontSize=8.5, leading=13, textColor=colors.HexColor("#475569"))
        story = []
        normalized = self._normalize_text(markdown).replace("\r\n", "\n")
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
                table_text = self._table_line(line)
                if table_text:
                    story.append(Paragraph(self._escape(table_text), small))
                continue
            story.append(Paragraph(self._escape(self._clean_markdown(line)), base))
        doc.build(story)
        return buffer.getvalue()

    def _normalize_text(self, text: str) -> str:
        replacements = {
            "�": "",
            "•": "-",
            "●": "-",
            "·": "-",
            "～": "-",
            "—": "-",
            "–": "-",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _table_line(self, line: str) -> str:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            return ""
        return " | ".join(cells)

    def _clean_markdown(self, line: str) -> str:
        line = re.sub(r"^[-*]\s+", "- ", line)
        line = re.sub(r"^\d+\.\s+", "- ", line)
        line = line.replace("**", "")
        line = re.sub(r"`([^`]+)`", r"\1", line)
        return line

    def _escape(self, text: str) -> str:
        return escape(text or "", quote=False)