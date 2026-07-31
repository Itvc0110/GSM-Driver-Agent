"""D-M3-11 — RÒ RỈ THÔNG TIN TƯƠNG LAI ở các L3 view derive từ bảng thật (l1r).

Root cause (chứng minh 2026-08-01, không phải phỏng đoán): vòng lặp gom idle segment chỉ lọc
theo **NGÀY** (`seen[:10] != d`) và **không bao giờ so với `t_now`**. Hệ quả: gọi view ở 23:00
vẫn nhận về dwell **bắt đầu 23:03 và 23:27** — thứ chưa xảy ra tại thời điểm hỏi.

Bằng chứng phát hiện ra nó: `tests/test_idle_reduction.py::test_bug01_idle_never_exceeds_online_time`
đỏ ở `d-62` `2026-07-03` với idle **247,48′** > online **246,00′**. Phân rã đo được:
- 2 segment BẮT ĐẦU sau `t_now` ⇒ **37,15′** hoàn toàn chưa xảy ra;
- 1 segment ĐANG diễn ra bị tính TRỌN cả phần sau `t_now` ⇒ **2,82′** nữa.
Bỏ hai phần đó: 247,48 → **207,51′**, dưới online ⇒ bất biến vật lý được phục hồi.

Vì sao đây là lỗi ĐƯỜNG SẢN PHẨM chứ không phải chuyện của mock: `total_idle_min`/
`longest_idle_min` là đầu vào S7 IdleReduction — lời khuyên giảm-chờ nói cho tài xế lúc `t_now`
được tính trên thời gian tài xế sẽ chờ TRONG TƯƠNG LAI. Ngoài đời view này đọc bảng thật; một
tài xế thật không có dữ liệu 23:27 lúc 23:00, nên số của sim/mock **lạc quan hơn số chạy thật**.

`from_l1r.py:84` (`complete_time <= t_now`) chứng minh repo BIẾT luật này — deriver idle **bỏ
sót** nó, không phải chọn khác. Đây là hạng mục đầu tiên trong danh sách adversarial self-review
của `CLAUDE.md` §4b: *future-information leak*.
"""
from __future__ import annotations

from gsm_core.features.from_l1r import derive_idle_reduction_input_l1r

D = "2026-07-03"
T_NOW = f"{D}T20:00:00+07:00"


def _hex_row(start: str, dur_s: int, status: str = "idle") -> dict:
    return {"driver_id": "d-1", "current_hex": "h1", "tracking_status": status,
            "entered_current_hex_at": start, "last_seen_at": start,
            "stay_duration_seconds": dur_s, "campaign_id": None, "target_hex": None,
            "reached_target": None}


def _l1r(rows: list[dict], online_h: float = 8.0) -> dict:
    return {"public_driver_hex_tracking": rows, "trips": [],
            "driver_online_hours_sap_id": [{"driver_id": "d-1", "local_date": D,
                                            "online_time": online_h, "source": "MOCK"}]}


def _view(rows: list[dict], **kw):
    return derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r(rows), session_date=D, **kw)


def test_segment_bat_dau_sau_t_now_bi_loai():
    """Dwell 21:00 không tồn tại đối với người hỏi lúc 20:00."""
    v = _view([_hex_row(f"{D}T18:00:00+07:00", 600),
               _hex_row(f"{D}T21:00:00+07:00", 1800)])
    assert v["total_idle_min"] == 10.0, (
        f"segment 21:00 (chưa xảy ra lúc {T_NOW}) bị tính vào — rò rỉ tương lai: {v}")
    assert len(v["idle_segments"]) == 1


def test_segment_dang_dien_ra_bi_cat_ve_t_now():
    """Bắt đầu 19:50, kéo 30′ ⇒ tại 20:00 chỉ QUAN SÁT ĐƯỢC 10′, không phải 30′."""
    v = _view([_hex_row(f"{D}T19:50:00+07:00", 1800)])
    assert v["total_idle_min"] == 10.0, f"phần sau t_now bị tính trọn: {v}"
    assert v["longest_idle_min"] == 10.0
    assert v["idle_segments"][0]["duration_seconds"] == 600


def test_cat_xong_ma_ngan_hon_nguong_thi_khong_con_la_cho_lau():
    """Dwell mới bắt đầu 19:58 (2′ tại t_now) chưa đủ `idle_min_seconds` ⇒ không phải segment
    'chờ lâu'. Nếu giữ nó, ta báo tài xế đang chờ lâu trong khi họ vừa dừng 2 phút."""
    v = _view([_hex_row(f"{D}T19:58:00+07:00", 1800)])
    assert v["idle_segments"] == [], v
    assert v["total_idle_min"] == 0.0


