"""Solver S2 — ShiftDP (timing-only). DP tối ưu lịch online/nghỉ/sạc/kết-ca cả ca.

Bài toán (spec advisor-optimization-layer-a §2.1): max E[payout] gồm terminal mốc
thưởng NGÀY. Action/bucket {ONLINE, REST, SWAP, END}. KHÔNG cell/reposition (product
boundary). Forecast từ historical (no future-leak — chỉ đọc demand_forecast trong input).
State augment points_band để terminal bonus đúng. Thuần numpy, deterministic.
Trả SolverReport (schedule + next_action + delta E[payout]). Mọi số có source.
"""

from __future__ import annotations

import numpy as np

from gsm_core.policy import PolicyBundle

ACTIONS = ("ONLINE", "REST", "SWAP", "END")  # thứ tự = tie-break priority
DEFAULT_PARAMS = {
    "p_accept": 0.9,               # xác suất nhận đơn — CALLER NÊN TRUYỀN số thật (AUDIT S2-4)
    "avg_dist_km": 3.0,            # quãng đường TB — CALLER NÊN TRUYỀN từ data (AUDIT S2-5)
    "soc_bands": 10,               # rời rạc hóa SOC
    "points_bands": 16,            # rời rạc hóa điểm cho terminal
    "points_band_size": 15,        # mỗi band = 15 điểm (0..240)
    "soc_cost_per_bucket": 1,      # SOC band tiêu hao/bucket online 30' (scale theo bucket_min)
    "rest_min_per_4h": 1,          # số bucket nghỉ TỐI THIỂU mỗi 4h ca (nhu cầu sinh lý)
    # AUDIT S2-6 (UPDATE-069): bucket KHÔNG còn ngầm định 30' — producer sim/l1r dùng 60'.
    "bucket_min": 30,
    # AUDIT S2-7 mitigation: 1 tài xế phục vụ tối đa bucket_min/service_min cuốc/bucket —
    # demand forecast là CẢ CELL, không thể dồn hết vào 1 người. Chia-cạnh-tranh-cung thật
    # là MODEL GAP (đề án); cap này chỉ chặn phóng đại phi lý.
    "service_min_per_trip": 25.0,
    # AUDIT S2-3: terminal bonus chỉ được hứa khi đủ ngưỡng tỷ lệ (cùng chính sách S1-1).
    # None = caller không cấp số → GIỮ bonus nhưng thêm caveat (không bịa hướng ngược).
    "acceptance_rate": None,
    "completion_rate": None,
    # Model note: US-F2-02 — tài xế SẼ nghỉ (nhu cầu thật); DP tối ưu ĐẶT nghỉ vào
    # demand thấp nhất. Objective = payout THUẦN (không phạt fatigue ảo). delta ≥ 0
    # so baseline "nghỉ ngây thơ đầu ca". Fatigue-as-money bị bỏ (không bịa số §5).
    #
    # B2/C1 (PLAN-cycle-wx, 2026-07-29) — CHI PHÍ VẬN HÀNH/km, mặc định 0:
    # KHÔNG mâu thuẫn với dòng "fatigue-as-money bị bỏ" ở trên — fatigue là SỐ BỊA
    # (không nguồn), còn C1 có nguồn OFFICIAL (điện 70–93đ/km sạc nhà; đổi pin 9.000đ/lượt
    # SAU 31/03/2029 — research/economics/driver-cost-structure-2026.md). Giá trị do
    # POLICY quyết định theo (track, as_of) ở B3; caller truyền số, solver không bịa.
    # Chi phí đổi QUYẾT ĐỊNH (giá trị net nội bộ của DP) nhưng expected_payout_vnd
    # BÁO CÁO vẫn là GROSS payout — §5 tách gross/payout/net, test canh.
    "cash_cost_vnd_per_km": 0.0,
    # C5 (plan 2026-07-29): phí MỘT LƯỢT đổi pin — nguồn official 9.000đ/lượt sau
    # 31/03/2029 (driver-cost-structure-2026). Mặc định 0 = đúng chính sách hiện hành.
    # Tính TẠI SỰ KIỆN swap (không khấu hao vào cash/km — chống đếm kép, xem policy.py).
    "swap_fee_vnd": 0.0,
}


