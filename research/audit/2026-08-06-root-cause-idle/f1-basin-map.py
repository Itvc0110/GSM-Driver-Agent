"""F1 — BASIN MAP của luật đứng-chỗ: điểm hút + kích thước lưu vực. **0 seed sim, chỉ hình học.**

    uv run python research/audit/2026-08-06-root-cause-idle/f1-basin-map.py

## Vì sao script này tồn tại — nó là FALSIFIER cho chính kết luận của tôi

`rc-00-VERDICT.md` §2 kết luận: cung rảnh bị **giam trong hai ô "bẫy niềm tin"** (cực đại địa phương
của trường cầu tĩnh) cách mọi ô nhiều đơn chết 3,4–4,7 km. Nhưng rc-04 **tự thừa nhận** ở mục
*adversarial self-review*: nó **chưa liệt kê hết attractor** và **chưa đo kích thước lưu vực** ⇒
*"có thể còn attractor tốt (gần cầu) mà phần lớn tài xế thực ra rơi vào"*.

Script này trả lời đúng câu đó. Nó **có thể GIẾT** claim "bẫy": nếu phần lớn ô lõi chảy về những
attractor **gần cầu**, thì "bẫy" chỉ là chuyện của vài ô rìa và kết luận root-cause phải viết lại.

## Mô phỏng ĐÚNG luật, không xấp xỉ

- Niềm tin (`world.py:1146-1175`): chỉ dựng trên `grid_disk(cell, 2)` (**tầm nhìn ~0,74 km**);
  giá trị = `expected_demand_field[hour][cell] × nhiễu lognormal(0, σ)` **per-cell, keyed
  (seed, actor, hour, cell)** ⇒ tái tạo được y hệt.
- Leo dốc (`behavior.py:199-231`): `ring/bar/p_move` theo bậc sốt-ruột (`idle_impatience_step_min`,
  `max_steps`); chọn `nb` nếu `v − 0.15·dist_km > best_val × bar`; nhánh **give_up** (sốt ruột kịch)
  cho phép **một** bước không-lên-dốc: `max(_neighbors(ring), key=(hint, cell))`.
- ⚠ Ô ở **ring 3** luôn có `hint = 0.0` vì niềm tin chỉ phủ ring ≤ 2 ⇒ bước "đi xa hơn khi sốt ruột"
  là **NO-OP** (đó là nợ `B3`). Script mô phỏng đúng khuyết tật này, **không** sửa nó ngầm.
- `p_move` **không** được mô phỏng: nó chỉ ảnh hưởng *tốc độ* tới attractor, không đổi *attractor nào*.

Mọi số là hàm của `configs/pilot_dongda.yaml` + lưới H3 ⇒ **tái tạo được, 0 RNG sim**.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np                                              # noqa: E402
import yaml                                                     # noqa: E402

from gsm_sim.config import Config                                # noqa: E402
from gsm_sim.demand import expected_demand_field                 # noqa: E402
from gsm_sim.geo import build_grid, cell_distance_km, grid_disk   # noqa: E402

CFG_PATH = ROOT / "configs" / "pilot_dongda.yaml"
RC03 = Path(__file__).resolve().parent / "rc-03-overlap.json"


def _neighbors(cell: str, grid, ring: int) -> list[str]:
    """Bản sao NGUYÊN VĂN `behavior._neighbors` (chỉ ô LÕI, sorted để tất định)."""
    return sorted(c for c in grid_disk(cell, ring) if c != cell and grid.is_core(c))


def _belief(cell: str, field: dict, sigma: float, seed: int, actor: int, hour: int) -> dict:
    """Bản sao `world._actor_demand_hint`: chỉ ring ≤ 2, nhiễu per-cell keyed."""
    out = {}
    for c in sorted(grid_disk(cell, 2)):
        base = field.get(c, 0.0)
        if sigma <= 0:
            out[c] = base
        else:
            rng_c = np.random.default_rng((seed, actor, hour, int(c, 16)))
            out[c] = base * math.exp(rng_c.normal(0.0, sigma))
    return out


def _step(cell: str, grid, field: dict, *, ring: int, bar: float, give_up: bool,
          sigma: float, seed: int, actor: int, hour: int) -> str:
    """MỘT bước leo dốc theo đúng `behavior.consider_relocate` (bỏ phần `p_move`)."""
    hint = _belief(cell, field, sigma, seed, actor, hour)
    best_cell, best_val = cell, hint.get(cell, 0.0)
    for nb in _neighbors(cell, grid, ring):
        v_adj = hint.get(nb, 0.0) - 0.15 * cell_distance_km(grid, cell, nb)
        if v_adj > best_val * bar:
            best_cell, best_val = nb, v_adj
    if best_cell == cell and give_up:
        nbs = _neighbors(cell, grid, ring)
        if nbs:
            best_cell = max(nbs, key=lambda c: (hint.get(c, 0.0), c))
    return best_cell


def _attractor(start: str, grid, field: dict, *, sigma: float, seed: int, actor: int, hour: int,
               ring: int, bar: float, give_up: bool, max_steps: int = 60):
    """Đi tới khi lặp lại ⇒ trả (tập ô của attractor, số bước). Chu trình 2 ô cũng là attractor."""
    seen: list[str] = []
    cur = start
    for _ in range(max_steps):
        if cur in seen:
            return frozenset(seen[seen.index(cur):]), len(seen)
        seen.append(cur)
        nxt = _step(cur, grid, field, ring=ring, bar=bar, give_up=give_up,
                    sigma=sigma, seed=seed, actor=actor, hour=hour)
        if nxt == cur:
            return frozenset([cur]), len(seen)
        cur = nxt
    return frozenset([cur]), max_steps


def main() -> int:
    cfg = Config.load(str(CFG_PATH))
    data_dir = cfg.resolve_path("world.data_dir")
    grid = build_grid(
        geom_path=data_dir / cfg.get("world.geom_file"),
        stations_path=data_dir / cfg.get("world.stations_file"),
        poi_path=data_dir / cfg.get("world.poi_file"),
        res=int(cfg.get("world.h3_res")),
        res_report=int(cfg.get("world.h3_res_report")),
    )
    core = sorted(grid.core_cells)
    field_by_hour = expected_demand_field(grid, cfg)
    beh = cfg.get("behavior", {}) or {}
    step_min = float(beh.get("idle_impatience_step_min", 30.0))
    max_steps_cfg = int(beh.get("idle_impatience_max_steps", 2))

    # ô nhiều đơn chết — ưu tiên số ĐO ĐƯỢC từ rc-03; nếu không có thì nói rõ là dùng proxy
    expired_by_cell, nguon_expired = {}, "PROXY (cầu kỳ vọng — rc-03 không có bảng theo ô)"
    if RC03.exists():
        raw = json.loads(RC03.read_text(encoding="utf-8"))
        for k, v in _find_expired_map(raw):
            expired_by_cell, nguon_expired = v, f"ĐO (rc-03.{k})"
            break

    print(f"Lõi: {len(core)} ô res9 · giờ có cầu: {len(field_by_hour)}")
    print(f"Nguồn 'ô nhiều đơn chết': {nguon_expired}\n")

    # ---- ba bậc sốt ruột theo ĐÚNG config ----
    bac = [(0, 1, 1.25, False), (1, 2, 1.15, False), (max_steps_cfg, 1 + max_steps_cfg,
                                                      1.25 - 0.10 * max_steps_cfg, True)]
    hours = sorted(field_by_hour)
    for n, ring, bar, give_up in bac:
        km_ring = _ring_km(grid, core, ring)
        print(f"=== bậc sốt-ruột n={n} (rỗi ≥ {n * step_min:.0f}′): ring={ring} (~{km_ring:.2f} km) "
              f"· bar={bar:.2f} · give_up={give_up} ===")
        tong_basin: Counter = Counter()
        for hour in hours:
            field = field_by_hour[hour]
            basins: dict[frozenset, list[str]] = defaultdict(list)
            for c in core:
                att, _ = _attractor(c, grid, field, sigma=0.0, seed=0, actor=0, hour=hour,
                                    ring=ring, bar=bar, give_up=give_up)
                basins[att].append(c)
            for att, members in basins.items():
                tong_basin[att] += len(members)
        n_cell_hour = len(core) * len(hours)
        print(f"  số attractor khác nhau (gộp mọi giờ): {len(tong_basin)}")
        for att, size in tong_basin.most_common(5):
            lam = _demand_of(att, field_by_hour, hours)
            d_min = _min_dist_to_expired(att, grid, expired_by_cell, field_by_hour, hours)
            print(f"   · {sorted(att)}  lưu vực {size}/{n_cell_hour} = {size / n_cell_hour:5.1%}"
                  f"  · cầu TB {lam:6.2f}/ngày  · cách ô-nhiều-đơn-chết gần nhất {d_min:.2f} km")
        print()

    # ---- nhiễu per-actor có cứu được không? ----
    print("=== NHIỄU per-actor có đổi attractor không? (σ theo archetype) ===")
    n, ring, bar, give_up = bac[-1]
    hour = max(hours, key=lambda h: sum(field_by_hour[h].values()))
    for sigma in (0.0, 0.10, 0.30, 0.60):
        atts: Counter = Counter()
        for actor in range(40):
            for c in core[::7]:
                att, _ = _attractor(c, grid, field_by_hour[hour], sigma=sigma, seed=7000,
                                    actor=actor, hour=hour, ring=ring, bar=bar, give_up=give_up)
                atts[att] += 1
        top = atts.most_common(3)
        tong = sum(atts.values())
        print(f"  σ={sigma:.2f}: {len(atts)} attractor · top-3 chiếm "
              f"{sum(s for _, s in top) / tong:5.1%}" +
              "".join(f"\n      {sorted(a)} {s / tong:5.1%}" for a, s in top))
    print(f"\n(giờ dùng cho khảo sát nhiễu: {hour}h — giờ tổng cầu cao nhất)")
    return 0


def _ring_km(grid, core, ring: int) -> float:
    ds = []
    for c in core[:30]:
        for nb in _neighbors(c, grid, ring):
            ds.append(cell_distance_km(grid, c, nb))
    return max(ds) if ds else 0.0


def _demand_of(att: frozenset, field_by_hour: dict, hours: list) -> float:
    return sum(sum(field_by_hour[h].get(c, 0.0) for h in hours) for c in att) / max(1, len(att))


def _min_dist_to_expired(att: frozenset, grid, expired_by_cell: dict,
                         field_by_hour: dict, hours: list) -> float:
    if expired_by_cell:
        top = sorted(expired_by_cell, key=lambda c: -expired_by_cell[c])[:5]
    else:
        tong = Counter()
        for h in hours:
            for c, v in field_by_hour[h].items():
                tong[c] += v
        top = [c for c, _ in tong.most_common(5)]
    ds = [cell_distance_km(grid, a, t) for a in att for t in top if grid.is_core(t)]
    return min(ds) if ds else float("nan")


def _find_expired_map(raw, path=""):
    """Tìm dict {cell_h3: số} trong artifact rc-03 (khoá tên không chắc ⇒ dò theo HÌNH DẠNG)."""
    if isinstance(raw, dict):
        keys = list(raw)
        if keys and all(isinstance(k, str) and len(k) == 15 for k in keys[:5]) and \
                all(isinstance(v, (int, float)) for v in list(raw.values())[:5]):
            yield path, {k: float(v) for k, v in raw.items()}
        for k, v in raw.items():
            if "expired" in str(k).lower() or "cell" in str(k).lower() or isinstance(v, dict):
                yield from _find_expired_map(v, f"{path}.{k}" if path else str(k))


if __name__ == "__main__":
    raise SystemExit(main())
