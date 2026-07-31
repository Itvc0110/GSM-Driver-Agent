"""SIM-4 — THẾ GIỚI SONG SONG: đo advice giúp được bao nhiêu, có khoảng tin cậy.

Cường (`DIRECTIVES-2026-07-24.md` §5.6): *"các thế giới song song: khi **tự làm** vs khi **làm
theo chỉ dẫn**"*, đo trên **đúng tài xế đó**.

## Vì sao dùng HIỆU THEO CẶP (paired), không so hai nhóm độc lập

World A và World B chạy **cùng seed** ⇒ **cùng danh sách đơn, cùng thời tiết, cùng tắc đường**
(CRN — common random numbers). Chênh lệch còn lại vì thế phần lớn là **do advice**, không phải
do hôm nay nhiều khách hơn. So độc lập sẽ bị phương sai ngày-tốt/ngày-xấu nhấn chìm hiệu ứng.

Vì vậy thống kê phải làm trên **d_i = B_i − A_i từng seed**, rồi lấy trung bình + CI bootstrap.

## Nguyên tắc báo cáo

**CI chứa 0 là một KẾT QUẢ, không phải thất bại.** Không vặn tham số cho Δ đẹp lên — SIM-1 đã
ghi rõ bài học đó (spec §7.1). Nếu advice không giúp, phải nói là không giúp, rồi đi tìm vì sao.
"""

from __future__ import annotations

import copy
import statistics as st
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .journey import build_journey
from .metrics import summarize
from .runner import run_once

# Bộ kênh dựng sẵn cho đo THANG BẬC — biết giá trị đến từ kênh nào (attribution).
#
# 2026-07-28 (Cường duyệt UPDATE-087): mặc định sản phẩm đổi thành positioning wait_only +
# shift_plan OFF. Ladder vì thế phải SỞ HỮU cả khoá `positioning_overrides` (pseudo-channel,
# `_cfg_with` tách ra) — nếu không, "none" sẽ âm thầm thừa kế positioning từ config mặc định
# và bậc thang mất nghĩa: "none" phải là THẬT SỰ không can thiệp, bất biến với product default.
CHANNEL_LADDER = {
    "s2_only": {"shift_plan": True, "accept_lift": False, "shift_extend": False,
                "positioning_overrides": "off"},
    "rest_window": {"shift_plan": True, "accept_lift": False, "shift_extend": False,
                    "rest_window": True, "positioning_overrides": "off"},
    "accept_lift": {"shift_plan": True, "accept_lift": True, "shift_extend": False,
                    "positioning_overrides": "off"},
    "positioning": {"shift_plan": False, "accept_lift": False, "shift_extend": False,
                    "rest_window": False, "positioning_overrides": "wait_only"},   # = B3w
    "all": {"shift_plan": True, "accept_lift": True, "shift_extend": True, "rest_window": True,
            "positioning_overrides": "wait_only"},
    "none": {"shift_plan": False, "accept_lift": False, "shift_extend": False,
             "rest_window": False, "positioning_overrides": "off"},
}


@dataclass
class PairResult:
    seed: int
    actor_id: int
    a: dict          # metric của tài xế đích ở World A
    b: dict          # ... ở World B
    system_a: dict   # metric hệ thống (guardrail)
    system_b: dict
    # D-M3-10: adherence PHẢI nằm trong mọi PairResult. Luật "mọi arm báo kèm
    # decision_adherence, lệch danh nghĩa > 0,02 ⇒ TREO" từng chỉ tồn tại trên giấy —
    # đo được 2026-07-30: đường ống A/B tham chiếu `adherence` ĐÚNG 0 LẦN, và artifact
    # 35–39 không có khoá nào. Đó là lý do `shift_extend` báo 1,000 (sự thật 0,473) suốt
    # 39 artifact mà không cổng nào bắn. `adherence_b` là arm CÓ advice; `adherence_a` giữ
    # cho arm đối chứng (bài học DET-01: arm đối chứng cũng phải được đo, không giả định sạch).
    adherence_a: dict = field(default_factory=dict)
    adherence_b: dict = field(default_factory=dict)


