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

    Quy tắc chống đếm đôi: một actor đóng góp **tối đa một** đơn vị cung **trong mỗi sổ**. Nếu
    đang di chuyển thì tin `enroute_cell` (chuyển động thật) và **bỏ qua** lệnh trong sổ — sổ có
    thể là lệnh cũ chưa dọn, còn vị trí thì không nói dối.

    ⚠ E1b/ADV-09 (2026-08-06) — ĐỌC CHO ĐÚNG trước khi "sửa": actor IDLE có lệnh chờ xuất hiện
    ở **CẢ HAI sổ CÓ CHỦ Ý** — họ là cung tại chỗ THẬT (dispatcher vẫn match được họ ở ô đang
    đứng cho tới khi họ đi) *và* là cung sắp tới của ô đích (⭐ chống dồn cục). `now` và `inc` là
    hai sổ ngữ nghĩa KHÁC NHAU, không phải một tổng; consumer cộng gộp hai sổ sẽ bảo thủ (trần
    capacity trừ kép) — đó là đánh đổi đã chọn. Review r10/ADV-09 từng đọc câu "tối đa một đơn
    vị" thành bất biến TRÊN TỔNG và đề xuất bỏ actor khỏi `now` — làm `now` NÓI DỐI về cung
    match-được. Test ghim: `test_market_state_sim_producer.py` (cả hai sổ + bảo toàn từng sổ).
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


def count_idle_wait(actors) -> dict[str, tuple[int, float]]:
    """E10b (spec e10-advisor-noisy §4.2): `(n_idle, median idle_streak_min)` theo Ô.

    Mẫu = MỌI actor IDLE (platform quan sát mọi tài xế; `coverage` chỉ quyết định ai được
    NHẬN lời khuyên — lọc ở tầng ứng viên, không phải ở đây). READ-ONLY tuyệt đối trên
    `idle_streak_min` — biến này đang nuôi bản năng sốt ruột (`behavior.py`); mọi ý "sửa
    semantics cho sạch" đổi hành vi và bị CẤM trong cycle E10.
    """
    from statistics import median
    by_cell: dict[str, list[float]] = {}
    for a in actors:
        if a.state == ActorState.IDLE and a.cell:
            by_cell.setdefault(a.cell, []).append(float(a.idle_streak_min))
    return {c: (len(v), float(median(v))) for c, v in by_cell.items()}


