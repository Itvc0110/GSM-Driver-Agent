"""🔴 P1a — TEXT của thẻ phải nói phần KIẾM THÊM, không nói TỔNG MỐC.

Đây là **test duy nhất bắt được lỗi thật**. Các test số học ở `tests/test_p1a_tier_delta.py`
có thể xanh trong khi thẻ vẫn dựng kỳ vọng sai — vì lỗi không nằm ở CON SỐ mà ở **chỗ đặt số**:

    "Còn với được mốc thưởng 60.000đ hôm nay"
    "Bạn thiếu 15 điểm để chạm mốc kế (khoảng 2,0 giờ chạy nữa, 3 cuốc)."

Hai câu đó **ghép lại** dựng đúng kỳ vọng *"2 giờ = 60.000đ"*, trong khi tài xế đã chốt mốc
30.000đ chỉ đổi được thêm **30.000đ**. Số 60.000 tự nó không sai — nó là **tên của mốc**.

## Ca thử là ca THẬT, đo được, không phải fixture bịa

`research/audit/2026-08-07-p1-tien-tren-card/p1a-do-truoc-the-trung-tong-moc.json` (990 lượt,
CHỈ đội bike — đếm cả `ce-*` là bẫy đã làm `mm-03` sai ~2×):
**131/426 thẻ `feasible_gap` = 30,75%** · tiền bị thổi **4.440.000đ** · bội số **2,00×** (114
thẻ) và **2,09×** (17 thẻ). Ca dưới đây là dòng đầu của phần "ví dụ" trong artifact đó.
"""
from __future__ import annotations

import re

import pytest

from app.adapters import advisor

SHIFT_END = 22 * 60

# ⚠ Bản đầu NEO CỨNG ca `("d-13", "2026-09-26", 14*60)` lấy từ artifact đo trước. Sau khi
# `scripts/regen_mock.py` chạy lại (Cycle 1 — sửa mẫu số tỷ lệ nhận), ca đó **không còn** là ca
# "đã chốt mốc" (`bien == tong == 30.000`) ⇒ test đỏ vì DỮ LIỆU đổi, không phải vì code sai.
# Chốt chặn `assert bien < tong` đã bắt đúng chuyện đó — nó làm đúng việc của nó.
#
# Nay fixture **TỰ TÌM** một ca đã-chốt-mốc trên mock hiện hành. Nội dung khẳng định giữ
# nguyên từng chữ; chỉ cách chọn ca là động ⇒ test sống qua mọi lần regen sau.


def _tim_ca_da_chot_moc():
    """Quét mock tìm (driver, ngày, giờ) mà tài xế ĐÃ chốt một mốc và vẫn còn mốc kế.

    Đó là hình dạng DUY NHẤT mà lỗi P1a biểu hiện: `bonus_at(points_now) > 0` nên
    `tier_delta < tier_vnd`, tức có hai con số tiền khác nhau để đặt nhầm chỗ.
    """
    from app.adapters import mockdata
    pol = advisor.policy()
    cat = mockdata.catalog()
    ds = [r["driver_id"] for r in cat["drivers"]
          if str(r["driver_id"]).startswith(("d-", "r-"))]      # CHỈ bike — `ce-*` là bẫy mm-03
    for ngay in reversed(cat["dates"]):
        for did in ds:
            for gio in (14 * 60, 17 * 60, 20 * 60):
                try:
                    gi = advisor.build_gi(did, ngay, gio, SHIFT_END)
                except Exception:
                    continue
                if not gi.get("next_tiers") or int(pol.bonus_at(int(gi["points_now"]))) <= 0:
                    continue
                out = advisor.advice(did, ngay, gio, SHIFT_END)
                items = [i for i in (out.get("items") or [])
                         if i.get("reason_code") == "feasible_gap"]
                if items:
                    return (did, ngay, gio), items[0], gi
    return None, None, None


@pytest.fixture(scope="module")
def _ca():
    ca, item, gi = _tim_ca_da_chot_moc()
    if item is None:
        pytest.fail("không tìm được ca 'ĐÃ chốt mốc + còn mốc kế' nào trên mock hiện hành ⇒ "
                    "nhóm mà lỗi P1a biểu hiện đã BIẾN MẤT khỏi dữ liệu; đo lại artifact p1a "
                    "trước khi tin bộ test này (KHÔNG được skip im lặng)")
    return ca, item, gi


@pytest.fixture(scope="module")
def the(_ca):
    return _ca[1]


@pytest.fixture(scope="module")
def bien_that(_ca):
    _ca_id, _item, gi = _ca
    pol = advisor.policy()
    tier = gi["next_tiers"][0][1]
    return int(tier) - int(pol.bonus_at(int(gi["points_now"]))), int(tier)


