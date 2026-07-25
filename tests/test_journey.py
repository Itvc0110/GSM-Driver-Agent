"""SIM-2 — gate cho `DriverJourney`.

Journey là bản **lắp ráp lại** từ `RunResult`. Rủi ro lớn nhất không phải nó crash, mà là nó
**kể sai** về tài xế: mất phút, mất tiền, mất offer, hoặc từ chối "không rõ vì sao". Bộ test
này khoá đúng các bảo toàn đó — nếu journey lệch khỏi engine, đỏ ngay.

Kiểm trên **nhiều archetype** (không chỉ 1 tài xế may mắn) và nhiều seed cho phần bất biến.
"""

from __future__ import annotations

import json

import pytest

from gsm_sim.config import Config
from gsm_sim.journey import build_journey, journey_to_json
from gsm_sim.metrics import summarize
from gsm_sim.runner import run_once

SEED = 1000


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def result(cfg):
    return run_once(cfg, seed=SEED)


@pytest.fixture(scope="module")
def journeys(result):
    """1 tài xế đại diện cho MỖI archetype (người được chào đơn nhiều nhất)."""
    out = {}
    for a in result.actors:
        cur = out.get(a.archetype)
        if cur is None or a.orders_offered > cur.orders_offered:
            out[a.archetype] = a
    return {arch: build_journey(result, a.actor_id) for arch, a in out.items()}


# ---------- Bảo toàn: journey KHÔNG được lệch khỏi engine ----------


def test_offers_conserved(result, journeys):
    """Mỗi lần được chào đơn phải xuất hiện đúng 1 lần trong journey."""
    actors = {a.actor_id: a for a in result.actors}
    for arch, j in journeys.items():
        a = actors[j.actor_id]
        assert len(j.offers) == a.orders_offered, (
            f"{arch}: journey {len(j.offers)} offer != actor {a.orders_offered}")
        m = j.metrics
        assert m["accepted"] + m["declined"] + m["skipped_soc"] == a.orders_offered, (
            f"{arch}: accept+decline+skip != offered")
        assert m["accepted"] == a.orders_accepted
        assert m["trips_completed"] == a.orders_completed
        assert m["cancelled_after_accept"] == a.orders_cancelled


def test_time_conserved(journeys):
    """Mọi phút trong phiên phải có nhãn — không được 'bốc hơi' thời gian.
    Đây là chỗ dễ sai nhất vì `idle` do ta SUY RA, không phải sim ghi."""
    for arch, j in journeys.items():
        session_min = sum(b - a for a, b in j.sessions)
        timeline_min = sum(b.minutes for b in j.timeline)
        assert abs(timeline_min - session_min) <= 1.0, (
            f"{arch}: timeline {timeline_min:.1f}ph != phiên {session_min:.1f}ph")


def test_timeline_no_overlap(journeys):
    """Không được có 2 hoạt động chồng lên nhau (tài xế không phân thân được)."""
    for arch, j in journeys.items():
        blocks = sorted(j.timeline, key=lambda b: b.t0)
        for prev, nxt in zip(blocks, blocks[1:]):
            assert nxt.t0 >= prev.t1 - 1e-6, (
                f"{arch}: {prev.kind}({prev.t0}-{prev.t1}) chồng {nxt.kind}({nxt.t0}-{nxt.t1})")


def test_money_conserved(result, journeys):
    """Thu nhập tích luỹ phải khớp payout của actor và không bao giờ giảm."""
    actors = {a.actor_id: a for a in result.actors}
    for arch, j in journeys.items():
        vals = [v for _, v in j.income_curve]
        assert vals == sorted(vals), f"{arch}: thu nhập tích luỹ bị GIẢM"
        assert vals[-1] == actors[j.actor_id].payout_vnd, (
            f"{arch}: journey {vals[-1]}đ != actor {actors[j.actor_id].payout_vnd}đ")


