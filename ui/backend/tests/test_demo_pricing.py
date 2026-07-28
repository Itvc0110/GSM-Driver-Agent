import pytest


def test_quote_distance_uses_simulator_policy_boundaries():
    """Bắt hard-code UI: cùng distance phải cho đúng gross/payout của Simulator."""
    from app.adapters.sim_pricing import quote_distance

    assert quote_distance(0.0)["fare_vnd"] == 13_000
    assert quote_distance(2.0)["fare_vnd"] == 13_000
    quote = quote_distance(3.5)
    assert quote == {
        "fare_vnd": 19_450,
        "driver_payout_vnd": 14_588,
        "driver_share": 0.75,
        "fare_policy_version": "sim-policy-v0",
        "data_mode": "synthetic",
        "is_mock": True,
    }


def test_quote_distance_rejects_negative_distance():
    """Distance âm không được âm thầm biến thành base fare."""
    from app.adapters.sim_pricing import quote_distance

    with pytest.raises(ValueError, match="distance_km"):
        quote_distance(-0.1)
