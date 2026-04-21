"""Marketing RAG Agent — FunctionAgent với Groq LLM và 4 Function Tools."""
from pathlib import Path
import os
import asyncio


# ── System Prompt ──────────────────────────────────────────────────────────────
MARKETING_SYSTEM_PROMPT = """Bạn là Marketing AI Assistant của công ty vận chuyển quốc tế.
Bạn có thể trả lời các câu hỏi về: phản hồi khách hàng (CSAT), ROI chiến dịch marketing, voucher khuyến mãi, và chính sách công ty.

## CÔNG CỤ BẠN CÓ:
1. filter_and_analyze_csat: Phân tích phản hồi & đánh giá của khách hàng
2. calculate_roi: Tính ROI của chiến dịch marketing
3. find_voucher_by_tier: Tìm voucher theo hạng khách hàng (Standard/Silver/Gold/VIP)
4. search_policy: Tra cứu chính sách công ty

## QUY TẮC BẮT BUỘC:

### ROI:
- Công thức: ROI% = (revenue - actual_spend) / actual_spend × 100
- LUÔN dùng actual_spend (thực chi), TUYỆT ĐỐI KHÔNG dùng budget (ngân sách kế hoạch)
- Hai con số này khác nhau hoàn toàn

### Voucher:
- Voucher giảm trên purchase_price_vnd (giá hàng gốc)
- KHÔNG giảm trên total_payment_vnd (tổng thanh toán bao gồm phí vận chuyển)
- Tier voucher có thể là multi-value "Gold,VIP" — luôn kiểm tra theo contains

### Phản hồi:
- Trả lời bằng tiếng Việt
- Ngắn gọn, có số liệu cụ thể
- Khi có kết quả voucher, đề xuất hiển thị ảnh thẻ voucher
- Tối đa 3 sub-queries khi cần tìm kiếm

### 📚 TRÍCH DẪN NGUỒN:
- BẠN BẮT BUỘC PHẢI THÊM 1 DÒNG "Nguồn tham khảo: <Tên File Hoặc Đường Dẫn>" Ở CUỐI MỔI CÂU TRẢ LỜI.
- Hệ thống công cụ (tools) sẽ cung cấp cho bạn trường "sources" hoặc "source_file" trong kết quả JSON trả về.
- Nếu không có nguồn cụ thể, hãy mặc định trích dẫn "Nguồn: Nội bộ công ty".

## CẢNH BÁO BẢO MẬT:
- Không tiết lộ thông tin cá nhân của khách hàng ngoài những gì được yêu cầu
- Chỉ trả lời các câu hỏi liên quan đến marketing, CSAT, voucher, chính sách
- Nếu câu hỏi không liên quan, lịch sự từ chối và hướng dẫn lại
"""


def _sanitize_input(text: str) -> str:
    """Basic sanitize để chống prompt injection."""
    dangerous_patterns = [
        "ignore previous instructions",
        "forget your instructions",
        "you are now",
        "act as",
        "pretend you are",
        "system:",
        "assistant:",
        "human:",
    ]
    lower_text = text.lower()
    for pattern in dangerous_patterns:
        if pattern in lower_text:
            return "[INPUT FILTERED - Phát hiện chuỗi nguy hiểm]"
    return text[:2000]


