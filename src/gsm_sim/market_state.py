"""Producer `MarketStateView` cho sim — đếm CUNG từ `World` (T-045a b2).

Lõi tính toán nằm ở `gsm_core.features.market_state.build_market_state` (thuần hàm, 9 test).
File này chỉ làm **một việc**: dịch trạng thái sống của `World` thành số cung, rồi gọi lõi đó.
Cố ý không tính lại trần/tỷ lệ ở đây — hai chỗ cùng tính một luật chính là mẫu lỗi T-046.

## Ba loại cung, và vì sao phân biệt

| loại | ai | vì sao |
|---|---|---|
| `supply_now` | actor `IDLE` theo ô | người **nhận được đơn ngay** |
| `supply_incoming` (đang đi) | actor có `enroute_cell` | sắp thành cung của ô đích |
| `supply_incoming` (đã khuyên) | advice vừa phát, chưa thực hiện | ⭐ **thứ chống dồn cục** |

Vế thứ ba là điểm khác biệt so với bản đồ nhiệt của hãng (hồ sơ `19-*` §4). Thiếu nó thì trong
cùng một bucket, mọi tài xế hỏi sau đều thấy ô tốt nhất còn trống và đều được khuyên tới đó —
*fallacy of composition* mà hồ sơ `07` đã đo được.

## Giới hạn có nhãn (v1)

- Người đang **nghỉ / đổi pin** sẽ quay lại làm việc nhưng chưa được mô hình hoá là cung tương lai.
- Người đang **chở khách** không tính là cung sắp tới ô trả khách — chân trời dài và bất định.
- `expected_demand` là **PROXY**: λ từ config (`World.demand_field`), không phải cầu quan sát được.
"""

from __future__ import annotations

from gsm_core.features.market_state import build_market_state

from .entities import ActorState

# Giờ/bucket → nhãn ISO. Sim chạy trong MỘT ngày nên chỉ cần giờ; giữ ngày gốc cho khớp
# `advice_bridge._iso`.
_BASE_DATE = "2026-07-01"


def count_supply(actors, pending_targets: dict[int, str] | None = None
                 ) -> tuple[dict[str, int], dict[str, int]]:
    """Đếm `(supply_now, supply_incoming)` theo ô.

    `pending_targets`: `{actor_id: cell}` — lời khuyên vị trí **đã phát mà tài xế chưa đi**.

    Quy tắc chống đếm đôi: một actor đóng góp **tối đa một** đơn vị cung. Nếu đang di chuyển thì
    tin `enroute_cell` (chuyển động thật) và **bỏ qua** lệnh trong sổ — sổ có thể là lệnh cũ chưa
    dọn, còn vị trí thì không nói dối.
    """
    pending = pending_targets or {}
    now: dict[str, int] = {}
    inc: dict[str, int] = {}
    for a in actors:
        if a.state == ActorState.OFFLINE:
            continue
        target = getattr(a, "enroute_cell", None)
        if target:
            inc[target] = inc.get(target, 0) + 1
            continue
        if a.state == ActorState.IDLE and a.cell:
            now[a.cell] = now.get(a.cell, 0) + 1
        pend = pending.get(a.actor_id)
        if pend:
            inc[pend] = inc.get(pend, 0) + 1
    return now, inc


class MarketStateProducer:
    """Dựng view theo bucket, có cache.

    Cache là **bắt buộc về hiệu năng**: vòng idle hỏi mỗi 2 phút cho ~90 actor suốt ~20 giờ. Nhưng
    cache **không được sống quá bucket** — quyết định bằng ảnh cung của một giờ trước là đúng loại
    lỗi "số cũ trông như số mới" mà `supply_cell_hhi` từng mắc.
    """

    def __init__(self, world, bucket_min: int = 60, supply_available: bool = True):
        self.world = world
        self.bucket_min = int(bucket_min)
        # Cờ để dựng lại kịch bản `absent` (data thật không có cung theo ô). Solver phải chạy
        # được ở cả ba mức available/degraded/absent — spec §3.
        self.supply_available = bool(supply_available)
        adv = (world.cfg.get("advice", {}) or {}) if hasattr(world, "cfg") else {}
        self.trips_per_hour_est = float(adv.get("trips_per_hour_est", 1.5) or 1.5)
        self._cache: dict[int, dict] = {}
        self.pending_targets: dict[int, str] = {}

    def _demand(self, hour: int) -> dict[str, float]:
        return dict(self.world.demand_field.get(hour, {}) or {})

    def view(self, now_min: float) -> dict:
        idx = int(now_min) // self.bucket_min
        hit = self._cache.get(idx)
        if hit is not None:
            return hit
        self._cache.clear()               # chỉ giữ bucket hiện tại — không để số cũ sống sót
        hour = (idx * self.bucket_min // 60) % 24
        acts = self.world.actors
        acts = list(acts.values()) if hasattr(acts, "values") else list(acts)
        if self.supply_available:
            now, inc = count_supply(acts, self.pending_targets)
        else:
            now, inc = None, None
        start = idx * self.bucket_min
        v = build_market_state(
            t_now=f"{_BASE_DATE}T{(start // 60) % 24:02d}:{start % 60:02d}:00+07:00",
            bucket_min=self.bucket_min,
            demand_by_cell=self._demand(hour),
            supply_now_by_cell=now,
            supply_incoming_by_cell=inc,
            trips_per_driver_per_bucket=self.trips_per_hour_est * self.bucket_min / 60.0,
            source="MOCK",
        )
        self._cache[idx] = v
        return v
