"""Điểm TRẢ KHÁCH phải bám CẦU (b0-D — Cường chốt 2026-07-28 "sửa trước khi đo b4").

## Vấn đề đo được (seed 1000, trước fix)

- `corr(cầu_đặt, nơi_trả_khách) = −0,226` — **anti-tương quan**: thế giới chủ động ném tài xế
  ra chỗ ít khách hơn nơi họ vừa rời;
- 10 ô cầu cao nhất chiếm **30,3%** lượt ĐẶT nhưng chỉ **2,2%** lượt TRẢ;
- **82,3%** cuốc trả NGOÀI lõi ⇒ buộc deadhead về (11,8% tổng thời gian).

## Root cause (không phải bug — MODEL GAP)

`_sample_drop` cân **thuần theo khoảng-cách-mục-tiêu**: vùng được phép trả 316 ô nhưng lõi chỉ
85 (26,9%), và distance-decay đẩy điểm trả ra vành ngoài ⇒ tỷ lệ rơi vào lõi (17,7%) còn thấp
hơn cả chọn đều. Trong khi thực tế người ta đi TỚI chỗ đông (nhà, văn phòng, TTTM) — chính những
nơi phát sinh cầu.

## Thiết kế fix

Nhân thêm hệ số cầu **pha tuyến tính** vào trọng số distance-decay:

    m(c) = 1 + alpha × (w_demand(c)/w̄ − 1),  kẹp ≥ 0

- `alpha = 0` ⇒ m ≡ 1.0 **chính xác từng bit** ⇒ trace cũ y hệt (tắt được về baseline);
- `alpha = 1` ⇒ m tỷ lệ thuận cầu (ô không cầu → 0);
- alpha giữa ⇒ ô buffer (cầu 0) vẫn sống với trọng số 1−alpha — **cố ý khác** công thức luỹ thừa
  `(w/w̄)^alpha` trong preview đã duyệt: luỹ thừa với w=0 giết SẠCH mọi ô buffer ở mọi alpha>0,
  tức không còn cuốc nào trả ngoài lõi — phi thực tế theo chiều ngược lại. Pha tuyến tính có
  ảnh hưởng bị chặn và đúng bằng 1 tại alpha=0.
"""

from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from gsm_sim import geo
from gsm_sim.config import Config
from gsm_sim.demand import generate_orders
from gsm_sim.policy import PolicyBundle

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "research" / "simulation" / "data"


@pytest.fixture(scope="module")
def base_cfg():
    return Config.load(ROOT / "configs" / "pilot_dongda.yaml")


@pytest.fixture(scope="module")
def grid():
    return geo.build_grid(DATA / "dd_geom.json", DATA / "batt_dd.json", DATA / "poi_dd.json", 9, 8)


def _with_alpha(base_cfg, alpha: float) -> Config:
    c = Config(copy.deepcopy(base_cfg.data), base_cfg.root_dir)
    c.data.setdefault("demand", {})["drop_demand_alpha"] = alpha
    return c


def _orders(base_cfg, grid, alpha: float, seed: int = 1000):
    cfg = _with_alpha(base_cfg, alpha)
    return generate_orders(grid, cfg, PolicyBundle.from_config(cfg), seed)


def _corr_pick_drop(orders) -> float:
    pick = Counter(o.pickup_cell for o in orders)
    drop = Counter(o.drop_cell for o in orders)
    cells = sorted(set(pick) | set(drop))
    pv = np.array([pick.get(c, 0) for c in cells], float)
    dv = np.array([drop.get(c, 0) for c in cells], float)
    return float(np.corrcoef(pv, dv)[0, 1])


