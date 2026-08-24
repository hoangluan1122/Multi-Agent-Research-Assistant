"""
Kịch bản kiểm thử tích hợp toàn diện cho Backend PaperFlow (Validation Test Suite):
- Khởi tạo bảng cơ sở dữ liệu (SQLite / PostgreSQL).
- Kiểm tra Health Check & Cấu hình hệ thống (UC013).
- Kiểm tra Khởi tạo phiên nghiên cứu (UC001).
- Kiểm tra Tìm kiếm tài liệu học thuật (UC002).
- Kiểm tra Đọc và trích xuất cấu trúc bài báo (UC004, UC005).
- Kiểm tra Quy trình Multi-Agent hoàn chỉnh (UC006 - UC011).
- Kiểm tra Báo cáo và Xuất bản sang Markdown, DOCX, PDF (UC012).
"""

import asyncio
import os
import sys
import io

# Đảm bảo mã hóa UTF-8 trên console Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Đảm bảo thư mục Backend nằm trong sys.path để import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import init_db
from app.orchestrator.workflow import workflow_engine

async def run_backend_tests():
    """Hàm thực thi toàn bộ kịch bản kiểm thử tích hợp Backend."""
    print("\n--- Starting PaperFlow Backend Validation Tests ---", flush=True)
    await init_db()
    print("[OK] Database tables initialized.", flush=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Kiểm tra trạng thái máy chủ (Health Check)
        resp = await client.get("/api/health")
        assert resp.status_code == 200, f"Health check failed: {resp.text}"
        print(f"[OK] Health Check: {resp.json()}", flush=True)

        # 2. Kiểm tra API cấu hình hệ thống (UC013)
        resp = await client.get("/api/v1/config")
        assert resp.status_code == 200, f"Config failed: {resp.text}"
        print(f"[OK] System Config: {resp.json()['project_name']} (v{resp.json()['version']})", flush=True)

        # 3. Tạo phiên nghiên cứu mới (UC001)
        session_payload = {
            "topic": "Deep Learning for Medical Image Segmentation",
            "research_question": "What are the latest transformer-based architectures and benchmarks?",
            "max_papers": 2,
            "sources": ["arxiv", "semantic_scholar"],
            "citation_style": "IEEE"
        }
        resp = await client.post("/api/v1/sessions", json=session_payload)
        assert resp.status_code == 201, f"Create session failed: {resp.text}"
        session_data = resp.json()
        session_id = session_data["id"]
        print(f"[OK] Created Research Session UC001 (ID: {session_id}, Status: {session_data['status']})", flush=True)

        # 4. Tìm kiếm tài liệu học thuật (UC002)
        search_payload = {
            "session_id": session_id,
            "query": "medical image segmentation transformer",
            "max_results": 2
        }
        resp = await client.post("/api/v1/papers/search", json=search_payload)
        assert resp.status_code == 200, f"Search papers failed: {resp.text}"
        papers = resp.json()
        assert len(papers) > 0, "No papers found"
        print(f"[OK] Academic Search UC002 found {len(papers)} papers: '{papers[0]['title'][:50]}...'", flush=True)

        # 5. Phân tích tài liệu đơn lẻ (UC004, UC005)
        first_paper_id = papers[0]["id"]
        resp = await client.post(f"/api/v1/papers/{first_paper_id}/analyze")
        assert resp.status_code == 200, f"Analyze paper failed: {resp.text}"
        analyzed_paper = resp.json()
        assert analyzed_paper.get("analysis") is not None, "Paper analysis missing"
        print(f"[OK] Paper Analysis UC004/UC005: Method='{analyzed_paper['analysis']['method'][:40]}...'", flush=True)

        # 6. Thực thi quy trình Multi-Agent hoàn chỉnh (UC006 - UC011)
        print("  Running Multi-Agent workflow pipeline directly...", flush=True)
        await workflow_engine.run_full_workflow(
            session_id=session_id,
            auto_search=False,
            max_papers=2,
            citation_style="IEEE"
        )
        print("[OK] Multi-Agent workflow completed successfully!", flush=True)

        # 7. Kiểm tra trạng thái tiến trình Workflow
        st_resp = await client.get(f"/api/v1/workflow/status/{session_id}")
        assert st_resp.status_code == 200, f"Get status failed: {st_resp.text}"
        st_data = st_resp.json()
        print(f"[OK] Final Workflow Status: {st_data['status']} (Progress: {st_data['progress_percentage']}%, Agent Runs: {len(st_data['agent_runs'])})", flush=True)

        # 8. Kiểm tra Báo cáo và Đánh giá Review (UC009, UC010)
        r_resp = await client.get(f"/api/v1/reports/session/{session_id}")
        assert r_resp.status_code == 200, f"Get reports failed: {r_resp.text}"
        reports = r_resp.json()
        assert len(reports) > 0, "No report was created"
        report_id = reports[0]["id"]
        print(f"[OK] Literature Review Report Generated (ID: {report_id}, Version: {reports[0]['version']})", flush=True)
        print(f"  Report Title: '{reports[0]['title']}', Review status: {reports[0]['review_status']}", flush=True)

        # 9. Xuất bản báo cáo sang Markdown, DOCX và PDF (UC012)
        for fmt in ["markdown", "docx", "pdf"]:
            exp_resp = await client.post(f"/api/v1/reports/{report_id}/export", json={"format": fmt})
            assert exp_resp.status_code == 200, f"Export {fmt} failed: {exp_resp.text}"
            print(f"[OK] Export UC012 to {fmt.upper()} successful ({len(exp_resp.content)} bytes)", flush=True)

    print("\n--- All PaperFlow Backend Verification Tests PASSED! ---\n", flush=True)

if __name__ == "__main__":
    asyncio.run(run_backend_tests())

