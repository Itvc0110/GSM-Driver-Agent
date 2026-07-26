"""SIM-XANH Phase 2 — gate cho rating/tân binh/mission trong sim.

Ba bất biến phải giữ:
1. **Không làm trôi hiệu chỉnh**: rating dùng RNG stream RIÊNG; mission/newbie chỉ cộng
   payout (không feedback vào hành vi nhận đơn) ⇒ served/accept/completion giữ nguyên.
2. **Bảo toàn tiền 4 nguồn**: cuốc + thưởng ngày + mission + tân binh == payout actor.
3. **Trả đúng MỘT lần**: mission chạm mốc 1 lần/ngày; mốc tân binh tuần-1 một lần/đời.
"""

from __future__ import annotations

import copy

import pytest

from gsm_sim.config import Config
from gsm_sim.journey import build_journey
from gsm_sim.multiday import run_multiday
from gsm_sim.runner import run_once

SEED = 7100


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def result(cfg):
    return run_once(cfg, seed=SEED)


# ---------- Rating trong sim ----------


def test_ratings_exist_and_bounded(result):
    rated = [e for e in result.events if e.kind == "trip_rated"]
    assert rated, "không có rating nào — cơ chế chết"
    assert all(1 <= e.detail["stars"] <= 5 for e in rated)
    drops = sum(1 for e in result.events if e.kind == "dropoff")
    # p_rated 0.75 ⇒ tỷ lệ chấm sao phải quanh đó (biên rộng cho 1 seed)
    assert 0.6 <= len(rated) / drops <= 0.9


def test_rating_counters_match_events(result):
    by_actor: dict[int, list[int]] = {}
    for e in result.events:
        if e.kind == "trip_rated":
            by_actor.setdefault(e.actor_id, []).append(e.detail["stars"])
    for a in result.actors:
        stars = by_actor.get(a.actor_id, [])
        assert a.ratings_n == len(stars)
        assert a.ratings_sum == sum(stars)
        assert a.ratings_5 == sum(1 for s in stars if s == 5)


def test_top_archetype_rates_higher_than_newbie(result):
    """P3 (top) phải có tỷ lệ 5★ cao hơn P4 (tân binh) — nếu không thì config đặt ngược."""
    def p5(arch):
        n = f = 0
        for a in result.actors:
            if a.archetype == arch and a.ratings_n:
                n += a.ratings_n
                f += a.ratings_5
        return f / n if n else None
    a3, a4 = p5("P3"), p5("P4")
    if a3 is None or a4 is None:
        pytest.skip("thiếu mẫu rating cho P3/P4 seed này")
    assert a3 > a4


def test_ratings_use_separate_rng_stream(cfg):
    """QUAN TRỌNG NHẤT: tắt rating (p_rated=0) không được đổi BẤT KỲ hành vi nào khác.
    Nếu rating rút từ stream hành vi chung thì mọi hiệu chỉnh SIM-1/P1 trôi sạch."""
    from gsm_sim.metrics import summarize
    on = summarize(run_once(cfg, seed=33))
    c2 = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c2.data["rating"]["p_rated"] = 0.0
    off = summarize(run_once(c2, seed=33))
    keys = ("orders_total", "orders_completed", "served_rate", "orders_declined")
    assert {k: on[k] for k in keys} == {k: off[k] for k in keys}, \
        "tắt rating làm đổi hành vi thị trường — rating đang ăn chung RNG stream"


# ---------- Mission ----------


def test_mission_reward_paid_once_per_mission(result):
    seen: set[tuple[int, str]] = set()
    for e in result.events:
        if e.kind == "mission_completed":
            key = (e.actor_id, e.detail["mission_id"])
            assert key not in seen, f"mission {key} trả thưởng HAI lần trong một ngày"
            seen.add(key)


def test_mission_progress_never_exceeds_target(result, cfg):
    targets = {m["mission_id"]: int(m["target"]) for m in cfg.get("missions.daily_catalog")}
    for a in result.actors:
        for mid, cnt in a.mission_progress.items():
            assert cnt <= targets[mid], f"tiến độ {mid} vượt target — đếm không dừng"


