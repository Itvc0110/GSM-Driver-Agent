"""G3 — Q-07 ở **n=100 paired seed**: nới shortlist k=6→8 đáng bao nhiêu, và lệch `accept_base` bao nhiêu?

    uv run python research/audit/2026-08-06-root-cause-idle/g3-q07-n100.py

## Vì sao PHẢI n=100 (không phải 30)

Đây là so **biến thể-vs-biến thể** (config k=6 vs k=8), không phải A/B advice-on/off ⇒ luật repo đòi
**`MIN_SEEDS_FOR_VARIANT_COMPARISON` = 100** (`CLAUDE.md`/BOOTSTRAP §6).

Và có một lý do **cấp thiết hơn**: quyết định Q-07 đang treo trên một con số **ngay sát ngưỡng**, mà hai
ước lượng hiện có **nằm hai bên ngưỡng đó**:

| nguồn | n | lệch lớn nhất vs `accept_base` ở k=8 |
| --- | --- | --- |
| comment config | 12 | **P7 −5,7đp** ❌ (vượt dung sai 5đp) |
| tôi đo (`g2`) | 5 | **P7 −4,99đp** ✅ (sát mép, chưa vượt) |

⇒ **Độ bất định của phép đo đang CÙNG BẬC với khoảng cách tới ngưỡng.** Quyết một câu chính sách trên
một con số như thế là sai. G3 đo ở n=100 **kèm CI bootstrap theo seed** để câu trả lời không phụ thuộc may.

## Đo gì

Ghép cặp cùng seed (CRN) giữa **A0 = k=6** và **A1 = k=8**:
- **Q-07**: `realized accept` từng archetype vs `accept_base` **cấu hình** (P1 0,85 · P2 0,95 · P3 0,98 ·
  P4 0,80 · P5 0,97 · P6 0,93 · P7 0,94) ⇒ **max |lệch|** + CI. Đây là đại lượng test `test_sim_realism`
  dùng — **không** phải hiệu k=8−k=6 (tôi đã suýt đo sai đại lượng này một lần, `UPDATE-176` §4).
- **Giá trị**: `served_rate`, đơn hết hạn, idle %, trips/tài xế, payout/tài xế.
- **Equity** (nợ đã ghi): **Gini payout** giữa các tài xế — để biết cải thiện có dồn vào một nhóm không.
- **Sức khoẻ**: đếm veto/flag tầng 5 để thấy trips tăng có chạm lan can không.

Nhãn: **MOCK/SIM**, advisor **TẮT** ở cả hai arm (cô lập hiệu chỉnh world).
"""
from __future__ import annotations

import copy
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                                 # noqa: E402
from gsm_sim.runner import run_once                               # noqa: E402

OUT = Path(__file__).resolve().parent / "g3-q07-n100.json"
SEEDS = list(range(3000, 3100))          # cửa sổ seed CHƯA dùng cho A0/A1 (tránh trùng 1000s)
ACCEPT_BASE = {"P1": 0.85, "P2": 0.95, "P3": 0.98, "P4": 0.80,
               "P5": 0.97, "P6": 0.93, "P7": 0.94}
BOOT = 2000


def _cfg(base: Config, k: int) -> Config:
    d = copy.deepcopy(base._data)
    d.setdefault("dispatcher", {})["candidate_ring_k_max"] = k
    return Config(d, base.root_dir)


def _gini(xs: list[float]) -> float:
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if n < 2 or sum(xs) <= 0:
        return 0.0
    cum = sum((2 * i - n + 1) * x for i, x in enumerate(xs))
    return cum / (n * sum(xs))


def _one(cfg: Config, seed: int) -> dict:
    res = run_once(cfg, seed)
    expired = sum(1 for e in res.events if e.kind == "order_expired")
    n_orders = len(res.orders)
    per_arch: dict[str, list[float]] = {}
    trips = idle = online = 0.0
    payouts: list[float] = []
    for a in res.actors:
        arch = str(getattr(a, "archetype", "?"))
        off = float(getattr(a, "orders_offered", 0.0))
        acc = float(getattr(a, "orders_accepted", 0.0))
        if off > 0:
            per_arch.setdefault(arch, []).append(acc / off)
        trips += float(getattr(a, "trips_done", 0.0))
        idle += float(getattr(a, "idle_min", 0.0))
        online += float(getattr(a, "online_min", 0.0))
        payouts.append(float(getattr(a, "payout_vnd", 0.0)))
    n = max(1, len(payouts))
    lech = {k: statistics.mean(v) - ACCEPT_BASE[k]
            for k, v in per_arch.items() if k in ACCEPT_BASE}
    veto = sum(1 for e in res.events if "veto" in e.kind or "fatigue" in e.kind)
    return {"served_rate": (n_orders - expired) / max(1, n_orders), "expired": expired,
            "idle_share": idle / max(1e-9, online), "trips_per_driver": trips / n,
            "payout_per_driver": sum(payouts) / n, "gini_payout": _gini(payouts),
            "veto_n": veto,
            "max_abs_lech": max((abs(v) for v in lech.values()), default=0.0),
            "arch_lech": lech}


