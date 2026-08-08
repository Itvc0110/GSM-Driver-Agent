"""SIM-1 REALISM GATE — chống trôi 3 tỷ lệ nền của simulation.

Bối cảnh (`specs/simulation/00-sim-overhaul-master.md` §2, chỉ thị Cường §5.7:
*"tỷ lệ hoàn thành chuyến tổng đang quá thấp so với thực tế"*). Đo baseline seed 42:

    served 61.9% (thực tế 80-85%) · accept 96.3% (thực tế 0.74-0.97 theo archetype)
    completion 99.6% (thực tế ~95%)

Gate này khoá cả 3 lại. **Chạy ≥30 seed** vì đây là hành vi stochastic: kết luận trên
1 seed không có ý nghĩa thống kê (harness CLAUDE.md §4b).

Ngưỡng đọc thế nào:
  - **median** là ước lượng của tỷ lệ HỆ THỐNG → kẹp vào dải thực tế.
  - **per-seed** nới rộng hơn: mỗi seed là MỘT NGÀY, ngày tốt/ngày xấu là dao động THẬT,
    không phải lỗi. Kẹp per-seed quá chặt sẽ biến biến động tự nhiên thành test đỏ.

BỘ NHỚ: **không giữ RunResult**. Mỗi run bị rút gọn NGAY thành aggregate nhỏ rồi thả cho
GC. Bản đầu giữ cả 30 world (events + orders + segments + gps ping) → polars OOM
(`ComputeError: not enough memory`) ở test khác khi chạy full suite.
"""

from __future__ import annotations

import statistics as st

import pytest

from gsm_sim.archetypes import ARCHETYPES
from gsm_sim.config import Config
from gsm_sim.runner import run_once

N_SEEDS = 30
SEEDS = list(range(1000, 1000 + N_SEEDS))

# --- dải mục tiêu (nguồn: spec §2 bảng chẩn đoán) ---
SERVED_MEDIAN = (0.78, 0.88)      # mục tiêu 80-85%, nới biên cho dao động seed
SERVED_PER_SEED = (0.70, 0.92)
COMPLETION_MEDIAN = (0.92, 0.97)
COMPLETION_PER_SEED = (0.90, 0.99)
CANCEL_MEDIAN = (0.02, 0.09)
ACCEPT_TOL_PP = 0.05              # realized accept vs accept_base của archetype
MAX_HOURLY_EXPIRY = 0.40          # không giờ nào được "chết"
MIN_HOUR_DEMAND = 20              # chỉ soi giờ có cầu đáng kể (đơn/ngày)


