"""AUDIT STATS-3/BEHAV-4 (UPDATE-069) — công thức realized-cap của sweep phải bám anchor ĐO."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("run_sensitivity", ROOT / "scripts" / "run_sensitivity.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


def test_realized_cap_matches_measured_anchor():
    """Anchor config: max_realized_accept=0.93 tại P4 lift=0.15 (nominal 0.95).
    Công thức cũ 0.80+lift+0.03 cho 0.98 tại đúng ô này — sai chiều anchor."""
    assert rs.realized_cap("P4", 0.15) == 0.93


def test_realized_cap_uses_archetype_base():
    """P2 base 0.95 — công thức cũ hardcode 0.80 làm cap của P2 THẤP hơn cả base."""
    assert rs.realized_cap("P2", 0.10) > 0.95
    assert rs.realized_cap("P1", 0.10) == 0.93
    assert rs.realized_cap("P2", 0.19) == 0.98  # kẹp trần


def test_realized_cap_below_nominal():
    for arch in ("P1", "P2", "P4"):
        for lift in (0.10, 0.15, 0.19):
            nominal = rs.BASE_BY_ARCHETYPE[arch] + lift
            assert rs.realized_cap(arch, lift) <= min(0.98, nominal), \
                "realized cap không được LẠC QUAN hơn nominal (bài học BEHAV-4)"