def wait_fired_cells(stats: dict[str, tuple[int, float]],
                     threshold_min: float, min_idle: int) -> set[str]:
    """Luật trigger E10b — pre-registered, ngưỡng TUYỆT ĐỐI (spec §4.2 giữ nguyên ba lý do
    bác percentile): fire ⇔ `n_idle ≥ min_idle ∧ median > T`. `min_idle` chặn luật
    per-driver lách cửa sau (n=1 ⇒ "median theo Ô" là chờ của đúng một người)."""
    return {c for c, (n, med) in stats.items() if n >= min_idle and med > threshold_min}


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
        # Cycle Q / ĐA-09 §2.2 — belief cầu RIÊNG của advisor cho fictitious play:
        # `{hour: {cell: λ}}`, khoá giờ chịu cả int lẫn str (YAML). CHỈ producer này đọc —
        # `_actor_demand_hint` (bản năng tài xế) tuyệt đối không; nếu bản năng cũng ăn theo
        # belief lặp thì vòng lặp đang đổi THẾ GIỚI chứ không phải advisor (test canh bằng
        # cách tắt planner: override có/không phải cho trace y hệt). Dữ liệu là aggregate
        # của RUN KHÁC (cross-run learning) — không phải future-leak trong run.
        ov = adv.get("market_demand_override") or None
        self.demand_override: dict[int, dict[str, float]] | None = (
            {int(h): {str(c): float(v) for c, v in cells.items()}
             for h, cells in ov.items()} if ov else None)
        # E10 (specs/simulation/e10-advisor-noisy.md §2): nguồn cầu là THAM SỐ của producer.
        # `oracle` (default) = đường cũ nguyên trạng từng bit; `realized` = λ̂ từ cuốc ĐÃ ĐÓN
        # (RealizedDemandEstimator — narrow reader, chỉ cầm list events + scalars, không cầm
        # world). Giá trị lạ ⇒ nổ ngay: fail-loud thắng hidden fallback (họ lỗi D-R12).
        src = str(adv.get("market_demand_source") or "oracle")
        if src not in ("oracle", "realized"):
            raise ValueError(f"advice.market_demand_source={src!r} — chỉ nhận oracle|realized")
        self.demand_source = None
        if src == "realized":
            if self.demand_override is not None:
                # hai belief THAY THẾ nhau (xem comment `_demand`) — trộn là vô nghĩa
                raise ValueError("market_demand_source=realized không đi cùng "
                                 "market_demand_override: hai belief thay thế nhau")
            if self.bucket_min != 60:
                # phạm vi đo E10 pin b=60 (spec §3.2 — mọi neo/độ lớn derive ở b này);
                # muốn b khác phải re-derive rồi gỡ chốt, không âm thầm chạy tiếp
                raise ValueError(f"market_demand_source=realized đòi bucket_min=60 "
                                 f"(đang {self.bucket_min}) — spec e10 §3.2")
            from .demand_estimator import RealizedDemandEstimator
            rd = adv.get("realized_demand") or {}
            self.demand_source = RealizedDemandEstimator(
                world.events, start_min=int(world.cfg.get("time.start_min")),
                bucket_min=self.bucket_min,
                window_buckets=int(rd.get("window_buckets", 3)),
                min_pickups=int(rd.get("min_pickups", 5)))
        self._cache: dict[int, dict] = {}
        self.pending_targets: dict[int, str] = {}

    def _demand(self, hour: int, idx: int) -> dict[str, float]:
        if self.demand_source is not None:
            # E10a: λ̂ realized theo bucket planner — COLD trả {} (advisor im lặng),
            # tuyệt đối không rơi về demand_field/override.
            return self.demand_source.estimate(idx)
        if self.demand_override is not None:
            # THAY THẾ (không merge): fictitious play cần kiểm soát trọn belief; merge nửa
            # vời sẽ trộn hai thế hệ belief và không hội tụ được về bất kỳ đâu.
            return dict(self.demand_override.get(hour, {}) or {})
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
        dem = self._demand(hour, idx)
        v = build_market_state(
            t_now=f"{_BASE_DATE}T{(start // 60) % 24:02d}:{start % 60:02d}:00+07:00",
            bucket_min=self.bucket_min,
            demand_by_cell=dem,
            supply_now_by_cell=now,
            supply_incoming_by_cell=inc,
            trips_per_driver_per_bucket=self.trips_per_hour_est * self.bucket_min / 60.0,
            source="MOCK",
        )
        if self.demand_source is not None:
            # E10 §3.3/§3.6: log MỘT lần/bucket (nhánh cache-miss này) — diag cho B1 và
            # % bucket câm. Mode oracle tuyệt đối không log gì (neutrality, test T9 canh).
            # Cache là hợp đồng "một ảnh mỗi bucket": ai xoá cache giữa bucket sẽ không đổi
            # λ̂ (estimator chốt cửa sổ tại biên bucket) nhưng sẽ chụp lại CUNG.
            est = self.demand_source
            if dem:
                self.world.log(-1, "demand_est", "", idx=idx,
                               total=est.last_total, n_buckets=est.last_n_buckets,
                               n_cells=len(dem),
                               cells={c: [(int(now.get(c, 0)) + int(inc.get(c, 0))
                                           if now is not None else None),
                                          round(lam, 6)]
                                      for c, lam in sorted(dem.items())})
            else:
                self.world.log(-1, "demand_est_cold", "", idx=idx,
                               total=est.last_total, n_buckets=est.last_n_buckets)
        self._cache[idx] = v
        return v
