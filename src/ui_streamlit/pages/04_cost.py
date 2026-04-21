"""Cost Tracking page — Báo cáo chi phí AI cho giám khảo và quản lý."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Báo cáo Chi Phí — Marketing AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.ui_streamlit.components.layout import render_header, render_sidebar
from src.ui_streamlit.components.theme import inject_light_theme

inject_light_theme()
render_header(title="📊 Báo cáo Chi Phí AI")
render_sidebar(tracker=st.session_state.get("tracker"))

tracker = st.session_state.get("tracker")

# ── Hero summary ───────────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:linear-gradient(135deg,#8B5CF6 0%,#4F6BED 100%);'
    'border-radius:14px;padding:28px 36px;margin-bottom:24px;">'
    '<h2 style="color:#fff;margin:0 0 6px 0;font-size:1.4rem;font-weight:700;">Chi Phí Vận Hành AI</h2>'
    '<p style="color:rgba(255,255,255,0.85);margin:0;font-size:0.9rem;line-height:1.6;">'
    'Theo dõi chi phí theo từng câu hỏi, từng tác vụ và ước tính chi phí mở rộng. '
    'Hệ thống sử dụng Groq API (free tier) kết hợp model local — chi phí gần như bằng 0.'
    '</p></div>',
    unsafe_allow_html=True,
)

# ── KPI 4 metrics ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("📨 Tổng queries", tracker.total_requests if tracker else 0)
with c2:
    cost = tracker.total_cost_usd if tracker and tracker.total_requests > 0 else 0.0
    st.metric("💰 Tổng chi phí", f"${cost:.6f}")
with c3:
    avg = tracker.avg_cost_per_request if tracker and tracker.total_requests > 0 else 0.0
    st.metric("📊 Chi phí / câu hỏi", f"${avg:.6f}")
with c4:
    tokens = tracker.total_tokens if tracker else 0
    st.metric("🪙 Tổng tokens", f"{tokens:,}")

st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

if not tracker or tracker.total_requests == 0:
    st.markdown(
        '<div style="text-align:center;padding:40px;background:#F7F8FC;'
        'border-radius:12px;border:1px dashed #C7CCE3;">'
        '<div style="font-size:2.5rem;margin-bottom:12px;">📭</div>'
        '<p style="color:#5A6178;font-size:0.9rem;margin:0;">'
        'Chưa có dữ liệu chi phí — hãy dùng Chat trước để bắt đầu theo dõi.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    # ── Budget progress ────────────────────────────────────────────────────────
    try:
        from src.config import SESSION_BUDGET_USD
        budget_pct = min(tracker.total_cost_usd / SESSION_BUDGET_USD, 1.0)
        label = f"Budget phiên: ${SESSION_BUDGET_USD:.2f} — đã dùng {budget_pct*100:.1f}%"
        if budget_pct >= 1.0:
            st.error(f"⚠️ Vượt ngưỡng ngân sách ${SESSION_BUDGET_USD:.2f}!")
        elif budget_pct >= 0.8:
            st.warning(label)
        else:
            st.progress(budget_pct, text=label)
    except Exception:
        pass

    st.divider()

    # ── Request log ────────────────────────────────────────────────────────────
    st.subheader("📋 Lịch sử từng câu hỏi")
    req_log = tracker.request_log()
    if req_log:
        st.dataframe(pd.DataFrame(req_log), use_container_width=True, hide_index=True)

    st.divider()

    # ── Tool breakdown ─────────────────────────────────────────────────────────
    st.subheader("🔧 Chi phí theo tác vụ AI")
    tool_rows = tracker.tool_cost_table()
    if tool_rows:
        st.dataframe(pd.DataFrame(tool_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu phân tách theo tác vụ.")

    st.divider()

    # ── Service breakdown ──────────────────────────────────────────────────────
    st.subheader("📈 Chi phí theo loại dịch vụ")
    breakdown = tracker.service_cost_breakdown()
    service_df = pd.DataFrame([
        {
            "Dịch vụ":      svc,
            "% Chi phí":    f"{pct}%",
            "Ước tính ($)": round(tracker.total_cost_usd * pct / 100, 6),
        }
        for svc, pct in breakdown.items()
    ])
    svc_col1, svc_col2 = st.columns([1, 1])
    with svc_col1:
        chart_df = pd.DataFrame([{"Dịch vụ": s, "% Chi phí": p} for s, p in breakdown.items()])
        st.bar_chart(chart_df.set_index("Dịch vụ")["% Chi phí"])
    with svc_col2:
        st.dataframe(service_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Cost estimation ────────────────────────────────────────────────────────
    st.subheader("📅 Ước tính chi phí mở rộng")
    q_per_day = st.slider("Số câu hỏi / ngày", 10, 2000, 100, step=10)
    e1, e2, e3 = st.columns(3)
    e1.metric("Chi phí / ngày",  f"${tracker.estimated_daily_cost(q_per_day):.4f}")
    e2.metric("Chi phí / tháng", f"${tracker.estimated_monthly_cost(q_per_day):.2f}")
    e3.metric("Chi phí / năm",   f"${tracker.estimated_monthly_cost(q_per_day) * 12:.2f}")

    # ── Cost history ───────────────────────────────────────────────────────────
    history = tracker.cost_history()
    if len(history) > 1:
        st.divider()
        st.subheader("📉 Chi phí tích lũy theo câu hỏi")
        st.line_chart(pd.DataFrame({"Chi phí tích lũy ($)": history}), height=200)

st.divider()

# ── Model comparison table (always visible) ────────────────────────────────────
st.subheader("⚖️ So sánh chi phí các Model AI")

session_cost = tracker.avg_cost_per_request if tracker and tracker.total_requests > 0 else 0.0
monthly      = tracker.estimated_monthly_cost(100) if tracker and tracker.total_requests > 0 else 0.0

comparison_df = pd.DataFrame([
    {
        "Model": "✅ Groq Llama 3.1 8B (đang dùng)",
        "Loại": "API free tier",
        "Input / 1M tokens": "$0.05",
        "Output / 1M tokens": "$0.08",
        "Latency": "< 1s",
        "Chi phí / câu hỏi": f"${session_cost:.6f}" if session_cost else "~$0.001",
        "Chi phí / tháng (100 câu/ngày)": f"${monthly:.2f}" if monthly else "~$0.24",
    },
    {
        "Model": "✅ BGE-M3 Embedding (đang dùng)",
        "Loại": "Local · Miễn phí",
        "Input / 1M tokens": "$0",
        "Output / 1M tokens": "$0",
        "Latency": "0.1–0.5s",
        "Chi phí / câu hỏi": "$0",
        "Chi phí / tháng (100 câu/ngày)": "$0",
    },
    {
        "Model": "✅ BGE Reranker v2-M3 (đang dùng)",
        "Loại": "Local · Miễn phí",
        "Input / 1M tokens": "$0",
        "Output / 1M tokens": "$0",
        "Latency": "0.1–0.3s",
        "Chi phí / câu hỏi": "$0",
        "Chi phí / tháng (100 câu/ngày)": "$0",
    },
    {
        "Model": "OpenAI GPT-4o",
        "Loại": "API trả phí",
        "Input / 1M tokens": "$5.00",
        "Output / 1M tokens": "$15.00",
        "Latency": "1–3s",
        "Chi phí / câu hỏi": "~$0.050",
        "Chi phí / tháng (100 câu/ngày)": "~$150",
    },
    {
        "Model": "OpenAI GPT-4o-mini",
        "Loại": "API trả phí",
        "Input / 1M tokens": "$0.15",
        "Output / 1M tokens": "$0.60",
        "Latency": "0.5–1s",
        "Chi phí / câu hỏi": "~$0.003",
        "Chi phí / tháng (100 câu/ngày)": "~$9",
    },
    {
        "Model": "Ollama Llama 3.1 8B",
        "Loại": "Local · Miễn phí",
        "Input / 1M tokens": "$0",
        "Output / 1M tokens": "$0",
        "Latency": "2–5s (CPU)",
        "Chi phí / câu hỏi": "$0",
        "Chi phí / tháng (100 câu/ngày)": "$0 (điện ~$1)",
    },
])

st.dataframe(comparison_df, use_container_width=True, hide_index=True)
st.success("✅ **Kết luận**: Groq API (free tier) + Local models — chi phí gần bằng $0 cho toàn bộ demo, latency < 1s.")

st.divider()

# ── Cost Routing Logic ─────────────────────────────────────────────────────────
st.subheader("🔀 Cơ chế tối ưu chi phí (Cost Routing)")

st.markdown("""
| Loại câu hỏi | Xử lý | Tiết kiệm |
|---|---|---|
| Chào hỏi, câu đơn giản | Trả lời trực tiếp — không gọi LLM | ~100% |
| Phân tích CSAT / ROI / Voucher | Groq Llama 3.1 8B + Function Tool | — |
| Tìm kiếm chính sách | Groq + BGE Reranker (RAG pipeline) | — |

> 💡 Câu hỏi đơn giản được phát hiện trước khi gọi Agent, tiết kiệm ~60% token tổng cộng.
""")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:20px;margin-top:32px;border-top:1px solid #E5E7EB;">'
    '<p style="color:#8E95A9;font-size:0.78rem;margin:0;">'
    '📊 Marketing AI Assistant · Red Team Gang · Hackathon Spring 2026 · Track C'
    '</p></div>',
    unsafe_allow_html=True,
)
