"""
Service quản lý Cơ sở dữ liệu Vector Qdrant và chức năng tìm kiếm tăng cường truy xuất (RAG).
Hỗ trợ lưu trữ Vector in-memory/server, tính toán embedding vector hóa văn bản và truy vấn tìm kiếm đoạn tài liệu tương đồng nhất theo ngữ cảnh.
"""

import logging
import hashlib
import uuid
from typing import List, Dict, Any, Optional, Union
import numpy as np
import google.generativeai as genai

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.core.config import settings

logger = logging.getLogger("paperflow.qdrant")

class QdrantService:
    """
    Lớp dịch vụ cơ sở dữ liệu Vector:
    - Quản lý kết nối Qdrant (in-memory `:memory:` hoặc external server).
    - Tạo collection lưu trữ vector embedding và metadata của các chunk.
    - Mã hóa ngữ nghĩa văn bản thành vector 768 chiều qua Google Gemini API (text-embedding-004).
    - Lưu trữ (upsert) và tìm kiếm ngữ nghĩa (cosine similarity search) phục vụ RAG.
    """
    def __init__(self):
        self.dimension = settings.VECTOR_DIMENSION
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        # self.embedding_model = "models/text-embedding-004"
        self.embedding_model = "models/gemini-embedding-001"
        self._init_gemini()
        self.client = self._init_client()
        self._ensure_collection()

    def _init_gemini(self):
        """Khởi tạo API Key cho Google AI Studio Gemini SDK."""
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            logger.info("Configured Gemini API for Text Embeddings (models/gemini-embedding-001).")
        else:
            logger.warning("GEMINI_API_KEY is not configured. Embeddings will use zero-vector fallback.")

    def _init_client(self) -> QdrantClient:
        """Khởi tạo kết nối Qdrant Client; tự động chuyển về in-memory nếu không kết nối được server."""
        try:
            if settings.QDRANT_USE_MEMORY:
                logger.info("Initializing Qdrant In-Memory Vector Store.")
                return QdrantClient(":memory:")
            else:
                logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
                return QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
                )
        except Exception as e:
            logger.warning(f"Could not connect to external Qdrant: {e}. Falling back to In-Memory store.")
            return QdrantClient(":memory:")

    def _ensure_collection(self):
        """Đảm bảo Collection lưu trữ vector đã tồn tại trong Qdrant với cấu hình khoảng cách Cosine."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    async def generate_embedding(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Mã hóa một đoạn văn bản thành vector ngữ nghĩa 768 chiều sử dụng Gemini API:
        - Sử dụng mô hình `models/text-embedding-004`.
        - Hỗ trợ task_type: 'retrieval_document' (cho tài liệu/chunk) hoặc 'retrieval_query' (cho câu hỏi).
        """
        if not text or not text.strip():
            return [0.0] * self.dimension

        if settings.GEMINI_API_KEY:
            try:
                response = await genai.embed_content_async(
                    model=self.embedding_model,
                    content=text.strip(),
                    task_type=task_type
                )
                embedding = getattr(response, "embedding", None) or []
                if not embedding and hasattr(response, "embeddings"):
                    embs = response.embeddings
                    if embs:
                        first = embs[0]
                        if hasattr(first, "values"):
                            v = first.values
                            embedding = list(v() if callable(v) else v)
                        elif isinstance(first, (list, tuple)):
                            embedding = list(first)
            except Exception as e:
                logger.error(f"Error generating embedding via Gemini API: {e}")

        # Fallback an toàn nếu chưa cấu hình API key hoặc có sự cố mạng
        return [0.0] * self.dimension

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document"
    ) -> List[List[float]]:
        """
        Mã hóa một danh sách các văn bản thành danh sách vectors trong một lượt gọi API (Batch Embedding),
        giúp tối ưu tốc độ và giảm thiểu giới hạn Request Rate Limit của Google AI Studio.
        """
        valid_texts = [t.strip() if t and t.strip() else " " for t in texts]
        if not valid_texts:
            return []

        if settings.GEMINI_API_KEY:
            try:
                response = await genai.embed_content_async(
                    model=self.embedding_model,
                    content=valid_texts,
                    task_type=task_type
                )
                raw_embeddings = getattr(response, "embeddings", None) or []
                embeddings = []
                for e in raw_embeddings:
                    if isinstance(e, dict) and "values" in e:
                        embeddings.append(list(e["values"]))
                    elif hasattr(e, "values"):
                        v = e.values
                        embeddings.append(list(v() if callable(v) else v))
                    elif isinstance(e, (list, tuple)):
                        embeddings.append(list(e))
                if embeddings:
                    return embeddings
            except Exception as e:
                logger.error(f"Error generating batch embeddings via Gemini API: {e}")

        # Fallback khi gọi theo batch thất bại: sinh fallback từng phần tử
        return [[0.0] * self.dimension for _ in texts]


    async def insert_chunks(
        self,
        session_id: str,
        paper_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Lưu trữ danh sách các đoạn văn bản (chunks) và vector embedding tương ứng vào Qdrant (collection: paperflow_chunks):
        - Mã hóa ngữ nghĩa toàn bộ chunks bằng Gemini API thông qua batch embedding.
        - Đóng gói đầy đủ payload metadata: session_id, paper_id, chunk_index, page_number, section_name, text.
        - Thực hiện Upsert vào Qdrant và trả về danh sách UUID embedding_id.
        """
        if not chunks:
            return []

        # 1. Trích xuất text và thực hiện batch embedding qua Gemini
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.generate_embeddings_batch(texts, task_type="retrieval_document")

        points = []
        point_ids = []

        for idx, chunk in enumerate(chunks):
            # Tạo UUID xác định theo paper_id và chunk_index để đảm bảo tính Idempotent
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{paper_id}_{chunk.get('chunk_index', idx)}"))
            point_ids.append(point_uuid)

            vector = embeddings[idx] if idx < len(embeddings) else [0.0] * self.dimension

            payload = {
                "session_id": session_id,
                "paper_id": paper_id,
                "chunk_index": chunk.get("chunk_index", idx),
                "page_number": chunk.get("page_number", 1),
                "section_name": chunk.get("section_name", "General"),
                "text": chunk["text"],
            }

            points.append(PointStruct(
                id=point_uuid,
                vector=vector,
                payload=payload
            ))

        # 2. Upsert vectors và payload vào Qdrant collection
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} vector points into Qdrant collection '{self.collection_name}' for paper '{paper_id}'")

        return point_ids


    async def search_relevant_chunks(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        paper_id: Optional[str] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Truy xuất các đoạn văn bản liên quan nhất theo ngữ nghĩa (RAG Semantic Retrieval):
        - Nhận câu query, mã hóa thành vector 768 chiều với task_type='retrieval_query' qua Gemini API.
        - Gọi Qdrant search với độ đo Cosine Similarity.
        - Áp dụng bộ lọc bắt buộc (must filter) theo `session_id` (và tùy chọn `paper_id`) để cô lập dữ liệu.
        - Trả về danh sách top_k chunks kèm điểm tương đồng (score) và metadata (số trang, phân mục).
        """
        if not query or not query.strip():
            logger.warning("Empty query provided to search_relevant_chunks")
            return []

        try:
            # 1. Mã hóa câu hỏi thành vector ngữ nghĩa thông qua Gemini
            query_vector = await self.generate_embedding(query.strip(), task_type="retrieval_query")
            
            # 2. Thiết lập bộ lọc dữ liệu chính xác theo session_id
            must_conditions = [
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id)
                )
            ]
            if paper_id:
                must_conditions.append(
                    FieldCondition(
                        key="paper_id",
                        match=MatchValue(value=paper_id)
                    )
                )

            query_filter = Filter(must=must_conditions)

            # 3. Thực hiện truy vấn xấp xỉ lân cận gần nhất (ANN) trên Qdrant với Cosine Similarity
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold
            )

            # 4. Trích xuất kết quả và metadata trả về cho LLM / Agent
            results = []
            for hit in search_results:
                payload = hit.payload or {}  # Guard: payload can be None if no data was stored
                results.append({
                    "chunk_id": str(hit.id),
                    "score": round(float(hit.score), 4),
                    "text": payload.get("text", ""),
                    "paper_id": payload.get("paper_id", ""),
                    "page_number": payload.get("page_number", 1),
                    "section_name": payload.get("section_name", "General"),
                    "chunk_index": payload.get("chunk_index", 0),
                    "session_id": payload.get("session_id", session_id)
                })

            logger.info(f"Retrieved {len(results)} chunks for session '{session_id}' with query: '{query[:50]}...'")
            return results

        except Exception as e:
            logger.error(f"Error searching Qdrant in session {session_id}: {e}", exc_info=True)
            return []


    # Alias thuận tiện gọi hàm
    search_chunks = search_relevant_chunks

# Khởi tạo singleton instance cho QdrantService
qdrant_service = QdrantService()