def _ci(ds: list[float], rng: random.Random) -> tuple[float, float]:
    n = len(ds)
    boots = []
    for _ in range(BOOT):
        boots.append(statistics.mean(rng.choice(ds) for _ in range(n)))
    boots.sort()
    return boots[int(0.025 * BOOT)], boots[int(0.975 * BOOT)]


def main() -> int:
    base = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    c0, c1 = _cfg(base, 6), _cfg(base, 8)
    rows0, rows1 = [], []
    for i, s in enumerate(SEEDS):
        rows0.append(_one(c0, s))
        rows1.append(_one(c1, s))
        if (i + 1) % 20 == 0:
            print(f"  ... {i + 1}/{len(SEEDS)} seed")
    rng = random.Random(12345)

    print(f"\n=== A0 (k=6) vs A1 (k=8) · n={len(SEEDS)} paired seed (CRN) · advisor TẮT ===")
    keys = [("served_rate", "served_rate", 4), ("expired", "đơn hết hạn/ngày", 1),
            ("idle_share", "idle % online", 4), ("trips_per_driver", "trips/tài xế", 2),
            ("payout_per_driver", "payout/tài xế (đ)", 0), ("gini_payout", "Gini payout", 4),
            ("veto_n", "veto sức khoẻ (đếm)", 1)]
    ket = {}
    for k, nhan, nd in keys:
        a = statistics.mean(r[k] for r in rows0)
        b = statistics.mean(r[k] for r in rows1)
        ds = [rows1[i][k] - rows0[i][k] for i in range(len(SEEDS))]
        lo, hi = _ci(ds, rng)
        sig = "SIG" if (lo > 0 or hi < 0) else "ns "
        print(f"  {nhan:<24} A0 {a:>13.{nd}f} → A1 {b:>13.{nd}f} · Δ {statistics.mean(ds):>+12.{nd}f} "
              f"CI[{lo:+.{nd}f}; {hi:+.{nd}f}] {sig}")
        ket[k] = {"A0": a, "A1": b, "delta": statistics.mean(ds), "ci95": [lo, hi],
                  "significant": sig.strip() == "SIG"}

    print(f"\n=== Q-07: lệch lớn nhất vs `accept_base` CẤU HÌNH (dung sai 5,00đp) ===")
    for ten, rows in (("A0 k=6", rows0), ("A1 k=8", rows1)):
        mx = [r["max_abs_lech"] for r in rows]
        m = statistics.mean(mx)
        lo, hi = _ci(mx, rng)
        vuot = sum(1 for v in mx if v > 0.05)
        print(f"  {ten}: max|lệch| TB {m * 100:5.2f}đp · CI[{lo * 100:5.2f}; {hi * 100:5.2f}]đp "
              f"· số seed VƯỢT 5đp: {vuot}/{len(mx)} = {vuot / len(mx):.0%}")
        ket[f"q07_{ten.split()[0]}"] = {"mean_dp": m * 100, "ci95_dp": [lo * 100, hi * 100],
                                        "seed_vuot_5dp": vuot, "n": len(mx)}
    # archetype nào là vế ràng
    print(f"\n  lệch TB theo archetype (đp) — A0 → A1:")
    for arch in sorted(ACCEPT_BASE):
        a = statistics.mean(r["arch_lech"].get(arch, 0.0) for r in rows0) * 100
        b = statistics.mean(r["arch_lech"].get(arch, 0.0) for r in rows1) * 100
        co = "  ← VẾ RÀNG" if abs(b) >= 4.5 else ""
        print(f"    {arch}: {a:+6.2f} → {b:+6.2f}{co}")
        ket.setdefault("arch_lech_dp", {})[arch] = {"A0": a, "A1": b}

    q0, q1 = ket["q07_A0"], ket["q07_A1"]
    print(f"\n=== PHÁN QUYẾT Q-07 (n=100, có CI) ===")
    if q1["ci95_dp"][0] > 5.0:
        print(f"  ⇒ k=8 VƯỢT dung sai một cách CHẮC CHẮN (cận dưới CI {q1['ci95_dp'][0]:.2f}đp > 5) "
              f"⇒ Q-07 chặn thật, comment config ĐÚNG.")
    elif q1["ci95_dp"][1] < 5.0:
        print(f"  ⇒ k=8 KHÔNG vượt dung sai (cận trên CI {q1['ci95_dp'][1]:.2f}đp < 5) "
              f"⇒ **comment config (n=12) đã ước QUÁ CAO** ⇒ Q-07 có thể KHÔNG còn là vật chặn.")
    else:
        print(f"  ⇒ CI [{q1['ci95_dp'][0]:.2f}; {q1['ci95_dp'][1]:.2f}]đp **BẮC QUA** ngưỡng 5đp "
              f"⇒ ở n=100 vẫn KHÔNG phân xử được. Đây là thông tin QUAN TRỌNG: câu hỏi Q-07 "
              f"không nên được quyết bằng một ngưỡng cứng trên một đại lượng nhiễu cỡ này.")

    OUT.write_text(json.dumps({
        "what": "G3 — Q-07 ở n=100 paired seed: giá trị của k=8 và lệch accept_base",
        "mock": True, "advisor": "TẮT ở cả hai arm", "seeds": [SEEDS[0], SEEDS[-1]],
        "n_seeds": len(SEEDS), "bootstrap": BOOT, "accept_base_config": ACCEPT_BASE,
        "ket_qua": ket,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
