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
from datetime import date, timedelta

import numpy as np

# Ngày gốc của sim. Mọi nhãn thời gian sinh ra ở đây phải mang **ngày thật**, không chỉ giờ.
_BASE_DATE = date(2026, 7, 1)
_MIN_PER_DAY = 1440


def _iso(minute: float) -> str:
    """Nhãn ISO từ *phút kể từ 00:00 ngày gốc*, mang NGÀY THẬT.

    BUG THỜI GIAN (b0-A, 2026-07-28 — Cường hỏi *"có lỗi time mismatch ở đâu không"*):
    bản cũ ghi `f"2026-07-01T{(s // 60) % 24:02d}:…"`. `% 24` giữ GIỜ nhưng **vứt mất NGÀY**, nên
    một bucket ở tương lai (sau 24:00) lại mang nhãn `01/07 00:00` — **sớm hơn `t_now`**.
    `shift_dp._forecast_arrays` gộp theo timestamp rồi `sorted(grouped)`, tức **sort chuỗi ISO
    theo từ điển** ⇒ bucket cuối-thực-tế nhảy về vị trí 0 và `hrs` gán sai giờ cho cả lịch.
    Hậu quả nặng nhất: `schedule[0]` — thứ bridge thi hành làm hành động TỨC THỜI — được tính
    cho một bucket khác.

    **Đo được**: tái lập bằng forecast có cầu ở giờ 0 (`00:00` ra vị trí 0). Nhưng chạy thật
    **0/1197 lần** vì `demand_field` chỉ phủ 05:00–24:00 ⇒ giờ 0 trả `{}` ⇒ không sinh dòng nào.
    ⇒ lỗi TIỀM ẨN, không phải lỗi đang xảy ra; số của UPDATE-047 **không** bị nhiễm (tôi từng
    nghi là có — sai, đã đính chính). Vẫn sửa vì chỉ cần ai thêm cầu ban đêm vào config là nó
    sống dậy im lặng.
    """
    m = int(minute)
    d = _BASE_DATE + timedelta(days=m // _MIN_PER_DAY)
    rem = m % _MIN_PER_DAY
    return f"{d.isoformat()}T{rem // 60:02d}:{rem % 60:02d}:00+07:00"

from gsm_core.solvers import bonus_feasibility, idle_reduction, shift_dp

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
class BonusGateAdvice:
    """SIM-4 — kênh `accept_lift`: cảnh báo tỷ lệ nhận dưới ngưỡng ĐỦ ĐIỀU KIỆN thưởng.

    Vì sao đây là kênh giá trị NHẤT (đo được, không phỏng đoán): `policy.day_bonus()` trả **0**
    khi `acceptance < bonus_min_acceptance` — *bất kể tài xế chạy bao nhiêu điểm*. Config pilot
    đặt ngưỡng **0.85**, trong khi P4 tân binh có `accept_base = 0.80` ⇒ tân binh **bị loại khỏi
    toàn bộ thưởng ngày**. SIM-2 đo đúng vậy: P4 và P1 nhận **0đ** thưởng, còn P2/P3/P5/P6/P7
    (accept ≥ 0.90) nhận 30-60k.

    Lời khuyên ở đây là **sự thật policy** ("tỷ lệ của anh dưới ngưỡng X nên đang mất thưởng"),
    tác động ở **mức TỶ LỆ** — KHÔNG phải "nhận cuốc cụ thể này" (ranh giới sản phẩm §5).
    """
    t_min: float
    acceptance_now: float
    threshold: float
    lift_applied: float
    followed: bool


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
        # Biên thời gian của CHÍNH thế giới này. Advisor không được lập kế hoạch — cũng không
        # được hoãn ca — vượt quá lúc thế giới dừng (b0-A).
        self.world_end_min = float(cfg.get("time.end_min", 1440) or 1440)
        # UPDATE-082 — GIẢ THUYẾT ĐÃ BỊ SỐ LIỆU BÁC BỎ, giữ cờ để tra cứu.
        #
        # Giả thuyết: `REST` của S2 nghĩa "đừng ONLINE kiếm tiền", mà `go_swap`/`relocate` vốn
        # đã không phải ONLINE ⇒ ghi đè chúng là thừa và phá hoại (đo: 92/166 = 55% số can
        # thiệp là loại này). Nghe rất thuyết phục.
        #
        # ĐO 15 seed: bật chốt chặn làm advisor **TỆ ĐI**, không tốt lên:
        #     tắt  (hiện tại): −14.125đ  CI [−35.019, +7.617]  lợi 4/15
        #     bật            : −32.383đ  CI [−50.001, −15.644] lợi 3/15
        #
        # Vì sao: `go_swap` tốn chuyến đi trạm + chờ (11% thất bại), `relocate` là chạy rỗng
        # (14% thời gian). Chính các lần ghi đè đó đang **CỨU** tài xế khỏi hành động đắt.
        # ⇒ Mặc định FALSE (giữ hành vi hiện tại). Giữ cờ để so A/B, không để mặc.
        self.rest_only_overrides_wait = bool(adv.get("rest_only_overrides_wait", False))
        # BUG-S2-PARAMS (UPDATE-078): quãng đường TB của CHÍNH thế giới này, không phải hằng
        # `avg_dist_km=3.0` trong `DEFAULT_PARAMS`. Cùng nguồn với world sinh cuốc.
        self.avg_dist_km = float(cfg.get("orders.trip_km_median", 3.5) or 3.5)
        # prior hoàn thành của quần thể = 1 − tỷ lệ huỷ-sau-nhận của chính thế giới này
        self.completion_prior = round(
            1.0 - float(cfg.get("orders.cancel_after_accept_rate", 0.05) or 0.05), 4)
        # T-045a b3 — kênh VỊ TRÍ (S4 capacity_alloc, batch tick). Ba mức, Cường chốt đo CẢ HAI
        # mức bật ở b4:
        #   "off"               → mặc định, KHÔNG chạy planner, trace y hệt không có cờ;
        #   "wait_only"         → chỉ ghi đè khi bản năng là WAIT (bảo thủ — bài học REST:
        #                          ghi đè hành động 'đắt' từng làm advisor tệ đi −14k → −32k);
        #   "wait_and_relocate" → đổi cả ĐÍCH của relocate bản năng.
        self.positioning_overrides = str(adv.get("positioning_overrides", "off") or "off")
        # Cờ dựng kịch bản ABSENT (data thật không có cung theo ô): solver phải chạy được ở cả
        # ba mức available/degraded/absent — thiếu cung ⇒ KHÔNG khuyên vị trí, không đoán.
        self.market_supply_available = bool(adv.get("market_supply_available", True))
        # SIM-4: mỗi kênh bật/tắt RIÊNG ⇒ đo được kênh nào tạo ra giá trị (attribution).
        ch = adv.get("channels") or {}
        self.ch_shift_plan = bool(ch.get("shift_plan", True))
        self.ch_accept_lift = bool(ch.get("accept_lift", False))
        self.ch_shift_extend = bool(ch.get("shift_extend", False))
        self.ch_rest_window = bool(ch.get("rest_window", False))
        self.rest_defer_max_min = float(adv.get("rest_defer_max_min", 120))
        self.lift_step = float(adv.get("accept_lift_step", 0.10))
        self.lift_max = float(adv.get("accept_lift_max", 0.15))
        self.min_offers_before_lift = int(adv.get("min_offers_before_lift", 5))
        self.extend_max_min = float(adv.get("shift_extend_max_min", 60))
        # D-SIM-05: tham số của điều kiện khả thi
        self.max_realized_accept = float(adv.get("max_realized_accept", 0.93))
        self.min_online_min_for_rate = float(adv.get("min_online_min_for_rate", 30))
        self.trips_per_hour_est = float(adv.get("trips_per_hour_est", 1.5))
        # ghi lại các lần TỪ CHỐI khuyên — để đo "đã tránh được bao nhiêu lời khuyên có hại"
        self.skipped_advice: list[tuple[float, int, str]] = []
        # D-SIM-13: lịch sử cuộn nhiều ngày (`{actor_id: DriverMemory}`), do `run_multiday`
        # gán SAU khi tạo World — chữ ký constructor không đổi nên đường 1-ngày không đụng.
        # Memory tại thời điểm gán chỉ chứa các ngày ĐÃ XONG ⇒ không rò tương lai.
        self.memory: dict | None = None
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
        # BUCKET MA (b0-A): thế giới dừng ở `time.end_min` (`world.py`: `while env.now < end_min`),
        # nhưng `check_shift_extend` có thể đẩy `shift_end_min` vượt qua đó. Lập lịch cho khoảng
        # thời gian thế giới KHÔNG tồn tại làm `buckets_remaining` phồng lên, mà `B` đi thẳng vào
        # `_required_rest(B, params)` ⇒ advisor ép nghỉ vì một khung giờ không có thật.
        # Đo seed 1000: **48 lần** `horizon > 1440`, mỗi lần thừa đúng 1 bucket.
        horizon = min(float(horizon_min), self.world_end_min)
        starts = [s for s in range(int(now_min) - int(now_min) % b, int(horizon), b)
                  if s + b > now_min]
        forecast = []
        for s in starts:
            hour = (s // 60) % 24          # belief cá nhân tra theo GIỜ trong ngày — đúng ngữ nghĩa
            hint = demand_hint_fn(actor, hour) or {}
            for cell, exp in sorted(hint.items(), key=lambda kv: (-kv[1], kv[0]))[:3]:
                forecast.append({
                    "bucket": _iso(s),      # nhãn mang NGÀY THẬT, không wrap `% 24`
                    "cell_cluster": cell,
                    "expected_orders": round(float(exp), 3),
                })
        return {
            "schema_version": "1.0.0", "driver_id": f"d-{actor.actor_id}",
            "t_now": _iso(now_min),
            "buckets_remaining": len(starts),
            "soc_pct": round(actor.soc_pct, 1),   # sim CÓ telemetry pin (data thật thì không)
            "points_now": int(actor.points),
            "demand_forecast": forecast,
            "policy_bundle_version": self.policy.version,
            "view_version": "sim-3", "source": "MOCK",
        }

    # ---------- BUG-S2-PARAMS: tham số THẬT cho solver ----------

    def _acc_estimate(self, actor: Actor) -> float:
        """Ước lượng tỷ lệ nhận **as-of** — quá khứ, không rò tương lai.

        Chưa đủ mẫu trong ngày thì dùng lịch sử cuộn nhiều ngày (D-SIM-13, số ĐO thật của chính
        tài xế), thiếu nữa thì `accept_base` (đại diện cho tỷ lệ lịch sử mà hệ thật đọc từ
        `driver_statistic_daily`). KHÔNG dùng property `actor.acceptance_rate` khi chưa có offer:
        nó trả 1.0 cho 0/0 (BUG-DSIM13-02) — "chưa biết" bị hiểu thành "hoàn hảo".
        """
        if actor.orders_offered < self.min_offers_before_lift:
            mem = (self.memory or {}).get(actor.actor_id)
            return float(mem.acceptance_avg if mem is not None and mem.acceptance_avg is not None
                         else actor.accept_base)
        return float(actor.acceptance_rate)

    def _comp_estimate(self, actor: Actor) -> float:
        """Như trên, cho tỷ lệ hoàn thành.

        Chưa nhận cuốc nào ⇒ property trả **1.0** (cùng bệnh 0/0 với acceptance). Thay bằng:
        lịch sử nhiều ngày của chính tài xế, thiếu thì **prior quần thể** = `1 − cancel_after_
        accept_rate` của chính thế giới này (0,05 ⇒ 0,95) — cùng loại thay thế mà code sẵn có
        đang dùng `accept_base` cho acceptance (*"thực tế đọc từ `driver_statistic_daily`"*).

        **Không** dùng `bonus_min_completion` làm fallback: nó bằng ĐÚNG ngưỡng, mà `_bonus_
        eligible` so `>=` ⇒ hoá ra **qua** gate — nghe như bảo thủ nhưng thực chất là dễ dãi.
        """
        if actor.orders_accepted <= 0:
            mem = (self.memory or {}).get(actor.actor_id)
            if mem is not None and mem.completion_avg is not None:
                return float(mem.completion_avg)
            return self.completion_prior
        return float(actor.completion_rate)

    def solver_params(self, actor: Actor) -> dict:
        """Tham số THẬT truyền cho `shift_dp`.

        BUG-S2-PARAMS (hồ sơ `10-bug-bucket-min-khong-truyen.md`): trước đây `consult` gọi
        `shift_dp.solve(spi, policy)` **không params**, nên solver dùng `DEFAULT_PARAMS`:

        - `bucket_min = 30` trong khi bridge dựng bucket **60′** ⇒ DP tin pin bền **gấp đôi**
          và nghỉ bắt buộc chỉ còn **một nửa** ⇒ nghiệm lệch hẳn về ONLINE (đo: 18/25 tài xế
          đổi lịch, `OOO` → `OOR`);
        - `p_accept = 0.9`, `avg_dist_km = 3.0` — chính docstring của `DEFAULT_PARAMS` ghi
          *"CALLER NÊN TRUYỀN số thật"* (AUDIT S2-4/S2-5);
        - thiếu `acceptance_rate`/`completion_rate` ⇒ `_bonus_eligible` trả "không có số để
          xét" ⇒ S2 **hứa thưởng cho cả người chính sách sẽ không trả**.
        """
        return {
            "bucket_min": self.bucket_min,
            "p_accept": self._acc_estimate(actor),
            "avg_dist_km": self.avg_dist_km,
            "acceptance_rate": self._acc_estimate(actor),
            "completion_rate": self._comp_estimate(actor),
        }

    # ---------- hỏi ý kiến ----------

    def consult(self, actor: Actor, now_min: float, demand_hint_fn,
                horizon_min: float) -> BridgedAdvice | None:
        """Trả `BridgedAdvice` nếu có lời khuyên áp dụng được, None nếu không."""
        if not (self.ch_shift_plan and self.covers(actor)) or not self.due(actor, now_min):
            return None
        self._last_consult[actor.actor_id] = now_min

        spi = self.build_shift_plan_input(actor, now_min, demand_hint_fn, horizon_min)
        if spi["buckets_remaining"] <= 0:
            return None
        report = shift_dp.solve(spi, self.policy, self.solver_params(actor))
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


    # ---------- T-045a b3: adherence cho kênh vị trí ----------

    def standby_follow_draw(self, actor: Actor) -> bool:
        """MỘT lần rút adherence cho MỘT lượt gán standby — rút tại thời điểm GÁN (planner),
        không rút lại mỗi vòng poll.

        Vì sao quan trọng: rút ở vòng poll nghĩa là re-roll mỗi 2 phút tới khi "follow" — đúng
        lỗi D-SIM-14 mà ĐA-04 chốt phải sửa (*"một adherence draw cho (decision_id,
        material_revision)"*). Dùng cùng dòng RNG `seed ^ 0xADD1CE` với mọi kênh advice ⇒ bật
        kênh không dịch chuỗi ngẫu nhiên của actor (giữ CRN)."""
        p = float(self.adherence.get(actor.archetype, DEFAULT_ADHERENCE_FALLBACK))
        return bool(self.rng.random() < p)

    # ---------- SIM-4 kênh 2: cảnh báo tỷ lệ nhận dưới ngưỡng thưởng ----------

    def check_bonus_gate(self, actor: Actor, now_min: float) -> BonusGateAdvice | None:
        """Nếu tỷ lệ nhận đang dưới ngưỡng đủ điều kiện thưởng → khuyên nâng tỷ lệ.

        Chỉ khuyên khi CÒN GỠ ĐƯỢC: đã có đủ mẫu (`min_offers_before_lift`) và chưa hết ca.
        Không khuyên khi đã đạt ngưỡng (không có gì để nói) hoặc đã lift kịch trần.
        """
        if not (self.ch_accept_lift and self.covers(actor)):
            return None
        if now_min >= actor.shift_end_min:
            return None                       # hết ca, khuyên cũng vô ích
        thr = float(self.policy.bonus_min_acceptance)

        # PHÁT HIỆN SIM-4 (đo, không đoán): tỷ lệ nhận là **luỹ kế CẢ NGÀY**, nên những lần
        # từ chối đầu ca KHÔNG gỡ lại được. Bản đầu chỉ khuyên sau `min_offers_before_lift`
        # offer (phản ứng) ⇒ d-42 chỉ bò từ 0.79 lên 0.8235, **vẫn dưới ngưỡng 0.85**, thưởng
        # vẫn 0đ. Lời khuyên đúng phải là **PHÒNG NGỪA, từ đầu ca**.
        #
        # Khi chưa đủ mẫu trong ngày, ước lượng bằng LỊCH SỬ: ưu tiên lịch sử cuộn nhiều ngày
        # (D-SIM-13 — số ĐO thật của chính tài xế), thiếu thì `accept_base` (tham số archetype;
        # thực tế đọc từ `driver_statistic_daily`). Cả hai đều là quá khứ, không rò tương lai.
        acc = self._acc_estimate(actor)   # UPDATE-078: một nguồn với `solver_params`

        # --- D-SIM-05: CHỈ khuyên khi lời khuyên THỰC SỰ có ích ---
        # SIM-4 chứng minh hiệu ứng VÁCH ĐÁ: nâng tỷ lệ mà KHÔNG chạm ngưỡng làm tài xế
        # nhận thêm cuốc rẻ, chiếm chỗ cuốc tốt ⇒ mất 34k mà chẳng có thưởng bù. Thưởng
        # theo ngưỡng là được-ăn-cả-ngã-về-không, nên khuyên nửa vời TỆ HƠN không khuyên.
        ok, why = self._advice_would_help(actor, now_min, thr, acc_est=acc)
        if not ok:
            self.skipped_advice.append((now_min, actor.actor_id, why))
            return None
        if acc >= thr or actor.accept_lift >= self.lift_max:
            return None
        p = float(self.adherence.get(actor.archetype, DEFAULT_ADHERENCE_FALLBACK))
        followed = bool(self.rng.random() < p)
        applied = 0.0
        if followed:
            applied = min(self.lift_step, self.lift_max - actor.accept_lift)
            actor.accept_lift += applied
        return BonusGateAdvice(t_min=now_min, acceptance_now=round(acc, 4), threshold=thr,
                               lift_applied=round(applied, 4), followed=followed)

    # ---------- D-SIM-03: kênh `rest_window` — dồn nghỉ/đổi pin vào khung vắng khách ----------

    def build_idle_reduction_input(self, actor: Actor, now_min: float, demand_hint_fn) -> dict:
        """`idle_reduction_input` (schema L3) dựng từ idle ĐÃ TÍCH LUỸ tới hiện tại.

        `demand_by_hour` là **chỉ số 0..1 chuẩn hoá theo đỉnh trong ngày**, lấy từ belief cá nhân
        của actor (`_actor_demand_hint`) — không đọc đơn tương lai (nguyên tắc SIM-3).
        S7 coi `demand_index ≤ 0.5` là khung "thấp điểm".
        """
        segs, total, longest = [], 0.0, 0.0
        for h, mins in sorted(actor.idle_by_hour.items()):
            segs.append({"hour": int(h), "duration_seconds": float(mins) * 60.0})
            total += float(mins)
            longest = max(longest, float(mins))

        raw = {h: sum((demand_hint_fn(actor, h) or {}).values()) for h in range(24)}
        peak = max(raw.values()) or 1.0
        demand_by_hour = {str(h): round(v / peak, 4) for h, v in raw.items()}

        return {
            "schema_version": "1.0.0", "driver_id": f"d-{actor.actor_id}",
            "t_now": _iso(now_min),
            "session_date": _iso(now_min)[:10],
            "idle_segments": segs,
            "total_idle_min": round(total, 2),
            "longest_idle_min": round(longest, 2),
            "online_hours": round(max(0.0, actor.online_min) / 60.0, 3),
            "demand_by_hour": demand_by_hour,
            "active_reposition": None,      # sim chưa mô hình mission reposition của GSM (D-004b)
            "view_version": "sim-3", "source": "MOCK",
        }

    def rest_window_hour(self, actor: Actor, now_min: float, demand_hint_fn) -> int | None:
        """Khung giờ solver S7 khuyên dồn nghỉ/đổi pin vào. None = không có khuyến nghị.

        Gọi **solver thật** (`idle_reduction.solve`) chứ không tự cài lại lý lẽ — tránh lặp lỗi
        "hai nguồn sự thật" (xem `D-SIM-09`: `check_bonus_gate` đang mắc đúng lỗi đó).
        """
        if not (self.ch_rest_window and self.covers(actor)):
            return None
        # D-SIM-10: ưu tiên khung đã LÊN KẾ HOẠCH TỪ HÔM QUA. Đây là cách duy nhất lời khuyên
        # HỒI CỨU của S7 có tác dụng: trong ngày, khung nó chỉ ra luôn nằm phía sau (đo được ở
        # UPDATE-050, kênh inert hoàn toàn). Biết trước từ hôm qua thì khung còn ở phía TRƯỚC.
        if actor.planned_rest_hour is not None:
            return int(actor.planned_rest_hour)
        ii = self.build_idle_reduction_input(actor, now_min, demand_hint_fn)
        rep = idle_reduction.solve(ii)
        sol = rep.get("solution") or {}
        if not sol.get("notable"):
            return None                      # S7 KHÔNG bịa vấn đề khi tài xế không chờ nhiều
        w = sol.get("worst_window")
        return int(w["hour"]) if w else None

    def should_defer_rest(self, actor: Actor, now_min: float, hour: int,
                          demand_hint_fn, soc_threshold: float) -> tuple[bool, str]:
        """Có nên HOÃN nghỉ/đổi pin để dồn vào khung vắng khách không?

        BA LAN CAN — thiếu bất kỳ cái nào là biến lời khuyên thành có hại:
          1. **SOC thấp** ⇒ KHÔNG hoãn. Hoãn đổi pin làm tài xế hết pin giữa đường
             (`battery_stranded`) — hỏng nặng hơn mọi lợi ích idle.
          2. **Mệt thật** (`online_min > fatigue_threshold_min`) ⇒ KHÔNG hoãn. Sức khoẻ tài xế
             không phải biến để tối ưu.
          3. **Trần hoãn** `rest_defer_max_min` ⇒ không đẩy nghỉ đi vô hạn.
        """
        if actor.soc_pct <= soc_threshold:
            return False, "soc_low"
        if actor.online_min > actor.fatigue_threshold_min:
            return False, "fatigued"
        if actor.rest_deferred_min >= self.rest_defer_max_min:
            return False, "defer_cap"
        target = self.rest_window_hour(actor, now_min, demand_hint_fn)
        if target is None or target == hour:
            return False, "no_window" if target is None else "at_window"
        # chỉ hoãn nếu khung đó còn Ở PHÍA TRƯỚC trong ca
        minutes_to = ((target - hour) % 24) * 60
        if minutes_to <= 0 or now_min + minutes_to > actor.shift_end_min:
            return False, "window_past"
        if actor.rest_deferred_min + minutes_to > self.rest_defer_max_min:
            return False, "defer_cap"
        return True, f"defer_to_{target:02d}h"

    # ---------- D-SIM-05: điều kiện KHẢ THI của lời khuyên nâng tỷ lệ ----------

    def _acceptance_recoverable(self, actor: Actor, now_min: float, thr: float) -> bool:
        """Tỷ lệ nhận (LUỸ KẾ cả ngày) còn gỡ lại kịp trước khi hết ca không?

        Với `o` offer đã được chào, `a` đã nhận, `R` offer kỳ vọng còn lại, và `p` là tỷ lệ
        nhận cao nhất **đạt được thực tế** khi lift kịch trần (đo được ≈0.93 — không bịa):

            final = (a + p·R) / (o + R)   ⇒ khả thi khi final ≥ ngưỡng

        `R` ước lượng từ tốc độ nhận offer của CHÍNH tài xế này trong ca, nhân thời gian
        còn lại. Chỉ dùng dữ liệu **tới hiện tại** ⇒ không rò thông tin tương lai.

        `o = 0` (đầu ca): chưa từ chối gì nên chưa mất gì ⇒ luôn khả thi. Đúng bản chất —
        lời khuyên PHÒNG NGỪA đầu ca là loại tốt nhất (PHÁT HIỆN SIM-4-B).
        """
        o, a = actor.orders_offered, actor.orders_accepted
        if o == 0:
            return True
        remaining_min = max(0.0, actor.shift_end_min - now_min)
        elapsed = max(1.0, actor.online_min)
        R = (o / elapsed) * remaining_min          # offer kỳ vọng còn lại
        p = self.max_realized_accept
        if o + R <= 0:
            return False
        return (a + p * R) / (o + R) >= thr

    def build_bonus_gap_input(self, actor: Actor, now_min: float) -> dict:
        """`bonus_gap_input` (schema L3) từ trạng thái HIỆN TẠI của actor.

        `historical_points_per_hour` ước từ **chính tài xế trong ca**; chưa đủ lịch sử thì để
        rỗng để S1 dùng fallback lý thuyết của nó (`points_per_trip_estimate`) — không tự chế
        ước lượng song song.
        """
        tiers = [[int(p), int(v)] for p, v in self.policy.day_bonus_tiers
                 if int(p) > int(actor.points)]
        # D-SIM-13: ưu tiên LỊCH SỬ CUỘN nhiều ngày (giá trị chính của multi-day) — đó là
        # đúng thứ S1 được thiết kế để nhận. Chưa có (ngày đầu / chế độ 1 ngày) mới rơi về
        # ước lượng trong-ngày như cũ.
        hist = {}
        mem = (self.memory or {}).get(actor.actor_id)
        # REVIEW-C9: so `is not None`, KHÔNG so truthiness — lịch sử 0.0 điểm/giờ là dữ
        # liệu HỢP LỆ (tài xế lịch sử không kiếm được điểm ⇒ S1 phải thấy đúng điều đó
        # và kết luận infeasible), không phải "thiếu lịch sử".
        if mem is not None and mem.points_per_hour_avg is not None:
            # lịch sử ngày TRỌN (trộn cả peak/offpeak) → điền cả 2 bucket
            hist = {"peak": mem.points_per_hour_avg, "offpeak": mem.points_per_hour_avg}
        elif actor.online_min >= self.min_online_min_for_rate and actor.points > 0:
            rate = actor.points / (actor.online_min / 60.0)
            hour = int(now_min // 60) % 24
            hist = {("peak" if self.policy.is_peak(hour) else "offpeak"): round(rate, 3)}
        return {
            "schema_version": "1.0.0", "driver_id": f"d-{actor.actor_id}",
            "t_now": _iso(now_min),
            "points_now": int(actor.points),
            "next_tiers": tiers,
            "historical_points_per_hour": hist,
            "hours_budget_remaining": round(max(0.0, actor.shift_end_min - now_min) / 60.0, 3),
            "acceptance_rate": round(actor.acceptance_rate, 4),
            "completion_rate": round(actor.completion_rate, 4),
            "policy_bundle_version": self.policy.version,
            "view_version": "sim-3", "source": "MOCK",
        }

    def _advice_would_help(self, actor: Actor, now_min: float, thr: float,
                           acc_est: float | None = None) -> tuple[bool, str]:
        """Lời khuyên nâng tỷ lệ nhận có ích không?

        **D-SIM-09 — ranh giới rõ ràng giữa solver và sim** (trước đây bridge tự chép lý lẽ
        advisor, đúng lỗi "hai nguồn sự thật" mà SIM-1/SIM-3 phải đi sửa):

        - **SOLVER S1 `bonus_feasibility` quyết định**: còn mốc để với không · quỹ giờ có đủ
          không · ràng buộc `acceptance` **và `completion`** có đạt không. Bridge KHÔNG được
          tính lại mấy thứ này.
        - **SIM bổ sung DUY NHẤT một thứ S1 không trả lời được**: tỷ lệ nhận là **luỹ kế cả
          ngày** — *"tới giờ này còn gỡ kịp không?"* (`_acceptance_recoverable`). S1 chỉ kiểm
          TĨNH (`acceptance >= ngưỡng`) nên không thay thế được phần này.
        """
        rep = bonus_feasibility.solve(self.build_bonus_gap_input(actor, now_min), self.policy)
        sol = rep.get("solution") or {}
        # C2 (UPDATE-076): chỉ im lặng khi kịch mốc **VÀ** thưởng thật sự an toàn. Kịch mốc mà
        # tỷ lệ dưới ngưỡng ⇒ chính sách trả 0đ; im lặng lúc đó là bỏ rơi tài xế đúng lúc còn
        # gỡ được. Rơi xuống dưới để `_acceptance_recoverable` quyết định có kịp không.
        if sol.get("already_maxed") and sol.get("feasible"):
            return False, "already_maxed"        # kịch mốc VÀ an toàn ⇒ khuyên thêm là thừa

        reason = (rep.get("infeasible_reason") or "")
        if not sol.get("feasible"):
            # S1 nói KHÔNG khả thi. Kênh này CHỈ sửa được tỷ lệ NHẬN, nên chỉ đáng khuyên khi
            # nghẽn **DUY NHẤT** ở đó. Nếu còn nghẽn ở quỹ GIỜ hoặc ở tỷ lệ HOÀN THÀNH thì
            # nâng tỷ lệ nhận là **sai địa chỉ** — tài xế ôm thêm cuốc rẻ mà vẫn không có
            # thưởng. (Bản trước bỏ sót hoàn toàn ràng buộc completion.)
            blocked_elsewhere = ("quỹ" in reason) or ("hoàn thành" in reason)
            if blocked_elsewhere or "tỷ lệ nhận" not in reason:
                return False, "blocked_elsewhere"
        # BUG-DSIM13-02 (lộ ra khi viết test cho REVIEW-C19): trước đây so
        # `actor.acceptance_rate >= thr` — property này TRẢ 1.0 khi CHƯA có offer nào
        # (0/0) ⇒ đầu ca luôn bị chặn nhầm là "đã đạt ngưỡng", giết đúng lời khuyên
        # PHÒNG NGỪA đầu ca (loại giá trị nhất — PHÁT HIỆN SIM-4-B). Phải dùng CÙNG ước
        # lượng mà check_bonus_gate đã chọn (lịch sử/base), không dùng số thoái hoá.
        elif (acc_est if acc_est is not None
              else actor.acceptance_rate) >= float(self.policy.bonus_min_acceptance):
            return False, "already_qualified"

        if not self._acceptance_recoverable(actor, now_min, thr):
            return False, "acceptance_unrecoverable"
        return True, ""

    # ---------- SIM-4 kênh 3: hoãn kết ca khi sát mốc điểm ----------

    def check_shift_extend(self, actor: Actor, now_min: float) -> float:
        """Trả số phút hoãn kết ca (0 = không hoãn).

        Chỉ hoãn khi **sát mốc điểm kế tiếp** — nếu không thì hoãn chỉ làm tài xế mệt thêm mà
        không thêm thưởng. Có TRẦN tổng thời gian hoãn để không biến thành "chạy vô hạn".
        """
        if not (self.ch_shift_extend and self.covers(actor)):
            return 0.0
        if actor.shift_extended_min >= self.extend_max_min:
            return 0.0
        gap = self.policy.next_tier_gap(int(actor.points))
        if not gap:
            return 0.0                        # đã ở mốc cao nhất → không có gì để với
        gap_points = int(gap[0])
        # ước lượng điểm/giờ từ CHÍNH tài xế này (không nhìn tương lai)
        online_h = max(0.5, actor.online_min / 60.0)
        rate = actor.points / online_h
        if rate <= 0:
            return 0.0
        need_min = gap_points / rate * 60.0
        if need_min > self.extend_max_min - actor.shift_extended_min:
            return 0.0                        # không với tới trong trần cho phép
        p = float(self.adherence.get(actor.archetype, DEFAULT_ADHERENCE_FALLBACK))
        if not (self.rng.random() < p):
            return 0.0
        add = min(need_min * 1.15, self.extend_max_min - actor.shift_extended_min)
        # b0-A: KHÔNG hoãn quá lúc thế giới dừng. Kéo ca tới 25:00 khi `time.end_min = 24:00` là
        # lời khuyên **không thể thực hiện được**: không sinh thêm cuốc nào, nhưng vẫn tiêu ngân
        # sách `shift_extended_min` và vẫn ghi event `advice_shift_extend` ⇒ A/B đọc thành "có
        # can thiệp" trong khi thực tế không có gì xảy ra. Đo seed 1000: 9/49 lần hoãn rơi vào ca
        # này. Cắt ở đây, không cắt ở chỗ tiêu thụ — nếu không thì mỗi consumer phải tự nhớ.
        add = min(add, max(0.0, self.world_end_min - actor.shift_end_min))
        if add <= 0.0:
            return 0.0
        actor.shift_extended_min += add
        actor.shift_end_min += add
        return add


def _map_action(solver_action: str, actor: Actor) -> IdleAction | None:
    if solver_action == "SWAP":
        return IdleAction.GO_SWAP if actor.fleet == FleetType.SWAP else IdleAction.GO_CHARGE
    return _ACTION_MAP.get(solver_action)
