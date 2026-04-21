"""Tool 2: Tính ROI chiến dịch marketing từ báo cáo PDF."""
from pathlib import Path
import json
import re


# Cache campaigns data
_campaigns_df = None


def _get_campaigns_df():
    """Load campaigns data từ LanceDB campaigns table."""
    global _campaigns_df
    if _campaigns_df is not None:
        return _campaigns_df

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import MARKETING_DATA_PATH
    from src.ingestion.loaders import PDFLoader, HTMLEmailLoader
    import pandas as pd

    records = []
    pdf_loader = PDFLoader()
    pdf_dir = MARKETING_DATA_PATH / "MARKETING" / "bao_cao_marketing"

    if pdf_dir.exists():
        for pdf_file in sorted(pdf_dir.glob("*.pdf")):
            try:
                items = pdf_loader.load_with_metadata(pdf_file)
                for item in items:
                    meta = json.loads(item.get("metadata", "{}"))
                    meta["full_text"] = item.get("text", "")
                    records.append(meta)
            except Exception:
                pass

    if records:
        _campaigns_df = pd.DataFrame(records)
    else:
        _campaigns_df = pd.DataFrame()

    return _campaigns_df


def _extract_number(text: str) -> float:
    """Extract số từ chuỗi text (VD: '1,234,567 VND' → 1234567.0)."""
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _search_campaign_in_text(text: str, keyword: str) -> dict:
    """Tìm kiếm thông tin campaign trong text PDF."""
    result = {
        "campaign_id": "",
        "campaign_name": "",
        "channel": "",
        "actual_spend": 0.0,
        "revenue": 0.0,
        "roi_percent": 0.0,
        "report_month": "",
    }

    # Tìm CAM ID
    cam_match = re.search(r"CAM\d+", text)
    if cam_match:
        result["campaign_id"] = cam_match.group()

    # Tìm actual_spend (thực chi)
    spend_patterns = [
        r"thực chi[:\s]+([\d,\.]+)",
        r"actual.spend[:\s]+([\d,\.]+)",
        r"chi phí thực tế[:\s]+([\d,\.]+)",
    ]
    for pat in spend_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["actual_spend"] = _extract_number(m.group(1))
            break

    # Tìm revenue
    rev_patterns = [
        r"doanh thu[:\s]+([\d,\.]+)",
        r"revenue[:\s]+([\d,\.]+)",
    ]
    for pat in rev_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            result["revenue"] = _extract_number(m.group(1))
            break

    # Tính ROI nếu có đủ dữ liệu
    if result["actual_spend"] > 0 and result["revenue"] > 0:
        result["roi_percent"] = round(
            (result["revenue"] - result["actual_spend"]) / result["actual_spend"] * 100, 2
        )

    # Tìm channel
    channels = ["TikTok", "Facebook", "Zalo", "Email", "KOL", "Influencer", "Google"]
    for ch in channels:
        if ch.lower() in text.lower():
            result["channel"] = ch
            break

    return result


def calculate_roi(
    campaign_id_or_name: str = "",
    channel_filter: str = "",
) -> str:
    """
    Tính toán ROI của chiến dịch marketing.

    QUAN TRỌNG: ROI được tính theo công thức:
    ROI% = (revenue - actual_spend) / actual_spend × 100
    Sử dụng actual_spend (thực chi), KHÔNG dùng budget (ngân sách kế hoạch).

    Args:
        campaign_id_or_name: ID chiến dịch (VD: CAM0021) hoặc tên/từ khóa chiến dịch
        channel_filter: Lọc theo kênh (VD: TikTok, Facebook, Zalo, Email, KOL)

    Returns:
        JSON string với thông tin ROI chiến dịch
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import MARKETING_DATA_PATH, LANCEDB_URI
    from src.ingestion.loaders import PDFLoader

    pdf_dir = MARKETING_DATA_PATH / "MARKETING" / "bao_cao_marketing"
    if not pdf_dir.exists():
        return json.dumps({"error": "Không tìm thấy thư mục báo cáo"}, ensure_ascii=False)

    loader = PDFLoader()
    campaigns_found = []

    for pdf_file in sorted(pdf_dir.glob("*.pdf")):
        try:
            items = loader.load_with_metadata(pdf_file)
            for item in items:
                text = item.get("text", "")
                meta = json.loads(item.get("metadata", "{}"))

                # Filter theo campaign ID/name
                if campaign_id_or_name:
                    keyword = campaign_id_or_name.lower()
                    if keyword not in text.lower() and keyword not in pdf_file.name.lower():
                        continue

                # Filter theo channel
                if channel_filter and channel_filter.lower() not in text.lower():
                    continue

                info = _search_campaign_in_text(text, campaign_id_or_name)
                info["report_month"] = meta.get("report_month", "")
                info["source_file"] = pdf_file.name

                # Chỉ thêm nếu có thông tin hữu ích
                if info["actual_spend"] > 0 or info["campaign_id"]:
                    campaigns_found.append(info)

        except Exception as e:
            continue

    if not campaigns_found:
        return json.dumps({
            "message": f"Không tìm thấy chiến dịch phù hợp với '{campaign_id_or_name}' / channel '{channel_filter}'",
            "tip": "Thử tìm theo: CAM ID (VD: CAM0021), tên kênh (TikTok, Facebook, Zalo)",
        }, ensure_ascii=False)

    # Extract sources for the final JSON
    sources = list(set([c.get("source_file", "") for c in campaigns_found if c.get("source_file")]))

    return json.dumps({
        "formula": "ROI% = (revenue - actual_spend) / actual_spend × 100",
        "note": "actual_spend = thực chi (không phải budget ngân sách kế hoạch)",
        "campaigns": campaigns_found,
        "sources": sources,
    }, ensure_ascii=False, indent=2)
