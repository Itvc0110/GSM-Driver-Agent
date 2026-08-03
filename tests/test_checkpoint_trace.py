"""P2 AdviceCheckpoint simulator traceability — post-run and RAM-only guards."""

from __future__ import annotations

import json
import copy
from types import SimpleNamespace


def _actor():
    return SimpleNamespace(
        actor_id=7, state=SimpleNamespace(value="idle"), cell="892ab13a677ffff",
        lat=21.02, lon=105.82, soc_pct=42.5, points=78, orders_offered=10,
        orders_accepted=8, orders_completed=7, online_min=180.0, rest_min=20.0,
        shift_start_min=360.0, shift_end_min=1080.0,
    )


def test_snapshot_is_auditable_without_raw_coordinates_or_pii():
    from gsm_sim.checkpoint_trace import actor_snapshot

    snapshot = actor_snapshot(_actor(), now_min=540, run_id="run-1")

    assert snapshot["driver_id"] == "d-7"
    assert snapshot["zone_h3"] == "892ab13a677ffff"
    assert snapshot["soc_pct"] == 42.5
    assert "lat" not in snapshot and "lon" not in snapshot
    assert "name" not in snapshot and "phone" not in snapshot
    assert snapshot["is_mock"] is True


def test_segment_ids_are_deterministic_and_do_not_change_segment_order():
    from gsm_sim.checkpoint_trace import annotate_segment_ids

    original = [
        {"actor_id": 7, "t0": 540.0, "t1": 550.0, "kind": "relocate",
         "from_lat": 21.0, "from_lon": 105.8, "to_lat": 21.1, "to_lon": 105.9},
        {"actor_id": 7, "t0": 550.0, "t1": 570.0, "kind": "on_trip",
         "from_lat": 21.1, "from_lon": 105.9, "to_lat": 21.2, "to_lon": 106.0},
    ]
    first = annotate_segment_ids("run-1", original)
    second = annotate_segment_ids("run-1", list(reversed(list(reversed(original)))))

    assert [s["segment_id"] for s in first] == [s["segment_id"] for s in second]
    assert [(s["kind"], s["t0"], s["t1"]) for s in first] == [
        ("relocate", 540.0, 550.0), ("on_trip", 550.0, 570.0)]


def test_trace_export_writes_four_jsonl_files_and_digest_manifest(tmp_path):
    from gsm_sim.checkpoint_trace import export_checkpoint_trace

    result = SimpleNamespace(
        advice_artifacts=[{"artifact_id": "a-1"}],
        advice_checkpoints=[{"checkpoint_id": "ckpt-1"}],
        advice_checkpoint_events=[{"event_id": "e-1"}],
        execution_links=[{"execution_link_id": "x-1"}],
    )

    manifest = export_checkpoint_trace(result, tmp_path)

    expected = {
        "advice_artifacts.jsonl", "advice_checkpoints.jsonl",
        "advice_checkpoint_events.jsonl", "execution_links.jsonl",
    }
    assert expected <= {path.name for path in tmp_path.iterdir()}
    assert manifest["files"]["advice_artifacts.jsonl"]["count"] == 1
    assert manifest["files"]["execution_links.jsonl"]["digest"].startswith("sha256:")
    assert json.loads((tmp_path / "checkpoint_manifest.json").read_text()) == manifest


def test_shadow_comparator_ignores_only_diagnostic_metadata():
    from scripts.compare_checkpoint_shadow import semantic_fingerprint

    base = SimpleNamespace(
        actors=[SimpleNamespace(actor_id=1, payout_vnd=100, soc_pct=45.0,
                                trips_done=2, state=SimpleNamespace(value="offline"))],
        orders=[SimpleNamespace(order_id=1, state="COMPLETED")],
        segments=[{"actor_id": 1, "t0": 1.0, "t1": 2.0, "kind": "on_trip"}],
    )
    traced = SimpleNamespace(
        actors=base.actors, orders=base.orders,
        segments=[{**base.segments[0], "segment_id": "seg-diagnostic"}],
    )
    changed = SimpleNamespace(
        actors=[SimpleNamespace(actor_id=1, payout_vnd=101, soc_pct=45.0,
                                trips_done=2, state=SimpleNamespace(value="offline"))],
        orders=base.orders, segments=base.segments,
    )

    assert semantic_fingerprint(base) == semantic_fingerprint(traced)
    assert semantic_fingerprint(base) != semantic_fingerprint(changed)


