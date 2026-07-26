"""SIM-4 — THẾ GIỚI SONG SONG: đo advice giúp được bao nhiêu, có khoảng tin cậy.

Cường (`DIRECTIVES-2026-07-24.md` §5.6): *"các thế giới song song: khi **tự làm** vs khi **làm
theo chỉ dẫn**"*, đo trên **đúng tài xế đó**.

## Vì sao dùng HIỆU THEO CẶP (paired), không so hai nhóm độc lập

World A và World B chạy **cùng seed** ⇒ **cùng danh sách đơn, cùng thời tiết, cùng tắc đường**
(CRN — common random numbers). Chênh lệch còn lại vì thế phần lớn là **do advice**, không phải
do hôm nay nhiều khách hơn. So độc lập sẽ bị phương sai ngày-tốt/ngày-xấu nhấn chìm hiệu ứng.

Vì vậy thống kê phải làm trên **d_i = B_i − A_i từng seed**, rồi lấy trung bình + CI bootstrap.

## Nguyên tắc báo cáo

**CI chứa 0 là một KẾT QUẢ, không phải thất bại.** Không vặn tham số cho Δ đẹp lên — SIM-1 đã
ghi rõ bài học đó (spec §7.1). Nếu advice không giúp, phải nói là không giúp, rồi đi tìm vì sao.
"""

from __future__ import annotations

import copy
import statistics as st
from dataclasses import dataclass

import numpy as np

from .config import Config
from .journey import build_journey
from .metrics import summarize
from .runner import run_once

# Bộ kênh dựng sẵn cho đo THANG BẬC — biết giá trị đến từ kênh nào (attribution).
CHANNEL_LADDER = {
    "s2_only": {"shift_plan": True, "accept_lift": False, "shift_extend": False},
    "rest_window": {"shift_plan": True, "accept_lift": False, "shift_extend": False,
                    "rest_window": True},
    "accept_lift": {"shift_plan": True, "accept_lift": True, "shift_extend": False},
    "all": {"shift_plan": True, "accept_lift": True, "shift_extend": True, "rest_window": True},
    "none": {"shift_plan": False, "accept_lift": False, "shift_extend": False,
             "rest_window": False},
}


@dataclass
class PairResult:
    seed: int
    actor_id: int
    a: dict          # metric của tài xế đích ở World A
    b: dict          # ... ở World B
    system_a: dict   # metric hệ thống (guardrail)
    system_b: dict


def _cfg_with(cfg: Config, *, enabled: bool, actor_id: int | None,
              channels: dict | None) -> Config:
    """Bản SAO SÂU của config với cờ advice đã đặt.

    Phải deep-copy: nếu sửa tại chỗ thì nhánh A và B dùng chung một dict ⇒ chạy A xong đã bị
    nhánh B ghi đè, mọi so sánh thành vô nghĩa.
    """
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    adv = c.data.setdefault("advice", {})
    adv["enabled"] = enabled
    adv["coverage"] = "single"
    adv["single_actor_id"] = actor_id
    if channels is not None:
        adv["channels"] = dict(channels)
    return c


def pick_target(result, archetype: str = "P4") -> int:
    """Tài xế đích mặc định = người thuộc `archetype` được chào đơn nhiều nhất.

    P4 (tân binh) là baseline Cường yêu cầu. LƯU Ý: đây chưa phải hồ sơ tân binh THẬT —
    `D-SIM-02` (thưởng riêng tài xế mới) vẫn đang chờ Cường chốt số policy.
    """
    cands = [a for a in result.actors if a.archetype == archetype] or list(result.actors)
    return max(cands, key=lambda a: a.orders_offered).actor_id


def _driver_metrics(result, actor_id: int) -> dict:
    m = build_journey(result, actor_id).metrics
    return {k: m[k] for k in (
        "payout_vnd", "trip_payout_vnd", "day_bonus_vnd", "trips_completed",
        "acceptance_rate", "completion_rate", "utilization", "idle_min", "online_min",
        "offers", "declined", "points",
    )}


def _system_metrics(result, exclude_actor: int) -> dict:
    """Guardrail: advice KHÔNG được cải thiện 1 người bằng cách làm xấu hệ thống."""
    s = summarize(result)
    others = [a for a in result.actors if a.actor_id != exclude_actor]
    swap_waits = [e.detail.get("wait_min", 0.0) for e in result.events
                  if e.kind == "swap_done" and "wait_min" in e.detail]
    return {
        "served_rate": s["served_rate"],
        "orders_completed": s["orders_completed"],
        "others_payout_vnd": sum(a.payout_vnd for a in others),
        "others_trips": sum(a.trips_done for a in others),
        "swap_wait_mean": round(st.mean(swap_waits), 3) if swap_waits else 0.0,
    }


def run_pair(cfg: Config, seed: int, channels: dict | None = None,
             actor_id: int | None = None, archetype: str = "P4") -> PairResult:
    """Chạy World A (tự làm) và World B (theo chỉ dẫn) trên **cùng seed**."""
    ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
    aid = actor_id if actor_id is not None else pick_target(ra, archetype)
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=aid, channels=channels), seed)
    return PairResult(seed=seed, actor_id=aid,
                      a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                      system_a=_system_metrics(ra, aid), system_b=_system_metrics(rb, aid))


