"""E1a — sửa THƯỚC ĐO trước khi sửa kênh (UPDATE-151 r07/r03/r08; plan E1 duyệt 2026-08-06).

Vì sao tồn tại: review 21 agent tìm ra bộ thước đang có 4 lỗ — `xveto_*`/`commit_*` lọt bảng
significance HAI CHIỀU (lỗ Goodhart mà `HEALTH_KEYS_ONE_WAY` sinh ra để chặn), `n_insufficient`
so hằng 30 kể cả khi caller đòi 100, hàng system thiếu mean/n_positive và keys lấy từ pairs[0]
(archetype vắng ở seed sau ⇒ KeyError), metric pin bị mean 2 đội che (charge_min lưỡng đỉnh
1-2′ vs 210′), và `format: date-time` vô hiệu trên 15 schema (timestamp `2029-02-31` lọt store
append-only). File này viết ĐỎ-TRƯỚC.
"""
from __future__ import annotations

import statistics as st
from types import SimpleNamespace

import pytest

from gsm_core.schema_registry import SchemaRegistry
from gsm_sim.entities import FleetType
from gsm_sim.parallel import PairResult, _cohort_metrics, compare


# ---------- stub ----------

def _sys(seed: int, extra: dict | None = None, drop: tuple = ()) -> dict:
    d = {"payout_mean_all": 100.0 + seed, "payout_mean_P4": 90.0 + seed,
         "xveto_fired_n": 5.0 + seed, "commit_kept_n": 2.0,
         "rest_min_total": 3000.0, "n_actors_scope": 90.0,
         "served_rate": 0.75}
    d.update(extra or {})
    for k in drop:
        d.pop(k, None)
    return d


def _pair(seed: int, **kw) -> PairResult:
    drv = {"payout_vnd": 100000.0 + seed * 1000}
    return PairResult(seed=seed, actor_id=1, a=dict(drv),
                      b={k: v + 500 for k, v in drv.items()},
                      system_a=_sys(seed, kw.get("extra_a"), kw.get("drop_a", ())),
                      system_b=_sys(seed, kw.get("extra_b"), kw.get("drop_b", ())))


PAIRS = [_pair(s) for s in range(3)]


# ---------- (3) xveto_*/commit_* phải là cổng MỘT CHIỀU ----------

def test_xveto_va_commit_khong_co_significant_hai_chieu():
    """Lỗ Goodhart r07-F6: các khoá nối vào tầng 5 SAU khi HEALTH_KEYS_ONE_WAY chốt danh sách
    (xveto_* UPDATE-138, commit_* UPDATE-142) đang được gắn `significant` hai chiều — veto tăng
    in ra như "hệ thống tốt lên". Mọi khoá tiền tố veto_/xveto_/commit_ phải đi cổng một chiều."""
    out = compare(PAIRS)
    for k in ("xveto_fired_n", "commit_kept_n"):
        row = out["system"][k]
        assert "one_way_gate" in row, f"{k} thiếu one_way_gate"
        assert "significant" not in row, f"{k} vẫn mang significant hai chiều"


def test_doi_chung_metric_kinh_te_van_hai_chieu():
    row = compare(PAIRS)["system"]["payout_mean_P4"]
    assert "significant" in row and "one_way_gate" not in row


# ---------- (2) n_insufficient theo min_seeds thật ----------

def test_n_insufficient_theo_min_seeds_truyen_vao():
    """r07-F3/BUG-PARALLEL-NINSUF: n=3 với min_seeds=3 ⇒ mẫu ĐỦ theo hợp đồng caller đặt;
    bản cũ so hằng 30 nên hai cờ tự mâu thuẫn (n_insufficient=False ở n=50/min=100 và ngược)."""
    assert compare(PAIRS, min_seeds=3)["n_insufficient"] is False
    assert compare(PAIRS)["n_insufficient"] is True          # mặc định 30 giữ nguyên nghĩa


