"""Visual gate của E10 — bản đồ CUNG: advisor mất λ đẩy tài xế đi đâu khác?

    uv run python scripts/e10_visual.py [seed]      # mặc định 5000

Sinh HTML self-contained (SVG thuần, không CDN) tại
`research/audit/2026-07-27-current-state/41-e10-visual-map.html`:
- 3 bản đồ H3: World A (không advice) · B_oracle (λ config) · B_real (λ̂ realized)
- 1 bản đồ HIỆU B_real − B_oracle: đỏ = realized dồn NHIỀU hơn, xanh = ÍT hơn
- Màu = tài xế-phút IDLE trong ô (mật độ CUNG đứng chờ), đọc từ event probe log-only.

Vì sao đo cung IDLE chứ không phải pickup: câu hỏi của visual gate là *advisor đẩy người
đi đâu*, không phải *khách ở đâu* (cầu do generator quyết, không đổi giữa các arm — CRN).

MỌI SỐ LÀ MOCK (`configs/pilot_dongda.yaml`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import h3

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with
from gsm_sim.runner import Config, run_once

OUT = Path("research/audit/2026-07-27-current-state")
PREREG = Path("specs/simulation/e10-prereg-locked.json")


def _idle_minutes(events) -> dict[str, float]:
    """Tài xế-phút IDLE per ô, từ event probe (log-only, chu kỳ 60′)."""
    out: dict[str, float] = {}
    for e in events:
        if e.kind != "probe_wait_stats":
            continue
        for cell, (n, _med) in e.detail["cells"].items():
            out[cell] = out.get(cell, 0.0) + float(n) * 60.0
    return out


def _run(over: dict | None, enabled: bool, seed: int):
    import copy
    base = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(base.data), base.root_dir)
    if over:
        c.data.setdefault("advice", {}).update(copy.deepcopy(over))
    c.data["probe"] = {"wait_stats": True}
    cfg = _cfg_with(c, enabled=enabled, actor_id=None,
                    channels=CHANNEL_LADDER["positioning"] if enabled else None,
                    coverage="all")
    return run_once(cfg, seed)


def _svg(cells: list[str], values: dict[str, float], *, diverging: bool,
         width: int = 420, height: int = 380) -> str:
    """H3 → SVG polygon. Mercator thô là đủ ở quy mô một quận."""
    pts = {c: h3.cell_to_boundary(c) for c in cells}
    lats = [p[0] for b in pts.values() for p in b]
    lons = [p[1] for b in pts.values() for p in b]
    lat0, lat1, lon0, lon1 = min(lats), max(lats), min(lons), max(lons)
    pad = 8

    def xy(lat, lon):
        x = pad + (lon - lon0) / (lon1 - lon0) * (width - 2 * pad)
        y = pad + (lat1 - lat) / (lat1 - lat0) * (height - 2 * pad)
        return f"{x:.1f},{y:.1f}"

    vs = [v for v in values.values() if v]
    vmax = max((abs(v) for v in vs), default=1.0) or 1.0
    body = []
    for c in cells:
        v = values.get(c, 0.0)
        t = abs(v) / vmax
        if diverging:
            # đỏ = realized dồn NHIỀU hơn oracle · xanh = ít hơn
            col = (f"rgba(220,60,60,{0.12 + 0.78 * t:.2f})" if v > 0
                   else (f"rgba(40,130,200,{0.12 + 0.78 * t:.2f})" if v < 0
                         else "rgba(140,140,140,0.10)"))
        else:
            col = f"rgba(0,150,120,{0.10 + 0.80 * t:.2f})"
        poly = " ".join(xy(la, lo) for la, lo in pts[c])
        body.append(f'<polygon points="{poly}" fill="{col}" stroke="rgba(120,120,120,.25)" '
                    f'stroke-width=".5"><title>{c}: {v:,.0f}</title></polygon>')
    return (f'<svg viewBox="0 0 {width} {height}" width="100%" '
            f'style="max-width:{width}px;height:auto">{"".join(body)}</svg>')


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    locked = json.loads(PREREG.read_text(encoding="utf-8"))
    k = locked["k_star"]
    print(f"seed {seed} · k*={k} — chạy 3 arm…", flush=True)

    rA = _run(None, False, seed)
    rO = _run({}, True, seed)
    rR = _run({"market_demand_source": "realized",
               "realized_demand": {"window_buckets": k,
                                   "min_pickups": locked["min_pickups"]}}, True, seed)
    print("  xong 3 run, dựng bản đồ…", flush=True)

    cells = sorted(rA.grid.core_cells)
    mA, mO, mR = (_idle_minutes(r.events) for r in (rA, rO, rR))
    diff = {c: mR.get(c, 0.0) - mO.get(c, 0.0) for c in cells}
    tot = lambda m: sum(m.values())
    hhi = lambda m: (sum((v / (tot(m) or 1)) ** 2 for v in m.values()))
    moved = sum(abs(v) for v in diff.values()) / 2

    diff_art = json.loads((OUT / "41-e10-diff.json").read_text(encoding="utf-8"))
    from e10_visual_render import render
    html = render(seed=seed, k=k,
                  svg_a=_svg(cells, mA, diverging=False),
                  svg_o=_svg(cells, mO, diverging=False),
                  svg_r=_svg(cells, mR, diverging=False),
                  svg_diff=_svg(cells, diff, diverging=True),
                  tot_a=tot(mA), tot_o=tot(mO), tot_r=tot(mR),
                  hhi_a=hhi(mA), hhi_o=hhi(mO), hhi_r=hhi(mR),
                  moved=moved, diff_art=diff_art)
    out = OUT / "41-e10-visual-map.html"
    out.write_text(html, encoding="utf-8")
    print(f"-> {out}")
    print(f"HHI cung: A {hhi(mA):.4f} · oracle {hhi(mO):.4f} · real {hhi(mR):.4f} · "
          f"dịch chuyển {moved:,.0f} tài xế-phút")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
