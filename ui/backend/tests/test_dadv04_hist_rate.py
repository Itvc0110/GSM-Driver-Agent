"""`D-ADV-04` trên ĐƯỜNG SẢN PHẨM — mẫu số bucket + hedge sát biên.

Đây là đường mà lỗi đập thẳng vào card của tài xế thật: `S1` là solver **duy nhất** đường này chạy
(`B6-PARITY`), và bản cũ chia điểm-của-bucket cho `online_time` **TOÀN NGÀY** trong khi solver tiêu thụ
số đó như điểm/giờ **TRONG bucket** ⇒ hệ nói *"không với tới mốc"* về mốc **với tới được**.
"""

import polars as pl
import pytest

from app.adapters.advisor import _hist_rate, _table, _trips_of, build_gi, policy


def _driver_co_lich_su() -> tuple[str, str]:
    """Chọn một (tài xế, ngày) có ≥3 ngày lịch sử trước đó — điều kiện để tin rate cá nhân."""
    tr = _table("trips")
    dates = sorted({i[:10] for i in tr["request_time"].to_list()})
    date = dates[-1]
    for drv in sorted(set(tr["driver_id"].to_list())):
        t = _trips_of(drv)
        truoc = {i[:10] for i in t["request_time"].to_list() if i[:10] < date}
        if len(truoc) >= 4:
            return drv, date
    pytest.skip("bộ mock không có tài xế nào đủ 4 ngày lịch sử")


def test_hist_rate_tra_ve_ca_NHAN_va_cach_suy_mau_so():
    """Chữ ký mới trả `(rate, method)` — nhãn xấp xỉ phải đi CÙNG số, không tách rời.

    Bảng thật chỉ có TỔNG `online_time` (không có `go_online`/`go_offline`) ⇒ giờ-trong-bucket là
    XẤP XỈ; trình bày nó như số đo là nói quá về độ chắc.
    """
    drv, date = _driver_co_lich_su()
    rate, method = _hist_rate(_trips_of(drv), drv, date, policy())
    assert isinstance(rate, dict) and isinstance(method, str)
    assert method in ("measured_intervals", "estimated_span_scaled", "day_average_mixed", "none")
    assert all(v >= 0 for v in rate.values())


def test_rate_peak_khong_con_o_bac_cua_quy_uoc_cu():
    """Quy ước cũ nén rate peak xuống theo tỷ số `giờ_ngày / giờ_peak` (peak thường 2–5×).

    Không đòi một con số cụ thể (dữ liệu mock, mỗi tài xế một hình dạng) — đòi **quan hệ**: rate peak
    theo mẫu số TRONG BUCKET phải **lớn hơn** rate theo mẫu số toàn ngày, vì `giờ_ngày ≥ giờ_bucket`.
    Đây là bất đẳng thức TOÁN HỌC, không phải kỳ vọng thống kê ⇒ test đúng cho mọi tài xế.
    """
    pol = policy()
    tr, onl = _table("trips"), _table("driver_online_hours_sap_id")
    dates = sorted({i[:10] for i in tr["request_time"].to_list()})
    date = dates[-1]
    da_kiem = 0
    for drv in sorted(set(tr["driver_id"].to_list()))[:20]:
        t = _trips_of(drv)
        rate, _ = _hist_rate(t, drv, date, pol)
        if "peak" not in rate or rate["peak"] <= 0:
            continue
        oh_by = {r["local_date"]: float(r["online_time"])
                 for r in onl.filter(pl.col("driver_id") == drv).iter_rows(named=True)}
        # quy ước CŨ nguyên văn, tính lại tại chỗ để so
        days = sorted({i[:10] for i in t["request_time"].to_list() if i[:10] < date})[-7:]
        cu = []
        for d in days:
            oh = oh_by.get(d, 0.0)
            if oh <= 0:
                continue
            p = sum(pol.trip_points(int(i[11:13])) for i in
                    t.filter(pl.col("request_time").str.starts_with(d))["request_time"].to_list()
                    if pol.is_peak(int(i[11:13])))
            if p > 0:
                cu.append(p / oh)
        if len(cu) >= 3:
            rate_cu = sorted(cu)[len(cu) // 2]
            assert rate["peak"] >= rate_cu - 1e-9, (
                f"{drv}: rate peak mới {rate['peak']} < quy ước cũ {rate_cu} — sai chiều bất đẳng thức")
            da_kiem += 1
    assert da_kiem >= 1, "không kiểm được tài xế nào có rate peak — fixture/dữ liệu đổi?"


def test_build_gi_mang_nhan_va_schema_1_1_0():
    drv, date = _driver_co_lich_su()
    gi = build_gi(drv, date, 14 * 60)
    assert gi["schema_version"] == "1.1.0"
    assert "historical_rate_method" in gi, "số xấp xỉ mà không có nhãn cách suy"


def test_card_feasible_co_hedge_khi_sat_bien():
    """Sửa mẫu số làm advisor bớt bi quan ⇒ rủi ro MỚI là hứa hẹn ở dải 50-50.

    Khi `sensitivity` của solver có cờ `flips_feasible` (rate giảm 20% là trượt mốc), card phải có
    **một câu** cảnh báo sát biên — và **không được thêm số nào** (không cam kết mức thưởng).
    """
    from gsm_core.solvers.bonus_feasibility import solve
    from app.adapters.advisor import advice
    pol = policy()
    tr = _table("trips")
    dates = sorted({i[:10] for i in tr["request_time"].to_list()})
    n_sat_bien = 0
    for drv in sorted(set(tr["driver_id"].to_list()))[:40]:
        for date in dates[-3:]:
            for now_min in (10 * 60, 14 * 60, 17 * 60):
                gi = build_gi(drv, date, now_min)
                if not gi["next_tiers"]:
                    continue
                report = solve(gi, pol)
                if not report["solution"].get("feasible"):
                    continue
                if not any(s.get("flips_feasible") for s in (report.get("sensitivity") or [])):
                    continue
                items = [i for i in (advice(drv, date, now_min).get("items") or [])
                         if i.get("reason_code") == "feasible_gap"]
                if not items:
                    continue
                card = items[0]
                assert "sát biên" in (card.get("caveat") or ""), (
                    f"card feasible SÁT BIÊN mà không cảnh báo: {card.get('caveat')!r}")
                n_sat_bien += 1
                if n_sat_bien >= 2:
                    return
    if not n_sat_bien:
        pytest.skip("bộ mock hiện không có ca feasible-sát-biên để kiểm (cần dữ liệu khác)")
