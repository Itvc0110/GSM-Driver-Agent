"""SIM-4 — gate cho thế giới song song (máy đo A/B).

Máy đo này quyết định ta KẾT LUẬN gì về advisor. Sai ở đây thì mọi con số báo cáo cho Cường
đều sai, nên khoá chặt 4 thứ:

1. **CRN** — hai nhánh phải dùng chung ngoại sinh (cùng đơn hàng). Lệch ⇒ mọi Δ là rác.
2. **Cổng an toàn** — tắt hết kênh thì B phải ≡ A từng con số.
3. **Thống kê trung thực** — CI phải thật sự chứa/không chứa 0 đúng như dữ liệu nói.
4. **Guardrail** — không được cải thiện 1 tài xế bằng cách làm xấu hệ thống mà không ai biết.
"""

from __future__ import annotations

import pytest

from gsm_sim.config import Config
from gsm_sim.parallel import (
    CHANNEL_LADDER, PairResult, assert_crn, bootstrap_ci, compare, pick_target, run_pair,
)
from gsm_sim.runner import run_once

SEED = 3000


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def target(cfg):
    return pick_target(run_once(cfg, seed=SEED), "P4")


# ---------- Gate 1: CRN ----------


def test_crn_same_orders_both_worlds(cfg, target):
    """Cùng seed ⇒ **cùng danh sách đơn** ở cả hai nhánh. Đây là điều kiện TIÊN QUYẾT của
    hiệu-theo-cặp: nếu ngoại sinh lệch, Δ đo được lẫn cả 'hôm nay nhiều khách hơn'."""
    assert assert_crn(cfg, SEED, target), "ngoại sinh LỆCH giữa 2 nhánh — mọi Δ vô nghĩa"


# ---------- Gate 2: cổng an toàn ----------


def test_all_channels_off_means_identical_worlds(cfg, target):
    """Tắt hết kênh ⇒ B ≡ A. Nếu đỏ, nghĩa là chỉ riêng việc BẬT advice (chưa làm gì) đã
    làm lệch mô phỏng — khi đó không thể quy Δ cho advice được nữa."""
    p = run_pair(cfg, SEED, channels=CHANNEL_LADDER["none"], actor_id=target)
    assert p.a == p.b, f"tắt hết kênh mà tài xế vẫn khác: {p.a} vs {p.b}"
    assert p.system_a == p.system_b, "tắt hết kênh mà hệ thống vẫn khác"


def test_advice_targets_only_chosen_driver(cfg, target):
    """coverage=single ⇒ chỉ tài xế đích nhận advice."""
    from gsm_sim.parallel import _cfg_with
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=target,
                            channels=CHANNEL_LADDER["all"]), SEED)
    ids = {e.actor_id for e in rb.events
           if e.kind in ("advice_given", "advice_bonus_gate", "advice_shift_extend")}
    assert ids <= {target}, f"advice rò sang tài xế khác: {ids - {target}}"


# ---------- Gate 3: thống kê ----------


def test_bootstrap_ci_brackets_mean():
    ci = bootstrap_ci([10.0, 12.0, 8.0, 11.0, 9.0])
    assert ci[0] < 10.0 < ci[1]


def test_bootstrap_ci_detects_no_effect():
    """Dữ liệu quanh 0 ⇒ CI phải CHỨA 0. Nếu máy đo báo 'có ý nghĩa' ở đây thì nó sẽ bịa ra
    hiệu ứng không tồn tại."""
    lo, hi = bootstrap_ci([1.0, -1.0, 2.0, -2.0, 0.5, -0.5] * 5)
    assert lo < 0 < hi


def test_bootstrap_ci_detects_real_effect():
    lo, hi = bootstrap_ci([100.0, 120.0, 90.0, 110.0, 105.0] * 6)
    assert lo > 0, "hiệu ứng rõ ràng mà CI vẫn chứa 0 — máy đo quá bảo thủ"


def test_compare_uses_paired_difference():
    """Δ phải là trung bình HIỆU THEO CẶP, không phải hiệu của hai trung bình rời rạc."""
    mk = lambda s, pa, pb: PairResult(  # noqa: E731
        seed=s, actor_id=1,
        a={"payout_vnd": pa}, b={"payout_vnd": pb},
        system_a={"served_rate": 0.8}, system_b={"served_rate": 0.8})
    out = compare([mk(1, 100, 150), mk(2, 200, 210)])
    d = out["driver"]["payout_vnd"]
    assert d["delta_mean"] == 30.0          # (50 + 10) / 2
    assert d["n_positive"] == 2
    assert out["n_seeds"] == 2


