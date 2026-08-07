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
    # E1a (UPDATE-151 r03 SWAP-07): metric pin phải báo THEO FLEET. Hai lý do đo được:
    # (1) fleet confound 100% với archetype (P1=charge, P2/P4/P6/P7=swap) ⇒ so 2 đội bằng mean
    # gộp là so persona chứ không phải công nghệ pin; (2) `charge_min` LƯỠNG ĐỈNH — swap 1-2′/lượt
    # vs sạc cắm 210′ — mean gộp vô nghĩa, nên downtime pin báo percentile theo đội.
    # Tiền tố `F_` để không đụng namespace `payout_mean_{P*}` (archetype) đã có consumer.
    by_fleet: dict[str, dict[str, list[float]]] = {}
    for a in result.actors:
        f = by_fleet.setdefault(getattr(a.fleet, "value", str(a.fleet)),
                                {"pay": [], "net": [], "charge": []})
        f["pay"].append(float(a.payout_vnd))
        f["net"].append(float(a.payout_vnd) - float(a.cost_vnd))
        f["charge"].append(float(getattr(a, "charge_min", 0.0) or 0.0))
    for fl in sorted(by_fleet):
        v = by_fleet[fl]
        out[f"payout_mean_F_{fl}"] = round(st.mean(v["pay"]), 2)
        out[f"net_mean_F_{fl}"] = round(st.mean(v["net"]), 2)
        out[f"charge_min_p50_F_{fl}"] = round(float(np.percentile(v["charge"], 50)), 1)
        out[f"charge_min_p90_F_{fl}"] = round(float(np.percentile(v["charge"], 90)), 1)
    return out


def _driver_metrics(result, actor_id: int) -> dict:
    m = build_journey(result, actor_id).metrics
    return {k: m[k] for k in (
        "payout_vnd", "trip_payout_vnd", "day_bonus_vnd", "trips_completed",
        "acceptance_rate", "completion_rate", "utilization", "idle_min", "online_min",
        "offers", "declined", "points",
    )}


def _system_metrics(result, exclude_actor: int, health_actor_ids: set[int] | None = None) -> dict:
    """Guardrail: advice KHÔNG được cải thiện 1 người bằng cách làm xấu hệ thống.

    ĐA-08 (UPDATE-075): mở rộng từ 5 trường lên đủ **4 tầng** của chỉ tiêu kép —
    hệ thống · khách hàng · công bằng · tập trung. Bản 5 trường cũ không có Gini, không có
    TỔNG payout (⇒ không phân biệt được positive-sum với tái phân phối), không có đơn hết hạn
    và không có chỉ số dồn cục — tức không thể phát biểu chỉ tiêu kép.

    Số nền đo bằng chính bộ này: `research/audit/2026-07-27-current-state/09-*` (30 seed,
    `coverage: all`). Lưu ý khi đọc: ở n=30 **mọi tầng hệ thống đều có CI chứa 0**; chỗ có ý
    nghĩa thống kê là tầng CÁ NHÂN (payout −17.310đ). Đừng trích số 10-seed của hồ sơ 07.
    """
    from .sim_metrics import health_guardrail, system_guardrail
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
        # --- TẦNG 5 sức khoẻ (D-M3-13) ---
        # NGUỒN của `aggregate_health_guardrail`. Trước 2026-08-01 nó KHÔNG được nối: hàm gộp
        # tồn tại, `health_guardrail` tồn tại, nhưng `system_a`/`system_b` không mang khoá nào
        # ⇒ mọi `run_ladder` trả verdict TREO kèm flag "THIẾU DỮ LIỆU". Đo được (seed 5011):
        # health_guardrail(ra) có rest_min_total=3689.0, veto_fired_n=175 — tức dữ liệu LUÔN
        # có sẵn, chỉ thiếu đúng dòng merge này. Lần thứ BA cùng mẫu D-R12 trong hai ngày.
        # `health_actor_ids` = nhóm BỊ CHẠM (UPDATE-114 lỗ (b)); None = toàn cohort.
        # `compare()` đưa các khoá này vào nhánh MỘT CHIỀU (HEALTH_KEYS_ONE_WAY) nên chúng
        # không bao giờ được gắn `significant` hai chiều.
        **health_guardrail(result, actor_ids=health_actor_ids),
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
    from .sim_metrics import adherence_audit, touched_actors
    # Tập bị chạm lấy từ arm B (arm A không có event advice nên luôn rỗng) rồi áp cho CẢ HAI
    # arm — nhờ CRN, cùng actor_id tồn tại hai bên, nên tầng 5 so đúng CÙNG một nhóm người.
    touched = touched_actors(rb) or None
    return PairResult(seed=seed, actor_id=aid,
                      adherence_a=adherence_audit(ra), adherence_b=adherence_audit(rb),
                      a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                      system_a=_system_metrics(ra, aid, health_actor_ids=touched),
                      system_b=_system_metrics(rb, aid, health_actor_ids=touched))


