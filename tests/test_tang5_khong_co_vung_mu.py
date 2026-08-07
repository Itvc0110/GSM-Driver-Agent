"""🔴 CỔNG BẤT BIẾN tầng 5 — *"được định tuyến một chiều"* phải kéo theo *"THỰC SỰ được soi"*.

## Lỗi mà cổng này chặn (đã xảy ra BA lần)

`parallel._ONE_WAY_PREFIXES = ("veto_", "xveto_", "commit_")` đẩy ba họ khoá **RA KHỎI** bảng
significance hai chiều — đúng, vì tầng 5 là cổng MỘT CHIỀU chống Goodhart. Artifact vì thế in
cạnh mỗi khoá đó `"one_way_gate": "sim_metrics.health_guardrail_flags (D-M3-05)"`.

**Nhưng cổng ấy chỉ lặp `REST_RAILS`.** Đo được (`c4b-do-vung-mu-tang-5.py`, tiêm *"rail sụp về
0"* cho từng khoá): **7 khoá** nằm ngoài tầm soi và **9 khoá** không vào cả `a_mean` — trong khi
nhãn nói ngược lại. Tức **một lời khai quản trị không có thật**.

`parallel.py:415-419` tự chép rằng danh sách tường minh *"đã HỞ hai lần"* (`xveto_*` UPDATE-138,
`commit_*` UPDATE-142) và `_ONE_WAY_PREFIXES` sinh ra để chặn. Bản vá đó nối đúng **chiều đi ra**
nhưng **quên chiều đi vào**. Sửa nửa đường, nửa còn lại im lặng — đó là lý do phải có một BẤT
BIẾN chứ không phải một lần sửa.

## Vì sao đây không phải *"nhớ cẩn thận hơn"*

Ba assert dưới đây suy danh sách khoá từ **chính các hằng rail**, nên thêm một rail mới mà quên
nối là **ĐỎ NGAY**, không cần ai nhớ. Rail cố ý trơ thì khai vào `sim_metrics.RAIL_KHAI_TRO`
kèm lý do **và điều kiện mở lại** — biến một sự im lặng thành một dòng khai báo có chủ ý.
"""
from __future__ import annotations

import pytest

from gsm_sim.parallel import _ONE_WAY_PREFIXES, aggregate_health_guardrail
from gsm_sim.sim_metrics import (COMMIT_KEYS, EXTEND_RAILS, RAIL_ALIVE_MIN_N, RAIL_KHAI_TRO,
                                 REST_RAILS, health_guardrail_flags)

# Khoá tầng 5 KHÔNG được soi riêng — và đó là ĐÚNG THIẾT KẾ, không phải vùng mù:
#   `*_calls_n`  MẪU SỐ (số lần cổng chạy)      `*_fired_n`      TỔNG của các rail
#   `commit_made_n`  kênh nói ít hơn ≠ suy giảm  `commit_broken_n` sụp về 0 là TỐT
#   `commit_cleared_n` nghỉ sớm tự nguyện ≠ suy giảm
# Tố giác bất kỳ khoá nào ở đây sẽ tạo **chiều khen**, đúng hướng Goodhart mà tầng 5 chặn.
# Tách tường minh để không ai đếm thô rồi báo thổi (đếm thô ra 11; vùng mù thật là 7).
CHI_HIEN_THI = frozenset({"veto_calls_n", "veto_fired_n", "xveto_calls_n", "xveto_fired_n",
                          "commit_made_n", "commit_broken_n", "commit_cleared_n"})


def _moi_khoa_mot_chieu() -> set[str]:
    ks = {f"veto_{r}_n" for r in REST_RAILS} | {"veto_calls_n", "veto_fired_n"}
    ks |= {f"xveto_{r}_n" for r in EXTEND_RAILS} | {"xveto_calls_n", "xveto_fired_n"}
    ks |= set(COMMIT_KEYS)
    assert all(k.startswith(_ONE_WAY_PREFIXES) for k in ks), "một khoá tầng 5 lọt tiền tố"
    return ks


def _nen_sach(moi: set[str]) -> dict:
    """Một arm KHÔNG có cờ nào — nền để tiêm.

    ⚠ Bản đầu của harness này đặt MỌI khoá = 100, khiến `kept+broken+cleared = 300 > made = 100`
    ⇒ cờ *"vỡ bảo toàn"* nổ **trước khi tiêm bất cứ thứ gì** ⇒ `_cong_co_soi` trả True cho mọi
    khoá và phép đo trở nên vô nghĩa. Đây đúng họ lỗi *"fixture suy biến"* (L2) mà repo đã trả
    giá — nên `test_nen_phai_SACH_CO` dưới đây ghim nó lại."""
    a = {k: 50.0 for k in moi}
    a.update({"rest_min_total": 1000.0, "work_span_p90": 100.0, "drive_min_p90": 100.0,
              "commit_made_n": 100.0, "commit_kept_n": 40.0,
              "commit_broken_n": 30.0, "commit_cleared_n": 20.0})   # Σ 90 ≤ 100: bảo toàn OK
    return a