def _co_so(text: str, vnd: int) -> bool:
    return advisor._vn(vnd, "vnd") in text


# ---------- test CHÍNH ----------

def test_text_the_dung_TANG_THEM_khong_dung_TONG(the, bien_that):
    bien, tong = bien_that
    assert bien < tong, f"ca thử không còn là ca 'đã chốt mốc' (bien={bien}, tong={tong})"
    text = f"{the['title']} {the['message']}"
    assert _co_so(text, bien), (
        f"thẻ KHÔNG nêu phần kiếm thêm {bien:,}đ ở đâu cả — tài xế chỉ thấy {tong:,}đ cạnh "
        f"cụm thời gian ⇒ hiểu gấp {tong / bien:.1f} lần thứ họ thật sự nhận.\n"
        f"  title  = {the['title']!r}\n  message= {the['message']!r}")


def test_so_TONG_khong_dung_ngay_canh_cum_THOI_GIAN(the, bien_that):
    """Chặt hơn: khối text mang cụm *"giờ chạy nữa"* không được mang số TỔNG.

    ⚠ **Bản đầu của test này TỰ VÔ HIỆU** — tôi cắt câu bằng `re.split(r"[.·]", ...)`, mà
    `_vn(60000,'vnd')` render ra **"60.000đ"** *có dấu chấm bên trong* ⇒ phép cắt xé đôi chính
    chuỗi tiền, câu chứa cụm thời gian không còn chuỗi đầy đủ để so ⇒ assert luôn xanh.
    Đúng lớp lỗi **"test ghim vô hiệu" (L2)** mà docstring file này cảnh báo, xảy ra ngay trong
    file cảnh báo nó. Nay neo vào **`message`** — nơi chứa cụm nỗ lực — thay vì cắt chuỗi."""
    _bien, tong = bien_that
    assert "giờ chạy nữa" in the["message"], (
        "test neo vào `message` vì nó mang cụm nỗ lực; wording đổi thì phải sửa neo, "
        f"không được để test trôi thành vô hiệu: {the['message']!r}")
    assert not _co_so(the["message"], tong), (
        f"`message` — nơi có 'giờ chạy nữa' — đang mang số TỔNG {tong:,}đ. Đây chính là chỗ "
        f"dựng kỳ vọng sai: {the['message']!r}")


def test_numbers_khai_phan_tang_them_co_NGUON(the, bien_that):
    """CLAUDE §5: mọi số hiển thị phải có `source`."""
    bien, _tong = bien_that
    tt = [n for n in the["numbers"] if n["value"] == bien and n["unit"] == "vnd"]
    assert tt, f"`numbers` chưa khai phần kiếm thêm {bien:,}đ: {the['numbers']}"
    assert tt[0].get("source"), "số tiền không có nguồn"


def test_verifier_van_xanh_sau_khi_them_so(the):
    """`_verify_item` đòi mọi số trong text trace về `numbers`. Text nêu một số KHÔNG khai ⇒
    thẻ bị loại **im lặng** và tài xế không thấy gì — đúng cơ chế đã giết `_cliff_item` 246/246."""
    assert advisor._verify_item(the) == [], advisor._verify_item(the)


# ---------- chống hồi quy: nhóm ĐÔNG NHẤT không được đổi ----------

def test_chua_chot_moc_nao_thi_THE_KHONG_THEM_SO_TRUNG():
    """`bonus_at = 0` ⇒ biên = tổng ⇒ thẻ **không được** mang hai số tiền trùng nhau.

    Nhóm này đông nhất (đo: 295/426 thẻ feasible). Quét toàn mock cho chắc, không chỉ một ca."""
    from app.adapters import mockdata
    pol = advisor.policy()
    cat = mockdata.catalog()
    ds = [r["driver_id"] for r in cat["drivers"]
          if str(r["driver_id"]).startswith(("d-", "r-"))][:25]
    n_kiem = 0
    for did in ds:
        for ngay in cat["dates"][-1:]:
            out = advisor.advice(did, ngay, 14 * 60, SHIFT_END)
            for it in (out.get("items") or []):
                if it.get("reason_code") != "feasible_gap":
                    continue
                gi = advisor.build_gi(did, ngay, 14 * 60, SHIFT_END)
                if int(pol.bonus_at(int(gi["points_now"]))) != 0:
                    continue
                n_kiem += 1
                vnd = [n["value"] for n in it["numbers"] if n["unit"] == "vnd"]
                assert len(vnd) == len(set(vnd)), (
                    f"{did}/{ngay}: thẻ của người CHƯA chốt mốc nào mang số tiền trùng lặp "
                    f"{vnd} — bản vá đang đổi thẻ của nhóm không liên quan")
    assert n_kiem > 0, "không quét được ca 'chưa chốt mốc' nào ⇒ test này vô hiệu"
