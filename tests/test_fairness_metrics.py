"""ĐA-08 bước 1 — bộ đo CÔNG BẰNG / TẬP TRUNG / KHÁCH HÀNG (đo trước, sửa solver sau).

Vì sao cần: hồ sơ `research/audit/2026-07-27-current-state/07` đo được advice diện rộng làm
`served_rate` giảm 6/10 seed và đơn hết hạn +8/ngày, nhưng guardrail A/B hiện KHÔNG có metric nào
bắt được điều đó — nó chỉ có 5 trường và còn ép `coverage="single"` (chế độ mà tác động hệ thống
gần bằng 0 theo thiết kế). Bộ này là điều kiện tiên quyết của chỉ tiêu kép.
"""

from __future__ import annotations

import pytest

from gsm_sim.config import Config
from gsm_sim.runner import run_once
from gsm_sim import sim_metrics as SM

SEED = 1000


@pytest.fixture(scope="module")
def result():
    return run_once(Config.load("configs/pilot_dongda.yaml"), SEED)


# ---------- Gini ----------

def test_gini_known_values():
    """Tính chất toán học phải đúng trước khi tin số trên data thật."""
    assert SM.gini([100, 100, 100, 100]) == pytest.approx(0.0, abs=1e-9), "phân phối đều ⇒ 0"
    assert SM.gini([0, 0, 0, 400]) == pytest.approx(0.75, abs=0.01), "n-1 người trắng tay ⇒ (n-1)/n"
    assert SM.gini([]) == 0.0 and SM.gini([0, 0]) == 0.0, "biên không được chia 0"
    assert 0.0 <= SM.gini([50, 120, 300, 900]) <= 1.0
    # bất biến theo thang: nhân đôi mọi thu nhập KHÔNG đổi bất bình đẳng
    assert SM.gini([50, 120, 300]) == pytest.approx(SM.gini([100, 240, 600]), abs=1e-9)


def test_fairness_metrics_on_real_run(result):
    f = SM.fairness_metrics(result)
    assert 0.0 <= f["gini_payout"] <= 1.0
    assert f["payout_p10"] <= f["payout_median"] <= f["payout_p90"]
    assert f["total_payout_vnd"] > 0, "cần TỔNG payout để phân biệt positive-sum vs tái phân phối"
    assert f["n_actors"] > 0


# ---------- Tập trung (herding) ----------

def test_concentration_metrics_on_real_run(result):
    c = SM.concentration_metrics(result)
    # HHI chuẩn hoá: 0 = trải đều tuyệt đối, 1 = dồn hết vào một chỗ
    assert 0.0 <= c["station_hhi"] <= 1.0
    assert 0.0 <= c["supply_cell_hhi"] <= 1.0
    assert c["peak_swap_per_hour"] >= 0 and c["peak_rest_per_hour"] >= 0


def test_supply_cell_hhi_is_not_silently_zero(result):
    """REGRESSION cho flaw của CHÍNH bản nháp này (tự phát hiện, UPDATE-075 §3).

    Bản đầu đọc `segment["cell"]` — **field đó KHÔNG tồn tại** (`world._seg` chỉ ghi
    `from_lat/from_lon/to_lat/to_lon`). Hệ quả: `supply_cell_hhi` luôn = 0.0, và test cũ
    `0 <= hhi <= 1` vẫn XANH. Đây đúng loại "hidden fallback trả 0 im lặng" mà CLAUDE §4b bắt
    phải soi. Test này ràng buộc việc quy ô có THẬT SỰ xảy ra.
    """
    c = SM.concentration_metrics(result)
    assert c["n_supply_cells"] >= 2, "không quy được ô nào ⇒ metric là số 0 giả"
    assert c["supply_cell_hhi"] > 0.0, "90 tài xế không thể trải đều TUYỆT ĐỐI — 0.0 là dấu hiệu bug"
    assert c["supply_minutes_total"] > 0


def test_hhi_edges():
    assert SM.hhi([10]) == pytest.approx(1.0), "một chỗ ôm hết ⇒ 1"
    assert SM.hhi([5, 5, 5, 5]) == pytest.approx(0.0, abs=1e-9), "trải đều ⇒ 0"
    assert SM.hhi([]) == 0.0


# ---------- Khách hàng ----------

def test_customer_impact_includes_expired(result):
    """`customer_wait` cũ CHỈ tính đơn được ghép — chính đơn KHÔNG ai nhận mới là hại lớn nhất
    cho khách. Bộ mới phải tách rõ hai nhóm."""
    ci = SM.customer_impact(result)
    assert ci["expired_n"] >= 0
    # hàm làm tròn 4 chữ số ⇒ tolerance phải nới tương ứng (5e-5), không chặt hơn chính nó
    assert ci["expired_rate"] == pytest.approx(ci["expired_n"] / max(1, ci["orders_total"]), abs=5e-5)
    assert ci["wait_median_min"] >= 0
    assert "unserved_breakdown" in ci, "phải tách expired/censored/cancelled — không gộp một cục"


# ---------- Gói guardrail dùng cho A/B ----------

def test_system_guardrail_bundle_has_all_five_layers(result):
    """Chỉ tiêu kép cần đủ NĂM tầng: hệ thống · khách hàng · công bằng · tập trung ·
    SỨC KHOẺ (D-M3-05, 2026-07-31 — tầng 5 tố giác đòn xoá-lan-can mà 4 tầng cũ mù)."""
    g = SM.system_guardrail(result)
    for key in ("served_rate", "total_payout_vnd", "expired_n", "wait_median_min",
                "gini_payout", "station_hhi", "supply_cell_hhi", "starved_hours_n",
                "rest_min_total", "veto_fired_n", "work_span_p90", "drive_min_p90"):
        assert key in g, f"guardrail thiếu {key}"


def test_starved_hours_comes_from_supply_demand_density(result):
    """`supply_demand_density()` đã viết + test từ SIM-5 nhưng **chưa consumer nào gọi** ngoài
    test — spec §6.1 yêu cầu nối vào guardrail. Nối bằng scalar `starved_hours_n` (số giờ có
    >40% đơn hết hạn), là dạng so sánh được A/B; giữ nguyên hàm gốc làm nguồn duy nhất."""
    g = SM.system_guardrail(result)
    assert g["starved_hours_n"] == len(SM.supply_demand_density(result)["starved_hours"])