def _cfg_with(cfg: Config, *, enabled: bool, actor_id: int | None,
              channels: dict | None, coverage: str = "single") -> Config:
    """Bản SAO SÂU của config với cờ advice đã đặt.

    Phải deep-copy: nếu sửa tại chỗ thì nhánh A và B dùng chung một dict ⇒ chạy A xong đã bị
    nhánh B ghi đè, mọi so sánh thành vô nghĩa.
    """
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    adv = c.data.setdefault("advice", {})
    adv["enabled"] = enabled
    # ĐA-08 (UPDATE-075): coverage KHÔNG còn bị ép "single". Guardrail hệ thống đo ở chế độ
    # single là vô nghĩa — tác động của MỘT tài xế lên thị trường gần bằng 0 theo thiết kế
    # (hồ sơ 07 §5.2). `coverage="all"` là chế độ phải dùng khi đánh giá tác hại hệ thống.
    adv["coverage"] = coverage
    adv["single_actor_id"] = actor_id if coverage == "single" else None
    if channels is not None:
        ch = dict(channels)
        # pseudo-channel (xem comment CHANNEL_LADDER): tách ra khỏi dict kênh thật
        pos = ch.pop("positioning_overrides", None)
        adv["channels"] = ch
        if pos is not None:
            adv["positioning_overrides"] = pos
    return c


def pick_target(result, archetype: str = "P4") -> int:
    """Tài xế đích = người thuộc `archetype` được chào đơn nhiều nhất Ở THẾ GIỚI A.

    ## ⛔ BIASED-DIAGNOSTIC — BUG-EVAL-ARGMAX (UPDATE-085 §4, Q-11 chốt 2026-07-28)

    Đây là phép CHỌN CỰC TRỊ: max-offers của A là người "may nhất" thế giới A, nên mọi nhiễu
    loạn (bật bất kỳ kênh advice nào) kéo họ về trung bình ⇒ Δ(B−A) trên người này **âm bất kể
    nội dung can thiệp**. Chứng minh sign-flip 5 seed, cùng can thiệp: argmax-A −19.654đ ·
    argmax-B +27.416đ · mean-P4 không chọn lọc +3.610đ. Chuỗi kết luận "advisor làm tài xế
    nghèo đi −17k…−40k" (UPDATE-075/078/081/084) nhiễm bias này.

    ⇒ CHỈ dùng để soi hành trình MỘT cá thể (Gantt, drill-down). **CẤM dùng làm tiêu chí 1 của
    ĐA-08** — tiêu chí đó đọc `payout_mean_P4`/`payout_mean_all` từ `_cohort_metrics` (không
    chọn lọc). Test `test_argmax_view_carries_bias_warning` canh nhãn này.

    P4 (tân binh) là baseline Cường yêu cầu; chưa phải hồ sơ tân binh THẬT (`D-SIM-02` treo).
    """
    cands = [a for a in result.actors if a.archetype == archetype] or list(result.actors)
    return max(cands, key=lambda a: a.orders_offered).actor_id


def _cohort_metrics(result) -> dict:
    """Tiêu chí CÁ NHÂN không bias (Q-11): mean trên MỌI tài xế, tách theo archetype.

    Không chọn lọc theo bất kỳ thống kê nào của A hay B ⇒ không có regression-to-the-mean.
    Sống trong dict `system` để `PairResult`/`compare()` giữ nguyên hình dạng.

    B1 (PLAN-cycle-wx): thêm `net_mean_all`/`net_mean_{arch}` = mean(payout − cost) và
    `cost_mean_all` = mean(cost) — CHỈ THÊM khoá, không sửa `payout_mean_*` đã có. Mặc định
    `cost_vnd` = 0 (T-045b) ⇒ `net_mean_all == payout_mean_all` cho tới khi B3/B4 bật chi phí."""
    by_arch_pay: dict[str, list[float]] = {}
    by_arch_net: dict[str, list[float]] = {}
    pays, trips, nets, costs = [], [], [], []
    for a in result.actors:
        net = float(a.payout_vnd) - float(a.cost_vnd)
        by_arch_pay.setdefault(a.archetype, []).append(float(a.payout_vnd))
        by_arch_net.setdefault(a.archetype, []).append(net)
        pays.append(float(a.payout_vnd))
        trips.append(float(a.trips_done))
        nets.append(net)
        costs.append(float(a.cost_vnd))
    out = {"payout_mean_all": round(st.mean(pays), 2) if pays else 0.0,
           "trips_mean_all": round(st.mean(trips), 3) if trips else 0.0,
           "net_mean_all": round(st.mean(nets), 2) if nets else 0.0,
           "cost_mean_all": round(st.mean(costs), 2) if costs else 0.0}
    for arch in sorted(by_arch_pay):
        out[f"payout_mean_{arch}"] = round(st.mean(by_arch_pay[arch]), 2)
        out[f"net_mean_{arch}"] = round(st.mean(by_arch_net[arch]), 2)
    return out


