"""Chấm `station_choice` theo ĐÚNG VĂN BẢN ĐA-08 (spec advisor-objective-model-v2 §5 + AMENDMENT
2026-07-28) trên artifact `research/audit/2026-08-06-e2/e01-station-100.json`.

    uv run python scripts/cham_da08_station_choice.py

Vì sao script này tồn tại (Cường 2026-08-06: *"đọc tài liệu quan trọng trước khi ra quyết định,
đừng dựa ký ức"*): bản chấm đầu trong đầu tôi đã HẠ CHUẨN thành "cơ chế + vô hại" — văn bản thật
đòi (1a) `payout_mean_all` > 0 **CI95 loại 0**. Chấm bằng máy trên artifact, không chấm bằng nhớ.

Tiêu chí (trích spec §5):
  1a. payout_mean_all > 0, CI95 loại 0, n≥30 (ở đây n=100)
  1b. không archetype nào Δ payout_mean_{P1..P7} ÂM-SIG (CI hoàn toàn < 0) — báo cáo đủ 7
  2.  served_rate không giảm (không âm-SIG)
  3.  expired_n không tăng SIG; wait_median_min không tăng SIG
  4.  gini_payout không tăng SIG
  5.  tầng 5 (D-M3-05): đọc quan sát một chiều — rest_min_total không giảm-SIG;
      work_span_p90 tăng < 10% (SPAN_P90_RISE_TOL)
  Veto 8/9(b): km-rỗng/đổi-pin ĐƯỢC PHÉP tốn nếu swap_wait không tăng SIG
      và total_payout_vnd tăng SIG cùng lúc — với kênh này swap_wait GIẢM là mục tiêu.
"""
from __future__ import annotations

import json
import pathlib
import sys

ART = pathlib.Path(__file__).resolve().parents[1] / \
    "research/audit/2026-08-06-e2/e01-station-100.json"


def row(sys_, k):
    r = sys_.get(k) or {}
    return r.get("delta_mean"), tuple(r.get("ci95") or (None, None)), r.get("significant")


def am_sig(ci):
    return ci[0] is not None and ci[1] is not None and ci[1] < 0


def duong_sig(ci):
    return ci[0] is not None and ci[0] > 0


def main() -> int:
    art = json.loads(ART.read_text(encoding="utf-8"))
    s = art["compare"]["system"]
    n = art["compare"]["n_seeds"]
    ok = {}

    d, ci, sig = row(s, "payout_mean_all")
    ok["1a payout_mean_all >0 CI loại 0"] = bool(sig and d and d > 0)
    print(f"1a  payout_mean_all: Δ={d:,.1f} CI={ci} sig={sig} n={n}"
          f"  -> {'PASS' if ok['1a payout_mean_all >0 CI loại 0'] else 'FAIL'}")

    harmed = []
    for i in range(1, 8):
        d2, ci2, _ = row(s, f"payout_mean_P{i}")
        if d2 is None:
            harmed.append(f"P{i}:THIẾU")
        elif am_sig(ci2):
            harmed.append(f"P{i}:{d2:,.0f}{ci2}")
        print(f"    P{i}: Δ={d2:,.1f} CI={ci2}")
    ok["1b no-harm P1..P7"] = not harmed
    print(f"1b  no-harm: {'PASS' if not harmed else 'FAIL ' + str(harmed)}")

    d, ci, _ = row(s, "served_rate")
    ok["2 served không giảm"] = not am_sig(ci)
    print(f"2   served_rate: Δ={d} CI={ci} -> {'PASS' if ok['2 served không giảm'] else 'FAIL'}")

    d, ci, _ = row(s, "expired_n")
    okx = not duong_sig(ci)
    d2, ci2, _ = row(s, "wait_median_min")
    okw = not duong_sig(ci2)
    ok["3 khách (expired/wait)"] = okx and okw
    print(f"3   expired: Δ={d} CI={ci} · wait_median: Δ={d2} CI={ci2}"
          f" -> {'PASS' if ok['3 khách (expired/wait)'] else 'FAIL'}")

    d, ci, _ = row(s, "gini_payout")
    ok["4 gini không tăng"] = not duong_sig(ci)
    print(f"4   gini: Δ={d} CI={ci} -> {'PASS' if ok['4 gini không tăng'] else 'FAIL'}")

    d, ci, _ = row(s, "rest_min_total")
    ok_rest = not am_sig(ci)
    a_span = (s.get("work_span_p90") or {}).get("mean_a") or 0
    d2, ci2, _ = row(s, "work_span_p90")
    ok_span = (d2 or 0) / a_span < 0.10 if a_span else True
    ok["5 tầng 5 (rest/span<10%)"] = ok_rest and ok_span
    print(f"5   rest_total: Δ={d} CI={ci} · span_p90: Δ={d2} ({(d2 or 0)/a_span:.1%} nền)"
          f" -> {'PASS' if ok['5 tầng 5 (rest/span<10%)'] else 'FAIL'}")

    d, ci, _ = row(s, "swap_wait_mean")
    print(f"ref swap_wait: Δ={d} CI={ci} (mục tiêu kênh — kỳ vọng ÂM SIG)")

    print("\n" + "=" * 60)
    fails = [k for k, v in ok.items() if not v]
    if not fails:
        print("VERDICT: PASS TOÀN BỘ ĐA-08 ⇒ đủ điều kiện bật mặc định"
              " (uỷ quyền Cường 2026-08-06 'cái nào tốt thì mặc định bật').")
    else:
        print(f"VERDICT: FAIL {fails} ⇒ KHÔNG bật mặc định theo văn bản hiện hành."
              " Muốn bật vẫn được nhưng đó là NỚI CHUẨN — quyết định của Cường, không của agent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
