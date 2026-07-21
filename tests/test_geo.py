"""Test lớp không gian: polyfill H3, nạp trạm/POI, phép toán lưới."""

from pathlib import Path

import pytest

from gsm_sim import geo

DATA = Path(__file__).resolve().parent.parent / "research" / "simulation" / "data"


@pytest.fixture(scope="module")
def grid():
    return geo.build_grid(
        geom_path=DATA / "dd_geom.json",
        stations_path=DATA / "batt_dd.json",
        poi_path=DATA / "poi_dd.json",
        res=9,
        res_report=8,
    )


def test_core_cells_count(grid):
    # Research: ~85 cells lõi res 9 (dải chấp nhận rộng vì phụ thuộc thư viện polyfill)
    assert 60 <= len(grid.core_cells) <= 130, len(grid.core_cells)


def test_stations_loaded(grid):
    # 11 tủ pin Đống Đa
    assert len(grid.stations) == 11
    # phần lớn trạm nằm trong hoặc sát lõi
    in_core = sum(1 for s in grid.stations if grid.is_core(s.cell))
    assert in_core >= 8, in_core


def test_pois_loaded(grid):
    kinds = {}
    for p in grid.pois:
        kinds[p.kind] = kinds.get(p.kind, 0) + 1
    assert kinds.get("hospital", 0) >= 20, kinds
    assert kinds.get("university", 0) >= 10, kinds


def test_grid_distance_symmetric(grid):
    a, b = grid.core_cells[0], grid.core_cells[len(grid.core_cells) // 2]
    assert geo.grid_distance(a, b) == geo.grid_distance(b, a)
    assert geo.grid_distance(a, a) == 0


def test_cell_distance_km(grid):
    a, b = grid.core_cells[0], grid.core_cells[-1]
    d = geo.cell_distance_km(grid, a, b)
    # Đống Đa rộng ~3-4 km → khoảng cách 2 cell xa nhất phải hợp lý
    assert 0.0 < d < 8.0, d
    assert geo.cell_distance_km(grid, a, a) == 0.0
