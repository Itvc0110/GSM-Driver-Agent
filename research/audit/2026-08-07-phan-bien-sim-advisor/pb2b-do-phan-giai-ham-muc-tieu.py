"""pb2b — ĐỘ PHÂN GIẢI của hàm mục tiêu S4: mỗi hàng cost có mấy GIÁ TRỊ KHÁC NHAU?

`capacity_alloc._assign_kind` dựng `cost[i, j] = pen_i` nếu `slots[j].target == cand_i.target`,
ngược lại `pen_i + 10.0`. `pen_i` KHÔNG phụ thuộc `j` ⇒ mỗi HÀNG chỉ có **tối đa 2 giá trị**
⇒ mọi ô "không đúng target" **BẰNG NHAU TUYỆT ĐỐI** ⇒ ai bị stagger thì đi đâu là một phép
PHÁ HOÀ THUẦN TUÝ của scipy, không phải một lựa chọn được mô hình hoá.

Đo (arm B thật, 10 seed):
  · số giá trị KHÁC NHAU trong mỗi hàng cost (kỳ vọng cấu trúc: ≤2)
  · cỡ TẬP HOÀ = số ô đích khác `target` mà một ứng viên bị stagger có thể rơi vào
  · khoảng cách (km) từ ô ĐÍNH HƯỚNG (`target` = ô còn trần GẦN NHẤT, world.py `pref`)
    tới ô THỰC SỰ bị gán — tức lượng thông tin địa lý DUY NHẤT của pipeline bị vứt đi

Chạy: uv run python research/audit/2026-08-07-phan-bien-sim-advisor/pb2b-do-phan-giai-ham-muc-tieu.py
"""
from __future__ import annotations

import copy
import json
import pathlib
import statistics
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gsm_core.solvers import capacity_alloc as CA  # noqa: E402
from gsm_sim.config import Config  # noqa: E402
from gsm_sim.geo import cell_distance_km  # noqa: E402
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = list(range(3300, 3310))
_THAT = CA.solve


class _Ghi:
    def __init__(self):
        self.lo = []

    def __call__(self, ai):
        rep = _THAT(ai)
        self.lo.append((copy.deepcopy(ai), copy.deepcopy(rep)))
        return rep


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    n_hang, gia_tri_hang, tap_hoa, km_vut, n_zone, cap_val = 0, Counter(), [], [], [], Counter()
    n_alloc = n_stag = 0
    ly_do = Counter()
    grid = None
    for seed in SEEDS:
        g = _Ghi()
        CA.solve = g
        try:
            r = run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                   coverage="all"), seed)
        finally:
            CA.solve = _THAT
        grid = r.grid
        for ai, rep in g.lo:
            cands = [c for c in ai["candidates"] if c["advice_kind"] == "standby_zone"]
            zones = [z["zone"] for z in ai["zone_supply"]]
            for z in ai["zone_supply"]:
                cap_val[int(z["capacity"])] += 1
            n_zone.append(len(zones))
            tgt = {c["driver_id"]: c["target"] for c in cands}
            for c in cands:
                n_hang += 1
                # số giá trị khác nhau trên hàng: pen (nếu target ∈ zones) và pen+10
                k = (1 if c["target"] in zones else 0) + (1 if any(
                    z != c["target"] for z in zones) else 0)
                gia_tri_hang[k] += 1
                if k == 1:
                    ly_do[("target∉zones" if c["target"] not in zones
                           else f"chỉ_{len(set(zones))}_zone")] += 1
            for a in (rep["solution"]["allocations"]):
                if a["advice_kind"] != "standby_zone":
                    continue
                n_alloc += 1
                t0 = tgt[a["driver_id"]]
                if a["assigned_target"] != t0:
                    n_stag += 1
                    tap_hoa.append(sum(1 for z in set(zones) if z != t0))
                    km_vut.append(cell_distance_km(r.grid, t0, a["assigned_target"]))
    out = {
        "seeds": SEEDS, "n_hang_cost": n_hang,
        "so_gia_tri_khac_nhau_moi_hang": dict(gia_tri_hang),
        "ly_do_hang_1_gia_tri": dict(ly_do),
        "n_alloc": n_alloc, "n_stagger": n_stag, "pct_stagger": n_stag / max(1, n_alloc),
        "tap_hoa_tb": statistics.mean(tap_hoa) if tap_hoa else 0.0,
        "tap_hoa_median": statistics.median(tap_hoa) if tap_hoa else 0.0,
        "tap_hoa_min": min(tap_hoa, default=0), "tap_hoa_max": max(tap_hoa, default=0),
        "km_vut_tb": statistics.mean(km_vut) if km_vut else 0.0,
        "km_vut_median": statistics.median(km_vut) if km_vut else 0.0,
        "km_vut_max": max(km_vut, default=0.0),
        "n_zone_tb": statistics.mean(n_zone), "capacity_phan_bo": dict(cap_val),
    }
    print(f"hàng cost: {n_hang} | số GIÁ TRỊ KHÁC NHAU mỗi hàng: {dict(gia_tri_hang)}")
    print(f"  lý do hàng chỉ 1 giá trị: {dict(ly_do)}")
    print(f"alloc {n_alloc} | stagger {n_stag} = {out['pct_stagger']:.1%}")
    print(f"TẬP HOÀ (ô đích bằng-cost khi bị stagger): TB {out['tap_hoa_tb']:.2f}"
          f" · median {out['tap_hoa_median']} · [{out['tap_hoa_min']}; {out['tap_hoa_max']}]")
    print(f"km bị VỨT (ô đính hướng → ô thực gán): TB {out['km_vut_tb']:.3f} km"
          f" · median {out['km_vut_median']:.3f} · max {out['km_vut_max']:.3f}")
    print(f"số zone/lô TB {out['n_zone_tb']:.2f} | phân bố capacity {dict(cap_val)}")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"artifact → {OUT}")


if __name__ == "__main__":
    main()
