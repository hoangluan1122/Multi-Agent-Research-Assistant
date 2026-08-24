"""
Service xử lý và trích xuất nội dung từ file PDF bài báo khoa học.
Hỗ trợ đọc từng trang, làm sạch khoảng trắng/gạch nối, nhận diện phân mục và băm văn bản thành các chunks có độ chồng lấn (overlap).
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from app.core.config import settings

logger = logging.getLogger("paperflow.pdf")

class PDFParser:
    """
    Lớp dịch vụ phân tích tài liệu PDF:
    - Trích xuất toàn bộ văn bản và cấu trúc phân trang từ PDF bằng pypdf.
    - Nhận diện phần tiêu mục (Abstract, Introduction, Methodology, Experiments, Conclusion...).
    - Chia nhỏ văn bản thành các DocumentChunk phù hợp cho việc đánh chỉ mục vector RAG.
    """
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Đọc file PDF từ đường dẫn và trích xuất nội dung văn bản:
        Trả về tuple gồm (toàn bộ văn bản nối lại, danh sách nội dung theo từng trang).
        """
        full_text = []
        pages_content = []

        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)

            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                text = self._clean_text(text)
                if text:
                    full_text.append(text)
                    pages_content.append({
                        "page_number": page_idx + 1,
                        "text": text
                    })

            joined_text = "\n\n".join(full_text)
            logger.info(f"Successfully extracted {len(joined_text)} chars from {total_pages} pages in {file_path}")
            return joined_text, pages_content
        except Exception as e:
            logger.error(f"Error reading PDF file {file_path}: {e}")
            raise

    def chunk_document(self, pages_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chia nhỏ nội dung văn bản thành các chunks có kích thước cố định và có phần chồng lấn (overlap):
        Giữ nguyên số trang và tên phân mục ước tính cho từng đoạn.
        """
        chunks = []
        chunk_idx = 0

        for page_data in pages_content:
            page_num = page_data["page_number"]
            page_text = page_data["text"]

            # Nhận diện tiêu mục sơ bộ
            current_section = self._detect_section(page_text)

            # Chia đoạn văn bản của trang thành các chunk có kích thước chunk_size và chồng lấn chunk_overlap
            start = 0
            text_len = len(page_text)

            while start < text_len:
                end = min(start + self.chunk_size, text_len)
                chunk_text = page_text[start:end].strip()

                # Bỏ qua các đoạn quá ngắn hoặc chỉ chứa ký tự rác
                if len(chunk_text) > 50:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "section_name": current_section,
                        "text": chunk_text
                    })
                    chunk_idx += 1

                if end >= text_len:
                    break
                start += (self.chunk_size - self.chunk_overlap)

        return chunks

    def _clean_text(self, text: str) -> str:
        """Chuẩn hóa văn bản: Loại bỏ khoảng trắng thừa, sửa lỗi ngắt từ bằng dấu gạch nối ở cuối dòng."""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"-\s+", "", text)  # Khôi phục các từ bị gắt dòng (ví dụ: trans- former -> transformer)
        return text.strip()

    def _detect_section(self, text: str) -> str:
        """Heuristic nhận diện tên phân mục học thuật (Section) từ 300 ký tự đầu của đoạn văn bản."""
        lower = text.lower()
        if "abstract" in lower[:300]:
            return "Abstract"
        elif "introduction" in lower[:300]:
            return "Introduction"
        elif "related work" in lower[:300] or "background" in lower[:300]:
            return "Related Work"
        elif "method" in lower[:300] or "methodology" in lower[:300] or "architecture" in lower[:300]:
            return "Methodology"
        elif "experiment" in lower[:300] or "evaluation" in lower[:300] or "results" in lower[:300]:
            return "Experiments & Results"
        elif "discussion" in lower[:300] or "limitation" in lower[:300]:
            return "Discussion & Limitations"
        elif "conclusion" in lower[:300]:
            return "Conclusion"
        return "Body"

# Khởi tạo singleton instance cho PDFParser
pdf_parser = PDFParser()

