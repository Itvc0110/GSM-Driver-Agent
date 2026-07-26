"""AUDIT A2 (UPDATE-066) — mở rộng gate schema: nhất quán KIỂU + khoá ngoại giữa bảng.

Gate cũ (`test_schema_matches_gsm_spec.py`) chỉ kiểm tên bảng + tên/thứ tự cột —
KHÔNG kiểm kiểu dữ liệu, nullability, hay quan hệ giữa bảng. Lỗ đó nghĩa là generator
có thể đổi kiểu một cột (int→str) hoặc sinh mission_id mồ côi mà không test nào đỏ.

Giới hạn TRUNG THỰC: metadata GSM Cường cấp KHÔNG kèm dtype/nullability chính thức
⇒ gate này chỉ ép NHẤT QUÁN NỘI BỘ (kiểu ổn định giữa các dòng, khoá không null,
khoá ngoại không mồ côi) — không thay được so khớp dtype với bảng thật (data gap,
ghi trong research/audit/2026-07-26-full-audit/README.md).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.mockgen.realdata import generate_realdata

# (bảng, cột khoá KHÔNG được null/rỗng)
KEY_COLS = {
    "driver_statistic_daily": ["driver_id", "local_date"],
    "driver_income_daily": ["driver_id", "order_date"],
    "driver_online_hours_sap_id": ["driver_id", "local_date"],
    "trips": ["trip_id", "driver_id", "request_time"],
    "public_mission": ["id"],
    "public_mission_earn_history": ["id", "mission_id", "driver_id"],
    "public_user_mission_progress": ["id", "mission_id", "driver_id"],
}


@pytest.fixture(scope="module")
def tables():
    with TemporaryDirectory() as td:
        return generate_realdata(days=8, seed_base=555, out_dir=Path(td))["tables"]


def test_column_types_stable_across_rows(tables):
    """Kiểu mỗi cột phải ỔN ĐỊNH trong toàn bảng (cho phép None lẫn 1 kiểu thật —
    int/float coi là một họ số). Kiểu trôi giữa dòng = consumer polars/BQ vỡ ngầm."""
    for name, rows in tables.items():
        if not rows:
            continue
        types: dict[str, set] = {}
        for r in rows:
            for col, v in r.items():
                if v is None:
                    continue
                t = float if isinstance(v, bool) is False and isinstance(v, (int, float)) else type(v)
                types.setdefault(col, set()).add(t)
        bad = {c: ts for c, ts in types.items() if len(ts) > 1}
        assert not bad, f"{name}: cột đổi kiểu giữa các dòng: {bad}"


def test_key_columns_never_null(tables):
    for name, cols in KEY_COLS.items():
        for i, r in enumerate(tables[name]):
            for c in cols:
                assert r.get(c) not in (None, ""), f"{name}[{i}].{c} null/rỗng — khoá bảng"


def test_mission_foreign_keys_not_orphaned(tables):
    """earn_history / progress phải trỏ về mission CÓ THẬT trong catalog."""
    mission_ids = {r["id"] for r in tables["public_mission"]}
    for tbl in ("public_mission_earn_history", "public_user_mission_progress"):
        orphans = {r["mission_id"] for r in tables[tbl]} - mission_ids
        assert not orphans, f"{tbl}: mission_id mồ côi: {sorted(orphans)[:5]}"


def test_driver_ids_consistent_across_tables(tables):
    """driver_id ở bảng phụ phải là tập con universe (statistic_daily — bảng gốc)."""
    universe = {r["driver_id"] for r in tables["driver_statistic_daily"]}
    for tbl in ("driver_income_daily", "driver_online_hours_sap_id", "trips",
                "public_mission_earn_history", "public_user_mission_progress"):
        extra = {r["driver_id"] for r in tables[tbl]} - universe
        assert not extra, f"{tbl}: driver_id lạ không có trong universe: {sorted(extra)[:5]}"


def test_trips_reference_valid_dates_and_money(tables):
    """trips: gross > 0, commission ≤ gross (driver_share ≤ 1), thời gian tăng dần."""
    for r in tables["trips"][:2000]:
        assert r["gross_vnd"] > 0
        assert 0 <= r["commission_vnd"] <= r["gross_vnd"]
        assert r["request_time"] <= r["complete_time"], "cuốc xong trước khi đặt"
