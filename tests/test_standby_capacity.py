"""Hồi sinh S4 — lời khuyên VỊ TRÍ có TRẦN, gán theo lô (T-045a b3).

## Vì sao S4 phải bật CÙNG heatmap, không được để sau (hồ sơ `19-*` §5)

Heatmap không có capacity ledger là **cỗ máy tạo dồn cục**: nguồn ngoài xác nhận *"herding vẫn là
vấn đề nền tảng"* dù đã có heatmap; hồ sơ `07` đo được khuyên diện rộng làm served GIẢM. HHI dồn
cục hiện ≈ 0 **chỉ vì** advisor chưa khuyên vị trí — bật kênh này không kèm trần là tự tạo ra đúng
vấn đề mình vừa xây thước để đo. Đây cũng là rủi ro Cường nêu trong DIRECTIVES §14.1: *"ai cũng
chọn ra điểm đông khách hay sạc cùng 1 lúc thì khách khó bắt xe"*.

## Kiến trúc đã chốt (Cường, planning 2026-07-28)

**BATCH TICK**: mỗi `advice.bucket_min`, World gom mọi tài xế được phủ đang rỗi → dựng
`MarketStateView` → S4 `capacity_alloc` gán MỘT lần (Hungarian) → `standby_plan`. Vòng idle chỉ
ĐỌC. Không greedy trừ dần — mất tính gán tối ưu và không so được với phân bổ tập trung (ĐA-09).

**Cờ `advice.positioning_overrides`**: `"off"` (mặc định — hành vi cũ y hệt) | `"wait_only"`
(chỉ ghi đè khi bản năng là WAIT) | `"wait_and_relocate"` (đổi cả đích relocate). Đo CẢ HAI ở b4.
"""

from __future__ import annotations

import copy
from collections import Counter, defaultdict

import pytest

from gsm_sim.config import Config
from gsm_sim.runner import run_once

SEED = 1000


def _cfg(base, mode: str | None, **adv_extra):
    c = Config(copy.deepcopy(base.data), base.root_dir)
    adv = c.data.setdefault("advice", {})
    adv.update({"enabled": True, "coverage": "all"})
    if mode is not None:
        adv["positioning_overrides"] = mode
    adv.update(adv_extra)
    return c


@pytest.fixture(scope="module")
def base():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def run_on(base):
    """Một run với kênh vị trí BẬT mạnh nhất — dùng chung cho các test đọc event."""
    return run_once(_cfg(base, "wait_and_relocate"), SEED)


# ---------- 1. Cờ thật sự điều khiển: off == không có cờ, từng bit ----------

def test_off_is_bit_identical_to_flag_absent(base):
    """`positioning_overrides: off` phải cho trace Y HỆT config không có khoá này.

    Nếu chỉ riêng việc CÓ cờ (dù tắt) đã làm lệch trace — planner tiêu RNG, dịch lịch SimPy —
    thì mọi so sánh A/B từ đây về sau đều đo lẫn nhiễu của chính cái cờ. Đây là tiêu chí 7
    của kế hoạch đo, và là điều kiện để baseline cũ còn dùng được."""
    r_absent = run_once(_cfg(base, None), SEED)
    r_off = run_once(_cfg(base, "off"), SEED)
    pay_a = {a.actor_id: a.payout_vnd for a in r_absent.actors}
    pay_o = {a.actor_id: a.payout_vnd for a in r_off.actors}
    assert pay_a == pay_o, "cờ OFF vẫn làm lệch payout — planner đang chạy/tiêu RNG khi tắt"
    assert len(r_absent.events) == len(r_off.events), "cờ OFF làm lệch số event"
    assert not [e for e in r_off.events if e.kind.startswith("standby")], \
        "cờ OFF mà vẫn có event standby"


# ---------- 2. Trần là TRẦN ----------

def test_no_cell_receives_more_than_its_capacity(run_on):
    """Bất biến sống còn: trong MỖI lượt gán, số người được khuyên tới một ô ≤ trần còn lại
    của ô đó TẠI THỜI ĐIỂM GÁN.

    Event `standby_alloc` phải tự mang đủ bằng chứng (`cell`, `n_assigned`, `capacity_left`) —
    không bắt test dựng lại MarketState (hai chỗ cùng tính một luật là mẫu lỗi T-046)."""
    allocs = [e for e in run_on.events if e.kind == "standby_alloc"]
    assert allocs, "kênh bật mà không có lượt gán nào — planner không chạy?"
    for e in allocs:
        n, cap = int(e.detail["n_assigned"]), int(e.detail["capacity_left"])
        assert n <= cap, (
            f"t={e.t_min:.0f} ô {e.cell}: gán {n} người vào ô chỉ còn trần {cap} — "
            f"S4 đang tạo dồn cục thay vì chống nó")