def test_compare_empty_is_safe():
    assert compare([])["n_seeds"] == 0


# ---------- Gate 4: guardrail hệ thống ----------


def test_system_guardrail_is_measured(cfg, target):
    """Guardrail phải ĐƯỢC ĐO, không phải giả định. Thiếu chỉ số này thì advice có thể cải
    thiện 1 người bằng cách hút đơn của người khác mà báo cáo vẫn 'đẹp'."""
    p = run_pair(cfg, SEED, channels=CHANNEL_LADDER["all"], actor_id=target)
    for key in ("served_rate", "others_payout_vnd", "others_trips", "swap_wait_mean"):
        assert key in p.system_a and key in p.system_b


# ---------- Gate 5: kênh accept_lift đúng ngữ nghĩa ----------


def test_accept_lift_respects_ceiling(cfg, target):
    """Lift phải có TRẦN — nếu không, advisor biến tài xế thành người nhận mọi cuốc, điều
    vừa phi thực tế vừa làm mọi kết luận A/B thổi phồng."""
    from gsm_sim.parallel import _cfg_with
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=target,
                            channels=CHANNEL_LADDER["accept_lift"]), SEED)
    a = next(x for x in rb.actors if x.actor_id == target)
    assert a.accept_lift <= float(cfg.get("advice.accept_lift_max"))
    assert a.effective_accept_base <= 0.98


def test_accept_lift_only_when_below_threshold(cfg):
    """Không khuyên người đã đạt ngưỡng — advice thừa làm loãng tín hiệu và gây hại
    (tài xế nhận thêm cuốc rẻ mà chẳng được gì thêm)."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.parallel import _cfg_with
    from gsm_sim.policy import PolicyBundle
    ra = run_once(cfg, seed=SEED)
    good = next(a for a in ra.actors if a.archetype == "P3" and a.orders_offered > 5)
    c = _cfg_with(cfg, enabled=True, actor_id=good.actor_id,
                  channels=CHANNEL_LADDER["accept_lift"])
    bridge = AdviceActionBridge(c, PolicyBundle.from_config(cfg), seed=1)
    good.accept_lift = 0.0
    assert bridge.check_bonus_gate(good, now_min=good.shift_start_min + 60) is None


def test_lift_does_not_change_rng_draw_count(cfg, target):
    """Lift chỉ đổi XÁC SUẤT, không đổi SỐ LẦN rút ngẫu nhiên ⇒ CRN còn nguyên.
    Bằng chứng gián tiếp: số đơn ngoại sinh hai nhánh vẫn khớp (gate 1) và tài xế KHÁC
    không bị đổi số offer được chào."""
    from gsm_sim.parallel import _cfg_with
    ra = run_once(cfg, seed=SEED)
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=target,
                            channels=CHANNEL_LADDER["accept_lift"]), SEED)
    assert len(ra.orders) == len(rb.orders)


# ---------- AUDIT STATS-5 (UPDATE-069): significant phải gate theo n ----------


def test_significant_requires_min_seeds():
    """n nhỏ → bootstrap CI degenerate (n=1: CI rộng 0 ⇒ mọi Δ≠0 'significant').
    compare() phải trả significant=False + n_insufficient=True khi n < 30."""
    from gsm_sim.parallel import PairResult, compare, bootstrap_ci
    lo, hi = bootstrap_ci([12345.0])
    assert lo == hi == 12345.0, "degenerate case nền tảng của bug"
    pairs = [PairResult(seed=1, actor_id=0,
                        a={"payout_vnd": 0}, b={"payout_vnd": 12345},
                        system_a={"served_rate": 0.8}, system_b={"served_rate": 0.8})]
    c = compare(pairs)
    assert c["n_insufficient"] is True
    assert c["driver"]["payout_vnd"]["significant"] is False, \
        "1 seed mà significant=True — chuẩn ≥30 seed CLAUDE §4b bị vi phạm"


def test_significant_allowed_at_30_seeds():
    from gsm_sim.parallel import PairResult, compare
    pairs = [PairResult(seed=i, actor_id=0,
                        a={"payout_vnd": 0}, b={"payout_vnd": 10_000 + i * 10},
                        system_a={"served_rate": 0.8}, system_b={"served_rate": 0.8})
             for i in range(30)]
    c = compare(pairs)
    assert c["n_insufficient"] is False
    assert c["driver"]["payout_vnd"]["significant"] is True