def _driver_metrics(result, actor_id: int) -> dict:
    m = build_journey(result, actor_id).metrics
    return {k: m[k] for k in (
        "payout_vnd", "trip_payout_vnd", "day_bonus_vnd", "trips_completed",
        "acceptance_rate", "completion_rate", "utilization", "idle_min", "online_min",
        "offers", "declined", "points",
    )}


def _system_metrics(result, exclude_actor: int) -> dict:
    """Guardrail: advice KHÔNG được cải thiện 1 người bằng cách làm xấu hệ thống.

    ĐA-08 (UPDATE-075): mở rộng từ 5 trường lên đủ **4 tầng** của chỉ tiêu kép —
    hệ thống · khách hàng · công bằng · tập trung. Bản 5 trường cũ không có Gini, không có
    TỔNG payout (⇒ không phân biệt được positive-sum với tái phân phối), không có đơn hết hạn
    và không có chỉ số dồn cục — tức không thể phát biểu chỉ tiêu kép.

    Số nền đo bằng chính bộ này: `research/audit/2026-07-27-current-state/09-*` (30 seed,
    `coverage: all`). Lưu ý khi đọc: ở n=30 **mọi tầng hệ thống đều có CI chứa 0**; chỗ có ý
    nghĩa thống kê là tầng CÁ NHÂN (payout −17.310đ). Đừng trích số 10-seed của hồ sơ 07.
    """
    from .sim_metrics import system_guardrail
    s = summarize(result)
    others = [a for a in result.actors if a.actor_id != exclude_actor]
    swap_waits = [e.detail.get("wait_min", 0.0) for e in result.events
                  if e.kind == "swap_done" and "wait_min" in e.detail]
    g = system_guardrail(result)
    return {
        # Q-11: cohort estimator KHÔNG BIAS — nguồn của tiêu chí 1 ĐA-08 (thay argmax)
        **_cohort_metrics(result),
        "served_rate": s["served_rate"],
        "orders_completed": s["orders_completed"],
        "others_payout_vnd": sum(a.payout_vnd for a in others),
        "others_trips": sum(a.trips_done for a in others),
        "swap_wait_mean": round(st.mean(swap_waits), 3) if swap_waits else 0.0,
        # --- 4 tầng ĐA-08 ---
        "total_payout_vnd": g["total_payout_vnd"],      # positive-sum hay tái phân phối?
        "expired_n": g["expired_n"],                     # khách bị bỏ
        "wait_median_min": g["wait_median_min"],         # khách chờ
        "gini_payout": g["gini_payout"],                 # công bằng
        "station_hhi": g["station_hhi"],                 # dồn trạm
        "supply_cell_hhi": g["supply_cell_hhi"],         # dồn khu
        "starved_hours_n": g["starved_hours_n"],         # giờ đói cung
    }


def run_pair(cfg: Config, seed: int, channels: dict | None = None,
             actor_id: int | None = None, archetype: str = "P4",
             coverage: str = "single") -> PairResult:
    """Chạy World A (tự làm) và World B (theo chỉ dẫn) trên **cùng seed**.

    `coverage="all"` = advice cho TOÀN ĐỘI — chế độ BẮT BUỘC khi đánh giá tác động hệ thống
    (ĐA-08). `"single"` giữ nguyên cho nghiên cứu attribution trên một tài xế.
    """
    ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
    aid = actor_id if actor_id is not None else pick_target(ra, archetype)
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=aid, channels=channels,
                            coverage=coverage), seed)
    from .sim_metrics import adherence_audit
    return PairResult(seed=seed, actor_id=aid,
                      adherence_a=adherence_audit(ra), adherence_b=adherence_audit(rb),
                      a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                      system_a=_system_metrics(ra, aid), system_b=_system_metrics(rb, aid))


