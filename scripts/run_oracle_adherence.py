"""E2 — arm ORACLE-ADHERENCE: tách "giá trị NỘI DUNG" khỏi "mức CHỊU NGHE".

    uv run python scripts/run_oracle_adherence.py --seeds 30            # thăm dò
    uv run python scripts/run_oracle_adherence.py --seeds 100 --json …  # chốt (chuẩn T-041 1b')

Ba arm mỗi seed (coverage="all" — hết pha loãng 1/k của r07-F2):
  A        = advice OFF (đối chứng, chạy trong run_pair)
  B_real   = kênh ship (positioning wait_only) + adherence THỰC TẾ (config/DEFAULT)
  B_oracle = y hệt B_real nhưng `advice.adherence_by_archetype = 1.0` toàn bộ

🔒 Bẫy ORACLE-03 (UPDATE-151 r04, verify ĐỨNG): override đặt trên **cfg GỐC truyền vào
run_pair/nominal_adherence** — override chỉ ở arm B thì cổng |z|>4 so đo-được-1.0 với
null-thực-tế ⇒ TREO oan hàng loạt (mẫu D-R20). Coin là sha256 thuần ⇒ p=1.0 không trôi RNG.

Đọc kết quả:
  · Δ(B_real − A) và Δ(B_oracle − A): bootstrap ghép cặp theo seed như mọi phép đo.
  · TRẦN nội dung = Δ_oracle; PHẦN MẤT VÌ KHÔNG NGHE = Δ_oracle − Δ_real (hiệu-của-hiệu,
    ghép cặp theo seed — so biến-thể-vs-biến-thể ⇒ significant cần ≥100 seed, T-041 1b').
  · ⚠ D-SIM-K3: Δ nào cũng lẫn random-stream divergence; oracle là cực đại phân kỳ hành vi.
Mọi số MOCK.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import statistics as st
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                                    # noqa: E402
from gsm_sim.parallel import (MIN_SEEDS_FOR_VARIANT_COMPARISON,      # noqa: E402
                              aggregate_adherence, bootstrap_ci, compare,
                              nominal_adherence, run_pair)

CH_SHIP = {"shift_plan": False, "accept_lift": False, "shift_extend": False,
           "rest_window": False, "positioning_overrides": "wait_only"}
ORACLE = {f"P{i}": 1.0 for i in range(1, 8)}
KEYS = ("payout_mean_all", "net_mean_all", "trips_mean_all", "gini_payout", "served_rate")


def cfg_oracle(base: Config) -> Config:
    """Override trên cfg GỐC (bẫy ORACLE-03) — mẫu y hệt scripts/run_sensitivity.py."""
    data = copy.deepcopy(base.data)
    data.setdefault("advice", {})["adherence_by_archetype"] = dict(ORACLE)
    return Config(data, base.root_dir)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("--config", default=str(ROOT / "configs/pilot_dongda.yaml"))
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    base = Config.load(args.config)
    orc = cfg_oracle(base)
    assert nominal_adherence(orc) and all(v == 1.0 for v in nominal_adherence(orc).values()), \
        "ORACLE-03: nominal của cfg oracle phải thấy 1.0 — override đặt sai chỗ"
    seeds = list(range(args.seed0, args.seed0 + args.seeds))

    t0 = time.time()
    pairs_real, pairs_orc = [], []
    for i, s in enumerate(seeds, 1):
        pairs_real.append(run_pair(base, s, channels=CH_SHIP, coverage="all"))
        pairs_orc.append(run_pair(orc, s, channels=CH_SHIP, coverage="all"))
        el = time.time() - t0
        print(f"   seed {s} ({i}/{len(seeds)})  {el/60:.1f}' troi", flush=True)

    ms = MIN_SEEDS_FOR_VARIANT_COMPARISON
    cmp_real = compare(pairs_real)                       # A/B chuẩn: min 30
    cmp_orc = compare(pairs_orc)
    adh_real = aggregate_adherence(pairs_real, nominal=nominal_adherence(base))
    adh_orc = aggregate_adherence(pairs_orc, nominal=nominal_adherence(orc))

    print(f"\n=== ORACLE vs REALISTIC · {len(seeds)} seed · coverage=all · kênh ship ===")
    print(f"  adherence gate: real={adh_real['verdict']}  oracle={adh_orc['verdict']}")
    print(f"  {'metric':ekhoa>18}" if False else f"  {'metric':>18}{'Δ real':>12}{'Δ oracle':>12}"
          f"{'mất vì không nghe':>20}{'CI95 (hiệu-của-hiệu)':>26}")
    dod_out = {}
    for k in KEYS:
        r, o = cmp_real["system"].get(k), cmp_orc["system"].get(k)
        if not r or not o:
            continue
        # hiệu-của-hiệu GHÉP CẶP theo seed: (B_orc−A_orc) − (B_real−A_real) từng seed
        dod = [(float(po.system_b[k] or 0) - float(po.system_a[k] or 0))
               - (float(pr.system_b[k] or 0) - float(pr.system_a[k] or 0))
               for pr, po in zip(pairs_real, pairs_orc)]
        lo, hi = bootstrap_ci(dod)
        dod_out[k] = {"delta_mean": round(st.mean(dod), 4), "ci95": (round(lo, 4), round(hi, 4)),
                      "significant": bool(len(dod) >= ms and (lo > 0 or hi < 0))}
        print(f"  {k:>18}{r['delta_mean']:>12,.1f}{o['delta_mean']:>12,.1f}"
              f"{st.mean(dod):>+20,.1f}{f'[{lo:,.1f}, {hi:,.1f}]':>26}")
    if len(seeds) < ms:
        print(f"\n  ⚠ n={len(seeds)} < {ms} (chuẩn biến-thể-vs-biến-thể T-041 1b') — "
              f"hiệu-của-hiệu CHỈ ĐỌC THĂM DÒ, cấm trích làm kết luận (bài học n-nhỏ ×3).")

    if args.json:
        art = {"what": "E2 oracle-adherence vs realistic — kênh ship, coverage=all",
               "mock": True, "seeds": seeds, "n": len(seeds), "min_seeds_variant": ms,
               "channels": CH_SHIP, "oracle": ORACLE,
               "compare_real": cmp_real, "compare_oracle": cmp_orc,
               "adherence_real": adh_real, "adherence_oracle": adh_orc,
               "diff_of_diff": dod_out,
               "canh_bao_doc": [
                   "Δ lẫn random-stream divergence (D-SIM-K3) — oracle là cực đại phân kỳ.",
                   "diff_of_diff significant đòi n ≥ 100 (T-041 1b').",
                   "KHÔNG quy chỉ tiêu sức khoẻ ra VND; gini/served chỉ đọc hai chiều kinh tế."]}
        p = pathlib.Path(args.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  artifact → {p}")
    print(f"  tổng {(time.time()-t0)/60:.1f}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
