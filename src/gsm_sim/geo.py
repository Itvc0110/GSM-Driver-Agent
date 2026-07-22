"""Lớp không gian: nạp dữ liệu OSM (polygon phường, trạm pin, POI), polyfill H3,
và các phép toán lưới. API h3 v4 (snake_case).

Nguồn dữ liệu: research/simulation/data/ (OSM Overpass, ODbL, snapshot 2026-07-21).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import h3
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import polygonize, unary_union

# --- Kiểu dữ liệu ---


@dataclass(frozen=True)
class Station:
    node_id: int
    lat: float
    lon: float
    cell: str


@dataclass(frozen=True)
class Poi:
    lat: float
    lon: float
    kind: str  # hospital/university/college/marketplace/bus_station/mall/...
    cell: str


@dataclass
class Grid:
    """Lưới H3 của khu vực pilot."""

    res: int
    res_report: int
    core_cells: list[str]  # cells lõi (tâm trong polygon)
    core_set: frozenset[str]
    boundary: MultiPolygon
    stations: list[Station]
    pois: list[Poi]
    cell_centroid: dict[str, tuple[float, float]] = field(default_factory=dict)
    pois_by_cell: dict[str, list[Poi]] = field(default_factory=dict)

    def is_core(self, cell: str) -> bool:
        return cell in self.core_set

    def parent_report(self, cell: str) -> str:
        return h3.cell_to_parent(cell, self.res_report)


# --- Nạp OSM ---


def _osm_relation_to_polygon(element: dict) -> Polygon | MultiPolygon | None:
    """Ghép các way 'outer' của một relation boundary thành polygon.

    Overpass `out geom`: mỗi member way có 'geometry' = list {lat, lon}. Các way
    outer là những ĐOẠN rời (thường 2 điểm) phải nối lại thành ring — dùng
    shapely.polygonize trên tập LineString.
    """
    segments: list[LineString] = []
    for m in element.get("members", []):
        if m.get("type") != "way" or m.get("role") not in ("outer", ""):
            continue
        geom = m.get("geometry")
        if not geom or len(geom) < 2:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in geom]
        segments.append(LineString(coords))
    if not segments:
        return None
    # nối các đoạn thành polygon
    merged_lines = unary_union(segments)
    polys = list(polygonize(merged_lines))
    if not polys:
        return None
    merged = unary_union([p.buffer(0) for p in polys if p.area > 0])
    if merged.is_empty:
        return None
    return merged


def load_boundary(geom_path: Path) -> MultiPolygon:
    """Nạp polygon khu vực = hợp các relation phường trong file."""
    data = json.loads(geom_path.read_text(encoding="utf-8"))
    polys: list[Polygon] = []
    for el in data.get("elements", []):
        if el.get("type") != "relation":
            continue
        poly = _osm_relation_to_polygon(el)
        if poly is None:
            continue
        if isinstance(poly, MultiPolygon):
            polys.extend(list(poly.geoms))
        else:
            polys.append(poly)
    if not polys:
        raise ValueError(f"Không dựng được polygon từ {geom_path}")
    merged = unary_union(polys)
    if isinstance(merged, Polygon):
        return MultiPolygon([merged])
    return merged


def _load_points(path: Path) -> list[tuple[float, float, dict]]:
    """Trả (lat, lon, tags) cho mọi element định vị được: node (lat/lon) hoặc
    way/relation có 'center' (Overpass `out center`)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[tuple[float, float, dict]] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            out.append((float(el["lat"]), float(el["lon"]), tags))
        elif "center" in el:
            c = el["center"]
            out.append((float(c["lat"]), float(c["lon"]), tags))
    return out


def _poi_kind(tags: dict) -> str | None:
    amenity = tags.get("amenity")
    if amenity in ("hospital", "university", "college", "marketplace", "bus_station"):
        return amenity
    if tags.get("shop") == "mall":
        return "mall"
    return None


# --- Polyfill H3 ---


def _polygon_to_cells(poly: Polygon, res: int) -> set[str]:
    """h3shape_to_cells: các cell có tâm trong polygon (mọi ring outer/holes)."""
    exterior = [(lat, lng) for lng, lat in poly.exterior.coords]
    holes = [[(lat, lng) for lng, lat in interior.coords] for interior in poly.interiors]
    h3shape = h3.LatLngPoly(exterior, *holes)
    return set(h3.h3shape_to_cells(h3shape, res))