def assert_crn(cfg: Config, seed: int, actor_id: int) -> bool:
    """CRN phải đúng: cùng seed ⇒ **cùng danh sách đơn** ở hai nhánh.

    Nếu ngoại sinh lệch thì mọi Δ là rác — kiểm trước khi tin bất kỳ con số nào.
    """
    ra = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
    rb = run_once(_cfg_with(cfg, enabled=True, actor_id=actor_id,
                            channels=CHANNEL_LADDER["all"]), seed)
    ka = [(o.order_id, round(o.t_min, 6), o.pickup_cell, o.gross_vnd) for o in ra.orders]
    kb = [(o.order_id, round(o.t_min, 6), o.pickup_cell, o.gross_vnd) for o in rb.orders]
    return ka == kb


def bootstrap_ci(diffs: list[float], n_boot: int = 5000, alpha: float = 0.05,
                 seed: int = 12345) -> tuple[float, float]:
    """CI phần trăm bootstrap cho TRUNG BÌNH hiệu theo cặp.

    Bootstrap thay vì t-test vì phân phối Δ (payout/ngày) lệch và có đuôi — không nên giả
    định chuẩn khi mẫu chỉ vài chục seed.
    """
    if not diffs:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    arr = np.asarray(diffs, dtype=float)
    means = arr[rng.integers(0, len(arr), size=(n_boot, len(arr)))].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


# AUDIT STATS-5 (UPDATE-069): bootstrap CI degenerate với n nhỏ (n=1 → CI rộng 0, MỌI Δ≠0
# thành "significant"; n=2 → đồng xu 50%). Chuẩn CLAUDE §4b: kết luận distribution cần ≥30 seed.
MIN_SEEDS_FOR_SIGNIFICANCE = 30

# UPDATE-078: ngưỡng 30 ở trên hiệu chỉnh cho **A/B advice** (có advice vs không). So **hai BIẾN
# THỂ advice** với nhau là bài toán KHÁC và cần nhiều seed hơn hẳn: đo thật cho fix
# BUG-S2-PARAMS ra hiệu số −7.650đ với SD ~40.000đ theo seed (spread −90k..+96k) ⇒
# n ≈ (1,96·40.000/7.650)² ≈ 105.
#
# Ghi ra để không ai lặp lại lỗi tôi vừa mắc: chạy 30 seed hai lần với hai bản code rồi kết luận
# "bản mới tệ hơn". Muốn so biến thể thì phải GHÉP CẶP (cùng World A theo seed, hai nhánh B) và
# bootstrap **hiệu của hiệu** — xem `research/audit/2026-07-27-current-state/11-*` §4.
MIN_SEEDS_FOR_VARIANT_COMPARISON = 100


# (e) 2026-07-31: tầng 5 sức khoẻ (D-M3-05) là cổng MỘT CHIỀU — nó chỉ tố giác SUY GIẢM,
# cố ý KHÔNG có chiều khen (chống Goodhart: tối ưu cho `veto_fired_n` CAO = ép tài xế chạm
# mệt/cạn pin nhiều hơn để "qua cổng"). Đưa các khoá này vào bảng significance HAI CHIỀU của
# `compare()['system']` làm "veto tăng" bị in ra như *"ĐỘNG TỚI HỆ THỐNG"* — tức đọc thành
# advice làm hệ thống TỐT lên, đúng hướng Goodhart mà tầng 5 sinh ra để chặn. Chúng đi qua
# `health_guardrail_flags`, không qua `_sig`.
HEALTH_KEYS_ONE_WAY = frozenset({
    "rest_min_total", "veto_calls_n", "veto_fired_n",
    "veto_soc_low_n", "veto_fatigued_n", "veto_defer_cap_n",
    "work_span_p50", "work_span_p90", "work_span_max",
    "drive_min_p50", "drive_min_p90", "drive_min_max",
})


