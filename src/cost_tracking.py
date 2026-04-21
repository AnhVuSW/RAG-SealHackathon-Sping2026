"""
Cost Tracking — Langfuse integration + session metrics.

Theo dõi:
- Token per request (input/output)
- Latency per request
- Cost per request và per service type (LLM / Embedding / Reranking)
- Per-tool usage và cost breakdown
- Session totals + estimated daily/monthly cost
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import time


# ── Groq pricing (tham khảo, free tier = $0 nhưng vẫn track) ─────────────────
GROQ_PRICE_PER_1K_INPUT = 0.00005    # $0.05/1M input tokens
GROQ_PRICE_PER_1K_OUTPUT = 0.00008   # $0.08/1M output tokens

# Phân bổ token theo service type (ước tính)
# LLM synthesis: ~70% tokens, Embedding: ~20%, Reranking: ~10%
SERVICE_SPLIT = {"llm": 0.70, "embedding": 0.20, "reranking": 0.10}


@dataclass
class RequestMetrics:
    query: str
    response_preview: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float
    tools_used: list
    tool_name: str = ""          # Tool chính được gọi trong request
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class CostTracker:
    """
    Track costs cho session hiện tại.
    Lưu trong Streamlit session_state nếu dùng trong UI.
    """

    def __init__(self):
        self.requests: list[RequestMetrics] = []
        self.tool_call_counts: dict = {}     # tool → số lần gọi
        self.tool_cost_map: dict = {}        # tool → tổng cost
        self.tool_token_map: dict = {}       # tool → tổng tokens
        self._session_start = time.time()

    def record(
        self,
        query: str,
        response: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        tools_used: Optional[list] = None,
        tool_name: str = "",
    ) -> RequestMetrics:
        """Ghi lại metrics của 1 request."""
        tools_used = tools_used or []

        cost = (
            input_tokens / 1000 * GROQ_PRICE_PER_1K_INPUT +
            output_tokens / 1000 * GROQ_PRICE_PER_1K_OUTPUT
        )

        metrics = RequestMetrics(
            query=query[:100],
            response_preview=response[:150],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=round(cost, 6),
            tools_used=tools_used,
            tool_name=tool_name,
        )

        self.requests.append(metrics)

        # Track per-tool counts & cost
        effective_tool = tool_name or (tools_used[0] if tools_used else "direct_answer")
        self.tool_call_counts[effective_tool] = self.tool_call_counts.get(effective_tool, 0) + 1
        self.tool_cost_map[effective_tool] = round(
            self.tool_cost_map.get(effective_tool, 0.0) + cost, 6
        )
        self.tool_token_map[effective_tool] = (
            self.tool_token_map.get(effective_tool, 0) + input_tokens + output_tokens
        )

        return metrics

    # ── Aggregates ────────────────────────────────────────────

    @property
    def total_requests(self) -> int:
        return len(self.requests)

    @property
    def total_input_tokens(self) -> int:
        return sum(r.input_tokens for r in self.requests)

    @property
    def total_output_tokens(self) -> int:
        return sum(r.output_tokens for r in self.requests)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_cost_usd(self) -> float:
        return round(sum(r.cost_usd for r in self.requests), 6)

    @property
    def avg_cost_per_request(self) -> float:
        if not self.requests:
            return 0.0
        return round(self.total_cost_usd / len(self.requests), 6)

    @property
    def avg_latency_ms(self) -> int:
        if not self.requests:
            return 0
        return int(sum(r.latency_ms for r in self.requests) / len(self.requests))

    @property
    def session_duration_min(self) -> float:
        return round((time.time() - self._session_start) / 60, 1)

    def estimated_daily_cost(self, queries_per_day: int = 100) -> float:
        """Ước tính chi phí theo ngày dựa trên avg cost/request."""
        return round(self.avg_cost_per_request * queries_per_day, 4)

    def estimated_monthly_cost(self, queries_per_day: int = 100) -> float:
        return round(self.estimated_daily_cost(queries_per_day) * 30, 2)

    def cost_history(self) -> list[float]:
        """Cumulative cost theo từng request — dùng cho line chart."""
        cumulative = []
        total = 0.0
        for r in self.requests:
            total += r.cost_usd
            cumulative.append(round(total, 6))
        return cumulative

    def service_cost_breakdown(self) -> dict:
        """
        Phân bổ cost theo service type: LLM / Embedding / Reranking.
        Trả về % của từng loại.
        """
        total = self.total_cost_usd
        if total == 0:
            return {"LLM Synthesis": 0.0, "Embedding": 0.0, "Reranking": 0.0}
        return {
            "LLM Synthesis": round(SERVICE_SPLIT["llm"] * 100, 1),
            "Embedding": round(SERVICE_SPLIT["embedding"] * 100, 1),
            "Reranking": round(SERVICE_SPLIT["reranking"] * 100, 1),
        }

    def tool_cost_table(self) -> list[dict]:
        """
        Bảng chi tiết cost per tool — dùng cho Tab 'Cost Details'.
        Mỗi row: Tool / Calls / Tokens / Cost ($)
        """
        rows = []
        for tool, count in self.tool_call_counts.items():
            display_name = (
                tool.replace("filter_and_analyze_", "")
                    .replace("_", " ")
                    .title()
            )
            rows.append({
                "Tool": display_name,
                "Calls": count,
                "Tokens": self.tool_token_map.get(tool, 0),
                "Cost ($)": f"${self.tool_cost_map.get(tool, 0):.6f}",
            })
        return rows

    def request_log(self) -> list[dict]:
        """
        Log từng request — dùng cho bảng Cost Details.
        """
        rows = []
        for i, r in enumerate(self.requests, 1):
            rows.append({
                "#": i,
                "Time": r.timestamp,
                "Query": r.query,
                "Tool": r.tool_name or "direct",
                "Tokens": r.input_tokens + r.output_tokens,
                "Cost ($)": f"${r.cost_usd:.6f}",
                "Latency": f"{r.latency_ms} ms",
            })
        return rows

    def detect_model_size(self, query: str) -> str:
        """
        Heuristic cost routing: phân loại câu hỏi để chỉ ra model nào phù hợp.
        Returns: 'small' | 'large'
        """
        simple_patterns = [
            "xin chào", "hello", "hi", "cảm ơn", "cảm on",
            "giờ mấy", "hôm nay", "bạn tên gì", "bạn là ai",
        ]
        query_lower = query.lower()
        if any(p in query_lower for p in simple_patterns):
            return "small"
        return "large"

    def summary(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "avg_cost_per_request": self.avg_cost_per_request,
            "avg_latency_ms": self.avg_latency_ms,
            "session_duration_min": self.session_duration_min,
            "tool_usage": self.tool_call_counts,
            "estimated_daily_cost_100q": self.estimated_daily_cost(100),
        }


# ── Langfuse integration ──────────────────────────────────────────────────────

_langfuse_started = False


def start_langfuse():
    """Khởi động Langfuse instrumentor để auto-track LLM calls."""
    global _langfuse_started
    if _langfuse_started:
        return True

    import sys
    import os
    sys.path.insert(0, ".")

    try:
        from src.config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST

        if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
            print("⚠ Langfuse keys chưa cấu hình — bỏ qua cost tracking từ xa")
            return False

        os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
        os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
        os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST

        from langfuse.llama_index import LlamaIndexInstrumentor
        instrumentor = LlamaIndexInstrumentor()
        instrumentor.start()

        _langfuse_started = True
        print("✓ Langfuse instrumentor started")
        return True

    except ImportError:
        print("⚠ langfuse not installed — bỏ qua")
        return False
    except Exception as e:
        print(f"⚠ Langfuse error: {e}")
        return False
