"""Cycle 9 — PHÂN RÃ `+6.016đ` bằng ghép cặp **CÙNG ACTOR** giữa hai arm (paired CRN).

## Câu hỏi

`positioning` là kênh **DUY NHẤT** Cường duyệt bật mặc định, và `+6.016đ/người/ngày`
(`UPDATE-087`) là bằng chứng giá trị của advisor. Nhưng tôi vừa đo: chỉ **30,0–40,0%** đội thực
sự nhận và đi theo lời khuyên (`D-B3-LIEU`). Hai cách đọc dẫn tới **hai quyết định ship khác hẳn**:

  (a) **TẬP TRUNG** — hiệu ứng dồn vào ~1/3 người được chạm ⇒ giá trị/người CAO hơn nhiều
  (b) **LAN TOẢ** — người không được chạm cũng hưởng (bớt dồn cục) ⇒ đọc như hiện tại

## Vì sao phải ghép CÙNG actor

Ở `b3-*.py` tôi đã đo phép so **hai nhóm** (được-chạm vs không) và nó **VÔ DỤNG**:
`+9.703đ / +5.030đ / −5.558đ` — **đổi dấu giữa các seed**, vì ai được gán phụ thuộc vị trí/trạng
thái (**selection**). Cách đúng: so **mỗi actor với CHÍNH NÓ** ở arm đối chứng, cùng seed (CRN).

## Đại lượng

Với mỗi seed: `Δ_i = payout_B(i) − payout_A(i)` cho từng actor `i`, rồi tách theo
`touched_B(i)` = actor `i` có ≥1 event `standby_followed` ở arm B.

  · `delta_all`     — trung bình toàn đội (phải **hoà giải** được với con số đang trích)
  · `delta_touched` — hiệu ứng ở nhóm cơ chế THỰC SỰ chạm tới
  · `delta_un`      — **lan toả** lên nhóm không được chạm ⇒ phân xử (a) vs (b)

⚠ **Giới hạn phải nói trước:** `touched_B` được xác định **SAU** can thiệp và phụ thuộc chính
arm B ⇒ đây là ước lượng kiểu **ATT** cho nhóm mà cơ chế với tới, **không** phải hiệu ứng nhân
quả cho một nhóm định trước. Nó KHÔNG bị lỗi selection của phép so hai nhóm (vì mỗi actor so với
chính nó), nhưng **thành viên nhóm là nội sinh**.

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/c9-phan-ra-per-actor-paired-crn.py
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
from gsm_sim.parallel import _cfg_with  # noqa: E402  (đúng ngữ nghĩa deep-copy/coverage của engine)
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = list(range(3300, 3330))          # 30 seed TƯƠI (chưa dùng ở G1/G3/B3)
B = 2000                                  # lần bootstrap


def _boot(xs: list[float], rng: random.Random) -> tuple[float, float]:
    if len(xs) < 2:
        return (float("nan"), float("nan"))
    m = [statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(B)]
    m.sort()
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
        cham = {e.actor_id for e in rb.events if e.kind == "standby_followed"}
        ids = sorted(set(pa) & set(pb))
        d_all = [pb[i] - pa[i] for i in ids]
        d_t = [pb[i] - pa[i] for i in ids if i in cham]
        d_u = [pb[i] - pa[i] for i in ids if i not in cham]
        per_seed.append({
            "seed": seed, "n": len(ids), "n_cham": len(d_t),
            "ty_le_cham": len(d_t) / len(ids) if ids else 0.0,
            "delta_all": statistics.mean(d_all) if d_all else 0.0,
            "delta_touched": statistics.mean(d_t) if d_t else float("nan"),
            "delta_un": statistics.mean(d_u) if d_u else float("nan"),
        })
        if k % 5 == 0 or k == len(SEEDS):
            print(f"  ... {k}/{len(SEEDS)} seed")

    rng = random.Random(20260807)
    out: dict = {"seeds": SEEDS, "per_seed": per_seed}
    print(f"\n=== PHÂN RÃ · n={len(SEEDS)} seed ghép cặp CÙNG ACTOR (CRN) · kênh positioning ===")
    print(f"{'đại lượng':<34}{'trung bình':>14}  {'CI 95%':>26}")
    for ten, key in (("Δ payout TOÀN ĐỘI", "delta_all"),
                     ("Δ payout nhóm ĐƯỢC CHẠM", "delta_touched"),
                     ("Δ payout nhóm KHÔNG chạm (lan toả)", "delta_un")):
        xs = [r[key] for r in per_seed if r[key] == r[key]]      # loại NaN
        m = statistics.mean(xs)
        lo, hi = _boot(xs, rng)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns "
        out[key] = {"mean": m, "ci95": [lo, hi], "sig": sig.strip()}
        print(f"{ten:<34}{m:>13,.0f}đ  [{lo:>10,.0f}; {hi:>10,.0f}]  {sig}")

    ty = [r["ty_le_cham"] for r in per_seed]
    out["ty_le_cham"] = {"mean": statistics.mean(ty), "min": min(ty), "max": max(ty)}
    print(f"\ntỷ lệ đội ĐƯỢC CHẠM: TB {statistics.mean(ty):.1%} "
          f"[{min(ty):.1%}; {max(ty):.1%}]")

    da, dt = out["delta_all"]["mean"], out["delta_touched"]["mean"]
    if da:
        print(f"\n⇒ Δ ở nhóm được chạm gấp **{dt / da:.2f}×** trung bình toàn đội "
              f"(vì liều chỉ rơi vào {statistics.mean(ty):.0%} người)")
    print("⚠ `touched` xác định SAU can thiệp và nội sinh theo arm B ⇒ đây là ước lượng kiểu ATT")
    print("  cho nhóm cơ chế với tới, KHÔNG phải hiệu ứng nhân quả cho một nhóm định trước.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
