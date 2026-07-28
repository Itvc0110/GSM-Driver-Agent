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
    # Khoán tuần (Vận Doanh 23/02/2026) — None nếu policy chưa có số (TBC-với-GSM).
    # Solver KHÔNG được bịa số khi None (§5).
    weekly_quota: dict | None = None
    # Cycle P/① (2026-07-28): HẠN HIỆU LỰC của bundle. Schema L0 đã BẮT BUỘC `effective_from`
    # từ đầu nhưng code vứt đi — nên "pin miễn phí tới 31/03/2029" trông như hằng số vật lý
    # thay vì chính sách có hạn. Đây là nền cho A1 router-theo-policy (OPEN-THREADS §A1):
    # agent đọc trạng thái hiệu lực để định hình bài toán, KHÔNG tự bịa số.
    effective_from: str | None = None    # ISO date; None = nguồn không ghi (validity UNKNOWN)
    effective_to: str | None = None      # None = không có hạn trên ĐÃ BIẾT

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
            weekly_quota=rec.get("weekly_quota") or None,
            effective_from=rec.get("effective_from") or None,
            effective_to=rec.get("effective_to") or None,
        )

    def is_valid_at(self, as_of: str) -> bool | None:
        """Bundle có hiệu lực tại `as_of` (ISO date/datetime) không?

        Trả **None khi KHÔNG BIẾT** (nguồn không ghi hạn) — caller phải phân biệt "không biết"
        với "còn hiệu lực"; gộp hai cái là hidden fallback (bài học soc_pct=None ⇒ pin đầy).
        So sánh chuỗi ISO — cùng bất biến mà `shift_dp` dựa vào (chuỗi ISO so được như thời gian).
        """
        if not self.effective_from:
            return None
        d = str(as_of)[:10]
        if d < str(self.effective_from)[:10]:
            return False
        if self.effective_to and d > str(self.effective_to)[:10]:
            return False
        return True

    def has_weekly_quota(self) -> bool:
        """True khi policy có ĐỦ số khoán tuần để tính (không suy đoán)."""
        q = self.weekly_quota or {}
        return q.get("min_revenue_vnd") is not None

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
