"""E1b — sửa CÔNG THỨC KÊNH (UPDATE-151 r10 ADV-01..05/07; plan E1 duyệt 2026-08-06).

Batch (i): solver S2/S1 + gate accept_lift + kênh kéo ca. Viết ĐỎ-TRƯỚC 2026-08-06.
Reproduce đã làm trước khi viết: CLI smoke 2 seed cho Δ=0 TUYỆT ĐỐI ở s2_only (UPDATE-152 §quan
sát) — khớp ADV-01: band điểm floor mỗi bucket nên mốc thưởng không bao giờ vào giá trị Bellman,
tức F-098-01 (gate lại về CÓ CẦU để "bonus trả cho lỗ nhỏ") chưa bao giờ chạy được phần bonus.
"""
from __future__ import annotations

import inspect

import pytest

from gsm_core.policy import PolicyBundle as CorePolicy
from gsm_core.solvers import shift_dp
from gsm_core.solvers.bonus_feasibility import _hour_rate
from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.config import Config
from gsm_sim.policy import PolicyBundle as SimPolicy


@pytest.fixture(scope="module")
def policy() -> CorePolicy:
    sp = SimPolicy.from_config(Config.load("configs/pilot_dongda.yaml"))
    return CorePolicy.from_record(sp.to_core_record())


