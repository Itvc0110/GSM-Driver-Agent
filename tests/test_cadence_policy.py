"""ĐA-04 lõi — `gsm_core/lifecycle/cadence.py`: MỘT LUẬT nhịp advice cho sim và UI.

Design đã duyệt (audit `04-*` §5): ≥20′/topic · ≤6 proactive/ca · anchor theo PHA CA
(bỏ wall-clock) · while-driving → QUEUE · MỘT adherence draw cho
(decision_id, material_revision) · typed suppression reason.

Cường chốt 2026-07-29: cửa sổ `dismissed` = **hết PHA ca hiện tại** (không dùng hằng số
phút vô căn cứ; không im hết ca vì sẽ chặn cả cảnh báo an toàn/mất thưởng về sau).
"""

from __future__ import annotations

import pytest

from gsm_core.lifecycle.cadence import (
    PRESENT, QUEUE, SUPPRESS, CadenceConfig, CadenceMemory, adherence_coin,
    evaluate, shift_phase,
)

CFG = CadenceConfig()


def _mem(**kw) -> CadenceMemory:
    """Memory rỗng — mọi trường override qua kwargs."""
    return CadenceMemory(
        last_decided_min=kw.get("last_decided_min", {}),
        dismissed_in_phase=kw.get("dismissed_in_phase", {}),
        proactive_count=kw.get("proactive_count", 0),
    )


# ---------- baseline đã duyệt ----------

def test_defaults_match_approved_baseline():
    assert CFG.min_gap_min_per_topic == 20
    assert CFG.max_proactive_per_shift == 6


def test_clean_path_presents():
    v = evaluate("shift_plan", now_min=600.0, phase="mid", memory=_mem(), cfg=CFG)
    assert v.verdict == PRESENT and v.reason is None


# ---------- cooldown 20′/topic ----------

def test_topic_cooldown_blocks_then_releases():
    """Cooldown THỰC THI = `effective_gap_min` = max(min_gap 20′, bucket quyết định 30′).

    ⚠ Số kỳ vọng đổi 620 → 630 ngày 2026-07-31 (UPDATE-112): KHÔNG phải nới test cho xanh —
    hành vi cũ (nói lại ở phút 21–29) chính là lỗi `L4-03` đã reproduce: card tới tay tài xế
    nhưng `event_id` trùng bucket ⇒ không event, không tiêu ngân sách. Bất biến đúng nằm ở
    test dưới (`test_mot_quyet_dinh_toi_da_mot_lan_noi`)."""
    mem = _mem(last_decided_min={"shift_plan": 600.0})
    early = evaluate("shift_plan", now_min=615.0, phase="mid", memory=mem, cfg=CFG)
    assert early.verdict == SUPPRESS and early.reason == "topic_cooldown"
    assert early.next_eligible_min == 600.0 + CFG.effective_gap_min == 630.0
    ok = evaluate("shift_plan", now_min=630.0, phase="mid", memory=mem, cfg=CFG)
    assert ok.verdict == PRESENT


def test_mot_quyet_dinh_toi_da_mot_lan_noi():
    """BẤT BIẾN `L4-03` — luật dẫn xuất, không phải hằng số: hai lần được phép nói KHÔNG BAO
    GIỜ rơi vào cùng một bucket quyết định. Quét toàn dải phút của một ca.

    Đỏ trước fix: cooldown 20′ < bucket 30′ ⇒ t=600 và t=620 cùng bucket 20 mà cả hai PRESENT.
    """
    from gsm_core.lifecycle.cadence import decision_bucket
    for t0 in range(300, 1400, 7):
        mem = _mem(last_decided_min={"shift_plan": float(t0)})
        for dt in range(1, 61):
            v = evaluate("shift_plan", now_min=float(t0 + dt), phase="mid", memory=mem, cfg=CFG)
            if v.verdict != PRESENT:
                continue
            assert decision_bucket(float(t0)) != decision_bucket(float(t0 + dt)), (
                f"nói lại ở t={t0 + dt} rơi CÙNG bucket quyết định với lần nói t={t0} — "
                f"lặp lại chính mình, và event sẽ bị store dedupe (L4-03)")


