"""
Service quản lý Cơ sở dữ liệu Vector Qdrant và chức năng tìm kiếm tăng cường truy xuất (RAG).
Hỗ trợ lưu trữ Vector in-memory/server, tính toán embedding vector hóa văn bản và truy vấn tìm kiếm đoạn tài liệu tương đồng nhất theo ngữ cảnh.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
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
    - Tạo bảng (collection) lưu trữ vector embedding và metadata của các chunk.
    - Chuyển đổi văn bản thành vector embedding (Deterministic Semantic Vectorizer).
    - Lưu trữ (upsert) và tìm kiếm ngữ nghĩa (cosine similarity search) phục vụ RAG.
    """
    def __init__(self):
        self.dimension = settings.VECTOR_DIMENSION
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.client = self._init_client()
        self._ensure_collection()

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

    def generate_embedding(self, text: str) -> List[float]:
        """
        Tạo vector embedding từ văn bản bằng kỹ thuật Hashing Vectorization chuẩn hóa (L2 Normalized):
        Đảm bảo tính toán nhanh, độc lập mạng và tính xác định (deterministic) cho RAG.
        """
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for word in words:
            # Hash từng từ sang chỉ số trong không gian vector
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            val = (h % 1000) / 1000.0 - 0.5
            vec[idx] += val

        # Chuẩn hóa vector theo độ dài đơn vị (Unit L2 norm)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def insert_chunks(
        self,
        session_id: str,
        paper_id: str,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """Lưu trữ danh sách các đoạn văn bản (chunks) và vector embedding tương ứng vào Qdrant."""
        points = []
        point_ids = []

        for idx, chunk in enumerate(chunks):
            point_id = f"{paper_id}_{idx}"
            embedding = self.generate_embedding(chunk["text"])
            
            payload = {
                "session_id": session_id,
                "paper_id": paper_id,
                "chunk_index": chunk.get("chunk_index", idx),
                "page_number": chunk.get("page_number", 1),
                "section_name": chunk.get("section_name", "General"),
                "text": chunk["text"],
            }

            # Chuyển đổi định danh sang số nguyên 64-bit cho Qdrant ID
            int_id = int(hashlib.md5(point_id.encode("utf-8")).hexdigest()[:16], 16)
            point_ids.append(point_id)

            points.append(PointStruct(
                id=int_id,
                vector=embedding,
                payload=payload
            ))

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Inserted {len(points)} chunks into Qdrant for paper {paper_id}")

        return point_ids

    async def search_relevant_chunks(
        self,
        session_id: str,
        query: str,
        top_k: int = 5,
        paper_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Truy xuất các đoạn văn bản liên quan nhất theo ngữ nghĩa (RAG Semantic Search):
        Lọc chính xác theo session_id (và tùy chọn paper_id) để đảm bảo cô lập dữ liệu giữa các phiên.
        """
        try:
            query_vector = self.generate_embedding(query)
            
            # Thiết lập bộ lọc dữ liệu theo session_id
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

            # Thực hiện truy vấn tương đồng cosine trên Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k
            )

            results = []
            for hit in search_results:
                results.append({
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "paper_id": hit.payload.get("paper_id", ""),
                    "page_number": hit.payload.get("page_number", 1),
                    "section_name": hit.payload.get("section_name", ""),
                    "chunk_index": hit.payload.get("chunk_index", 0),
                })
            return results
        except Exception as e:
            logger.error(f"Error searching Qdrant: {e}")
            return []

    # Alias thuận tiện gọi hàm
    search_chunks = search_relevant_chunks

# Khởi tạo singleton instance cho QdrantService
qdrant_service = QdrantService()

