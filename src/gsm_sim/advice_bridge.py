"""SIM-3 — CẦU NỐI advice → action.

Yêu cầu Cường (`DIRECTIVES-2026-07-24.md` §5.4): *"Dịch được kết quả gợi ý của advisor → action
của actor trong simulation."* Không có cầu nối này thì "làm theo chỉ dẫn" ở SIM-4 chỉ là chữ.

Cầu nối là **ánh xạ từ vựng ĐÓNG sang từ vựng ĐÓNG**, không phải hiểu ngôn ngữ tự nhiên:

    solver S2 (shift_dp)  ──►  ONLINE / REST / SWAP / END
                                       │
                                       ▼  (+ mô hình tuân thủ)
    actor                 ──►  WAIT / REST / GO_SWAP|GO_CHARGE / END_SHIFT

Cường đã chốt (spec §3b): dùng **pipeline deterministic** (solver, KHÔNG gọi LLM live). Nội dung
QUYẾT ĐỊNH nằm ở solver; composer chỉ diễn đạt lại thành câu — nên lấy thẳng từ solver là trung
thực với advisor thật.

## Hai cái bẫy đã tránh (ghi lại để đừng ai vô tình mở lại)

1. **KHÔNG dùng `next_action` làm hành động TỨC THỜI.** `shift_dp` định nghĩa `next_action` là
   *"action đầu tiên KHÁC ONLINE trong cả lịch"* — nó có thể nằm ở bucket cách hiện tại vài
   TIẾNG. Dùng nó ngay sẽ bắt tài xế nghỉ sớm 2-3 tiếng so kế hoạch. Hành động tức thời phải lấy
   từ **`schedule[0]`** (bucket hiện tại); `next_action` chỉ dùng để GIẢI THÍCH ("sắp tới nên…").

2. **KHÔNG để advisor nhìn tương lai.** `demand_forecast` dựng từ `World._actor_demand_hint()` —
   trường kỳ vọng từ CONFIG × nhiễu cá nhân theo archetype, đã được chứng minh không đọc realized
   trace từ M0-3. **Tuyệt đối không** dựng từ `world.orders` của phần còn lại trong ngày: làm vậy
   sẽ khiến SIM-4 báo Δ(B−A) dương GIẢ.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gsm_core.solvers import shift_dp

from .behavior import IdleAction
from .entities import Actor, FleetType

# Ánh xạ hành động solver → hành động actor. SWAP tách theo đội xe: tài xế sạc cắm ở nhà
# không "đổi pin" được.
_ACTION_MAP = {
    # BUG-SIM3-01: TRƯỚC ĐÂY `ONLINE -> WAIT`. SAI NGỮ NGHĨA và có hại đo được.
    #   `ONLINE` của solver nghĩa là *"khung này nên ở trạng thái làm việc"* — nó KHÔNG nói
    #   đứng yên hay dịch chuyển. Trong sim, `WAIT` = ĐỨNG IM chờ đơn, còn `RELOCATE` =
    #   sang ô đông khách hơn; **cả hai đều là đang-online**. Map ONLINE->WAIT biến lời
    #   khuyên "cứ chạy tiếp" thành mệnh lệnh "đứng im", ghi đè cả RELOCATE.
    #   Đo trên d-42 (P4, seed 1000): 14 -> 11 cuốc, payout 214.400 -> 155.376đ,
    #   idle 148 -> 215ph. Advice làm tài xế NGHÈO ĐI vì lỗi dịch, không phải vì advisor kém.
    # ⇒ ONLINE = KHÔNG can thiệp (None): advisor đồng ý "cứ làm việc", để bản năng chọn
    #   giữa WAIT/RELOCATE. Điều này cũng khớp ranh giới sản phẩm D-004 (advisor không
    #   chỉ định ô/reposition).
    "ONLINE": None,
    "REST": IdleAction.REST,
    "END": IdleAction.END_SHIFT,
}

# Mô hình tuân thủ — ASSUMPTION có lập luận, CHƯA có số thật:
#   tân binh (P4) thiếu kinh nghiệm ⇒ nghe theo nhiều nhất;
#   top/lão làng (P3/P5) đã có hệ thống riêng ⇒ nghe ít nhất;
#   phần còn lại ở giữa.
# Cần hiệu chỉnh khi có dữ liệu adherence thật (khảo sát tài xế / A-B thật). Ghi ở UPDATE-046.
DEFAULT_ADHERENCE = {
    "P1": 0.55, "P2": 0.50, "P3": 0.30, "P4": 0.75, "P5": 0.30, "P6": 0.50, "P7": 0.50,
}
DEFAULT_ADHERENCE_FALLBACK = 0.50


@dataclass(frozen=True)
class BridgedAdvice:
    """Một lần hỏi ý kiến advisor + kết cục."""
    t_min: float
    solver_action: str            # ONLINE | REST | SWAP | END (bucket HIỆN TẠI)
    mapped_action: IdleAction | None
    followed: bool
    adherence: str                # follow | ignore
    plan_next_action: str | None  # `next_action` của S2 — để GIẢI THÍCH, không thi hành ngay
    plan_next_bucket: str | None
    reason: str | None


class AdviceActionBridge:
    """Hỏi solver S2 xem NÊN làm gì lúc này, rồi quyết định actor có nghe hay không.

    RNG: dùng **dòng riêng** (`seed ^ 0xADV1CE`). Nếu dùng chung `world.rng` thì việc bật advice
    sẽ **dịch chuỗi ngẫu nhiên** của mọi actor ⇒ World A và World B khác nhau vì lý do KHÔNG
    liên quan tới advice, phá nền CRN (paired-seed) mà SIM-4 dựa vào.
    """

    def __init__(self, cfg, policy, seed: int):
        adv = cfg.get("advice", {}) or {}
        self.enabled = bool(adv.get("enabled", False))
        self.coverage = str(adv.get("coverage", "single"))
        self.single_actor_id = adv.get("single_actor_id")
        self.interval_min = float(adv.get("interval_min", 30))
        self.adherence = {**DEFAULT_ADHERENCE, **(adv.get("adherence_by_archetype") or {})}
        # Solver S2 ở gsm_core dùng lớp PolicyBundle KHÁC (có `bonus_at`). Chuyển đổi qua
        # `to_core_record()` — nguồn duy nhất, dùng chung với mockgen (chống lệch policy).
        from gsm_core.policy import PolicyBundle as CorePolicy
        self.sim_policy = policy
        self.policy = CorePolicy.from_record(policy.to_core_record())
        self.bucket_min = int(adv.get("bucket_min", 60))
        self.rng = np.random.default_rng(seed ^ 0xADD1CE)
        self._last_consult: dict[int, float] = {}
        self._share = float(adv.get("share", 0.0))
        self._covered_cache: dict[int, bool] = {}

    # ---------- ai được nhận advice ----------

    def covers(self, actor: Actor) -> bool:
        if not self.enabled:
            return False
        hit = self._covered_cache.get(actor.actor_id)
        if hit is not None:
            return hit
        if self.coverage == "all":
            hit = True
        elif self.coverage == "single":
            hit = (self.single_actor_id is not None
                   and int(self.single_actor_id) == actor.actor_id)
        elif self.coverage == "share":
            # deterministic theo actor_id, KHÔNG tiêu RNG dùng chung (giữ CRN)
            hit = float(np.random.default_rng(actor.actor_id ^ 0x5A4E).random()) < self._share
        else:                       # "none" hoặc giá trị lạ → không ai
            hit = False
        self._covered_cache[actor.actor_id] = hit
        return hit

    def due(self, actor: Actor, now_min: float) -> bool:
        """Chỉ hỏi khi tới hạn — hỏi mỗi tick vừa đắt vừa phi thực tế (tài xế không mở app
        30 giây một lần)."""
        last = self._last_consult.get(actor.actor_id)
        return last is None or (now_min - last) >= self.interval_min

    # ---------- dựng input cho solver (KHÔNG rò tương lai) ----------

    def build_shift_plan_input(self, actor: Actor, now_min: float, demand_hint_fn,
                               horizon_min: float) -> dict:
        """`shift_plan_input` theo schema L3, dựng từ trạng thái HIỆN TẠI của actor.

        `demand_hint_fn(actor, hour) -> {cell: expected_orders}` chính là belief cá nhân của
        actor (`World._actor_demand_hint`). Không nhận `world.orders`.
        """
        b = self.bucket_min
        starts = [s for s in range(int(now_min) - int(now_min) % b, int(horizon_min), b)
                  if s + b > now_min]
        forecast = []
        for s in starts:
            hour = (s // 60) % 24
            hint = demand_hint_fn(actor, hour) or {}
            for cell, exp in sorted(hint.items(), key=lambda kv: (-kv[1], kv[0]))[:3]:
                forecast.append({
                    "bucket": f"2026-07-01T{(s // 60) % 24:02d}:{s % 60:02d}:00+07:00",
                    "cell_cluster": cell,
                    "expected_orders": round(float(exp), 3),
                })
        return {
            "schema_version": "1.0.0", "driver_id": f"d-{actor.actor_id}",
            "t_now": f"2026-07-01T{int(now_min) // 60 % 24:02d}:{int(now_min) % 60:02d}:00+07:00",
            "buckets_remaining": len(starts),
            "soc_pct": round(actor.soc_pct, 1),   # sim CÓ telemetry pin (data thật thì không)
            "points_now": int(actor.points),
            "demand_forecast": forecast,
            "policy_bundle_version": self.policy.version,
            "view_version": "sim-3", "source": "MOCK",
        }

    # ---------- hỏi ý kiến ----------

    def consult(self, actor: Actor, now_min: float, demand_hint_fn,
                horizon_min: float) -> BridgedAdvice | None:
        """Trả `BridgedAdvice` nếu có lời khuyên áp dụng được, None nếu không."""
        if not self.covers(actor) or not self.due(actor, now_min):
            return None
        self._last_consult[actor.actor_id] = now_min

        spi = self.build_shift_plan_input(actor, now_min, demand_hint_fn, horizon_min)
        if spi["buckets_remaining"] <= 0:
            return None
        report = shift_dp.solve(spi, self.policy)
        sol = report.get("solution") or {}
        schedule = sol.get("schedule") or []
        if not schedule:
            return None

        # BẪY 1: hành động TỨC THỜI = bucket hiện tại, KHÔNG phải `next_action`
        solver_action = str(schedule[0].get("action") or "ONLINE").upper()
        na = sol.get("next_action") or {}

        mapped = _map_action(solver_action, actor)
        p = float(self.adherence.get(actor.archetype, DEFAULT_ADHERENCE_FALLBACK))
        followed = bool(self.rng.random() < p)
        return BridgedAdvice(
            t_min=now_min, solver_action=solver_action,
            mapped_action=mapped if followed else None,
            followed=followed, adherence="follow" if followed else "ignore",
            plan_next_action=na.get("action"), plan_next_bucket=na.get("bucket"),
            reason=na.get("reason"),
        )


def _map_action(solver_action: str, actor: Actor) -> IdleAction | None:
    if solver_action == "SWAP":
        return IdleAction.GO_SWAP if actor.fleet == FleetType.SWAP else IdleAction.GO_CHARGE
    return _ACTION_MAP.get(solver_action)
