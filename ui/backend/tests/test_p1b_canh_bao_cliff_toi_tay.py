"""🔴 P1b — cảnh báo "tỷ lệ nhận sát ngưỡng" phải TỚI ĐƯỢC tài xế.

## Lỗi: thẻ bị giết HAI LẦN, độc lập nhau

1. `_verify_item` đòi mọi số trong text trace về `numbers`, mà `_cliff_item` **cố ý** để
   `numbers: []` (*"KHÔNG số tiền, KHÔNG hứa hẹn"*) ⇒ note của solver luôn chứa `0.85`/`0.86`
   ⇒ `check_bare_numbers` **luôn** bắn ⇒ thẻ bị loại.
2. `cards.js` chỉ vẽ `items[0]`, mà cliff luôn được `append` **thứ hai**.

Đo: `pb5` — **246/2.310 lượt sinh · 0/246 sống · 0/246 được vẽ**.
Tôi đo lại trên đội bike: **96/990 lượt (9,70%) ở trong dải · 0/96 tới tay tài xế**.

## Vì sao đáng ship — đo, không phỏng đoán

`research/audit/2026-08-07-p1-tien-tren-card/p1b-canh-bao-sat-nguong-co-hanh-dong-duoc-khong.json`:

    còn mấy lần từ chối nữa thì rơi dưới ngưỡng:
       1 lần → 66/96 = 68,8%
       2 lần → 27/96 = 28,1%
       3 lần →  3/96 =  3,1%
    ⇒ 100% số ca chỉ cần ≤3 lần từ chối là mất TOÀN BỘ thưởng ngày
    quỹ giờ còn lại lúc cảnh báo: trung vị 5,0 giờ

Một tài xế cách **một cú từ chối** khỏi việc mất trọn thưởng ngày, còn 5 giờ ca phía trước — và
hệ thống **không nói gì**. Fallback *"đừng ship nếu không hành động được"* KHÔNG kích hoạt.

⚠ Đại lượng: dải cảnh báo dùng `acceptance_rate` **đã co** (góc nhìn advisor), còn `k` tính trên
**đếm thô** — và đếm thô mới là thứ **chính sách dùng cuối ngày** để quyết trả thưởng.
"""
from __future__ import annotations

import pytest

from app.adapters import advisor, mockdata

SHIFT_END = 22 * 60
GIO = 14 * 60
CUM = "sát ngưỡng"


def _quet(n_driver: int = 40):
    """Trả (n_trong_dai, n_toi_tay) trên một lát mock — dùng ĐÚNG cửa `advisor.advice`."""
    pol = advisor.policy()
    nguong, margin = float(pol.bonus_min_acceptance), 0.03
    cat = mockdata.catalog()
    ds = [r["driver_id"] for r in cat["drivers"]
          if str(r["driver_id"]).startswith(("d-", "r-"))][:n_driver]
    ngay = cat["dates"][-1]
    trong_dai = toi_tay = 0
    for did in ds:
        gi = advisor.build_gi(did, ngay, GIO, SHIFT_END)
        if not (nguong <= float(gi["acceptance_rate"]) < nguong + margin):
            continue
        trong_dai += 1
        out = advisor.advice(did, ngay, GIO, SHIFT_END)
        txt = " ".join(f"{i.get('title','')} {i.get('message','')} {i.get('caveat','')}"
                       for i in (out.get("items") or []))
        if CUM in txt:
            toi_tay += 1
    return trong_dai, toi_tay


def test_canh_bao_cliff_TOI_TAY_tai_xe():
    """Bất biến: mọi tài xế trong dải sát ngưỡng phải THẤY cảnh báo, không chỉ được SINH ra."""
    trong_dai, toi_tay = _quet()
    if trong_dai == 0:
        pytest.skip("lát mock này không có ai trong dải sát ngưỡng — mở rộng n_driver")
    assert toi_tay == trong_dai, (
        f"{trong_dai - toi_tay}/{trong_dai} tài xế trong dải sát ngưỡng KHÔNG thấy cảnh báo. "
        f"Đây là nhóm mà 100% số ca chỉ cần ≤3 lần từ chối là mất TOÀN BỘ thưởng ngày.")


def test_canh_bao_KHONG_mang_so_de_verifier_khong_giet_the():
    """Cơ chế đã giết thẻ cliff 246/246: có số trong text mà không khai `numbers`.

    Câu gộp vào `caveat` **không được** mang số — nếu ai đó thêm "0,85" vào đó, `check_bare_numbers`
    sẽ bắn và **cả thẻ chính** bị loại, tức làm hỏng thứ đang chạy tốt."""
    import re
    pol = advisor.policy()
    nguong, margin = float(pol.bonus_min_acceptance), 0.03
    cat = mockdata.catalog()
    ngay = cat["dates"][-1]
    for r in cat["drivers"]:
        did = r["driver_id"]
        if not str(did).startswith(("d-", "r-")):
            continue
        gi = advisor.build_gi(did, ngay, GIO, SHIFT_END)
        if not (nguong <= float(gi["acceptance_rate"]) < nguong + margin):
            continue
        out = advisor.advice(did, ngay, GIO, SHIFT_END)
        for it in (out.get("items") or []):
            cav = str(it.get("caveat") or "")
            if CUM not in cav:
                continue
            assert not re.search(r"\d", cav.split(CUM)[1] if CUM in cav else ""), (
                f"câu cảnh báo mang SỐ ⇒ verifier sẽ bắn và loại cả thẻ: {cav!r}")
            assert advisor._verify_item(it) == [], (
                f"verifier bắn trên thẻ có cảnh báo ⇒ tài xế mất CẢ hai thứ: "
                f"{advisor._verify_item(it)}")
        return
    pytest.skip("không có ai trong dải sát ngưỡng trên lát mock này")


def test_khong_them_canh_bao_cho_nguoi_KHONG_trong_dai():
    """Chống hồi quy: người ngoài dải không được nhận cảnh báo (nhiễu = mất niềm tin)."""
    pol = advisor.policy()
    nguong, margin = float(pol.bonus_min_acceptance), 0.03
    cat = mockdata.catalog()
    ngay = cat["dates"][-1]
    n = 0
    for r in cat["drivers"][:40]:
        did = r["driver_id"]
        if not str(did).startswith(("d-", "r-")):
            continue
        gi = advisor.build_gi(did, ngay, GIO, SHIFT_END)
        if nguong <= float(gi["acceptance_rate"]) < nguong + margin:
            continue
        n += 1
        out = advisor.advice(did, ngay, GIO, SHIFT_END)
        for it in (out.get("items") or []):
            assert CUM not in str(it.get("caveat") or ""), (
                f"{did} (tỷ lệ {gi['acceptance_rate']:.3f}) NGOÀI dải mà vẫn nhận cảnh báo")
    assert n > 0, "không quét được ai ngoài dải ⇒ test vô hiệu"
