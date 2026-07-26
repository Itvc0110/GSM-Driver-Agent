"""SIM-XANH Phase 1 — fetch ma trận đường THẬT (OSRM /table) cho mọi cell của sim.

    uv run python scripts/fetch_osrm_matrix.py

Chạy MỘT LẦN (cần mạng) → ghi `research/simulation/data/osrm_matrix_dd.parquet`
(cell_from, cell_to, road_km, duration_s). Sim/test sau đó đọc file này **offline** —
đúng nguyên tắc DIRECTIVES §2: external chỉ fetch-rồi-cache, không bao giờ gọi mạng
trong đường chạy chính.

Vì sao: sim đang xấp xỉ mọi quãng đường = haversine × detour 1.3 (một hằng cho cả quận).
Đường thật Hà Nội không đồng nhất — qua hồ/đường một chiều/ngõ, detour thực dao động mạnh
theo cặp điểm. OSRM (OSM data, không cần key) cho khoảng cách + thời gian lái THẬT.

Server: `OSRM_BASE_URL` trong .env (mặc định https://router.project-osrm.org — demo public,
giới hạn lịch sự: chunk nhỏ + nghỉ giữa các request).
"""

from __future__ import annotations

import os
import sys
import time
import urllib.request
import json as _json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import h3                                  # noqa: E402
import polars as pl                        # noqa: E402

from gsm_sim.config import Config          # noqa: E402
from gsm_sim.geo import build_grid         # noqa: E402
from gsm_sim.runner import _data           # noqa: E402

OUT = ROOT / "research" / "simulation" / "data" / "osrm_matrix_dd.parquet"
CHUNK = 50                                 # 50 nguồn × 50 đích / request — URL ngắn, demo chịu được
SLEEP_S = 0.7                              # lịch sự với server public


def cells_and_points() -> tuple[list[str], list[tuple[float, float]]]:
    cfg = Config.load(ROOT / "configs" / "pilot_dongda.yaml")
    grid = build_grid(geom_path=_data(cfg, "geom_file"), stations_path=_data(cfg, "stations_file"),
                      poi_path=_data(cfg, "poi_file"), res=int(cfg.get("world.h3_res")),
                      res_report=int(cfg.get("world.h3_res_report")))
    cells: set[str] = set(grid.core_cells)
    for c in grid.core_cells:
        cells |= set(h3.grid_disk(c, int(cfg.get("world.buffer_ring_k", 4))))
    ordered = sorted(cells)
    pts = []
    for c in ordered:
        lat, lon = grid.cell_centroid.get(c) or h3.cell_to_latlng(c)
        pts.append((lat, lon))
    return ordered, pts


def fetch_block(base: str, src_pts, dst_pts):
    coords = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in list(src_pts) + list(dst_pts))
    ns = len(src_pts)
    srcs = ";".join(str(i) for i in range(ns))
    dsts = ";".join(str(ns + i) for i in range(len(dst_pts)))
    url = (f"{base}/table/v1/driving/{coords}"
           f"?sources={srcs}&destinations={dsts}&annotations=distance,duration")
    with urllib.request.urlopen(url, timeout=60) as r:
        obj = _json.loads(r.read().decode("utf-8"))
    if obj.get("code") != "Ok":
        raise RuntimeError(f"OSRM: {obj.get('code')} {obj.get('message')}")
    return obj["distances"], obj["durations"]


def main() -> None:
    base = os.environ.get("OSRM_BASE_URL", "https://router.project-osrm.org").rstrip("/")
    cells, pts = cells_and_points()
    n = len(cells)
    n_chunks = (n + CHUNK - 1) // CHUNK
    print(f"{n} cell → {n_chunks * n_chunks} request (chunk {CHUNK}) tới {base}")

    rows_from, rows_to, rows_km, rows_s = [], [], [], []
    done = 0
    for bi in range(n_chunks):
        s0, s1 = bi * CHUNK, min((bi + 1) * CHUNK, n)
        for bj in range(n_chunks):
            d0, d1 = bj * CHUNK, min((bj + 1) * CHUNK, n)
            for attempt in range(3):
                try:
                    dist, dur = fetch_block(base, pts[s0:s1], pts[d0:d1])
                    break
                except Exception as e:              # retry có backoff — mạng public
                    if attempt == 2:
                        raise
                    print(f"  retry ({e})"); time.sleep(3 * (attempt + 1))
            for i, ci in enumerate(cells[s0:s1]):
                for j, cj in enumerate(cells[d0:d1]):
                    d_m, t_s = dist[i][j], dur[i][j]
                    if d_m is None or t_s is None:
                        continue                     # OSRM không nối được (hiếm) → sim fallback
                    rows_from.append(ci); rows_to.append(cj)
                    # ép float TƯỜNG MINH: OSRM trả lẫn int/float; round(int,1) giữ int
                    # → polars strict nổ khi build Series (đã dính, đừng lặp lại)
                    rows_km.append(float(round(d_m / 1000.0, 4)))
                    rows_s.append(float(round(float(t_s), 1)))
            done += 1
            if done % 10 == 0:
                print(f"  {done}/{n_chunks * n_chunks} block")
            time.sleep(SLEEP_S)

    df = pl.DataFrame({"cell_from": rows_from, "cell_to": rows_to,
                       "road_km": rows_km, "duration_s": rows_s})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUT)
    print(f"\nghi {df.height:,} cặp → {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")
    print(f"thiếu (OSRM không nối được): {n*n - df.height:,} cặp — sim sẽ fallback haversine×detour")


if __name__ == "__main__":
    main()
