"""CongestionField — độ tắc spatiotemporal suy từ phân phối đơn + route_effect sự kiện.

Nguồn: research/market/dispatch-signals-and-external-apis.md (NHÓM 1: S/D ratio, ETA),
specs/environment-variables.md. Giả định (Cường chốt): **phân phối đơn đặt biểu diễn độ tắc**
→ cell đông đơn giờ cao điểm chạy chậm hơn cell vắng.

Kết hợp với mưa qua survival product ở world._eff_speed (env.speed_factor(t, r_cong)):
    speed = base · (1 − r_rain) · (1 − r_cong)
r_cong ∈ [0, cap] theo (cell, giờ); route_effect sự kiện cộng thêm cục bộ quanh venue
(cũng survival — KHÔNG nhân demand, tránh double-count với λ_event).

Tắt được: congestion.enabled=false hoặc cap=0 → r_cong=0 (baseline bất biến).
"""

from __future__ import annotations

import math

from .config import Config
from .geo import grid_distance


class CongestionField:
    def __init__(self, orders: list, cfg: Config, env=None):
        cong = cfg.get("congestion", {}) or {}
        self.enabled = bool(cong.get("enabled", True))
        self.cap = float(cong.get("cap", 0.35))
        self.normalize = str(cong.get("normalize", "global_peak"))  # global_peak | hour_peak
        self.env = env

        # demand_field[hour][cell] = số đơn (pickup) — nền suy độ đông
        self._field: dict[int, dict[str, float]] = {}
        for o in orders:
            h = int(o.t_min // 60) % 24
            cells = self._field.setdefault(h, {})
            cells[o.pickup_cell] = cells.get(o.pickup_cell, 0.0) + 1.0
        self._global_peak = max((v for cells in self._field.values() for v in cells.values()), default=1.0)
        self._hour_peak = {h: (max(cells.values()) if cells else 1.0) for h, cells in self._field.items()}

    def _base_r(self, cell: str, hour: int) -> float:
        """Độ tắc nền theo mật độ đơn cục bộ, chuẩn hoá về [0, cap]."""
        if not self.enabled or self.cap <= 0.0:
            return 0.0
        dens = self._field.get(hour, {}).get(cell, 0.0)
        if self.normalize == "hour_peak":
            denom = self._hour_peak.get(hour, 1.0)
        else:
            denom = self._global_peak
        return self.cap * (dens / denom) if denom > 0 else 0.0

    def _route_r(self, cell: str, hour: int) -> float:
        """route_effect sự kiện: cấm/giảm tốc cục bộ quanh venue trong cửa sổ sự kiện.
        r_route = (1 − speed_mult) · Gauss(khoảng cách H3). Survival gộp nhiều sự kiện."""
        if self.env is None or not getattr(self.env, "events", None):
            return 0.0
        t = hour * 60 + 30
        surv = 1.0
        for ev in self.env.events:
            mult = getattr(ev, "route_speed_mult", 1.0)
            if mult >= 1.0:
                continue
            # cửa sổ sự kiện tác động tuyến (gồm ingress + egress)
            t_lo = ev.t_start_min - ev.ramp_in_min
            t_hi = ev.t_end_min + ev.egress_min
            if not (t_lo <= t <= t_hi):
                continue
            gd = grid_distance(cell, ev.venue_cell)
            sig = getattr(ev, "route_sigma_cells", 1.5)
            if gd < 0 or gd > 4 * sig:
                continue
            g = math.exp(-(gd ** 2) / (2 * sig ** 2))
            r_ev = (1.0 - mult) * g
            surv *= (1.0 - r_ev)
        return 1.0 - surv

    def r(self, cell: str, hour: int) -> float:
        """Tổng r_cong ∈ [0, 0.95]: survival gộp tắc-nền × route_effect.
        C-2: enabled=false → 0 TOÀN BỘ (kể cả event route_effect) — đúng docstring
        'tắt được về baseline'; route_effect thuộc speed model nên đi theo toggle này."""
        if not self.enabled:
            return 0.0
        base = self._base_r(cell, hour)
        route = self._route_r(cell, hour)
        r = 1.0 - (1.0 - base) * (1.0 - route)
        return min(0.95, max(0.0, r))
