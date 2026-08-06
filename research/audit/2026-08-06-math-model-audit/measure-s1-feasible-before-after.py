"""`D-ADV-04` — đo TRƯỚC/SAU trên ĐƯỜNG SẢN PHẨM: sửa mẫu số đổi verdict `feasible` thế nào.

    uv run python research/audit/2026-08-06-math-model-audit/measure-s1-feasible-before-after.py

## Đo cái gì

Với mỗi (tài xế × ngày × giờ hỏi), dựng `bonus_gap_input` bằng **ba** cách tính
`historical_points_per_hour` rồi cho **cùng một** solver S1 phán:

| arm | mẫu số | survivorship |
| --- | --- | --- |
| `A_cu` | giờ online **TOÀN NGÀY** (quy ước SAI cũ) | ngày 0-điểm bị **LOẠI** (`if p > 0`) |
| `B_maunso` | giờ online **TRONG BUCKET** | ngày 0-điểm bị **LOẠI** (tách riêng vế mẫu số) |
| `C_ca_hai` | giờ online **TRONG BUCKET** | ngày 0-điểm đóng **0.0** (= code sau fix) |

Tách hai vế vì chúng **thiên lệch NGƯỢC CHIỀU** (mẫu số ⇒ bi quan; survivorship ⇒ lạc quan) nên nếu
chỉ đo `A → C` thì không biết mỗi vế đóng góp bao nhiêu, và một lỗi thứ ba có thể ẩn trong phần bù trừ.

## Kỳ vọng TIỀN-ĐĂNG-KÝ (chốt trước khi chạy — nếu lệch thì ĐIỀU TRA, không giải thích sau)

1. `A → B` phải **ĐƠN ĐIỆU**: 0 ca đi từ feasible sang infeasible. Đây là hệ quả TOÁN HỌC của
   `giờ_ngày ≥ giờ_bucket` ⇒ rate mới ≥ rate cũ. **Có ca đi ngược ⇒ code sai**, không phải "dữ liệu lạ".
2. `B → C` chỉ được đi **một chiều** (feasible → infeasible), vì thêm mẫu `0.0` chỉ có thể hạ median.
3. `hist` rỗng **không tăng**: fix không được làm mất prior cá nhân của ai.
4. Verdict **không** được đảo ở > 5% ca khi đổi `MIN_BUCKET_HOURS` (0,25 / 0,5 / 1,0) — nếu đảo thì
   kết luận là hiện vật của một hằng số ASSUMPTION, phải hiệu chỉnh bằng dữ liệu chứ không chốt bằng nó.

**Mọi số là MOCK** (bộ `data/mock/realdata-v1`), không phải dữ liệu GSM thật.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "ui" / "backend"))

import polars as pl                                                   # noqa: E402
from app.adapters.advisor import (_hour, _min_of_day, _points_until,   # noqa: E402
                                  _rate_asof, _table, _trips_of, policy,
                                  DEFAULT_SHIFT_END_MIN)
from gsm_core.rates import (bucket_of_hour, bucket_online_hours_estimated,   # noqa: E402
                            bucket_rate_samples, median_bucket_rates)
from gsm_core.solvers.bonus_feasibility import solve                   # noqa: E402

ASK_HOURS = [10, 14, 17, 20]
N_DAYS = 5


def _hist_cu(trips: pl.DataFrame, oh_by_date: dict, date: str, pol) -> dict:
    """Quy ước CŨ nguyên văn: điểm-của-bucket ÷ giờ online TOÀN NGÀY, bỏ ngày 0 điểm."""
    days = sorted({i[:10] for i in trips["request_time"].to_list() if i[:10] < date})[-7:]
    per: dict[str, list[float]] = {"peak": [], "offpeak": []}
    for d in days:
        oh = oh_by_date.get(d, 0.0)
        if oh <= 0:
            continue
        bp = {"peak": 0, "offpeak": 0}
        for iso in trips.filter(pl.col("request_time").str.starts_with(d))["request_time"].to_list():
            bp["peak" if pol.is_peak(_hour(iso)) else "offpeak"] += pol.trip_points(_hour(iso))
        for b, p in bp.items():
            if p > 0:                      # ← survivorship của bản cũ
                per[b].append(p / oh)
    return {b: round(sorted(v)[len(v) // 2], 3) for b, v in per.items() if len(v) >= 3}


def _hist_moi(trips: pl.DataFrame, oh_by_date: dict, date: str, pol, *,
              min_bucket_hours: float, dong_0: bool) -> dict:
    days = sorted({i[:10] for i in trips["request_time"].to_list() if i[:10] < date})[-7:]
    per: dict[str, list[float]] = {}
    for d in days:
        oh = oh_by_date.get(d, 0.0)
        if oh <= 0:
            continue
        day = trips.filter(pl.col("request_time").str.starts_with(d))
        req = day["request_time"].to_list()
        if not req:
            continue
        comp = day["complete_time"].to_list() if "complete_time" in day.columns else req
        span = (min(_min_of_day(i) for i in req), max(_min_of_day(i) for i in comp))
        bh, _ = bucket_online_hours_estimated(pol, oh, span)
        if not bh:
            continue
        bp: dict[str, float] = {}
        for iso in req:
            b = bucket_of_hour(pol, _hour(iso))
            if b is not None:
                bp[b] = bp.get(b, 0.0) + pol.trip_points(_hour(iso))
        for b, rate in bucket_rate_samples(bp, bh, min_hours=min_bucket_hours).items():
            if not dong_0 and rate == 0.0:
                continue               # mô phỏng survivorship cũ trên mẫu số MỚI
            per.setdefault(b, []).append(rate)
    return median_bucket_rates(per)


def _gi(driver_id: str, date: str, now_min: int, points_now: int, hist: dict, pol) -> dict:
    return {
        "schema_version": "1.1.0", "driver_id": driver_id,
        "t_now": f"{date}T{now_min // 60:02d}:{now_min % 60:02d}:00+07:00",
        "points_now": points_now,
        "next_tiers": [[pt, v] for pt, v in pol.day_bonus_tiers if pt > points_now],
        "historical_points_per_hour": hist, "historical_rate_method": "estimated_span_scaled",
        "hours_budget_remaining": round(max(0.0, (DEFAULT_SHIFT_END_MIN - now_min) / 60.0), 3),
        "acceptance_rate": _rate_asof(driver_id, date, "acceptance"),
        "completion_rate": _rate_asof(driver_id, date, "completion"),
        "policy_bundle_version": pol.version, "view_version": "1.0.0", "source": "MOCK",
    }


def main() -> int:
    pol = policy()
    trips_all = _table("trips")
    drivers = sorted(set(trips_all["driver_id"].to_list()))
    dates = sorted({i[:10] for i in trips_all["request_time"].to_list()})[-N_DAYS:]
    print(f"MOCK · {len(drivers)} tài xế × {len(dates)} ngày × {len(ASK_HOURS)} giờ hỏi "
          f"= {len(drivers) * len(dates) * len(ASK_HOURS)} ca\n")

    onl_all = _table("driver_online_hours_sap_id")
    cnt: Counter = Counter()
    flips: dict[str, list] = {"A_to_B_nguoc": [], "B_to_C_nguoc": []}
    mbh_verdict: dict[float, list[bool]] = {0.25: [], 0.5: [], 1.0: []}

    for drv in drivers:
        trips = _trips_of(drv)
        if trips.is_empty():
            continue
        onl = onl_all.filter(pl.col("driver_id") == drv)
        oh_by_date = {r["local_date"]: float(r["online_time"]) for r in onl.iter_rows(named=True)}
        for date in dates:
            h_cu = _hist_cu(trips, oh_by_date, date, pol)
            h_b = _hist_moi(trips, oh_by_date, date, pol, min_bucket_hours=0.5, dong_0=False)
            h_c = _hist_moi(trips, oh_by_date, date, pol, min_bucket_hours=0.5, dong_0=True)
            h_mbh = {m: _hist_moi(trips, oh_by_date, date, pol, min_bucket_hours=m, dong_0=True)
                     for m in mbh_verdict}
            for hh in ASK_HOURS:
                now = hh * 60
                pts = _points_until(trips, date, now, pol)
                verdicts = {}
                for name, hist in (("A", h_cu), ("B", h_b), ("C", h_c)):
                    r = solve(_gi(drv, date, now, pts, hist, pol), pol)
                    verdicts[name] = bool(r["solution"]["feasible"])
                    cnt[f"feasible_{name}"] += verdicts[name]
                cnt["n"] += 1
                cnt["hist_rong_A"] += (not h_cu)
                cnt["hist_rong_C"] += (not h_c)
                if verdicts["A"] and not verdicts["B"]:
                    cnt["A_to_B_NGUOC"] += 1
                    flips["A_to_B_nguoc"].append((drv, date, hh, h_cu, h_b))
                if not verdicts["A"] and verdicts["B"]:
                    cnt["A_to_B_thuan"] += 1
                if verdicts["B"] and not verdicts["C"]:
                    cnt["B_to_C_thuan"] += 1
                if not verdicts["B"] and verdicts["C"]:
                    cnt["B_to_C_NGUOC"] += 1
                    flips["B_to_C_nguoc"].append((drv, date, hh, h_b, h_c))
                for m, hist in h_mbh.items():
                    mbh_verdict[m].append(
                        bool(solve(_gi(drv, date, now, pts, hist, pol), pol)["solution"]["feasible"]))

    n = max(1, cnt["n"])
    print("=== VERDICT feasible ===")
    for name, mo_ta in (("A", "cũ (mẫu số TOÀN NGÀY + bỏ ngày 0 điểm)"),
                        ("B", "sửa MẪU SỐ (vẫn bỏ ngày 0 điểm)"),
                        ("C", "sửa CẢ HAI vế = code sau fix")):
        c = cnt[f"feasible_{name}"]
        print(f"  {name}: {c:5d}/{n} = {c / n:6.1%}   {mo_ta}")
    print("\n=== LẬT VERDICT ===")
    print(f"  A→B thuận (infeasible→feasible): {cnt['A_to_B_thuan']}")
    print(f"  A→B NGƯỢC  (feasible→infeasible): {cnt['A_to_B_NGUOC']}"
          f"   {'✅ ĐƠN ĐIỆU như kỳ vọng' if not cnt['A_to_B_NGUOC'] else '🔴 PHẢN KỲ VỌNG #1 — ĐIỀU TRA'}")
    print(f"  B→C thuận (feasible→infeasible, do đóng 0.0): {cnt['B_to_C_thuan']}")
    print(f"  B→C NGƯỢC: {cnt['B_to_C_NGUOC']}"
          f"   {'✅ một chiều như kỳ vọng' if not cnt['B_to_C_NGUOC'] else '🔴 PHẢN KỲ VỌNG #2'}")
    if cnt['A_to_B_thuan']:
        print(f"  tỷ lệ kéo lại của vế survivorship: "
              f"{cnt['B_to_C_thuan'] / cnt['A_to_B_thuan']:.1%} của chiều thuận")
    print("\n=== PRIOR CÁ NHÂN (hist rỗng) ===")
    print(f"  A: {cnt['hist_rong_A']}/{n} = {cnt['hist_rong_A'] / n:.1%}"
          f"   ·   C: {cnt['hist_rong_C']}/{n} = {cnt['hist_rong_C'] / n:.1%}"
          f"   {'✅ không mất prior' if cnt['hist_rong_C'] <= cnt['hist_rong_A'] else '⚠ MẤT prior'}")
    print("\n=== FALSIFIER: kết luận có phụ thuộc hằng số MIN_BUCKET_HOURS không? ===")
    base = mbh_verdict[0.5]
    for m, vs in sorted(mbh_verdict.items()):
        khac = sum(1 for a, b in zip(vs, base) if a != b)
        print(f"  MIN_BUCKET_HOURS={m}: feasible {sum(vs)}/{len(vs)} = {sum(vs) / max(1, len(vs)):6.1%}"
              f"   · lệch so với 0.5: {khac}/{len(vs)} = {khac / max(1, len(vs)):.1%}"
              f"   {'🔴 > 5% ⇒ hiện vật hằng số' if khac / max(1, len(vs)) > 0.05 else ''}")
    for k, v in flips.items():
        if v:
            print(f"\n⚠ {k} — 10 ca đầu để đọc tay:")
            for row in v[:10]:
                print("   ", row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