def test_qua_khu_nguyen_ven_khong_bi_cat_oan():
    """Đối chứng: dwell kết thúc TRƯỚC t_now phải giữ nguyên từng giây — fix không được
    ăn bớt quá khứ."""
    v = _view([_hex_row(f"{D}T10:00:00+07:00", 900),
               _hex_row(f"{D}T12:00:00+07:00", 660)])
    assert v["total_idle_min"] == 26.0, v
    assert v["longest_idle_min"] == 15.0


def test_bat_bien_idle_khong_vuot_online_tren_mock_that():
    """Bất biến VẬT LÝ trên chính driver-day đã phơi ra bug (`d-62` `2026-07-03`), đo qua
    mock deterministic — đây là ca reproduce của D-M3-11."""
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from gsm_core.mockgen.realdata import generate_realdata
    with TemporaryDirectory() as td:
        t = generate_realdata(days=6, seed_base=900, out_dir=Path(td))["tables"]
    onl = {(r["driver_id"], r["local_date"]): r["online_time"]
           for r in t["driver_online_hours_sap_id"]}
    v = derive_idle_reduction_input_l1r("d-62", f"{D}T23:00:00+07:00", t, session_date=D)
    online_min = onl[("d-62", D)] * 60
    assert v["total_idle_min"] <= online_min, (
        f"idle {v['total_idle_min']:.2f}′ > online {online_min:.0f}′ — không thể chờ lâu hơn "
        f"thời gian có mặt (D-M3-11)")
    for s in v["idle_segments"]:
        assert s["start"] < f"{D}T23:00:00+07:00", f"segment tương lai còn sót: {s}"


# ---------- hai rò rỉ NỮA trong cùng deriver, do probe tổng quát tìm ra ----------
# Probe: gọi view trên bảng đầy đủ vs bảng đã XOÁ mọi record sau t_now. Khác nhau ⇒ đọc tương
# lai. Nó bắt được hai field mà mắt tôi bỏ qua khi chỉ nhìn `idle_segments`.


def test_demand_by_hour_khong_thay_cau_cua_tuong_lai():
    """`demand_by_hour` gộp MỌI ngày trong bảng nên không cắt là để lọt cầu buổi chiều chưa
    diễn ra — đúng thứ S7 định khuyên ("đứng đâu giờ nào"). Chuẩn hoá theo đỉnh khiến rò rỉ
    này bóp méo CẢ hình dạng, không chỉ một ô."""
    rows = [_hex_row(f"{D}T10:00:00+07:00", 600)]
    l1r = _l1r(rows)
    l1r["trips"] = [
        {"driver_id": "d-1", "request_time": f"{D}T09:00:00+07:00",
         "complete_time": f"{D}T09:20:00+07:00", "gross_vnd": 50000},
        {"driver_id": "d-1", "request_time": f"{D}T09:30:00+07:00",
         "complete_time": f"{D}T09:50:00+07:00", "gross_vnd": 50000},
        {"driver_id": "d-1", "request_time": f"{D}T22:00:00+07:00",   # SAU t_now=20:00
         "complete_time": f"{D}T22:20:00+07:00", "gross_vnd": 50000},
    ]
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, l1r, session_date=D)
    assert "22" not in v["demand_by_hour"], f"cầu giờ 22 chưa xảy ra lúc 20:00: {v['demand_by_hour']}"
    assert v["demand_by_hour"] == {"9": 1.0}, v["demand_by_hour"]


def test_active_reposition_chua_bat_dau_thi_khong_ton_tai():
    r = _hex_row(f"{D}T21:00:00+07:00", 1800, status="active")
    r.update(campaign_id="repo-01", target_hex="h9", reached_target=True)
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r([r]), session_date=D)
    assert v["active_reposition"] is None, v["active_reposition"]


def test_active_reposition_dang_dien_ra_thi_ket_cuc_CHUA_CHOT():
    """`reached_target_at` rỗng trong cả mock lẫn 13 bảng thật ⇒ với segment còn đang diễn ra
    ta KHÔNG biết đã tới đích chưa. Khai `None` = chưa biết, thay vì chép True của tương lai."""
    r = _hex_row(f"{D}T19:50:00+07:00", 1800, status="active")     # kết thúc 20:20 > t_now
    r.update(campaign_id="repo-01", target_hex="h9", reached_target=True,
             last_seen_at=f"{D}T20:20:00+07:00")
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r([r]), session_date=D)
    assert v["active_reposition"]["campaign_id"] == "repo-01"
    assert v["active_reposition"]["reached"] is None, v["active_reposition"]


def test_reposition_da_ket_thuc_thi_ket_cuc_doc_duoc():
    """Đối chứng: segment đã đóng trước t_now ⇒ kết cục là dữ kiện, phải đọc được."""
    r = _hex_row(f"{D}T10:00:00+07:00", 600, status="active")
    r.update(campaign_id="repo-01", target_hex="h9", reached_target=True,
             last_seen_at=f"{D}T10:10:00+07:00")
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r([r]), session_date=D)
    assert v["active_reposition"]["reached"] is True, v["active_reposition"]