def _cong_co_soi(k: str, moi: set[str]) -> bool:
    """TIÊM: b[k] sụp về 0 so với a. Cổng lành mạnh phải tố giác."""
    a = _nen_sach(moi)
    b = dict(a)
    b[k] = 0.0
    return len(health_guardrail_flags(a, b)) > 0


def test_nen_phai_SACH_CO_truoc_khi_tiem():
    """Không có assert này thì mọi kết quả của `_cong_co_soi` là hiện vật của nền, không phải
    của cổng — và tôi đã sập đúng bẫy đó ở bản đầu."""
    moi = _moi_khoa_mot_chieu()
    a = _nen_sach(moi)
    assert health_guardrail_flags(a, dict(a)) == [], (
        "nền đã có cờ TRƯỚC khi tiêm ⇒ phép đo vùng mù vô nghĩa")


def test_moi_lan_can_mot_chieu_deu_duoc_cong_SOI():
    """Bất biến chính: mọi khoá tầng 5 **trừ mẫu số/tổng** phải làm cổng nổ khi sụp về 0."""
    moi = _moi_khoa_mot_chieu()
    mu = sorted(k for k in moi if k not in CHI_HIEN_THI and not _cong_co_soi(k, moi))
    assert not mu, (
        "VÙNG MÙ tầng 5 — các khoá này được `_ONE_WAY_PREFIXES` đẩy khỏi bảng hai chiều và gắn "
        f"nhãn 'one_way_gate: health_guardrail_flags', nhưng cổng KHÔNG soi chúng: {mu}. "
        "Đây là lời khai quản trị không có thật — đã xảy ra 3 lần, xem docstring.")


def test_khoa_CHI_HIEN_THI_khong_duoc_soi_rieng():
    """Đối chứng ngược — chống việc 'sửa' bằng cách bắt cổng soi cả mẫu số.

    `veto_calls_n` là MẪU SỐ (số lần cổng chạy) và `veto_fired_n` là TỔNG. Bắt cổng tố giác khi
    chúng giảm sẽ tạo **chiều khen** cho veto CAO — đúng hướng Goodhart mà tầng 5 sinh ra để
    chặn (`sim_metrics.py:318-321`)."""
    moi = _moi_khoa_mot_chieu()
    sai = sorted(k for k in CHI_HIEN_THI if _cong_co_soi(k, moi))
    assert not sai, (
        f"cổng đang tố giác MẪU SỐ/TỔNG {sai} — điều này tạo chiều khen cho 'veto cao', tức "
        "phần thưởng cho việc ép tài xế chạm mệt nhiều hơn để qua cổng")


def test_moi_khoa_mot_chieu_deu_co_mat_trong_a_mean():
    """`a_mean`/`b_mean` là bảng người đọc nhìn. Khoá vắng mặt ở đó thì dù cổng có soi, không ai
    kiểm lại được bằng mắt — và mẫu số vắng mặt vi phạm đúng nguyên tắc `parallel.py:561-564`
    tự phát biểu (*"MẪU SỐ phải hiện trong artifact"*)."""
    class _Pair:
        pass

    moi = _moi_khoa_mot_chieu()
    p = _Pair()
    p.system_a = {**{k: 1.0 for k in moi}, "rest_min_total": 10.0}
    p.system_b = dict(p.system_a)
    out = aggregate_health_guardrail([p])
    thieu = sorted(k for k in moi if k not in out["a_mean"])
    assert not thieu, (
        f"khoá tầng 5 KHÔNG vào `a_mean` ⇒ không hiện trong artifact A/B: {thieu}")


def test_RAIL_KHAI_TRO_phai_co_LY_DO_va_DIEU_KIEN_MO_LAI():
    """Allowlist là nơi duy nhất được phép 'trơ' — nên nó phải đắt hơn việc sửa."""
    for k, ly_do in RAIL_KHAI_TRO.items():
        assert k in _moi_khoa_mot_chieu(), f"`{k}` khai trơ nhưng không phải khoá tầng 5"
        assert len(ly_do) > 80, f"`{k}`: lý do quá ngắn để ai đó thẩm định lại"
        assert "MỞ LẠI" in ly_do, (
            f"`{k}`: thiếu ĐIỀU KIỆN MỞ LẠI — không có nó thì khai trơ là vĩnh viễn, và một "
            f"lan can chết vĩnh viễn chính là thứ cổng này đi bắt")


