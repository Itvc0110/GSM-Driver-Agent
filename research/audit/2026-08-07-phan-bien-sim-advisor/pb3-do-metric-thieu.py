"""pb3 — ĐO: bộ metric hiện có có BẮT được kịch bản "phân phối lại" không?

Câu hỏi phải trả lời BẰNG SỐ (không suy từ code):
  (a) ĐA-08 1a/1b có PASS trên chính arm đang ship (positioning, coverage=all) trong khi
      tercile `idle_min` đo ở arm A cho -15.290đ / +26.106đ?  ⇒ nếu PASS thì đó là LỖ HỔNG.
      Cơ chế nghi ngờ: archetype KHÔNG trùng tercile idle ⇒ trung bình theo archetype PHA LOÃNG.
      ⇒ đo luôn CROSSTAB archetype × tercile để chứng minh/bác cơ chế pha loãng.
  (b) `gini_payout`, `supply_cell_hhi`, `station_hhi` (tầng Công bằng / Tập trung) có bắn không?
  (d) `payout_p10/median/p90` (ĐÃ TÍNH trong `fairness_metrics`, KHÔNG được `_system_metrics`
      chuyển tiếp) có SIG không? — nếu có thì đó là metric TÍNH RỒI VỨT ĐI đúng lúc cần nhất.
  (c) ứng viên metric mới: `harmed_share`, `delta_p10`, `churn_ratio` — đo thử luôn.

Ghép cặp CRN cùng seed, bootstrap trên HIỆU THEO SEED (đúng cách `parallel.compare` làm).
Chạy: uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb3-do-metric-thieu.py [n_seed]
"""
from __future__ import annotations

import json
import pathlib
import random
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gsm_sim.config import Config  # noqa: E402
from gsm_sim.metrics import summarize  # noqa: E402
from gsm_sim.parallel import _cfg_with, _cohort_metrics  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402
from gsm_sim.sim_metrics import (concentration_metrics, customer_impact,  # noqa: E402
                                 fairness_metrics)

OUT = pathlib.Path(__file__).with_name("pb3-do-metric-thieu.json")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SEEDS = list(range(3300, 3300 + N))
B = 2000


def _boot(xs: list[float], rng: random.Random) -> tuple[float, float]:
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(B))
    return (m[int(0.025 * B)], m[int(0.975 * B)])


