"""`D-M3-04` — A/B NHIỀU NGÀY cho kênh `rest_window`, theo prereg ĐÃ KHOÁ.

    uv run python scripts/run_dm304.py --smoke          # 5 seed, KIỂM ĐƯỜNG ỐNG
    uv run python scripts/run_dm304.py --json <path>    # 100 seed, phép đo thật (~4h)

Prereg: `specs/simulation/d-m3-04-multiday-prereg-locked.json`
  · khoá 2026-08-01 (thiết kế, metric, kỳ vọng, 4 STOP, cấm vĩnh viễn)
  · `luat_quyet_dinh` khoá 2026-08-03 (Cường xác nhận bản dịch)
  · `dinh_chinh_TRUOC_KHI_DO_2026_08_05` (3 điểm, ghi TRƯỚC khi chạy seed nào)

## Vì sao script riêng thay vì mở rộng `run_parallel.py`

`run_parallel.py` đi đường `run_ladder`, mà `run_ladder` gọi `compare(pairs)` **không truyền
`min_seeds`** (`parallel.py:378`) ⇒ dùng hằng 30. Prereg khoá `min_seeds_for_sig = 100`. Dùng lại
đường đó là âm thầm chấm bằng ngưỡng sai.

## 🔒 Ba điều script này KHÔNG được làm (trích thẳng prereg)

- Chấm *"có ý nghĩa"* bằng bất kỳ tiêu chí nào khác `luat_quyet_dinh`.
- Nới `REST_TOTAL_DROP_TOL` / `SPAN_P90_RISE_TOL` / `rest_defer_max_min`.
- **Quy bất kỳ chỉ tiêu sức khoẻ nào ra VND.** Tầng 5 ở cột RIÊNG.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                       # noqa: E402
from gsm_sim.multiday import run_multiday               # noqa: E402
from gsm_sim.parallel import (MIN_SEEDS_FOR_VARIANT_COMPARISON, _cfg_with,  # noqa: E402
                              aggregate_adherence, aggregate_health_guardrail,
                              compare, nominal_adherence, run_pair_multiday)
from gsm_sim.sim_metrics import fingerprint_actors      # noqa: E402

# ---- thiết kế arm: khai TƯỜNG MINH cả hai, KHÔNG dùng CHANNEL_LADDER["rest_window"] ----
# Prereg `thiet_ke.KHONG_dung`: ladder bật kèm `shift_plan: True`, mà shift_plan đã bị ĐA-07 TẮT
# vì CÓ HẠI ⇒ đo trên đó là đo hai can thiệp trộn nhau.
_BASE = {"shift_plan": False, "accept_lift": False, "shift_extend": False}
CHANNELS_A = {**_BASE, "rest_window": False, "positioning_overrides": "wait_only"}
CHANNELS_B = {**_BASE, "rest_window": True, "positioning_overrides": "wait_only"}

DAYS = 3
METRIC_DAYS = [1, 2]          # BỎ ngày 0 — chưa có DriverMemory ⇒ planned_rest_hour vẫn None
KENH = "rest_window"
METRIC_CHINH = "payout_mean_all"   # prereg `dinh_chinh...3_doc_ro_metric_driver_payout`


def stop_d_fingerprint(cfg: Config, seed: int) -> dict:
    """STOP-D — multiday có tất định không? Chạy arm A HAI LẦN, so ngày 0 **và** ngày 1.

    Prereg nói ngày 0, brief nói ngày 1 ⇒ đính chính 2026-08-05: kiểm CẢ HAI. Ngày 0 chỉ kiểm tất
    định của thế giới; ngày 1 kiểm tất định SAU khi `DriverMemory` đã truyền qua — đó mới là chỗ
    multiday có thể mất tất định.
    """
    c = _cfg_with(cfg, enabled=True, actor_id=None, channels=CHANNELS_A, coverage="all")
    r1, r2 = run_multiday(c, seed, days=DAYS), run_multiday(c, seed, days=DAYS)
    out = {}
    for d in (0, 1):
        f1, f2 = fingerprint_actors(r1.days[d]), fingerprint_actors(r2.days[d])
        out[f"day{d}"] = {"run1": f1, "run2": f2, "identical": f1 == f2}
    out["pass"] = all(v["identical"] for v in out.values() if isinstance(v, dict))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--seed0", type=int, default=7000)
    ap.add_argument("--days", type=int, default=DAYS)
    ap.add_argument("--smoke", action="store_true",
                    help="5 seed, CHỈ kiểm đường ống — KHÔNG được đọc như kết luận")
    ap.add_argument("--config", default=str(ROOT / "configs/pilot_dongda.yaml"))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    n = 5 if args.smoke else args.seeds
    seeds = list(range(args.seed0, args.seed0 + n))
    cfg = Config.load(args.config)

    if args.smoke:
        print("⚠ SMOKE — kiểm ĐƯỜNG ỐNG. Prereg khoá min_seeds_for_sig=100; "
              "KHÔNG đọc kết quả này như kết luận GIỮ/REVERT.\n")

    t0 = time.time()
    print(f"STOP-D: fingerprint tất định (seed {seeds[0]}, chạy arm A hai lần)…")
    stop_d = stop_d_fingerprint(cfg, seeds[0])
    for d in ("day0", "day1"):
        v = stop_d[d]
        print(f"   {d}: {v['run1']} vs {v['run2']}  {'✅' if v['identical'] else '🔴 KHÁC'}")
    if not stop_d["pass"]:
        print("\n🔴 STOP-D BẮN — multiday không tất định ⇒ mọi Δ vô nghĩa. Dừng.")
        return 2

    pairs = []
    for i, s in enumerate(seeds, 1):
        pairs.append(run_pair_multiday(cfg, s, days=args.days, channels_a=CHANNELS_A,
                                       channels_b=CHANNELS_B, metric_days=METRIC_DAYS))
        el = time.time() - t0
        print(f"   seed {s}  ({i}/{n})  {el/60:.1f}′ trôi, ~{el/i*(n-i)/60:.0f}′ còn lại")

    # STOP-A (cả hai arm) + STOP-B (DET-01 thu hẹp về KÊNH ĐANG ĐO)
    adh = aggregate_adherence(pairs, nominal=nominal_adherence(cfg),
                              control_clean_channels=(KENH,), gate_both_arms=True)
    # STOP-C — tầng 5 trên `touched_actors` (đã áp trong `run_pair_multiday`)
    health = aggregate_health_guardrail(pairs)
    cmp_ = compare(pairs, min_seeds=MIN_SEEDS_FOR_VARIANT_COMPARISON)

    row = (cmp_.get("system") or {}).get(METRIC_CHINH) or {}
    delta, ci = row.get("delta_mean"), row.get("ci95")
    sig = bool(row.get("significant"))
    stops = {
        "STOP-A/B (adherence + đối chứng)": adh["verdict"],
        "STOP-C (tầng 5)": health["verdict"],
        "STOP-D (tất định)": "OK" if stop_d["pass"] else "TREO",
    }
    treo = [k for k, v in stops.items() if not str(v).startswith("OK")]

    print("\n" + "=" * 70)
    for k, v in stops.items():
        print(f"  {k:38} {v}")
    # Một cổng BẮN mà không in LÝ DO là cổng nửa vời: người đọc chỉ thấy "TREO" rồi đi nới
    # tolerance vì không biết cái gì hỏng. Prereg cấm nới — nên phải cho thấy cái cần sửa.
    for ten, fl in (("STOP-A/B", adh.get("flags_per_seed")),
                    ("STOP-C", health.get("flags"))):
        for f in (fl or [])[:12]:
            print(f"     ⤷ [{ten}] {f}")
    if health.get("flags"):
        a_m, b_m = health.get("a_mean") or {}, health.get("b_mean") or {}
        print("\n  tầng 5 — cột RIÊNG, KHÔNG quy ra VND (prereg cam_vinh_vien):")
        for k in ("rest_min_total", "work_span_p90", "drive_min_p90", "n_actors_scope",
                  "veto_fired_n"):
            if k in a_m or k in b_m:
                print(f"     {k:18} A={a_m.get(k)}   B={b_m.get(k)}")
    print(f"\n  metric CHÍNH ({METRIC_CHINH}, trung bình ngày {METRIC_DAYS}):")
    print(f"     Δ = {delta}   CI95 = {ci}   significant = {sig}   n = {n}"
          f" (min_seeds = {MIN_SEEDS_FOR_VARIANT_COMPARISON})")

    # ⚠ `compare()` tính `n_insufficient` theo hằng 30 chứ KHÔNG theo `min_seeds` truyền vào
    # (`parallel.py:309`) ⇒ đừng tin cờ đó; đọc `n` và `min_seeds` cạnh nhau như trên.
    if n < MIN_SEEDS_FOR_VARIANT_COMPARISON:
        verdict = "KHÔNG CHẤM — n < min_seeds (prereg khoá 100)"
    elif treo:
        verdict = f"TREO — {treo}"
    elif sig and (delta or 0) > 0:
        verdict = "GIỮ — Δ dương SIG, tầng 5 không suy giảm, 0 STOP"
    else:
        verdict = "REVERT — Δ ≤ 0 hoặc ns (nhánh ĐƯỢC DỰ ĐOÁN TRƯỚC: world β=0)"
    print(f"\n  VERDICT: {verdict}")
    if verdict.startswith("GIỮ") and (delta or 0) > 1000:
        print("  🔴 Δ > +1.000đ là NGOÀI dự đoán đã khoá [−1.500, +500] ⇒ PHẢI điều tra trước khi "
              "trích. Ứng viên đầu: hiệu ứng THỜI ĐIỂM (C2′), KHÔNG phải hiệu ứng sức khoẻ.")

    art = {
        "what": "D-M3-04 multiday A/B — kênh rest_window",
        "mock": True,
        "prereg": "specs/simulation/d-m3-04-multiday-prereg-locked.json",
        "smoke": bool(args.smoke),
        "config": args.config, "days": args.days, "metric_days": METRIC_DAYS,
        "metric_chinh": METRIC_CHINH,
        "channels_a": CHANNELS_A, "channels_b": CHANNELS_B,
        "control_clean_channels": [KENH], "gate_both_arms": True,
        "seeds": seeds, "n": n, "min_seeds": MIN_SEEDS_FOR_VARIANT_COMPARISON,
        "stop_a_b": adh, "stop_c": health, "stop_d": stop_d,
        "compare": cmp_, "verdict": verdict,
        "canh_bao_doc": [
            "Tầng 5 ở cột RIÊNG — CẤM quy ra VND (prereg cam_vinh_vien).",
            "n_insufficient của compare() tính theo hằng 30, KHÔNG theo min_seeds — đọc n/min_seeds.",
            "Khi REVERT: được nói 'trong world không có hậu quả mệt, kênh nghỉ là chi phí thuần'; "
            "KHÔNG được nói 'gợi ý nghỉ vô giá trị ngoài đời'.",
            "KHÔNG trích trần 71%/≤29% cho chế độ multiday (prereg vung_mu_khai_truoc).",
        ],
    }
    if args.json:
        p = pathlib.Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n  artifact → {p}")
    print(f"  tổng {(time.time()-t0)/60:.1f}′")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
