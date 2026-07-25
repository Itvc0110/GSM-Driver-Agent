"""GATE — mock l1r phải khớp CHÍNH XÁC metadata GSM Cường cung cấp (2026-07-24).

Không để trôi schema: tên bảng (đúng tên thật), SỐ cột, TÊN cột, THỨ TỰ cột.
Cột meta của ta (`schema_version`, `source`) là chủ ý §5 (nhãn nguồn mock) — tách riêng.
SPEC lấy từ `gsm_core.mockgen.gsm_spec` (MỘT nguồn sự thật, dùng chung với script audit).
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.schema_registry import L1R_ENTITIES
from gsm_core.mockgen.gsm_spec import SPEC, META_COLS

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def tables():
    with TemporaryDirectory() as td:
        return generate_realdata(days=8, seed_base=700, out_dir=Path(td))["tables"]


def test_all_13_entities_named_exactly_like_gsm():
    """Tên entity = tên bảng thật (vd public_mission, KHÔNG phải mission_catalog)."""
    spec_entities = {ent for ent, _ in SPEC.values()}
    assert len(spec_entities) == 13
    assert set(L1R_ENTITIES) == spec_entities, (
        f"lệch: thiếu={spec_entities - set(L1R_ENTITIES)}, thừa={set(L1R_ENTITIES) - spec_entities}")


@pytest.mark.parametrize("full_path", sorted(SPEC))
def test_columns_match_spec_exactly(tables, full_path):
    """Cột nghiệp vụ phải khớp spec: đủ, không thừa, ĐÚNG THỨ TỰ."""
    entity, spec_cols = SPEC[full_path]
    rows = tables.get(entity)
    assert rows is not None, f"{entity} không được sinh"
    if spec_cols is None:
        pytest.skip(f"{entity}: spec chưa có cột (ENGINEER)")
    assert rows, f"{entity} rỗng — không kiểm được cột"
    biz = [c for c in rows[0] if c not in META_COLS]
    assert biz == spec_cols, (
        f"{entity}: thiếu={[c for c in spec_cols if c not in biz]} "
        f"thừa={[c for c in biz if c not in spec_cols]} (hoặc sai thứ tự)")


def test_meta_columns_present_and_labeled(tables):
    """Mọi bảng có đúng 2 cột meta của ta + record gắn nhãn nguồn hợp lệ (§5)."""
    valid = {"MOCK", "REAL", "ESTIMATED", "COARSE", "INFERRED"}
    for entity, rows in tables.items():
        if not rows:
            continue
        assert META_COLS <= set(rows[0]), f"{entity} thiếu cột meta"
        assert rows[0]["source"] in valid, f"{entity} nhãn nguồn lạ: {rows[0]['source']}"