def _sig(lo: float, hi: float, n: int, min_seeds: int = MIN_SEEDS_FOR_SIGNIFICANCE) -> bool:
    """CI không chứa 0 VÀ đủ seed. `min_seeds` mặc định 30 (chuẩn A/B: có-advice vs không).

    (d) 2026-07-31 — vòng soi D-M3-04: so **HAI BIẾN THỂ advice** với nhau là bài toán KHÁC và
    cần `MIN_SEEDS_FOR_VARIANT_COMPARISON = 100` (xem comment của hằng đó: đo thật cho SD ~40k
    theo seed ⇒ n ≈ 105). Trước đây `_sig` kẹp cứng 30 nên mọi contrast biến-thể-vs-biến-thể
    đi qua `compare()` được gắn `significant` ở n=30 — dưới chuẩn. Caller nay truyền
    `min_seeds=MIN_SEEDS_FOR_VARIANT_COMPARISON` khi contrast là biến-thể.
    """
    return bool(n >= min_seeds and (lo > 0 or hi < 0))


def compare(pairs: list[PairResult], min_seeds: int | None = None) -> dict:
    """Tổng hợp: hiệu theo cặp cho từng metric + CI bootstrap + guardrail hệ thống.

    `significant` chỉ được bật khi n ≥ MIN_SEEDS_FOR_SIGNIFICANCE — dưới đó flag luôn
    False và `n_insufficient`=True để consumer không đọc nhầm nhiễu thành hiệu ứng."""
    n = len(pairs)
    out: dict = {"n_seeds": n, "n_insufficient": n < MIN_SEEDS_FOR_SIGNIFICANCE,
                 "driver": {}, "system": {},
           "min_seeds_for_sig": (min_seeds if min_seeds is not None
                                 else MIN_SEEDS_FOR_SIGNIFICANCE)}
    ms = out["min_seeds_for_sig"]
    if not pairs:
        return out
    for key in pairs[0].a:
        diffs = [float(p.b[key] or 0) - float(p.a[key] or 0) for p in pairs]
        lo, hi = bootstrap_ci(diffs)
        out["driver"][key] = {
            "mean_a": round(st.mean(float(p.a[key] or 0) for p in pairs), 2),
            "mean_b": round(st.mean(float(p.b[key] or 0) for p in pairs), 2),
            "delta_mean": round(st.mean(diffs), 2),
            "ci95": (round(lo, 2), round(hi, 2)),
            "significant": _sig(lo, hi, n, ms),
            "n_positive": sum(1 for d in diffs if d > 0),
        }
    for key in pairs[0].system_a:
        diffs = [float(p.system_b[key] or 0) - float(p.system_a[key] or 0) for p in pairs]
        lo, hi = bootstrap_ci(diffs)
        row = {"delta_mean": round(st.mean(diffs), 4), "ci95": (round(lo, 4), round(hi, 4))}
        if key in HEALTH_KEYS_ONE_WAY:
            # (e) tầng 5 KHÔNG có `significant` hai chiều — cổng của nó là
            # `sim_metrics.health_guardrail_flags` (một chiều, chỉ tố giác suy giảm).
            # Để `significant` ở đây làm "veto tăng" được in như hệ thống TỐT lên.
            row["one_way_gate"] = "sim_metrics.health_guardrail_flags (D-M3-05)"
        else:
            row["significant"] = _sig(lo, hi, n, ms)
        out["system"][key] = row
    return out


def run_ladder(cfg: Config, seeds: list[int], archetype: str = "P4",
               steps: tuple[str, ...] = ("s2_only", "accept_lift", "all"),
               coverage: str = "single") -> dict:
    """Đo THANG BẬC: từng bậc kênh → biết giá trị đến từ đâu (attribution).

    Cùng tài xế đích cho mọi bậc để so sánh công bằng.

    `coverage="all"` trả lời gap mà hồ sơ `07` §6 tự ghi là chưa làm: *"chưa tách đóng góp của
    từng kênh ở chế độ diện rộng"* (ablation cũ chỉ chạy ở mức 1 tài xế).

    Hiệu năng: World A **chạy MỘT LẦN cho mỗi seed** rồi dùng lại cho mọi bậc — A không phụ
    thuộc cấu hình kênh. Ngây thơ chạy lại A ở từng bậc sẽ tốn gấp đôi mà kết quả y hệt.
    """
    from .sim_metrics import adherence_audit
    cfg_a = _cfg_with(cfg, enabled=False, actor_id=None, channels=None)
    ra0 = run_once(cfg_a, seeds[0])
    aid = pick_target(ra0, archetype)

    cache_a = {seeds[0]: ra0}
    out: dict = {}
    for name in steps:
        pairs = []
        for s in seeds:
            ra = cache_a.get(s) or run_once(cfg_a, s)
            cache_a[s] = ra
            rb = run_once(_cfg_with(cfg, enabled=True, actor_id=aid,
                                    channels=CHANNEL_LADDER[name], coverage=coverage), s)
            pairs.append(PairResult(
                seed=s, actor_id=aid,
                a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                system_a=_system_metrics(ra, aid), system_b=_system_metrics(rb, aid),
                adherence_a=adherence_audit(ra), adherence_b=adherence_audit(rb)))
        out[name] = compare(pairs)
        out[name]["adherence"] = aggregate_adherence(pairs, nominal=nominal_adherence(cfg))
        out[name]["health_guardrail"] = aggregate_health_guardrail(pairs)
    return out


