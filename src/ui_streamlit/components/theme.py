"""Global light theme CSS injection — Marketing-friendly design.

Gọi `inject_light_theme()` ở đầu mỗi page để áp dụng theme nhất quán.
"""
import streamlit as st


LIGHT_THEME_CSS = """
<style>
/* ── Google Font: Inter ─────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root variables ─────────────────────────────────────── */
:root {
    --bg-page:        #F7F8FC;
    --bg-card:        #FFFFFF;
    --bg-sidebar:     #F0F2F8;
    --text-primary:   #1A1D29;
    --text-secondary: #5A6178;
    --text-muted:     #8E95A9;
    --accent:         #4F6BED;
    --accent-light:   #EEF1FD;
    --accent-success: #22C55E;
    --accent-success-light: #F0FDF4;
    --accent-warning: #F59E0B;
    --accent-warning-light: #FFFBEB;
    --accent-danger:  #EF4444;
    --accent-purple:  #8B5CF6;
    --accent-orange:  #F97316;
    --border:         #E5E7EB;
    --border-hover:   #C7CCE3;
    --shadow-sm:      0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md:      0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.05);
    --radius:         12px;
    --radius-sm:      8px;
}

/* ── Global reset ───────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: var(--bg-page) !important;
    color: var(--text-primary) !important;
}

/* ── Main content area ──────────────────────────────────── */
section.main > div {
    background-color: var(--bg-page) !important;
    padding-top: 1.5rem !important;
}

/* ── Sidebar ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-primary) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 0.5rem !important;
}

/* ── Typography ─────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}
/* Only target text inside main content — don't touch Streamlit icon glyphs */
.stMarkdown p, .stMarkdown li {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-secondary) !important;
}
p {
    font-family: 'Inter', sans-serif !important;
}

/* ── Streamlit metric cards ─────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.2rem !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 1.6rem !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

/* ── Buttons ────────────────────────────────────────────── */
.stButton > button {
    background-color: var(--accent) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.5rem 1.2rem !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(79,107,237,0.3) !important;
}
.stButton > button:hover {
    background-color: #3A57D8 !important;
    box-shadow: 0 4px 12px rgba(79,107,237,0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background-color: var(--bg-card) !important;
    color: var(--accent) !important;
    border: 1.5px solid var(--accent) !important;
    box-shadow: none !important;
}

/* ── Input fields ───────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea textarea {
    background-color: var(--bg-card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(79,107,237,0.15) !important;
}

/* ── Chat messages ──────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
    margin-bottom: 0.75rem !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    background: var(--accent-light) !important;
    border-color: rgba(79,107,237,0.2) !important;
}
[data-testid="stChatInput"] > div {
    background: var(--bg-card) !important;
    border: 2px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(79,107,237,0.15) !important;
}

/* ── Tabs ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: var(--radius) var(--radius) 0 0 !important;
    padding: 0.3rem 0.5rem !important;
    border-bottom: 2px solid var(--border) !important;
    gap: 0.3rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.15s ease !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent-light) !important;
    color: var(--accent) !important;
    font-weight: 600 !important;
}

/* ── Dataframes ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}

/* ── Alerts & info boxes ────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border: none !important;
}
.stSuccess {
    background: var(--accent-success-light) !important;
    border-left: 4px solid var(--accent-success) !important;
}
.stWarning {
    background: var(--accent-warning-light) !important;
    border-left: 4px solid var(--accent-warning) !important;
}

/* ── Progress bar ───────────────────────────────────────── */
.stProgress > div > div {
    background: var(--border) !important;
    border-radius: 100px !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent), #7C3AED) !important;
    border-radius: 100px !important;
}

/* ── Divider ────────────────────────────────────────────── */
hr {
    border-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Scrollbar ──────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-page); }
::-webkit-scrollbar-thumb { background: var(--border-hover); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Spinner ────────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* ── Page link buttons ──────────────────────────────────── */
[data-testid="stPageLink"] a {
    color: var(--accent) !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.3rem !important;
    padding: 0.35rem 0.8rem !important;
    border-radius: var(--radius-sm) !important;
    border: 1.5px solid rgba(79,107,237,0.35) !important;
    background: var(--accent-light) !important;
    transition: all 0.15s ease !important;
    margin-top: 0.5rem !important;
}
[data-testid="stPageLink"] a:hover {
    background: var(--accent) !important;
    color: #fff !important;
    border-color: var(--accent) !important;
}

/* ── Slider ─────────────────────────────────────────────── */
[data-testid="stSlider"] [role="slider"] {
    background: var(--accent) !important;
}

/* ── Code blocks ────────────────────────────────────────── */
pre, code {
    background: #F0F2F8 !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: #374151 !important;
}
</style>
"""


def inject_light_theme():
    """Inject CSS light theme vào Streamlit page. Gọi ở đầu mỗi page."""
    st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)


# ── Reusable card HTML helpers ───────────────────────────────────────────────

def card(content_html: str, accent_color: str = "#4F6BED", padding: str = "24px") -> str:
    """Tạo white card với shadow nhẹ."""
    return f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: {padding};
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
        margin-bottom: 0.5rem;
    ">
        {content_html}
    </div>
    """


def badge(text: str, color: str = "#4F6BED") -> str:
    """Tạo badge nhỏ."""
    from hashlib import md5
    bg = color + "18"  # ~10% opacity
    return f"""
    <span style="
        background: {bg};
        border: 1px solid {color}40;
        color: {color};
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        display: inline-block;
    ">{text}</span>
    """


def nav_card(icon: str, title: str, desc: str, accent: str = "#4F6BED") -> str:
    """Tạo navigation card."""
    accent_light = accent + "12"
    accent_border = accent + "30"
    return f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid {accent_border};
        border-top: 3px solid {accent};
        border-radius: 12px;
        padding: 24px;
        min-height: 160px;
        transition: box-shadow 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    ">
        <div style="font-size: 2rem; margin-bottom: 12px;">{icon}</div>
        <h3 style="margin: 0 0 6px 0; color: #1A1D29; font-size: 1rem; font-weight: 700;">{title}</h3>
        <p style="color: #5A6178; font-size: 0.85rem; margin: 0; line-height: 1.5;">{desc}</p>
    </div>
    """


def kpi_card(icon: str, label: str, value: str, sub: str = "", color: str = "#4F6BED") -> str:
    """Tạo KPI card dạng custom HTML (thay thế st.metric nếu muốn)."""
    return f"""
    <div style="
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    ">
        <div style="color:{color}; font-size:1.5rem; margin-bottom:8px;">{icon}</div>
        <div style="color:#5A6178; font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">{label}</div>
        <div style="color:#1A1D29; font-size:1.6rem; font-weight:700; margin-top:4px;">{value}</div>
        {f'<div style="color:#8E95A9; font-size:0.78rem; margin-top:4px;">{sub}</div>' if sub else ''}
    </div>
    """