def test_effective_gap_theo_kenh_co_nhip_khac():
    """Kênh có nhịp ra quyết định thưa hơn (positioning: planner tick 60′) ⇒ cooldown hiệu
    dụng phải bằng nhịp đó, không phải 20′ chung."""
    from dataclasses import replace
    cfg60 = replace(CFG, decision_bucket_min=60.0)
    assert cfg60.effective_gap_min == 60.0
    assert CFG.effective_gap_min == 30.0


def test_cooldown_is_per_topic_not_global():
    """Nhắc đổi pin không được khoá miệng cảnh báo thưởng — cooldown theo TOPIC."""
    mem = _mem(last_decided_min={"rest_window": 600.0})
    v = evaluate("accept_lift", now_min=605.0, phase="mid", memory=mem, cfg=CFG)
    assert v.verdict == PRESENT


# ---------- budget ≤6 proactive/ca ----------

def test_shift_budget_exhausted():
    v = evaluate("shift_plan", now_min=600.0, phase="mid",
                 memory=_mem(proactive_count=6), cfg=CFG)
    assert v.verdict == SUPPRESS and v.reason == "shift_budget_exhausted"
    v5 = evaluate("shift_plan", now_min=600.0, phase="mid",
                  memory=_mem(proactive_count=5), cfg=CFG)
    assert v5.verdict == PRESENT


# ---------- dismissed = hết PHA (verdict Cường) ----------

def test_dismissed_silences_only_current_phase():
    mem = _mem(dismissed_in_phase={"rest_window": "mid"})
    same = evaluate("rest_window", now_min=600.0, phase="mid", memory=mem, cfg=CFG)
    assert same.verdict == SUPPRESS and same.reason == "dismissed_for_window"
    later = evaluate("rest_window", now_min=900.0, phase="late", memory=mem, cfg=CFG)
    assert later.verdict == PRESENT, "sang PHA MỚI phải được nói lại (an toàn/thưởng)"


def test_dismissed_does_not_leak_across_topics():
    mem = _mem(dismissed_in_phase={"rest_window": "mid"})
    assert evaluate("accept_lift", now_min=600.0, phase="mid",
                    memory=mem, cfg=CFG).verdict == PRESENT


# ---------- safety: while-driving → QUEUE (không mất, chỉ hoãn) ----------

def test_driving_queues_not_suppresses():
    v = evaluate("accept_lift", now_min=600.0, phase="mid", memory=_mem(),
                 cfg=CFG, is_driving=True)
    assert v.verdict == QUEUE and v.reason == "unsafe_while_moving"


def test_safety_topic_presents_even_while_driving():
    """Card chữ không phải emergency modality: đang lái thì phải hoãn an toàn."""
    v = evaluate("safety", now_min=600.0, phase="mid", memory=_mem(),
                 cfg=CFG, is_driving=True)
    assert v.verdict == QUEUE and v.reason == "unsafe_while_moving"


def test_budget_does_not_block_safety():
    v = evaluate("safety", now_min=600.0, phase="mid",
                 memory=_mem(proactive_count=99), cfg=CFG)
    assert v.verdict == PRESENT


# ---------- pha ca ----------

def test_safety_beats_dismiss_and_cooldown():
    """R-16 (soi đối kháng vòng 2): ưu tiên safety trước đây chỉ được pin MỘT NỬA.

    Có test safety-vs-`is_driving` và safety-vs-budget, nhưng KHÔNG có safety-vs-`dismissed`
    và safety-vs-`cooldown`. Mutation đưa hai nhánh đó lên trước nhánh safety ⇒ mọi test
    xanh, mà hậu quả sản phẩm là **bỏ qua một thẻ an toàn làm im TOÀN BỘ cảnh báo an toàn
    tới hết pha** — đúng thứ priority `safety > policy > demand` sinh ra để cấm."""
    mem = CadenceMemory(dismissed_in_phase={"safety": "mid"},
                        last_decided_min={"safety": 599.0},
                        proactive_count=99)
    v = evaluate("safety", now_min=600.0, phase="mid", memory=mem)
    assert v.verdict == PRESENT, f"safety phải vượt cả dismiss lẫn cooldown lẫn budget: {v}"