def test_excess_candidates_are_dropped_not_squeezed(run_on):
    """Dư người so với tổng trần ⇒ phần dư là `unassigned` (im lặng), KHÔNG nhét thêm.

    Bỏ advice là hành vi ĐÚNG của S4 (docstring gốc: "dư thì unassigned — bỏ advice, chống
    dồn"). Test đọc tổng từ event summary của planner."""
    summaries = [e for e in run_on.events if e.kind == "standby_planner"]
    assert summaries, "planner không ghi summary — không audit được"
    total_unassigned = sum(int(e.detail["n_unassigned"]) for e in summaries)
    total_assigned = sum(int(e.detail["n_assigned"]) for e in summaries)
    assert total_assigned > 0, "không gán được ai — kênh chết"
    # 90 tài xế / trần từng ô nhỏ ⇒ PHẢI có lúc dư. Nếu không bao giờ dư thì hoặc trần quá
    # rộng (không ràng buộc gì) hoặc candidates quá ít (kênh gần chết) — cả hai đáng ngờ.
    assert total_unassigned > 0, (
        "không lần nào dư candidate — trần không ràng buộc gì; kiểm capacity_left và bucket_min")


# ---------- 3. Thiếu dữ liệu cung ⇒ im lặng ----------

def test_absent_supply_means_zero_positioning_advice(base):
    """Không có dữ liệu cung ⇒ `positioning_allowed = False` ⇒ KHÔNG một lời khuyên vị trí nào.

    Đây là bài học 'hidden fallback' đã trả giá hai lần (UPDATE-075 supply_cell_hhi trả 0.0 âm
    thầm; UPDATE-079 soc_pct=None thành pin đầy). Im lặng khi mù, không đoán."""
    r = run_once(_cfg(base, "wait_and_relocate", market_supply_available=False), SEED)
    assert not [e for e in r.events if e.kind == "standby_alloc"], \
        "mù dữ liệu cung mà vẫn khuyên vị trí — hidden fallback quay lại"


# ---------- 4. Ranh giới ghi đè: bài học REST ----------

def test_wait_only_never_overrides_productive_actions(base):
    """`wait_only` chỉ được ghi đè khi bản năng là WAIT.

    Bài học đã trả giá bằng số: chặn ghi đè go_swap/relocate của kênh REST làm advisor TỆ ĐI
    (−14.125đ → −32.383đ) vì các hành động đó đang CỨU tài xế. Ở đây chiều ngược lại — không
    được cướp quyền của go_swap (pin), rest (sức khoẻ), end_shift (kết ca)."""
    r = run_once(_cfg(base, "wait_only"), SEED)
    followed = [e for e in r.events if e.kind == "standby_followed"]
    assert followed, "wait_only không có lượt follow nào — kênh chết hoặc adherence hỏng"
    bad = [e for e in followed if e.detail.get("from_action") != "wait"]
    assert not bad, (
        f"{len(bad)} lượt ghi đè hành động KHÔNG phải wait (vd {bad[0].detail}) — "
        f"đúng lỗi ghi đè quá tay đã bác bỏ ở kênh REST")


# ---------- 5. Vòng phản hồi khép kín ----------

def test_followed_advice_becomes_incoming_supply(run_on):
    """Tài xế nghe theo ⇒ phải xuất hiện như CUNG ĐANG TỚI của ô đích (enroute_cell).

    Đây là vòng khép kín chống fallacy-of-composition: lời khuyên vừa phát trừ ngay vào trần
    cho người hỏi sau. Kiểm bằng event relocate có reason=standby."""
    stand_reloc = [e for e in run_on.events
                   if e.kind == "relocate" and e.detail.get("reason") == "standby"]
    followed = [e for e in run_on.events if e.kind == "standby_followed"]
    assert followed, "không có lượt follow nào"
    assert stand_reloc, "follow rồi mà không có relocate reason=standby — hành động không xảy ra"


# ---------- 6. An toàn sản phẩm ----------

def test_safety_flags_survive_to_the_event(run_on):
    """5 STANDBY_SAFETY_FLAGS của S4 phải đi tới tận event — không được rơi ở tầng bridge."""
    from gsm_core.solvers.capacity_alloc import STANDBY_SAFETY_FLAGS
    allocs = [e for e in run_on.events if e.kind == "standby_alloc"]
    assert allocs
    for e in allocs:
        flags = e.detail.get("safety_flags") or []
        assert set(STANDBY_SAFETY_FLAGS) <= set(flags), (
            f"thiếu safety flag: {sorted(set(STANDBY_SAFETY_FLAGS) - set(flags))} — "
            f"ranh giới sản phẩm F2-04 bị rơi trên đường từ solver tới event")


# ---------- 7. Determinism ----------

def test_standby_channel_is_deterministic(base):
    """Cùng seed ⇒ cùng kết quả, kể cả khi kênh vị trí bật (exact-repeat như mọi kênh khác)."""
    r1 = run_once(_cfg(base, "wait_and_relocate"), SEED)
    r2 = run_once(_cfg(base, "wait_and_relocate"), SEED)
    assert {a.actor_id: a.payout_vnd for a in r1.actors} == \
           {a.actor_id: a.payout_vnd for a in r2.actors}
    k1 = Counter(e.kind for e in r1.events)
    k2 = Counter(e.kind for e in r2.events)
    assert k1 == k2
