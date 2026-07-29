"""Router khu Mô phỏng — serialize KẾT QUẢ ENGINE cho web UI (contract journey/replay/ab_result).

Nguyên tắc một-nguồn-sự-thật (bài học SIM-1, giữ từ dashboard P4): endpoint CHỈ
serialize `RunResult`/`build_journey`/`run_pair` — không tính lại bất kỳ số nào.
run_once cache theo seed (LRU) vì mỗi run ~10-20s; determinism của engine đảm bảo
cùng seed → cùng JSON.
"""

from __future__ import annotations

import json
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Query

from gsm_sim.config import Config
from gsm_sim.journey import build_journey
from gsm_sim.parallel import (  # noqa: SLF001 — dùng ĐÚNG máy đo của parallel, không chép logic
    CHANNEL_LADDER, _cfg_with, _driver_metrics, _system_metrics, pick_target,
)
from gsm_sim.runner import run_once

from app.adapters.mockdata import REPO_ROOT

router = APIRouter()

SWEEP_FILE = REPO_ROOT / "research" / "experiments" / "sensitivity" / "dsim06_sweep.json"
AB_WARNING = ("1 seed = 1 ngày mô phỏng — kết quả đơn lẻ KHÔNG phải kết luận. "
              "Kết luận cần ≥30 seed + CI bootstrap (xem tab Độ nhạy).")


@lru_cache(maxsize=1)
def _cfg() -> Config:
    return Config.load(str(REPO_ROOT / "configs" / "pilot_dongda.yaml"))


@lru_cache(maxsize=6)
def _run(seed: int):
    return run_once(_cfg(), seed)


@lru_cache(maxsize=4)
def _run_advice_pair(seed: int):
    """(result_A, result_B, target_actor) — cùng transform config như run_pair (import
    `_cfg_with` từ parallel để KHÔNG chép logic — hai nguồn sự thật là lỗi đã trả giá)."""
    base = _cfg()
    ra = run_once(_cfg_with(base, enabled=False, actor_id=None, channels=None), seed)
    aid = pick_target(ra)
    rb = run_once(_cfg_with(base, enabled=True, actor_id=aid,
                            channels=CHANNEL_LADDER["all"]), seed)
    return ra, rb, aid


def _journey_payload(result, actor_id: int, seed: int) -> dict:
    j = build_journey(result, actor_id)
    events = []
    for e in result.events:
        if e.actor_id != actor_id:
            continue
        if e.kind.startswith("advice_") or e.kind == "standby_followed":
            # ĐA-04/W6: TRƯỚC ĐÂY nén thành {"kind":"advice","label":...} — mất
            # followed/channel/reason nên khu Mô phỏng không thể cho thấy NHỊP nói
            # (khi nào advisor im và vì sao). Nay giữ đủ để nhìn thấy cadence.
            d = e.detail or {}
            suppressed = e.kind == "advice_suppressed"
            events.append({
                "t_min": int(e.t_min),
                "kind": "advice_suppressed" if suppressed else "advice",
                "label": d.get("channel") or e.kind.removeprefix("advice_"),
                "channel": d.get("channel"),
                "followed": bool(d.get("followed")) if "followed" in d else None,
                "reason": d.get("reason"),
                "decision_id": d.get("decision_id"),
            })
        elif e.kind == "mission_completed":
            events.append({"t_min": int(e.t_min), "kind": "mission_completed",
                           "label": f"mission +{e.detail.get('reward_vnd', 0):,}đ".replace(",", ".")})
        elif e.kind == "day_end_settle" and int(e.detail.get("day_bonus", 0) or 0) > 0:
            events.append({"t_min": int(e.t_min), "kind": "day_bonus",
                           "label": f"thưởng ngày +{e.detail['day_bonus']:,}đ".replace(",", ".")})
        elif e.kind in ("newbie_guarantee_topup", "newbie_week1_bonus"):
            events.append({"t_min": int(e.t_min), "kind": "newbie_bonus", "label": "tân binh"})
    return {
        "seed": seed, "actor_id": actor_id, "archetype": j.archetype,
        "data_mode": "sim-engine", "is_mock": True,
        "segments": [{"t0_min": int(b.t0), "t1_min": int(b.t1), "kind": b.kind,
                      "from": None, "to": None} for b in j.timeline],
        "offers": [{"t_min": int(o.t_min), "accepted": o.decision == "accept",
                    "completed": (o.outcome == "completed") if o.outcome else None,
                    "reason": o.reason, "fare_vnd": o.gross_vnd,
                    "dist_km": o.pickup_km} for o in j.offers],
        "income_curve": [[float(t), int(v)] for t, v in j.income_curve],
        "events": events,
        "metrics": j.metrics,
    }


@router.get("/run")
def get_run(seed: int = Query(1000, ge=0)):
    """Tổng quan 1 ngày sim: danh sách tài xế cho picker + phạm vi thời gian."""
    r = _run(seed)
    return {
        "seed": seed, "data_mode": "sim-engine", "is_mock": True,
        "n_actors": len(r.actors),
        "actors": sorted(({"actor_id": a.actor_id, "archetype": a.archetype,
                           "trips": a.trips_done, "payout_vnd": a.payout_vnd,
                           "offers": a.orders_offered} for a in r.actors),
                         key=lambda x: -x["offers"]),
    }


