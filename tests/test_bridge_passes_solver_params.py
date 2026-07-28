"""BUG-S2-PARAMS — bridge phải truyền tham số THẬT cho `shift_dp`, không để solver đoán.

Hồ sơ: `research/audit/2026-07-27-current-state/10-bug-bucket-min-khong-truyen.md`.

`advice_bridge.consult` gọi `shift_dp.solve(spi, self.policy)` **không có `params`** ⇒ solver rơi
về `DEFAULT_PARAMS`, trong đó `bucket_min = 30` — trong khi bridge dựng bucket **60 phút**. DP vì
thế tin pin bền gấp đôi và nghỉ bắt buộc chỉ còn một nửa, nên nghiệm lệch hẳn về "cứ ONLINE".
Đo được: **18/25 tài xế đổi lịch**, chiều `OOO` → `OOR`.

`DEFAULT_PARAMS` còn tự ghi *"CALLER NÊN TRUYỀN số thật"* cho `p_accept` (S2-4) và `avg_dist_km`
(S2-5); và khi thiếu `acceptance_rate`/`completion_rate` thì `_bonus_eligible` trả
`(True, False)` = **luôn coi như đủ điều kiện thưởng** dù sim biết thừa tỷ lệ thật.

Test bắt ở mức **caller** — test của solver đã xanh sẵn (nó nhận đúng tham số được truyền), đúng
lý do bug sống sót; cũng là lý do mutation MUT10 sống sót (không đường chạy nào dùng `≠ 30`).
"""

from __future__ import annotations

import copy

import pytest

from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.config import Config
from gsm_sim.policy import PolicyBundle as SimPolicy
from gsm_sim.runner import run_once

SEED = 1000


@pytest.fixture(scope="module")
def env():
    cfg = Config.load("configs/pilot_dongda.yaml")
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c.data["advice"].update(enabled=True, coverage="all")
    return run_once(c, SEED), c, SimPolicy.from_config(cfg)


def _capture_params(monkeypatch):
    """Bắt `params` mà bridge truyền cho solver (test HÀNH VI, không soi source)."""
    from gsm_core.solvers import shift_dp as real_dp
    from gsm_sim import advice_bridge as AB
    seen: list[dict | None] = []
    orig = real_dp.solve

    def spy(spi, policy, params=None):
        seen.append(params)
        return orig(spi, policy, params)

    monkeypatch.setattr(AB.shift_dp, "solve", spy)
    return seen


def _consult_once(env, seen):
    result, cfg, pol = env
    bridge = AdviceActionBridge(cfg, pol, seed=1)
    for a in result.actors:
        now = a.shift_start_min + 120
        if now >= a.shift_end_min:
            continue
        bridge.consult(a, now, lambda ac, h: {"x": 3.0}, a.shift_end_min)
        if seen:
            return bridge
    pytest.skip("không actor nào gọi tới solver ở seed này")


def test_bridge_passes_its_own_bucket_min(env, monkeypatch):
    """Bucket của DP phải bằng ĐÚNG bucket bridge dựng — nếu không, mọi phép tính pin/nghỉ
    của DP lệch theo tỷ lệ `bridge.bucket_min / 30`."""
    seen = _capture_params(monkeypatch)
    bridge = _consult_once(env, seen)
    assert seen and seen[0] is not None, "bridge gọi solver mà KHÔNG truyền params nào"
    assert seen[0].get("bucket_min") == bridge.bucket_min, (
        f"DP tính theo bucket {seen[0].get('bucket_min')}′ trong khi sim tiến "
        f"{bridge.bucket_min}′ mỗi bucket"
    )


def test_bridge_passes_real_rates_so_bonus_gate_applies(env, monkeypatch):
    """Thiếu `acceptance_rate`/`completion_rate` ⇒ `_bonus_eligible` trả 'không có số để xét'
    ⇒ S2 hứa thưởng cho cả người chính sách sẽ KHÔNG trả. Sim biết hai số này."""
    seen = _capture_params(monkeypatch)
    _consult_once(env, seen)
    p = seen[0] or {}
    assert p.get("acceptance_rate") is not None, "sim biết tỷ lệ nhận mà không truyền cho S2"
    assert p.get("completion_rate") is not None, "sim biết tỷ lệ hoàn thành mà không truyền"


def test_bridge_passes_real_p_accept_and_dist(env, monkeypatch):
    """`DEFAULT_PARAMS` tự ghi 'CALLER NÊN TRUYỀN số thật' (AUDIT S2-4/S2-5). Để mặc định
    `p_accept=0.9`/`avg_dist_km=3.0` là dùng số của một tài xế tưởng tượng."""
    from gsm_core.solvers.shift_dp import DEFAULT_PARAMS
    seen = _capture_params(monkeypatch)
    _consult_once(env, seen)
    p = seen[0] or {}
    assert "p_accept" in p and "avg_dist_km" in p
    assert not (p["p_accept"] == DEFAULT_PARAMS["p_accept"]
                and p["avg_dist_km"] == DEFAULT_PARAMS["avg_dist_km"]), \
        "truyền đúng bằng mặc định cho CẢ HAI ⇒ nhiều khả năng vẫn là số bịa, không phải số thật"