def test_ram_sink_keeps_exact_solver_artifacts_and_links_execution_post_run():
    from gsm_sim.checkpoint_trace import CheckpointTraceSink, annotate_segment_ids

    actor = _actor()
    solver_input = {
        "schema_version": "1.1.0", "driver_id": "d-7",
        "t_now": "2026-07-01T09:00:00+07:00", "buckets_remaining": 2,
    }
    solver_report = {"status": "optimal", "confidence": 0.8, "solution": {
        "schedule": [
            {"bucket": "2026-07-01T09:00:00+07:00", "action": "REST"},
            {"bucket": "2026-07-01T10:00:00+07:00", "action": "ONLINE"},
        ],
        "next_action": {"bucket": "2026-07-01T10:00:00+07:00", "action": "ONLINE"},
    }}
    sink = CheckpointTraceSink(enabled=True, run_id="run-1")

    checkpoint_id = sink.capture(
        "S2", actor, 540, solver_input, solver_report, "decision-1")

    checkpoint = sink.checkpoints[0]
    refs = {record["artifact_id"]: record for record in sink.artifacts}
    assert checkpoint_id == checkpoint["checkpoint_id"]
    assert refs[checkpoint["solver_input_refs"][0]]["payload"] == solver_input
    assert refs[checkpoint["solver_report_refs"][0]]["payload"] == solver_report
    assert [event["event_type"] for event in sink.events] == ["created", "ready"]

    segments = annotate_segment_ids("run-1", [{
        "actor_id": 7, "t0": 540.0, "t1": 560.0, "kind": "rest",
        "from_lat": 21.0, "from_lon": 105.8,
        "to_lat": 21.0, "to_lon": 105.8,
    }])
    links = sink.finalize_execution_links(segments, legacy_events=[])

    assert links[0]["checkpoint_id"] == checkpoint_id
    assert links[0]["segment_id"] == segments[0]["segment_id"]
    assert links[0]["relation_type"] == "coincident"
    assert [event["event_type"] for event in sink.events][-1] == "execution_observed"
    assert all(event["event_type"] != "accepted" for event in sink.events)


def test_run_once_wires_shadow_trace_without_changing_semantic_outcomes():
    from gsm_sim.config import Config
    from gsm_sim.runner import run_once
    from scripts.compare_checkpoint_shadow import semantic_fingerprint

    base = Config.load("configs/pilot_dongda.yaml")
    data = copy.deepcopy(base.data)
    data["advice"].update(
        enabled=True, coverage="single", single_actor_id=42,
        channels={"shift_plan": True, "accept_lift": False,
                  "shift_extend": False, "rest_window": False},
        positioning_overrides="off",
    )
    off_data = copy.deepcopy(data)
    off_data["checkpoint_shadow"] = {"enabled": False}
    on_data = copy.deepcopy(data)
    on_data["checkpoint_shadow"] = {"enabled": True}

    plain = run_once(Config(off_data, base.root_dir), seed=1000)
    shadow = run_once(Config(on_data, base.root_dir), seed=1000)

    assert semantic_fingerprint(plain) == semantic_fingerprint(shadow)
    assert plain.advice_checkpoints == []
    assert shadow.advice_checkpoints
    assert all("segment_id" in segment for segment in shadow.segments)
    assert all("segment_id" not in segment for segment in plain.segments)


def test_presenters_run_post_run_on_the_same_fixed_trajectory():
    from gsm_core.advisor.checkpoint_presenter import CheckpointPresenter
    from gsm_sim.checkpoint_trace import evaluate_presenters_post_run

    result = SimpleNamespace(
        advice_checkpoints=[{
            "checkpoint_id": "ckpt-1", "surface": "nudge", "topic": "energy",
            "current_action": {"code": "SWAP", "label_id": "action.swap"},
            "action_window": None, "urgency_band": "medium",
            "confidence_band": "high", "reason_code": "soc_low",
            "solver_report_refs": [],
        }],
        advice_artifacts=[],
        segments=[{"segment_id": "seg-1", "actor_id": 1, "kind": "rest",
                   "t0": 1.0, "t1": 2.0}],
    )
    before = json.dumps(result.segments, sort_keys=True)
    outputs = evaluate_presenters_post_run(
        result, {"template-a": CheckpointPresenter(),
                 "template-b": CheckpointPresenter()})

    assert set(outputs) == {"template-a", "template-b"}
    assert outputs["template-a"][0]["checkpoint_id"] == "ckpt-1"
    assert json.dumps(result.segments, sort_keys=True) == before


def test_checkpoint_metrics_keep_acceptance_execution_and_adherence_separate():
    from gsm_sim.checkpoint_trace import checkpoint_metrics

    result = SimpleNamespace(
        advice_checkpoints=[{"checkpoint_id": "ckpt-1"}],
        advice_checkpoint_events=[
            {"checkpoint_id": "ckpt-1", "event_type": "created"},
            {"checkpoint_id": "ckpt-1", "event_type": "ready"},
            {"checkpoint_id": "ckpt-1", "event_type": "offered"},
            {"checkpoint_id": "ckpt-1", "event_type": "accepted"},
        ],
        execution_links=[], events=[],
    )
    metrics = checkpoint_metrics(result)
    assert metrics["accept_rate"] == 1.0
    assert metrics["execution_rate"] == 0.0
    assert "decision_adherence" in metrics and "event_adherence" in metrics
