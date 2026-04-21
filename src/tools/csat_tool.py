"""Tool 1: Phân tích CSAT & phản hồi khách hàng từ CSV feedbacks."""
from pathlib import Path
import json


# Cache DataFrame để không đọc lại nhiều lần
_feedback_df = None


def _get_feedback_df():
    global _feedback_df
    if _feedback_df is not None:
        return _feedback_df

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import MARKETING_DATA_PATH
    from src.ingestion.loaders import CSVFeedbackLoader

    folder = MARKETING_DATA_PATH / "MARKETING" / "phan_hoi_hang_thang"
    loader = CSVFeedbackLoader()
    _feedback_df = loader.load_dataframe(folder)
    return _feedback_df


def filter_and_analyze_csat(
    date_start: str = "",
    date_end: str = "",
    min_rating: int = 1,
    max_rating: int = 5,
    sentiment_filter: str = "",
) -> str:
    """
    Phân tích dữ liệu CSAT và phản hồi khách hàng.

    Args:
        date_start: Ngày bắt đầu lọc, định dạng YYYY-MM-DD (để trống = không giới hạn)
        date_end: Ngày kết thúc lọc, định dạng YYYY-MM-DD (để trống = không giới hạn)
        min_rating: Rating tối thiểu (1-5, mặc định 1)
        max_rating: Rating tối đa (1-5, mặc định 5)
        sentiment_filter: Lọc theo sentiment: 'positive', 'negative', 'neutral' (để trống = tất cả)

    Returns:
        JSON string với kết quả phân tích CSAT
    """
    import pandas as pd

    df = _get_feedback_df()
    if df.empty:
        return json.dumps({"error": "Không tìm thấy dữ liệu feedback"}, ensure_ascii=False)

    filtered = df.copy()

    # Filter theo ngày
    if date_start and "created_at" in filtered.columns:
        try:
            filtered = filtered[filtered["created_at"] >= pd.to_datetime(date_start)]
        except Exception:
            pass

    if date_end and "created_at" in filtered.columns:
        try:
            filtered = filtered[filtered["created_at"] <= pd.to_datetime(date_end)]
        except Exception:
            pass

    # Filter theo rating
    if "rating" in filtered.columns:
        filtered = filtered[
            (filtered["rating"] >= min_rating) & (filtered["rating"] <= max_rating)
        ]

    # Filter theo sentiment
    if sentiment_filter and "sentiment" in filtered.columns:
        filtered = filtered[
            filtered["sentiment"].str.lower() == sentiment_filter.lower()
        ]

    if filtered.empty:
        return json.dumps({
            "message": "Không có feedback nào phù hợp với điều kiện lọc",
            "total_records": 0,
        }, ensure_ascii=False)

    # ── Tính toán thống kê ─────────────────────────────────
    result = {
        "total_records": int(len(filtered)),
        "avg_rating": round(float(filtered["rating"].mean()), 2) if "rating" in filtered.columns else None,
        "sentiment_distribution": {},
        "top_feedback": [],
        "tier_breakdown": {},
        "nps_breakdown": {},
    }

    # Phân bố sentiment
    if "sentiment" in filtered.columns:
        sentiment_counts = filtered["sentiment"].value_counts()
        total = len(filtered)
        result["sentiment_distribution"] = {
            s: {"count": int(c), "percent": round(c / total * 100, 1)}
            for s, c in sentiment_counts.items()
        }

    # Top feedback text (negative hoặc filter hiện tại)
    if "feedback_text" in filtered.columns:
        top_rows = filtered.nsmallest(5, "rating") if "rating" in filtered.columns else filtered.head(5)
        result["top_feedback"] = [
            {
                "rating": int(row.get("rating", 0)) if not pd.isna(row.get("rating", 0)) else 0,
                "sentiment": str(row.get("sentiment", "")),
                "text": str(row.get("feedback_text", ""))[:200],
                "tier": str(row.get("customer_tier", "")),
                "route": str(row.get("route_name", "")),
            }
            for _, row in top_rows.iterrows()
        ]

    # Breakdown theo tier
    if "customer_tier" in filtered.columns:
        tier_avg = filtered.groupby("customer_tier")["rating"].mean().round(2)
        result["tier_breakdown"] = {k: float(v) for k, v in tier_avg.items()}

    # NPS breakdown
    if "phan_loai_nps" in filtered.columns:
        nps_counts = filtered["phan_loai_nps"].value_counts()
        result["nps_breakdown"] = {k: int(v) for k, v in nps_counts.items()}
        
    result["sources"] = ["MARKETING_DataSwamp_VN/MARKETING/phan_hoi_hang_thang/*.csv"]

    return json.dumps(result, ensure_ascii=False, indent=2)
