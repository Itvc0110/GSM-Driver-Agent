"""Cycle W (ĐA-05): advice lifecycle store — event log append-only + projections một-luật.

TDD đỏ trước. Phủ: W2 schema qua registry đa phiên bản · W1 AdviceEventLog (idempotency,
append-only, close — LAYEROUT-16) · W3 projections (state machine, adherence denominator
từ `decided`, sim adapter, replay determinism).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gsm_core.schema_registry import LAYER_OF, SchemaRegistry

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"


@pytest.fixture()
def reg() -> SchemaRegistry:
    return SchemaRegistry(SCHEMAS)


def _ev(**kw) -> dict:
    """Factory event hợp lệ tối thiểu — override từng trường qua kwargs."""
    base = {
        "event_id": "evt-001",
        "decision_id": "adv-abc123",
        "display_id": None,
        "driver_id": "driver-01",
        "run_id": None,
        "event_type": "decided",
        "reason_code": None,
        "occurred_at": "2026-07-29T08:00:00+07:00",
        "observed_at": "2026-07-29T08:00:00+07:00",
        "actor": "advisor",
        "origin": "pipeline",
        "source": "MOCK",
        "context_revision": None,
        "payload": {},
        "schema_version": "1.0.0",
    }
    base.update(kw)
    return base


# ---------- W2: schema qua registry đa phiên bản ----------

def test_entity_registered(reg):
    assert LAYER_OF.get("advice_lifecycle_event") == "advisor"
    assert reg.versions("advice_lifecycle_event") == ("1.0.0",)


def test_valid_event_passes(reg):
    assert reg.validate("advice_lifecycle_event", _ev()) == []


def test_missing_decision_id_fails(reg):
    ev = _ev()
    del ev["decision_id"]
    assert reg.validate("advice_lifecycle_event", ev)


def test_unknown_event_type_fails(reg):
    assert reg.validate("advice_lifecycle_event", _ev(event_type="yolo"))


def test_unknown_version_fails_loud(reg):
    errs = reg.validate("advice_lifecycle_event", _ev(schema_version="9.9.9"))
    assert errs and "9.9.9" in errs[0]


# ---------- W1: AdviceEventLog ----------

def _log(tmp_path):
    from gsm_core.lifecycle.event_log import AdviceEventLog
    return AdviceEventLog(tmp_path / "lifecycle.db")


def test_append_and_read_roundtrip(tmp_path):
    with _log(tmp_path) as log:
        assert log.append(_ev()) is True
        rows = log.events()
        assert len(rows) == 1 and rows[0]["event_id"] == "evt-001"
        assert rows[0]["payload"] == {}


def test_append_idempotent_by_event_id(tmp_path):
    """Cùng event_id ⇒ lần 2 KHÔNG ghi đè, trả False — INSERT OR IGNORE."""
    with _log(tmp_path) as log:
        assert log.append(_ev()) is True
        assert log.append(_ev(event_type="followed")) is False  # cùng event_id
        rows = log.events()
        assert len(rows) == 1
        assert rows[0]["event_type"] == "decided"  # bản ĐẦU thắng, không update


def test_append_only_no_mutation_api(tmp_path):
    """Append-only: store không có API update/delete."""
    with _log(tmp_path) as log:
        for name in ("update", "delete", "update_event", "delete_event", "clear"):
            assert not hasattr(log, name), f"store append-only không được có .{name}()"


def test_append_invalid_event_raises(tmp_path):
    """Validate qua registry TRƯỚC khi ghi — event hỏng không được vào log."""
    with _log(tmp_path) as log:
        bad = _ev()
        del bad["decision_id"]
        with pytest.raises(ValueError, match="decision_id"):
            log.append(bad)
        assert log.events() == []


# --- 3 lan can từ review đối kháng tự làm (đều reproduce được TRƯỚC khi fix) ---

def test_naive_timestamp_rejected_at_append(tmp_path):
    """Timestamp KHÔNG có offset múi giờ phải bị chặn NGAY lúc ghi.

    Reproduce: trộn naive + aware ⇒ `sorted()` nổ TypeError ("can't compare offset-naive
    and offset-aware") — tức MỘT record naive lọt vào làm CHẾT toàn bộ projection của
    store, kể cả các decision không liên quan. Fail-loud tại boundary thay vì fail muộn
    ở consumer (goal Cường: data ngoài phải normalize về đúng dạng TRƯỚC khi vào hệ)."""
    with _log(tmp_path) as log:
        with pytest.raises(ValueError, match="occurred_at"):
            log.append(_ev(occurred_at="2026-07-29T08:00:00"))   # thiếu +07:00/Z
        assert log.events() == []


def test_garbage_timestamp_rejected_at_append(tmp_path):
    """Chuỗi rác qua được `minLength` cũ ⇒ vào log rồi mới nổ ở projection (đã persist)."""
    with _log(tmp_path) as log:
        with pytest.raises(ValueError):
            log.append(_ev(occurred_at="hôm qua"))
        assert log.events() == []


def test_numpy_scalars_in_payload_are_normalized(tmp_path):
    """Sim detail mang numpy scalar (`np.float64` từ acceptance/lift) — `json.dumps`
    thô nổ TypeError ở đúng đường export sim→store mà ĐA-04 sắp dùng. Phải normalize
    về kiểu Python GIỮ NGUYÊN GIÁ TRỊ (không str hoá — str hoá là làm hỏng số im lặng)."""
    np = pytest.importorskip("numpy")
    with _log(tmp_path) as log:
        log.append(_ev(payload={"lift": np.float64(1.5), "n": np.int64(3),
                                "flag": np.bool_(True)}))
        p = log.events()[0]["payload"]
    assert p == {"lift": 1.5, "n": 3, "flag": True}
    assert isinstance(p["n"], int) and isinstance(p["lift"], float)


def test_unserializable_payload_fails_loud(tmp_path):
    """Kiểu KHÔNG normalize được phải nổ tường minh, không âm thầm str hoá."""
    with _log(tmp_path) as log:
        with pytest.raises((ValueError, TypeError)):
            log.append(_ev(payload={"obj": object()}))


def test_filter_by_decision_and_run(tmp_path):
    with _log(tmp_path) as log:
        log.append(_ev(event_id="e1", decision_id="d1", run_id="7-B-all-single"))
        log.append(_ev(event_id="e2", decision_id="d2", run_id="7-B-all-single"))
        log.append(_ev(event_id="e3", decision_id="d1", run_id=None))
        assert {r["event_id"] for r in log.events(decision_id="d1")} == {"e1", "e3"}
        assert {r["event_id"] for r in log.events(run_id="7-B-all-single")} == {"e1", "e2"}


def test_close_releases_file_windows(tmp_path):
    """LAYEROUT-16: đóng connection thật — file mở lại/xoá được trên Windows."""
    log = _log(tmp_path)
    log.append(_ev())
    log.close()
    (tmp_path / "lifecycle.db").unlink()  # PermissionError nếu connection còn giữ


def test_persist_across_reopen(tmp_path):
    with _log(tmp_path) as log:
        log.append(_ev())
    with _log(tmp_path) as log2:
        assert len(log2.events()) == 1


# ---------- W3: projections — MỘT LUẬT (pure function trên iterable) ----------

def _proj():
    from gsm_core.lifecycle import projections
    return projections


def test_state_machine_follow_path():
    p = _proj()
    events = [
        _ev(event_id="e1", decision_id="d1", event_type="decided",
            occurred_at="2026-07-29T08:00:00+07:00"),
        _ev(event_id="e2", decision_id="d1", event_type="displayed",
            display_id="disp-1", occurred_at="2026-07-29T08:01:00+07:00"),
        _ev(event_id="e3", decision_id="d1", event_type="followed",
            occurred_at="2026-07-29T08:05:00+07:00", actor="driver"),
    ]
    st = p.decision_state(events)
    assert st["d1"]["state"] == "followed"
    assert st["d1"]["displayed"] is True


def test_state_machine_dismiss_terminal():
    p = _proj()
    events = [
        _ev(event_id="e1", decision_id="d1", event_type="decided"),
        _ev(event_id="e2", decision_id="d1", event_type="dismissed",
            occurred_at="2026-07-29T08:02:00+07:00", actor="driver",
            reason_code="dismissed_for_window"),
    ]
    st = p.decision_state(events)
    assert st["d1"]["state"] == "dismissed"
    assert st["d1"]["reason_code"] == "dismissed_for_window"


def test_replay_deterministic_and_duplicate_safe():
    """Replay 2 lần = cùng kết quả; event trùng/đảo thứ tự không phá state."""
    p = _proj()
    events = [
        _ev(event_id="e3", decision_id="d1", event_type="followed",
            occurred_at="2026-07-29T08:05:00+07:00"),
        _ev(event_id="e1", decision_id="d1", event_type="decided",
            occurred_at="2026-07-29T08:00:00+07:00"),
        _ev(event_id="e1", decision_id="d1", event_type="decided",
            occurred_at="2026-07-29T08:00:00+07:00"),  # duplicate y hệt
    ]
    once = p.decision_state(events)
    twice = p.decision_state(list(events))
    assert once == twice
    assert once["d1"]["state"] == "followed"  # sort theo occurred_at, không theo vị trí list


def test_mixed_timezone_offsets_sorted_by_real_time():
    """Sort theo CHUỖI ISO là bẫy: '2026-07-29T00:30:00+00:00' < '2026-07-29T01:00:00+07:00'
    lexicographic, nhưng 01:00+07:00 = 18:00Z NGÀY TRƯỚC — sớm hơn thật. Ba origin ghi
    ba múi giờ (pipeline UTC, sim/UI +07:00) nên luật phải sort theo thời gian THẬT."""
    p = _proj()
    events = [
        # dismissed xảy ra SAU followed theo thời gian thật (00:30Z > 18:00Z hôm trước)
        _ev(event_id="e2", decision_id="d1", event_type="dismissed",
            occurred_at="2026-07-29T00:30:00+00:00"),
        _ev(event_id="e1", decision_id="d1", event_type="followed",
            occurred_at="2026-07-29T01:00:00+07:00"),
    ]
    st = p.decision_state(events)
    assert st["d1"]["state"] == "dismissed", (
        "phải sort theo thời gian thật (dismissed 00:30Z là event CUỐI), "
        "không phải theo chuỗi")


def test_adherence_denominator_is_decided():
    """BRIDGE-3 khắc trong luật: denominator = số decision ĐÃ QUYẾT, không phải số followed."""
    p = _proj()
    events = []
    for i, outcome in enumerate(["followed", "dismissed", None]):
        did = f"d{i}"
        events.append(_ev(event_id=f"dec-{i}", decision_id=did, event_type="decided",
                          driver_id="driver-01", payload={"topic": "positioning"}))
        if outcome:
            events.append(_ev(event_id=f"out-{i}", decision_id=did, event_type=outcome,
                              driver_id="driver-01",
                              occurred_at="2026-07-29T09:00:00+07:00"))
    view = p.adherence_view(events)
    # khoá gồm run_id (None ở đường pipeline/UI) — xem F-2: thiếu run_id thì actor 0 của
    # hai run sim khác nhau bị gộp làm một người
    row = view[(None, "driver-01", "positioning")]
    assert row["decided"] == 3
    assert row["followed"] == 1
    assert row["dismissed"] == 1


# ---------- W3: sim adapter — events RAM → lifecycle (một luật chạm sim) ----------

def test_sim_events_to_lifecycle_valid_and_mapped(reg):
    from gsm_sim.world import Event
    p = _proj()
    run_id = "7-B-positioning-single"
    # `advice_given` mang cờ followed như producer THẬT (world.py) — `advice_followed`
    # là marker BRIDGE-3 dư thừa, adapter cố ý KHÔNG map (F-S1: map cả hai là đếm một
    # lần theo thành hai — event_followed 655 thay vì 631).
    sim_events = [
        Event(t_min=480.0, actor_id=3, kind="advice_given",
              detail={"decision_id": "slth-7-3-shift_plan-8", "action": "REST",
                      "followed": True}),
        Event(t_min=485.0, actor_id=3, kind="advice_followed",
              detail={"decision_id": "slth-7-3-shift_plan-8"}),  # bị bỏ qua có chủ ý
        Event(t_min=490.0, actor_id=4, kind="advice_suppressed",
              detail={"decision_id": "slth-7-4-rest_window-8", "reason": "wait_only"}),
        Event(t_min=500.0, actor_id=5, kind="order_pickup", detail={}),  # không decision_id → bỏ
    ]
    lc = p.sim_events_to_lifecycle(sim_events, run_id=run_id)
    assert len(lc) == 3  # decided + followed (từ cờ) + suppressed
    for e in lc:
        assert reg.validate("advice_lifecycle_event", e) == [], e
        assert e["run_id"] == run_id
        assert e["origin"] == "sim" and e["source"] == "MOCK"
    st = p.decision_state(lc)
    assert st["slth-7-3-shift_plan-8"]["state"] == "followed"
    assert st["slth-7-4-rest_window-8"]["state"] == "suppressed"


def test_sim_adapter_deterministic_event_ids():
    """Cùng input ⇒ cùng event_id (derive thuần, không uuid) — exact-repeat của sim giữ nguyên."""
    from gsm_sim.world import Event
    p = _proj()
    evs = [Event(t_min=480.0, actor_id=3, kind="advice_given",
                 detail={"decision_id": "slth-7-3-shift_plan-8"})]
    a = p.sim_events_to_lifecycle(evs, run_id="r1")
    b = p.sim_events_to_lifecycle(evs, run_id="r1")
    assert a == b
    assert a[0]["event_id"]  # non-empty, deterministic