def _required_rest(B: int, params: dict, rest_taken_min: float | None = None,
                   shift_elapsed_min: float | None = None) -> int:
    """Số bucket nghỉ tối thiểu cho ca còn B bucket — theo PHÚT THẬT của bucket
    (AUDIT S2-6: bản cũ hardcode 30' → producer 60' bị tính nghỉ thiếu một nửa).

    ## Cycle R / H1 (2026-07-28) — TÍN DỤNG cho nghỉ ĐÃ NGHỈ

    Bản mù-state bị TÁI ÁP mỗi lần hỏi: mỗi consult tính lại `R` cho phần ca còn lại và ép nghỉ
    đủ R **bất kể tài xế vừa nghỉ xong**. Reproduce 3 seed: advisor làm tổng nghỉ +16–27%,
    11–14 lần/seed tái-khuyên REST trong 60′ sau một lần nghỉ hoàn tất.

    ## ⚠ Công thức ĐẦU TIÊN đã bị số liệu BÁC BỎ — ghi lại để không ai đi lại đường này

    Bản đầu dùng `R = nhu_cầu_CẢ_CA − đã_nghỉ` (backfill). Đo 3 seed: advisory REST nổ
    **55–66 → 145–178/seed**, tổng nghỉ **+16–27% → +39–54%** — vì tài xế CHƯA nghỉ (do đang
    bận kiếm tiền, điều tốt) bị đòi bù cả phần quá khứ: giữa ca 10h chưa nghỉ thì cả-ca đòi
    2 bucket trong khi công thức cũ chỉ đòi 1 cho phần còn lại.

    Công thức hiện tại — **TÍN DỤNG ĐƠN ĐIỆU AN TOÀN** (`R_mới ≤ R_cũ` luôn):

        surplus = max(0, đã_nghỉ_quy_bucket − nhu_cầu_phần_ca_ĐÃ_QUA)
        R       = clamp( nhu_cầu_phần_còn_lại (công thức cũ) − surplus , 0 , B )

    Nghỉ VƯỢT mức cần của phần ca đã qua mới được trừ vào phần còn lại; thiếu hụt quá khứ
    KHÔNG bị bắt bù (thế giới này không phạt việc chưa nghỉ — ép bù là lỗ thuần, hồ sơ 18 §2.2).
    KHÔNG truyền state (producer l1r, caller cũ) ⇒ đúng công thức cũ từng bit.

    Đây là fix VISIBILITY (cấp state có thật), không phải "giá trị nghỉ" (Cường cấm bịa số).
    """
    bucket_min = int(params.get("bucket_min", 30))
    forward = min(B, (B * bucket_min // 240) * params["rest_min_per_4h"])
    if rest_taken_min is None or shift_elapsed_min is None:
        return forward
    elapsed_need = (int(max(0.0, float(shift_elapsed_min))) // 240) * params["rest_min_per_4h"]
    taken = int(round(max(0.0, float(rest_taken_min)) / bucket_min))
    surplus = max(0, taken - elapsed_need)
    return max(0, forward - surplus)


def _soc_cost(params: dict) -> int:
    """SOC band/bucket online — chuẩn theo 30', scale theo bucket_min (S2-6).

    BLOCKER-R5-MUT10 (UPDATE-074): dòng return từng bị thay bằng mutation thử-nghiệm
    (`return int(params["soc_cost_per_bucket"])` — bỏ scale) khi một reviewer agent chạy
    mutation-test rồi bị quota giết trước lúc khôi phục; commit `7739b3c` cuốn luôn vào
    repo vì `git add -A`. Mutation ĐÃ SỐNG SÓT qua test — nghĩa là không test nào phủ
    bucket_min ≠ 30 ⇒ nay có `test_soc_cost_scales_with_bucket_min`.
    """
    bucket_min = int(params.get("bucket_min", 30))
    return max(1, round(int(params["soc_cost_per_bucket"]) * bucket_min / 30.0))


def _bonus_eligible(params: dict, policy: PolicyBundle) -> tuple[bool, bool]:
    """(đủ điều kiện thưởng?, có số để xét?) — S2-3: dưới ngưỡng thì mọi nhánh bonus_at = 0."""
    acc, comp = params.get("acceptance_rate"), params.get("completion_rate")
    if acc is None or comp is None:
        return True, False
    return (float(acc) >= policy.bonus_min_acceptance
            and float(comp) >= policy.bonus_min_completion), True


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _num(value, unit, source):
    return {"value": round(float(value), 3), "unit": unit, "source": source}


def _payout_per_order(policy: PolicyBundle, avg_dist_km: float) -> float:
    gross = policy.base_fare_vnd + max(0.0, avg_dist_km - policy.base_km) * policy.per_km_vnd
    return gross * policy.driver_share


def _points_of_hour(policy: PolicyBundle, hour: int) -> int:
    return policy.trip_points(hour)


def _forecast_arrays(spi: dict, params: dict, demand_scale: float):
    """AUDIT S2-2 (UPDATE-069): producer (bridge sim lẫn l1r) sinh NHIỀU dòng/bucket
    (mỗi cell 1 dòng) — bản cũ đọc theo INDEX làm demand lệch giờ + mất bucket cuối
    (E[payout] sai ~×2, repro trong verify-11). Nay GỘP theo timestamp bucket, sort
    thời gian, và CAP theo sức chứa phục vụ (S2-7 mitigation)."""
    B = int(spi["buckets_remaining"])
    bucket_min = float(params.get("bucket_min", 30))
    cap_trips = bucket_min / float(params.get("service_min_per_trip", 25.0))
    grouped: dict[str, float] = {}
    for row in spi["demand_forecast"]:
        b = row["bucket"]
        grouped[b] = grouped.get(b, 0.0) + float(row["expected_orders"])
    buckets: list[str | None] = sorted(grouped)[:B]
    eo = [min(cap_trips, grouped[b] * demand_scale) for b in buckets]
    hrs = [_hour(b) for b in buckets]
    while len(eo) < B:          # forecast thiếu bucket → demand 0 (giữ ngữ nghĩa cũ)
        eo.append(0.0)
        hrs.append(hrs[-1] + 1 if hrs else 12)
        buckets.append(None)
    return B, eo, hrs, buckets


def _solve_dp(spi: dict, policy: PolicyBundle, params: dict, demand_scale: float = 1.0):
    """DP: max E[payout] THUẦN với ràng buộc nghỉ tối thiểu R (đặt nghỉ vào demand thấp)
    + SOC (swap khi cạn) + terminal mốc thưởng ngày. State (b, soc, points, rests_left).
    Trả (schedule actions, expected_payout, projected_points)."""
    B, eo, hrs, _ = _forecast_arrays(spi, params, demand_scale)
    if B <= 0:
        return [], 0.0, int(spi["points_now"])
    NB, PBS, NS = params["points_bands"], params["points_band_size"], params["soc_bands"]
    R = _required_rest(B, params, spi.get("rest_taken_min"), spi.get("shift_elapsed_min"))
    ppo = _payout_per_order(policy, params["avg_dist_km"])
    p_acc = params["p_accept"]
    soc_cost = _soc_cost(params)
    eligible, _has_rates = _bonus_eligible(params, policy)
    bonus_at = (lambda pts: policy.bonus_at(pts)) if eligible else (lambda pts: 0)

    pts0 = min(NB - 1, int(spi["points_now"]) // PBS)
    soc0 = NS - 1 if spi.get("soc_pct") is None else \
        min(NS - 1, max(0, int(spi["soc_pct"] / (100.0 / NS))))

    NEG = -1e18
    shape = (B + 1, NS, NB, R + 1)
    V = np.full(shape, NEG)
    A = np.zeros(shape, dtype=np.int8)

    # terminal: phải nghỉ đủ (rests_left==0) mới hợp lệ; bonus theo điểm
    for soc in range(NS):
        for pb in range(NB):
            V[B, soc, pb, 0] = bonus_at(pb * PBS)
            # rests_left>0 tại B = vi phạm → NEG (buộc DP nghỉ đủ trong ca)

    # B2/C1: chi phí vận hành/km — mặc định 0 ⇒ online_net == online_pay (bit-identical).
    # Giá trị QUYẾT ĐỊNH của nhánh ONLINE là NET; báo cáo payout vẫn GROSS (xem reconstruct).
    cash_km = float(params.get("cash_cost_vnd_per_km", 0.0) or 0.0)
    cost_per_trip = cash_km * float(params["avg_dist_km"])
    # C5: gia MOT LUOT swap — fee=0 ⇒ nhánh SWAP y hệt cũ (tie-break Cycle R giữ nguyên)
    swap_fee = float(params.get("swap_fee_vnd", 0.0) or 0.0)

    for b in range(B - 1, -1, -1):
        buckets_left = B - b
        exp_trips = eo[b] * p_acc
        pph = _points_of_hour(policy, hrs[b])
        # gross payout kỳ vọng được tính lại ở reconstruct (báo cáo); DP chỉ cần NET
        online_net = exp_trips * (ppo - cost_per_trip)
        add_pts = int(round(exp_trips * pph))
        for soc in range(NS):
            nsoc_online = max(0, soc - soc_cost)
            npb_online = lambda pb: min(NB - 1, pb + add_pts // PBS)  # noqa: E731
            for pb in range(NB):
                np_on = npb_online(pb)
                for rl in range(R + 1):
                    # nếu rests_left > buckets_left → không thể nghỉ đủ → NEG
                    if rl > buckets_left:
                        continue
                    best_v, best_a = NEG, 0
                    # ONLINE (chỉ khi còn SOC, còn chỗ ngoài nghỉ bắt buộc, VÀ kỳ vọng
                    # NET>0 — B2/C1: online mà mỗi cuốc lỗ tiền mặt thì vô ích như
                    # demand=0, nhường END/REST. cash=0 ⇒ net==pay, hành vi y hệt cũ.)
                    if soc > 0 and rl < buckets_left and online_net > 0:
                        v = online_net + V[b + 1, nsoc_online, np_on, rl]
                        if v > best_v:
                            best_v, best_a = v, 0  # ONLINE
                    # Cycle R / H3 (2026-07-28): SWAP xét TRƯỚC REST — thứ tự CÓ CHỦ Ý.
                    # Cả hai cùng 0 thu nhập tức thời nên rất hay HOÀ, và `v > best_v`
                    # (so sánh chặt) trao mọi thế hoà cho nhánh xét trước. Bản cũ xét REST
                    # trước ⇒ fixture SOC=22% + demand phẳng cho lịch `ONLINE,REST,REST,
                    # SWAP,…` — nghỉ hai bucket TRƯỚC khi đổi pin dưới ngưỡng, khớp 7–12
                    # lần `go_swap → rest`/seed đo ngoài sim. Thế giới thật không hoà:
                    # hoãn swap ⇒ pin tụt + hàng đợi trạm + 11% thất bại — DP không mô hình
                    # hoá các chi phí đó nên tối thiểu thứ tự ưu tiên phải nghiêng về swap.
                    # (Không thêm số bịa nào — chỉ đổi tie-break.)
                    # SWAP (nạp đầy; tính như 1 bucket không kiếm tiền)
                    if rl < buckets_left:
                        # C5: swap có GIÁ THẬT (policy) — fee=0 giữ 0.0 + tie-break cũ;
                        # fee>0 ⇒ swap thừa thua REST, DP tự cân "chạy nốt hay giữ pin"
                        v = -swap_fee + V[b + 1, NS - 1, pb, rl]
                        if v > best_v:
                            best_v, best_a = v, 2  # SWAP
                    # REST (giảm rests_left nếu còn cần)
                    nrl = rl - 1 if rl > 0 else 0
                    v = 0.0 + V[b + 1, soc, pb, nrl]
                    if v > best_v:
                        best_v, best_a = v, 1  # REST
                    # END chỉ hợp lệ khi đã nghỉ đủ (rl==0)
                    if rl == 0:
                        v = bonus_at(pb * PBS)  # kết ca: chốt bonus hiện có (đã gate S2-3)
                        if v > best_v:
                            best_v, best_a = v, 3  # END
                    V[b, soc, pb, rl] = best_v
                    A[b, soc, pb, rl] = best_a

    # reconstruct
    schedule, soc, pb, rl = [], soc0, pts0, R
    proj_points, exp_payout, n_swaps = spi["points_now"], 0.0, 0
    ended = False
    for b in range(B):
        if ended:
            schedule.append("END")
            continue
        a = int(A[b, soc, pb, rl])
        act = ACTIONS[a]
        schedule.append(act)
        if act == "ONLINE":
            et = eo[b] * p_acc
            exp_payout += et * ppo
            ap = int(round(et * _points_of_hour(policy, hrs[b])))
            proj_points += ap
            pb = min(NB - 1, pb + ap // PBS)
            soc = max(0, soc - soc_cost)
        elif act == "REST":
            rl = max(0, rl - 1)
        elif act == "SWAP":
            soc = NS - 1
            n_swaps += 1
        elif act == "END":
            ended = True
    exp_payout += bonus_at(proj_points)
    return schedule, exp_payout, proj_points, n_swaps


def _baseline_naive_rest(spi: dict, policy: PolicyBundle, params: dict,
                         demand_scale: float = 1.0) -> float:
    """Baseline: nghỉ R bucket ĐẦU CA (ngây thơ — mất demand sáng), swap khi cạn.
    DP đặt nghỉ vào demand thấp nhất → luôn ≥ baseline này."""
    B, eo, hrs, _ = _forecast_arrays(spi, params, demand_scale)
    if B <= 0:
        return 0.0, 0
    eligible, _hr = _bonus_eligible(params, policy)
    R = _required_rest(B, params)
    ppo = _payout_per_order(policy, params["avg_dist_km"])
    pts, payout, n_swaps = spi["points_now"], 0.0, 0
    soc = params["soc_bands"] - 1 if spi.get("soc_pct") is None else \
        min(params["soc_bands"] - 1, int(spi["soc_pct"] / (100.0 / params["soc_bands"])))
    for i in range(B):
        if i < R:  # nghỉ đầu ca
            continue
        if soc <= 0:
            soc = params["soc_bands"] - 1
            n_swaps += 1
            continue  # bucket này đi swap (C5: chi phí expose ở baseline_swap_cost_vnd)
        et = eo[i] * params["p_accept"]
        payout += et * ppo
        pts += int(round(et * _points_of_hour(policy, hrs[i])))
        soc -= _soc_cost(params)
    payout += policy.bonus_at(pts) if eligible else 0
    return payout, n_swaps


def solve(spi: dict, policy: PolicyBundle, params: dict | None = None) -> dict:
    """spi = shift_plan_input record. Trả solver_report record.

    B3 (PLAN-cycle-wx): `params["policy_costs_as_of"]` bật đường POLICY-QUYẾT-ĐỊNH-CHI-PHÍ
    — solver tra `resolve_cost_params(policy, as_of)` để biết số hạng nào sống/chết và
    giá trị nào được điền (vế A5 tầm nhìn: "hàm tối ưu cập nhật giá trị biến theo chính
    sách"). Đi qua `params` CÓ CHỦ Ý: guard chống-future-leak pin chữ ký (spi, policy,
    params) — as_of là ngữ cảnh "bây giờ", không phải data tương lai, và opt-in tường
    minh giữ mọi caller cũ nguyên vẹn (không terms_active, không caveat mới).
    Quy tắc nguồn: `params["cash_cost_vnd_per_km"]` TƯỜNG MINH thắng policy (đường sim
    B2 — nguồn sự thật của sim là config). UNKNOWN ⇒ dùng 0 + caveat, KHÔNG bịa (§5).
    """
    p = {**DEFAULT_PARAMS, **(params or {})}
    terms_active: list[dict] | None = None
    as_of = (params or {}).get("policy_costs_as_of")
    if as_of is not None:
        from gsm_core.policy import resolve_cost_params
        resolved = resolve_cost_params(policy, as_of)
        cash_term = dict(resolved["cash_per_km"])
        if params is not None and "cash_cost_vnd_per_km" in params:
            cash_term = {"value": float(params["cash_cost_vnd_per_km"]),
                         "state": "ACTIVE", "source": "params(explicit)",
                         "reason": "caller truyền tường minh — thắng policy (đường sim)"}
        else:
            p["cash_cost_vnd_per_km"] = cash_term["value"]
        battery_term = dict(resolved["battery"])
        if params is not None and "swap_fee_vnd" in params:
            battery_term = {"value": float(params["swap_fee_vnd"]), "state": "ACTIVE",
                            "per": "swap", "source": "params(explicit)",
                            "reason": "caller truyền tường minh — thắng policy (đường sim)"}
        elif battery_term["state"] == "ACTIVE":
            p["swap_fee_vnd"] = battery_term["value"]   # C5: DP trả phí tại sự kiện swap
        terms_active = [{"term": "cash_per_km", **cash_term},
                        {"term": "battery", **battery_term}]
    B = int(spi["buckets_remaining"])
    fc = spi["demand_forecast"]
    forecast_source = "historical_forecast" if spi["source"] in ("MOCK", "REAL") else "dp:fallback"
    confidence = 0.8 if len(fc) >= B and B > 0 else 0.5
    pv = f"policy_v:{policy.version}"

    schedule_acts, exp_payout, proj_points, n_swaps = _solve_dp(spi, policy, p)
    baseline, baseline_swaps = _baseline_naive_rest(spi, policy, p)
    delta = exp_payout - baseline

    # S2-2: nhãn bucket lấy từ danh sách ĐÃ GỘP-SORT (không phải fc[i] thô đa-cell)
    _, _, _, bucket_labels = _forecast_arrays(spi, p, 1.0)
    schedule = [{"bucket": bucket_labels[i], "action": schedule_acts[i]}
                for i in range(len(schedule_acts))]

    # next_action nổi bật = action đầu tiên KHÁC ONLINE, else ONLINE bucket 0
    next_action = {"action": schedule_acts[0] if schedule_acts else "END",
                   "bucket": bucket_labels[0] if bucket_labels else None,
                   "reason": "bắt đầu ca theo lịch tối ưu"}
    for i, act in enumerate(schedule_acts):
        if act in ("REST", "SWAP", "END"):
            next_action = {"action": act, "bucket": bucket_labels[i] if i < len(bucket_labels) else None,
                           "reason": {"REST": "nghỉ lệch khung demand thấp",
                                      "SWAP": "đổi pin trước khi cạn",
                                      "END": "kết ca — thêm giờ không tăng kỳ vọng"}[act]}
            break

    eligible, has_rates = _bonus_eligible(p, policy)
    proj_tier = policy.bonus_at(proj_points) if eligible else 0

    numbers = [
        _num(exp_payout, "vnd", f"dp:{forecast_source}"),
        _num(baseline, "vnd", f"dp:{forecast_source}"),
        _num(delta, "vnd", "dp:computed"),
        _num(proj_points, "points", f"dp:{forecast_source}"),
        _num(proj_tier, "vnd", pv),
        _num(_payout_per_order(policy, p["avg_dist_km"]), "vnd_per_order", pv),
    ]

    # sensitivity: demand −20%/−40% → re-solve delta (cùng demand_scale cho cả baseline)
    sensitivity = []
    for pct in (0.20, 0.40):
        _, ep2, _, _ = _solve_dp(spi, policy, p, demand_scale=1 - pct)
        bl2, _ = _baseline_naive_rest(spi, policy, p, demand_scale=1 - pct)
        sensitivity.append({"param": f"demand_-{int(pct * 100)}%",
                            "delta_payout": round(ep2 - bl2, 1)})

    n_online = sum(1 for a in schedule_acts if a == "ONLINE")
    n_rest = sum(1 for a in schedule_acts if a == "REST")
    digest = (f"Tài xế {spi['driver_id']}: lịch {B} bucket tối ưu — "
              f"{n_online} bucket chạy, {n_rest} nghỉ; điểm dự kiến {proj_points} "
              f"(mốc {proj_tier:,}đ); E[payout] {exp_payout:,.0f}đ "
              f"(hơn baseline {delta:+,.0f}đ).")

    caveats = ["số cuốc thực phụ thuộc nhu cầu (forecast lịch sử) — không đảm bảo",
               "advice timing, không chỉ định khu vực/đơn cụ thể"]
    if confidence < 0.8:
        caveats.append("thiếu forecast đầy đủ — độ tin thấp")
    if not has_rates:
        caveats.append("chưa có tỷ lệ nhận/hoàn thành để xét điều kiện thưởng — "
                       "mốc thưởng chỉ đạt khi tỷ lệ giữ trên ngưỡng")
    elif not eligible:
        caveats.append("tỷ lệ nhận/hoàn thành đang DƯỚI ngưỡng — mốc thưởng sẽ KHÔNG được trả "
                       "nếu giữ nguyên (E[payout] đã bỏ thưởng)")
    if terms_active is not None:
        for t in terms_active:
            if t["state"] == "UNKNOWN":
                caveats.append(f"chi phí '{t['term']}' UNKNOWN — {t['reason']}; "
                               f"dùng 0, KHÔNG bịa số")

    fee_out = float(p.get("swap_fee_vnd", 0.0) or 0.0)
    solution = {
        "schedule": schedule, "next_action": next_action,
        "expected_payout": round(exp_payout, 1), "baseline_payout": round(baseline, 1),
        "delta_payout": round(delta, 1),
        "projected_points": proj_points, "projected_bonus_tier": proj_tier,
        # C5: chi phí swap MINH BẠCH cho CẢ HAI lịch — KHÔNG trộn vào payout/delta (§5:
        # gross giữ gross; consumer muốn net thì tự trừ, có đủ số để trừ công bằng).
        "expected_swap_cost_vnd": round(n_swaps * fee_out, 1),
        "baseline_swap_cost_vnd": round(baseline_swaps * fee_out, 1),
    }
    if terms_active is not None:
        # B3: output NÓI RA số hạng nào sống/chết + lý do (câu hỏi thiết kế #2 của Cường:
        # "hiện không tính chi phí pin vì đang miễn phí tới 31/03/2029")
        solution["terms_active"] = terms_active

    return {
        "schema_version": "1.0.0", "solver": "shift_dp",
        "problem_digest": digest,
        "inputs_used": [{"view_id": f"shift_plan_input:{spi['driver_id']}",
                         "version": spi["view_version"], "freshness": spi["t_now"]}],
        "solution": solution,
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": confidence, "caveats": caveats, "infeasible_reason": None,
    }