def aggregate_health_guardrail(pairs: list[PairResult]) -> dict:
    """D-M3-05 tầng 5 GỘP qua seeds: mean per khoá (A và B) + cổng một chiều trên MEAN.

    Không có bước này thì tầng 5 "sống trên giấy" đúng mẫu D-R12 — hàm có trong
    sim_metrics nhưng không artifact A/B nào mang nó (test T10 canh).
    """
    from .sim_metrics import health_guardrail_flags

    keys = ("rest_min_total", "veto_calls_n", "veto_fired_n",
            "veto_soc_low_n", "veto_fatigued_n", "veto_defer_cap_n",
            "work_span_p50", "work_span_p90", "work_span_max",
            "drive_min_p50", "drive_min_p90", "drive_min_max")

    def _mean(side: str) -> dict:
        rows = [getattr(pr, side) for pr in pairs]
        rows = [r for r in rows if r and "rest_min_total" in r]
        if not rows:
            return {}
        return {k: round(float(st.mean([float(r.get(k) or 0) for r in rows])), 2)
                for k in keys}

    a, b = _mean("system_a"), _mean("system_b")
    flags = health_guardrail_flags(a, b) if a and b else         ["tầng 5 THIẾU DỮ LIỆU (system_a/b không mang khoá sức khoẻ) — không được coi là sạch"]
    return {"a_mean": a, "b_mean": b, "flags": flags,
            "verdict": "TREO — sức khoẻ suy giảm" if flags else "OK"}


def nominal_adherence(cfg: Config) -> dict[str, float]:
    """Adherence DANH NGHĨA của run này — ĐÚNG bộ số mà bridge dùng làm p của coin.

    Rà 2026-07-30 (UPDATE-107) bắt được: cổng thống kê dùng `DEFAULT_ADHERENCE` cứng trong
    khi bridge merge `advice.adherence_by_archetype` từ config (`advice_bridge.py:148`) —
    hai nguồn sự thật, hôm nay TÌNH CỜ trùng giá trị. Khoá config đó tồn tại để được đổi
    (quét độ nhạy, calibrate E10); khi đổi, cổng so với null CŨ ⇒ bắn oan hàng loạt ⇒ bị
    tắt (mẫu `D-R20`). Null của phép kiểm PHẢI là tham số của chính run được kiểm.
    """
    from .advice_bridge import DEFAULT_ADHERENCE
    adv = cfg.data.get("advice") or {}
    return {**DEFAULT_ADHERENCE, **(adv.get("adherence_by_archetype") or {})}