# ---------- cùng HỌ lỗi ở HAI deriver khác — probe tổng quát tìm ra ----------
# Probe (chạy 2026-08-01, seed 900, t_now=08:00): gọi mỗi deriver hai lần — bảng đầy đủ vs bảng
# đã xoá record sau t_now. `bonus_gap.historical_points_per_hour` và `shift_plan.points_now`
# đổi giá trị ⇒ cả hai đọc tương lai. `weekly_khoan`, `penalty_explain`, `anomaly_alert`,
# `mission_select` KHÔNG đổi ⇒ sạch (đã kiểm, không phải giả định).

import pytest

from gsm_core.features.from_l1r import (derive_bonus_gap_input_l1r,
                                       derive_shift_plan_input_l1r)
from gsm_core.policy import PolicyBundle

POLICY_REC = {   # cùng bundle với tests/test_features_from_l1r.py (giữ một nguồn)
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300}, "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                   "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}


@pytest.fixture
def pol():
    return PolicyBundle.from_record(POLICY_REC)


def _trip(day: str, hour: int, cell: str = "c1") -> dict:
    t = f"{day}T{hour:02d}:00:00+07:00"
    return {"driver_id": "d-1", "request_time": t, "complete_time": t,
            "gross_vnd": 50000, "pickup_h3": cell}


def _onl(day: str, h: float = 8.0) -> dict:
    return {"driver_id": "d-1", "local_date": day, "online_time": h, "source": "MOCK"}


def test_historical_points_per_hour_khong_gom_ngay_SAU_hom_nay(pol):
    """`- {today}` bỏ đúng hôm nay nhưng KHÔNG bỏ ngày sau hôm nay. Ba ngày "lịch sử" ở đây
    toàn là TƯƠNG LAI ⇒ prior phải rỗng, không phải có số."""
    days_tuong_lai = ["2026-07-04", "2026-07-05", "2026-07-06"]
    l1r = {"trips": [_trip(d, 8) for d in days_tuong_lai] * 2,
           "driver_online_hours_sap_id": [_onl(d) for d in days_tuong_lai],
           "driver_statistic_daily": [], "public_driver_hex_tracking": []}
    v = derive_bonus_gap_input_l1r("d-1", "2026-07-03T20:00:00+07:00", l1r, pol)
    assert v["historical_points_per_hour"] == {}, (
        f"tốc độ điểm 'lịch sử' tính từ ngày CHƯA TỚI: {v['historical_points_per_hour']}")


def test_historical_van_dung_ngay_qua_khu_that(pol):
    """Đối chứng: 3 ngày THẬT trong quá khứ ⇒ prior phải có số (fix không được làm rỗng oan)."""
    qua_khu = ["2026-06-30", "2026-07-01", "2026-07-02"]
    l1r = {"trips": [_trip(d, 8) for d in qua_khu] * 2,
           "driver_online_hours_sap_id": [_onl(d) for d in qua_khu],
           "driver_statistic_daily": [], "public_driver_hex_tracking": []}
    v = derive_bonus_gap_input_l1r("d-1", "2026-07-03T20:00:00+07:00", l1r, pol)
    assert v["historical_points_per_hour"], "prior rỗng dù có đủ 3 ngày quá khứ thật"


def test_shift_plan_points_now_cat_tai_t_now(pol):
    """Họ AUDIT A3 LAYEROUT-4: `derive_bonus_gap_input_l1r` đã cắt từ UPDATE-070, deriver này
    bỏ sót ⇒ 08:00 sáng đã cộng điểm của cuốc chạy chiều."""
    d = "2026-07-03"
    l1r = {"trips": [_trip(d, 6), _trip(d, 18)],       # 6h đã xong, 18h chưa xảy ra
           "driver_online_hours_sap_id": [_onl(d)],
           "driver_statistic_daily": [], "public_driver_hex_tracking": []}
    v = derive_shift_plan_input_l1r("d-1", f"{d}T08:00:00+07:00", l1r, pol)
    assert v["points_now"] == pol.trip_points(6), (
        f"points_now={v['points_now']} gồm cả cuốc 18:00 chưa chạy")


