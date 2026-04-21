"""Tool 3: Tìm kiếm voucher theo hạng khách hàng từ DOCX bảng 300 mã."""
from pathlib import Path
import json


# Cache voucher DataFrame
_voucher_df = None


def _get_voucher_df():
    global _voucher_df
    if _voucher_df is not None:
        return _voucher_df

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import MARKETING_DATA_PATH
    from src.ingestion.loaders import DocxTableLoader

    voucher_file = MARKETING_DATA_PATH / "MARKETING" / "the_le_voucher_300_ma.docx"
    if not voucher_file.exists():
        import pandas as pd
        _voucher_df = pd.DataFrame()
        return _voucher_df

    loader = DocxTableLoader()
    _voucher_df = loader.load_dataframe(voucher_file)
    return _voucher_df


def find_voucher_by_tier(
    tier_name: str,
    active_only: bool = True,
) -> str:
    """
    Tìm voucher khuyến mãi theo hạng khách hàng.

    LƯU Ý QUAN TRỌNG:
    - Voucher giảm trên purchase_price_vnd (giá hàng), KHÔNG phải total_payment_vnd (tổng thanh toán)
    - Tier có thể multi-value như 'Gold,VIP' — tool tự xử lý str.contains()

    Args:
        tier_name: Hạng KH cần tìm: 'Standard', 'Silver', 'Gold', 'VIP', hoặc 'All'
        active_only: Chỉ lấy voucher còn hiệu lực (mặc định True)

    Returns:
        JSON string danh sách voucher phù hợp kèm image_path để hiển thị ảnh
    """
    import pandas as pd

    df = _get_voucher_df()
    if df.empty:
        return json.dumps({"error": "Không tìm thấy dữ liệu voucher"}, ensure_ascii=False)

    filtered = df.copy()

    # Tìm cột tier (tên cột có thể khác nhau tùy DOCX)
    tier_col = None
    for col in filtered.columns:
        if "tier" in col.lower() or "hạng" in col.lower() or "rank" in col.lower():
            tier_col = col
            break

    if tier_col is None:
        return json.dumps({
            "error": "Không tìm thấy cột tier trong dữ liệu voucher",
            "columns": list(filtered.columns),
        }, ensure_ascii=False)

    # Filter theo tier — dùng str.contains() để xử lý multi-value "Gold,VIP"
    tier_mask = (
        filtered[tier_col].str.contains(tier_name, case=False, na=False) |
        filtered[tier_col].str.contains("All", case=False, na=False)
    )
    filtered = filtered[tier_mask]

    # Filter theo status
    if active_only:
        status_col = None
        for col in filtered.columns:
            if "status" in col.lower() or "trạng thái" in col.lower() or "hiệu lực" in col.lower():
                status_col = col
                break
        if status_col:
            filtered = filtered[
                filtered[status_col].str.contains("hiệu lực|active|còn", case=False, na=False)
            ]

    if filtered.empty:
        return json.dumps({
            "message": f"Không có voucher nào cho hạng '{tier_name}'" + (" còn hiệu lực" if active_only else ""),
            "total": 0,
        }, ensure_ascii=False)

    # Chuẩn bị kết quả
    vouchers = []
    for _, row in filtered.head(10).iterrows():  # Giới hạn 10 kết quả
        v = row.to_dict()
        # Thêm image_path nếu chưa có
        if "image_path" not in v or not v.get("image_path"):
            code = str(v.get("voucher_code", v.get("Mã voucher", "")))
            import re
            nums = re.findall(r"\d+", code)
            if nums:
                v["image_path"] = f"the_voucher_{nums[0].zfill(4)}_{code}.jpg"

        vouchers.append({k: str(val) for k, val in v.items() if val and str(val) != "nan"})

    return json.dumps({
        "tier_searched": tier_name,
        "total_found": len(filtered),
        "showing": len(vouchers),
        "note": "Voucher giảm trên purchase_price_vnd (giá hàng), KHÔNG phải tổng thanh toán",
        "vouchers": vouchers,
        "sources": ["MARKETING_DataSwamp_VN/MARKETING/the_le_voucher_300_ma.docx"],
    }, ensure_ascii=False, indent=2)
