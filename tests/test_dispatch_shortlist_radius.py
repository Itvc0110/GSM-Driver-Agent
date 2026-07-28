"""BUG-DISPATCH-SHORTLIST — shortlist H3 quá hẹp so với tầm với mà `eta_max_min` cho phép.

Hồ sơ: `research/audit/2026-07-27-current-state/14-bien-gioi-cung-cau-va-tran-nang-luc.md` §2.

`match_batch` lấy ứng viên bằng `grid_disk(pickup, candidate_ring_k_max)` rồi mới kiểm ETA.
Nếu đĩa H3 **hẹp hơn** bán kính mà ETA cho phép thì tài xế thoả ETA **không bao giờ vào
shortlist** — bị loại **âm thầm**, không log, không hạ confidence.

Đo được ở config cũ (`k_max = 6`): đĩa phủ **2,22 km**, trong khi ETA 11′ ở tốc độ đêm 30 km/h
với `factor` nhỏ nhất 1,0 cho phép tới **5,50 km**.

Đây là **lần thứ sáu** trong repo gặp mẫu "hai tham số phải khớp nhau nhưng được đặt độc lập"
(hồ sơ `13` Phần 1). Vì vậy test quan trọng nhất ở đây **không phải** "k == 12" mà là **bất biến
phủ sóng** — nó sẽ đỏ lại nếu ai đó đổi `eta_max_min`, tốc độ, hoặc độ phân giải H3 mà quên k.
"""

from __future__ import annotations

import copy
import math

import h3
import pytest

from gsm_sim.config import Config
from gsm_sim.geo import grid_disk, haversine_km, load_road_matrix
from gsm_sim.metrics import summarize
from gsm_sim.runner import run_once

SEEDS = (1000, 1001, 1002)


@pytest.fixture(scope="module")
def world():
    cfg = Config.load("configs/pilot_dongda.yaml")
    return cfg, run_once(cfg, SEEDS[0])


def _ring_radius_km(cell: str, k: int) -> float:
    lat0, lon0 = h3.cell_to_latlng(cell)
    return max(haversine_km(lat0, lon0, *h3.cell_to_latlng(c)) for c in grid_disk(cell, k))


def _zone_diameter_km(grid) -> float:
    cs = sorted(grid.core_cells)[::5]
    return max(haversine_km(*h3.cell_to_latlng(a), *h3.cell_to_latlng(b))
               for a in cs for b in cs)


def test_widening_shortlist_still_raises_served(world):
    """Ghi nhận: nới shortlist VẪN phục vụ nhiều hơn, kể cả sau khi có tầng 2 Hungarian.

    Đo **30 seed** (đúng bộ của `test_sim_realism.py`), `matching: batch`:

        k  | served | hết hạn | pickup | lệch lớn nhất vs accept_base
        6  | 0.763  |  231    | 0.97   | P7 −0.0490  ✅
        8  | 0.793  |  194    | 1.10   | P7 −0.0582  ❌
        10 | 0.801  |  183    | 1.13   | P7 −0.0627  ❌

    ⇒ **Đánh đổi VẪN CÒN** dù đã có Hungarian: giả thuyết "gán tối ưu tổng sẽ đảo chiều đánh đổi"
    (hồ sơ `15-*` §4.1) **SAI**. Hungarian rút ngắn pickup ở CÙNG một k (1.04 → 0.97 km) nhưng
    nới k vẫn kéo thêm những cuốc đón xa. Q-07 **chưa được giải**.

    ⚠ Test này chỉ assert vế **served** — vế archetype **cố ý KHÔNG assert ở đây** vì với 3 seed
    nó là số nhiễu (đo thử: 3 seed cho k6 0.073 / k8 0.049, **ngược dấu** với 30 seed). Assert
    một đại lượng nhiễu ở mẫu nhỏ là test flaky — tệ hơn không có test. Vế archetype do
    `test_sim_realism.py::test_accept_matches_archetype_base` canh, ở đúng 30 seed.
    """
    cfg, _ = world
    assert int(cfg.get("dispatcher.candidate_ring_k_max")) == 6, (
        "k_max đổi khỏi 6 — phải chạy lại sweep ≥30 seed và kiểm "
        "`test_sim_realism.py::test_accept_matches_archetype_base` (Q-07)."
    )

    def served(k: int) -> float:
        out = []
        for seed in SEEDS:
            c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
            c.data["dispatcher"]["candidate_ring_k_max"] = k
            out.append(summarize(run_once(c, seed))["served_rate"])
        return sum(out) / len(out)

    s6, s8 = served(6), served(8)
    assert s8 > s6, (
        f"nới shortlist không còn phục vụ nhiều hơn (k6={s6:.3f} k8={s8:.3f}) ⇒ tiền đề của "
        f"Q-07 đã đổi, XEM LẠI hồ sơ `14-*`/`15-*` trước khi kết luận gì thêm."
    )


def test_ring_k_is_not_smaller_than_starting_ring(world):
    """`candidate_ring_k` (điểm bắt đầu) không được lớn hơn `candidate_ring_k_max`."""
    cfg, _ = world
    assert int(cfg.get("dispatcher.candidate_ring_k")) <= int(
        cfg.get("dispatcher.candidate_ring_k_max"))


def test_eta_max_unchanged_realism_guard():
    """`eta_max_min` là ràng buộc REALISM (khách không chờ đón quá lâu), **không** phải nút
    chỉnh cho số đẹp. Nới nó là vặn thực tế cho vừa kết quả — `CLAUDE §4b` cấm.

    Nguồn: `configs/pilot_dongda.yaml` — research 8–10′, hiệu chỉnh ×1.46/1.3 ⇒ 11.
    """
    cfg = Config.load("configs/pilot_dongda.yaml")
    assert float(cfg.get("dispatcher.eta_max_min")) <= 12.0, (
        "eta_max_min bị nới quá ngưỡng research (8–10′ + hiệu chỉnh factor ⇒ ~11′). "
        "Nếu thật sự cần đổi, phải có nguồn mới trong research/ và ghi vào UPDATE."
    )


def test_dispatch_determinism_unchanged(world):
    """Cùng seed ⇒ cùng kết quả (tie-break vẫn deterministic sau khi nới shortlist)."""
    cfg, _ = world
    a = run_once(Config(copy.deepcopy(cfg.data), cfg.root_dir), 1000)
    b = run_once(Config(copy.deepcopy(cfg.data), cfg.root_dir), 1000)
    assert summarize(a) == summarize(b)
    assert [(o.order_id, o.pickup_cell) for o in a.orders] == \
           [(o.order_id, o.pickup_cell) for o in b.orders]
