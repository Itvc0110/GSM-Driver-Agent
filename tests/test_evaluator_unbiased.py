"""Evaluator KHÔNG BIAS cho tiêu chí cá nhân của ĐA-08 (Cycle E, Q-11 đã duyệt).

## BUG-EVAL-ARGMAX (UPDATE-085 §4)

`pick_target` chọn tài xế MAX-offers của thế giới A — chọn CỰC TRỊ — nên Δ(B−A) trên người đó
bias âm bất kể nội dung can thiệp (regression to the mean). Chứng minh sign-flip 5 seed, cùng
một can thiệp B1: argmax-A **−19.654đ** · argmax-B **+27.416đ** · mean-P4 không chọn lọc
**+3.610đ** · toàn đội +5.350đ/người. Toàn bộ chuỗi "advisor làm tài xế nghèo đi −17k…−40k"
(UPDATE-075/078/081/084) nhiễm bias này; các tầng HỆ THỐNG (aggregate không chọn lọc) thì không.

## Tiêu chí 1 ĐA-08 mới (Q-11): mean Δpayout trên MỌI tài xế, tách theo archetype

Estimator sống trong `_system_metrics` (cùng dict với guardrail) ⇒ `PairResult` giữ nguyên hình
dạng, `compare()` tự nhặt key mới, mọi consumer cũ nguyên vẹn. View argmax GIỮ LẠI làm chẩn đoán
cá thể — có nhãn BIASED, cấm dùng làm tiêu chí.
"""

from __future__ import annotations

import copy
import statistics as st

import pytest

from gsm_sim.config import Config
from gsm_sim.parallel import PairResult, _cfg_with, _system_metrics, compare, pick_target, run_pair
from gsm_sim.runner import run_once

SEED = 2000


@pytest.fixture(scope="module")
def base():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def run_a(base):
    return run_once(_cfg_with(base, enabled=False, actor_id=None, channels=None,
                              coverage="all"), SEED)


# ---------- 1. cohort metrics reconcile với sự thật ----------

def test_cohort_means_reconcile_with_actors(run_a):
    """`payout_mean_P4` phải bằng ĐÚNG mean tính tay từ actors — không qua tầng trung gian nào.

    Reconcile chống lỗi 'hai chỗ cùng tính một luật' (T-046): estimator đọc thẳng actor state."""
    m = _system_metrics(run_a, exclude_actor=-1)
    p4 = [a.payout_vnd for a in run_a.actors if a.archetype == "P4"]
    # tolerance = đúng mức làm tròn đã khai trong `_cohort_metrics` (2 chữ số tiền, 3 chữ số cuốc)
    assert m.get("payout_mean_P4") == pytest.approx(st.mean(p4), abs=0.005), \
        "payout_mean_P4 không khớp mean tính tay — estimator đọc sai nguồn"
    assert m.get("payout_mean_all") == pytest.approx(
        st.mean(a.payout_vnd for a in run_a.actors), abs=0.005)
    assert m.get("trips_mean_all") == pytest.approx(
        st.mean(a.trips_done for a in run_a.actors), abs=0.0005)


# ---------- 2. PLACEBO: can thiệp rỗng ⇒ Δ = 0 tuyệt đối ----------

def test_placebo_intervention_measures_exactly_zero(base):
    """Advice BẬT nhưng mọi kênh TẮT + positioning off ⇒ World B y hệt A ⇒ mọi Δ cohort = 0.

    Placebo test mà thiết kế đo cũ CHƯA TỪNG có — nếu có từ đầu thì argmax-bias không lộ qua
    placebo (placebo không nhiễu loạn thế giới), nhưng nó canh được: (i) đường ống estimator
    không tự chế số, (ii) CRN không rò (bật cờ advice mà không kênh nào chạy thì RNG actor
    không được dịch một draw nào)."""
    ra = run_once(_cfg_with(base, enabled=False, actor_id=None, channels=None,
                            coverage="all"), SEED)
    ch_off = {"shift_plan": False, "accept_lift": False,
              "shift_extend": False, "rest_window": False}
    rb = run_once(_cfg_with(base, enabled=True, actor_id=None, channels=ch_off,
                            coverage="all"), SEED)
    ma = _system_metrics(ra, exclude_actor=-1)
    mb = _system_metrics(rb, exclude_actor=-1)
    cohort_keys = [k for k in ma if k.startswith(("payout_mean", "trips_mean"))]
    assert cohort_keys, "không có cohort key nào — test đang XANH RỖNG, estimator chưa tồn tại"
    for k in cohort_keys:
        if True:
            assert ma[k] == mb[k], (
                f"placebo mà {k} lệch ({ma[k]} vs {mb[k]}) — hoặc estimator tự chế số, "
                f"hoặc bật cờ advice đã dịch RNG (vỡ CRN)")


# ---------- 3. compare() báo CI cho cohort keys ----------

def test_compare_reports_cohort_delta_with_ci():
    def mk(seed, pa, pb):
        sys_a = {"payout_mean_P4": pa, "payout_mean_all": pa}
        sys_b = {"payout_mean_P4": pb, "payout_mean_all": pb}
        return PairResult(seed, 1, {"payout_vnd": pa}, {"payout_vnd": pb}, sys_a, sys_b)
    out = compare([mk(1, 100.0, 130.0), mk(2, 200.0, 220.0)])
    d = out["system"]["payout_mean_P4"]
    assert d["delta_mean"] == pytest.approx(25.0)
    assert "ci95" in d


# ---------- 4. nhãn bias không được biến mất ----------

def test_argmax_view_carries_bias_warning():
    """`pick_target` phải mang cảnh báo BIASED trong docstring — ai xoá cảnh báo là mở lại
    đường cho tiêu chí 1 quay về argmax mà không ai nhớ vì sao không được."""
    assert "BIAS" in (pick_target.__doc__ or "").upper(), (
        "docstring pick_target mất nhãn bias — xem UPDATE-085 §4 trước khi xoá")
