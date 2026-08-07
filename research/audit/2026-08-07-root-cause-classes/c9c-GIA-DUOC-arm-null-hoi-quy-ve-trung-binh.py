"""Cycle 9c — PLACEBO: mẫu hình tercile của `9b` có phải HIỆN VẬT của hồi-quy-về-trung-bình không?

## Mối đe doạ

`9b` chia tercile theo `idle_min` **đo ở arm A** rồi đo `Δ = payout_B − payout_A`, và ra:
rảnh-ít **−15.290đ SIG** · rảnh-nhiều **+26.106đ SIG**.

Nhưng **một mẫu hình y hệt xuất hiện khi KHÔNG có tác dụng nào cả**: `idle_min` ở A một phần là
may rủi (họ tình cờ đứng đâu). Ai có A **xấu bất thường** (rảnh nhiều) thì ở một lần rút khác sẽ
**tốt lên**; ai có A **tốt bất thường** (rảnh ít) sẽ **xấu đi**. Đó là **hồi quy về trung bình**,
và nó tạo ra đúng dấu +/− theo tercile mà `9b` quan sát được.

⇒ Không loại được cái này thì `9b` **không nói được gì**.

## Phép thử

Chạy **arm NULL**: `advice.enabled = True`, `coverage = all`, **nhưng `positioning_overrides =
"off"`** — advisor bật mà **kênh duy nhất đang ship thì tắt**. Mọi thứ khác giữ nguyên.

  · Nếu arm NULL **bit-identical** với arm A ⇒ không có xáo trộn ⇒ mẫu hình của `9b` là **THẬT**.
  · Nếu arm NULL **phân kỳ** và cho **cùng dấu +/− theo tercile** ⇒ mẫu hình `9b` là **HIỆN VẬT**.
  · Nếu phân kỳ nhưng Δ tercile **nhỏ hơn nhiều** ⇒ trừ đi phần hiện vật, phần còn lại là thật.

⚠ Bài học `DET-01` (đã trả giá): *"cờ bật/tắt có thể đổi nhiều thứ hơn ta tưởng — đo arm đối
chứng TRƯỚC khi tin Δ A/B"*. Đây chính là phép đo đó, áp cho một kết luận tôi sắp báo.

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/c9c-GIA-DUOC-arm-null-hoi-quy-ve-trung-binh.py
"""
from __future__ import annotations

import copy
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
from gsm_sim.sim_metrics import fingerprint_actors  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = list(range(3300, 3330))          # CÙNG cửa sổ với 9a/9b
B = 2000
NHOM = ("rảnh ÍT nhất", "giữa", "rảnh NHIỀU nhất")
# Δ của 9b để so trực tiếp
NHOM_9B = (-15290.0, -1158.0, 26106.0)


def _boot(xs, rng):
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(B))
    return (m[int(0.025 * B)], m[int(0.975 * B)])


def _null_cfg(cfg: Config) -> Config:
    """advisor BẬT nhưng kênh DUY NHẤT đang ship thì TẮT."""
    c = _cfg_with(cfg, enabled=True, actor_id=None, channels=None, coverage="all")
    c.data["advice"]["positioning_overrides"] = "off"
    return Config(copy.deepcopy(c.data), c.root_dir)


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    per_seed, n_identical = [], 0
    for k, seed in enumerate(SEEDS, 1):
        ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        rn = run_once(_null_cfg(cfg), seed)
        giong = fingerprint_actors(ra) == fingerprint_actors(rn)
        n_identical += giong
        pa = {a.actor_id: float(a.payout_vnd) for a in ra.actors}
        pn = {a.actor_id: float(a.payout_vnd) for a in rn.actors}
        idle_a = {a.actor_id: float(a.idle_min) for a in ra.actors}
        ids = sorted(set(pa) & set(pn) & set(idle_a))
        xep = sorted(ids, key=lambda i: idle_a[i])
        t = len(xep) // 3
        row = {"seed": seed, "fingerprint_giong": giong}
        for j, grp in enumerate((xep[:t], xep[t:2 * t], xep[2 * t:])):
            row[f"delta_t{j}"] = statistics.mean([pn[i] - pa[i] for i in grp]) if grp else 0.0
        per_seed.append(row)
        if k % 5 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed")

    print(f"\n=== ARM NULL (advisor bật, positioning TẮT) vs ARM A · n={len(SEEDS)} ===")
    print(f"fingerprint GIỐNG HỆT: {n_identical}/{len(SEEDS)} seed")
    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS, "n_fingerprint_giong": n_identical, "per_seed": per_seed}
    print(f"\n{'nhóm':<22}{'Δ arm NULL':>13}  {'CI 95%':>26}   {'Δ 9b (THẬT?)':>14}  {'tỷ lệ':>8}")
    for j, ten in enumerate(NHOM):
        ds = [r[f"delta_t{j}"] for r in per_seed]
        m, (lo, hi) = statistics.mean(ds), _boot(ds, rng)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns "
        ty = (m / NHOM_9B[j]) if NHOM_9B[j] else float("nan")
        out[f"tercile_{j}"] = {"ten": ten, "delta_null": m, "ci95": [lo, hi], "sig": sig.strip(),
                               "delta_9b": NHOM_9B[j], "ty_le_hien_vat": ty}
        print(f"{ten:<22}{m:>12,.0f}đ  [{lo:>10,.0f}; {hi:>10,.0f}] {sig} "
              f"{NHOM_9B[j]:>13,.0f}đ {ty:>7.1%}")

    print("\n⇒ Cột cuối = **phần của 9b có thể giải thích bằng xáo trộn thuần**, KHÔNG cần advisor.")
    print("  Gần 0% ⇒ 9b là thật. Gần 100% ⇒ 9b là hiện vật. Ở giữa ⇒ trừ đi rồi mới đọc.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
