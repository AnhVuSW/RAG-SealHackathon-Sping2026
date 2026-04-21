"""Dashboard homepage — Marketing RAG Agent."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st

from src.ui_streamlit.components.layout import render_header, render_sidebar
from src.ui_streamlit.components.theme import inject_light_theme, nav_card

inject_light_theme()
render_header()
render_sidebar(tracker=st.session_state.get("tracker"))

# ── Hero Banner ────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="background:linear-gradient(135deg,#4F6BED 0%,#7C3AED 60%,#EC4899 100%);'
    'border-radius:16px;padding:40px 48px;margin-bottom:28px;">'
    '<div style="display:inline-block;background:rgba(255,255,255,0.2);color:#fff;'
    'font-size:0.78rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;'
    'padding:4px 14px;border-radius:20px;margin-bottom:14px;">'
    '🏆 HACKATHON SPRING 2026 · TRACK C</div>'
    '<h1 style="color:#FFFFFF;margin:0 0 10px 0;font-size:2.2rem;font-weight:800;line-height:1.2;">'
    'Marketing AI Assistant</h1>'
    '<p style="color:rgba(255,255,255,0.85);margin:0 0 22px 0;font-size:1rem;line-height:1.6;max-width:580px;">'
    'Hỏi bất cứ điều gì về dữ liệu marketing — phản hồi khách hàng, ROI chiến dịch, '
    'voucher khuyến mãi, chính sách công ty. AI sẽ trả lời ngay.'
    '</p>'
    '<div style="display:flex;gap:10px;flex-wrap:wrap;">'
    '<span style="background:rgba(255,255,255,0.2);color:#fff;border:1px solid rgba(255,255,255,0.35);'
    'padding:5px 14px;border-radius:20px;font-size:0.82rem;font-weight:600;">⚡ Phản hồi dưới 1 giây</span>'
    '<span style="background:rgba(255,255,255,0.2);color:#fff;border:1px solid rgba(255,255,255,0.35);'
    'padding:5px 14px;border-radius:20px;font-size:0.82rem;font-weight:600;">🔍 Tìm hiểu dữ liệu thực tế</span>'
    '<span style="background:rgba(255,255,255,0.2);color:#fff;border:1px solid rgba(255,255,255,0.35);'
    'padding:5px 14px;border-radius:20px;font-size:0.82rem;font-weight:600;">💰 Theo dõi chi phí tự động</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── KPI Metrics ────────────────────────────────────────────────────────────────
tracker = st.session_state.get("tracker")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_req = tracker.total_requests if tracker else 0
    st.metric("📨 Queries hôm nay", total_req,
              delta=f"+{total_req}" if total_req > 0 else None)

with col2:
    total_cost = tracker.total_cost_usd if tracker and tracker.total_requests > 0 else 0.0
    st.metric("💰 Chi phí phiên", f"${total_cost:.4f}",
              delta="Free tier ✅", delta_color="off")

with col3:
    avg_lat = tracker.avg_latency_ms if tracker and tracker.total_requests > 0 else 0
    st.metric("⏱️ Tốc độ phản hồi", f"{avg_lat} ms" if avg_lat else "— ms",
              delta="Realtime" if avg_lat and avg_lat < 1000 else None, delta_color="off")

with col4:
    try:
        from src.config import LANCEDB_URI
        import lancedb
        db = lancedb.connect(LANCEDB_URI)
        tables = db.table_names()
        total_docs = sum(db.open_table(t).count_rows() for t in tables)
        st.metric("🗄️ Dữ liệu đã nạp", f"{total_docs:,} docs",
                  delta=f"{len(tables)} bộ dữ liệu ✅")
    except Exception:
        st.metric("🗄️ Dữ liệu", "Chưa sẵn sàng", delta="Liên hệ admin")

st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

# ── 2 Nav Cards ────────────────────────────────────────────────────────────────
st.markdown("### Bắt đầu nhanh")
nav_col1, nav_col2 = st.columns(2)

with nav_col1:
    st.markdown(nav_card(
        icon="💬",
        title="Chat với AI Agent",
        desc="Đặt câu hỏi bằng tiếng Việt tự nhiên — phân tích CSAT, ROI chiến dịch, tra cứu voucher &amp; chính sách công ty.",
        accent="#4F6BED",
    ), unsafe_allow_html=True)
    st.page_link("pages/01_chat.py", label="Mở Chat →", icon="💬")

with nav_col2:
    st.markdown(nav_card(
        icon="📊",
        title="Báo cáo chi phí AI",
        desc="Xem chi tiết chi phí từng câu hỏi, breakdown theo tác vụ và ước tính chi phí vận hành theo tháng.",
        accent="#8B5CF6",
    ), unsafe_allow_html=True)
    st.page_link("pages/04_cost.py", label="Xem Chi Phí →", icon="📊")

st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
st.divider()

# ── System Status ──────────────────────────────────────────────────────────────
st.markdown("### 🟢 Trạng thái hệ thống")

try:
    from src.config import GROQ_API_KEY, LANCEDB_URI
    import lancedb as _ldb
    _db    = _ldb.connect(LANCEDB_URI)
    _tables = _db.table_names()
    _total  = sum(_db.open_table(t).count_rows() for t in _tables)
    _ready  = bool(GROQ_API_KEY and _tables)
except Exception:
    _ready = False; _total = 0; _tables = []

if _ready:
    st.markdown(
        '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:12px;'
        'padding:20px 24px;display:flex;align-items:center;gap:16px;">'
        '<span style="font-size:2rem;">✅</span>'
        f'<div><strong style="color:#15803D;font-size:1rem;">Hệ thống sẵn sàng</strong>'
        f'<p style="color:#5A6178;margin:4px 0 0 0;font-size:0.85rem;">'
        f'Đã nạp {_total:,} tài liệu từ {len(_tables)} bộ dữ liệu — AI sẵn sàng trả lời.</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;'
        'padding:20px 24px;display:flex;align-items:center;gap:16px;">'
        '<span style="font-size:2rem;">⚙️</span>'
        '<div><strong style="color:#92400E;font-size:1rem;">Đang thiết lập</strong>'
        '<p style="color:#5A6178;margin:4px 0 0 0;font-size:0.85rem;">'
        'Hệ thống chưa nạp dữ liệu. Liên hệ bộ phận kỹ thuật để được hỗ trợ.</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
st.divider()

# ── Sample Questions ───────────────────────────────────────────────────────────
st.markdown("### 💡 Gợi ý — bạn có thể hỏi AI những gì?")

q_data = [
    {"category": "📊 Phân tích phản hồi khách hàng", "color": "#4F6BED", "bg": "#EEF1FD",
     "questions": ["Tóm tắt lý do KH đánh giá 1-2 sao tháng 1/2023",
                   "Phân bố sentiment (tích cực / tiêu cực) tháng 3/2023",
                   "Khách hàng phàn nàn nhiều nhất về vấn đề gì?"]},
    {"category": "💸 Hiệu quả chiến dịch marketing", "color": "#22C55E", "bg": "#F0FDF4",
     "questions": ["ROI chiến dịch TikTok tháng trước là bao nhiêu?",
                   "Kênh nào mang lại hiệu quả tốt nhất Q1/2023?",
                   "So sánh ROI giữa Facebook Ads và TikTok Ads"]},
    {"category": "🎫 Voucher &amp; Khuyến mãi", "color": "#F59E0B", "bg": "#FFFBEB",
     "questions": ["Hiện có mã giảm giá nào cho khách hàng hạng Gold không?",
                   "Voucher nào đang còn hiệu lực cho khách VIP?",
                   "Tìm voucher giảm trên 20% cho hạng Silver"]},
    {"category": "📋 Chính sách công ty", "color": "#8B5CF6", "bg": "#F5F3FF",
     "questions": ["Chính sách bồi thường hàng hỏng trong vận chuyển thế nào?",
                   "Quy trình xử lý khiếu nại của khách hàng là gì?",
                   "Điều kiện bảo hiểm hàng hóa áp dụng như thế nào?"]},
]

q_col1, q_col2 = st.columns(2)
for i, item in enumerate(q_data):
    col = q_col1 if i % 2 == 0 else q_col2
    color, bg, cat = item["color"], item["bg"], item["category"]
    qs_html = "".join(
        f'<li style="color:#5A6178;font-size:0.83rem;margin:5px 0;padding:6px 12px;'
        f'background:{bg};border-radius:6px;border-left:3px solid {color};list-style:none;">{q}</li>'
        for q in item["questions"]
    )
    col.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;'
        f'padding:16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<p style="font-weight:700;color:{color};font-size:0.88rem;margin:0 0 10px 0;">{cat}</p>'
        f'<ul style="margin:0;padding:0;">{qs_html}</ul></div>',
        unsafe_allow_html=True,
    )

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:20px;margin-top:32px;border-top:1px solid #E5E7EB;">'
    '<p style="color:#8E95A9;font-size:0.78rem;margin:0;">'
    '📊 Marketing AI Assistant · Red Team Gang · Hackathon Spring 2026 · Track C'
    '</p></div>',
    unsafe_allow_html=True,
)
