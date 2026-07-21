"""Sim Policy Bundle v0 (MOCK). Nguồn: specs/sim-policy-bundle-v0.md.

Tất cả số đọc từ config (không hard-code). Cung cấp: fare, payout, điểm/cuốc,
mốc thưởng ngày, chi phí theo track. KHÔNG phải số thật của GSM.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import Config


@dataclass(frozen=True)
class PolicyBundle:
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
    version: str

    @classmethod
    def from_config(cls, cfg: Config) -> "PolicyBundle":
        p = cfg.get("policy")
        tiers = tuple((int(pt), int(vnd)) for pt, vnd in p["day_bonus_tiers"])
        return cls(
            base_fare_vnd=int(p["base_fare_vnd"]),
            base_km=float(p["base_km"]),
            per_km_vnd=int(p["per_km_vnd"]),
            driver_share=float(p["driver_share"]),
            point_peak=int(p["point_peak"]),
            point_normal=int(p["point_normal"]),
            point_window_hours=frozenset(int(h) for h in p["point_window_hours"]),
            point_peak_hours=frozenset(int(h) for h in p["point_peak_hours"]),
            day_bonus_tiers=tiers,
            bonus_min_acceptance=float(p["bonus_min_acceptance"]),
            bonus_min_completion=float(p["bonus_min_completion"]),
            version=str(cfg.get("meta.policy_bundle_version", "sim-policy-v0")),
        )

    # --- Fare & payout ---

    def gross_fare(self, dist_km: float) -> int:
        """Cước gross (VND) cho một cuốc dài dist_km."""
        extra = max(0.0, dist_km - self.base_km)
        return int(round(self.base_fare_vnd + extra * self.per_km_vnd))

    def driver_payout_from_gross(self, gross_vnd: int) -> int:
        """Phần tài xế nhận (chưa gồm thưởng), = gross × share."""
        return int(round(gross_vnd * self.driver_share))

    # --- Điểm thưởng ---

    def trip_points(self, order_hour: int) -> int:
        """Điểm cho một cuốc theo GIỜ KHÁCH ĐẶT."""
        if order_hour not in self.point_window_hours:
            return 0
        if order_hour in self.point_peak_hours:
            return self.point_peak
        return self.point_normal

    def day_bonus(self, points: int, acceptance: float, completion: float) -> int:
        """Thưởng ngày: mốc cao nhất đạt được, chỉ khi đủ điều kiện tỷ lệ."""
        if acceptance < self.bonus_min_acceptance or completion < self.bonus_min_completion:
            return 0
        bonus = 0
        for tier_pts, tier_vnd in self.day_bonus_tiers:
            if points >= tier_pts:
                bonus = tier_vnd
        return bonus

    def next_tier_gap(self, points: int) -> tuple[int, int] | None:
        """(điểm còn thiếu, thưởng mốc kế) hoặc None nếu đã max. Dùng cho advice 'chốt mốc'."""
        for tier_pts, tier_vnd in self.day_bonus_tiers:
            if points < tier_pts:
                return (tier_pts - points, tier_vnd)
        return None
