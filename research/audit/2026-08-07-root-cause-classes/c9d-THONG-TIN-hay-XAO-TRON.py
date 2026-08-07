"""Cycle 9d — PHÂN XỬ: giá trị của kênh vị trí là **THÔNG TIN** hay chỉ là **XÁO TRỘN**?

## Câu hỏi còn treo sau 9a/9b/9c

`9b` (chia tercile theo `idle_min` **ở arm A**, tiền-can-thiệp) cho:
rảnh-ít **−15.290đ SIG** · rảnh-nhiều **+26.106đ SIG** · toàn đội **+3.219đ SIG**.

`9c` (placebo cờ) đã loại **hiện vật của việc bật cờ**: arm NULL bit-identical **30/30 seed**.

**Nhưng chưa loại được** giả thuyết *"can thiệp như một BỘ XÁO TRỘN"*: điều kiện hoá trên
`idle_min` của A rồi đo `B − A` **vốn** sinh hồi-quy-về-trung-bình khi B là một lần rút khác —
**kể cả khi lời khuyên không mang thông tin nào**. Không loại được thì biên độ tercile vô nghĩa.

## Placebo CÓ NHIỄU — giữ nguyên LIỀU, xoá đúng THÔNG TIN

Arm `SHUF`: chặn `capacity_alloc.solve` và **hoán vị `assigned_target` giữa chính các allocation
đó**. Giữ nguyên **mọi** thứ khác:

| giữ nguyên | bị phá |
| --- | --- |
| ai được gán · bao nhiêu người · lúc nào | **ghép cặp người ↔ ô** do solver tính |
| tập ô đích và **số suất mỗi ô** (đa tập không đổi ⇒ trần vẫn đúng) | |
| coin adherence, cadence, mọi dòng RNG của world | |
| bất biến zone-veto (đích vẫn ∈ zones, ∉ fired) | |

⇒ `SHUF` là **cùng một cú xáo trộn với cùng cường độ**, chỉ khác: nó **không biết đi đâu**.

**Phán xử:**
  · `SHUF` cho **cùng mẫu hình tercile** ⇒ `9b` là **hồi quy về trung bình / xáo trộn** ⇒ biên độ
    tercile **KHÔNG được trích**, và giá trị kênh chỉ còn là Δ toàn đội.
  · `SHUF` **phẳng** trong khi `B` có mẫu hình ⇒ **thông tin của solver là THẬT** ⇒ `9b` đứng.
  · `SHUF` có một phần ⇒ phần **THẬT = B − SHUF**.

⚠ RNG của phép hoán vị là **riêng**, keyed theo `(seed, số lần gọi)` — không đụng dòng RNG nào
của world (nếu đụng thì chính placebo lại thành một can thiệp khác, đúng bẫy `DET-01`).

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/c9d-THONG-TIN-hay-XAO-TRON.py
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

from gsm_core.solvers import capacity_alloc as CA  # noqa: E402
from gsm_sim.config import Config  # noqa: E402
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = list(range(3300, 3330))          # CÙNG cửa sổ với 9a/9b/9c
B = 2000
NHOM = ("rảnh ÍT nhất", "giữa", "rảnh NHIỀU nhất")

# ⚠ `world.py:383` import capacity_alloc **CỤC BỘ TRONG HÀM**, nên vá namespace của
# world là VÔ TÁC DỤNG (đã thử, AttributeError). Phải vá chính thuộc tính `solve`
# của module solver — `capacity_alloc.solve` được tra CỨU LÚC GỌI.
_THAT_SOLVE = CA.solve                    # hàm thật, giữ lại để khôi phục


class _Hoanvi:
    """Bọc `capacity_alloc`: giữ nguyên lời giải, chỉ HOÁN VỊ đích giữa các allocation."""

    def __init__(self, seed: int):
        self.rng = random.Random(900000 + seed)   # RNG RIÊNG, không đụng dòng nào của world
        self.n = 0

    def __call__(self, ai):
        rep = _THAT_SOLVE(ai)
        allocs = (rep.get("solution") or {}).get("allocations") or []
        if len(allocs) > 1:
            dich = [a["assigned_target"] for a in allocs]
            self.rng.shuffle(dich)           # đa tập KHÔNG đổi ⇒ trần/zone-veto vẫn đúng
            for a, t in zip(allocs, dich):
                a["assigned_target"] = t
            self.n += 1
        return rep


def _boot(xs, rng):
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(B))
    return (m[int(0.025 * B)], m[int(0.975 * B)])


def _tercile(pa, px, idle_a):
    ids = sorted(set(pa) & set(px) & set(idle_a))
    xep = sorted(ids, key=lambda i: idle_a[i])
    t = len(xep) // 3
    return [statistics.mean([px[i] - pa[i] for i in g]) if g else 0.0
            for g in (xep[:t], xep[t:2 * t], xep[2 * t:])], \
        (statistics.mean([px[i] - pa[i] for i in ids]) if ids else 0.0)


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    rows = []
    for k, seed in enumerate(SEEDS, 1):
        ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        cfg_b = _cfg_with(cfg, enabled=True, actor_id=None, channels=None, coverage="all")
        rb = run_once(cfg_b, seed)
        hv = _Hoanvi(seed)
        CA.solve = hv                             # ← vá thuộc tính `solve` của module solver
        try:
            rs = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                    coverage="all"), seed)
        finally:
            CA.solve = _THAT_SOLVE
        pa = {a.actor_id: float(a.payout_vnd) for a in ra.actors}
        pb = {a.actor_id: float(a.payout_vnd) for a in rb.actors}
        ps = {a.actor_id: float(a.payout_vnd) for a in rs.actors}
        idle_a = {a.actor_id: float(a.idle_min) for a in ra.actors}
        tb, mb = _tercile(pa, pb, idle_a)
        ts, ms = _tercile(pa, ps, idle_a)
        rows.append({"seed": seed, "n_hoan_vi": hv.n,
                     "B_tercile": tb, "B_all": mb, "S_tercile": ts, "S_all": ms})
        if k % 5 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed")

    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS, "per_seed": rows}
    print(f"\n=== THÔNG TIN hay XÁO TRỘN · n={len(SEEDS)} seed · "
          f"{statistics.mean([r['n_hoan_vi'] for r in rows]):.0f} lượt hoán vị/seed ===")
    print(f"{'nhóm':<20}{'B (solver)':>13}{'SHUF (mù)':>13}{'THẬT = B−SHUF':>16}  {'CI 95% của hiệu':>26}")
    for j, ten in enumerate(NHOM):
        b = [r["B_tercile"][j] for r in rows]
        s = [r["S_tercile"][j] for r in rows]
        d = [x - y for x, y in zip(b, s)]
        lo, hi = _boot(d, rng)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns "
        out[f"tercile_{j}"] = {"ten": ten, "B": statistics.mean(b), "SHUF": statistics.mean(s),
                               "that": statistics.mean(d), "ci95": [lo, hi], "sig": sig.strip()}
        print(f"{ten:<20}{statistics.mean(b):>12,.0f}đ{statistics.mean(s):>12,.0f}đ"
              f"{statistics.mean(d):>15,.0f}đ  [{lo:>10,.0f}; {hi:>10,.0f}] {sig}")
    b = [r["B_all"] for r in rows]
    s = [r["S_all"] for r in rows]
    d = [x - y for x, y in zip(b, s)]
    lo, hi = _boot(d, rng)
    sig = "SIG" if (lo > 0 or hi < 0) else "ns "
    out["toan_doi"] = {"B": statistics.mean(b), "SHUF": statistics.mean(s),
                       "that": statistics.mean(d), "ci95": [lo, hi], "sig": sig.strip()}
    print(f"{'TOÀN ĐỘI':<20}{statistics.mean(b):>12,.0f}đ{statistics.mean(s):>12,.0f}đ"
          f"{statistics.mean(d):>15,.0f}đ  [{lo:>10,.0f}; {hi:>10,.0f}] {sig}")
    print("\n⇒ Cột `SHUF` = cùng LIỀU, cùng cường độ xáo trộn, nhưng **không biết đi đâu**.")
    print("  `THẬT = B − SHUF` là phần **chỉ giải thích được bằng THÔNG TIN của solver**.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
