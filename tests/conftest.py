"""E5 (UPDATE-158) — cache run sim SESSION-SCOPED theo phán quyết trọng tài lọc-test (r13).

113 call-site `run_once/run_multiday` trùng lặp xuyên file là nguồn thời gian suite lớn nhất.
Cache theo (fingerprint config, seed) với BA ĐIỀU KIỆN CỨNG của phán quyết:

  1. **Trả DEEPCOPY** — test mutate kết quả không được đầu độc test khác (mutation thật đã đo
     ở test_lifecycle_review_fixes dòng 275/294).
  2. **Cặp determinism/exact-repeat giữ ≥ 1 run TƯƠI** — hai vế cùng lấy từ cache là so cache
     với chính nó, cổng tất định thành vô dụng. Fixture này KHÔNG được dùng cho cả hai vế
     (test_run_smoke giữ nguyên cặp gốc, ngoài cache).
  3. **`test_parallel_worlds` đứng NGOÀI cache hoàn toàn** — máy đo A/B (CRN, draw-count,
     arm A untouched) phải chạy run độc lập.

Dùng: test NHẬN fixture `cached_run_once` rồi gọi `cached_run_once(cfg, seed)` — file nào
chưa chuyển thì hành vi giữ nguyên (conftest chỉ THÊM fixture, không đổi test cũ).
"""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

_CACHE: dict = {}


def _cfg_fingerprint(cfg) -> str:
    try:
        blob = json.dumps(cfg.data, sort_keys=True, default=str)
    except Exception:                      # config chứa thứ không serialize được ⇒ không cache
        return f"nocache-{id(cfg)}"
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


@pytest.fixture(scope="session")
def cached_run_once():
    """`get(cfg, seed) -> RunResult` (DEEPCOPY từ cache session)."""
    from gsm_sim.runner import run_once

    def get(cfg, seed: int):
        key = ("once", _cfg_fingerprint(cfg), int(seed))
        if key not in _CACHE:
            _CACHE[key] = run_once(cfg, seed)
        return copy.deepcopy(_CACHE[key])

    return get


@pytest.fixture(scope="session")
def cached_run_multiday():
    """`get(cfg, seed, days) -> MultiDayResult` (DEEPCOPY từ cache session)."""
    from gsm_sim.multiday import run_multiday

    def get(cfg, seed: int, days: int):
        key = ("md", _cfg_fingerprint(cfg), int(seed), int(days))
        if key not in _CACHE:
            _CACHE[key] = run_multiday(cfg, seed, days=days)
        return copy.deepcopy(_CACHE[key])

    return get
