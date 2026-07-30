"""`D-M3-10` — cổng hợp lệ của mọi arm A/B: adherence PHẢI nằm trong artifact.

Luật đã có từ lâu trong tài liệu: *"mọi arm phải báo kèm `decision_adherence` per archetype
so với danh nghĩa; lệch > 0,02 ⇒ TREO kết quả"*. Đo được 2026-07-30: `parallel.py` /
`sim_metrics.py` / `scripts/run_parallel.py` tham chiếu `adherence`/`followed`/`decided`
**ĐÚNG 0 LẦN**, và artifact 35–39 **không có khoá `adherence` nào** ⇒ cổng chỉ tồn tại trên
giấy.

Đó là **lý do trực tiếp** `D-M3-01` sống được qua 39 artifact: `shift_extend` báo
`decision_adherence = 1,000` (sự thật 0,473) suốt 39 lần mà không cổng nào bắn.

File này khoá ba thứ vào luật:
1. `PairResult` mang adherence của **cả hai** arm (bài học `DET-01`: arm đối chứng cũng phải
   được đo, không giả định sạch);
2. `run_ladder` ghi `adherence` + `verdict` vào mỗi bậc;
3. cổng BẤT KHẢ **thật sự bắt được** `D-M3-01` — test cuối chứng minh nó ĐỎ ĐƯỢC, vì một cổng
   không đỏ được thì vô giá trị (bài học `L5-04`: test tautology sống 39 artifact).
"""
from __future__ import annotations

import pytest

from gsm_sim.config import Config
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with, run_ladder, run_pair
from gsm_sim.runner import run_once
from gsm_sim.sim_metrics import (IMPOSSIBLE_ADHERENCE_MIN_DENOM, adherence_audit,
                                 adherence_flags)

CHANNELS = ("shift_plan", "accept_lift", "shift_extend", "positioning")


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def run_all(cfg):
    return run_once(_cfg_with(cfg, enabled=True, actor_id=None,
                              channels=CHANNEL_LADDER["all"], coverage="all"), 1000)


def test_audit_covers_every_channel_that_spoke(run_all):
    """Mỗi kênh có nói thì phải có một hàng adherence — không kênh nào vô hình."""
    audit = adherence_audit(run_all)
    for ch in CHANNELS:
        assert ch in audit["by_channel"], (
            f"kênh {ch} không có hàng adherence ⇒ nó vô hình với mọi cổng")
        assert audit["by_channel"][ch]["decided"] > 0, f"{ch}: mẫu số rỗng"


def test_audit_splits_by_archetype(run_all):
    """Luật đòi 'per archetype' — gộp toàn đội che được một archetype lệch hẳn."""
    audit = adherence_audit(run_all)
    keys = audit["by_channel_archetype"]
    assert keys, "không có ô (kênh × archetype)"
    arche = {k.split("|", 1)[1] for k in keys}
    assert len(arche) >= 3, f"chỉ {len(arche)} archetype — 'per archetype' mất nghĩa: {arche}"


def test_no_impossible_state_on_fixed_code(run_all):
    """Sau `D-M3-01`, không kênh nào được ở trạng thái bất khả."""
    audit = adherence_audit(run_all)
    assert audit["flags"] == [], f"cờ BẤT KHẢ còn sống: {audit['flags']}"


def test_pair_result_carries_both_arms(cfg):
    """`DET-01`: arm đối chứng cũng phải ĐƯỢC ĐO, không giả định là sạch."""
    pr = run_pair(cfg, 1000, channels=CHANNEL_LADDER["all"], coverage="all")
    assert isinstance(pr.adherence_a, dict) and isinstance(pr.adherence_b, dict)
    assert pr.adherence_b["by_channel"], "arm B không có adherence"
    # Arm A tắt advice ⇒ không kênh nào; đó là kết quả ĐÚNG, và nó phải KIỂM ĐƯỢC
    # chứ không phải được giả định.
    assert pr.adherence_a["by_channel"] == {}, (
        f"arm A tắt advice mà vẫn có kênh: {sorted(pr.adherence_a['by_channel'])}")


