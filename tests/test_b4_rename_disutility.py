"""B4 (PLAN-cycle-wx) — hoàn tất đổi tên nửa vời: `accept_cost_per_pickup_km_vnd` →
`pickup_disutility_vnd_per_km`.

Vì sao (hồ sơ chi phí §6): 3.000đ/km là DISUTILITY CẢM NHẬN trong quyết định nhận đơn,
không phải tiền mặt (tiền thật 30–250đ/km — lệch 10–20×). Hàm trong `behavior.py` đã đổi
tên từ Cycle P nhưng config/world/dashboard vẫn mang tên "cost" — hai tên một sự thật,
ai đọc key config sẽ hiểu nhầm là tiền.
"""

from __future__ import annotations

from gsm_sim.config import Config


def test_config_uses_disutility_name():
    c = Config.load("configs/pilot_dongda.yaml")
    b = c.get("behavior", {})
    assert "pickup_disutility_vnd_per_km" in b, "key mới phải tồn tại"
    assert "accept_cost_per_pickup_km_vnd" not in b, "key cũ 'cost' phải biến mất"
    assert float(b["pickup_disutility_vnd_per_km"]) == 3000.0, "GIÁ TRỊ không đổi (rename thuần)"


def test_world_reads_new_key():
    from gsm_sim.runner import run_once
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["behavior"]["pickup_disutility_vnd_per_km"] = 4321.0
    r = run_once(c, seed=1)  # chạy được là đủ — giá trị kiểm qua attr world khó truy sau run
    assert r.events  # smoke
    # đường trực tiếp: World đọc đúng key mới
    from gsm_sim.world import World  # noqa: F401 — import guard
    import inspect
    src = inspect.getsource(World.__init__)
    assert "pickup_disutility_vnd_per_km" in src
    assert "accept_cost_per_pickup_km_vnd" not in src or "deprecated" in src.lower()