def _digest(result) -> dict:
    """Rút gọn 1 RunResult → aggregate nhỏ. Gọi xong là world được thả."""
    k: dict[str, int] = {}
    for e in result.events:
        k[e.kind] = k.get(e.kind, 0) + 1
    matched = k.get("order_matched", 0)
    assert matched, "sim không ghép được đơn nào"

    hour_demand: dict[int, int] = {}
    t_of = {}
    for o in result.orders:
        h = int(o.t_min // 60) % 24
        hour_demand[h] = hour_demand.get(h, 0) + 1
        t_of[o.order_id] = o.t_min
    hour_expired: dict[int, int] = {}
    for e in result.events:
        if e.kind == "order_expired":
            t = t_of.get(e.detail.get("order_id"))
            if t is not None:
                h = int(t // 60) % 24
                hour_expired[h] = hour_expired.get(h, 0) + 1

    by_arch: dict[str, list[int]] = {}
    for a in result.actors:
        # Cycle 1: mẫu số là `orders_decided` (lượt tài xế THẬT SỰ được hỏi), không phải
        # `orders_offered`. Dùng `offered` thì cổng này đo một đại lượng NHIỄM: 7/7 archetype
        # lệch âm trung bình −0,0246, mà **80% khoảng lệch của P7 là lượt bị chặn vì pin** —
        # tức cổng đang tố giác tài xế về những đơn họ chưa từng được hỏi.
        if a.orders_decided:
            cur = by_arch.setdefault(a.archetype, [0, 0])
            cur[0] += a.orders_accepted
            cur[1] += a.orders_decided

    censored = sum(1 for s in result.order_states.values() if s[0] == "CENSORED_END_OF_RUN")
    return {
        "served": matched / len(result.orders),
        "completion": k.get("dropoff", 0) / matched,
        "accept": matched / (matched + k.get("order_declined", 0)),
        "cancel": k.get("order_cancelled_after_accept", 0) / matched,
        "hour_demand": hour_demand,
        "hour_expired": hour_expired,
        "by_arch": by_arch,
        "lifecycle": (matched, k.get("dropoff", 0)
                      + k.get("order_cancelled_after_accept", 0) + censored),
    }


@pytest.fixture(scope="module")
def agg():
    cfg = Config.load("configs/pilot_dongda.yaml")
    return [_digest(run_once(cfg, seed=s)) for s in SEEDS]


def _median(agg, key):
    return st.median(a[key] for a in agg)


def _in(value, bounds):
    return bounds[0] <= value <= bounds[1]


# ---------- Gate 1: served (khuyết tật CHÍNH Cường chỉ ra) ----------


def test_served_rate_in_real_range(agg):
    """served = matched/orders. Baseline 61.9% ⇒ 38% cầu không ai nhận."""
    med = _median(agg, "served")
    assert _in(med, SERVED_MEDIAN), (
        f"served median {med:.3f} ngoài dải thực tế {SERVED_MEDIAN} "
        f"(min {min(a['served'] for a in agg):.3f}, max {max(a['served'] for a in agg):.3f})")


def test_served_no_catastrophic_seed(agg):
    """Không seed nào được sụp — bắt lỗi chỉ xuất hiện ở seed hiếm."""
    bad = [f"{a['served']:.3f}" for a in agg if not _in(a["served"], SERVED_PER_SEED)]
    assert not bad, f"{len(bad)}/{N_SEEDS} seed có served ngoài {SERVED_PER_SEED}: {bad[:5]}"


# ---------- Gate 2: completion (huỷ sau khi nhận) ----------


def test_completion_rate_not_too_clean(agg):
    """Baseline 99.6% = 'quá sạch'. Thực tế có khách bom/huỷ/sự cố ⇒ ~95%."""
    med = _median(agg, "completion")
    assert _in(med, COMPLETION_MEDIAN), (
        f"completion median {med:.3f} ngoài dải thực tế {COMPLETION_MEDIAN}")


def test_completion_per_seed(agg):
    bad = [f"{a['completion']:.3f}" for a in agg if not _in(a["completion"], COMPLETION_PER_SEED)]
    assert not bad, f"{len(bad)}/{N_SEEDS} seed có completion ngoài {COMPLETION_PER_SEED}: {bad[:5]}"


def test_cancel_after_accept_actually_happens(agg):
    """Chống hồi quy IM LẶNG: nếu ai đó tắt nhánh huỷ, completion về 1.0 — mà một mình
    ngưỡng completion có thể vẫn không bắt được. Bắt buộc event phải TỒN TẠI."""
    med = _median(agg, "cancel")
    assert _in(med, CANCEL_MEDIAN), f"cancel-after-accept median {med:.3f} ngoài {CANCEL_MEDIAN}"


# ---------- Gate 3: accept phải BÁM accept_base theo archetype ----------


def _arch_realized(agg) -> dict[str, float]:
    tot: dict[str, list[int]] = {}
    for a in agg:
        for name, (acc, off) in a["by_arch"].items():
            cur = tot.setdefault(name, [0, 0])
            cur[0] += acc
            cur[1] += off
    return {n: acc / off for n, (acc, off) in tot.items() if off}


def test_accept_matches_archetype_base(agg):
    """KHUYẾT TẬT 2 đã sửa: trước đây số hạng kinh tế áp đảo ⇒ P4 (base 0.80) thực tế
    nhận 94%, P3 (0.98) nhận 99.5% ⇒ **archetype vô nghĩa**. Nay realized phải bám base.
    """
    realized = _arch_realized(agg)
    assert realized, "không archetype nào được chào đơn"
    bad = [f"{n}: realized {v:.3f} vs base {ARCHETYPES[n].accept_base:.2f}"
           for n, v in sorted(realized.items())
           if abs(v - ARCHETYPES[n].accept_base) > ACCEPT_TOL_PP]
    assert not bad, f"accept lệch accept_base > {ACCEPT_TOL_PP:.0%}: {bad}"


def test_newbie_accepts_less_than_top(agg):
    """Kiểm tra Ý NGHĨA chứ không chỉ con số: P4 (tân binh) PHẢI kén hơn P3 (top).
    Đây là dư địa advisor — nếu mất, so sánh A/B ở SIM-4 sẽ vô nghĩa."""
    realized = _arch_realized(agg)
    assert realized["P4"] < realized["P3"] - 0.05, (
        f"P4 tân binh ({realized['P4']:.3f}) phải kén hơn RÕ RỆT P3 top ({realized['P3']:.3f})")


# ---------- Gate 4: không giờ nào "chết" vì thiếu cung ----------


def test_no_dead_hour(agg):
    """Khuyết tật 1: 05-06h từng có **0 tài xế** cho 93 đơn (94% hết hạn).
    Mọi giờ có cầu đáng kể phải được phục vụ ở mức chấp nhận được."""
    demand: dict[int, int] = {}
    expired: dict[int, int] = {}
    for a in agg:
        for h, v in a["hour_demand"].items():
            demand[h] = demand.get(h, 0) + v
        for h, v in a["hour_expired"].items():
            expired[h] = expired.get(h, 0) + v
    bad = []
    for h in sorted(demand):
        if demand[h] < MIN_HOUR_DEMAND * N_SEEDS:
            continue
        rate = expired.get(h, 0) / demand[h]
        if rate > MAX_HOURLY_EXPIRY:
            bad.append(f"{h:02d}h: {rate:.0%} hết hạn ({expired.get(h, 0)}/{demand[h]})")
    assert not bad, f"giờ bị bỏ đói (>{MAX_HOURLY_EXPIRY:.0%} hết hạn): {bad}"


# ---------- Gate 5: KHÔNG được vặn cầu để làm đẹp số ----------


def test_demand_not_tuned_down():
    """Ràng buộc plan SIM-1: chỉ sửa CUNG/HÀNH VI, giữ nguyên cầu. Nếu ai đó hạ
    `orders_per_day` để served đẹp lên thì gate ở trên sẽ xanh GIẢ ⇒ khoá riêng."""
    cfg = Config.load("configs/pilot_dongda.yaml")
    assert int(cfg.get("demand.orders_per_day")) == 1200, (
        "orders_per_day phải giữ 1200 — served cao nhờ giảm cầu là số đẹp GIẢ")


# ---------- Gate 6: coherence sim ↔ data (SIM-1 fix D) ----------


@pytest.fixture(scope="module")
def generated():
    """Sinh 3 ngày data thật qua đúng đường mockgen dùng ở production."""
    from gsm_core.mockgen.adapter_sim import generate_day
    from gsm_core.mockgen.profiles import build_profile_universe
    from gsm_core.mockgen.realdata import build_tables
    days = [generate_day("configs/pilot_dongda.yaml", seed=700 + i, date=f"2026-07-{1 + i:02d}")
            for i in range(3)]
    uni = build_profile_universe([p["driver_id"] for p in days[0]["driver_profile"]], 700)
    return days, uni, build_tables(days, uni, 700)


def test_no_silent_fallback_to_target_profile(generated):
    """`_emit_day` dùng `sim_stats.get(...)` → tra HỤT sẽ ÂM THẦM rơi về target profile
    (đúng loại 'hidden fallback' harness §4b cấm). Khoá lại: mọi driver-day BIKE có cuốc
    PHẢI tra được counter sim. Nếu đổi định dạng ngày/driver_id, test này đỏ thay vì
    lặng lẽ sinh data sai nguồn."""
    from gsm_core.mockgen.realdata import _date_of
    days, _, _ = generated
    missing = []
    for day in days:
        sd = day["_sim_driver_day"]
        keys = {(d, sd["date"]) for d in sd["stats"]}
        seen = {(t["driver_id"], _date_of(t["t_complete"])) for t in day["trip_record"]}
        missing += sorted(seen - keys)
    assert not missing, f"{len(missing)} driver-day BIKE không tra được sim_stats: {missing[:3]}"


def test_data_acceptance_coherent_with_sim(generated):
    """Khuyết tật xuyên tầng cũ: data nói 0.88 trong khi sim hành xử 0.96. Nay BIKE phải
    kể CÙNG một câu chuyện với sim."""
    _, uni, tables = generated
    bike = {d for d, p in uni.items() if p["simulated"]}
    acc = [r["acceptance_rate"] for r in tables["driver_statistic_daily"]
           if r["driver_id"] in bike]
    assert acc, "không có driver-day BIKE"
    med = st.median(acc)
    assert 0.85 <= med <= 0.95, (
        f"acceptance median trong DATA {med:.3f} lệch khỏi hành vi sim (~0.91)")


def test_non_simulated_drivers_still_generated(generated):
    """CAR/PREMIUM/RTO **không có sim** ⇒ vẫn phải dùng target profile. Nếu ai đó 'dọn sạch'
    nhánh target vì tưởng nó là bản vá, các tài xế này sẽ mất data."""
    _, uni, tables = generated
    non_sim = {d for d, p in uni.items() if not p["simulated"]}
    rows = [r for r in tables["driver_statistic_daily"] if r["driver_id"] in non_sim]
    assert rows, "tài xế CAR/PREMIUM/RTO bị mất khỏi driver_statistic_daily"
    assert all(0.5 <= r["acceptance_rate"] <= 1.0 for r in rows)


# ---------- Gate 7: bảo toàn vòng đời đơn ----------


def test_order_lifecycle_conservation(agg):
    """matched = dropoff + cancelled_after_accept + censored (không đơn nào bốc hơi)."""
    for i, a in enumerate(agg):
        matched, closed = a["lifecycle"]
        assert matched == closed, (
            f"seed {SEEDS[i]}: rò rỉ vòng đời — matched {matched} != "
            f"dropoff+cancel+censored {closed}")
