"""
Agent Đọc và Phân tích tài liệu (ReadingAgent - UC004, UC005).
Chịu trách nhiệm bóc tách nội dung PDF/Abstract, đánh chỉ mục vector RAG vào Qdrant và trích xuất cấu trúc 5 thành phần trọng tâm (Phương pháp, Bộ dữ liệu, Chỉ số, Kết quả, Hạn chế).
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .base import BaseAgent
from .adk_tools import retrieve_document_chunks
from ..models.paper import Paper, PaperAnalysis
from ..models.chunk import DocumentChunk
from ..services.pdf_parser import pdf_parser
from ..services.qdrant_service import qdrant_service
from ..services.llm_service import llm_service
from app.core.config import settings

logger = logging.getLogger("paperflow.reading_agent")


class ReadingAgent(BaseAgent):
    MISSING_DATA = "Chưa trích xuất được dữ liệu."
    ANALYSIS_FIELDS = ("method", "dataset", "metrics", "results", "limitations", "summary")
    """
    ReadingAgent: Tác tử đọc sâu tài liệu khoa học:
    - Đọc file PDF tải lên hoặc Abstract của bài báo.
    - Chia nhỏ thành DocumentChunk và nhúng vector vào Qdrant (RAG Storage).
    - Sử dụng LLM trích xuất 5 khía cạnh có cấu trúc (method, dataset, metrics, results, limitations).
    - Lưu kết quả vào bảng `paper_analyses` và `document_chunks`.
    """
    def __init__(self):
        super().__init__(
            name="ReadingAgent",
            description="Đọc tài liệu, trích xuất thông tin cấu trúc và lưu trữ vector ngữ nghĩa vào Qdrant (UC004, UC005).",
            instruction="""Bạn là chuyên gia phân tích và bóc tách tài liệu học thuật.
            Nhiệm vụ: Phân tích sâu nội dung bài báo khoa học, trích xuất chính xác 5 khía cạnh trọng tâm:
            1. method: Kiến trúc mô hình, phương pháp thuật toán.
            2. dataset: Tập dữ liệu huấn luyện và đánh giá.
            3. metrics: Chỉ số định lượng và thước đo hiệu năng.
            4. results: Các phát hiện thực nghiệm then chốt.
            5. limitations: Rào cản, hạn chế kỹ thuật và chi phí tính toán.""",
            tools=[retrieve_document_chunks]
        )

    async def run(
        self,
        db: AsyncSession,
        session_id: str,
        paper_ids: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Thực thi quy trình đọc và phân tích tài liệu:
        - Lấy danh sách các bài báo được chọn trong phiên (is_selected=True).
        - Lặp qua từng bài báo để trích xuất chunk, lưu Qdrant và phân tích cấu trúc JSON qua LLM.
        """
        run = await self.log_start(
            db,
            session_id,
            step_description="Đọc và phân tích cấu trúc tài liệu nghiên cứu theo chuẩn ADK",
            input_data={"paper_ids": paper_ids}
        )

        try:
            # Truy vấn danh sách bài báo được chọn kèm quan hệ analysis
            stmt = (
                select(Paper)
                .where(Paper.session_id == session_id, Paper.is_selected.is_(True))
                .options(selectinload(Paper.analysis))
            )
            if paper_ids:
                stmt = stmt.where(Paper.id.in_(paper_ids))
            
            res = await db.execute(stmt)
            papers = res.scalars().all()

            if not papers:
                logger.warning(f"[{self.name}] No selected papers found for session {session_id}")
                await self.log_end(db, run, status="COMPLETED", output_data={"analyzed_count": 0})
                return {"analyzed_count": 0, "results": []}

            analyzed_results = []

            for paper in papers:
                analysis = await self._analyze_paper(db, session_id, paper)
                analyzed_results.append(analysis)

            await db.commit()

            output = {
                "analyzed_count": len(analyzed_results),
                "paper_ids": [p.id for p in papers]
            }
            await self.log_end(db, run, status="COMPLETED", output_data=output)
            return output

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}", exc_info=True)
            await db.rollback()
            await self.log_end(db, run, status="FAILED", error_message=str(e))
            raise

    def _detect_section(self, text: str) -> str:
        """Nhận diện tên phân mục học thuật sơ bộ (Section) từ đoạn đầu của chunk."""
        lower = text.lower()[:300]
        if "abstract" in lower:
            return "Abstract"
        elif "introduction" in lower:
            return "Introduction"
        elif "related work" in lower or "background" in lower:
            return "Related Work"
        elif "method" in lower or "methodology" in lower or "architecture" in lower:
            return "Methodology"
        elif "experiment" in lower or "evaluation" in lower or "results" in lower:
            return "Experiments & Results"
        elif "discussion" in lower or "limitation" in lower:
            return "Discussion & Limitations"
        elif "conclusion" in lower:
            return "Conclusion"
        return "Body"

    def extract_and_chunk_pdf(
        self,
        pdf_path: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Đọc file PDF bài báo và chia nhỏ thành các chunks có kích thước phù hợp (Sliding Window Chunking):
        - Sử dụng pypdf để trích xuất văn bản từng trang.
        - Giữ lại số trang (page_number) chính xác cho từng chunk phục vụ trích dẫn RAG.
        - Áp dụng chunk_size và chunk_overlap để giữ sự liên tục về mặt ngữ nghĩa giữa các đoạn cắt.
        - Loại bỏ ký tự thừa và khôi phục từ bị ngắt dòng gạch nối.
        """
        c_size = chunk_size or settings.CHUNK_SIZE
        c_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        chunks: List[Dict[str, Any]] = []
        full_text_list: List[str] = []
        chunk_idx = 0

        reader = PdfReader(pdf_path)
        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""

            # Chuẩn hóa văn bản: gộp khoảng trắng thừa và nối từ bị ngắt ở cuối dòng
            cleaned_text = re.sub(r"\s+", " ", raw_text)
            cleaned_text = re.sub(r"-\s+", "", cleaned_text).strip()

            if not cleaned_text:
                continue

            full_text_list.append(cleaned_text)

            # Cắt văn bản trang thành các chunks có kích thước cố định và có phần overlap
            start = 0
            text_len = len(cleaned_text)

            while start < text_len:
                end = min(start + c_size, text_len)
                chunk_text = cleaned_text[start:end].strip()

                # Bỏ qua những đoạn quá ngắn (< 50 ký tự) không chứa đủ thông tin ngữ nghĩa
                if len(chunk_text) >= 50:
                    chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "section_name": self._detect_section(chunk_text),
                        "text": chunk_text
                    })
                    chunk_idx += 1

                if end >= text_len:
                    break
                start += max(1, c_size - c_overlap)

        full_text = "\n\n".join(full_text_list)
        return full_text, chunks

    async def _analyze_paper(self, db: AsyncSession, session_id: str, paper: Paper) -> Dict[str, Any]:
        """
        Xử lý chi tiết một bài báo:
        1. Đọc nội dung PDF hoặc trích tóm tắt abstract.
        2. Băm văn bản và đưa các vector embedding vào Qdrant (UC005).
        3. Dùng LLM bóc tách thông tin có cấu trúc (UC004).
        4. Tạo mới hoặc cập nhật bản ghi PaperAnalysis trong SQL database.
        """
        content_text = ""
        chunks = []

        # 1. Đọc nội dung file PDF nếu tồn tại trên ổ đĩa
        if paper.pdf_path and os.path.exists(paper.pdf_path):
            try:
                full_text, chunks = self.extract_and_chunk_pdf(paper.pdf_path)
                content_text = full_text[:8000]  # Lấy 8.000 ký tự đầu cho phân tích trích xuất
            except Exception as e:
                logger.warning(f"Failed to parse PDF for {paper.id}: {e}. Falling back to abstract.")
                content_text = f"Title: {paper.title}\nAbstract: {paper.abstract}"
        else:
            content_text = f"Title: {paper.title}\nAbstract: {paper.abstract or ''}"
            # Tạo chunk tổng hợp phục vụ RAG
            chunks = [{
                "chunk_index": 0,
                "page_number": 1,
                "section_name": "Abstract",
                "text": content_text
            }]


        # 2. Đưa các Chunks vào Qdrant Vector Store (UC005)
        try:
            point_ids = await qdrant_service.insert_chunks(
                session_id=session_id,
                paper_id=paper.id,
                chunks=chunks
            )
            # Xóa các chunk cũ trong SQL để đảm bảo tính idempotent
            del_chunks_stmt = select(DocumentChunk).where(DocumentChunk.paper_id == paper.id)
            del_res = await db.execute(del_chunks_stmt)
            for old_c in del_res.scalars().all():
                await db.delete(old_c)

            # Lưu metadata của từng chunk vào bảng document_chunks trong SQL
            for idx, c in enumerate(chunks):
                doc_chunk = DocumentChunk(
                    paper_id=paper.id,
                    session_id=session_id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                    section_name=c["section_name"],
                    text=c["text"],
                    embedding_id=point_ids[idx] if idx < len(point_ids) else None
                )
                db.add(doc_chunk)
            await db.flush()
        except Exception as e:
            logger.error(f"Error ingesting chunks to Qdrant: {e}")


        # 3. Sử dụng LLM trích xuất các thành phần có cấu trúc (UC004)
        prompt = f"""You are an expert scientific researcher. Analyze the following academic paper content and extract structured research components in Vietnamese (Tiếng Việt).
Paper Title: {paper.title}
Authors: {", ".join(paper.authors) if paper.authors else "N/A"}
Content:
{content_text[:5000]}

Extract the following in Vietnamese (Tiếng Việt) with accurate scientific terminology:
1. method: Kiến trúc mô hình, phương pháp thuật toán cốt lõi.
2. dataset: Tập dữ liệu huấn luyện, kiểm thử và benchmark được sử dụng.
3. metrics: Chỉ số định lượng và thước đo hiệu năng (Accuracy, F1, Dice, mIoU...).
4. results: Kết quả thực nghiệm chính và đóng góp nổi bật.
5. limitations: Rào cản, hạn chế kỹ thuật và chi phí tính toán.
6. summary: Bản tóm tắt tổng quan 2-3 câu bằng Tiếng Việt.

Respond in exact JSON format:
{{
  "method": "...",
  "dataset": "...",
  "metrics": "...",
  "results": "...",
  "limitations": "...",
  "summary": "..."
}}
"""
        # PaperAnalysis feeds the comparison matrix and final report.  Never permit
        # the LLM service's offline mock here: it fabricates the same method,
        # dataset and metrics for every unrelated paper.
        try:
            extracted = await llm_service.generate_json(prompt, allow_mock=False)
            extracted = self._normalize_extraction(extracted)
        except Exception as exc:
            logger.warning(
                "Unable to extract structured evidence for paper %s; saving missing-data markers: %s",
                paper.id,
                exc,
            )
            extracted = self._missing_extraction(paper.abstract)

        # 4. Lưu / Cập nhật bảng PaperAnalysis
        if paper.analysis:
            analysis = paper.analysis
            analysis.method = extracted["method"]
            analysis.dataset = extracted["dataset"]
            analysis.metrics = extracted["metrics"]
            analysis.results = extracted["results"]
            analysis.limitations = extracted["limitations"]
            analysis.summary = extracted["summary"]
            analysis.raw_analysis = extracted
        else:
            analysis = PaperAnalysis(
                paper_id=paper.id,
                method=extracted["method"],
                dataset=extracted["dataset"],
                metrics=extracted["metrics"],
                results=extracted["results"],
                limitations=extracted["limitations"],
                summary=extracted["summary"],
                raw_analysis=extracted
            )
            db.add(analysis)

        paper.ingestion_status = "PROCESSED"
        return extracted

    @classmethod
    def _missing_extraction(cls, abstract: Optional[str] = None) -> Dict[str, str]:
        """Return transparent placeholders, never plausible but unsupported facts."""
        return {
            "method": cls.MISSING_DATA,
            "dataset": cls.MISSING_DATA,
            "metrics": cls.MISSING_DATA,
            "results": cls.MISSING_DATA,
            "limitations": cls.MISSING_DATA,
            "summary": abstract.strip() if abstract and abstract.strip() else cls.MISSING_DATA,
        }

    @classmethod
    def _normalize_extraction(cls, extracted: Any) -> Dict[str, str]:
        """Accept only non-empty model fields; label omitted fields transparently."""
        if not isinstance(extracted, dict):
            return cls._missing_extraction()
        normalized = cls._missing_extraction()
        for field in cls.ANALYSIS_FIELDS:
            value = extracted.get(field)
            if isinstance(value, str) and value.strip():
                normalized[field] = value.strip()
        return normalized

# Khởi tạo singleton instance cho ReadingAgent
reading_agent = ReadingAgent()