# ---------- (4) hàng system đủ mean_a/mean_b/n_positive; keys là UNION ----------

def test_system_row_co_mean_va_n_positive():
    row = compare(PAIRS)["system"]["payout_mean_P4"]
    for k in ("mean_a", "mean_b", "n_positive"):
        assert k in row, f"hàng system thiếu {k} (r07-F7)"
    assert row["mean_a"] == pytest.approx(st.mean([90.0, 91.0, 92.0]))


def test_keys_union_archetype_vang_khong_no_khong_roi():
    """r07-F8: pairs[0] thiếu P3 nhưng seed sau có ⇒ bản cũ RƠI IM LẶNG; pairs sau thiếu ⇒
    KeyError. Bản mới: union keys + `n_pairs` khai số cặp thực có khi < n."""
    pairs = [_pair(0, extra_a={"payout_mean_P3": 80.0}, extra_b={"payout_mean_P3": 82.0}),
             _pair(1),                                        # P3 vắng ở seed này
             _pair(2, extra_a={"payout_mean_P3": 84.0}, extra_b={"payout_mean_P3": 83.0})]
    out = compare(pairs)
    row = out["system"].get("payout_mean_P3")
    assert row is not None, "key chỉ có ở seed sau bị rơi im lặng"
    assert row.get("n_pairs") == 2, row


# ---------- (5) metric pin THEO FLEET ----------

def _actor(fleet, payout, charge_min, arch="P4"):
    return SimpleNamespace(archetype=arch, fleet=fleet, payout_vnd=payout, cost_vnd=0.0,
                           trips_done=10, charge_min=charge_min)


def test_cohort_metrics_bao_theo_fleet():
    """r03 SWAP-07: fleet confound 100% với archetype + charge_min lưỡng đỉnh (1-2′ vs 210′)
    ⇒ mean 2 đội gộp là vô nghĩa. Phải có payout/net mean THEO FLEET + percentile charge_min."""
    res = SimpleNamespace(actors=[
        _actor(FleetType.SWAP, 100_000.0, 2.0), _actor(FleetType.SWAP, 120_000.0, 4.0),
        _actor(FleetType.CHARGE, 90_000.0, 210.0, arch="P1"),
    ])
    m = _cohort_metrics(res)
    assert m["payout_mean_F_swap"] == pytest.approx(110_000.0)
    assert m["payout_mean_F_charge"] == pytest.approx(90_000.0)
    assert m["charge_min_p90_F_swap"] < 10.0
    assert m["charge_min_p90_F_charge"] == pytest.approx(210.0)


# ---------- (7) format date-time phải CÓ RĂNG ----------

def test_date_time_rac_bi_chan():
    """r08 REVIEW-092-5: Draft202012Validator không format_checker ⇒ `2029-02-31` lọt validate.
    ⚠ jsonschema.FORMAT_CHECKER mặc định KHÔNG kiểm date-time khi thiếu rfc3339-validator (đã
    kiểm 2026-08-06: 'date-time' not in checkers) — thêm format_checker suông là placebo D-R12;
    phải đăng ký checker thật."""
    reg = SchemaRegistry("schemas")
    rec = {"schema_version": "1.1.0", "event_id": "e1", "checkpoint_id": "c1",
           "driver_id": "d-1", "display_id": None, "event_type": "created",
           "occurred_at": "2029-02-31T00:00:00Z",           # ngày KHÔNG TỒN TẠI
           "actor": "system", "origin": "checkpoint", "reason_code": None,
           "relation_type": None, "confidence": None, "payload": {}}
    errs = reg.validate("advice_checkpoint_event", rec)
    assert errs, "timestamp rác 2029-02-31 vẫn lọt validate — format date-time không răng"
    rec_ok = dict(rec, occurred_at="2026-08-06T09:30:00Z")
    assert reg.validate("advice_checkpoint_event", rec_ok) == [], "bản hợp lệ bị chặn oan"
