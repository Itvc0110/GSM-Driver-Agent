"""E2 — arm oracle-adherence: các bẫy đã khai trước phải có cổng (UPDATE-151 r04).

Nhẹ (không chạy sim): kiểm cấu trúc script + bẫy ORACLE-03 + AST chống lối tắt.
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_oracle_adherence.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_oracle_adherence", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_oracle_03_override_tren_cfg_goc():
    """Bẫy ORACLE-03: nominal_adherence(cfg_oracle) PHẢI thấy 1.0 — override lệch chỗ là cổng
    |z|>4 treo oan (mẫu D-R20)."""
    mod = _load()
    from gsm_sim.config import Config
    from gsm_sim.parallel import nominal_adherence
    orc = mod.cfg_oracle(Config.load(str(ROOT / "configs/pilot_dongda.yaml")))
    nom = nominal_adherence(orc)
    assert nom and all(v == 1.0 for v in nom.values()), nom


def test_khong_sua_default_adherence():
    """Đường rẻ nhất là override CONFIG, không phải sửa DEFAULT_ADHERENCE (khoá config tồn tại
    để được đổi — docstring nominal_adherence). AST: script không gán DEFAULT_ADHERENCE."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                assert not (isinstance(t, ast.Attribute) and t.attr == "DEFAULT_ADHERENCE"), \
                    "script sửa DEFAULT_ADHERENCE — sai đường (ORACLE-02)"


def test_oracle_du_7_archetype():
    mod = _load()
    assert set(mod.ORACLE) == {f"P{i}" for i in range(1, 8)}
    assert all(v == 1.0 for v in mod.ORACLE.values())


def test_min_seeds_variant_100_duoc_ton_trong():
    """diff-of-diff là so BIẾN-THỂ-vs-BIẾN-THỂ ⇒ significant phải gate ở
    MIN_SEEDS_FOR_VARIANT_COMPARISON (100), không phải 30."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "MIN_SEEDS_FOR_VARIANT_COMPARISON" in src
    assert "len(dod) >= ms" in src
