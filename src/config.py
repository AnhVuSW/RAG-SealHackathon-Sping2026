"""Central configuration — load from .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# ── LLM ──────────────────────────────────────────────────
LLM_MODEL = "llama-3.1-8b-instant"   # Groq free, nhanh, tiết kiệm token

# ── Embedding & Reranker (local) ─────────────────────────
EMBEDDING_MODEL = "BAAI/bge-m3"                # Multilingual, hỗ trợ tiếng Việt
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"    # Local reranker
EMBEDDING_DIM = 1024                            # bge-m3 output dim

# ── Data ─────────────────────────────────────────────────
MARKETING_DATA_PATH = Path(
    os.getenv(
        "MARKETING_DATA_PATH",
        r"C:\Users\ASUS\Downloads\New folder (2)\MARKETING_DataSwamp_VN"
    )
)
LANCEDB_URI = os.getenv("LANCEDB_URI", "./data/lancedb")

# ── Voucher images ────────────────────────────────────────
VOUCHER_IMAGE_DIR = MARKETING_DATA_PATH / "MARKETING" / "the_voucher"

# ── Policy documents ──────────────────────────────────────
POLICY_DATA_PATH = Path(
    os.getenv(
        "POLICY_DATA_PATH",
        r"C:\Users\ASUS\Downloads\New folder (2)\chinh_sach_cong_ty\chinh_sach_cong_ty"
    )
)

# ── LanceDB table names ───────────────────────────────────
TABLE_FEEDBACKS = "feedbacks"
TABLE_VOUCHERS = "vouchers"
TABLE_CAMPAIGNS = "campaigns"
TABLE_POLICIES = "policies"

# ── Chunking ──────────────────────────────────────────────
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# ── Retrieval ─────────────────────────────────────────────
TOP_K_RETRIEVE = 20
TOP_K_RERANK = 5
MAX_SUB_QUERIES = 3

# ── Cost / Budget ─────────────────────────────────────────
SESSION_BUDGET_USD = 1.0    # Cảnh báo khi vượt ngưỡng
