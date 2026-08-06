"""E5 — cổng cho chính cache conftest: 3 điều kiện cứng của phán quyết r13 phải THẬT.

Mutation phải bắt được: cache trả CÙNG OBJECT (bỏ deepcopy) ⇒ test cô lập đỏ.
"""
from __future__ import annotations

from gsm_sim.config import Config


def test_cache_tra_deepcopy_khong_cung_object(cached_run_once):
    cfg = Config.load("configs/pilot_dongda.yaml")
    r1 = cached_run_once(cfg, 4400)
    r2 = cached_run_once(cfg, 4400)
    assert r1 is not r2, "cache trả cùng object — test mutate sẽ đầu độc test khác"
    assert r1.actors is not r2.actors
    # cùng NỘI DUNG (cache đúng nghĩa)
    from gsm_sim.sim_metrics import fingerprint_actors
    assert fingerprint_actors(r1) == fingerprint_actors(r2)
    # mutate bản 1 không lây bản 3
    r1.actors[0].payout_vnd = -1.0
    r3 = cached_run_once(cfg, 4400)
    assert r3.actors[0].payout_vnd != -1.0, "mutation lây qua cache — thiếu deepcopy"


def test_cache_phan_biet_config(cached_run_once):
    import copy as _c
    base = Config.load("configs/pilot_dongda.yaml")
    c2 = Config(_c.deepcopy(base.data), base.root_dir)
    c2.data["actors"]["n"] = int(base.get("actors.n")) - 5
    r_a = cached_run_once(base, 4401)
    r_b = cached_run_once(c2, 4401)
    assert len(r_a.actors) != len(r_b.actors), "hai config khác nhau bị gộp một khoá cache"


def test_parallel_worlds_khong_dung_cache():
    """Điều kiện cứng #3: máy đo A/B phải chạy run độc lập — file đó không được nhận fixture."""
    import pathlib

    src = (pathlib.Path(__file__).parent / "test_parallel_worlds.py").read_text(encoding="utf-8")
    assert "cached_run_once" not in src and "cached_run_multiday" not in src
