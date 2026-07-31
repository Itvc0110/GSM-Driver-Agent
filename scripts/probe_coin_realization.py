"""D-E10-06 — Δ của kênh vị trí NHẠY tới mức nào với realization COIN?

Câu hỏi (mở từ 2026-07-31): đổi lưới quyết định 60′→30′ làm `Δ_oracle` dịch **−1.590đ**
(ghép cặp n=100, CI [−2.775, −356], p=0,012, 62/38 seed âm). Lưới chỉ đổi *chuỗi khoá* của
coin, không đổi luật nào — nên hoặc (a) có cơ chế chưa thấy, hoặc (b) type-I error trên MỘT
phép so.

Phép phân biệt: giữ NGUYÊN mọi thứ, chỉ đổi **salt của coin** (một hằng vô hại thêm vào
`material_revision`). Nếu Δ cũng dịch cỡ tương tự ⇒ đó là **bất định coin-realization** mà
CI per-seed không bắt hết ⇒ kết luận (b), và bài học là: *CI của Δ chưa bao gồm bất định
này; muốn kết luận chắc phải lặp qua nhiều realization*. Nếu Δ gần như không dịch ⇒ (a).

    uv run python scripts/probe_coin_realization.py [n_salt]      # mặc định 3 salt × 100 seed

Artifact: research/audit/2026-07-27-current-state/43-coin-realization-probe.json
Mọi số MOCK.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from gsm_core.lifecycle import cadence
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with, bootstrap_ci
from gsm_sim.runner import Config, run_once

OUT = Path("research/audit/2026-07-27-current-state")
SEEDS = list(range(5000, 5100))


def main() -> None:
    n_salt = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    base = Config.load("configs/pilot_dongda.yaml")
    cfg_a = _cfg_with(base, enabled=False, actor_id=None, channels=None)
    cfg_b = _cfg_with(base, enabled=True, actor_id=None,
                      channels=CHANNEL_LADDER["positioning"], coverage="all")

    orig = cadence.adherence_coin
    world_a: dict[int, float] = {}
    rows: dict[str, list[float]] = {}

    for k in range(n_salt):
        salt = "" if k == 0 else f"|salt{k}"

        def coin(seed, decision_id, material_revision, _s=salt):
            return orig(seed, decision_id, material_revision + _s)

        cadence.adherence_coin = coin
        # bridge import trực tiếp tên hàm ⇒ phải vá cả module đó
        import gsm_sim.advice_bridge as AB
        AB.adherence_coin = coin
        deltas = []
        for s in SEEDS:
            if s not in world_a:
                world_a[s] = float(np.mean([a.payout_vnd for a in run_once(cfg_a, s).actors]))
            rb = run_once(cfg_b, s)
            deltas.append(float(np.mean([a.payout_vnd for a in rb.actors])) - world_a[s])
        rows[f"salt{k}"] = deltas
        print(f"  salt{k}: Δ mean = {np.mean(deltas):+.0f}đ", flush=True)

    cadence.adherence_coin = orig
    import gsm_sim.advice_bridge as AB
    AB.adherence_coin = orig

    base_key = "salt0"
    art = {"what": "D-E10-06 — Δ kênh vị trí nhạy tới mức nào với realization COIN",
           "mock": True, "seeds": SEEDS, "n_salt": n_salt,
           "arm": "positioning wait_only, coverage all, lưới quyết định hiện hành (30′)",
           "per_salt": {}, "paired_vs_salt0": {}}
    for k, d in rows.items():
        lo, hi = bootstrap_ci(d)
        art["per_salt"][k] = {"mean": round(float(np.mean(d)), 1),
                              "ci": [round(lo, 1), round(hi, 1)]}
        if k != base_key:
            dd = [d[i] - rows[base_key][i] for i in range(len(d))]
            lo2, hi2 = bootstrap_ci(dd)
            art["paired_vs_salt0"][k] = {
                "mean": round(float(np.mean(dd)), 1), "ci": [round(lo2, 1), round(hi2, 1)],
                "n_am": int(sum(1 for x in dd if x < 0)), "n_duong": int(sum(1 for x in dd if x > 0)),
                "sig": bool(lo2 > 0 or hi2 < 0)}
    shifts = [v["mean"] for v in art["paired_vs_salt0"].values()]
    art["ket_luan"] = (
        f"Đổi salt (KHÔNG đổi luật nào) làm Δ dịch {min(shifts):+.0f}..{max(shifts):+.0f}đ. "
        + ("Cỡ dịch SO SÁNH ĐƯỢC với −1.590đ của đổi lưới ⇒ nhất quán với giả thuyết (b) "
           "BẤT ĐỊNH COIN-REALIZATION, không phải cơ chế của lưới."
           if max(abs(s) for s in shifts) >= 700 else
           "Cỡ dịch NHỎ HƠN HẲN −1.590đ ⇒ nghiêng về giả thuyết (a): đổi lưới có cơ chế thật.")
        + " ⚠ Hệ quả chung: CI per-seed KHÔNG bao gồm bất định realization coin.")
    out = OUT / "43-coin-realization-probe.json"
    out.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {out}")
    for k, v in art["paired_vs_salt0"].items():
        print(f"  {k} vs salt0: {v['mean']:+.0f}đ CI={v['ci']} sig={v['sig']} "
              f"({v['n_am']}âm/{v['n_duong']}dương)")
    print(art["ket_luan"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