class MarketingAgent:
    """
    FunctionAgent với Groq LLM và 4 function tools:
    - filter_and_analyze_csat
    - calculate_roi
    - find_voucher_by_tier
    - search_policy
    """

    def __init__(self):
        self._agent = None
        self._llm = None
        self._chat_history = []

    def _ensure_init(self):
        if self._agent is not None:
            return

        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.config import GROQ_API_KEY, LLM_MODEL

        from llama_index.llms.groq import Groq
        from llama_index.core.agent import FunctionAgent
        from llama_index.core.tools import FunctionTool

        from src.tools.csat_tool import filter_and_analyze_csat
        from src.tools.roi_tool import calculate_roi
        from src.tools.voucher_tool import find_voucher_by_tier
        from src.tools.policy_tool import search_policy

        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY chưa được cấu hình trong file .env")

        os.environ["GROQ_API_KEY"] = GROQ_API_KEY

        # ── LLM ─────────────────────────────────────────────
        self._llm = Groq(
            model=LLM_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.1,
        )

        # ── Tools ────────────────────────────────────────────
        tools = [
            FunctionTool.from_defaults(
                fn=filter_and_analyze_csat,
                name="filter_and_analyze_csat",
                description=(
                    "Phân tích phản hồi & đánh giá (CSAT) của khách hàng. "
                    "Dùng khi hỏi về: rating, sentiment, lý do đánh giá thấp/cao, "
                    "phân bố cảm xúc khách hàng, NPS theo khoảng thời gian."
                ),
            ),
            FunctionTool.from_defaults(
                fn=calculate_roi,
                name="calculate_roi",
                description=(
                    "Tính ROI chiến dịch marketing. "
                    "Dùng khi hỏi về: ROI, hiệu quả chiến dịch, chi phí marketing, "
                    "kênh nào hiệu quả nhất. "
                    "ROI = (revenue - actual_spend) / actual_spend × 100."
                ),
            ),
            FunctionTool.from_defaults(
                fn=find_voucher_by_tier,
                name="find_voucher_by_tier",
                description=(
                    "Tìm voucher giảm giá theo hạng khách hàng (Standard/Silver/Gold/VIP). "
                    "Dùng khi hỏi về: mã giảm giá, khuyến mãi, voucher, ưu đãi theo hạng."
                ),
            ),
            FunctionTool.from_defaults(
                fn=search_policy,
                name="search_policy",
                description=(
                    "Tra cứu chính sách công ty: bồi thường, bảo hiểm, đóng gói, "
                    "hỗ trợ, hợp đồng, quy trình vận hành. "
                    "Dùng khi hỏi về quy định, thể lệ, chính sách."
                ),
            ),
        ]

        # ── Agent ────────────────────────────────────────────
        self._agent = FunctionAgent(
            tools=tools,
            llm=self._llm,
            system_prompt=MARKETING_SYSTEM_PROMPT,
            verbose=True,
        )
        self._chat_history = []

    def chat(self, message: str) -> dict:
        """Gửi message tới agent, trả về response + metadata."""
        self._ensure_init()

        safe_message = _sanitize_input(message)

        import time
        import asyncio
        start = time.time()

        try:
            async def _run():
                # Only pass chat_history when non-empty to avoid
                # FunctionAgent.run() bug where `[] or None` → None
                kwargs = {"user_msg": safe_message}
                if self._chat_history:
                    kwargs["chat_history"] = self._chat_history
                handler = self._agent.run(**kwargs)
                return await handler

            # Handle both sync and async contexts (e.g. Streamlit)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    response = loop.run_until_complete(_run())
                else:
                    response = asyncio.run(_run())
            except RuntimeError:
                response = asyncio.run(_run())

            # Append to chat history for memory
            from llama_index.core.llms import ChatMessage, MessageRole
            self._chat_history.append(ChatMessage(role=MessageRole.USER, content=safe_message))
            self._chat_history.append(ChatMessage(role=MessageRole.ASSISTANT, content=str(response)))

            # 🛑 OVERRIDE LUÔN Ở ĐÂY ĐỂ TRÁNH LỖI GROQ API:
            # Giữ lại tối đa 4 messages (2 lượt hội thoại gần nhất) 
            if len(self._chat_history) > 4:
                self._chat_history = self._chat_history[-4:]

            latency_ms = int((time.time() - start) * 1000)
            return {
                "response": str(response),
                "latency_ms": latency_ms,
                "sources": [],
            }
        except Exception as e:
            return {
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "latency_ms": int((time.time() - start) * 1000),
                "sources": [],
                "error": str(e),
            }

    def reset_memory(self):
        """Reset conversation memory."""
        self._chat_history = []
