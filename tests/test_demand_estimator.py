"""E10a — `RealizedDemandEstimator` (spec e10-advisor-noisy §3, §8 T3–T7).

Đơn vị đã pin: pickups / bucket planner. Config chuẩn của test: b=60, start_min=300
⇒ `first_op_bucket = 5`. Mỗi test một vế công thức §3.2.

Bằng chứng đỏ (đã chạy 2026-07-31, chi tiết trong UPDATE của cycle):
- chia `n_buckets` thay `k` · cold-không-fallback: đỏ được bằng mutation MỘT chỗ;
- biên bucket / rò cùng-thời-điểm: enforce HAI LỚP trùng nhau (ingest cut `>=` VÀ window
  `range(lo, idx)`) — mutation một lớp được lớp kia đỡ (vẫn xanh), sever CẢ HAI ⇒ 2 test đỏ.
  Đây là defense-in-depth chủ ý, không phải test không răng;
- `max(0, idx−lo)` và `idx <= first_op_bucket`: KHÔNG chứng minh đỏ được ở implementation
  dạng con-trỏ-theo-bucket — khi n_buckets ≤ 0 thì `range(lo, idx)` rỗng ⇒ acc rỗng ⇒ bug
  "chia số âm" spec §3.2 lo sợ không thể biểu hiện. Bất biến giữ theo CẤU TRÚC (mạnh hơn
  theo test); hai guard giữ lại làm hàng rào cho người sửa sau.
"""
from __future__ import annotations

from pathlib import Path

from gsm_sim.demand_estimator import RealizedDemandEstimator
from gsm_sim.world import Event

B, START = 60, 300


def _ev(t: float, cell: str, kind: str = "pickup") -> Event:
    return Event(t_min=float(t), actor_id=1, kind=kind, cell=cell)


def _make(events, k: int = 3, min_n: int = 1) -> RealizedDemandEstimator:
    return RealizedDemandEstimator(events, start_min=START, bucket_min=B,
                                   window_buckets=k, min_pickups=min_n)


# --- T3: công thức từng vế -------------------------------------------------

def test_t3_cong_thuc_chia_n_buckets_khong_chia_k():
    # bucket 5: A×3, B×1 · bucket 6: A×1  ⇒ estimate(7), k=3: lo=5, n_buckets=2
    events = [_ev(310, "A"), _ev(320, "A"), _ev(350, "A"), _ev(330, "B"), _ev(370, "A")]
    lam = _make(events).estimate(7)
    assert lam == {"A": 2.0, "B": 0.5}          # 4/2 và 1/2 — chia 2 bucket vận hành, KHÔNG chia k=3


def test_t3_chi_dem_pickup_khong_dem_kind_khac():
    # order_matched (cell = ô TÀI XẾ — đo CUNG) và expired/censored (future leak) bị CẤM
    events = [_ev(310, "A"),
              _ev(311, "A", kind="order_matched"), _ev(312, "A", kind="order_expired"),
              _ev(313, "A", kind="order_censored"), _ev(314, "A", kind="dropoff")]
    assert _make(events).estimate(7) == {"A": 0.5}


def test_t3_bien_bucket_t_bang_idx_b_thuoc_bucket_idx():
    # event t == 420.0 = 7·60 thuộc bucket 7 ⇒ NGOÀI cửa sổ [lo, 7) — không rò cùng-thời-điểm
    events = [_ev(310, "A"), _ev(420.0, "A")]
    assert _make(events).estimate(7) == {"A": 0.5}
    # còn 419.999 (round 3 chữ số của log()) vẫn thuộc bucket 6 ⇒ được đếm
    events2 = [_ev(310, "A"), _ev(419.999, "A")]
    assert _make(events2).estimate(7) == {"A": 1.0}


def test_t3_clip_first_op_bucket_khong_keo_lambda_xuong_bang_so_0_cau_truc():
    # estimate(6), k=3: cửa sổ thô [3,6) dính 2 bucket đóng cửa ⇒ clip lo=5, n_buckets=1
    events = [_ev(310, "A"), _ev(320, "A")]
    assert _make(events).estimate(6) == {"A": 2.0}   # 2/1, KHÔNG phải 2/3


def test_t3_n_buckets_khong_am_truoc_gio_mo_cua():
    # planner tick từ env.now=0 ⇒ idx 0..4 gọi estimator; idx=3: lo=5>3 ⇒ max(0, 3−5)=0 ⇒ COLD.
    # min_pickups=0 CỐ Ý — không cho vế `total < min_n` che bug âm (bug ngủ spec §3.2).
    assert _make([], min_n=0).estimate(3) == {}


# --- T4: cold ⇒ IM LẶNG, không fallback -------------------------------------

def test_t4_cold_tra_dict_rong_khong_fallback():
    est = _make([_ev(310, "A")], min_n=5)
    out = est.estimate(7)                        # total=1 < min_n=5 ⇒ COLD
    assert out == {}                             # {} nghĩa đen — không phải λ oracle, không prior
    assert _make([], min_n=1).estimate(5) == {}  # idx == first_op_bucket: chưa bucket nào trọn


def test_t4_o_khong_quan_sat_khong_xuat_hien_voi_gia_0():
    # chỉ ô có Σ N > 0 mới có mặt — ô 0 quan sát vắng mặt, KHÔNG phải 0.0 (để ranked tự loại)
    lam = _make([_ev(310, "A")]).estimate(7)
    assert "B" not in lam and lam["A"] == 0.5


# --- T5 + T7: narrow reader, 0 oracle, 0 RNG trong module --------------------

def test_t5_constructor_chi_nhan_list_khong_nhan_world():
    # narrow reader: tham số đầu là chính list events — estimator không cầm object nào
    # có orders_sorted / demand_field trong tầm với. Chạy trọn một ngày event tổng hợp.
    events = [_ev(300 + i * 7, "A" if i % 3 else "B") for i in range(120)]
    est = RealizedDemandEstimator(events, start_min=START, bucket_min=B,
                                  window_buckets=3, min_pickups=1)
    for idx in range(0, 20):
        out = est.estimate(idx)
        assert isinstance(out, dict)


def test_t7_module_khong_cham_oracle_khong_rng():
    src = (Path(__file__).resolve().parents[1] / "src" / "gsm_sim"
           / "demand_estimator.py").read_text(encoding="utf-8")
    for cam in ("demand_field", "orders_sorted", "world", "rng", "random"):
        assert cam not in src, f"module estimator chứa token cấm: {cam!r}"


# --- T6: không phụ thuộc thời điểm gọi trong bucket --------------------------

def test_t6_estimate_giua_bucket_bang_tai_bien_bucket_exact():
    early = [_ev(310, "A"), _ev(370, "B")]
    late = [_ev(430, "A"), _ev(431, "A")]        # bucket 7 — "tương lai" so với estimate(7)
    e_mid = _make(early + late)                  # gọi khi list ĐÃ chứa event bucket 7
    e_edge = _make(early)                        # gọi đúng biên bucket
    assert e_mid.estimate(7) == e_edge.estimate(7)


def test_t6_goi_lui_idx_nho_hon_sau_khi_da_ingest_xa():
    events = [_ev(310, "A"), _ev(370, "A"), _ev(430, "A"), _ev(490, "A")]
    est = _make(events)
    ahead = est.estimate(9)                      # ingest tới t<540
    assert ahead == {"A": 1.0}
    assert est.estimate(7) == _make(events).estimate(7)   # gọi lùi vẫn exact
