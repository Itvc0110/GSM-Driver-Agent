"""F3 — vì sao đội xe hội tụ về lưu vực XA (`953`+`bb3`) thay vì lưu vực GẦN mà luật ưu ái hơn?

    uv run python research/audit/2026-08-06-root-cause-idle/f3-why-far-basin.py

## Câu hỏi (từ `UPDATE-169` §5)

F1 đo: cặp attractor có lưu vực **lớn nhất** là `88f`+`8c7` (**42,8%** ô-giờ) và nó nằm **1,34–1,60 km**
từ ô nhiều-đơn-chết. Nhưng run thật (rc-03) cho: **56,6%** phút idle của đội dồn vào `953`+`bb3` — cặp
nằm **3,46–3,71 km**, tức **NGOÀI** bán kính chào đơn.

Vì sao? F1 cân **mọi ô khởi đầu như nhau**; đội xe thật thì **không** — họ bắt đầu từ `home_cell`.
Giả thuyết F3: **VỊ TRÍ KHỞI ĐẦU quyết định lưu vực**, không phải luật ưu ái cái nào.

## Cách kiểm (rẻ, quyết định được)

Với từng actor thật: lấy `home_cell` → chạy **đúng** luật leo dốc (bậc sốt-ruột cao, như F1) → xem nó
rơi vào attractor nào. Nếu phân bố attractor theo `home_cell` **khớp** phân bố idle quan sát được (dồn
vào `953`+`bb3`) ⇒ giả thuyết ĐỨNG. Nếu vẫn ra `88f`+`8c7` ⇒ giả thuyết ĐỔ, phải tìm chỗ khác.

Nhãn: **MOCK/SIM**, arm A.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gsm_sim.config import Config                                # noqa: E402
from gsm_sim.demand import expected_demand_field                 # noqa: E402
from gsm_sim.geo import build_grid                               # noqa: E402
from gsm_sim.runner import run_once                              # noqa: E402

from importlib import import_module                              # noqa: E402
_f1 = import_module("f1-basin-map".replace("-", "_")) if False else None
# import trực tiếp hai hàm của F1 mà không đổi tên file (tên có dấu '-')
import importlib.util                                            # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "f1mod", Path(__file__).resolve().parent / "f1-basin-map.py")
f1mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(f1mod)

OUT = Path(__file__).resolve().parent / "f3-why-far-basin.json"
SEEDS = [1000, 1001, 1002, 1003, 1004]
O_HUT_QUAN_SAT = {"89415cb4953ffff", "89415cb4bb3ffff"}
F1_TOP = {"89415cb488fffff", "89415cb48c7ffff"}


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
    field_by_hour = expected_demand_field(grid, cfg)
    beh = cfg.get("behavior", {}) or {}
    max_steps = int(beh.get("idle_impatience_max_steps", 2))
    ring, bar, give_up = 1 + max_steps, 1.25 - 0.10 * max_steps, True
    hour = max(field_by_hour, key=lambda h: sum(field_by_hour[h].values()))

    home_counts: Counter = Counter()
    n_actor = 0
    for s in SEEDS:
        res = run_once(cfg, s)
        for a in res.actors:
            hc = getattr(a, "home_cell", None)
            if hc:
                home_counts[hc] += 1
                n_actor += 1
    print(f"MOCK · arm A · {len(SEEDS)} seed · {n_actor} actor-run · "
          f"{len(home_counts)} home_cell khác nhau · giờ khảo sát {hour}h\n")

    # attractor của từng home_cell theo ĐÚNG luật (dùng lại hàm của F1, σ=0 và σ thực tế)
    for sigma, ten in ((0.0, "σ=0 (không nhiễu)"), (0.30, "σ=0,30 (nhiễu điển hình)")):
        att_by_actor: Counter = Counter()
        for i, (hc, cnt) in enumerate(home_counts.items()):
            if not grid.is_core(hc):
                att_by_actor[("NGOAI_LOI",)] += cnt
                continue
            att, _ = f1mod._attractor(hc, grid, field_by_hour[hour], sigma=sigma, seed=7000,
                                      actor=i, hour=hour, ring=ring, bar=bar, give_up=give_up)
            att_by_actor[tuple(sorted(att))] += cnt
        tong = sum(att_by_actor.values())
        print(f"=== Lưu vực theo HOME_CELL — {ten} ===")
        for att, c in att_by_actor.most_common(5):
            nhan = ""
            if set(att) & O_HUT_QUAN_SAT:
                nhan = "  ← Ô HÚT QUAN SÁT ĐƯỢC (xa 3,5 km)"
            elif set(att) & F1_TOP:
                nhan = "  ← attractor lưu vực lớn nhất của F1 (gần 1,3 km)"
            print(f"  {list(att)}  {c}/{tong} = {c / tong:6.1%}{nhan}")
        share_hut = sum(c for a, c in att_by_actor.items() if set(a) & O_HUT_QUAN_SAT) / tong
        share_top = sum(c for a, c in att_by_actor.items() if set(a) & F1_TOP) / tong
        print(f"  ⇒ vào Ô HÚT quan sát được: {share_hut:.1%}  ·  "
              f"vào attractor GẦN cầu của F1: {share_top:.1%}\n")

    # home_cell có tự dồn vào hai ô hút không?
    hut_home = sum(c for hc, c in home_counts.items() if hc in O_HUT_QUAN_SAT) / max(1, n_actor)
    print(f"=== home_cell có TRÙNG hai ô hút không? {hut_home:.1%} actor có home_cell là chính hai ô đó")
    top_home = home_counts.most_common(5)
    print("  top-5 home_cell: " + ", ".join(f"{h[-6:]}={c}" for h, c in top_home))

    OUT.write_text(json.dumps({
        "what": "F3 — lưu vực theo home_cell: vị trí khởi đầu có giải thích được ô hút xa không?",
        "mock": True, "arm": "A", "seeds": SEEDS, "hour": hour,
        "n_actor_run": n_actor,
        "share_home_cell_la_o_hut": round(hut_home, 4),
        "top5_home_cell": [[h, c] for h, c in top_home],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
