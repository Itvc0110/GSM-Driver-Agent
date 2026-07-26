"""Adapter advisor cho UI: dựng `bonus_gap_input` từ bảng mock → gọi solver S1 THẬT.

Nguyên tắc (CLAUDE §5): backend KHÔNG tự tính lời khuyên — mọi số đến từ
`gsm_core.solvers.bonus_feasibility.solve()` + `PolicyBundle`; adapter chỉ dựng
input từ data và dịch SolverReport → contract `ui/contracts/advice.json`.
Trạng thái IM LẶNG là kết quả hợp lệ (đã đạt mốc cao nhất / hết quỹ giờ).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import polars as pl

from gsm_core.policy import PolicyBundle as CorePolicy
from gsm_core.solvers import bonus_feasibility

from .mockdata import REPO_ROOT, _table, _stat_row

# Ca khai báo mặc định khi tài xế chưa khai (ASSUMPTION — UI cho sửa qua query param)
DEFAULT_SHIFT_END_MIN = 22 * 60


@lru_cache(maxsize=1)
def policy() -> CorePolicy:
    """Policy DUY NHẤT một nguồn: sim config → to_core_record — cùng đường với mockgen
    (adapter_sim.py L0 policy_bundle), nên UI/advisor/data không bao giờ lệch số policy."""
    from gsm_sim.config import Config
    from gsm_sim.policy import PolicyBundle as SimPolicy
    cfg = Config.load(str(REPO_ROOT / "configs" / "pilot_dongda.yaml"))
    rec = SimPolicy.from_config(cfg).to_core_record()
    rec.setdefault("version", str(cfg.get("meta.policy_bundle_version")))
    return CorePolicy.from_record(rec)


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _trips_of(driver_id: str) -> pl.DataFrame:
    return _table("trips").filter(pl.col("driver_id") == driver_id)


def _points_until(trips: pl.DataFrame, date: str, now_min: int, pol: CorePolicy) -> int:
    day = trips.filter(pl.col("request_time").str.starts_with(date))
    pts = 0
    for iso in day["request_time"].to_list():
        t_min = _hour(iso) * 60 + int(iso[14:16])
        if t_min <= now_min:
            pts += pol.trip_points(_hour(iso))
    return pts


def _hist_rate(trips: pl.DataFrame, driver_id: str, date: str, pol: CorePolicy) -> dict:
    """median điểm/giờ-online theo bucket từ ≤7 ngày trước `date` (≥3 ngày mới tin)."""
    onl = _table("driver_online_hours_sap_id").filter(pl.col("driver_id") == driver_id)
    oh_by_date = {r["local_date"]: float(r["online_time"]) for r in onl.iter_rows(named=True)}
    days = sorted({iso[:10] for iso in trips["request_time"].to_list() if iso[:10] < date})[-7:]
    per_bucket: dict[str, list[float]] = {"peak": [], "offpeak": []}
    for d in days:
        oh = oh_by_date.get(d, 0.0)
        if oh <= 0:
            continue
        bp = {"peak": 0, "offpeak": 0}
        for iso in trips.filter(pl.col("request_time").str.starts_with(d))["request_time"].to_list():
            b = "peak" if pol.is_peak(_hour(iso)) else "offpeak"
            bp[b] += pol.trip_points(_hour(iso))
        for b, p in bp.items():
            if p > 0:
                per_bucket[b].append(p / oh)
    out = {}
    for b, rates in per_bucket.items():
        if len(rates) >= 3:
            out[b] = round(sorted(rates)[len(rates) // 2], 3)
    return out


def build_gi(driver_id: str, date: str, now_min: int,
             shift_end_min: int = DEFAULT_SHIFT_END_MIN) -> dict:
    pol = policy()
    trips = _trips_of(driver_id)
    stat = _stat_row(driver_id, date) or {}
    points_now = _points_until(trips, date, now_min, pol)
    return {
        "schema_version": "1.0.0", "driver_id": driver_id,
        "t_now": f"{date}T{now_min // 60:02d}:{now_min % 60:02d}:00+07:00",
        "points_now": points_now,
        "next_tiers": [[pt, vnd] for pt, vnd in pol.day_bonus_tiers if pt > points_now],
        "historical_points_per_hour": _hist_rate(trips, driver_id, date, pol),
        "hours_budget_remaining": round(max(0.0, (shift_end_min - now_min) / 60.0), 3),
        # tỷ lệ NGÀY từ bảng statistic (granularity ngày — caveat ghi trong advice)
        "acceptance_rate": round(float(stat.get("acceptance_rate", 1.0) or 1.0), 4),
        "completion_rate": round(float(stat.get("fulfillment_rate", 1.0) or 1.0), 4),
        "policy_bundle_version": pol.version, "view_version": "1.0.0", "source": "MOCK",
    }


def _num_source(raw: str) -> str:
    if raw.startswith("policy_v"):
        return "MOCK"          # policy bundle mock có nguồn research (sim-policy-bundle-v0)
    if raw.startswith("historical"):
        return "MOCK"          # lịch sử cá nhân từ data mock
    if raw.startswith("dp:"):
        return "ASSUMPTION"    # ước lượng lý thuyết khi thiếu lịch sử
    return "SOLVER"


def advice(driver_id: str, date: str, now_min: int,
           shift_end_min: int = DEFAULT_SHIFT_END_MIN) -> dict:
    if not driver_id.startswith(("d-", "r-")):
        # policy S1 hiện là policy BIKE — không áp bừa cho đội car/premium (không bịa policy)
        return {"scenario_id": f"mock-realdata:{date}", "seed": 0,
                "data_mode": "mock-realdata", "is_mock": True, "generated_at_min": now_min,
                "silent": {"is_silent": True, "reason_code": "no_active_channel",
                           "message": "Trợ lý mới phủ đội bike (chính sách điểm/thưởng bike). "
                                      "Đội car/premium sẽ có khi đủ policy — không đoán số."},
                "items": []}
    gi = build_gi(driver_id, date, now_min, shift_end_min)
    report = bonus_feasibility.solve(gi, policy())
    sol = report["solution"]

    base = {
        "scenario_id": f"mock-realdata:{date}", "seed": 0,
        "data_mode": "mock-realdata", "is_mock": True,
        "generated_at_min": now_min,
    }

    if sol.get("already_maxed"):
        return {**base,
                "silent": {"is_silent": True, "reason_code": "already_on_track",
                           "message": "Bạn đã đạt mốc thưởng ngày cao nhất — không có gì cần chỉnh. Giữ nhịp hiện tại."},
                "items": []}

    numbers = [{"name": n, "value": v, "unit": u, "source": s} for n, v, u, s in [
        ("diem_con_thieu", sol["gap_points"], "điểm", "MOCK"),
        ("thuong_moc_ke", sol["tier_vnd"], "vnd", "MOCK"),
    ]]
    # AUDIT S1: hours_needed = None nghĩa là "không đạt được trong hôm nay" — không ép thành số
    if sol.get("hours_needed") is not None:
        numbers.append({"name": "gio_can_them", "value": sol["hours_needed"], "unit": "giờ",
                        "source": _num_source(report["numbers"][2]["source"])})
    if sol.get("trips_needed") is not None:
        numbers.append({"name": "cuoc_can_them", "value": sol["trips_needed"],
                        "unit": "cuốc", "source": "SOLVER"})
    caveat = " · ".join(report.get("caveats", []))

    if sol["feasible"]:
        item = {
            "advice_id": f"s1-{driver_id}-{date}-{now_min}",
            "solver": "S1", "kind": "bonus_gap",
            "title": f"Còn với được mốc thưởng {sol['tier_vnd']:,}đ hôm nay".replace(",", "."),
            "message": (f"Bạn thiếu {sol['gap_points']} điểm để chạm mốc kế "
                        f"(~{sol['hours_needed']:.1f} giờ chạy nữa, khoảng "
                        f"{sol['trips_needed']} cuốc). Quỹ giờ còn lại đủ."),
            "confidence": report["confidence"],
            "reason_code": "feasible_gap",
            "numbers": numbers, "caveat": caveat,
        }
        return {**base, "silent": {"is_silent": False}, "items": [item]}

    # infeasible — nói thật lý do, không hứa hẹn
    constraints = sol.get("constraints", {})
    if not constraints.get("enough_hours", True):
        reason_code = "insufficient_budget_hours"
    elif not constraints.get("ok_acceptance", True):
        reason_code = "acceptance_below_threshold"
    else:
        reason_code = "completion_below_threshold"
    item = {
        "advice_id": f"s1-{driver_id}-{date}-{now_min}",
        "solver": "S1", "kind": "info",
        "title": "Mốc thưởng kế khó khả thi hôm nay",
        "message": (report.get("infeasible_reason") or "Không đủ điều kiện đạt mốc kế.")
                   + " Đừng cố quá — giữ tỷ lệ hoàn thành tốt cho ngày mai.",
        "confidence": report["confidence"],
        "reason_code": reason_code,
        "numbers": numbers, "caveat": caveat,
    }
    return {**base, "silent": {"is_silent": False}, "items": [item]}
