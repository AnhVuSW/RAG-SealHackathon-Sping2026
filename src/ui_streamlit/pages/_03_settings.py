"""Settings page — cấu hình API keys và model — light theme."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Settings — Marketing AI",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.ui_streamlit.components.layout import render_header, render_sidebar
from src.ui_streamlit.components.theme import inject_light_theme

inject_light_theme()
render_header(title="⚙️ Cài đặt hệ thống")
render_sidebar()

# ── API Keys ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    background: #FFFFFF; border: 1px solid #E5E7EB;
    border-radius: 12px; padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
">
    <h3 style="margin: 0 0 4px 0; color: #1A1D29; font-size: 1rem;">🔑 API Keys</h3>
    <p style="color: #8E95A9; font-size: 0.82rem; margin: 0 0 16px 0;">
        Thông tin này được lưu cục bộ trong file <code>.env</code> — không gửi ra ngoài.
    </p>
</div>
""", unsafe_allow_html=True)

from src.config import GROQ_API_KEY, LANGFUSE_PUBLIC_KEY

col_key1, col_key2 = st.columns(2)
with col_key1:
    groq_key = st.text_input(
        "🔑 Groq API Key",
        value=GROQ_API_KEY if GROQ_API_KEY else "",
        type="password",
        help="Lấy tại https://console.groq.com — miễn phí",
        placeholder="gsk_...",
    )
    st.caption("📎 [Lấy Groq API Key miễn phí](https://console.groq.com)")

with col_key2:
    langfuse_key = st.text_input(
        "📊 Langfuse Public Key",
        value=LANGFUSE_PUBLIC_KEY if LANGFUSE_PUBLIC_KEY else "",
        type="password",
        help="Lấy tại https://cloud.langfuse.com — miễn phí",
        placeholder="pk-lf-...",
    )
    st.caption("📎 [Lấy Langfuse Key miễn phí](https://cloud.langfuse.com)")

if st.button("💾 Lưu vào .env", type="primary"):
    env_path = Path(".env")
    lines    = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()

    def _update_env(lines, key, value):
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                return lines
        lines.append(f"{key}={value}")
        return lines

    if groq_key:
        lines = _update_env(lines, "GROQ_API_KEY", groq_key)
    if langfuse_key:
        lines = _update_env(lines, "LANGFUSE_PUBLIC_KEY", langfuse_key)

    env_path.write_text("\n".join(lines))
    st.success("✅ Đã lưu. Khởi động lại app để áp dụng.")

st.divider()

# ── Model Info ─────────────────────────────────────────────────────────────────
st.subheader("🤖 Cấu hình Model")

from src.config import LLM_MODEL, EMBEDDING_MODEL, RERANKER_MODEL

model_info = [
    {
        "icon": "⚡",
        "name": LLM_MODEL,
        "label": "LLM Chính",
        "sub": "Groq API · Free tier · < 1s latency",
        "color": "#4F6BED",
    },
    {
        "icon": "🔍",
        "name": "bge-m3",
        "label": "Embedding Model",
        "sub": "BAAI · Local · Hỗ trợ tiếng Việt",
        "color": "#22C55E",
    },
    {
        "icon": "🏆",
        "name": "bge-reranker-v2-m3",
        "label": "Reranker",
        "sub": "BAAI · Local · Cross-encoder",
        "color": "#F59E0B",
    },
]

m_cols = st.columns(3)
for i, m in enumerate(model_info):
    with m_cols[i]:
        st.markdown(f"""
        <div style="
            background: #FFFFFF; border: 1px solid #E5E7EB;
            border-top: 3px solid {m['color']};
            border-radius: 12px; padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        ">
            <div style="font-size:1.6rem; margin-bottom:8px;">{m['icon']}</div>
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase;
                        letter-spacing:0.06em; color:{m['color']}; margin-bottom:4px;">
                {m['label']}
            </div>
            <div style="font-size:0.92rem; font-weight:700; color:#1A1D29; margin-bottom:4px;">
                {m['name']}
            </div>
            <div style="font-size:0.78rem; color:#8E95A9;">{m['sub']}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Cost comparison ────────────────────────────────────────────────────────────
st.subheader("💸 So sánh chi phí Model")

import pandas as pd
cost_data = pd.DataFrame([
    {"Model": "✅ Groq Llama 3.1 8B (API)",  "Input/1M tokens": "$0.05",  "Output/1M tokens": "$0.08",  "Latency": "< 1s",       "Chi phí demo": "~$0.001"},
    {"Model": "✅ BGE-M3 Embedding (Local)",  "Input/1M tokens": "$0",     "Output/1M tokens": "$0",     "Latency": "0.1–0.5s",    "Chi phí demo": "$0"},
    {"Model": "✅ BGE Reranker (Local)",      "Input/1M tokens": "$0",     "Output/1M tokens": "$0",     "Latency": "0.1–0.3s",    "Chi phí demo": "$0"},
    {"Model": "OpenAI GPT-4o (tham khảo)",   "Input/1M tokens": "$5.00",  "Output/1M tokens": "$15.00", "Latency": "1–3s",        "Chi phí demo": "~$0.10"},
    {"Model": "OpenAI GPT-4o-mini (tham khảo)", "Input/1M tokens": "$0.15", "Output/1M tokens": "$0.60", "Latency": "0.5–1s",    "Chi phí demo": "~$0.003"},
])
st.dataframe(cost_data, use_container_width=True, hide_index=True)
st.success("✅ Sử dụng Groq + Local models: chi phí gần như **$0** cho toàn bộ demo")

st.divider()

# ── System info ────────────────────────────────────────────────────────────────
st.subheader("ℹ️ Thông tin hệ thống")

sys_col1, sys_col2 = st.columns(2)
with sys_col1:
    try:
        from src.config import LANCEDB_URI
        import lancedb
        db = lancedb.connect(LANCEDB_URI)
        tables = db.table_names()
        st.markdown(f"""
        <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-radius:8px; padding:12px 16px;">
            <strong style="color:#15803D;">✅ LanceDB</strong><br>
            <span style="color:#5A6178; font-size:0.82rem;">
                URI: <code>{LANCEDB_URI}</code><br>
                Collections: {len(tables)} ({', '.join(tables) if tables else 'trống'})
            </span>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"LanceDB: {e}")

with sys_col2:
    try:
        import streamlit
        import llama_index
        st.markdown(f"""
        <div style="background:#EEF1FD; border:1px solid #C7D2FE; border-radius:8px; padding:12px 16px;">
            <strong style="color:#4F6BED;">📦 Phiên bản thư viện</strong><br>
            <span style="color:#5A6178; font-size:0.82rem;">
                Streamlit: {streamlit.__version__}<br>
                LlamaIndex: {llama_index.__version__}
            </span>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        st.info("Không đọc được phiên bản thư viện")
