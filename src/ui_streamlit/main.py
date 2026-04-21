"""Streamlit main app — Marketing RAG Agent — Entry point với st.navigation()."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Marketing AI Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from src.cost_tracking import start_langfuse
    start_langfuse()
except Exception:
    pass

# ── Dùng st.navigation() để control chính xác pages nào hiển thị ──────────────
home = st.Page("pages/home.py",    title="Dashboard",        icon="🏠", default=True)
chat = st.Page("pages/01_chat.py", title="Chat với Agent",   icon="💬")
cost = st.Page("pages/04_cost.py", title="Báo cáo Chi Phí", icon="📊")

pg = st.navigation([home, chat, cost])
pg.run()