def aggregate_adherence(pairs: list[PairResult], nominal: dict[str, float] | None = None) -> dict:
    """Gộp adherence của arm B qua các seed + cổng BẤT KHẢ (`D-M3-10`).

    Vì sao phải gộp thay vì lấy per-seed: ngưỡng 0,02 của luật gốc là ngưỡng cho TỔNG.
    Với ~250 quyết định/seed, sai số chuẩn lấy mẫu ≈ 0,03 ⇒ cổng 0,02 mỗi seed sẽ bắn
    liên tục vì NHIỄU, và người sửa sẽ nới ngưỡng thay vì sửa lỗi (mẫu đã thấy ở `D-R20`).

    Cổng BẤT KHẢ thì áp per-seed được, vì nó không phải phép kiểm thống kê:
    `decision_adherence` đúng 1,0 hay 0,0 trên mẫu số ≥20 là dấu hiệu mẫu số/tử số hụt.

    `nominal`: adherence danh nghĩa của RUN (xem `nominal_adherence`) — None thì rơi về
    `DEFAULT_ADHERENCE`, chỉ đúng khi run không override `adherence_by_archetype`.
    """
    from .advice_bridge import DEFAULT_ADHERENCE
    from .sim_metrics import adherence_stat_flags

    if nominal is None:
        nominal = DEFAULT_ADHERENCE

    tot: dict[str, dict] = {}
    tot_arche: dict[str, dict] = {}
    flags: list[str] = []
    for pr in pairs:
        for ch, r in (pr.adherence_b.get("by_channel") or {}).items():
            # (c) 2026-07-31: `dismissed`/`suppressed` từng bị BỎ SÓT ⇒ không bao giờ tới
            # artifact ⇒ mất đường phân biệt "tài xế TỪ CHỐI" với "advisor bị NHỊP CHẶN"
            # (hai kết cục khác nhau của ĐA-04). Vi phạm bằng bỏ sót, không bằng tính sai.
            row = tot.setdefault(ch, {"decided": 0, "followed": 0, "dismissed": 0,
                                      "suppressed": 0,
                                      "event_decided": 0, "event_followed": 0})
            for k in row:
                row[k] += int(r.get(k) or 0)
        for key, r in (pr.adherence_b.get("by_channel_archetype") or {}).items():
            row = tot_arche.setdefault(key, {"decided": 0, "followed": 0})
            row["decided"] += int(r.get("decided") or 0)
            row["followed"] += int(r.get("followed") or 0)
        for f in pr.adherence_b.get("flags") or []:
            msg = f"seed {pr.seed}: {f}"
            if msg not in flags:
                flags.append(msg)
    # (a) 2026-07-31 — DET-01 có CỔNG THẬT: `adherence_a` tồn tại kèm comment "arm đối chứng
    # cũng phải được ĐO, không giả định sạch" nhưng KHÔNG cổng nào đọc nó ⇒ đúng họ lỗi
    # `D-R12` (cơ chế sống ở comment + field, không có đường chạy). Arm A có `advice.enabled
    # = false` ⇒ KHÔNG kênh nào được phép có quyết định; có là arm đối chứng bị nhiễm và mọi
    # Δ thành rác (DET-01 đã báo một con số sai cho Cường vì đúng chỗ này).
    for pr in pairs:
        # `getattr` vì một số test dựng stub pair chỉ có `adherence_b` (chúng kiểm cổng THỐNG
        # KÊ, không kiểm cổng đối chứng). `PairResult` thật luôn có cả hai (field có
        # default_factory) ⇒ đường production không lọt. Đánh đổi khai rõ: stub thiếu
        # `adherence_a` sẽ không được cổng này kiểm.
        adh_a = getattr(pr, "adherence_a", None) or {}
        dirty = {ch: int(r.get("decided") or 0)
                 for ch, r in (adh_a.get("by_channel") or {}).items()
                 if int(r.get("decided") or 0) > 0}
        if dirty:
            msg = (f"seed {pr.seed}: arm ĐỐI CHỨNG (advice off) có quyết định {dirty} — "
                   f"arm A KHÔNG SẠCH, mọi Δ của seed này là rác (DET-01)")
            if msg not in flags:
                flags.append(msg)

    for r in tot.values():
        r["decision_adherence"] = (r["followed"] / r["decided"]) if r["decided"] else None
        r["event_adherence"] = ((r["event_followed"] / r["event_decided"])
                                if r["event_decided"] else None)
    # D-M3-10 cổng THỐNG KÊ (chốt UPDATE-103, thi công UPDATE-107): áp trên TỔNG nhiều seed —
    # đúng ngưỡng |z|>4 dẫn xuất được thiết kế cho, không phải per-seed (SE quá thô).
    for f in adherence_stat_flags(tot_arche, nominal):
        if f not in flags:
            flags.append(f)
    return {"by_channel": tot, "flags_per_seed": flags,
            # ⚠ ĐỌC CÁI NÀY TRƯỚC KHI TIN Δ CỦA ARM: có flag ⇒ thước đo của arm đó hỏng
            # ⇒ TREO kết quả, không phải "ghi chú nhỏ" (D-M3-10).
            "verdict": "TREO — thước đo hỏng" if flags else "OK"}
