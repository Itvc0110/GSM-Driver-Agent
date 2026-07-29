"""B1 (PLAN-cycle-wx, Cường đã duyệt) — thước `net_mean_all` ĐỌC sổ chi phí `actor.cost_vnd`.

Vì sao: sim đã TÍNH chi phí (`actor.cost_vnd`, T-045b) nhưng KHÔNG thước nào đọc nó — sổ chết.
Bước C1 (chi phí vào solver) sẽ vô nghĩa nếu thước không thấy chi phí: solver hy sinh payout để
tiết kiệm khoản vô hình ⇒ trông tệ oan. Bước NÀY chỉ THÊM thước, KHÔNG đổi solver/behavior —
`payout_vnd` và mọi trace phải y hệt trước/sau (xem `test_cost_ledger.py`).
"""

from __future__ import annotations

import copy

from gsm_sim.config import Config
from gsm_sim.parallel import _cohort_metrics
from gsm_sim.runner import run_once
from gsm_sim.sim_metrics import cost_summary

SEED = 1000


def _cfg(**veh):
    base = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(base.data), base.root_dir)
    if veh:
        c.data.setdefault("vehicle", {}).update(veh)
    return c


# ---------- a) mặc định cash_cost=0: net == payout, cost == 0 ----------

def test_net_equals_payout_when_cost_is_zero():
    r = run_once(_cfg(), SEED)
    m = _cohort_metrics(r)
    cs = cost_summary(r)
    assert m["net_mean_all"] == m["payout_mean_all"], (
        "chi phí mặc định 0 mà net_mean_all lệch payout_mean_all — cost đang rò vào công thức")
    assert m["cost_mean_all"] == 0.0, "cost mặc định phải 0 (T-045b) — sổ không được bịa số"
    assert cs["cost_total_vnd"] == 0
    assert cs["net_mean_vnd"] == m["payout_mean_all"]


# ---------- b) bật cash_cost + swap_fee: net < payout, payout KHÔNG đổi so với (a) ----------

def test_net_below_payout_when_cost_enabled_and_payout_untouched():
    r0 = run_once(_cfg(), SEED)
    m0 = _cohort_metrics(r0)

    r1 = run_once(_cfg(cash_cost_vnd_per_km=100, swap_fee_vnd=5000), SEED)
    m1 = _cohort_metrics(r1)
    cs1 = cost_summary(r1)

    assert m1["net_mean_all"] < m1["payout_mean_all"], (
        "bật cash_cost + swap_fee mà net_mean_all không tụt dưới payout_mean_all — "
        "thước không thấy chi phí (sổ vẫn chết)")
    assert m1["payout_mean_all"] == m0["payout_mean_all"], (
        "payout_mean_all đổi khi bật chi phí — cost đang RÒ vào payout (vi phạm §5 CLAUDE.md: "
        "tách gross/payout/net)")
    assert cs1["cost_total_vnd"] > 0
    assert cs1["net_mean_vnd"] == m1["net_mean_all"], (
        "cost_summary và _cohort_metrics phải reconcile — không hai nguồn cho cùng một sự thật")


# ---------- c) exact-repeat: cùng seed + cùng config chi phí ⇒ mọi số y hệt ----------

def test_exact_repeat_with_cost_enabled():
    r1 = run_once(_cfg(cash_cost_vnd_per_km=100, swap_fee_vnd=5000), SEED)
    r2 = run_once(_cfg(cash_cost_vnd_per_km=100, swap_fee_vnd=5000), SEED)

    m1, m2 = _cohort_metrics(r1), _cohort_metrics(r2)
    assert m1 == m2, "hai lần chạy CÙNG seed/config mà cohort metrics khác nhau — vỡ exact-repeat"

    cs1, cs2 = cost_summary(r1), cost_summary(r2)
    assert cs1 == cs2, "hai lần chạy CÙNG seed/config mà cost_summary khác nhau — vỡ exact-repeat"

    assert {a.actor_id: a.payout_vnd for a in r1.actors} == \
           {a.actor_id: a.payout_vnd for a in r2.actors}, "payout không exact-repeat"