@pytest.mark.parametrize("elapsed,expect", [
    (0.0, "early"), (149.0, "early"), (150.0, "mid"),
    (449.0, "mid"), (450.0, "late"), (600.0, "late"),
])
def test_shift_phase_boundaries(elapsed, expect):
    """Ca 10h (600′): ranh giới 25% = 150′, 75% = 450′."""
    assert shift_phase(elapsed, 600.0) == expect


def test_shift_phase_degenerate_shift():
    assert shift_phase(0.0, 0.0) == "early"      # ca rỗng: không nổ, không chia 0


# ---------- keyed adherence coin (giết washout D-SIM-14/D-A3-01) ----------

def test_decision_bucket_min_is_pinned_and_meaningful():
    """R-06 (soi đối kháng vòng 2): `DECISION_BUCKET_MIN` tự nhận trong comment là "NGUỒN SỰ
    THẬT DUY NHẤT, sai là washout sống lại im lặng" — nhưng KHÔNG test nào pin nó.

    Vì sao pin giá trị là chưa đủ: đổi 30,0 → 2,0 thì coin và `world._decision_id` co lại
    NHẤT QUÁN, nên `test_recheck_does_not_reroll` vẫn xanh — washout sống lại dạng "hỏi lại
    tới khi nghe" mà không test nào đỏ. Nên pin cả NGỮ NGHĨA: hai lần hỏi cách nhau dưới
    30′ phải là MỘT quyết định."""
    from gsm_core.lifecycle.cadence import DECISION_BUCKET_MIN, decision_bucket
    assert DECISION_BUCKET_MIN == 30.0
    # ngữ nghĩa: <30′ ⇒ cùng bucket ⇒ cùng coin; ≥30′ ⇒ được phép khác
    assert decision_bucket(600.0) == decision_bucket(629.9)
    assert decision_bucket(600.0) != decision_bucket(630.0)
    k = lambda t: adherence_coin(7, f"3-accept_lift-{decision_bucket(t)}", "lift")
    assert k(600.0) == k(629.9), "trong cùng bucket phải MỘT coin (chống re-roll)"
    # và bucket phải RỘNG HƠN cooldown, nếu không một bucket chứa hai lần NÓI hợp lệ
    assert DECISION_BUCKET_MIN >= CFG.min_gap_min_per_topic, (
        f"bucket {DECISION_BUCKET_MIN}′ hẹp hơn cooldown {CFG.min_gap_min_per_topic}′ ⇒ "
        "hai lần nói khác nhau dùng chung một coin")


def test_coin_deterministic_same_key():
    a = adherence_coin(1000, "slth-x-3-shift_plan-8", "REST")
    b = adherence_coin(1000, "slth-x-3-shift_plan-8", "REST")
    assert a == b, "re-check cùng quyết định KHÔNG được re-roll (đây là washout)"


def test_coin_changes_when_content_changes():
    a = adherence_coin(1000, "slth-x-3-shift_plan-8", "REST")
    b = adherence_coin(1000, "slth-x-3-shift_plan-8", "ONLINE")
    assert a != b, "nội dung khuyên đổi thật ⇒ coin mới (material_revision)"


def test_coin_changes_with_seed_and_decision():
    base = adherence_coin(1000, "d1", "m")
    assert adherence_coin(1001, "d1", "m") != base
    assert adherence_coin(1000, "d2", "m") != base


def test_coin_in_unit_range_and_roughly_uniform():
    xs = [adherence_coin(7, f"d-{i}", "m") for i in range(10000)]
    assert all(0.0 <= x < 1.0 for x in xs)
    mean = sum(xs) / len(xs)
    assert 0.48 < mean < 0.52, f"coin lệch uniform: mean={mean:.4f}"
    # phủ đều 10 khoảng — bắt hàm băm dồn cục
    buckets = [0] * 10
    for x in xs:
        buckets[min(9, int(x * 10))] += 1
    assert all(800 < b < 1200 for b in buckets), buckets
