"""Layout components — header và sidebar với light theme cho marketing staff."""
import streamlit as st
from src.ui_streamlit.components.theme import inject_light_theme


def render_header(title: str = "Marketing AI Assistant"):
    inject_light_theme()
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.25rem;
    ">
        <span style="font-size: 1.8rem;">📊</span>
        <div>
            <h1 style="
                margin: 0;
                font-size: 1.5rem;
                font-weight: 700;
                color: #1A1D29;
            ">{title}</h1>
            <p style="
                margin: 0;
                font-size: 0.82rem;
                color: #8E95A9;
                font-weight: 400;
            ">Powered by Groq Llama 3.1 8B · LanceDB · BGE-M3 · Langfuse</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(tracker=None):
    """Sidebar với navigation + cost dashboard — light theme."""
    with st.sidebar:
        # ── Logo / Brand ────────────────────────────────────
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #4F6BED, #7C3AED);
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <div style="font-size: 1.5rem;">🤖</div>
            <div style="color:#fff; font-weight:700; font-size:0.95rem; margin-top:4px;">
                Marketing RAG Agent
            </div>
            <div style="color:rgba(255,255,255,0.7); font-size:0.72rem; margin-top:2px;">
                Red Team Gang · Track C
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Navigation ──────────────────────────────────────
        st.markdown("""
        <p style="
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8E95A9;
            margin: 0 0 6px 0;
        ">MENU</p>
        """, unsafe_allow_html=True)

        st.page_link("pages/01_chat.py",  label="Chat với Agent",    icon="💬")
        st.page_link("pages/04_cost.py",  label="Báo cáo chi phí",  icon="📊")

        st.divider()

        # ── Cost Dashboard ──────────────────────────────────
        st.markdown("""
        <p style="
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8E95A9;
            margin: 0 0 8px 0;
        ">COST DASHBOARD</p>
        """, unsafe_allow_html=True)

        if not tracker or tracker.total_requests == 0:
            st.markdown("""
            <div style="
                background: #F7F8FC;
                border: 1px dashed #C7CCE3;
                border-radius: 8px;
                padding: 14px;
                text-align: center;
                color: #8E95A9;
                font-size: 0.82rem;
            ">
                📭 Chưa có request nào<br>
                <span style="font-size:0.75rem;">Bắt đầu chat để theo dõi chi phí</span>
            </div>
            """, unsafe_allow_html=True)
            st.caption("💡 Groq free tier: ~$0.05 / 1M tokens")
            return

        from src.config import SESSION_BUDGET_USD

        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Chi phí", f"${tracker.total_cost_usd:.4f}")
            st.metric("📨 Queries",  tracker.total_requests)
        with col2:
            st.metric("📊 /answer",   f"${tracker.avg_cost_per_request:.4f}")
            st.metric("🪙 Tokens",    f"{tracker.total_tokens:,}")

        st.caption(
            f"⏱ {tracker.session_duration_min} phút · "
            f"Avg {tracker.avg_latency_ms} ms"
        )

        # Budget bar
        st.divider()
        budget_pct = min(tracker.total_cost_usd / SESSION_BUDGET_USD, 1.0)
        label = f"Budget ${SESSION_BUDGET_USD:.2f} — {budget_pct*100:.0f}% used"
        if budget_pct >= 1.0:
            st.error(f"⚠️ Vượt ngưỡng ${SESSION_BUDGET_USD:.2f}!")
        elif budget_pct >= 0.8:
            st.warning(label)
        else:
            st.progress(budget_pct, text=label)

        # Model routing indicator
        last_q = tracker.requests[-1].query if tracker.requests else ""
        size   = tracker.detect_model_size(last_q)
        if size == "small":
            st.success("🟢 Query đơn giản → Model nhỏ (~60% tiết kiệm)", icon=None)
        else:
            st.info("🔵 Query phức tạp → Llama 3.1 8B (full power)", icon=None)

        # Estimates
        st.divider()
        st.caption("📈 Ước tính chi phí")
        c3, c4 = st.columns(2)
        with c3:
            st.metric("Ngày (100q)", f"${tracker.estimated_daily_cost(100):.4f}")
        with c4:
            st.metric("Tháng",       f"${tracker.estimated_monthly_cost(100):.2f}")

        # Service breakdown
        st.divider()
        st.caption("📊 Chi phí theo thành phần:")
        for i, (svc, pct) in enumerate(tracker.service_cost_breakdown().items(), 1):
            st.progress(pct / 100, text=f"{i}. {svc}  {pct}%")

        # Cost history chart
        history = tracker.cost_history()
        if len(history) > 1:
            import pandas as pd
            st.divider()
            st.caption("📉 Tích lũy theo request")
            st.line_chart(
                pd.DataFrame({"Cost ($)": history}),
                height=90,
            )

        st.caption(
            f"📥 In: {tracker.total_input_tokens:,} · "
            f"📤 Out: {tracker.total_output_tokens:,} tokens"
        )
