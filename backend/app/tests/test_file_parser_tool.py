from pathlib import Path

from pypdf import PdfWriter

from app.tools.file_parser_tool import FileParserTool


def test_txt_and_md_parse_as_text(tmp_path: Path):
    path = tmp_path / "material.txt"
    path.write_text("供应商存在交付延期。", encoding="utf-8")

    assert "交付延期" in FileParserTool().parse(path, "txt")


def test_csv_parse_to_readable_text(tmp_path: Path):
    path = tmp_path / "material.csv"
    path.write_text("事项,说明\n交付,存在交付延期\n付款,存在付款纠纷\n", encoding="utf-8")

    text = FileParserTool().parse(path, "csv")

    assert "表头" in text
    assert "交付延期" in text


def test_pdf_without_extractable_text_reports_ocr_not_supported(tmp_path: Path):
    path = tmp_path / "scan.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as file:
        writer.write(file)

    try:
        FileParserTool().parse(path, "pdf")
    except ValueError as exc:
        assert "OCR" in str(exc)
    else:
        raise AssertionError("blank PDF should not parse as text")
