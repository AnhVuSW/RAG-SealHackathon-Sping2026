"""Ingest page — nạp data vào LanceDB — light theme."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Ingest Data — Marketing AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.ui_streamlit.components.layout import render_header, render_sidebar
from src.ui_streamlit.components.theme import inject_light_theme

inject_light_theme()
render_header(title="📄 Ingest Marketing Data")
render_sidebar()

# ── Data path config ───────────────────────────────────────────────────────────
from src.config import MARKETING_DATA_PATH

default_path = str(MARKETING_DATA_PATH)
data_path = st.text_input(
    "📁 Đường dẫn thư mục MARKETING_DataSwamp_VN:",
    value=default_path,
    placeholder=r"C:\Users\...\MARKETING_DataSwamp_VN",
)

# ── Ingest priority guide ──────────────────────────────────────────────────────
st.markdown("#### 📋 Thứ tự ưu tiên ingest")

PRIORITY_ITEMS = [
    ("#EF4444", "#FEF2F2", "🔴", "feedbacks (CSV)",
     "35 files phản hồi khách hàng — CSAT &amp; Sentiment"),
    ("#EF4444", "#FEF2F2", "🔴", "vouchers (DOCX table)",
     "300 mã voucher có cấu trúc — KHÔNG cần OCR ảnh"),
    ("#EF4444", "#FEF2F2", "🔴", "campaigns (PDF + HTML email)",
     "29 PDF báo cáo + 45 email marketing (cần cho ROI)"),
    ("#F59E0B", "#FFFBEB", "🟡", "policies (DOCX)",
     "19 chính sách công ty — nếu kịp thời gian"),
    ("#8E95A9", "#F7F8FC", "⛔", "banner, poster, hồ sơ KH (ảnh JPG)",
     "DataSwamp bẫy — bỏ qua, không cần OCR"),
]

for border_color, bg_color, icon, title, desc in PRIORITY_ITEMS:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;margin:6px 0;'
        f'background:{bg_color};border-radius:8px;border-left:4px solid {border_color};">'
        f'<span style="font-size:1rem;">{icon}</span>'
        f'<div><strong style="color:#1A1D29;font-size:0.88rem;">{title}</strong>'
        f'<span style="color:#5A6178;font-size:0.82rem;margin-left:8px;">{desc}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

if st.button("🚀 Bắt đầu Ingest", type="primary"):
    root = Path(data_path)
    if not root.exists():
        st.error(f"❌ Không tìm thấy thư mục: {data_path}")
    else:
        from src.ingestion.pipeline import MarketingIngestionPipeline

        progress = st.progress(0)
        status   = st.empty()

        with st.spinner("⏳ Đang ingest data... (có thể mất vài phút do embedding model)"):
            try:
                pipeline = MarketingIngestionPipeline()
                status.text("Khởi tạo embedding model (BAAI/bge-m3)...")
                progress.progress(5)

                result = pipeline.ingest(str(root))
                progress.progress(100)

                st.success("✅ Ingest thành công!")
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.metric("Tổng chunks",    result.total_chunks)
                with res_col2:
                    st.metric("Tổng documents", result.total_docs)

                if result.collections:
                    st.subheader("📊 Chi tiết theo collection:")
                    cols = st.columns(max(len(result.collections), 1))
                    for i, (coll, count) in enumerate(result.collections.items()):
                        with cols[i]:
                            st.metric(coll, count)

            except Exception as e:
                st.error(f"❌ Lỗi: {str(e)}")
                st.exception(e)

# ── Status check ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Trạng thái LanceDB")

if st.button("🔍 Kiểm tra collections"):
    from src.config import LANCEDB_URI
    import lancedb

    try:
        db     = lancedb.connect(LANCEDB_URI)
        tables = db.table_names()

        if tables:
            st.success(f"Tìm thấy {len(tables)} collections:")
            for t in tables:
                count = db.open_table(t).count_rows()
                st.markdown(
                    f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;'
                    f'padding:10px 16px;margin:4px 0;display:flex;justify-content:space-between;'
                    f'font-size:0.85rem;">'
                    f'<span style="color:#15803D;font-weight:600;">✅ {t}</span>'
                    f'<span style="color:#5A6178;">{count:,} records</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.warning("Chưa có collection nào. Hãy ingest data trước.")
    except Exception as e:
        st.error(f"LanceDB error: {e}")