def _spi(b: int, points_now: int, eo: float = 1.0, start_h: int = 9, **extra) -> dict:
    rows = []
    for i in range(b):
        h, m = start_h + (i // 2), (i % 2) * 30
        rows.append({"bucket": f"2026-09-28T{h:02d}:{m:02d}:00", "expected_orders": eo})
    return {"driver_id": "d-test", "t_now": f"2026-09-28T{start_h:02d}:00:00",
            "view_version": "test", "source": "MOCK", "points_now": points_now,
            "buckets_remaining": b, "demand_forecast": rows, "soc_pct": 100.0, **extra}


# ---------- ADV-01: mốc thưởng phải LÁI ĐƯỢC lịch DP ----------

def test_dp_an_lo_nho_de_lay_moc_thuong(policy):
    """Kịch bản F-098-01 nguyên bản: 45 điểm, thiếu 15 tới mốc 60 (+30.000đ), net/cuốc −225đ
    (cash 4.400đ/km × 3km = 13.200 > ppo 12.975). DP đúng phải CHẠY 3 bucket ăn lỗ 675đ đổi
    30.000đ. Bản cũ: `add_pts // PBS` với add=5 < PBS=15 ⇒ band ĐÓNG BĂNG ⇒ bonus không bao giờ
    vào Bellman ⇒ DP trốn lỗ, bỏ mốc."""
    p = {"p_accept": 1.0, "avg_dist_km": 3.0, "cash_cost_vnd_per_km": 4400.0}
    rep = shift_dp.solve(_spi(4, points_now=45), policy, p)
    sol = rep["solution"]
    n_online = sum(1 for s in sol["schedule"] if s["action"] == "ONLINE")
    assert n_online >= 3, f"DP bỏ mốc 60 (+30.000đ) để né lỗ 675đ: {sol['schedule']}"
    assert sol["projected_bonus_tier"] == 30000, sol


def test_doi_chung_khong_co_moc_thi_ne_lo(policy):
    """Đối chứng ngược: cùng net âm nhưng điểm 0 (mốc 60 cần 12 bucket — ngoài tầm B=4)
    ⇒ DP đúng phải KHÔNG chạy bucket lỗ nào."""
    p = {"p_accept": 1.0, "avg_dist_km": 3.0, "cash_cost_vnd_per_km": 4400.0}
    sol = shift_dp.solve(_spi(4, points_now=0), policy, p)["solution"]
    assert sum(1 for s in sol["schedule"] if s["action"] == "ONLINE") == 0, sol["schedule"]


# ---------- ADV-04: baseline được TÍN DỤNG nghỉ như nhánh DP ----------

def test_baseline_duoc_tin_dung_nghi_da_nghi(policy):
    """`_baseline_naive_rest` bản cũ gọi `_required_rest(B, params)` KHÔNG truyền state ⇒
    tài xế đã nghỉ 120′ vẫn bị baseline ép nghỉ thêm ⇒ baseline thấp giả ⇒ delta DP thổi phồng
    một cách hệ thống. spi ĐÃ mang hai trường state (nhánh DP đang dùng)."""
    p = {**shift_dp.DEFAULT_PARAMS, "p_accept": 1.0, "avg_dist_km": 3.0}
    spi = _spi(8, points_now=0, rest_taken_min=120.0, shift_elapsed_min=240.0)
    base_credit, _ = shift_dp._baseline_naive_rest(spi, policy, p)
    ppo = shift_dp._payout_per_order(policy, 3.0)
    # 8 bucket × 240′ đã qua với 120′ nghỉ: surplus 3 bucket > nhu cầu còn lại 1 ⇒ R=0 ⇒ 8 cuốc
    assert base_credit == pytest.approx(8 * ppo, rel=1e-6), \
        f"baseline không nhận tín dụng nghỉ: {base_credit} vs {8 * ppo}"


# ---------- ADV-05: lịch sử 0.0 điểm/giờ là DỮ LIỆU, không phải thiếu ----------

def test_s1_lich_su_0_diem_gio_la_du_lieu_hop_le(policy):
    """`_hour_rate` bản cũ: `hist[bucket] > 0` ⇒ tài xế có lịch sử 0.0 (giờ đó chưa từng có
    cuốc) bị rơi về ước lượng LÝ THUYẾT DƯƠNG ⇒ 'còn kịp' lạc quan — ngược REVIEW-C9
    ('lịch sử 0.0 là dữ liệu HỢP LỆ')."""
    rate, ppt, src = _hour_rate(policy, {"offpeak": 0.0}, hour=9)
    assert rate == 0.0 and src == "historical:self", (rate, src)


# ---------- ADV-02/03: kéo ca so với thời gian ca CÒN LẠI + dự phóng cuối ca ----------

class _FakeActor:
    def __init__(self, **kw):
        self.actor_id = 1
        self.archetype = "P4"
        self.soc_pct = 90.0
        self.online_min = 100.0
        self.fatigue_threshold_min = 630.0
        self.shift_extended_min = 0.0
        self.points = 55
        self.shift_end_min = 0.0
        for k, v in kw.items():
            setattr(self, k, v)


def _ext_bridge():
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="all",
                            channels={"shift_plan": False, "accept_lift": False,
                                      "shift_extend": True, "rest_window": False})
    return AdviceActionBridge(c, SimPolicy.from_config(Config.load("configs/pilot_dongda.yaml")),
                              seed=1)


def test_extend_khong_keo_khi_moc_dat_duoc_trong_ca():
    """ADV-02: điểm 55, thiếu 5 tới mốc; rate 55đ/h ⇒ need ≈ 5,5′ trong khi ca còn 300′ —
    mốc đạt được KHÔNG CẦN kéo ca. Bản cũ vẫn cấp lệnh kéo (không so với ca còn lại)."""
    b = _ext_bridge()
    b.coin_follows = lambda *a, **k: True
    actor = _FakeActor(online_min=60.0, points=55,
                       shift_end_min=60.0 + 300.0)          # now=60 ⇒ ca còn 300′
    added, why = b.check_shift_extend(actor, now_min=60.0, soc_threshold=20.0)
    assert added == 0.0 and why == "reachable_in_shift", (added, why)