def _pct(vals: list[float], q: float) -> float:
    s = sorted(vals)
    k = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
    return float(s[k])


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    per_seed: list[dict] = []
    crosstab: dict[str, dict[str, int]] = {}
    for k, seed in enumerate(SEEDS, 1):
        ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        rb = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                coverage="all"), seed)
        pa = {a.actor_id: float(a.payout_vnd) for a in ra.actors}
        pb = {a.actor_id: float(a.payout_vnd) for a in rb.actors}
        idle_a = {a.actor_id: float(a.idle_min) for a in ra.actors}
        arch = {a.actor_id: str(a.archetype) for a in ra.actors}
        ids = sorted(set(pa) & set(pb))
        d = {i: pb[i] - pa[i] for i in ids}

        row: dict = {"seed": seed, "n": len(ids)}
        # --- ĐA-08 1a/1b: ĐÚNG khoá `_cohort_metrics` sinh ra ---
        ca, cb = _cohort_metrics(ra), _cohort_metrics(rb)
        for key in sorted(set(ca) & set(cb)):
            if key.startswith("payout_mean_") and not key.startswith("payout_mean_F_"):
                row[f"D::{key}"] = float(cb[key]) - float(ca[key])
        # --- tầng Công bằng / Tập trung / Khách hàng (khoá THẬT của guardrail) ---
        fa, fb = fairness_metrics(ra), fairness_metrics(rb)
        cca, ccb = concentration_metrics(ra), concentration_metrics(rb)
        cia, cib = customer_impact(ra), customer_impact(rb)
        sa, sb = summarize(ra), summarize(rb)
        for src_a, src_b, keys in (
                (fa, fb, ("gini_payout", "total_payout_vnd",
                          "payout_p10", "payout_median", "payout_p90")),
                (cca, ccb, ("station_hhi", "supply_cell_hhi", "n_supply_cells")),
                (cia, cib, ("expired_n", "wait_median_min", "wait_p90_min")),
                (sa, sb, ("served_rate",))):
            for key in keys:
                row[f"D::{key}"] = float(src_b[key]) - float(src_a[key])
        # --- ứng viên metric MỚI (đều tính từ dữ liệu SẴN CÓ: payout per actor) ---
        neg = [v for v in d.values() if v < 0]
        pos = [v for v in d.values() if v > 0]
        row["harmed_share"] = len([v for v in d.values() if v < -1000.0]) / len(ids)
        row["delta_p10"] = _pct(list(d.values()), 0.10)
        row["delta_p90"] = _pct(list(d.values()), 0.90)
        row["loss_total"] = sum(neg)
        row["gain_total"] = sum(pos)
        net = sum(d.values())
        row["churn_ratio"] = (sum(pos) - sum(neg)) / abs(net) if net else float("nan")

        # --- tercile idle_min ĐO Ở ARM A (tái lập c9b) + CROSSTAB archetype ---
        xep = sorted(ids, key=lambda i: idle_a[i])
        t = len(xep) // 3
        terciles = [xep[:t], xep[t:2 * t], xep[2 * t:]]
        for j, grp in enumerate(terciles):
            row[f"delta_t{j}"] = statistics.mean([d[i] for i in grp])
            for i in grp:
                crosstab.setdefault(arch[i], {"t0": 0, "t1": 0, "t2": 0})[f"t{j}"] += 1
        per_seed.append(row)
        if k % 5 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed", flush=True)

    rng = random.Random(20260807)
    keys = [k for k in per_seed[0] if k not in ("seed", "n")]
    res: dict = {}
    print(f"\n=== n={len(SEEDS)} seed CRN · arm B = positioning mặc định, coverage=all ===")
    print(f"{'khoá':<28}{'Δ trung bình':>16}  {'CI95':>30}  sig")
    for key in keys:
        xs = [r[key] for r in per_seed]
        m, (lo, hi) = statistics.mean(xs), _boot(xs, rng)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns"
        res[key] = {"delta_mean": m, "ci95": [lo, hi], "sig": sig}
        print(f"{key:<28}{m:>16,.4f}  [{lo:>13,.4f};{hi:>13,.4f}]  {sig}")

    # --- phán quyết ĐA-08 ---
    arch_keys = [k for k in res if k.startswith("D::payout_mean_") and k != "D::payout_mean_all"]
    hai_sig = [k for k in arch_keys if res[k]["sig"] == "SIG" and res[k]["delta_mean"] < 0]
    v1a = res["D::payout_mean_all"]["sig"] == "SIG" and res["D::payout_mean_all"]["delta_mean"] > 0
    verdict = {
        "1a_pass": v1a,
        "1b_pass": not hai_sig,
        "archetype_bi_hai_SIG": hai_sig,
        "he_thong_served_rate_giam_SIG": (res["D::served_rate"]["sig"] == "SIG"
                                          and res["D::served_rate"]["delta_mean"] < 0),
        "khach_expired_tang_SIG": (res["D::expired_n"]["sig"] == "SIG"
                                   and res["D::expired_n"]["delta_mean"] > 0),
        "cong_bang_gini_tang_SIG": (res["D::gini_payout"]["sig"] == "SIG"
                                    and res["D::gini_payout"]["delta_mean"] > 0),
        "tap_trung_hhi_o_tang_SIG": (res["D::supply_cell_hhi"]["sig"] == "SIG"
                                     and res["D::supply_cell_hhi"]["delta_mean"] > 0),
        "tap_trung_hhi_tram_tang_SIG": (res["D::station_hhi"]["sig"] == "SIG"
                                        and res["D::station_hhi"]["delta_mean"] > 0),
    }
    verdict["DA08_TONG"] = ("PASS" if (verdict["1a_pass"] and verdict["1b_pass"]
                                       and not verdict["he_thong_served_rate_giam_SIG"]
                                       and not verdict["khach_expired_tang_SIG"]
                                       and not verdict["cong_bang_gini_tang_SIG"]
                                       and not verdict["tap_trung_hhi_o_tang_SIG"]
                                       and not verdict["tap_trung_hhi_tram_tang_SIG"])
                           else "FAIL")
    print("\n=== PHÁN QUYẾT ĐA-08 (tính theo đúng 5 tầng §5) ===")
    for k, v in verdict.items():
        print(f"  {k:<32} {v}")

    print("\n=== CROSSTAB archetype × tercile idle_min(A) — gộp mọi seed ===")
    for a in sorted(crosstab):
        r = crosstab[a]
        tot = r["t0"] + r["t1"] + r["t2"]
        print(f"  {a:<6} t0={r['t0']:>5} ({r['t0']/tot:>5.1%})  t1={r['t1']:>5} "
              f"({r['t1']/tot:>5.1%})  t2={r['t2']:>5} ({r['t2']/tot:>5.1%})   tổng={tot}")

    OUT.write_text(json.dumps({"seeds": SEEDS, "per_seed": per_seed, "agg": res,
                               "verdict_da08": verdict, "crosstab_arch_tercile": crosstab},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
