"""`MarketStateView` — mở kênh thông tin CUNG cho solver (T-045a).

Nền: `specs/advisor-objective-model-v2.md` §3 + hồ sơ `19-*`.

Hai điều khiến view này khác một "bản đồ nhiệt" thường:

1. **Trừ cả CUNG ĐANG TỚI** — số tài xế đã được khuyên đi ô đó nhưng chưa tới. Không có nó thì
   90 tài xế hỏi cùng lúc nhận cùng một câu trả lời (*fallacy of composition*, hồ sơ `07`).
   Ngành cũng làm vậy: heatmap tốt tính theo *"phân bố đội xe hiện tại VÀ tương lai"*.
2. **Thiếu dữ liệu phải NÓI RA, không đoán bừa** — mỗi trường mang nhãn
   `available/degraded/absent`; thiếu cung ⇒ `sd_ratio = None` ⇒ solver **bỏ hẳn** lời khuyên vị
   trí, chứ không im lặng giả định. Đây là bài học `supply_cell_hhi` trả 0.0 âm thầm (UPDATE-075)
   và `soc_pct=None` ⇒ giả định pin đầy (UPDATE-079).
"""

from __future__ import annotations

import pytest

from gsm_core.features.market_state import build_market_state


def _mk(**kw):
    base = dict(
        t_now="2026-07-01T09:00:00+07:00",
        bucket_min=30,
        demand_by_cell={"a": 12.0, "b": 6.0, "c": 0.0},
        supply_now_by_cell={"a": 4, "b": 1, "c": 0},
        supply_incoming_by_cell={"a": 2, "b": 0, "c": 0},
        trips_per_driver_per_bucket=2.0,
        source="MOCK",
    )
    base.update(kw)
    return build_market_state(**base)


# ---------- Lõi: cung đang tới ----------

def test_incoming_supply_counts_against_a_cell():
    """Ô `a` có 4 người đang đứng + **2 người đang tới** ⇒ mẫu số là 6, không phải 4.

    Đây là điểm khác biệt chính so với bản đồ nhiệt của hãng — thứ họ không công bố là có."""
    v = _mk()
    a = v["cells"]["a"]
    assert a["supply_effective"] == 6, "chưa trừ cung đang tới ⇒ sẽ khuyên dồn vào ô đã đủ"
    assert a["sd_ratio"] == pytest.approx(12.0 / 6.0)


def test_capacity_left_excludes_incoming():
    """Trần còn lại = cầu/năng-suất − đang đứng − **đang tới**.

    a: 12/2 = 6 chỗ; đã có 4 + đang tới 2 ⇒ **còn 0**. Nếu quên `incoming` sẽ ra 2 ⇒ đẩy thêm
    2 người vào ô đã bão hoà.
    """
    v = _mk()
    assert v["cells"]["a"]["capacity_left"] == 0
    assert v["cells"]["b"]["capacity_left"] == 2      # 6/2=3, có 1, tới 0 → 2


def test_capacity_never_negative():
    v = _mk(supply_now_by_cell={"a": 99, "b": 1, "c": 0})
    assert v["cells"]["a"]["capacity_left"] == 0


# ---------- Thiếu dữ liệu: phải NÓI RA ----------

def test_absent_supply_disables_positioning_advice():
    """Không có dữ liệu cung ⇒ `sd_ratio = None` và nhãn `absent`.

    KHÔNG được im lặng coi cung = 0 (sẽ ra sd_ratio vô cùng ⇒ khuyên dồn hết vào đó)."""
    v = _mk(supply_now_by_cell=None, supply_incoming_by_cell=None)
    assert v["availability"]["supply"] == "absent"
    for c in v["cells"].values():
        assert c["sd_ratio"] is None
        assert c["capacity_left"] is None
    assert v["positioning_allowed"] is False, \
        "thiếu cung mà vẫn cho khuyên vị trí ⇒ đúng lỗi 'hidden fallback' đã trả giá 2 lần"


def test_degraded_when_incoming_unknown():
    """Biết cung hiện tại nhưng KHÔNG biết ai đang tới ⇒ `degraded`, vẫn chạy được nhưng
    confidence phải hạ (solver đọc nhãn này)."""
    v = _mk(supply_incoming_by_cell=None)
    assert v["availability"]["supply_incoming"] == "degraded"
    assert v["positioning_allowed"] is True
    assert v["cells"]["a"]["supply_effective"] == 4


def test_zero_supply_cell_is_not_infinite():
    """Ô có cầu nhưng KHÔNG ai ở đó: `sd_ratio` phải hữu hạn và có thứ hạng, không phải inf."""
    v = _mk(demand_by_cell={"a": 12.0, "z": 5.0}, supply_now_by_cell={"a": 4, "z": 0},
            supply_incoming_by_cell={"a": 2, "z": 0})
    z = v["cells"]["z"]
    assert z["sd_ratio"] is not None
    assert z["sd_ratio"] != float("inf")
    assert z["capacity_left"] == 2       # 5/2 = 2.5 → 2 chỗ


# ---------- Xếp hạng dùng được cho lời khuyên ----------

def test_ranking_prefers_underserved_cells():
    """Ô thiếu cung phải xếp trên ô thừa cung — đó là toàn bộ mục đích của view.

    (Bản đầu của test này mâu thuẫn với `test_ranking_excludes_cells_without_capacity`: nó đòi
    ô `a` phải có mặt trong xếp hạng, trong khi `a` đã hết trần nên bị loại — đúng thiết kế.
    Sửa: dùng bố trí mà CẢ HAI ô còn trần, để so đúng thứ hạng.)
    """
    v = _mk(demand_by_cell={"thua": 20.0, "thieu": 20.0},
            supply_now_by_cell={"thua": 8, "thieu": 2},
            supply_incoming_by_cell={"thua": 0, "thieu": 0})
    order = v["ranked_cells"]
    assert set(order) == {"thua", "thieu"}, f"cả hai ô còn trần đều phải được xét: {order}"
    assert order[0] == "thieu", f"ô thiếu cung phải đứng đầu, nhận được {order}"


def test_ranking_excludes_cells_without_capacity():
    """Ô đã hết trần KHÔNG được xuất hiện trong danh sách khuyên — chống dồn cục ngay từ view."""
    v = _mk()
    assert "a" not in v["ranked_cells"], "ô hết trần vẫn được khuyên ⇒ tạo herding"


def test_deterministic_and_labelled():
    a, b = _mk(), _mk()
    assert a == b
    assert a["source"] == "MOCK"
    assert a["schema_version"]