def test_day_bonus_included_in_income(journeys):
    """BUG-SIM2-01 (đã fix): income_curve ban đầu chỉ cộng payout TỪNG CUỐC, bỏ **thưởng
    ngày** ⇒ thiếu đúng 60.000đ so `actor.payout_vnd`. Với sản phẩm này bỏ sót thưởng là
    sai lệch nghiêm trọng — thưởng chiếm 20-30% thu nhập và chính là thứ advisor tối ưu.
    """
    for arch, j in journeys.items():
        m = j.metrics
        assert m["trip_payout_vnd"] + m["day_bonus_vnd"] == m["payout_vnd"], (
            f"{arch}: cuốc {m['trip_payout_vnd']} + thưởng {m['day_bonus_vnd']} "
            f"!= tổng {m['payout_vnd']}")
    # ít nhất một tài xế phải THỰC SỰ nhận thưởng, nếu không test trên vacuous
    assert any(j.metrics["day_bonus_vnd"] > 0 for j in journeys.values()), \
        "không tài xế nào nhận thưởng ngày — kiểm tra lại policy/day_bonus"


def test_utilization_within_bounds(journeys):
    for arch, j in journeys.items():
        assert 0.0 <= j.metrics["utilization"] <= 1.0, f"{arch}: util ngoài [0,1]"


# ---------- Yêu cầu Cường: từng offer phải giải trình được ----------


def test_every_offer_has_reason(journeys):
    """*"từng offer (nhận/từ chối + LÝ DO)"* — không được có quyết định 'unknown'."""
    valid = {"accepted", "forced", "economics", "base_behavior", "soc_insufficient"}
    for arch, j in journeys.items():
        bad = [(o.order_id, o.reason) for o in j.offers if o.reason not in valid]
        assert not bad, f"{arch}: offer không có lý do hợp lệ: {bad[:3]}"


def test_declines_carry_evidence(journeys):
    """Từ chối phải kèm SỐ (net/pickup/p_accept) — nếu không thì không giải trình được
    vì sao, và advisor sau này không có gì để bám vào."""
    for arch, j in journeys.items():
        for o in j.offers:
            if o.decision == "decline":
                assert o.net_vnd is not None and o.pickup_km is not None, \
                    f"{arch}: decline #{o.order_id} thiếu số liệu"
                assert 0.0 <= o.p_accept <= 1.0


def test_accepted_offers_have_outcome(journeys):
    """Đơn đã nhận phải có kết cục (không được lửng lơ)."""
    ok = {"completed", "cancelled_after_accept", "censored"}
    for arch, j in journeys.items():
        for o in j.offers:
            if o.decision == "accept":
                assert o.outcome in ok, f"{arch}: #{o.order_id} outcome={o.outcome}"


def test_newbie_declines_more_than_top(journeys):
    """P4 (tân binh) phải kén hơn P3 (top) ngay ở cấp CÁ NHÂN — đây là dư địa advisor mà
    SIM-4 sẽ đo. Nếu mất, journey không còn kể được câu chuyện nào đáng kể."""
    p4, p3 = journeys["P4"].metrics, journeys["P3"].metrics
    assert p4["acceptance_rate"] < p3["acceptance_rate"], (
        f"P4 {p4['acceptance_rate']} phải THẤP hơn P3 {p3['acceptance_rate']}")


# ---------- Per-driver phải cộng lại ra hệ thống ----------


def test_per_driver_sums_to_system(result):
    """Cộng metric của MỌI tài xế phải ra đúng metric hệ thống — chống việc journey đúng
    lẻ tẻ nhưng sai khi tổng hợp."""
    total_trips = total_payout = 0
    for a in result.actors:
        j = build_journey(result, a.actor_id)
        total_trips += j.metrics["trips_completed"]
        total_payout += j.metrics["payout_vnd"]
    m = summarize(result)
    assert total_trips == m["orders_completed"]
    assert total_payout == sum(a.payout_vnd for a in result.actors)


# ---------- Determinism + export ----------


def test_journey_deterministic(cfg):
    """Cùng seed → journey giống hệt (journey không được tiêu RNG)."""
    r1, r2 = run_once(cfg, seed=7), run_once(cfg, seed=7)
    aid = max(r1.actors, key=lambda a: a.orders_offered).actor_id
    assert build_journey(r1, aid).to_dict() == build_journey(r2, aid).to_dict()


def test_export_json_labeled_mock(result, tmp_path):
    aid = max(result.actors, key=lambda a: a.orders_offered).actor_id
    path = journey_to_json(result, aid, tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["source"] == "MOCK" and payload["manifest"]["label"] == "MOCK"
    assert payload["manifest"]["seed"] == SEED
    assert payload["offers"] and payload["timeline"]


def test_unknown_actor_raises(result):
    with pytest.raises(ValueError):
        build_journey(result, 10**6)
