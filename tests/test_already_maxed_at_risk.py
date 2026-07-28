"""C2 việc 0 — `already_maxed` KHÔNG được che `feasible`.

Kịch bản hại (hồ sơ `research/audit/2026-07-27-current-state/08-parity-sim-vs-ui.md` §1b):
tài xế **đã kịch mốc điểm** nhưng **tỷ lệ nhận dưới ngưỡng** ⇒ chính sách trả **0đ**. Solver đã
biết điều đó từ AUDIT A1 (UPDATE-065): `feasible=False` + `infeasible_reason`. Nhưng **cả ba
consumer** rẽ nhánh `already_maxed` TRƯỚC khi đọc `feasible`, nên tài xế nhận được sự trấn an
hoặc im lặng — đúng lúc còn kịp cứu tiền.

Test ở **mức consumer**, không phải mức solver: test solver đã xanh sẵn trong khi cả ba consumer
đều sai. Đó là lý do bug sống sót.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.solvers.bonus_feasibility import solve

ROOT = Path(__file__).resolve().parent.parent

POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
    "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                   "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


def _maxed_input(acceptance: float, completion: float = 0.95) -> dict:
    """Kịch mốc cao nhất (210 ≥ 200) ⇒ `next_tiers` rỗng ⇒ nhánh `already_maxed`."""
    return {
        "schema_version": "1.0.0", "driver_id": "d-1",
        "t_now": "2026-07-01T18:00:00+07:00",
        "points_now": 210, "next_tiers": [],
        "historical_points_per_hour": {}, "hours_budget_remaining": 3.0,
        "acceptance_rate": acceptance, "completion_rate": completion,
        "policy_bundle_version": "sim-policy-v0", "view_version": "1.0.0", "source": "MOCK",
    }


# ---------- Solver: phải trả CONSTRAINTS để consumer giải thích được lý do ----------

def test_solver_emits_constraints_when_maxed_at_risk(policy):
    """Nhánh `already_maxed` hiện KHÔNG trả `constraints`, trong khi consumer
    (`templates._gap_sentence`) đọc `sol["constraints"]` để nói lý do. Thiếu nó thì dù có sửa
    thứ tự nhánh, consumer vẫn không biết nghẽn ở ĐÂU."""
    r = solve(_maxed_input(acceptance=0.80), policy)
    sol = r["solution"]
    assert sol["already_maxed"] is True
    assert sol["feasible"] is False
    cons = sol.get("constraints")
    assert cons is not None, "nhánh already_maxed phải trả constraints như nhánh thường"
    assert cons["ok_acceptance"] is False
    assert cons["ok_completion"] is True


def test_solver_maxed_and_safe_is_feasible(policy):
    """Đối chứng: kịch mốc VÀ tỷ lệ đủ ⇒ thực sự yên tâm."""
    sol = solve(_maxed_input(acceptance=0.95), policy)["solution"]
    assert sol["already_maxed"] is True and sol["feasible"] is True


# ---------- Consumer 1: templates (câu chữ cho tài xế) ----------

def test_template_warns_instead_of_reassuring_when_maxed_at_risk(policy):
    """`templates._gap_sentence` trả " …đã đạt mốc thưởng cao nhất hôm nay." — TRẤN AN một
    người sắp mất sạch thưởng."""
    from gsm_core.advisor import templates as T
    reports = [solve(_maxed_input(acceptance=0.80), policy)]
    s = T._gap_sentence(reports, {}, "40 điểm", "115.000đ")
    assert "cao nhất" not in s or "tỷ lệ" in s, f"câu trấn an sai trong lúc thưởng đang mất: {s!r}"
    assert s.strip(), "không được im lặng — đây là lúc CẦN nói"
    assert "tỷ lệ" in s, "phải nói rõ nghẽn ở tỷ lệ để tài xế còn cứu được"


def test_template_reassures_when_maxed_and_safe(policy):
    """Đối chứng: đủ tỷ lệ thì câu trấn an là ĐÚNG, không được cảnh báo thừa."""
    from gsm_core.advisor import templates as T
    reports = [solve(_maxed_input(acceptance=0.95), policy)]
    s = T._gap_sentence(reports, {}, "40 điểm", "115.000đ")
    assert "cao nhất" in s and "tỷ lệ" not in s


# ---------- Consumer 2: sim advice_bridge (có khuyên hay không) ----------

# ---------- Anh em cùng dạng ở S5 `weekly_khoan` (hồ sơ 08 §1c) ----------

def _khoan_report(feasible: bool, gap: int = 1_200_000) -> dict:
    """SolverReport của `weekly_khoan` với `feasible` bật/tắt, giữ nguyên shape thật."""
    return {
        "solver": "weekly_khoan",
        "solution": {
            "quota_available": True, "feasible": feasible,
            "revenue_so_far_vnd": 3_000_000, "quota_vnd": 3_000_000 + gap,
            "gap_revenue_vnd": gap, "clawback_risk_vnd": 240_000,
            "hours_needed": None if not feasible else 8.0,
            "days_active": 5, "days_remaining": 2,
            "constraints": {"enough_hours": feasible, "ok_active_days": True},
            "money_basis": "payout",
        },
        "numbers": [], "infeasible_reason": None if feasible
        else "cần ~40.0 giờ nhưng quỹ tuần còn 12.0 giờ",
    }


def _khoan_reg() -> dict:
    """`numbers_registry`: {key: {value, unit}} — `_vn` chỉ render số CÓ trong đây (chống V1)."""
    return {"gap": {"value": 1_200_000, "unit": "vnd"},
            "claw": {"value": 240_000, "unit": "vnd"}}


def test_khoan_sentence_says_unreachable_when_infeasible():
    """S5: solver tính `feasible=False` (quỹ giờ tuần không đủ) nhưng `_khoan_sentence` KHÔNG
    đọc trường đó ⇒ vẫn nói *"còn thiếu Xđ để đạt khoán… có thể bị truy thu Yđ"*, vừa ngụ ý
    với tới được vừa treo doạ truy thu. AUDIT A3 LAYEROUT-2 đã sửa đúng nguyên tắc này cho S1
    (`_gap_sentence`) nhưng bỏ sót S5 — cùng dạng câu, cùng loại hại."""
    from gsm_core.advisor import templates as T
    s = T._khoan_sentence([_khoan_report(feasible=False)], _khoan_reg())
    assert s.strip(), "không được im lặng — tài xế cần biết tuần này khó đạt"
    assert ("khó" in s or "không đủ" in s or "không thể" in s), \
        f"nói như thể còn đạt được trong khi solver bảo KHÔNG khả thi: {s!r}"


def test_khoan_sentence_normal_when_feasible():
    """Đối chứng: còn đạt được thì câu cũ vẫn đúng, không được cảnh báo thừa."""
    from gsm_core.advisor import templates as T
    s = T._khoan_sentence([_khoan_report(feasible=True)], _khoan_reg())
    assert "còn thiếu" in s and "khó" not in s


@pytest.fixture(scope="module")
def sim_env():
    """Actor thật từ một run thật — test HÀNH VI, không soi source."""
    from gsm_sim.config import Config
    from gsm_sim.policy import PolicyBundle as SimPolicy
    from gsm_sim.runner import run_once
    cfg = Config.load(ROOT / "configs" / "pilot_dongda.yaml")
    return run_once(cfg, seed=1000), cfg, SimPolicy.from_config(cfg)


def _sim_bridge(cfg, sim_policy, actor_id: int):
    from gsm_sim.advice_bridge import AdviceActionBridge
    import copy
    c = type(cfg)(copy.deepcopy(cfg.data), cfg.root_dir)
    c.data["advice"].update(enabled=True, coverage="single", single_actor_id=actor_id)
    return AdviceActionBridge(c, sim_policy, seed=1)


def test_bridge_does_not_suppress_when_maxed_at_risk(sim_env, monkeypatch):
    """`advice_bridge._advice_would_help` trả `(False, "already_maxed")` = IM LẶNG.

    Im lặng ĐÚNG khi đã an toàn. Ở đây thưởng đang mất mà vẫn im ⇒ bỏ rơi tài xế đúng lúc còn
    cứu được. Ép solver trả đúng kịch bản "kịch mốc + dưới ngưỡng" để cô lập nhánh cần test.
    """
    from gsm_core.solvers import bonus_feasibility as BF
    from gsm_sim import advice_bridge as AB

    result, cfg, sim_policy = sim_env
    a = result.actors[0]
    b = _sim_bridge(cfg, sim_policy, a.actor_id)
    a.orders_offered, a.orders_accepted = 0, 0          # còn gỡ được hoàn toàn

    at_risk = {"already_maxed": True, "feasible": False, "gap_points": 0,
               "constraints": {"ok_acceptance": False, "ok_completion": True,
                               "enough_hours": True}}
    monkeypatch.setattr(AB.bonus_feasibility, "solve",
                        lambda *_a, **_k: {"solution": at_risk,
                                           "infeasible_reason": "tỷ lệ nhận dưới ngưỡng"})

    ok, reason = b._advice_would_help(a, a.shift_start_min, 0.85)
    assert not (reason == "already_maxed" and ok is False), (
        "kịch mốc NHƯNG thưởng sắp mất mà bridge vẫn im lặng vì 'already_maxed'"
    )
    assert ok, "còn gỡ được tỷ lệ ⇒ phải khuyên"
    assert BF  # giữ import tường minh cho người đọc: đây là solver bị monkeypatch