@router.get("/journey")
def get_journey(seed: int = Query(1000, ge=0), actor_id: int = Query(...)):
    r = _run(seed)
    if not any(a.actor_id == actor_id for a in r.actors):
        raise HTTPException(404, f"actor {actor_id} không tồn tại ở seed {seed}")
    return _journey_payload(r, actor_id, seed)


@router.get("/replay")
def get_replay(seed: int = Query(1000, ge=0)):
    """Toàn đội xe: legs có toạ độ — client nội suy theo phút (contract replay v1.0)."""
    r = _run(seed)
    by_actor: dict[int, list[dict]] = {}
    tmin, tmax = 24 * 60, 0
    for s in r.segments:
        by_actor.setdefault(s["actor_id"], []).append({
            "t0_min": int(s["t0"]), "t1_min": int(s["t1"]), "kind": s["kind"],
            "from": [round(s["from_lat"], 6), round(s["from_lon"], 6)],
            "to": [round(s["to_lat"], 6), round(s["to_lon"], 6)],
        })
        tmin, tmax = min(tmin, int(s["t0"])), max(tmax, int(s["t1"]))
    arch = {a.actor_id: a.archetype for a in r.actors}
    return {
        "seed": seed, "data_mode": "sim-engine", "is_mock": True,
        "t_min_range": [tmin, tmax],
        "actors": [{"actor_id": aid, "archetype": arch.get(aid, "?"),
                    "legs": sorted(legs, key=lambda x: x["t0_min"])}
                   for aid, legs in sorted(by_actor.items())],
        "stations": [{"id": str(st.node_id), "lat": st.lat, "lng": st.lon,
                      "name": f"Tủ pin {st.node_id}"} for st in r.grid.stations],
    }


@router.get("/ab")
def get_ab(seed: int = Query(1000, ge=0)):
    """Thế giới song song 1 seed (CRN paired) — warning bắt buộc theo contract."""
    ra, rb, aid = _run_advice_pair(seed)
    ma, mb = _driver_metrics(ra, aid), _driver_metrics(rb, aid)
    sa, sb = _system_metrics(ra, aid), _system_metrics(rb, aid)
    ja, jb = build_journey(ra, aid), build_journey(rb, aid)
    d_served = sb["orders_completed"] - sa["orders_completed"]
    d_others = sb["others_payout_vnd"] - sa["others_payout_vnd"]
    n_advice = sum(1 for e in rb.events
                   if e.actor_id == aid and e.kind.startswith("advice_"))
    # AUDIT A1 STATS-2 (UPDATE-065): guardrail per-cell THẬT thay vì tổng chợ dán nhãn
    # "worst_cell". Hoàn thành = event `dropoff` (mang order_id) → map về PICKUP cell.
    from collections import Counter

    def _served_by_cell(r):
        pick = {o.order_id: o.pickup_cell for o in r.orders}
        return Counter(pick[e.detail["order_id"]] for e in r.events
                       if e.kind == "dropoff" and e.detail.get("order_id") in pick)

    served_a, served_b = _served_by_cell(ra), _served_by_cell(rb)
    cell_delta = {c: served_b.get(c, 0) - served_a.get(c, 0)
                  for c in set(served_a) | set(served_b)}
    worst_cell_delta = min(cell_delta.values()) if cell_delta else 0
    # ngưỡng cờ −3 đơn/cell là NGƯỠNG THÔ CHO DEMO 1-SEED (nhiễu Poisson 1 ngày);
    # kết luận hệ thống thật nằm ở sweep 30-seed (tab Độ nhạy) — warning_text đã nói rõ
    flagged = sorted(c for c, d in cell_delta.items() if d <= -3)
    return {
        "seed": seed, "data_mode": "sim-engine", "is_mock": True,
        "channel": "all (accept_lift + shift_extend + rest_window + shift_plan)",
        "warning_text": AB_WARNING,
        "delta": {"payout_vnd": mb["payout_vnd"] - ma["payout_vnd"],
                  "served_total": d_served, "advice_events": n_advice},
        "target_actors": [{"actor_id": aid, "archetype": next(
            a.archetype for a in ra.actors if a.actor_id == aid),
            "payout_a_vnd": ma["payout_vnd"], "payout_b_vnd": mb["payout_vnd"],
            "delta_vnd": mb["payout_vnd"] - ma["payout_vnd"]}],
        # AUDIT STATS-1 (UPDATE-069): 1 seed KHÔNG đủ để phán "ổn/xấu" — ok=null, chỉ đưa
        # số quan sát; ngưỡng -50k cũ là số bịa đã gỡ. Kết luận hệ thống: tab Độ nhạy (30 seed).
        "guardrail": {"worst_cell_delta_served": worst_cell_delta,
                      "flagged_cells": flagged,
                      "others_payout_delta_vnd": d_others,
                      "ok": None},
        "metrics_a": ma, "metrics_b": mb,
        "income_curves": {"a": [[float(t), int(v)] for t, v in ja.income_curve],
                          "b": [[float(t), int(v)] for t, v in jb.income_curve]},
    }


@router.get("/sweep")
def get_sweep():
    """Kết quả sweep D-SIM-06 PRECOMPUTED (30 seed/ô) — đọc file, không tính lại."""
    if not SWEEP_FILE.exists():
        raise HTTPException(404, "chưa có file sweep (scripts/run_sensitivity.py)")
    return json.loads(SWEEP_FILE.read_text(encoding="utf-8"))