def build_grid(
    geom_path: Path,
    stations_path: Path,
    poi_path: Path,
    res: int,
    res_report: int,
) -> Grid:
    boundary = load_boundary(geom_path)

    core: set[str] = set()
    for poly in boundary.geoms:
        core |= _polygon_to_cells(poly, res)

    centroid: dict[str, tuple[float, float]] = {}
    for c in core:
        lat, lng = h3.cell_to_latlng(c)
        centroid[c] = (lat, lng)

    stations: list[Station] = []
    st_data = json.loads(stations_path.read_text(encoding="utf-8"))
    for n in st_data.get("elements", []):
        if n.get("type") != "node":
            continue
        lat, lon = float(n["lat"]), float(n["lon"])
        cell = h3.latlng_to_cell(lat, lon, res)
        stations.append(Station(node_id=int(n["id"]), lat=lat, lon=lon, cell=cell))
        centroid.setdefault(cell, h3.cell_to_latlng(cell))

    pois: list[Poi] = []
    for lat, lon, tags in _load_points(poi_path):
        kind = _poi_kind(tags)
        if kind is None:
            continue
        cell = h3.latlng_to_cell(lat, lon, res)
        pois.append(Poi(lat=lat, lon=lon, kind=kind, cell=cell))
        centroid.setdefault(cell, h3.cell_to_latlng(cell))

    pois_by_cell: dict[str, list[Poi]] = {}
    for p in pois:
        pois_by_cell.setdefault(p.cell, []).append(p)

    return Grid(
        res=res,
        res_report=res_report,
        core_cells=sorted(core),
        core_set=frozenset(core),
        boundary=boundary,
        stations=stations,
        pois=pois,
        cell_centroid=centroid,
        pois_by_cell=pois_by_cell,
    )


# --- Phép toán lưới ---


def grid_distance(a: str, b: str) -> int:
    """Số bước H3 giữa 2 cell (đối xứng). Trả -1 nếu không nối được."""
    try:
        return h3.grid_distance(a, b)
    except Exception:
        return -1


def grid_disk(cell: str, k: int) -> list[str]:
    return list(h3.grid_disk(cell, k))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def cell_distance_km(grid: Grid, a: str, b: str) -> float:
    """Khoảng cách xấp xỉ giữa 2 cell theo centroid (haversine)."""
    if a == b:
        return 0.0
    la = grid.cell_centroid.get(a) or h3.cell_to_latlng(a)
    lb = grid.cell_centroid.get(b) or h3.cell_to_latlng(b)
    return haversine_km(la[0], la[1], lb[0], lb[1])


# --- Toạ độ liên tục trong cell (hybrid lat/lng, cho movement + visualize) ---

_KM_PER_DEG_LAT = 110.574
_EDGE_KM_CACHE: dict[int, float] = {}


def _cell_inradius_km(res: int) -> float:
    """Bán kính an toàn để sample điểm trong cell H3 res. Apothem = edge·√3/2; lấy
    hệ số nhỏ hơn (0.72) chừa biên cho sai số xấp xỉ phẳng + cell H3 không đều tuyệt đối."""
    if res not in _EDGE_KM_CACHE:
        _EDGE_KM_CACHE[res] = float(h3.average_hexagon_edge_length(res, unit="km"))
    return _EDGE_KM_CACHE[res] * 0.72


def offset_latlng(lat: float, lon: float, dx_km: float, dy_km: float) -> tuple[float, float]:
    """Dời (lat,lon) đi (dx_km đông, dy_km bắc). Xấp xỉ phẳng — đủ ở quy mô cell."""
    dlat = dy_km / _KM_PER_DEG_LAT
    dlon = dx_km / (111.320 * math.cos(math.radians(lat)) or 1e-9)
    return lat + dlat, lon + dlon


def sample_point_in_cell(grid: Grid, cell: str, rng, poi_bias: float = 0.5,
                         poi_jitter_km: float = 0.025) -> tuple[float, float]:
    """Sinh 1 điểm (lat,lon) "địa chỉ thực" trong cell.

    Với xác suất poi_bias và cell có POI → snap về 1 POI (jitter nhỏ, giống điểm đón/trả
    thật quanh bệnh viện/trường/chợ). Ngược lại: điểm ngẫu nhiên trong đĩa bán kính nội
    tiếp quanh centroid (đảm bảo nằm trong hexagon). rng = numpy Generator (deterministic)."""
    pois = grid.pois_by_cell.get(cell)
    if pois and rng.random() < poi_bias:
        p = pois[rng.integers(len(pois))]
        r = poi_jitter_km * math.sqrt(rng.random())
        th = 2 * math.pi * rng.random()
        return offset_latlng(p.lat, p.lon, r * math.cos(th), r * math.sin(th))
    clat, clon = grid.cell_centroid.get(cell) or h3.cell_to_latlng(cell)
    r = _cell_inradius_km(grid.res) * math.sqrt(rng.random())
    th = 2 * math.pi * rng.random()
    return offset_latlng(clat, clon, r * math.cos(th), r * math.sin(th))
