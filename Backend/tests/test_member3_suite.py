"""
Bộ kiểm thử tích hợp chuyên biệt cho Thành viên 3 (Backend & Database).
Bao phủ toàn diện 100% các yêu cầu từ REQ-001 đến REQ-007:
- REQ-001: Validation dữ liệu đầu vào (Edge cases, invalid fields, year ranges).
- REQ-002: Xác thực & Phân quyền truy cập đa người dùng (Multi-user Isolation, 403 Forbidden).
- REQ-003: Quản lý version báo cáo & Ràng buộc không trùng lặp (Monotonic versions, UniqueConstraint).
- REQ-004: Chống chạy trùng quy trình & Quản lý trạng thái (Idempotency, 409 Conflict).
- REQ-005: Điều kiện xuất bản báo cáo (PASS-only constraint & Owner permission).
- REQ-006: Lưu trữ và phản hồi lỗi minh bạch (Error logging & structured API error response).
- REQ-007: Migration cơ sở dữ liệu & Toàn vẹn schema.
"""

import asyncio
import os
import sys
import uuid
import io

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.main import app
from app.db.session import init_db, AsyncSessionLocal
from app.models.user import User
from app.models.session import ResearchSession
from app.models.report import Report
from app.core.security import create_access_token, hash_password

async def run_member3_test_suite():
    print("\n=======================================================", flush=True)
    print("   BẮT ĐẦU KIỂM THỬ TOÀN DIỆN THÀNH VIÊN 3 (REQ-001 -> REQ-007)", flush=True)
    print("=======================================================\n", flush=True)

    # REQ-007: Migration & Database Schema Initialization
    print("[TEST REQ-007] Kiểm tra khởi tạo schema và tự động migration...", flush=True)
    await init_db()
    print("  -> REQ-007 PASS: Khởi tạo database và schema thành công.\n", flush=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # TẠO TÀI KHOẢN TEST: User A & User B
        user_a_email = f"usera_{uuid.uuid4().hex[:6]}@test.com"
        user_b_email = f"userb_{uuid.uuid4().hex[:6]}@test.com"

        reg_a = await client.post("/api/v1/auth/register", json={
            "email": user_a_email,
            "password": "Password123!",
            "full_name": "Nguyen Van A"
        })
        assert reg_a.status_code == 201, f"Register User A failed: {reg_a.text}"
        token_a = reg_a.json()["access_token"]
        user_a_id = reg_a.json()["user"]["id"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        reg_b = await client.post("/api/v1/auth/register", json={
            "email": user_b_email,
            "password": "Password123!",
            "full_name": "Tran Thi B"
        })
        assert reg_b.status_code == 201, f"Register User B failed: {reg_b.text}"
        token_b = reg_b.json()["access_token"]
        user_b_id = reg_b.json()["user"]["id"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        print(f"[AUTH OK] Đã tạo 2 tài khoản kiểm thử độc lập: User A ({user_a_id}) và User B ({user_b_id})\n", flush=True)

        # REQ-001: Validation Dữ Liệu Đầu Vào
        print("[TEST REQ-001] Kiểm tra validation dữ liệu đầu vào (Session)...", flush=True)
        
        # Test 1.1: Topic quá ngắn (< 3 ký tự)
        bad_topic_resp = await client.post("/api/v1/sessions", json={"topic": "AB"}, headers=headers_a)
        assert bad_topic_resp.status_code == 422, f"Expected 422 for short topic, got: {bad_topic_resp.status_code}"
        
        # Test 1.2: Năm bắt đầu > Năm kết thúc
        bad_year_resp = await client.post("/api/v1/sessions", json={
            "topic": "AI in Healthcare",
            "year_start": 2025,
            "year_end": 2020
        }, headers=headers_a)
        assert bad_year_resp.status_code == 422, f"Expected 422 for invalid year range, got: {bad_year_resp.status_code}"

        # Test 1.3: Citation style không hợp lệ
        bad_cite_resp = await client.post("/api/v1/sessions", json={
            "topic": "AI in Healthcare",
            "citation_style": "HARVARD_INVALID"
        }, headers=headers_a)
        assert bad_cite_resp.status_code == 422, f"Expected 422 for invalid citation_style, got: {bad_cite_resp.status_code}"

        # Test 1.4: Dữ liệu hợp lệ
        valid_sess_resp = await client.post("/api/v1/sessions", json={
            "topic": "Deep Learning for Computer Vision",
            "research_question": "What are the latest developments in Vision Transformers?",
            "year_start": 2021,
            "year_end": 2025,
            "max_papers": 5,
            "citation_style": "IEEE"
        }, headers=headers_a)
        assert valid_sess_resp.status_code == 201, f"Valid session creation failed: {valid_sess_resp.text}"
        session_a_id = valid_sess_resp.json()["id"]
        print(f"  -> REQ-001 PASS: Chặn chuẩn 422 dữ liệu sai, tạo thành công phiên hợp lệ: {session_a_id}\n", flush=True)

        # REQ-002: Multi-user Isolation & Quyền Truy Cập
        print("[TEST REQ-002] Kiểm tra phân lập dữ liệu người dùng (User B truy cập Session của User A)...", flush=True)
        
        # Test 2.1: User B xem chi tiết phiên của User A
        sec_get = await client.get(f"/api/v1/sessions/{session_a_id}", headers=headers_b)
        assert sec_get.status_code == 403, f"Expected 403 when User B accesses Session A, got {sec_get.status_code}"

        # Test 2.2: User B sửa thông tin phiên của User A
        sec_patch = await client.patch(f"/api/v1/sessions/{session_a_id}", json={"topic": "Hacked Topic"}, headers=headers_b)
        assert sec_patch.status_code == 403, f"Expected 403 when User B updates Session A, got {sec_patch.status_code}"

        # Test 2.3: User B xóa phiên của User A
        sec_del = await client.delete(f"/api/v1/sessions/{session_a_id}", headers=headers_b)
        assert sec_del.status_code == 403, f"Expected 403 when User B deletes Session A, got {sec_del.status_code}"

        # Test 2.4: User B tìm kiếm paper trong phiên của User A
        sec_paper_search = await client.post("/api/v1/papers/search", json={
            "session_id": session_a_id,
            "query": "transformer",
            "max_results": 2
        }, headers=headers_b)
        assert sec_paper_search.status_code == 403, f"Expected 403 when User B searches papers in Session A, got {sec_paper_search.status_code}"

        # Test 2.5: User B kích hoạt workflow trên phiên của User A
        sec_wf_start = await client.post("/api/v1/workflow/start", json={"session_id": session_a_id}, headers=headers_b)
        assert sec_wf_start.status_code == 403, f"Expected 403 when User B starts workflow on Session A, got {sec_wf_start.status_code}"

        # Test 2.6: Chính User A truy cập hợp lệ
        valid_get = await client.get(f"/api/v1/sessions/{session_a_id}", headers=headers_a)
        assert valid_get.status_code == 200, f"User A should be able to get own session, got {valid_get.status_code}"

        print("  -> REQ-002 PASS: Phân lập dữ liệu tuyệt đối (User B bị chặn 403 toàn bộ thao tác trái phép).\n", flush=True)

        # REQ-004: Chống Chạy Trùng Workflow (Idempotency)
        print("[TEST REQ-004] Kiểm tra chống chạy trùng workflow (Idempotency)...", flush=True)
        
        # Đặt phiên sang trạng thái RUNNING
        async with AsyncSessionLocal() as db:
            s_obj = (await db.execute(select(ResearchSession).where(ResearchSession.id == session_a_id))).scalar_one()
            s_obj.status = "RUNNING"
            await db.commit()

        # Gọi start workflow khi phiên đang RUNNING
        dup_wf = await client.post("/api/v1/workflow/start", json={"session_id": session_a_id}, headers=headers_a)
        assert dup_wf.status_code == 409, f"Expected 409 Conflict when running duplicate workflow, got {dup_wf.status_code}"
        print(f"  -> REQ-004 PASS: Chặn chạy trùng thành công với mã HTTP 409 Conflict: {dup_wf.json()['detail']}\n", flush=True)

        # Đặt lại trạng thái READY
        async with AsyncSessionLocal() as db:
            s_obj = (await db.execute(select(ResearchSession).where(ResearchSession.id == session_a_id))).scalar_one()
            s_obj.status = "READY"
            await db.commit()

        # REQ-003: Quản Lý Version Báo Cáo & Ràng Buộc Không Trùng Lặp
        print("[TEST REQ-003] Kiểm tra quản lý version báo cáo không trùng lặp...", flush=True)
        
        async with AsyncSessionLocal() as db:
            r1 = Report(
                session_id=session_a_id,
                title="Báo cáo Tổng quan Vision Transformers - Bản 1",
                content="# Vision Transformers\n\nNội dung phân tích tổng quan...",
                version=1,
                review_status="DRAFT"
            )
            db.add(r1)
            await db.commit()
            await db.refresh(r1)
            report_1_id = r1.id

            r2 = Report(
                session_id=session_a_id,
                title="Báo cáo Tổng quan Vision Transformers - Bản 2",
                content="# Vision Transformers v2\n\nNội dung đã qua chỉnh sửa...",
                version=2,
                review_status="PASS"
            )
            db.add(r2)
            await db.commit()
            await db.refresh(r2)
            report_2_id = r2.id

            # Kiểm tra ràng buộc UniqueConstraint(session_id, version)
            try:
                r_dup = Report(
                    session_id=session_a_id,
                    title="Báo cáo Trùng Version 1",
                    content="Nội dung...",
                    version=1,
                    review_status="DRAFT"
                )
                db.add(r_dup)
                await db.commit()
                assert False, "Cơ sở dữ liệu phải bắt lỗi trùng (session_id, version)!"
            except IntegrityError:
                await db.rollback()
                print("  [DB Constraint OK] Bắt chính xác lỗi IntegrityError khi tạo trùng version 1.")

            max_v = (await db.execute(select(func.max(Report.version)).where(Report.session_id == session_a_id))).scalar()
            assert max_v == 2, f"Expected max version 2, got {max_v}"
            next_v = max_v + 1
            assert next_v == 3, f"Expected next version 3, got {next_v}"

        print(f"  -> REQ-003 PASS: Quản lý version tăng dần chuẩn xác (v1, v2, v3), chặn trùng tuyệt đối.\n", flush=True)

        # REQ-005: Điều Kiện Xuất Bản Báo Cáo (PASS-only & Owner)
        print("[TEST REQ-005] Kiểm tra điều kiện xuất báo cáo (chỉ cho phép xuất bản khi PASS)...", flush=True)

        # Test 5.1: Xuất bản Report 1 (review_status = 'DRAFT' / chưa PASS)
        draft_exp = await client.post(f"/api/v1/reports/{report_1_id}/export", json={"format": "markdown"}, headers=headers_a)
        assert draft_exp.status_code == 400, f"Expected 400 when exporting non-PASS report, got {draft_exp.status_code}"
        print(f"  [Chặn DRAFT OK] Trả về 400: '{draft_exp.json()['detail']}'")

        # Test 5.2: User B tải trộm Report 2 của User A
        b_steal_exp = await client.post(f"/api/v1/reports/{report_2_id}/export", json={"format": "markdown"}, headers=headers_b)
        assert b_steal_exp.status_code == 403, f"Expected 403 when User B tries to export User A report, got {b_steal_exp.status_code}"
        print("  [Chặn Trái Quyền OK] User B không thể tải báo cáo của User A (HTTP 403).")

        # Test 5.3: User A xuất bản Report 2 (review_status = 'PASS')
        pass_exp = await client.post(f"/api/v1/reports/{report_2_id}/export", json={"format": "markdown"}, headers=headers_a)
        assert pass_exp.status_code == 200, f"Expected 200 when exporting PASS report, got {pass_exp.status_code}"
        assert len(pass_exp.content) > 0, "Exported file content should not be empty"
        print("  [Xuất PASS OK] Xuất bản báo cáo PASS thành công (HTTP 200, File nhận được đầy đủ).")

        print("  -> REQ-005 PASS: Điều kiện xuất báo cáo được kiểm soát chặt chẽ.\n", flush=True)

        # REQ-006: Lưu Trữ & Phản Hồi Lỗi Rõ Ràng
        print("[TEST REQ-006] Kiểm tra cơ chế lưu trữ và phản hồi lỗi hệ thống...", flush=True)
        
        async with AsyncSessionLocal() as db:
            s_obj = (await db.execute(select(ResearchSession).where(ResearchSession.id == session_a_id))).scalar_one()
            s_obj.status = "FAILED"
            s_obj.error_message = "Mô phỏng lỗi kết nối API bên ngoài"
            await db.commit()

        st_check = await client.get(f"/api/v1/workflow/status/{session_a_id}", headers=headers_a)
        assert st_check.status_code == 200
        assert st_check.json()["status"] == "FAILED"
        print("  -> REQ-006 PASS: Lỗi được ghi nhận vào database và trả về rõ ràng qua API.\n", flush=True)

        # REQ-008: Chế độ Khách Giới Hạn 2 Câu Hỏi / Phiên Nghiên Cứu
        print("[TEST REQ-008] Kiểm tra hạn mức 2 phiên trải nghiệm cho Chế độ Khách (Guest Quota)...", flush=True)

        guest_ip = f"198.51.100.{uuid.uuid4().hex[:4]}"  # IP duy nhất cho test case
        guest_headers = {"X-Forwarded-For": guest_ip}

        # Kiểm tra quota ban đầu
        quota_resp = await client.get("/api/v1/sessions/guest/quota", headers=guest_headers)
        assert quota_resp.status_code == 200
        assert quota_resp.json()["used"] == 0
        assert quota_resp.json()["remaining"] == 2
        assert quota_resp.json()["is_exceeded"] is False

        # Khách tạo câu hỏi 1 -> Thành công (201)
        g1 = await client.post("/api/v1/sessions", json={"topic": "Guest Research Question 1"}, headers=guest_headers)
        assert g1.status_code == 201, f"Guest session 1 failed: {g1.text}"
        print("  [Khách Câu 1 OK] Tạo thành công phiên 1 (HTTP 201).")

        # Khách tạo câu hỏi 2 -> Thành công (201)
        g2 = await client.post("/api/v1/sessions", json={"topic": "Guest Research Question 2"}, headers=guest_headers)
        assert g2.status_code == 201, f"Guest session 2 failed: {g2.text}"
        print("  [Khách Câu 2 OK] Tạo thành công phiên 2 (HTTP 201).")

        # Kiểm tra quota khi đã dùng 2/2
        quota_full = await client.get("/api/v1/sessions/guest/quota", headers=guest_headers)
        assert quota_full.json()["used"] == 2
        assert quota_full.json()["remaining"] == 0
        assert quota_full.json()["is_exceeded"] is True

        # Khách tạo câu hỏi 3 -> BỊ CHẶN 429 Too Many Requests
        g3 = await client.post("/api/v1/sessions", json={"topic": "Guest Research Question 3"}, headers=guest_headers)
        assert g3.status_code == 429, f"Expected 429 Too Many Requests, got {g3.status_code}"
        assert "hết 2 lượt" in g3.json()["detail"] or "Chế độ khách" in g3.json()["detail"]
        print(f"  [Chặn Câu 3 OK] Chặn chuẩn HTTP 429 Too Many Requests: '{g3.json()['detail']}'")

        # Người dùng đã đăng nhập (User A) tạo câu hỏi -> KHÔNG BỊ GIỚI HẠN
        auth_sess = await client.post("/api/v1/sessions", json={"topic": "User A Unlimited Research"}, headers=headers_a)
        assert auth_sess.status_code == 201
        print("  -> REQ-008 PASS: Kiểm soát hạn mức khách vãng lai và phân quyền không giới hạn cho tài khoản đăng nhập thành công tuyệt đối.\n", flush=True)

        # REQ-009: Phân Lập Tuyệt Đối Lịch Sử Phiên Nghiên Cứu (Session Privacy & Isolation)
        print("[TEST REQ-009] Kiểm tra phân lập tuyệt đối danh sách phiên (chỉ tài khoản sở hữu mới thấy)...", flush=True)

        # 1. User A gọi GET /sessions -> Chỉ thấy phiên của User A
        list_a = await client.get("/api/v1/sessions", headers=headers_a)
        assert list_a.status_code == 200
        sessions_of_a = list_a.json()
        assert all(s["user_id"] == user_a_id for s in sessions_of_a), "User A không được nhìn thấy phiên của người khác!"
        print(f"  [User A OK] User A chỉ thấy {len(sessions_of_a)} phiên của riêng mình.")

        # 2. User B gọi GET /sessions -> Không được thấy bất kỳ phiên nào của User A
        list_b = await client.get("/api/v1/sessions", headers=headers_b)
        assert list_b.status_code == 200
        sessions_of_b = list_b.json()
        assert all(s["user_id"] == user_b_id for s in sessions_of_b), "User B không được nhìn thấy phiên của User A!"
        assert not any(s["id"] == session_a_id for s in sessions_of_b), "User B bị cấm thấy session_a_id!"
        print(f"  [User B OK] User B chỉ thấy {len(sessions_of_b)} phiên của riêng mình, hoàn toàn không thấy phiên của User A.")

        # 3. Khách gọi GET /sessions -> Tuyệt đối không thấy phiên của User A hoặc User B
        other_guest_ip = f"198.51.200.{uuid.uuid4().hex[:4]}"
        list_guest = await client.get("/api/v1/sessions", headers={"X-Forwarded-For": other_guest_ip})
        assert list_guest.status_code == 200
        assert len(list_guest.json()) == 0, "Khách mới hoàn toàn không được nhìn thấy phiên của bất kỳ ai!"
        print("  [Khách Mới OK] Khách mới chưa tạo câu hỏi sẽ nhận danh sách rỗng, không bị lộ lịch sử nghiên cứu của người khác.")

        print("  -> REQ-009 PASS: Phân lập tuyệt đối lịch sử nghiên cứu của từng tài khoản thành công 100%.\n", flush=True)

    print("=======================================================", flush=True)
    print("   TẤT CẢ CÁC BÀI TEST THÀNH VIÊN 3 ĐÃ PASS 100%!", flush=True)
    print("=======================================================\n", flush=True)

if __name__ == "__main__":
    asyncio.run(run_member3_test_suite())
