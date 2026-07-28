"""TẦNG 2 dispatcher — batched bipartite matching (Hungarian), theo đặc tả đã có.

`research/simulation/world-parameters.md` §3 đặc tả dispatcher **hai tầng**, dẫn công bố DiDi:
tầng 1 lấy ứng viên bằng H3, **tầng 2 giải bipartite `cost = ETA_pickup` bằng
`scipy.linear_sum_assignment`**, chỉ nhận cặp `ETA ≤ eta_max`. Greedy nearest **giữ làm baseline
so sánh**.

**Tầng 2 chưa bao giờ được xây** — `dispatcher.py` docstring tự ghi *"Hungarian để vòng sau"*.
Và greedy hiện tại còn lệch cả docstring của chính nó: xếp hạng theo **haversine** chứ không phải
ETA (hồ sơ `15-*` §1).

Hai khuyết tật đo được của greedy:
  1. **`bad_hex`** (tên Rapido đặt): chọn người **gần hơn về hình học nhưng đường chậm hơn**, ETA
     fail ⇒ **bỏ luôn đơn**, trong khi người xa hơn + đường tốt vẫn đạt ETA. 293/3.520 lượt (8,3%).
  2. **Đói theo `order_id`**: greedy xét đơn theo id tăng dần ⇒ đơn cũ chiếm tài xế gần, đơn mới
     nhận phần thừa ở xa ⇒ pickup dài ⇒ bị từ chối nhiều hơn. Đây là cơ chế làm tỷ lệ nhận trôi
     khỏi `accept_base` khi nới shortlist (Q-07).

Test ở đây dùng fixture TỔNG HỢP để cô lập thuật toán; kiểm chứng mức hệ thống nằm ở
`test_dispatch_shortlist_radius.py` và `test_sim_realism.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

import h3
import pytest

from gsm_sim.dispatcher import match_batch

RES = 9
ETA_MAX = 11.0
SPEED = {"peak": 17, "offpeak": 25, "night": 30,
         "peak_hours": [6, 7, 8, 16, 17, 18], "night_hours": [21, 22, 23, 0, 1, 2, 3, 4, 5]}
DISP = {"candidate_ring_k": 4, "candidate_ring_k_max": 12, "eta_max_min": ETA_MAX}
HOUR = 10          # offpeak ⇒ 25 km/h


@dataclass
class FakeOrder:
    order_id: int
    pickup_lat: float
    pickup_lon: float

    @property
    def pickup_cell(self) -> str:
        return h3.latlng_to_cell(self.pickup_lat, self.pickup_lon, RES)


@dataclass
class FakeActor:
    actor_id: int
    lat: float
    lon: float

    @property
    def cell(self) -> str:
        return h3.latlng_to_cell(self.lat, self.lon, RES)


def _at(lat0: float, lon0: float, dkm_north: float, dkm_east: float):
    return lat0 + dkm_north / 111.0, lon0 + dkm_east / (111.0 * 0.934)


LAT0, LON0 = 21.015, 105.82


def _run(orders, actors, factor_fn=None):
    return match_batch(orders, actors, None, HOUR, SPEED, DISP,
                       speed_fn=None, detour=1.0, factor_fn=factor_fn)


# ---------- Khuyết tật 1: bad_hex ----------

def test_ranks_by_eta_not_haversine(monkeypatch):
    """Rapido gọi đây là `bad_hex` vs `good_hex`: người GẦN HƠN nhưng đường xấu có thể ETA TỆ HƠN
    người XA HƠN nhưng đường tốt. Xếp hạng theo haversine ⇒ chọn nhầm, rồi vứt đơn."""
    o = FakeOrder(1, LAT0, LON0)
    near_lat, near_lon = _at(LAT0, LON0, 2.0, 0.0)      # 2,0 km — đường XẤU
    far_lat, far_lon = _at(LAT0, LON0, 0.0, 2.6)        # 2,6 km — đường TỐT
    a_near, a_far = FakeActor(10, near_lat, near_lon), FakeActor(20, far_lat, far_lon)

    def factor(cell_from, cell_to):
        return 3.4 if cell_from == a_near.cell else 1.05

    # ETA: gần = 2.0×3.4/25×60 = 16.3′ (>11 ⇒ loại) · xa = 2.6×1.05/25×60 = 6.6′ (đạt)
    asg = _run([o], [a_near, a_far], factor_fn=factor)
    assert asg, "đơn bị BỎ dù có ứng viên đạt ETA (đúng bug 8,3% đã đo)"
    assert asg[0].actor_id == 20, (
        f"chọn theo haversine (người gần, đường xấu) thay vì ETA: {asg[0]}")
    assert asg[0].eta_min <= ETA_MAX


def test_never_drops_order_when_a_feasible_candidate_exists():
    """Bất biến: còn ứng viên nào đạt ETA thì KHÔNG được bỏ đơn."""
    o = FakeOrder(1, LAT0, LON0)
    actors = [FakeActor(i, *_at(LAT0, LON0, 0.0, 0.3 * i)) for i in range(1, 9)]
    asg = _run([o], actors)
    assert len(asg) == 1


# ---------- Khuyết tật 2: đói theo order_id ----------

def test_batch_assignment_serves_more_than_greedy_by_order_id():
    """Greedy xét theo `order_id` tăng dần ⇒ đơn #1 giành mất tài xế **DUY NHẤT** khả thi của #2.

    Bố trí (ETA cap 11′ @ 25 km/h ⇒ bán kính khả thi 4,58 km):
      o1 tại 0        · o2 tại 4,0 km Đông
      A  tại 0,5 Đông → o1: 0,5 km (1,2′) ✓ · o2: 3,5 km (8,4′) ✓
      B  tại 1,5 Tây  → o1: 1,5 km (3,6′) ✓ · o2: **5,5 km (13,2′) ✗**

      greedy    : o1 lấy A (gần nhất) ⇒ o2 chỉ còn B, KHÔNG đạt ETA ⇒ **o2 BỊ BỎ** (phục vụ 1)
      tối ưu    : o1 lấy B, o2 lấy A ⇒ **phục vụ CẢ HAI**

    Đây chính là cơ chế làm đơn chết dù có tài xế trong tầm — và là lý do nới shortlist theo
    greedy lại đẩy pickup dài ra (Q-07).
    """
    o1 = FakeOrder(1, LAT0, LON0)
    o2 = FakeOrder(2, *_at(LAT0, LON0, 0.0, 4.0))
    a_A = FakeActor(10, *_at(LAT0, LON0, 0.0, 0.5))
    a_B = FakeActor(20, *_at(LAT0, LON0, 0.0, -1.5))

    asg = _run([o1, o2], [a_A, a_B])
    assert len(asg) == 2, (
        f"chỉ phục vụ {len(asg)}/2 đơn — greedy theo order_id giành mất ứng viên duy nhất "
        f"của đơn sau: {[(x.order_id, x.actor_id) for x in asg]}")
    pair = {x.order_id: x.actor_id for x in asg}
    assert pair == {1: 20, 2: 10}, f"phân bổ sai: {pair}"
    assert all(x.eta_min <= ETA_MAX for x in asg)


def test_batch_matching_minimises_total_eta():
    """Tính chất chung: tổng ETA của lời giải phải ≤ mọi hoán vị khác."""
    import itertools
    orders = [FakeOrder(i, *_at(LAT0, LON0, 0.0, 0.6 * i)) for i in range(1, 4)]
    actors = [FakeActor(10 * j, *_at(LAT0, LON0, 0.35 * j, 0.0)) for j in range(1, 4)]
    asg = _run(orders, actors)
    assert len(asg) == 3

    from gsm_sim.geo import haversine_km
    def eta(o, a):
        return haversine_km(a.lat, a.lon, o.pickup_lat, o.pickup_lon) / 25.0 * 60.0

    got = sum(x.eta_min for x in asg)
    best = min(sum(eta(o, a) for o, a in zip(orders, perm))
               for perm in itertools.permutations(actors))
    # `Assignment.eta_min` làm tròn 2 chữ số ⇒ tolerance phải nới theo, không chặt hơn
    # chính dữ liệu (bài học tolerance của UPDATE-075).
    assert got == pytest.approx(best, abs=0.03), f"không phải nghiệm tối ưu: {got} vs {best}"


# ---------- Ràng buộc phải GIỮ ----------

def test_eta_cap_still_enforced():
    """Ứng viên duy nhất quá xa ⇒ KHÔNG gán (khách không chờ đón mãi)."""
    o = FakeOrder(1, LAT0, LON0)
    far = FakeActor(10, *_at(LAT0, LON0, 0.0, 9.0))     # 9 km ⇒ ~21,6′ > 11′
    assert _run([o], [far]) == []


def test_one_actor_per_tick():
    """Một tài xế chỉ nhận tối đa 1 đơn mỗi tick."""
    orders = [FakeOrder(i, *_at(LAT0, LON0, 0.0, 0.1 * i)) for i in range(1, 4)]
    a = FakeActor(10, LAT0, LON0)
    asg = _run(orders, [a])
    assert len(asg) == 1


def test_deterministic_same_input_same_output():
    orders = [FakeOrder(i, *_at(LAT0, LON0, 0.0, 0.4 * i)) for i in range(1, 5)]
    actors = [FakeActor(10 * j, *_at(LAT0, LON0, 0.3 * j, 0.1)) for j in range(1, 5)]
    a = [(x.order_id, x.actor_id, round(x.eta_min, 6)) for x in _run(orders, actors)]
    b = [(x.order_id, x.actor_id, round(x.eta_min, 6)) for x in _run(orders, actors)]
    assert a == b


def test_result_sorted_by_order_id():
    """Hợp đồng cũ: kết quả theo `order_id` tăng dần (caller dựa vào)."""
    orders = [FakeOrder(i, *_at(LAT0, LON0, 0.0, 0.4 * i)) for i in (3, 1, 2)]
    actors = [FakeActor(10 * j, *_at(LAT0, LON0, 0.3 * j, 0.1)) for j in range(1, 4)]
    ids = [x.order_id for x in _run(orders, actors)]
    assert ids == sorted(ids)


def test_empty_inputs_are_safe():
    assert _run([], [FakeActor(1, LAT0, LON0)]) == []
    assert _run([FakeOrder(1, LAT0, LON0)], []) == []