def test_ladder_artifact_carries_verdict(cfg):
    """Artifact phải mang `verdict` — người đọc thấy TREO/OK mà không phải tự suy."""
    res = run_ladder(cfg, [1000], steps=("all",), coverage="all")
    adh = res["all"]["adherence"]
    assert adh["verdict"] in ("OK", "TREO — thước đo hỏng")
    assert adh["by_channel"], "bậc thang không ghi adherence"
    assert adh["verdict"] == "OK", f"cờ: {adh['flags_per_seed']}"


# ---------- cổng phải ĐỎ ĐƯỢC, nếu không nó vô giá trị (bài học L5-04) ----------


def test_gate_catches_d_m3_01_denominator_bug():
    """Dựng lại ĐÚNG trạng thái `D-M3-01` và đòi cổng bắn.

    Đây là test quan trọng nhất của file: nó chứng minh cổng **không phải** một lời hứa.
    Trạng thái tái dựng: tử số = mẫu số (event chỉ tồn tại ở ca đã theo).
    """
    bug = {"shift_extend": {"decided": 101, "followed": 101, "dismissed": 0,
                            "suppressed": 0, "event_decided": 101, "event_followed": 101,
                            "decision_adherence": 1.0, "event_adherence": 1.0}}
    flags = adherence_flags(bug)
    assert flags, "cổng KHÔNG bắn trên đúng trạng thái D-M3-01 ⇒ cổng vô giá trị"
    assert "shift_extend" in flags[0] and "1,000" in flags[0]


def test_gate_catches_empty_denominator():
    """`rest_window` có event nhưng 0 quyết định vào mẫu số ⇒ mẫu số RỖNG, phải bắn."""
    flags = adherence_flags({"rest_window": {
        "decided": 0, "followed": 0, "dismissed": 0, "suppressed": 0,
        "event_decided": 0, "event_followed": 0,
        "decision_adherence": None, "event_adherence": None}})
    assert flags and "decided=0" in flags[0]


def test_gate_catches_dead_event_unit():
    """Một nửa bộ đo hai-đơn-vị chết im lặng (đường sản phẩm: `L4-01`) ⇒ phải bắn."""
    flags = adherence_flags({"bonus": {
        "decided": 50, "followed": 25, "dismissed": 10, "suppressed": 0,
        "event_decided": 0, "event_followed": 25,
        "decision_adherence": 0.5, "event_adherence": None}})
    assert flags and "event_decided=0" in flags[0]


def test_gate_does_not_cry_wolf_on_small_denominator():
    """Mẫu số nhỏ thì 1,0 CÓ THỂ là may mắn thật ⇒ không được bắn.

    Không có lan can này, cổng sẽ bắn trên nhiễu và người sửa sẽ tắt cổng — đúng mẫu
    `D-R20` (test bám một seed rồi bị nới CODE thay vì nới ngưỡng).
    """
    n = IMPOSSIBLE_ADHERENCE_MIN_DENOM - 1
    flags = adherence_flags({"shift_extend": {
        "decided": n, "followed": n, "dismissed": 0, "suppressed": 0,
        "event_decided": n, "event_followed": n,
        "decision_adherence": 1.0, "event_adherence": 1.0}})
    assert flags == [], f"bắn trên mẫu số {n} (quá nhỏ) ⇒ sẽ bị tắt vì nhiễu: {flags}"


# ---------- D-M3-10 cổng THỐNG KÊ (chốt UPDATE-103 §3): z Poisson-binomial, |z| > 4 ----------
#
# ⚠ Acceptance gốc trong PLAN viết "lệch 0,10 ở n≥250 ⇒ TREO" — TỰ MÂU THUẪN với ngưỡng 4:
# z = 0,10/√(0,25/250) = 3,16 < 4. Đã đính chính trong PLAN: cần n ≥ (2/0,10)² = 400.
# Ghi lại ở đây để người sau thấy các hằng số trong test DƯỚI là dẫn xuất, không phải tuỳ tiện.

