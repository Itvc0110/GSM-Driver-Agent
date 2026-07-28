"""Tài xế phải BIẾT SỐT RUỘT — cắt đuôi chờ phi thực tế (Q-08, T-045d).

## Vấn đề đo được

Khoảng chờ tối đa **244 phút** (đã từng 334) trong khi 20–30% đơn giờ cao điểm hết hạn. Truy nguyên
(hồ sơ `17-*`):

- vòng idle poll **mỗi 2 phút** ⇒ 244 phút = **122 lần ra quyết định** mà không dịch chuyển lần nào;
- `_actor_demand_hint` là **prior cache theo (actor, giờ)** — niềm tin **không cập nhật từ trải
  nghiệm**;
- `choose_idle_action` chỉ xét **ring-1** (6 ô, ~0,35 km), đòi hơn **25%**, rồi tung đồng xu 50%.

⇒ Nếu ô hiện tại là **cực đại địa phương** dưới niềm tin đó thì `best_cell == actor.cell` **suốt
cả giờ** — không có cả cú tung đồng xu. Tài xế ngồi 4 tiếng, không đơn nào, mà niềm tin "chỗ này
tốt nhất" **vẫn nguyên**.

## Ranh giới đã chốt (Q-08)

Đây là **bản năng**, KHÔNG phải lời khuyên: tài xế chỉ *sốt ruột đi xa hơn*, chứ không được biết
cầu ở đâu. Giá trị của advisor vẫn là **positioning CÓ THÔNG TIN** (đúng khu, đúng lúc,
capacity-aware). Vì vậy escalation phải:

- chỉ kích hoạt sau một ngưỡng rỗi (mặc định 30′) — vận hành bình thường KHÔNG đổi;
- **tắt được** về hành vi cũ bằng config;
- không dùng bất kỳ thông tin nào ngoài `demand_hint` mà actor vốn đã có.
"""

from __future__ import annotations

import copy
from collections import defaultdict

import pytest

from gsm_sim.config import Config
from gsm_sim.metrics import summarize
from gsm_sim.runner import run_once

SEEDS = (1000, 1001, 1002, 1003, 1004)
MAX_GAP_MIN = 90.0        # Q-08: không khoảng chờ nào > 90 phút
P99_GAP_MIN = 60.0        # Q-08: p99 < 60 phút


def _idle_gaps(r) -> list[float]:
    segs = defaultdict(list)
    for s in r.segments:
        segs[s["actor_id"]].append(s)
    out = []
    for ss in segs.values():
        ss.sort(key=lambda x: x["t0"])
        out += [b["t0"] - a["t1"] for a, b in zip(ss, ss[1:]) if b["t0"] > a["t1"]]
    return out


def _run(seed: int, **overrides):
    cfg = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c.data.setdefault("behavior", {}).update(overrides)
    return run_once(c, seed)


@pytest.fixture(scope="module")
def runs():
    return [_run(s) for s in SEEDS]


def test_no_implausible_idle_tail(runs):
    """Ngưỡng Q-08: không tài xế nào ngồi im quá 90 phút.

    Lý do phân định (agent chốt theo uỷ quyền): unserved/utilization trung bình là **dư địa hợp
    lệ** cho advisor; nhưng ngồi im hàng giờ trong khi đơn chết là **lỗi thế giới** — advisor
    không có lệnh nào tạo ra đơn hàng, nên đo advisor trên thế giới đó không cho kết luận dùng được.
    """
    worst = max(max(_idle_gaps(r)) for r in runs)
    assert worst <= MAX_GAP_MIN, (
        f"còn khoảng chờ {worst:.0f} phút — vượt ngưỡng khả tín vật lý {MAX_GAP_MIN:.0f}′. "
        f"Tài xế thật rỗi lâu như vậy sẽ tự đi chỗ khác.")


def test_idle_gap_p99_reasonable(runs):
    for r, seed in zip(runs, SEEDS):
        g = sorted(_idle_gaps(r))
        p99 = g[int(0.99 * len(g))]
        assert p99 < P99_GAP_MIN, f"seed {seed}: p99 khoảng chờ = {p99:.0f}′"


def test_impatience_can_be_switched_off(runs):
    """Tắt cờ ⇒ hành vi CŨ y hệt. Bắt buộc: mọi thay đổi hành vi phải tắt được về baseline
    để so sánh được (chuẩn `environment-variables.md`: mọi factor tắt được về 1)."""
    off = _run(SEEDS[0], idle_impatience_enabled=False)
    on = runs[0]
    assert max(_idle_gaps(off)) > max(_idle_gaps(on)), (
        "tắt cờ mà đuôi chờ không dài trở lại ⇒ cờ không thật sự điều khiển hành vi")


def test_impatience_does_not_hand_over_the_advisors_job(runs):
    """RANH GIỚI Q-08: sốt ruột là **bản năng**, không phải lời khuyên có thông tin.

    Nó được phép cắt đuôi, nhưng **không được** làm hệ thống tốt lên nhiều tới mức triệt tiêu dư
    địa của advisor. Ngưỡng: `served_rate` không được nhảy quá +0,05 so với bản tắt cờ.
    """
    import statistics as st
    on = st.mean(summarize(r)["served_rate"] for r in runs)
    off = st.mean(summarize(_run(s, idle_impatience_enabled=False))["served_rate"] for s in SEEDS)
    assert on - off <= 0.05, (
        f"served nhảy {on - off:+.3f} (off={off:.3f} on={on:.3f}) — bản năng đang làm thay việc "
        f"của advisor. Giảm mức escalation, đừng để nó thành 'positioning miễn phí'.")


def test_relocation_stays_local_knowledge_only(runs):
    """Tài xế KHÔNG được nhảy cóc khắp thành phố: bán kính tìm kiếm có trần."""
    from gsm_sim.geo import haversine_km
    for r in runs:
        for s in r.segments:
            # CHỈ xét relocate đi tìm khách; `deadhead_to_core` (về lõi sau khi trả khách
            # ngoài vùng) được phép đi xa — đó là hệ quả của cuốc, không phải tìm kiếm.
            if s["kind"] != "relocate" or s.get("reason") != "demand_seek":
                continue
            d = haversine_km(s["from_lat"], s["from_lon"], s["to_lat"], s["to_lon"])
            assert d <= 2.0, f"relocate {d:.2f} km — vượt tầm hiểu biết cục bộ của tài xế"
