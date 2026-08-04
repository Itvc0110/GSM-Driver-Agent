from __future__ import annotations


def test_real_demo_order_boundaries_capture_post_mutation_state():
    from app.services.demo_session import _default_run

    result = _default_run(1000)
    snapshots = {int(item["event_index"]): item for item in result.trace_snapshots}
    matched = [
        snapshots[index]["state"]
        for index, event in enumerate(result.events)
        if event.kind == "order_matched" and index in snapshots
    ]
    cancelled = [
        snapshots[index]["state"]
        for index, event in enumerate(result.events)
        if event.kind == "order_cancelled_after_accept" and index in snapshots
    ]

    assert matched, "demo run must contain an order_matched event"
    assert all(state == "enroute" for state in matched)
    assert all(state == "idle" for state in cancelled)
