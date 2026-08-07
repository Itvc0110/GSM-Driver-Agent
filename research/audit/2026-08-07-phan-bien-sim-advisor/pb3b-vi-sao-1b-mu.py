"""pb3b — CƠ CHẾ: vì sao vế 1b (ĐA-08) KHÔNG bắn dù tercile idle bị hại -15.290đ SIG.

Giả thuyết phải KIỂM (không suy): phân hoạch **archetype** gần trực giao với trục mà tác hại
thật sự nằm trên (`idle_min` đo ở arm A) ⇒ trung bình theo archetype PHA LOÃNG.

Đo:
  1. Ma trận Δ payout theo (archetype × tercile idle_A) — gộp mọi seed, ghép cặp CRN.
  2. R² (tỷ lệ phương sai của Δ per-actor giải thích được) của phân hoạch archetype
     so với phân hoạch tercile-idle. Cùng số nhóm (7 vs 3 ⇒ archetype được ƯU ÁI).
  3. `harmed_share` theo từng archetype.

⚠ MẪU SỐ: mọi phép chia ở đây trên ĐÚNG tập actor có mặt ở CẢ HAI arm (CRN, 90/90).
Chạy: uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb3b-vi-sao-1b-mu.py [n]
"""
from __future__ import annotations

import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gsm_sim.config import Config  # noqa: E402
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_name("pb3b-vi-sao-1b-mu.json")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SEEDS = list(range(3300, 3300 + N))


def r2(rows: list[tuple[str, float]]) -> float:
    """Tỷ lệ phương sai của Δ giải thích được bởi nhãn nhóm (one-way ANOVA R²)."""
    vals = [v for _, v in rows]
    gm = statistics.mean(vals)
    sst = sum((v - gm) ** 2 for v in vals)
    grp: dict[str, list[float]] = {}
    for g, v in rows:
        grp.setdefault(g, []).append(v)
    ssb = sum(len(v) * (statistics.mean(v) - gm) ** 2 for v in grp.values())
    return ssb / sst if sst else 0.0


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    rows: list[dict] = []
    for k, seed in enumerate(SEEDS, 1):
        ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        rb = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                coverage="all"), seed)
        pa = {a.actor_id: float(a.payout_vnd) for a in ra.actors}
        pb = {a.actor_id: float(a.payout_vnd) for a in rb.actors}
        idle_a = {a.actor_id: float(a.idle_min) for a in ra.actors}
        arch = {a.actor_id: str(a.archetype) for a in ra.actors}
        ids = sorted(set(pa) & set(pb))
        xep = sorted(ids, key=lambda i: idle_a[i])
        t = len(xep) // 3
        ter = {i: ("t0" if r < t else "t1" if r < 2 * t else "t2")
               for r, i in enumerate(xep)}
        for i in ids:
            rows.append({"seed": seed, "id": i, "arch": arch[i], "ter": ter[i],
                         "d": pb[i] - pa[i]})
        if k % 10 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed", flush=True)

    ARCHS = sorted({r["arch"] for r in rows})
    TERS = ("t0", "t1", "t2")
    print(f"\n=== Δ payout TRUNG BÌNH theo (archetype × tercile idle_A) · {len(rows)} quan sát ===")
    print(f"{'arch':<6}{'t0 (ít rảnh)':>22}{'t1':>22}{'t2 (rảnh nhiều)':>22}"
          f"{'TB archetype':>16}{'n/seed':>8}")
    mat: dict = {}
    for a in ARCHS:
        sub = [r for r in rows if r["arch"] == a]
        line = f"{a:<6}"
        mat[a] = {}
        for tt in TERS:
            g = [r["d"] for r in sub if r["ter"] == tt]
            mat[a][tt] = {"n": len(g), "mean": statistics.mean(g) if g else None}
            line += (f"{statistics.mean(g):>14,.0f}đ (n={len(g):>4})" if g
                     else f"{'—':>22}")
        mat[a]["all"] = {"n": len(sub), "mean": statistics.mean([r['d'] for r in sub])}
        line += f"{statistics.mean([r['d'] for r in sub]):>15,.0f}đ{len(sub)/len(SEEDS):>8.1f}"
        print(line)
    line = f"{'TB ô':<6}"
    for tt in TERS:
        g = [r["d"] for r in rows if r["ter"] == tt]
        mat.setdefault("_tercile", {})[tt] = {"n": len(g), "mean": statistics.mean(g)}
        line += f"{statistics.mean(g):>14,.0f}đ (n={len(g):>4})"
    print(line)

    r2_arch = r2([(r["arch"], r["d"]) for r in rows])
    r2_ter = r2([(r["ter"], r["d"]) for r in rows])
    r2_both = r2([(f"{r['arch']}|{r['ter']}", r["d"]) for r in rows])
    print(f"\n=== R² — phân hoạch nào GIẢI THÍCH được Δ ===")
    print(f"  archetype (7 nhóm — vế 1b dùng cái này): R² = {r2_arch:.4f}")
    print(f"  tercile idle_A (3 nhóm):                 R² = {r2_ter:.4f}")
    print(f"  archetype × tercile (21 nhóm):           R² = {r2_both:.4f}")
    print(f"  ⇒ tercile/archetype = {r2_ter / r2_arch:.2f}× dù ÍT nhóm hơn (3 vs 7)")

    print("\n=== harmed_share (Δ < −1.000đ) theo archetype ===")
    hs = {}
    for a in ARCHS:
        sub = [r["d"] for r in rows if r["arch"] == a]
        hs[a] = len([v for v in sub if v < -1000.0]) / len(sub)
        print(f"  {a}: {hs[a]:>6.1%}  (n={len(sub)})")
    tong = len([r for r in rows if r["d"] < -1000.0]) / len(rows)
    print(f"  TOÀN ĐỘI: {tong:.1%}")

    OUT.write_text(json.dumps({"seeds": SEEDS, "matrix": mat, "r2_archetype": r2_arch,
                               "r2_tercile": r2_ter, "r2_both": r2_both,
                               "harmed_share_by_arch": hs, "harmed_share_all": tong},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