def test_shift_plan_demand_forecast_khong_nuoi_bang_tuong_lai(pol):
    """Dự báo NÓI về tương lai là đúng; DỮ LIỆU nuôi nó thì không được lấy từ tương lai —
    nếu không, "kỳ vọng đơn" ở ô nào giờ nào chính là đáp án đã biết trước."""
    d = "2026-07-03"
    l1r = {"trips": [_trip(d, 6, "c_qua_khu")] + [_trip(d, 19, "c_tuong_lai")] * 5,
           "driver_online_hours_sap_id": [_onl(d)],
           "driver_statistic_daily": [], "public_driver_hex_tracking": []}
    v = derive_shift_plan_input_l1r("d-1", f"{d}T08:00:00+07:00", l1r, pol)
    cells = {f["cell_cluster"] for f in v["demand_forecast"]}
    assert "c_tuong_lai" not in cells, (
        f"dự báo được nuôi bằng 5 cuốc 19:00 chưa xảy ra: {v['demand_forecast'][:3]}")


# ---------- đường PARSE LỖI của `_observed_seconds` (nợ D-M3-12, phần test) ----------
# Self-review UPDATE-115 tự ghi: fallback "giữ nguyên `dur_s`" là **fallback im lặng** — đúng loại
# thứ repo đã trả giá vì nó. Ba test dưới PIN hành vi đó cho tường minh, để lần sau ai đổi nó
# phải đổi có ý thức; phần còn lại của nợ (KHAI cờ ra output thay vì im lặng) cần sửa schema
# `additionalProperties: false` nên nằm ngoài cycle này.


def test_timestamp_rac_o_CA_HAI_field_thi_record_bi_loc_NGAY_loai():
    """Đo được, không phải giả định: nếu `last_seen_at` cũng rác thì `seen[:10] != d` loại record
    NGAY, chưa tới `_observed_seconds`. Hợp lý — không biết ngày thì không thuộc ngày này."""
    v = derive_idle_reduction_input_l1r(
        "d-1", T_NOW, _l1r([_hex_row("khong-phai-timestamp", 900)]), session_date=D)
    assert v["total_idle_min"] == 0.0, v


def test_start_rac_nhung_seen_hop_le_thi_LUI_VE_seen_khong_NO():
    """🔴 Bug CÓ TRƯỚC `D-M3-11`, test này phơi ra: `_hour(start)` làm `int(iso[11:13])` nên
    timestamp rác gây **ValueError — view NỔ** thay vì degrade. (`or seen` cũ chỉ đỡ field RỖNG,
    không đỡ field RÁC.) Nay lùi về `last_seen_at`: dwell 12:00 kéo 15′ đã đóng trước `t_now`
    nên giữ trọn 15′."""
    r = _hex_row("khong-phai-timestamp", 900)
    r["last_seen_at"] = f"{D}T12:00:00+07:00"
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r([r]), session_date=D)
    assert v["total_idle_min"] == 15.0, v
    assert v["idle_segments"][0]["hour"] == 12, v["idle_segments"]


def test_ca_hai_timestamp_rac_nhung_qua_loc_ngay_thi_BO_record():
    """Ca biên: `last_seen_at` khớp 10 ký tự đầu (`2026-07-03…`) nên qua lọc ngày nhưng KHÔNG
    parse được ⇒ record không định vị được trong thời gian ⇒ bỏ, vì mọi số của nó vô nghĩa.
    Trước fix ca này cũng làm view NỔ."""
    r = _hex_row("2026-07-03Trac", 900)
    r["last_seen_at"] = "2026-07-03Trac-nua"
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r([r]), session_date=D)
    assert v["idle_segments"] == [] and v["total_idle_min"] == 0.0, v


def test_naive_datetime_thi_giu_nguyen_khong_no_TypeError():
    """So aware với naive là `TypeError` trong Python. Bảng thật có thể thiếu offset ⇒ phải
    không nổ, và phải giữ số thay vì bỏ segment."""
    r = _hex_row(f"{D}T19:50:00", 1800)      # không có +07:00
    v = derive_idle_reduction_input_l1r("d-1", T_NOW, _l1r([r]), session_date=D)
    assert v["total_idle_min"] == 30.0, v


def test_fallback_nay_la_VUNG_MU_da_khai():
    """⚠ Test này ghi lại một sự thật KHÔNG dễ chịu: với dữ liệu naive, việc cắt `t_now` **im
    lặng không có tác dụng** — tức fix D-M3-11 vô hiệu ở đúng loại dữ liệu đó, và view không hề
    báo ra. Nếu bảng thật GSM không dùng offset, phải đóng nốt `D-M3-12` TRƯỚC khi tin số."""
    naive = derive_idle_reduction_input_l1r(
        "d-1", T_NOW, _l1r([_hex_row(f"{D}T19:50:00", 1800)]), session_date=D)
    aware = derive_idle_reduction_input_l1r(
        "d-1", T_NOW, _l1r([_hex_row(f"{D}T19:50:00+07:00", 1800)]), session_date=D)
    assert naive["total_idle_min"] == 30.0 and aware["total_idle_min"] == 10.0, (naive, aware)
    assert naive["source"] == aware["source"], (
        "nếu một ngày source phân biệt được hai ca này thì D-M3-12 đã đóng — cập nhật test")
