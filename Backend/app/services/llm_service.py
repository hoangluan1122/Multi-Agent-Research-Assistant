"""
Service giao tiếp với các mô hình ngôn ngữ lớn (Large Language Models - LLM).
Hỗ trợ Google GenAI SDK (Gemini 2.5/3.7), OpenAI API / OpenRouter / Ollama và cơ chế Fallback học thuật thông minh.
"""

import json
import re
import asyncio
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

import time
logger = logging.getLogger("paperflow.llm")

class LLMService:
    """
    Lớp dịch vụ trung tâm xử lý gọi mô hình AI:
    - Quản lý khởi tạo client cho Gemini (Google GenAI) và OpenAI.
    - Cung cấp phương thức sinh văn bản (generate_text) với timeout và fallback an toàn.
    - Cung cấp phương thức sinh cấu trúc JSON (generate_json) có kiểm tra cú pháp.
    - Cung cấp bộ sinh dữ liệu giả lập chất lượng cao (Heuristic Mock) khi không có API Key.
    """
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.default_model = settings.DEFAULT_LLM_MODEL
        self._gemini_lock = asyncio.Lock()
        self._last_gemini_request = 0.0
        self._init_clients()

    def _init_clients(self):
        """Khởi tạo các Client kết nối API Google GenAI hoặc OpenAI nếu cấu hình API Key."""
        self.genai_client = None
        self.openai_client = None

        # Khởi tạo Google GenAI Client
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Google GenAI client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI client: {e}")

            try:
                import google.generativeai as gai
                gai.configure(api_key=settings.GEMINI_API_KEY)
                self.legacy_genai = gai
                logger.info("Legacy google.generativeai initialized as backup.")
            except Exception as e:
                logger.warning(f"Failed to initialize legacy google.generativeai: {e}")

        # Khởi tạo OpenAI Client
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
                logger.info("OpenAI client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")


    async def _call_gemini(self, model: str, prompt: str, config: Any) -> Any:
        """Gọi Gemini theo hàng đợi chung để không vượt giới hạn request/phút."""
        gemini_client: Any = self.genai_client
        if gemini_client is None:
            raise RuntimeError("Gemini client chưa được khởi tạo.")

        async with self._gemini_lock:
            elapsed = time.monotonic() - self._last_gemini_request
            wait_seconds = 13.0 - elapsed  # khoảng 4–5 request/phút
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            last_error: Optional[Exception] = None
            for attempt in range(3):
                try:
                    self._last_gemini_request = time.monotonic()
                    return await asyncio.wait_for(
                        gemini_client.aio.models.generate_content(
                            model=model,
                            contents=prompt,
                            config=config,
                        ),
                        timeout=90.0,
                    )
                except Exception as error:
                    last_error = error
                    message = str(error)
                    is_rate_limited = any(token in message for token in (
                        "429", "RESOURCE_EXHAUSTED", "rate limit"
                    ))
                    if not is_rate_limited or attempt == 2:
                        break
                    retry_after = 30 * (attempt + 1)
                    logger.warning("Gemini rate-limited; retrying in %ss: %s", retry_after, message)
                    await asyncio.sleep(retry_after)

            raise RuntimeError(f"Gemini không phản hồi được: {last_error}")

    # @trace: REQ-013
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        model: Optional[str] = None,
        allow_mock: bool = True,
    ) -> str:
        """
        Sinh nội dung từ provider đã được cấu hình.

        Khi provider là Gemini/OpenAI, lỗi phải được trả về cho workflow.
        Tuyệt đối không thay lỗi bằng báo cáo mẫu vì nội dung mẫu có thể lạc đề.
        """
        target_model = model or self.default_model

        # 1. Gemini: chỉ gọi model được cấu hình, không thử các model cũ.
        api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        if self.provider == "gemini":
            if not api_key or api_key.startswith("your_") or self.genai_client is None:
                raise RuntimeError("Gemini chưa được cấu hình API key hợp lệ.")

            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instruction,
            )
            response = await self._call_gemini(
                model=target_model,
                prompt=prompt,
                config=config,
            )
            response_text = getattr(response, "text", None)
            if response_text and response_text.strip():
                return response_text.strip()
            raise RuntimeError("Gemini trả về phản hồi rỗng; không tạo báo cáo mẫu.")

        # 2. OpenAI hoặc API tương thích OpenAI
        if self.provider in {"openai", "openrouter", "groq"} and self.openai_client and settings.OPENAI_API_KEY:
            try:
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                response = await asyncio.wait_for(
                    self.openai_client.chat.completions.create(
                        model=target_model if "gpt" in target_model else "gpt-4o-mini",
                        messages=messages,
                        temperature=temperature,
                    ),
                    timeout=15.0
                )
                content = response.choices[0].message.content or ""
                if content.strip():
                    return content.strip()
                raise RuntimeError("LLM trả về phản hồi rỗng.")
            except Exception as e:
                raise RuntimeError(f"Không thể gọi {self.provider}: {e}") from e

        # 3. Mock chỉ dành cho demo offline do người dùng chủ động cấu hình.
        if self.provider == "mock":
            if not allow_mock:
                raise RuntimeError("Chế độ mock không được phép cho thao tác này.")
            logger.warning("Using mock LLM output because LLM_PROVIDER=mock.")
            return self._mock_generation(prompt, system_instruction)

        raise RuntimeError(f"LLM provider '{self.provider}' chưa được cấu hình đúng hoặc thiếu API key.")

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        model: Optional[str] = None,
        allow_mock: bool = True,
    ) -> Dict[str, Any]:
        """
        Sinh kết quả có cấu trúc JSON từ LLM:
        - Bổ sung chỉ thị bắt buộc định dạng JSON thuần.
        - Làm sạch các ký tự markdown bao quanh (```json ... ```).
        - Parse kết quả sang Python Dictionary.
        """
        sys_prompt = (system_instruction or "") + "\n\nCRITICAL: Respond ONLY with valid JSON. No markdown formatting, no backticks, no extra text."
        raw_text = await self.generate_text(
            prompt,
            system_instruction=sys_prompt,
            temperature=temperature,
            model=model,
            allow_mock=allow_mock,
        )
        
        # Loại bỏ các thẻ code block nếu LLM bao bọc chuỗi JSON
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON directly from LLM: {raw_text[:100]}... Returning fallback dictionary.")
            return {"raw_response": raw_text}

    # @trace: REQ-013
    def _mock_generation(self, prompt: str, system_instruction: Optional[str]) -> str:
        """
        Cơ chế sinh phản hồi giả lập giàu ngữ cảnh học thuật:
        Tự động nhận diện chính xác mục đích prompt (soạn báo cáo tổng quan, phân tích paper, review, dịch thuật, từ khóa)
        và bám sát chủ đề người dùng nhập để không bao giờ trả về JSON thô hay lạc đề.
        """
        prompt_lower = prompt.lower()

        # 1. SOẠN THẢO BÁO CÁO LITERATURE REVIEW (WritingAgent)
        # BẮT BUỘC ĐẶT LÊN ĐẦU TIÊN để tránh các từ khóa 'method' / 'analyze' cướp luồng trả về JSON
        if (
            "literature review" in prompt_lower
            or "scientific academic researcher" in prompt_lower
            or "viết bài" in prompt_lower
            or "tổng quan nghiên cứu" in prompt_lower
            or ("requirements:" in prompt_lower and "giới thiệu" in prompt_lower)
        ):
            match = re.search(r"topic:\s*([^\n\r]+)", prompt, flags=re.IGNORECASE)
            topic = match.group(1).strip() if match else "Chủ đề nghiên cứu khoa học"

            return (
                f"## 1. Giới thiệu & Tổng quan bài toán\n\n"
                f"Nghiên cứu về **{topic}** là một trong những lĩnh vực trọng tâm nhận được sự quan tâm sâu sắc từ cộng đồng khoa học và y tế cộng đồng. "
                f"Các công bố học thuật và nghiên cứu dịch tễ học gần đây đã chỉ ra rõ rệt những tác động phức tạp, nhiều tầng nấc và nguy cơ tiềm ẩn đối với sức khỏe con người [1]. "
                f"Mục tiêu của bài tổng quan tài liệu (Literature Review) này là tổng hợp có hệ thống các phát hiện thực nghiệm, phân tích cơ chế sinh học - bệnh lý học, "
                f"và đánh giá định lượng các hệ quả lâu dài nhằm cung cấp cơ sở dữ liệu vững chắc cho các nghiên cứu tiếp nối [2].\n\n"
                f"## 2. Phân tích Phương pháp & Cơ chế Tác động\n\n"
                f"Các công trình nghiên cứu sử dụng nhiều phương pháp luận đa dạng: từ khảo sát đoàn hệ quy mô lớn (cohort studies), phân tích mẫu bệnh phẩm lâm sàng, "
                f"đến các mô hình định lượng chỉ thị sinh học (biomarkers) và phân tích thống kê đa biến [1]. "
                f"Các bằng chứng thực nghiệm khẳng định rằng các độc chất, hợp chất bay hơi và nicotin tác động trực tiếp lên hệ tuần hoàn, gây tổn thương niêm mạc biểu mô phế quản, "
                f"làm gia tăng phản ứng viêm toàn thân và đẩy nhanh quá trình xơ vữa thành mạch [2]. "
                f"Các chỉ số chức năng hô hấp (như FEV1/FVC) và nồng độ các chất chuyển hóa trong huyết thanh đóng vai trò là những thước đo định lượng khách quan cho mức độ tổn hại [3].\n\n"
                f"## 3. Bảng Ma trận So sánh Đối chiếu\n\n"
                f"Các công trình nghiên cứu tiêu biểu về **{topic}** được tổng hợp, phân loại theo phương pháp tiếp cận, đối tượng mẫu và các chỉ số đo lường then chốt để cung cấp góc nhìn so sánh đa chiều [1], [2].\n\n"
                f"## 4. Thảo luận & Hạn chế Nghiên cứu\n\n"
                f"Mặc dù mối quan hệ nhân quả giữa **{topic}** và các biến chứng bệnh lý nguy hiểm (ung thư, suy hô hấp mạn tính, tai biến tim mạch) đã được chứng minh rõ rệt, "
                f"các nghiên cứu hiện tại vẫn tồn tại một số hạn chế: khó khăn trong việc cô lập hoàn toàn các yếu tố nhiễu môi trường, lối sống, "
                f"và sự khác biệt về cơ địa nhạy cảm giữa các nhóm đối tượng phơi nhiễm chủ động và thụ động [2]. "
                f"Dữ liệu theo dõi tiến trình hồi phục sau can thiệp vẫn cần được mở rộng theo thời gian [3].\n\n"
                f"## 5. Hướng phát triển & Khuyến nghị Tương lai\n\n"
                f"Để nâng cao hiệu quả phòng ngừa và điều trị, các nghiên cứu trong tương lai cần tập trung vào việc ứng dụng công nghệ phân tích gen để phát hiện sớm các đột biến tế bào, "
                f"đồng thời đẩy mạnh phát triển các liệu pháp can thiệp hỗ trợ phục hồi mô cơ quan bị tổn thương. "
                f"Song song đó, việc củng cố các chính sách y tế công cộng và chiến dịch truyền thông giáo dục sức khỏe tiếp tục là trụ cột không thể thiếu [1], [2].\n\n"
                f"## 6. Danh mục Tài liệu Tham khảo\n"
            )

        # 2. PHÂN TÍCH CHI TIẾT TỪNG BÀI BÁO (ReadingAgent - Cấu trúc JSON 5 thành phần)
        elif (
            "5 khía cạnh" in prompt_lower
            or "cấu trúc json" in prompt_lower
            or ("method" in prompt_lower and "dataset" in prompt_lower and "metrics" in prompt_lower)
            or ("analyze" in prompt_lower and "abstract:" in prompt_lower)
        ):
            p_match = re.search(r"title:\s*([^\n\r]+)", prompt, flags=re.IGNORECASE)
            p_title = p_match.group(1).strip() if p_match else "Công trình nghiên cứu"

            if any(k in prompt_lower for k in ["điện thoại", "smartphone", "mobile phone", "screen time", "màn hình"]):
                return json.dumps({
                    "method": "Khảo sát tiến cứu và theo dõi thời gian màn hình kết hợp thang đo tâm lý chuẩn (PSQI, DASS-21)",
                    "dataset": "Tập dữ liệu theo dõi hành vi giới trẻ (n=8,200 thanh thiếu niên theo dõi 3 năm)",
                    "metrics": "Thời gian sử dụng (4.6h/ngày), Tỷ lệ rối loạn giấc ngủ (+34.2%), Nguy cơ lo âu (OR: 2.15, p < 0.001)",
                    "results": "Thời gian sử dụng điện thoại kéo dài vào ban đêm tương quan thuận rõ rệt với tình trạng mất ngủ, suy giảm chú ý và căng thẳng.",
                    "limitations": "Cần thêm dữ liệu cảm biến đo đạc tự động để giảm thiểu sai số tự báo cáo từ người tham gia.",
                    "summary": "Nghiên cứu cung cấp chứng cứ định lượng vững chắc về tác động tiêu cực của việc lạm dụng điện thoại đến sức khỏe thể chất và tinh thần."
                })
            elif any(k in prompt_lower for k in ["thuốc lá", "smoking", "tobacco", "nicotine", "lung", "health", "sức khỏe"]):
                return json.dumps({
                    "method": "Khảo sát lâm sàng tiến cứu kết hợp phân tích chỉ thị sinh học huyết thanh (Serum Cotinine & Inflammatory Biomarkers)",
                    "dataset": "Bộ dữ liệu giám sát y tế công cộng (n=12,500 đối tượng theo dõi 5 năm)",
                    "metrics": "Tỷ số chênh rủi ro (OR: 2.85), Suy giảm FEV1/FVC (-18.4%), nồng độ COHb huyết tương",
                    "results": "Xác nhận tổn thương tế bào biểu mô phế quản và tăng nguy cơ xơ vữa động mạch tỷ lệ thuận với thời gian phơi nhiễm.",
                    "limitations": "Chưa kiểm soát hoàn toàn các yếu tố nhiễu do phơi nhiễm thụ động ngoài môi trường sống.",
                    "summary": f"Nghiên cứu cung cấp bằng chứng định lượng vững chắc về mức độ tổn thương của khói thuốc lên cơ thể con người."
                })
            else:
                return json.dumps({
                    "method": f"Phương pháp phân tích thực nghiệm và đánh giá định lượng cho {p_title[:60]}",
                    "dataset": "Tập dữ liệu nghiên cứu tiêu chuẩn (Standard Research Dataset)",
                    "metrics": "Độ chính xác: 94.2%, F1-Score: 91.8%, p < 0.01",
                    "results": "Các chỉ số đo lường cho thấy hiệu quả vượt trội và tính nhất quán cao trên các bài thử nghiệm so sánh.",
                    "limitations": "Quy mô mẫu cần được mở rộng trên nhiều điều kiện thử nghiệm đa dạng hơn.",
                    "summary": f"Công trình trình bày những phát hiện học thuật có giá trị thực tiễn cao trong lĩnh vực nghiên cứu."
                })

        # 3. THẨM ĐỊNH CHẤT LƯỢNG (ReviewAgent)
        elif "review" in prompt_lower and "criteria" in prompt_lower or "score" in prompt_lower:
            return json.dumps({
                "score": 94.0,
                "status": "PASS",
                "issues": [
                    {"type": "citation_coverage", "description": "Tỷ lệ phủ trích dẫn đạt chuẩn học thuật cao, các luận điểm đều có căn cứ vững chắc.", "severity": "low"}
                ],
                "feedback": "Báo cáo tổng quan được biên soạn chặt chẽ, bố cục 6 phần rõ ràng, các phân tích phương pháp và số liệu đối chiếu chuẩn xác.",
                "hallucination_risks": [],
                "citation_coverage": 0.96
            })

        # 4. CHUYỂN NGỮ TIÊU ĐỀ & TÓM TẮT BÀI BÁO (SearchAgent Translation)
        elif "translate" in prompt_lower or "dịch" in prompt_lower or "title_vi" in prompt_lower:
            t_match = re.search(r"title:\s*([^\n\r]+)", prompt, flags=re.IGNORECASE)
            raw_t = t_match.group(1).strip() if t_match else "Tài liệu học thuật"

            trans_title = raw_t
            replacements = [
                ("Recent Advances in", "Các Tiến Bộ Gần Đây Trong Nghiên Cứu Về"),
                ("A Comprehensive Survey and Benchmark", "Báo Cáo Tổng Quan và Đánh Giá Chuẩn"),
                ("Multi-Agent Collaborative Frameworks for", "Khung Phối Hợp Đa Tác Tử Cho"),
                ("Empirical Evaluation and Limitations of Modern Approaches in", "Đánh Giá Thực Nghiệm và Hạn Chế Của Các Phương Pháp Trong"),
                ("Empirical Evaluation and Limitations of Modern Methodologies in", "Đánh Giá Thực Nghiệm và Giới Hạn Phương Pháp Trong"),
                ("Longitudinal Assessment of", "Đánh Giá Theo Thời Gian Dài Về"),
                ("Clinical and Behavioral Outcomes", "Kết Quả Lâm Sàng và Hành Vi"),
                ("Systematic Review and Meta-Analysis on the Impacts of", "Tổng Quan Hệ Thống và Phân Tích Tổng Hợp Về Tác Động Của"),
                ("Modern Analytical Approaches and Policy Interventions in", "Các Phương Pháp Tiếp Cận Phân Tích Hiện Đại và Can Thiệp Chính Sách Trong"),
                ("Cross-Sectional Investigation of Environmental and Biological Factors in", "Khảo Sát Cắt Ngang Về Các Yếu Tố Môi Trường và Sinh Học Trong"),
                ("Statistical Modeling and Risk Prediction Frameworks for", "Mô Hình Thống Kê và Khung Dự Đoán Rủi Ro Cho"),
                ("Technological and Social Perspectives on", "Góc Nhìn Công Nghệ và Xã Hội Về"),
                ("Future Horizons in", "Triển Vọng Tương Lai Trong"),
                ("Health Effects of", "Tác Động Sức Khỏe Của"),
                ("Adverse Effects of", "Tác Hại Tiêu Cực Của"),
                ("Smartphone", "Điện Thoại Thông Minh"),
                ("Mobile Phone", "Điện Thoại Di Động"),
                ("Screen Time", "Thời Gian Sử Dụng Màn Hình"),
                ("Mental Health", "Sức Khỏe Tâm Thần"),
                ("Adolescents", "Thanh Thiếu Niên"),
                ("Tobacco Smoking", "Hút Thuốc Lá"),
                ("Smoking", "Hút Thuốc Lá"),
                ("Nicotine", "Nicotin"),
                ("Human Body", "Cơ Thể Con Người"),
                ("Cardiovascular Disease", "Bệnh Tim Mạch"),
            ]
            for en_term, vi_term in replacements:
                trans_title = re.sub(re.escape(en_term), vi_term, trans_title, flags=re.IGNORECASE)

            trans_abstract = f"Bài báo này phân tích có hệ thống các khía cạnh liên quan đến {trans_title.lower()}, cung cấp các phân tích thực nghiệm và đánh giá khoa học chuyên sâu."
            return json.dumps({
                "title_vi": trans_title,
                "abstract_vi": trans_abstract
            })

        # 5. TRÍCH XUẤT TỪ KHÓA TÌM KIẾM (SearchAgent Keyword Extraction)
        elif "keywords" in prompt_lower or "extract" in prompt_lower:
            return self._mock_keyword_extraction(prompt)

        # 6. TÓM TẮT & TỔNG HỢP MA TRẬN (SummarizationAgent)
        elif "summary" in prompt_lower or "synthesize" in prompt_lower or "so sánh" in prompt_lower:
            return (
                "Tổng hợp các công trình nghiên cứu cho thấy sự đồng thuận cao về các rủi ro sức khỏe nghiêm trọng. "
                "Các phương pháp đánh giá định lượng ngày càng hoàn thiện, giúp xác định chính xác các giai đoạn tổn thương sinh học "
                "và mở ra các hướng tiếp cận can thiệp y tế hiệu quả hơn."
            )

        # MẶC ĐỊNH
        else:
            return (
                "## Tổng quan Nghiên cứu\n\n"
                "Nội dung nghiên cứu đã được tổng hợp có hệ thống từ các công bố khoa học gần đây, "
                "làm rõ các phương pháp luận, kết quả phân tích định lượng và định hướng phát triển trong tương lai."
            )

    # @trace: REQ-013
    def _mock_keyword_extraction(self, prompt: str) -> str:
        """Trích xuất từ khóa học thuật tiếng Anh phù hợp từ chủ đề người dùng nhập."""
        match = re.search(r"topic or question:\s*'([^']+)'", prompt, flags=re.IGNORECASE)
        topic = match.group(1) if match else prompt
        
        # Nhận diện chủ đề tiếng Việt phổ biến để chuyển sang từ khóa tiếng Anh học thuật cho ArXiv / Crossref
        topic_lower = topic.lower()
        if "tuyến tiền liệt" in topic_lower or "tiền liệt tuyến" in topic_lower or "prostate" in topic_lower:
            return "prostate cancer prostate-specific antigen diagnosis therapy"
        if "tiền" in topic_lower or "tiền tệ" in topic_lower or "tài chính" in topic_lower or "ngân hàng" in topic_lower:
            return "money currency monetary policy banking finance economics"
        if "ma tuý" in topic_lower or "ma túy" in topic_lower or "chất gây nghiện" in topic_lower:
            return "illicit drug abuse addiction narcotics public health"
        if "bảo hiểm" in topic_lower:
            return "insurance risk management deposit insurance social security"
        if "điện thoại" in topic_lower or "smartphone" in topic_lower or "màn hình" in topic_lower:
            return "smartphone screen time mental health cognitive effects adolescents"
        if "mạng xã hội" in topic_lower or "social media" in topic_lower:
            return "social media screen time depression anxiety adolescents"
        if "thuốc lá" in topic_lower or "smoking" in topic_lower or "tobacco" in topic_lower:
            return "tobacco smoking nicotine adverse health effects pulmonary cardiovascular"
        if "ung thư" in topic_lower or "cancer" in topic_lower:
            return "cancer oncology clinical trials diagnosis therapy"
        if "tim mạch" in topic_lower or "heart" in topic_lower or "cardio" in topic_lower:
            return "cardiovascular disease heart pathology clinical biomarkers"
        if "ô nhiễm" in topic_lower or "không khí" in topic_lower:
            return "air pollution environmental exposure respiratory health"
        if "trí tuệ nhân tạo" in topic_lower or "ai" in topic_lower or "học máy" in topic_lower:
            return "artificial intelligence machine learning deep neural networks"

        tokens = re.findall(r"[\w-]+", topic_lower, flags=re.UNICODE)
        stopwords = {
            "a", "an", "and", "are", "as", "for", "from", "given", "in", "of", "or",
            "question", "research", "terms", "the", "this", "topic", "what", "with",
            "của", "và", "các", "những", "cho", "trong", "đến", "về", "là"
        }
        keywords = [token for token in tokens if len(token) > 1 and token not in stopwords]
        return " ".join(keywords[:5]) or topic.strip()


# Khởi tạo singleton instance cho LLMService
llm_service = LLMService()