from gsm_sim.sim_metrics import adherence_stat_flags, poisson_binomial_z

NOMINAL = {"P1": 0.55, "P2": 0.50, "P3": 0.30, "P4": 0.75, "P5": 0.30, "P6": 0.50, "P7": 0.50}


def _cell(ch: str, arche: str, decided: int, followed: int) -> dict:
    return {f"{ch}|{arche}": {"decided": decided, "followed": followed}}


def test_stat_gate_fires_on_real_deviation():
    """Acceptance #1: lệch 0,10 ở n=500 ⇒ TREO (z ≈ 4,47 > 4)."""
    flags = adherence_stat_flags(_cell("x", "P2", 500, 300), NOMINAL)
    assert flags and "TREO" in flags[0], "lệch thật 0,10 @ n=500 mà cổng im"


def test_stat_gate_quiet_on_noise():
    """Acceptance #2: lệch 0,01 ở n=500 ⇒ OK (z ≈ 0,45) — cổng bắn oan sẽ bị TẮT (mẫu D-R20)."""
    assert adherence_stat_flags(_cell("x", "P2", 500, 255), NOMINAL) == []


def test_stat_gate_catches_d_m3_01_with_z_10():
    """Acceptance #3: dựng lại đúng trạng thái `D-M3-01` (1,000 trên 101 QĐ) ⇒ TREO, z ≈ 10.

    Đây là con số đã dùng để DẪN XUẤT ngưỡng (UPDATE-103 §3) — nếu test này đỏ thì hoặc công
    thức sai, hoặc ai đó đã nới ngưỡng. Cả hai đều phải dừng lại xem xét, không sửa test.
    """
    z = poisson_binomial_z(101, [0.5] * 101)
    assert 9.5 < z < 10.5, f"z = {z} — lệch hẳn con số dẫn xuất 10,0"
    flags = adherence_stat_flags(_cell("shift_extend", "P2", 101, 101), NOMINAL)
    assert flags and "z = +10" in flags[0]


def test_stat_gate_uses_archetype_mixture_not_fleet_mean():
    """Acceptance #4 — test mà BOOTSTRAP không vượt được: kênh chỉ chạm P3/P5 (p = 0,30)
    với adherence đo 0,30 phải OK, dù trung bình toàn đội là ~0,51.

    Bootstrap resample các quyết định đã quan sát ⇒ coi mọi quyết định là trao đổi được ⇒
    không phân biệt được null 0,30 với null 0,51. Công thức Poisson-binomial thì có."""
    mix = {"y|P3": {"decided": 200, "followed": 60},
           "y|P5": {"decided": 200, "followed": 60}}
    assert adherence_stat_flags(mix, NOMINAL) == [], (
        "cổng so kênh P3/P5 với trung bình đội thay vì hỗn hợp archetype của CHÍNH kênh đó")


def test_stat_gate_skips_tiny_denominators():
    """Mẫu số < STAT_GATE_MIN_DENOM: phương sai ước lượng quá thô ⇒ không kết luận."""
    assert adherence_stat_flags(_cell("x", "P2", 5, 5), NOMINAL) == []


def test_stat_gate_mixture_aggregation_fires():
    """Tổng hợp theo KÊNH (hỗn hợp thật của Poisson-binomial): hai ô lệch cùng chiều, mỗi ô
    chưa đủ |z|>4, nhưng KÊNH gộp thì đủ ⇒ phải bắn ở tầng kênh."""
    mix = {"y|P2": {"decided": 300, "followed": 180},   # 0,60 vs 0,50: z_ô ≈ 3,46
           "y|P6": {"decided": 300, "followed": 180}}   # idem
    flags = adherence_stat_flags(mix, NOMINAL)
    assert flags and "gộp hỗn hợp archetype" in flags[0], (
        "hai ô cùng lệch 3,5σ mà tầng kênh (z gộp ≈ 4,9) không bắn — mất đúng ca mà "
        "per-ô một mình không bắt được")
