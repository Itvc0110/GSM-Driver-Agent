"""Cycle W (ĐA-05) — W4/W5: nối 3 nguồn ID vào event log.

- W4-sim: `derive_run_id` deterministic; Event mang `run_id`; event advice mang
  `decision_id`+`channel`; exact-repeat giữ nguyên.
- W4-pipeline + W5: EpisodeStore = legacy adapter — `append_episode` phát event `decided`
  vào AdviceEventLog (một đường ghi, không double-write); pipeline làm giàu verify verdict
  (FAILCLOSED-3) + solver_report_refs thật (MEMSTATE-4).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gsm_core.schema_registry import SchemaRegistry
from gsm_sim.config import Config
from gsm_sim.runner import derive_run_id, run_once

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"


@pytest.fixture()
def reg() -> SchemaRegistry:
    return SchemaRegistry(ROOT / "schemas")


def _cfg(actor_id: int = 0) -> Config:
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="single", single_actor_id=actor_id,
                            channels={"shift_plan": True, "accept_lift": True,
                                      "shift_extend": False, "rest_window": False},
                            positioning_overrides="off")
    return c


# ---------- W4: derive_run_id ----------

def test_run_id_deterministic_and_encodes_identity():
    base = Config.load("configs/pilot_dongda.yaml")
    on = _cfg(actor_id=3)
    assert derive_run_id(base, 42) == derive_run_id(base, 42)
    assert derive_run_id(base, 42) != derive_run_id(base, 43)          # seed
    assert derive_run_id(base, 42) != derive_run_id(on, 42)            # arm A ≠ B
    assert "-A-" in derive_run_id(base, 42)
    assert "-B-" in derive_run_id(on, 42)
    other_actor = _cfg(actor_id=5)
    assert derive_run_id(on, 42) != derive_run_id(other_actor, 42)     # coverage target
    other_ch = _cfg(actor_id=3)
    other_ch.data["advice"]["channels"]["accept_lift"] = False
    assert derive_run_id(on, 42) != derive_run_id(other_ch, 42)        # bộ kênh


# ---------- W4: sim events mang run_id + decision_id ----------

def _cfg_all() -> Config:
    """coverage=all để chắc chắn có mẫu follow (single 1 actor có thể 0 lần follow)."""
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="all", single_actor_id=None,
                            channels={"shift_plan": True, "accept_lift": True,
                                      "shift_extend": False, "rest_window": False},
                            positioning_overrides="off")
    return c


@pytest.fixture(scope="module")
def run_b():
    return run_once(_cfg_all(), seed=1000)


def test_all_events_stamped_with_run_id(run_b):
    rid = derive_run_id(_cfg_all(), 1000)
    assert run_b.events, "run phải có event"
    assert all(e.run_id == rid for e in run_b.events)


def test_advice_events_carry_decision_id_and_channel(run_b):
    advice_kinds = {"advice_given", "advice_followed", "advice_suppressed",
                    "advice_bonus_gate", "advice_shift_extend", "advice_rest_window",
                    "standby_followed"}
    seen = [e for e in run_b.events if e.kind in advice_kinds]
    assert seen, "kịch bản này phải sinh advice event (shift_plan+accept_lift bật)"
    for e in seen:
        assert e.detail.get("decision_id", "").startswith("slth-"), (e.kind, e.detail)
        assert e.detail.get("channel"), e.kind


def test_same_tick_given_and_followed_share_decision(run_b):
    """advice_followed cùng tick với advice_given ⇒ CÙNG decision (join được)."""
    given = {(e.t_min, e.actor_id): e.detail["decision_id"]
             for e in run_b.events if e.kind == "advice_given"}
    followed = [e for e in run_b.events if e.kind == "advice_followed"]
    assert followed, "kịch bản phải có ít nhất một lần follow"
    for e in followed:
        assert given.get((e.t_min, e.actor_id)) == e.detail["decision_id"]


def test_exact_repeat_same_ids(run_b):
    """Exact-repeat: decision_id/run_id derive thuần từ cfg+seed, không uuid/wall-clock."""
    again = run_once(_cfg_all(), seed=1000)
    assert [(e.t_min, e.actor_id, e.kind, e.run_id, e.detail.get("decision_id"))
            for e in run_b.events] == \
           [(e.t_min, e.actor_id, e.kind, e.run_id, e.detail.get("decision_id"))
            for e in again.events]


def test_full_chain_sim_to_adherence_view(run_b, reg):
    """Chuỗi đầy đủ: sim RAM → lifecycle envelope hợp lệ → adherence view có mẫu số."""
    from gsm_core.lifecycle import projections as p
    rid = derive_run_id(_cfg_all(), 1000)
    lc = p.sim_events_to_lifecycle(run_b.events, run_id=rid)
    assert lc, "phải map được ít nhất một advice event"
    for e in lc[:20]:
        assert reg.validate("advice_lifecycle_event", e) == [], e
    view = p.adherence_view(lc)
    # khoá = (run_id, driver_id, topic) sau fix F-2
    assert any(k[2] == "shift_plan" and v["decided"] > 0 for k, v in view.items())


def test_multiday_events_also_stamped():
    """Đường multiday (`run_multiday`) cũng phải stamp run_id — nó là đường chạy chính của
    nghiên cứu memory/D-SIM-10/13 và là nguồn dữ liệu ĐA-04 sắp dùng. Tự bắt: `multiday`
    tạo `World(...)` riêng chứ không đi qua `run_once`, nên rất dễ quên."""
    from gsm_sim.multiday import run_multiday
    c = _cfg_all()
    res = run_multiday(c, seed=1000, days=2)
    for i, day in enumerate(res.days):
        assert day.events, f"ngày {i} phải có event"
        rids = {e.run_id for e in day.events}
        assert rids and "" not in rids, f"ngày {i} có event không mang run_id: {rids}"
    # hai ngày phải phân biệt được (day_seed khác nhau ⇒ run_id khác nhau)
    assert ({e.run_id for e in res.days[0].events}
            != {e.run_id for e in res.days[1].events})


def test_sim_export_into_store_end_to_end(run_b, tmp_path):
    """Đường THẬT sim→store (ĐA-04 sẽ dùng): mọi event của một run sim thật ghi được vào
    event log, không nổ vì dtype lạ (numpy scalar trong detail của bridge), và replay ra
    projection giống hệt khi đọc lại từ SQLite so với đọc thẳng từ RAM."""
    from gsm_core.lifecycle import projections as p
    from gsm_core.lifecycle.event_log import AdviceEventLog
    rid = derive_run_id(_cfg_all(), 1000)
    lc = p.sim_events_to_lifecycle(run_b.events, run_id=rid)
    with AdviceEventLog(tmp_path / "sim.db") as log:
        assert all(log.append(e) for e in lc), "mọi event phải ghi được (event_id distinct)"
        from_db = log.events(run_id=rid)
    assert len(from_db) == len(lc)
    assert p.decision_state(from_db) == p.decision_state(lc), (
        "UI đọc SQLite và sim đọc RAM phải ra CÙNG projection — điều kiện duyệt ĐA-05")


# ---------- W5: EpisodeStore = legacy adapter ----------

def test_append_episode_emits_decided_event(tmp_path):
    from gsm_core.advisor.episode_store import EpisodeStore
    from gsm_core.lifecycle.event_log import AdviceEventLog
    db = tmp_path / "ep.db"
    store = EpisodeStore(db)
    store.append_episode({"episode_id": "adv-x1", "driver_id": "d-1", "feature": "F1",
                          "message": "test", "confidence": 0.8, "fallback_used": True,
                          "route": "F1_bonus"})
    store.close()
    with AdviceEventLog(db) as log:
        evs = log.events(decision_id="adv-x1")
    assert len(evs) == 1
    e = evs[0]
    assert e["event_type"] == "decided" and e["origin"] == "pipeline"
    assert e["driver_id"] == "d-1" and e["payload"]["feature"] == "F1"


def test_count_episodes_from_projection(tmp_path):
    from gsm_core.advisor.episode_store import EpisodeStore
    store = EpisodeStore(tmp_path / "ep.db")
    for i in range(3):
        store.append_episode({"episode_id": f"adv-{i}", "driver_id": "d-1",
                              "feature": "F1", "message": "m", "confidence": 0.5,
                              "fallback_used": True})
    # append trùng episode_id ⇒ KHÔNG tăng (idempotent qua event log)
    store.append_episode({"episode_id": "adv-0", "driver_id": "d-1", "feature": "F1",
                          "message": "m", "confidence": 0.5, "fallback_used": True})
    assert store.count_episodes() == 3
    store.close()


def test_pipeline_decided_carries_verify_and_refs(tmp_path, reg):
    """FAILCLOSED-3 + MEMSTATE-4: event decided phải mang verify verdict + solver refs thật."""
    from gsm_core.advisor.pipeline import AdvisorPipeline
    from gsm_core.lifecycle.event_log import AdviceEventLog

    def _report_s1():  # bản sao fixture test_advisor_pipeline (tests không phải package)
        return {"schema_version": "1.0.0", "solver": "bonus_feasibility",
                "problem_digest": "Thiếu 20đ tới mốc 160",
                "inputs_used": [{"view_id": "bg:d-1", "version": "1.0.0",
                                 "freshness": "2026-07-01T18:00:00+07:00"}],
                "solution": {"feasible": True, "gap_points": 20, "hours_needed": 1.33,
                             "tier_points": 160, "tier_vnd": 115000},
                "numbers": [{"value": 20, "unit": "points",
                             "source": "policy_v:sim-policy-v0"},
                            {"value": 115000, "unit": "vnd",
                             "source": "policy_v:sim-policy-v0"}],
                "sensitivity": [], "confidence": 0.85, "caveats": ["demand proxy"],
                "infeasible_reason": None}

    db = tmp_path / "ep.db"
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=db, llm_mode="off")
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1",
           "feature": "F1", "free_text_query": None, "l3_view_refs": [],
           "session_id": "s1", "t_request": "2026-07-01T18:00:00+07:00",
           "trigger_source": "user_ask"}
    advice = pipe.handle(req, solver_reports=[_report_s1()], kb_track="platform")
    pipe.store.close()
    with AdviceEventLog(db) as log:
        evs = log.events(decision_id=advice["advice_id"])
    assert len(evs) == 1
    payload = evs[0]["payload"]
    assert payload["verify"]["passed"] is True
    assert payload["solver_report_refs"], "refs phải là digest THẬT, không còn hardcode []"
