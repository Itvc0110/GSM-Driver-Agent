"""Solver S4 — CapacityAlloc. Platform-level: gán advice nhiều driver vào slot có
capacity → CHỐNG HERDING ("cả làng cùng đi sạc").

swap_window → slots (station, bucket), capacity = throughput. standby_zone →
slots (zone, bucket), kèm 5 safety_flags F2-04. scipy.linear_sum_assignment tối ưu
tổng cost; dư candidate → unassigned (bỏ advice, chống dồn). US-F2-04, pain #1.
Không can thiệp dispatch; không chỉ đơn cụ thể (§5).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

# 5 điều kiện an toàn F2-04 (action-space §Phạm vi advisor) cho standby_zone
STANDBY_SAFETY_FLAGS = ["capacity_aware", "warn_acceptance", "mock_label",
                        "no_income_promise", "no_specific_order"]
LARGE = 1e6


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def _assign_kind(candidates: list[dict], slot_caps: dict, src_label: str,
                 safety: list[str] | None):
    """Gán candidates vào slots (target,bucket) với capacity. linear_sum_assignment
    trên slot expand (mỗi slot lặp capacity lần). Trả (allocations, unassigned).
    Cost = priority_penalty (SOC cao → cost cao → xếp sau) + target-mismatch."""
    if not candidates:
        return [], []
    # expand slots: mỗi (target,bucket) → capacity vị trí
    slots = []  # (target, bucket)
    for (target, bucket), cap in sorted(slot_caps.items()):
        slots.extend([(target, bucket)] * int(cap))
    # sort candidate deterministic (priority SOC thấp trước, rồi driver_id)
    cand = sorted(candidates, key=lambda c: ((c.get("priority_soc")
                  if c.get("priority_soc") is not None else 999.0), c["driver_id"]))
    nC, nS = len(cand), len(slots)
    if nS == 0:
        return [], [{"driver_id": c["driver_id"], "advice_kind": c["advice_kind"],
                     "reason": "no_capacity"} for c in cand]

    # cost matrix nC × nS: candidate i muốn target c["target"]; slot j có target
    cost = np.full((nC, nS), LARGE)
    for i, c in enumerate(cand):
        soc = c.get("priority_soc")
        pen = (soc / 100.0) if soc is not None else 0.5  # SOC cao → penalty cao
        for j, (tgt, _bk) in enumerate(slots):
            cost[i, j] = pen if tgt == c["target"] else pen + 10.0  # ưu tiên đúng target

    # rectangular: linear_sum_assignment gán min(nC,nS) cặp tối ưu
    rows, cols = linear_sum_assignment(cost)
    allocations, assigned_idx = [], set()
    for r, cc in zip(rows, cols):
        if cost[r, cc] >= LARGE:
            continue  # slot không khả dụng
        c = cand[r]
        tgt, bk = slots[cc]
        assigned_idx.add(r)
        a = {"driver_id": c["driver_id"], "advice_kind": c["advice_kind"],
             "assigned_target": tgt, "assigned_bucket": bk,
             "staggered": tgt != c["target"]}
        if safety:
            a["safety_flags"] = list(safety)
        allocations.append(a)
    unassigned = [{"driver_id": cand[i]["driver_id"],
                   "advice_kind": cand[i]["advice_kind"], "reason": "capacity_full"}
                  for i in range(nC) if i not in assigned_idx]
    return allocations, unassigned


def _slot_caps(entries: list[dict], key: str) -> dict:
    return {(e[key], e["bucket"]): int(e["capacity"]) for e in entries}


def solve(ai: dict, params: dict | None = None) -> dict:
    cands = ai["candidates"]
    swap = [c for c in cands if c["advice_kind"] == "swap_window"]
    standby = [c for c in cands if c["advice_kind"] == "standby_zone"]
    station_caps = _slot_caps(ai.get("station_capacity", []), "station_id")
    zone_caps = _slot_caps(ai.get("zone_supply", []), "zone")

    swap_alloc, swap_un = _assign_kind(swap, station_caps, "station_registry", None)
    standby_alloc, standby_un = _assign_kind(standby, zone_caps, "zone_supply",
                                             STANDBY_SAFETY_FLAGS)

    allocations = swap_alloc + standby_alloc
    unassigned = swap_un + standby_un
    n_stag = sum(1 for a in allocations if a.get("staggered"))
    herding_avoided = n_stag + len(unassigned)

    total_cap = sum(station_caps.values()) + sum(zone_caps.values())
    numbers = [
        _num(len(cands), "candidates", "computed:candidates"),
        _num(total_cap, "slots", "station_registry+zone_supply"),
        _num(n_stag, "staggered", "computed"),
        _num(len(unassigned), "unassigned", "computed"),
    ]

    # sensitivity capacity −20%
    sensitivity = []
    for pct in (0.20,):
        sc = {k: max(1, int(round(v * (1 - pct)))) for k, v in station_caps.items()}
        zc = {k: max(1, int(round(v * (1 - pct)))) for k, v in zone_caps.items()}
        _, su = _assign_kind(swap, sc, "station_registry", None)
        _, zu = _assign_kind(standby, zc, "zone_supply", STANDBY_SAFETY_FLAGS)
        sensitivity.append({"param": f"capacity_-{int(pct * 100)}%",
                            "n_unassigned": len(su) + len(zu)})

    digest = (f"Điều phối {len(cands)} advice ({len(swap)} đổi pin, {len(standby)} khu vực) "
              f"lúc {ai['t_now'][11:16]}: gán {len(allocations)}, "
              f"chống dồn cung {herding_avoided} (stagger {n_stag}, bỏ {len(unassigned)}).")

    return {
        "schema_version": "1.0.0", "solver": "capacity_alloc",
        "problem_digest": digest,
        "inputs_used": [{"view_id": "allocation_input", "version": ai["view_version"],
                         "freshness": ai["t_now"]}],
        "solution": {"allocations": allocations, "unassigned": unassigned,
                     "herding_avoided": herding_avoided,
                     "n_assigned": len(allocations)},
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": 0.8,
        "caveats": ["capacity trạm/zone là DANH ĐỊNH (chưa telemetry thật) — ESTIMATED",
                    "chỉ điều phối timing/khu vực, không can thiệp phân đơn",
                    "standby_zone kèm cảnh báo an toàn — không hứa thu nhập, không chỉ đơn"],
        "infeasible_reason": None,
    }