def _mean_dicts(rows: list[dict]) -> dict:
    """Trung bình theo khoá của nhiều dict metric. Khoá không phải số ⇒ lấy giá trị đầu.

    Dùng để nén NHIỀU NGÀY thành MỘT hàng/seed. Vì sao phải nén: prereg `D-M3-04` khoá
    *"bootstrap resample theo SEED, không theo ngày — các ngày KHÔNG độc lập (cùng actor mang
    memory sang)"*. `bootstrap_ci` resample theo phần tử của list truyền vào, nên chỉ cần bảo đảm
    **một phần tử = một seed** là bootstrap tự đúng chiều; không phải sửa `bootstrap_ci`.
    """
    if not rows:
        return {}
    out: dict = {}
    for k in rows[0]:
        vals = [r[k] for r in rows if k in r]
        nums = [v for v in vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
        out[k] = round(st.mean(nums), 4) if len(nums) == len(vals) and nums else vals[0]
    return out


def _merge_adherence(rows: list[dict]) -> dict:
    """Gộp `adherence_audit` của nhiều ngày thành MỘT (cộng đếm, nối flag).

    Cộng chứ không trung bình: `decided`/`followed` là ĐẾM, và cổng thống kê `D-M3-10` được thiết
    kế cho TỔNG (xem docstring `aggregate_adherence`). Trung bình hoá sẽ làm mẫu số nhỏ đi 3 lần
    và cổng |z|>4 mất hết công suất.
    """
    by_ch: dict[str, dict] = {}
    by_arche: dict[str, dict] = {}
    flags: list[str] = []
    for r in rows:
        for ch, v in (r.get("by_channel") or {}).items():
            row = by_ch.setdefault(ch, {"decided": 0, "followed": 0, "dismissed": 0,
                                        "suppressed": 0, "event_decided": 0,
                                        "event_followed": 0})
            for k in row:
                row[k] += int(v.get(k) or 0)
        for key, v in (r.get("by_channel_archetype") or {}).items():
            row = by_arche.setdefault(key, {"decided": 0, "followed": 0})
            row["decided"] += int(v.get("decided") or 0)
            row["followed"] += int(v.get("followed") or 0)
        for f in r.get("flags") or []:
            if f not in flags:
                flags.append(f)
    return {"by_channel": by_ch, "by_channel_archetype": by_arche, "flags": flags}


def run_pair_multiday(cfg: Config, seed: int, *, days: int, channels_a: dict,
                      channels_b: dict, metric_days: list[int],
                      coverage: str = "all", archetype: str = "P4") -> PairResult:
    """A/B **NHIỀU NGÀY** cho `D-M3-04` — trả MỘT `PairResult` cho MỘT seed.

    Prereg: `specs/simulation/d-m3-04-multiday-prereg-locked.json` (khoá 2026-08-01; đính chính
    ba điểm 2026-08-05 **trước khi đo**).

    ## Vì sao không dùng được `run_pair`

    `run_pair` gọi `run_once` — **một ngày**. Nhưng can thiệp cần đo (`rest_window`) chỉ sống từ
    **ngày thứ hai**: `planned_rest_hour` chỉ được nuôi ở `multiday.py:233` và chỉ khi `d > 0`
    (đo trước khi khoá prereg: decided **0/12/11** theo ngày 0/1/2). Đo một ngày là đo một kênh
    INERT.

    ## Ba ràng buộc của prereg mà hàm này thi hành

    1. **`metric_days` BỎ ngày 0.** Ngày 0 chưa có `DriverMemory` ⇒ `planned_rest_hour` vẫn None
       ⇒ gộp vào là pha loãng chính thứ cần đo.
    2. **MỘT `PairResult`/seed** (xem `_mean_dicts`) ⇒ bootstrap theo SEED.
    3. **`channels` khai TƯỜNG MINH cho CẢ HAI arm** — xem cảnh báo dưới.

    ## 🔴 Vì sao `channels_a` là tham số BẮT BUỘC, không có mặc định `None`

    `_cfg_with` chỉ ghi `advice.channels`/`positioning_overrides` khi `channels is not None`
    (`:88`). Truyền `None` cho arm A ⇒ nó **thừa kế im lặng** `positioning_overrides: wait_only`
    từ `configs/pilot_dongda.yaml`. Kết quả *tình cờ đúng* với prereg (nền A = `wait_only`) nhưng
    **vì lý do sai**: ngày ai đó đổi config, arm A đổi theo mà không phép đo nào biết. Bắt buộc
    khai ⇒ nền của cả hai arm nằm trong artifact, đọc lại được.

    🔴 **KHÔNG dùng `CHANNEL_LADDER["rest_window"]`** — nó bật kèm `shift_plan: True`, mà
    `shift_plan` đã bị ĐA-07/UPDATE-087 TẮT vì **có hại** ⇒ đo trên đó là đo hai can thiệp trộn
    nhau. Prereg cấm tường minh (`thiet_ke.KHONG_dung`).
    """
    from .multiday import run_multiday
    from .sim_metrics import adherence_audit, touched_actors

    if not metric_days:
        raise ValueError("`metric_days` rỗng — không có ngày nào để đo")
    if max(metric_days) >= days:
        raise ValueError(f"`metric_days`={metric_days} vượt quá `days`={days}")

    md_a = run_multiday(_cfg_with(cfg, enabled=True, actor_id=None,
                                  channels=channels_a, coverage=coverage), seed, days=days)
    md_b = run_multiday(_cfg_with(cfg, enabled=True, actor_id=None,
                                  channels=channels_b, coverage=coverage), seed, days=days)

    aid = pick_target(md_a.days[0], archetype)
    # Tập BỊ CHẠM lấy từ arm B rồi áp cho CẢ HAI arm (khuôn `run_pair:218-220`), gộp qua các ngày
    # đo — tầng 5 phải chấm trên `touched_actors`, KHÔNG trên tổng cohort (UPDATE-114 lỗ (b):
    # kênh chạm ~10% tài xế ⇒ chấm trên tổng pha loãng ~10× xuống dưới nhiễu seed).
    touched: set[int] = set()
    for d in metric_days:
        touched |= touched_actors(md_b.days[d])
    touched = touched or None

    return PairResult(
        seed=seed, actor_id=aid,
        adherence_a=_merge_adherence([adherence_audit(md_a.days[d]) for d in metric_days]),
        adherence_b=_merge_adherence([adherence_audit(md_b.days[d]) for d in metric_days]),
        a=_mean_dicts([_driver_metrics(md_a.days[d], aid) for d in metric_days]),
        b=_mean_dicts([_driver_metrics(md_b.days[d], aid) for d in metric_days]),
        system_a=_mean_dicts([_system_metrics(md_a.days[d], aid, health_actor_ids=touched)
                              for d in metric_days]),
        system_b=_mean_dicts([_system_metrics(md_b.days[d], aid, health_actor_ids=touched)
                              for d in metric_days]))


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

# E1a (UPDATE-151 r07-F6): danh sách tường minh ở trên đã HỞ hai lần — `xveto_*` (UPDATE-138)
# và `commit_*` (UPDATE-142) được nối vào tầng 5 SAU khi frozenset chốt, lọt bảng significance
# hai chiều và được in "ĐỘNG TỚI HỆ THỐNG" khi veto tăng. Chặn theo TIỀN TỐ để khoá tầng-5
# tương lai không lặp lại lỗ này; set tường minh giữ cho các khoá không có tiền tố chung
# (rest_min_total, work_span_*, drive_min_*).
_ONE_WAY_PREFIXES = ("veto_", "xveto_", "commit_")


def _is_one_way(key: str) -> bool:
    return key in HEALTH_KEYS_ONE_WAY or key.startswith(_ONE_WAY_PREFIXES)

# MẪU SỐ, không phải kết quả. Tách riêng khỏi `HEALTH_KEYS_ONE_WAY` vì hai lý do khác nhau:
# khoá một chiều bị chặn `significant` để "veto tăng" không đọc thành "hệ thống tốt lên"; khoá
# phạm vi bị chặn vì gắn `significant` cho một MẪU SỐ là vô nghĩa về ngữ nghĩa (Δ của nó luôn 0
# do hai arm dùng cùng tập actor — một "kết quả không đáng kể" hoàn toàn gây nhầm).
SCOPE_KEYS = frozenset({"n_actors_scope"})


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
    ms = min_seeds if min_seeds is not None else MIN_SEEDS_FOR_SIGNIFICANCE
    # E1a (r07-F3/BUG-PARALLEL-NINSUF): `n_insufficient` phải so với NGƯỠNG HIỆU LỰC, không
    # phải hằng 30 — caller truyền min_seeds=100 (so biến-thể, T-041 1b') mà cờ vẫn so 30 thì
    # artifact n=50 báo "mẫu đủ" trong khi mọi significant bị chặn ở 100: hai cờ tự mâu thuẫn.
    out: dict = {"n_seeds": n, "n_insufficient": n < ms,
                 "driver": {}, "system": {}, "min_seeds_for_sig": ms}
    if not pairs:
        return out
    # E1a (r07-F8): keys là UNION qua mọi pair, không phải pairs[0] — archetype/khoá vắng ở
    # seed đầu bị RƠI IM LẶNG, vắng ở seed sau thì KeyError. Cặp thiếu khoá bị BỎ QUA cho khoá
    # đó và `n_pairs` khai tường minh (không ép 0 im lặng — 0 là một GIÁ TRỊ, vắng là VẮNG).

    def _rows(get_a, get_b, keys, digits):
        rows = {}
        for key in sorted(keys):          # union là set — sort để artifact/CLI ổn định khi diff
            sub = [p for p in pairs if key in get_a(p) and key in get_b(p)]
            if not sub:
                continue
            va = [float(get_a(p)[key] or 0) for p in sub]
            vb = [float(get_b(p)[key] or 0) for p in sub]
            diffs = [b - a for a, b in zip(va, vb)]
            lo, hi = bootstrap_ci(diffs)
            row = {
                "mean_a": round(st.mean(va), digits),
                "mean_b": round(st.mean(vb), digits),
                "delta_mean": round(st.mean(diffs), digits),
                "ci95": (round(lo, digits), round(hi, digits)),
                "n_positive": sum(1 for d in diffs if d > 0),
                "_n_sub": len(sub), "_lo_hi": (lo, hi),
            }
            if len(sub) < n:
                row["n_pairs"] = len(sub)
            rows[key] = row
        return rows

    for key, row in _rows(lambda p: p.a, lambda p: p.b,
                          {k for p in pairs for k in p.a}, 2).items():
        n_sub, (lo, hi) = row.pop("_n_sub"), row.pop("_lo_hi")
        row["significant"] = _sig(lo, hi, n_sub, ms)
        out["driver"][key] = row
    for key, row in _rows(lambda p: p.system_a, lambda p: p.system_b,
                          {k for p in pairs for k in p.system_a}, 4).items():
        n_sub, (lo, hi) = row.pop("_n_sub"), row.pop("_lo_hi")
        if key in SCOPE_KEYS:
            row.pop("n_positive", None)
            row["role"] = "MẪU SỐ — số tài xế trong phạm vi chấm tầng 5, KHÔNG phải kết quả"
        elif _is_one_way(key):
            # (e) tầng 5 KHÔNG có `significant` hai chiều — cổng của nó là
            # `sim_metrics.health_guardrail_flags` (một chiều, chỉ tố giác suy giảm).
            # Để `significant` ở đây làm "veto tăng" được in như hệ thống TỐT lên.
            # E1a: match theo `_is_one_way` (tiền tố) — xveto_*/commit_* từng lọt (r07-F6).
            row["one_way_gate"] = "sim_metrics.health_guardrail_flags (D-M3-05)"
        else:
            row["significant"] = _sig(lo, hi, n_sub, ms)
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
    from .sim_metrics import adherence_audit, touched_actors
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
            touched = touched_actors(rb) or None      # xem ghi chú ở run_pair
            pairs.append(PairResult(
                seed=s, actor_id=aid,
                a=_driver_metrics(ra, aid), b=_driver_metrics(rb, aid),
                system_a=_system_metrics(ra, aid, health_actor_ids=touched),
                system_b=_system_metrics(rb, aid, health_actor_ids=touched),
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

    # ⚠ ĐÍNH CHÍNH Cycle 4 (2026-08-07) — danh sách này TRƯỚC ĐÂY CHÉP TAY và chỉ có `veto_*`.
    # Hệ quả đo được (`research/audit/2026-08-07-root-cause-classes/c4b-do-vung-mu-tang-5.json`):
    # **9 khoá** (`xveto_*` ×5, `commit_*` ×4) được `_ONE_WAY_PREFIXES` đẩy RA KHỎI bảng
    # significance hai chiều **vào một cổng không hề soi chúng**, và cũng không vào `a_mean` —
    # trong khi artifact vẫn in cạnh chúng `"one_way_gate": "health_guardrail_flags"`, tức một
    # LỜI KHAI QUẢN TRỊ KHÔNG CÓ THẬT. Đây là lần **thứ ba** cùng một lỗi: `parallel.py:415-419`
    # đã chép rằng danh sách tường minh *"đã HỞ hai lần"*, và bản vá lần đó chỉ nối **chiều đi
    # ra** (khỏi bảng hai chiều), quên **chiều đi vào** (tới cổng).
    #
    # Nay SUY RA từ chính các hằng rail — thêm một rail là nó tự vào đây, không phải nhớ sửa.
    from .sim_metrics import COMMIT_KEYS, EXTEND_RAILS, REST_RAILS

    keys = ("rest_min_total",
            "veto_calls_n", "veto_fired_n", *(f"veto_{r}_n" for r in REST_RAILS),
            "xveto_calls_n", "xveto_fired_n", *(f"xveto_{r}_n" for r in EXTEND_RAILS),
            *COMMIT_KEYS,
            "work_span_p50", "work_span_p90", "work_span_max",
            "drive_min_p50", "drive_min_p90", "drive_min_max",
            # MẪU SỐ phải hiện trong artifact: cùng một verdict OK có nghĩa hoàn toàn khác
            # khi chấm trên 90/90 tài xế (cổng nhạy) so với 9/90 (pha loãng ~10× ⇒ cổng canh
            # nhiễu). Thiếu khoá này thì người đọc không phân biệt được hai ca đó.
            "n_actors_scope")

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


def aggregate_adherence(pairs: list[PairResult], nominal: dict[str, float] | None = None,
                        *, control_clean_channels: tuple[str, ...] | None = None,
                        gate_both_arms: bool = False) -> dict:
    """Gộp adherence của arm B qua các seed + cổng BẤT KHẢ (`D-M3-10`).

    Vì sao phải gộp thay vì lấy per-seed: ngưỡng 0,02 của luật gốc là ngưỡng cho TỔNG.
    Với ~250 quyết định/seed, sai số chuẩn lấy mẫu ≈ 0,03 ⇒ cổng 0,02 mỗi seed sẽ bắn
    liên tục vì NHIỄU, và người sửa sẽ nới ngưỡng thay vì sửa lỗi (mẫu đã thấy ở `D-R20`).

    Cổng BẤT KHẢ thì áp per-seed được, vì nó không phải phép kiểm thống kê:
    `decision_adherence` đúng 1,0 hay 0,0 trên mẫu số ≥20 là dấu hiệu mẫu số/tử số hụt.

    `nominal`: adherence danh nghĩa của RUN (xem `nominal_adherence`) — None thì rơi về
    `DEFAULT_ADHERENCE`, chỉ đúng khi run không override `adherence_by_archetype`.

    ## `control_clean_channels` — DET-01 thu hẹp (`D-M3-04`, Cường chốt 2026-08-05)

    `None` (mặc định) = hành vi CŨ: arm A không được có quyết định ở **bất kỳ** kênh nào. Đúng khi
    arm A là `advice.enabled=false` — đó là mọi đường hiện hành (`run_pair:213`).

    Truyền một tuple = arm A chỉ phải sạch ở **những kênh đó**. Cần cho `D-M3-04`, nơi prereg định
    nghĩa `arm_A = positioning wait_only` — tức advice **BẬT**, luôn có quyết định `positioning`.
    Với hành vi cũ, cổng sẽ TREO **100% số seed** và phép đo không bao giờ chạy được.

    ⚠ Đây là **sửa nghĩa một cổng đã khoá trong prereg** — đã ghi vào
    `d-m3-04-multiday-prereg-locked.json` → `dinh_chinh_TRUOC_KHI_DO_2026_08_05` **trước khi chạy
    một seed nào**. Làm sau khi thấy số thì không phân biệt được với "nới cổng cho verdict đẹp".
    Lý lẽ: DET-01 sinh ra để bảo đảm arm đối chứng **sạch khỏi CAN THIỆP ĐANG ĐO**; nền `wait_only`
    giống nhau ở hai arm nên nó triệt tiêu trong hiệu số.

    ## `gate_both_arms` — STOP-A

    `False` (mặc định) = cổng thống kê |z|>4 chỉ soi **arm B**, như trước. `True` = soi **cả hai** —
    prereg `D-M3-04` STOP-A nói *"TREO ở BẤT KỲ arm nào"*, mà bản cũ chỉ đọc `adherence_b`.
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
                 if int(r.get("decided") or 0) > 0
                 and (control_clean_channels is None or ch in control_clean_channels)}
        if dirty:
            pham_vi = ("mọi kênh" if control_clean_channels is None
                       else f"kênh đang đo {list(control_clean_channels)}")
            msg = (f"seed {pr.seed}: arm ĐỐI CHỨNG có quyết định {dirty} ({pham_vi}) — "
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
    # STOP-A của `D-M3-04`: *"TREO ở BẤT KỲ arm nào"*. Bản cũ chỉ gộp `adherence_b` (`:452`) ⇒ arm
    # A hoàn toàn không qua cổng thống kê. Với `run_pair` thì vô hại (arm A advice-off, không có
    # quyết định nào để chấm), nhưng `D-M3-04` có arm A BẬT positioning ⇒ arm đó cũng có thước
    # adherence riêng, và một thước hỏng ở arm A làm hỏng Δ y như ở arm B.
    if gate_both_arms:
        tot_arche_a: dict[str, dict] = {}
        for pr in pairs:
            adh_a = getattr(pr, "adherence_a", None) or {}
            for key, r in (adh_a.get("by_channel_archetype") or {}).items():
                row = tot_arche_a.setdefault(key, {"decided": 0, "followed": 0})
                row["decided"] += int(r.get("decided") or 0)
                row["followed"] += int(r.get("followed") or 0)
        for f in adherence_stat_flags(tot_arche_a, nominal):
            msg = f"[arm A] {f}"
            if msg not in flags:
                flags.append(msg)
    return {"by_channel": tot, "flags_per_seed": flags,
            # ⚠ ĐỌC CÁI NÀY TRƯỚC KHI TIN Δ CỦA ARM: có flag ⇒ thước đo của arm đó hỏng
            # ⇒ TREO kết quả, không phải "ghi chú nhỏ" (D-M3-10).
            "verdict": "TREO — thước đo hỏng" if flags else "OK"}
