"""
Service xuất báo cáo tổng quan nghiên cứu sang các định dạng chuẩn (Markdown, Microsoft Word .docx, PDF).
Hỗ trợ định dạng bảng so sánh đối chiếu, danh sách gạch đầu dòng, heading phân cấp và danh mục tài liệu tham khảo.
"""

import os
import re
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("paperflow.export")

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except Exception as e:
    logger.warning(f"python-docx is unavailable: {e}")
    DOCX_AVAILABLE = False
    Document = None

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception as e:
    logger.warning(f"reportlab is unavailable: {e}")
    REPORTLAB_AVAILABLE = False

class ExportService:
    """
    Lớp dịch vụ xuất bản báo cáo:
    - Xuất file Markdown (.md).
    - Chuyển đổi cú pháp Markdown thành văn bản Microsoft Word (.docx) chuyên nghiệp có styling.
    - Tạo tài liệu PDF (.pdf) bằng ReportLab với định dạng màu sắc học thuật.
    """
    def __init__(self):
        self.export_dir = os.path.join(settings.UPLOAD_DIR, "exports")
        os.makedirs(self.export_dir, exist_ok=True)

    def export_markdown(self, title: str, content: str, session_id: str) -> str:
        """Xuất báo cáo nguyên bản dưới định dạng Markdown (.md)."""
        filename = f"report_{session_id[:8]}.md"
        file_path = os.path.join(self.export_dir, filename)

        full_md = f"# {title}\n\n{content}\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_md)

        return file_path

    def export_docx(self, title: str, content: str, session_id: str) -> str:
        """
        Chuyển đổi nội dung Markdown sang tài liệu Microsoft Word (.docx).
        """
        filename = f"report_{session_id[:8]}.docx"
        file_path = os.path.join(self.export_dir, filename)

        if not DOCX_AVAILABLE or Document is None:
            # Fallback sang markdown nếu docx không khả dụng
            return self.export_markdown(title, content, session_id)

        doc = Document()

        # Tiêu đề báo cáo
        title_p = doc.add_paragraph()
        title_run = title_p.add_run(title)
        title_run.font.size = Pt(22)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(17, 24, 39)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()  # Dòng trống tạo khoảng cách

        # Phân tích từng dòng markdown và thêm vào Word document
        lines = content.split("\n")
        in_table = False
        table_lines = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("|") and line_str.endswith("|"):
                in_table = True
                table_lines.append(line_str)
                continue
            elif in_table:
                # Dựng bảng Word đã thu thập
                self._render_docx_table(doc, table_lines)
                in_table = False
                table_lines = []

            if line_str.startswith("### "):
                h = doc.add_heading(level=3)
                r = h.add_run(line_str[4:])
                r.font.size = Pt(14)
                r.font.bold = True
            elif line_str.startswith("## "):
                h = doc.add_heading(level=2)
                r = h.add_run(line_str[3:])
                r.font.size = Pt(16)
                r.font.bold = True
                r.font.color.rgb = RGBColor(30, 58, 138)
            elif line_str.startswith("# "):
                h = doc.add_heading(level=1)
                r = h.add_run(line_str[2:])
                r.font.size = Pt(18)
                r.font.bold = True
            elif line_str.startswith("- ") or line_str.startswith("* "):
                p = doc.add_paragraph(style="List Bullet")
                self._add_formatted_runs(p, line_str[2:])
            elif re.match(r"^\d+\.\s", line_str):
                p = doc.add_paragraph(style="List Number")
                num_text = re.sub(r"^\d+\.\s", "", line_str)
                self._add_formatted_runs(p, num_text)
            else:
                p = doc.add_paragraph()
                self._add_formatted_runs(p, line_str)

        if in_table and table_lines:
            self._render_docx_table(doc, table_lines)

        doc.save(file_path)
        logger.info(f"Generated DOCX report: {file_path}")
        return file_path

    def export_pdf(self, title: str, content: str, session_id: str) -> str:
        """
        Xuất báo cáo sang định dạng PDF chất lượng cao bằng ReportLab:
        - Định dạng lề và khổ giấy Letter.
        - Thiết lập bảng màu sắc học thuật chuyên nghiệp.
        """
        filename = f"report_{session_id[:8]}.pdf"
        file_path = os.path.join(self.export_dir, filename)

        doc = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1E3A8A"),
            spaceAfter=15,
            alignment=1  # Căn giữa
        )
        h2_style = ParagraphStyle(
            "ReportH2",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E40AF"),
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=8
        )

        story = [
            Paragraph(title, title_style),
            Spacer(1, 12)
        ]

        for line in content.split("\n"):
            line_str = line.strip()
            if not line_str or line_str.startswith("|"):
                continue

            # Escape ký tự đặc biệt cho bộ parser XML của ReportLab
            clean = line_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            clean = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", clean)
            clean = re.sub(r"\*(.*?)\*", r"<i>\1</i>", clean)

            if clean.startswith("## "):
                story.append(Paragraph(clean[3:], h2_style))
            elif clean.startswith("### "):
                story.append(Paragraph(clean[4:], h2_style))
            elif clean.startswith("- "):
                story.append(Paragraph(f"&bull; {clean[2:]}", body_style))
            else:
                story.append(Paragraph(clean, body_style))

        doc.build(story)
        logger.info(f"Generated PDF report: {file_path}")
        return file_path

    def _render_docx_table(self, doc: Document, lines: list):
        """Chuyển đổi dữ liệu bảng Markdown sang đối tượng Table trong python-docx."""
        rows_data = []
        for l in lines:
            if "---" in l:
                continue
            cells = [c.strip() for c in l.split("|")[1:-1]]
            if cells:
                rows_data.append(cells)

        if not rows_data:
            return

        table = doc.add_table(rows=len(rows_data), cols=len(rows_data[0]))
        table.style = "Table Grid"

        for r_idx, row in enumerate(rows_data):
            for c_idx, cell_text in enumerate(row):
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_text
                if r_idx == 0:
                    for p in cell.paragraphs:
                        for r in p.runs:
                            r.font.bold = True

        doc.add_paragraph()  # Khoảng cách sau bảng

    def _add_formatted_runs(self, paragraph, text: str):
        """Hỗ trợ in đậm các đoạn văn bản có ký hiệu **...** trong Markdown."""
        parts = re.split(r"(\*\*.*?\*\*)", text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            else:
                paragraph.add_run(part)

# Khởi tạo singleton instance cho ExportService
export_service = ExportService()