def test_alpha_zero_reproduces_old_trace_exactly(base_cfg, grid):
    """`alpha = 0` ⇒ trace Y HỆT từng đơn — không phải "gần giống".

    Đây là điều kiện để mọi baseline cũ còn so sánh được: m(c) = 1 + 0×(…) = 1.0 chính xác
    IEEE, nhân vào trọng số không đổi bit nào, `rng.choice` rút y hệt.
    """
    # Config "không có khoá" phải DỰNG bằng cách XOÁ khoá — không dùng pilot config trực tiếp:
    # từ khi alpha=0.4 thành mặc định trong pilot, "config gốc" đã mang khoá ≠ 0 và test này
    # từng ĐỎ OAN vì so 0.4 với 0.0 (lộ ra ở suite 2026-07-28, sửa tại đây).
    c_absent = Config(copy.deepcopy(base_cfg.data), base_cfg.root_dir)
    (c_absent.data.get("demand") or {}).pop("drop_demand_alpha", None)
    old = generate_orders(grid, c_absent, PolicyBundle.from_config(c_absent), 1000)
    new = _orders(base_cfg, grid, alpha=0.0, seed=1000)
    assert len(old) == len(new)
    for a, b in zip(old, new):
        assert (a.pickup_cell, a.drop_cell, a.dist_km, a.gross_vnd) == \
               (b.pickup_cell, b.drop_cell, b.dist_km, b.gross_vnd), \
            f"alpha=0 làm lệch trace tại order {a.order_id} — cờ tắt không tái lập baseline"


def test_alpha_positive_kills_the_anticorrelation(base_cfg, grid):
    """Bật cầu ⇒ corr(cầu, nơi trả) phải RÕ RỆT tốt hơn mức −0,226 đã đo.

    Không đòi một giá trị đích cụ thể ở đây (đó là việc của bảng quét + Cường chọn); chỉ khoá
    HƯỚNG: alpha cao hơn không được làm corr tệ đi.
    """
    c0 = _corr_pick_drop(_orders(base_cfg, grid, alpha=0.0))
    c6 = _corr_pick_drop(_orders(base_cfg, grid, alpha=0.6))
    assert c6 > c0 + 0.2, (
        f"alpha=0.6 cho corr {c6:+.3f} vs {c0:+.3f} ở alpha=0 — hệ số cầu không có tác dụng "
        f"hoặc bị nuốt ở tầng dưới (mẫu lỗi T-046: thêm tham số mà consumer không nhận)")


def test_distance_distribution_not_destroyed(base_cfg, grid):
    """Bám cầu KHÔNG được phá phân phối quãng đường — hai ràng buộc phải sống chung.

    Nếu median dist trôi quá 15% thì hệ số cầu đang thắng distance-decay, tức cuốc bị kéo về
    ô đông bất kể xa gần — sai kiểu khác (cước/điểm/pin đều ăn theo dist).
    """
    d0 = np.median([o.dist_km for o in _orders(base_cfg, grid, alpha=0.0)])
    d6 = np.median([o.dist_km for o in _orders(base_cfg, grid, alpha=0.6)])
    assert abs(d6 - d0) / d0 < 0.15, f"median dist {d0:.2f} → {d6:.2f} km — lệch quá 15%"


def test_buffer_cells_still_receive_some_drops(base_cfg, grid):
    """Ô buffer (cầu = 0) vẫn phải nhận MỘT PHẦN cuốc ở alpha trung gian.

    Đây là lý do dùng pha tuyến tính thay vì luỹ thừa: thực tế vẫn có người về nhà ngoài lõi.
    Nếu 100% cuốc trả trong lõi thì đã sửa lố theo chiều ngược lại.
    """
    orders = _orders(base_cfg, grid, alpha=0.6)
    outside = sum(1 for o in orders if not grid.is_core(o.drop_cell))
    assert outside > 0, "alpha=0.6 mà không còn cuốc nào trả ngoài lõi — sửa lố, mất realism"
    share = outside / len(orders)
    assert share < 0.823, f"tỷ lệ trả ngoài lõi {share:.1%} không giảm so với 82,3% trước fix"
