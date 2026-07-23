"""PolicyBundle — đọc từ L0 policy_bundle record (schema), độc lập gsm_sim runtime.

Nguồn số tài chính/điểm cho solver. Logic khớp gsm_sim/policy.py nhưng đọc từ record
(schema-validated) thay vì sim config — gsm_core không phụ thuộc simulator.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyBundle:
    version: str
    base_fare_vnd: int
    base_km: float
    per_km_vnd: int
    driver_share: float
    point_peak: int
    point_normal: int
    point_window_hours: frozenset[int]
    point_peak_hours: frozenset[int]
    day_bonus_tiers: tuple[tuple[int, int], ...]  # (điểm, thưởng VND) tăng dần
    bonus_min_acceptance: float
    bonus_min_completion: float

    @classmethod
    def from_record(cls, rec: dict) -> "PolicyBundle":
        p = rec["points"]
        th = rec.get("thresholds", {})
        tiers = tuple((int(pt), int(vnd)) for pt, vnd in rec["day_bonus_tiers"])
        return cls(
            version=str(rec["version"]),
            base_fare_vnd=int(rec["fare"]["base_vnd"]),
            base_km=float(rec["fare"]["base_km"]),
            per_km_vnd=int(rec["fare"]["per_km_vnd"]),
            driver_share=float(rec["driver_share"]),
            point_peak=int(p["peak"]), point_normal=int(p["normal"]),
            point_window_hours=frozenset(int(h) for h in p["window_hours"]),
            point_peak_hours=frozenset(int(h) for h in p["peak_hours"]),
            day_bonus_tiers=tiers,
            bonus_min_acceptance=float(th.get("bonus_min_acceptance", 0.85)),
            bonus_min_completion=float(th.get("bonus_min_completion", 0.85)),
        )

    def trip_points(self, order_hour: int) -> int:
        """Điểm cho 1 cuốc theo giờ khách đặt."""
        if order_hour not in self.point_window_hours:
            return 0
        return self.point_peak if order_hour in self.point_peak_hours else self.point_normal

    def points_per_trip_estimate(self, hour: int) -> float:
        """Điểm/cuốc lý thuyết tại giờ (cho fallback khi thiếu lịch sử)."""
        pts = self.trip_points(hour)
        return float(pts) if pts > 0 else float(self.point_normal)

    def next_tier_gap(self, points: int) -> tuple[int, int] | None:
        """(điểm còn thiếu, thưởng mốc kế) hoặc None nếu đã đạt mốc cao nhất."""
        for tier_pts, tier_vnd in self.day_bonus_tiers:
            if points < tier_pts:
                return (tier_pts - points, tier_vnd)
        return None

    def bonus_at(self, points: int) -> int:
        """Thưởng ứng với số điểm (mốc cao nhất đạt được) — CHƯA xét ràng buộc tỷ lệ."""
        bonus = 0
        for tier_pts, tier_vnd in self.day_bonus_tiers:
            if points >= tier_pts:
                bonus = tier_vnd
        return bonus

    def is_peak(self, hour: int) -> bool:
        return hour in self.point_peak_hours
