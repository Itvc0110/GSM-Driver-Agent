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
    # B3 (PLAN-cycle-wx, 2026-07-29) — vế A5 VISION-ALIGNMENT: policy mang CHI PHÍ để
    # solver cập nhật giá trị biến theo chính sách. `track` cần cho resolve theo cohort.
    # None = bundle 1.0.0 (không biết chi phí) ⇒ resolve trả UNKNOWN, không bịa.
    track: str | None = None
    costs: dict | None = None

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
            track=rec.get("track") or None,
            costs=rec.get("costs") or None,
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


# ---------- B3: policy quyết định biến chi phí sống/chết (vế A5 VISION-ALIGNMENT) ----------

# Ba trạng thái — CẤM gộp UNKNOWN vào OFF_BY_POLICY: "biết là miễn phí" khác hẳn
# "không biết" (bài học hidden-fallback đã trả giá 3 lần: supply_hhi=0.0, soc=None→đầy,
# argmax bias). UNKNOWN ⇒ dùng 0 + caveat, KHÔNG bịa số (§5).
ACTIVE = "ACTIVE"
OFF_BY_POLICY = "OFF_BY_POLICY"
UNKNOWN = "UNKNOWN"


def _term(value: float, state: str, reason: str, source: str) -> dict:
    return {"value": float(value), "state": state, "reason": reason, "source": source}


def resolve_cost_params(policy: "PolicyBundle", as_of: str | None) -> dict:
    """Bảng tra THUẦN: (policy.costs, policy.track, as_of) → trạng thái + giá trị từng
    số hạng chi phí. Đây là phần RULE của ý tưởng A1 (agent chọn hàm/arg theo policy) —
    con số vẫn 100% từ policy bundle versioned; không LLM, không bịa.

    Trả {"battery": term, "cash_per_km": term} với term =
    {value, state ∈ ACTIVE|OFF_BY_POLICY|UNKNOWN, reason (đọc được — output PHẢI nói ra
    được "hiện không tính chi phí pin vì miễn phí tới <hạn>"), source}.
    """
    src = f"policy_v:{policy.version}"
    costs = policy.costs
    if costs is None:
        why = ("bundle không có khối costs (schema 1.0.0) — KHÔNG biết chi phí, "
               "dùng 0 + caveat, không bịa (§5)")
        return {"battery": _term(0.0, UNKNOWN, why, src),
                "cash_per_km": _term(0.0, UNKNOWN, why, src)}
    if as_of is None:
        why = "không có as_of — không xác định được chính sách nào đang hiệu lực"
        return {"battery": _term(0.0, UNKNOWN, why, src),
                "cash_per_km": _term(0.0, UNKNOWN, why, src)}

    day = str(as_of)[:10]
    free_until = costs.get("battery_free_until")
    by_track = costs.get("cash_cost_vnd_per_km_by_track") or {}
    track = policy.track or ""

    # --- số hạng PIN ---
    if free_until is not None and day <= str(free_until):
        battery = _term(0.0, OFF_BY_POLICY,
                        f"đổi pin miễn phí cho track '{track}' tới {free_until} "
                        f"(official) — số hạng pin BỎ khỏi objective, không phải đặt 0",
                        src)
    elif "swap_fee_vnd" in costs:
        battery = _term(costs["swap_fee_vnd"], ACTIVE,
                        f"sau {free_until or 'ưu đãi'}: phí đổi pin "
                        f"{costs['swap_fee_vnd']:.0f}đ/lượt — SOC thành biến kinh tế",
                        src)
    else:
        battery = _term(0.0, UNKNOWN, "costs không có swap_fee_vnd", src)

    # --- số hạng TIỀN MẶT/km ---
    if battery["state"] == ACTIVE and costs.get("swap_range_km_per_pack"):
        # pin trả phí ⇒ đ/km = phí/lượt ÷ tầm pack (cộng thêm nền theo track nếu có)
        per_km = costs["swap_fee_vnd"] / float(costs["swap_range_km_per_pack"])
        base = float(by_track.get(track, 0.0))
        cash = _term(per_km + base, ACTIVE,
                     f"{costs['swap_fee_vnd']:.0f}đ/lượt ÷ "
                     f"{costs['swap_range_km_per_pack']:.0f}km/pack"
                     + (f" + nền track {base:.0f}đ/km" if base else ""),
                     src)
    elif track in by_track:
        v = float(by_track[track])
        cash = _term(v, ACTIVE,
                     f"đ/km tiền mặt theo track '{track}' = {v:.0f}đ (policy costs)", src)
    else:
        cash = _term(0.0, UNKNOWN,
                     f"track '{track}' không có trong cash_cost_vnd_per_km_by_track", src)
    return {"battery": battery, "cash_per_km": cash}