def assert_crn(cfg: Config, seed: int, actor_id: int) -> bool:
    """CRN phải đúng: cùng seed ⇒ **cùng danh sách đơn** ở hai nhánh.

    Nếu ngoại sinh lệch thì mọi Δ là rác — kiểm trước khi tin bất kỳ con số nào.
    """
    ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=actor_id,
                            channels=CHANNEL_LADDER["all"]), seed)
    ka = [(o.order_id, round(o.t_min, 6), o.pickup_cell, o.gross_vnd) for o in ra.orders]
    kb = [(o.order_id, round(o.t_min, 6), o.pickup_cell, o.gross_vnd) for o in rb.orders]
    return ka == kb


def bootstrap_ci(diffs: list[float], n_boot: int = 5000, alpha: float = 0.05,
                 seed: int = 12345) -> tuple[float, float]:
    """CI phần trăm bootstrap cho TRUNG BÌNH hiệu theo cặp.

    Bootstrap thay vì t-test vì phân phối Δ (payout/ngày) lệch và có đuôi — không nên giả
    định chuẩn khi mẫu chỉ vài chục seed.
    """
    if not diffs:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    arr = np.asarray(diffs, dtype=float)
    means = arr[rng.integers(0, len(arr), size=(n_boot, len(arr)))].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


# AUDIT STATS-5 (UPDATE-069): bootstrap CI degenerate với n nhỏ (n=1 → CI rộng 0, MỌI Δ≠0
# thành "significant"; n=2 → đồng xu 50%). Chuẩn CLAUDE §4b: kết luận distribution cần ≥30 seed.
MIN_SEEDS_FOR_SIGNIFICANCE = 30


def _sig(lo: float, hi: float, n: int) -> bool:
    return bool(n >= MIN_SEEDS_FOR_SIGNIFICANCE and (lo > 0 or hi < 0))


def compare(pairs: list[PairResult]) -> dict:
    """Tổng hợp: hiệu theo cặp cho từng metric + CI bootstrap + guardrail hệ thống.

    `significant` chỉ được bật khi n ≥ MIN_SEEDS_FOR_SIGNIFICANCE — dưới đó flag luôn
    False và `n_insufficient`=True để consumer không đọc nhầm nhiễu thành hiệu ứng."""
    n = len(pairs)
    out: dict = {"n_seeds": n, "n_insufficient": n < MIN_SEEDS_FOR_SIGNIFICANCE,
                 "driver": {}, "system": {}}
    if not pairs:
        return out
    for key in pairs[0].a:
        diffs = [float(p.b[key] or 0) - float(p.a[key] or 0) for p in pairs]
        lo, hi = bootstrap_ci(diffs)
        out["driver"][key] = {
            "mean_a": round(st.mean(float(p.a[key] or 0) for p in pairs), 2),
            "mean_b": round(st.mean(float(p.b[key] or 0) for p in pairs), 2),
            "delta_mean": round(st.mean(diffs), 2),
            "ci95": (round(lo, 2), round(hi, 2)),
            "significant": _sig(lo, hi, n),
            "n_positive": sum(1 for d in diffs if d > 0),
        }
    for key in pairs[0].system_a:
        diffs = [float(p.system_b[key] or 0) - float(p.system_a[key] or 0) for p in pairs]
        lo, hi = bootstrap_ci(diffs)
        out["system"][key] = {"delta_mean": round(st.mean(diffs), 4),
                              "ci95": (round(lo, 4), round(hi, 4)),
                              "significant": _sig(lo, hi, n)}
    return out


def run_ladder(cfg: Config, seeds: list[int], archetype: str = "P4",
               steps: tuple[str, ...] = ("s2_only", "accept_lift", "all")) -> dict:
    """Đo THANG BẬC: từng bậc kênh → biết giá trị đến từ đâu (attribution).

    Cùng tài xế đích cho mọi bậc để so sánh công bằng.

    Hiệu năng: World A **chạy MỘT LẦN cho mỗi seed** rồi dùng lại cho mọi bậc — A không phụ
    thuộc cấu hình kênh. Ngây thơ chạy lại A ở từng bậc sẽ tốn gấp đôi mà kết quả y hệt.
    """
    cfg_a = _cfg_with(cfg, enabled=False, actor_id=None, channels=None)
    ra0 = run_once(cfg_a, seeds[0])
    aid = pick_target(ra0, archetype)

    cache_a = {seeds[0]: ra0}
    out: dict = {}
    for name in steps:
        pairs = []
        for s in seeds:
            ra = cache_a.get(s) or run_once(cfg_a, s)
            cache_a[s] = ra
            rb = run_once(_cfg_with(cfg, enabled=True, actor_id=aid,
                                    channels=CHANNEL_LADDER[name]), s)
            pairs.append(PairResult(
                seed=s, actor_id=aid,
                a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                system_a=_system_metrics(ra, aid), system_b=_system_metrics(rb, aid)))
        out[name] = compare(pairs)
    return out
