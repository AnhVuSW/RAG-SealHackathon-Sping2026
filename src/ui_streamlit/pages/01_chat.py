"""Chat page — Marketing RAG Agent — pure chat interface, no tabs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
import json
import re
import pandas as pd

st.set_page_config(
    page_title="Chat — Marketing AI",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.ui_streamlit.components.layout import render_header, render_sidebar
from src.ui_streamlit.components.theme import inject_light_theme

inject_light_theme()


# ── Session state init ─────────────────────────────────────────────────────────
def _init_session():
    if "agent" not in st.session_state:
        from src.agent import MarketingAgent
        st.session_state.agent = MarketingAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "tracker" not in st.session_state:
        from src.cost_tracking import CostTracker
        st.session_state.tracker = CostTracker()


def _detect_tool_used(query: str, response: str) -> str:
    q = query.lower()
    r = response.lower()
    if any(k in q or k in r for k in ["roi", "chiến dịch", "tiktok", "facebook", "kênh"]):
        return "calculate_roi"
    if any(k in q or k in r for k in ["voucher", "vch", "giảm giá", "khuyến mãi", "gold", "silver", "vip"]):
        return "find_voucher_by_tier"
    if any(k in q or k in r for k in ["csat", "rating", "sentiment", "đánh giá", "phản hồi", "1 sao"]):
        return "filter_and_analyze_csat"
    if any(k in q or k in r for k in ["chính sách", "bồi thường", "bảo hiểm", "quy trình"]):
        return "search_policy"
    return ""


def _extract_json(text: str) -> dict:
    depth = 0; start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0: start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start != -1:
                try: return json.loads(text[start:i + 1])
                except Exception: start = -1
    return {}


def _try_show_voucher_images(response_text: str):
    from src.config import VOUCHER_IMAGE_DIR
    image_files = re.findall(r"the_voucher_[\w]+\.jpg", response_text)
    if not image_files:
        for code in re.findall(r"VCH\d+", response_text)[:3]:
            nums = re.findall(r"\d+", code)
            if nums:
                image_files.append(f"the_voucher_{nums[0].zfill(4)}_{code}.jpg")
    if not image_files:
        return False
    shown = 0
    cols = st.columns(min(len(image_files), 3))
    for i, img_name in enumerate(image_files[:3]):
        img_path = VOUCHER_IMAGE_DIR / img_name
        if img_path.exists():
            with cols[i]:
                st.image(str(img_path), caption=img_name.replace(".jpg", ""), use_container_width=True)
            shown += 1
    return shown > 0


def _try_show_csat_chart(response_text: str):
    try:
        data = _extract_json(response_text)
        dist = data.get("sentiment_distribution", {})
        if dist:
            chart_df = pd.DataFrame([
                {"Sentiment": k, "Số lượng": v.get("count", 0) if isinstance(v, dict) else int(v)}
                for k, v in dist.items()
            ])
            st.bar_chart(chart_df.set_index("Sentiment")["Số lượng"])
            avg = data.get("avg_rating")
            if avg:
                st.metric("⭐ Rating trung bình", f"{avg}/5")
            return True
    except Exception:
        pass
    return False


def _try_show_roi_table(response_text: str):
    try:
        data = _extract_json(response_text)
        campaigns = data.get("campaigns", [])
        if campaigns:
            df = pd.DataFrame(campaigns)
            keep_cols = [c for c in [
                "campaign_id", "campaign_name", "channel",
                "actual_spend", "revenue", "roi_percent", "report_month"
            ] if c in df.columns]
            if keep_cols:
                df = df[keep_cols]
            st.dataframe(df, use_container_width=True, hide_index=True)
            return True
    except Exception:
        pass
    return False


TOOL_META = {
    "calculate_roi":             ("💸", "#22C55E", "ROI Calculator"),
    "find_voucher_by_tier":      ("🎫", "#F59E0B", "Voucher Search"),
    "filter_and_analyze_csat":   ("📊", "#4F6BED", "CSAT Analysis"),
    "search_policy":             ("📋", "#8B5CF6", "Policy Search"),
}


def _render_message(msg: dict):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            parts = []
            if msg.get("cost") is not None:
                parts.append(f"💰 ${msg['cost']:.6f}")
            if msg.get("latency_ms"):
                parts.append(f"⏱ {msg['latency_ms']} ms")
            meta_text = " · ".join(parts)
            tool = msg.get("tool_used", "")
            if tool in TOOL_META:
                icon, color, label = TOOL_META[tool]
                badge = (
                    f'<span style="background:{color}18;border:1px solid {color}40;color:{color};'
                    f'padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;">'
                    f'{icon} {label}</span>'
                )
            else:
                badge = ""
            if meta_text or badge:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;margin-top:4px;">'
                    f'<span style="color:#8E95A9;font-size:0.78rem;">{meta_text}</span>'
                    f'{badge}</div>',
                    unsafe_allow_html=True,
                )
            if msg.get("show_voucher"):
                _try_show_voucher_images(msg["content"])
            if msg.get("show_csat"):
                _try_show_csat_chart(msg["content"])
            if msg.get("show_roi"):
                _try_show_roi_table(msg["content"])


# ══════════════════════════════════════════════════════════════════════════════
render_header(title="💬 Chat với AI Agent")
_init_session()
render_sidebar(tracker=st.session_state.get("tracker"))

# ── Reset button (top-right) ───────────────────────────────────────────────────
_, col_reset = st.columns([11, 1])
with col_reset:
    if st.button("🗑️", help="Xóa lịch sử chat"):
        st.session_state.messages = []
        st.session_state.agent.reset_memory()
        from src.cost_tracking import CostTracker
        st.session_state.tracker = CostTracker()
        st.rerun()

# ── Message history ────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        '<div style="background:#FFFFFF;border:1px dashed #C7CCE3;border-radius:14px;'
        'padding:40px;text-align:center;margin:1rem 0;">'
        '<div style="font-size:3rem;margin-bottom:12px;">💬</div>'
        '<h3 style="color:#1A1D29;margin:0 0 8px 0;font-size:1.1rem;">Chào mừng bạn!</h3>'
        '<p style="color:#5A6178;font-size:0.88rem;margin:0 0 24px 0;">'
        'Hãy đặt câu hỏi bằng tiếng Việt để phân tích dữ liệu marketing</p>'
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;max-width:540px;margin:0 auto;text-align:left;">'
        '<div style="background:#EEF1FD;border-radius:8px;padding:10px 14px;font-size:0.82rem;color:#4F6BED;cursor:pointer;">'
        '📊 <em>Tóm tắt lý do KH đánh giá 1 sao tuần qua</em></div>'
        '<div style="background:#F0FDF4;border-radius:8px;padding:10px 14px;font-size:0.82rem;color:#15803D;cursor:pointer;">'
        '💸 <em>ROI chiến dịch TikTok tháng trước?</em></div>'
        '<div style="background:#FFFBEB;border-radius:8px;padding:10px 14px;font-size:0.82rem;color:#92400E;cursor:pointer;">'
        '🎫 <em>Có mã giảm giá nào cho hạng Gold?</em></div>'
        '<div style="background:#F5F3FF;border-radius:8px;padding:10px 14px;font-size:0.82rem;color:#6D28D9;cursor:pointer;">'
        '📋 <em>Chính sách bồi thường hàng hỏng?</em></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
else:
    for msg in st.session_state.messages:
        _render_message(msg)

# ── Chat input (must be at top level) ─────────────────────────────────────────
prompt = st.chat_input("Nhập câu hỏi về CSAT, ROI, voucher hoặc chính sách công ty...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("🤖 Đang phân tích..."):
        result    = st.session_state.agent.chat(prompt)
        response  = result.get("response", "")
        latency   = result.get("latency_ms", 0)

    tool_used     = _detect_tool_used(prompt, response)
    input_tokens  = len(prompt) // 4
    output_tokens = len(response) // 4

    tracker = st.session_state.tracker
    metrics = tracker.record(
        query=prompt,
        response=response,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency,
        tool_name=tool_used,
    )

    st.session_state.messages.append({
        "role":         "assistant",
        "content":      response,
        "cost":         metrics.cost_usd,
        "latency_ms":   latency,
        "tool_used":    tool_used,
        "show_voucher": tool_used == "find_voucher_by_tier" or "VCH" in response,
        "show_csat":    tool_used == "filter_and_analyze_csat",
        "show_roi":     tool_used == "calculate_roi",
    })
    st.rerun()
