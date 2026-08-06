"""F2 — xuất BẢNG ĐƠN CHẾT THEO Ô (đo thật) + tính lại khoảng cách attractor → ô nhiều đơn chết.

    uv run python research/audit/2026-08-06-root-cause-idle/f2-expired-by-cell.py

## Vì sao cần

`f1-basin-map.py` phải dùng **PROXY = cầu kỳ vọng** cho cột *"khoảng cách tới ô nhiều đơn chết"* vì
`rc-03-overlap.json` chỉ xuất **tổng hợp** (top-10 gộp = 85,8 đơn), **không** xuất bảng theo ô. Hệ quả:
`f1-basin-map-KETQUA.md` §2.6 phải tự ghi *"cấm dùng số 0,00–1,34 km của F1 để bác số 3,40–4,73 km của
verdict"* — một caveat do thiếu dữ liệu, không phải do bản chất.

Script này **đo thẳng** đơn chết theo ô từ event log arm A, rồi tính lại khoảng cách để **so được**.
Đây là phép kiểm cuối cho claim hình học của `rc-00-VERDICT` §0.

Nhãn: **MOCK/SIM**, arm A (mọi kênh tắt) — đúng nền mà verdict dùng.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                                # noqa: E402
from gsm_sim.geo import build_grid, cell_distance_km             # noqa: E402
from gsm_sim.runner import run_once                              # noqa: E402

OUT = Path(__file__).resolve().parent / "f2-expired-by-cell.json"
SEEDS = [1000, 1001, 1002, 1003, 1004]
# Hai ô hút idle ĐO ĐƯỢC ở rc-03 (§2 `top2_o_hut_idle.cells`) — giữ 15 ký tự như artifact
O_HUT = ["89415cb4953ffff", "89415cb4bb3ffff"]
# Attractor lưu vực lớn nhất mà F1 tìm ra (không phải hai ô trên) — để so hai bên
F1_TOP = ["89415cb488fffff", "89415cb48c7ffff"]


def main() -> int:
    cfg = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    data_dir = cfg.resolve_path("world.data_dir")
    grid = build_grid(
        geom_path=data_dir / cfg.get("world.geom_file"),
        stations_path=data_dir / cfg.get("world.stations_file"),
        poi_path=data_dir / cfg.get("world.poi_file"),
        res=int(cfg.get("world.h3_res")),
        res_report=int(cfg.get("world.h3_res_report")),
    )

    expired: Counter = Counter()
    tong_expired = 0
    for s in SEEDS:
        res = run_once(cfg, s)                      # arm A: config mặc định, advice.enabled=False
        # ⚠ event `order_expired` KHÔNG mang cell (`world.py:619` chỉ log order_id) ⇒ phải map qua
        # trace đơn. Đây chính là một mảnh của VISIBILITY GAP mà verdict §3-H4 nêu.
        cell_of = {o.order_id: o.pickup_cell for o in res.orders}
        for e in res.events:
            if e.kind == "order_expired":
                oid = (e.detail or {}).get("order_id")
                c = cell_of.get(oid, "")
                if c:
                    expired[c] += 1
                tong_expired += 1
    n = len(SEEDS)
    per_day = {c: v / n for c, v in expired.items()}
    print(f"MOCK · arm A · {n} seed · tổng đơn chết {tong_expired / n:.1f}/ngày "
          f"· {len(per_day)} ô có đơn chết\n")

    top = sorted(per_day.items(), key=lambda kv: -kv[1])
    print("=== TOP 10 ô nhiều đơn chết nhất (đo, arm A) ===")
    for c, v in top[:10]:
        print(f"  {c}  {v:6.2f} đơn/ngày")
    share10 = sum(v for _, v in top[:10]) / max(1e-9, sum(per_day.values()))
    print(f"  ⇒ top-10 chiếm {share10:.1%} kho đơn chết "
          f"(rc-03 báo 42,1% — {'KHỚP' if abs(share10 - 0.421) < 0.10 else 'LỆCH, phải truy'})\n")

    top5 = [c for c, _ in top[:5]]
    print("=== KHOẢNG CÁCH tới 5 ô nhiều đơn chết nhất — bây giờ SO ĐƯỢC với verdict ===")
    for nhom, ten in ((O_HUT, "hai ô HÚT IDLE đo được (verdict gọi là 'bẫy')"),
                      (F1_TOP, "attractor lưu vực LỚN NHẤT của F1")):
        print(f"  {ten}:")
        for a in nhom:
            ds = [(t, cell_distance_km(grid, a, t)) for t in top5]
            dmin = min(ds, key=lambda x: x[1])
            print(f"    {a}: gần nhất {dmin[1]:.2f} km ({dmin[0]}) · "
                  f"dải {min(d for _, d in ds):.2f}–{max(d for _, d in ds):.2f} km · "
                  f"đơn chết CỦA CHÍNH Ô NÀY {per_day.get(a, 0.0):.2f}/ngày")
    print("\n=== PHÁN QUYẾT claim hình học của verdict §0 ===")
    dmins = [min(cell_distance_km(grid, a, t) for t in top5) for a in O_HUT]
    lo, hi = min(dmins), max(dmins)
    print(f"  verdict nói: hai ô hút cách MỌI ô nhiều đơn chết 3,40–4,73 km")
    print(f"  đo được:     {lo:.2f}–{hi:.2f} km tới top-5 (đơn chết ĐO ĐƯỢC)")
    if lo >= 2.22:
        print(f"  ⇒ ĐỨNG về mặt định tính: cả hai ô hút đều NGOÀI bán kính chào đơn 2,22 km")
    else:
        print(f"  ⇒ 🔴 BÁC: có ô hút NẰM TRONG bán kính chào đơn 2,22 km ⇒ claim hình học sai")

    OUT.write_text(json.dumps({
        "what": "F2 — đơn chết theo ô (đo, arm A) + khoảng cách attractor→ô đơn chết",
        "mock": True, "arm": "A (mọi kênh tắt)", "seeds": SEEDS,
        "tong_don_chet_moi_ngay": round(tong_expired / n, 2),
        "don_chet_theo_o_moi_ngay": {c: round(v, 3) for c, v in top},
        "top10_share": round(share10, 4),
        "o_hut_idle_do_duoc": O_HUT, "f1_attractor_luu_vuc_lon_nhat": F1_TOP,
        "khoang_cach_km_toi_top5_o_don_chet": {
            a: {t: round(cell_distance_km(grid, a, t), 3) for t in top5}
            for a in O_HUT + F1_TOP},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
