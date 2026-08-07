"""Cycle 9b — phân rã lại, nhưng chia nhóm theo tiêu chí **TIỀN-CAN-THIỆP** (arm A).

## Vì sao cần bản 9b

`c9-phan-ra-per-actor-paired-crn.py` chia nhóm theo `touched_B` = *"actor có `standby_followed`
ở arm B"*. Kết quả gây sốc: nhóm **được chạm −2.326đ (ns)**, nhóm **không chạm +6.127đ (SIG)**.

**Nhưng `touched_B` là biến HẬU-CAN-THIỆP.** Điều kiện hoá trên nó là lỗi thiên lệch đã biết
(collider / post-treatment conditioning): actor được chạm **vì** ở arm B họ rơi vào trạng thái
rảnh ở ô bị siết trần — tức chính quỹ đạo do can thiệp tạo ra. Ghép cặp cùng actor **khử được**
đặc điểm cố định (archetype, ca) nhưng **không khử được** cái này.

## Bản 9b sửa đúng chỗ đó

Chia nhóm bằng một đại lượng **chỉ đọc từ arm A** — `Actor.idle_min` (phút rảnh của chính tài xế
đó trong thế giới KHÔNG có advisor). Arm A không chịu can thiệp nào ⇒ **không có post-treatment
conditioning**. Đây cũng đúng đối tượng mà kênh vị trí nhắm: người rảnh nhiều.

**Dự đoán nếu kênh hoạt động như thiết kế:** tercile RẢNH NHẤT (ở A) phải hưởng nhiều nhất.
**Nếu Δ phẳng hoặc đảo** ⇒ giá trị là **lan toả hệ thống**, không phải giúp đúng người nó nhắm.

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/c9b-phan-ra-theo-tieu-chi-TIEN-can-thiep.py
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
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = list(range(3300, 3330))          # CÙNG cửa sổ seed với 9a ⇒ so sánh được
B = 2000
NHOM = ("rảnh ÍT nhất", "giữa", "rảnh NHIỀU nhất")


def _boot(xs: list[float], rng: random.Random) -> tuple[float, float]:
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(B))
    return (m[int(0.025 * B)], m[int(0.975 * B)])


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    per_seed: list[dict] = []
    for k, seed in enumerate(SEEDS, 1):
        ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        rb = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                coverage="all"), seed)
        pa = {a.actor_id: float(a.payout_vnd) for a in ra.actors}
        pb = {a.actor_id: float(a.payout_vnd) for a in rb.actors}
        idle_a = {a.actor_id: float(a.idle_min) for a in ra.actors}      # ⭐ CHỈ arm A
        cham = {e.actor_id for e in rb.events if e.kind == "standby_followed"}
        ids = sorted(set(pa) & set(pb) & set(idle_a))
        xep = sorted(ids, key=lambda i: idle_a[i])
        t = len(xep) // 3
        terciles = [xep[:t], xep[t:2 * t], xep[2 * t:]]
        row = {"seed": seed, "n": len(ids)}
        for j, grp in enumerate(terciles):
            row[f"delta_t{j}"] = statistics.mean([pb[i] - pa[i] for i in grp]) if grp else 0.0
            row[f"idle_t{j}"] = statistics.mean([idle_a[i] for i in grp]) if grp else 0.0
            # ⭐ kiểm tiền đề: tercile rảnh nhiều có THẬT SỰ được chạm nhiều hơn không?
            row[f"cham_t{j}"] = (len([i for i in grp if i in cham]) / len(grp)) if grp else 0.0
        per_seed.append(row)
        if k % 5 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed")

    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS, "per_seed": per_seed}
    print(f"\n=== PHÂN RÃ theo TERCILE `idle_min` ĐO Ở ARM A · n={len(SEEDS)} seed ===")
    print(f"{'nhóm (tiền-can-thiệp)':<24}{'rảnh ở A':>10}{'% được chạm':>13}"
          f"{'Δ payout':>12}  {'CI 95%':>26}")
    for j, ten in enumerate(NHOM):
        ds = [r[f"delta_t{j}"] for r in per_seed]
        m, (lo, hi) = statistics.mean(ds), _boot(ds, rng)
        idl = statistics.mean([r[f"idle_t{j}"] for r in per_seed])
        ch = statistics.mean([r[f"cham_t{j}"] for r in per_seed])
        sig = "SIG" if (lo > 0 or hi < 0) else "ns "
        out[f"tercile_{j}"] = {"ten": ten, "idle_a_min": idl, "ty_le_cham": ch,
                               "delta_mean": m, "ci95": [lo, hi], "sig": sig.strip()}
        print(f"{ten:<24}{idl:>9.0f}′{ch:>12.1%}{m:>11,.0f}đ  [{lo:>10,.0f}; {hi:>10,.0f}] {sig}")

    print("\n⇒ Đọc: nếu kênh giúp ĐÚNG người nó nhắm thì tercile **rảnh NHIỀU nhất** phải hưởng")
    print("  nhiều nhất. Δ phẳng hoặc ĐẢO ⇒ giá trị là **lan toả hệ thống**, không phải trúng đích.")
    print("  Cột `% được chạm` là kiểm TIỀN ĐỀ: liều có thật sự rơi vào người rảnh nhiều không.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