def test_cong_TU_CHUNG_MINH_DO_DUOC_voi_rail_chua_tung_song():
    """Đối chứng DƯƠNG TÍNH cho nhánh MỚI (rail chưa từng sống).

    Không có test này thì nhánh đó có thể không bao giờ chạy và ta sẽ tin nhầm là đã phủ."""
    moi = _moi_khoa_mot_chieu()
    a = {k: 5.0 for k in moi}
    a.update({"rest_min_total": 100.0, "veto_calls_n": 100.0, "xveto_calls_n": 100.0})
    b = dict(a)
    # `fatigued` chưa từng bắn ở CẢ HAI arm dù cổng chạy 100 lượt — phải bị tố giác
    a["veto_fatigued_n"] = b["veto_fatigued_n"] = 0.0
    flags = health_guardrail_flags(a, b)
    assert any("CHƯA TỪNG BẮN" in f for f in flags), flags

    # ...nhưng rail đã KHAI TRƠ thì im
    a2 = {k: 5.0 for k in moi}
    a2.update({"rest_min_total": 100.0, "veto_calls_n": 100.0, "xveto_calls_n": 100.0})
    b2 = dict(a2)
    a2["veto_soc_low_n"] = b2["veto_soc_low_n"] = 0.0
    assert not any("CHƯA TỪNG BẮN" in f for f in health_guardrail_flags(a2, b2)), (
        "`veto_soc_low_n` đã khai trơ mà cổng vẫn nổ ⇒ cổng sẽ bị coi là ồn và bị tắt")


def test_nhanh_chua_tung_ban_phai_SONG_cho_ho_xveto_arm_A_luon_0_calls():
    """⚠ GHIM ĐÚNG CA ĐÃ LÀM NHÁNH NÀY CHẾT (audit L4, cùng ngày Cycle 4).

    Bản đầu của nhánh *"rail CHƯA TỪNG BẮN"* đòi `calls_a > 0 AND calls_b > 0`. Với họ `xveto_`
    điều đó **không bao giờ đúng**: `check_shift_extend` trả `channel_off` ngay
    (`advice_bridge.py:1119-1120`), mà `channel_off` ∉ `EXTEND_RAILS` nên `world.py:905` không
    log ⇒ **arm A (đối chứng) LUÔN `xveto_calls_n = 0`**.

    Tức cổng vừa mở rộng sang họ `xveto_` thì nhánh mới **chết ngay cho chính họ đó** — đúng loại
    "nhánh khai mà không có đường chạy" mà file này sinh ra để bắt. Test này ghim ca đó lại."""
    moi = _moi_khoa_mot_chieu()
    a = _nen_sach(moi)
    b = dict(a)
    # arm A: kênh kéo ca TẮT ⇒ cổng không chạy lần nào (đúng như run_pair thật)
    a["xveto_calls_n"] = 0.0
    for r in EXTEND_RAILS:
        a[f"xveto_{r}_n"] = 0.0
    # arm B: kênh BẬT, cổng chạy 200 lượt, nhưng rail `fatigued` chưa từng bắn
    b["xveto_calls_n"] = 200.0
    b["xveto_fatigued_n"] = 0.0
    flags = health_guardrail_flags(a, b)
    assert any("xveto_fatigued_n" in f and "CHƯA TỪNG BẮN" in f for f in flags), (
        "nhánh 'chưa từng bắn' CHẾT cho họ xveto_ — vì arm A của run_pair luôn có "
        f"xveto_calls_n=0. flags={flags}")


def test_kenh_TAT_thi_khong_to_giac_nham():
    """Mẫu số = 0 nghĩa là cổng KHÔNG chạy (kênh tắt), không phải 'lan can vô dụng'.

    Thiếu phân biệt này thì cổng sẽ đỏ trên mọi run mặc định — nơi cả 6 kênh advisor đều tắt —
    và sẽ bị tắt trong vòng một ngày."""
    moi = _moi_khoa_mot_chieu()
    a = {k: 0.0 for k in moi}
    a.update({"rest_min_total": 100.0, "work_span_p90": 100.0, "drive_min_p90": 100.0})
    assert health_guardrail_flags(a, dict(a)) == [], (
        "kênh tắt (mọi mẫu số 0) mà cổng vẫn tố giác ⇒ cổng vô dụng vì luôn đỏ")


@pytest.mark.parametrize("made,kept,broken,cleared,phai_do", [
    (RAIL_ALIVE_MIN_N + 5, 0, 0, 0, True),        # hứa nhiều, KHÔNG kết cục nào ⇒ sống trên giấy
    (RAIL_ALIVE_MIN_N + 5, 3, 2, 1, False),       # có kết cục ⇒ im
    (5, 0, 0, 0, False),                          # mẫu quá nhỏ ⇒ không phân biệt được với nhiễu
    (10, 6, 5, 4, True),                          # vỡ bảo toàn: 15 > 10
])
def test_so_CAM_KET_bi_soi(made, kept, broken, cleared, phai_do):
    """`D-M3-04-FIX` dựng sổ cam kết để 'hoãn = lời hứa' không sống trên giấy — nhưng sổ đó
    chưa từng được cổng nào soi."""
    moi = _moi_khoa_mot_chieu()
    a = {k: 50.0 for k in moi}
    a.update({"rest_min_total": 100.0, "work_span_p90": 100.0, "drive_min_p90": 100.0})
    b = dict(a)
    b.update({"commit_made_n": made, "commit_kept_n": kept,
              "commit_broken_n": broken, "commit_cleared_n": cleared})
    co_flag = any("CAM KẾT" in f for f in health_guardrail_flags(a, b))
    assert co_flag is phai_do