def test_mission_reward_in_payout(result):
    total_reward = sum(e.detail["reward_vnd"] for e in result.events
                       if e.kind == "mission_completed")
    assert total_reward == sum(a.mission_reward_vnd for a in result.actors)
    assert total_reward > 0, "không mission nào hoàn thành cả ngày — catalog quá khó?"


# ---------- Tân binh (Q-01, cấu trúc thật greensm.com) ----------


def test_newbie_only_for_low_tenure(result, cfg):
    max_t = int(cfg.get("newbie_program.tenure_newbie_max_days"))
    for e in result.events:
        if e.kind in ("newbie_guarantee_topup", "newbie_week1_bonus"):
            assert e.detail["tenure_days"] <= max_t, "tài xế CŨ nhận trợ cấp tân binh"


def test_guarantee_topup_requires_diligence(result, cfg):
    """Bảo lãnh doanh thu chỉ bù khi ĐỦ CHUYÊN CẦN (online ≥ ngưỡng) — chống lạm dụng."""
    min_online = float(cfg.get("newbie_program.guarantee_min_online_h")) * 60.0
    actors = {a.actor_id: a for a in result.actors}
    for e in result.events:
        if e.kind == "newbie_guarantee_topup":
            assert actors[e.actor_id].online_min >= min_online


def test_guarantee_math(result, cfg):
    """topup = (sàn − gross) × driver_share — đúng phần TÀI XẾ của khoảng thiếu."""
    floor = int(cfg.get("newbie_program.guarantee_gross_floor_vnd"))
    share = float(cfg.get("policy.driver_share"))
    for e in result.events:
        if e.kind == "newbie_guarantee_topup":
            want = int(round((floor - e.detail["gross_day"]) * share))
            assert e.detail["topup_vnd"] == want


def test_week1_bonus_once_across_days(cfg):
    """Mốc 50 cuốc/7 ngày: trả đúng MỘT lần dù đủ điều kiện nhiều ngày liên tiếp.

    Ép điều kiện dễ (target=5) để mốc chắc chắn đạt trong sim ngắn — đang test cơ chế
    MỘT-LẦN, không test độ khó.
    """
    # seed 7102 CÓ tài xế tenure=5 (d-46) — tìm bằng quét deterministic; tenure sample
    # theo (seed, actor) nên seed này LUÔN có tân binh tuần-đầu. Target ép xuống 3 để
    # mốc chắc chắn đạt (test cơ chế MỘT-LẦN, không test độ khó).
    c2 = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c2.data["newbie_program"]["first_week_trip_target"] = 3
    md = run_multiday(c2, seed=7102, days=3)
    bonus_by_actor: dict[int, int] = {}
    for r in md.days:
        for e in r.events:
            if e.kind == "newbie_week1_bonus":
                bonus_by_actor[e.actor_id] = bonus_by_actor.get(e.actor_id, 0) + 1
    assert bonus_by_actor, "không ai đạt mốc dù target=5 — cơ chế chết"
    assert all(n == 1 for n in bonus_by_actor.values()), \
        f"mốc tuần-1 trả NHIỀU lần: {bonus_by_actor}"


def test_tenure_advances_daily(cfg):
    md = run_multiday(cfg, seed=SEED, days=3)
    t0 = {a.actor_id: a.tenure_days for a in md.days[0].actors}
    t2 = {a.actor_id: a.tenure_days for a in md.days[2].actors}
    assert all(t2[aid] == t0[aid] + 2 for aid in t0), "tenure không tăng theo ngày"


# ---------- Bảo toàn tiền 4 nguồn (mở rộng BUG-SIM2-01) ----------


def test_four_source_money_conservation(result):
    for a in result.actors:
        if a.orders_offered == 0:
            continue
        m = build_journey(result, a.actor_id).metrics
        parts = (m["trip_payout_vnd"] + m["day_bonus_vnd"]
                 + m["mission_reward_vnd"] + m["newbie_vnd"])
        assert parts == m["payout_vnd"] == a.payout_vnd, (
            f"d-{a.actor_id}: {parts} != {a.payout_vnd} — rò tiền giữa 4 nguồn")