def test_extend_rail_du_phong_cuoi_ca_thang_tran_kinh_te():
    """ADV-03: mệt phải đo ở DỰ PHÓNG CUỐI CA (`online + ca-còn-lại + phần kéo`), không phải
    tại-lúc-khuyên. Kịch bản: online 100′, ca còn 200′, cần thêm ~300′ ngoài ca (kéo dự kiến
    345′) ⇒ dự phóng ~645′ > ngưỡng 630′ ⇒ phải chặn vì SỨC KHOẺ. Bản cũ: online+need =
    100+500 = 600 < 630 ⇒ lọt rail, rơi xuống trần kinh tế (`cap_unreachable`) — bảng veto nói
    'hết trần' cho đúng ca mà lan can sức khoẻ mới là thứ phải chặn (đúng lỗi đếm UPDATE-138)."""
    b = _ext_bridge()
    b.coin_follows = lambda *a, **k: True
    # rate = points/online_h = 50/(100/60) = 30đ/h; gap → 60 là 10 điểm ⇒ need = 20′? — dựng
    # bằng số cụ thể: points=50, online=100′ ⇒ rate=30; cần need 500′ ⇒ gap=250 điểm — vượt mốc
    # thật của policy. Thay vào đó chỉnh online/points cho need đúng 500′: gap 60−35=25 điểm,
    # rate = 35/(700/60) = 3đ/h ⇒ need = 25/3×60 = 500′. online=700 > ngưỡng? ngưỡng 630 —
    # fatigued chặn trước. Dùng ngưỡng cao hơn cho actor này (hồ sơ mệt khác nhau là hợp lệ).
    actor = _FakeActor(points=35, online_min=700.0, fatigue_threshold_min=1500.0,
                       shift_end_min=700.0 + 200.0)         # now=700 ⇒ ca còn 200′
    added, why = b.check_shift_extend(actor, now_min=700.0, soc_threshold=20.0)
    # need=500′ > còn 200′ ⇒ phần kéo thật ~300×1.15=345′; dự phóng = 700+200+345 = 1245′ < 1500
    # ⇒ chưa chặn. Hạ ngưỡng xuống 1200 để dự phóng vượt mà công thức CŨ (700+500=1200) thì vừa
    # KHÍT không vượt — knife-edge tách hai công thức:
    actor.fatigue_threshold_min = 1220.0
    added, why = b.check_shift_extend(actor, now_min=700.0, soc_threshold=20.0)
    assert added == 0.0 and why == "would_exceed_fatigue", (added, why)


def test_extend_chi_cap_phan_can_them_ngoai_ca():
    """ADV-02 vế hai: need 500′ mà ca còn 200′ ⇒ chỉ được cấp ~(500−200)×1.15 = 345′ (trước
    trần), KHÔNG phải 500×1.15 = 575′. Đo qua giá trị `added` khi mọi rail/trần đủ rộng."""
    b = _ext_bridge()
    b.coin_follows = lambda *a, **k: True
    b.extend_max_min = 10_000.0
    b.world_end_min = 10_000.0
    actor = _FakeActor(points=35, online_min=700.0, fatigue_threshold_min=10_000.0,
                       shift_end_min=700.0 + 200.0)
    added, why = b.check_shift_extend(actor, now_min=700.0, soc_threshold=20.0)
    assert added == pytest.approx(300.0 * 1.15), (added, why)


# ---------- ADV-07: gate đọc constraints TYPED, không parse chuỗi tiếng Việt ----------

def test_gate_accept_lift_khong_parse_chuoi():
    """`_advice_would_help` phân loại điểm nghẽn bằng parse chuỗi `infeasible_reason` tiếng
    Việt ('quỹ', 'hoàn thành', 'tỷ lệ nhận') — đổi wording của S1 là gate câm/loạn im lặng.
    S1 đã trả booleans typed trong `solution['constraints']` — gate phải đọc từ đó."""
    src = inspect.getsource(AdviceActionBridge._advice_would_help)
    assert '"quỹ"' not in src and '"hoàn thành"' not in src and '"tỷ lệ nhận"' not in src, \
        "gate vẫn parse chuỗi tiếng Việt"
    assert "constraints" in src, "gate chưa đọc solution['constraints'] typed"
