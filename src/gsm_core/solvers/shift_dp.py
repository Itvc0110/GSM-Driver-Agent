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
}


def _required_rest(B: int, params: dict) -> int:
    """Số bucket nghỉ tối thiểu cho ca còn B bucket — theo PHÚT THẬT của bucket
    (AUDIT S2-6: bản cũ hardcode 30' → producer 60' bị tính nghỉ thiếu một nửa)."""
    bucket_min = int(params.get("bucket_min", 30))
    return min(B, (B * bucket_min // 240) * params["rest_min_per_4h"])


def _soc_cost(params: dict) -> int:
    """SOC band/bucket online — chuẩn theo 30', scale theo bucket_min (S2-6)."""
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
    R = _required_rest(B, params)
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

    for b in range(B - 1, -1, -1):
        buckets_left = B - b
        exp_trips = eo[b] * p_acc
        pph = _points_of_hour(policy, hrs[b])
        online_pay = exp_trips * ppo
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
                    # ONLINE (chỉ khi còn SOC, còn chỗ ngoài nghỉ bắt buộc, VÀ có kỳ vọng
                    # payout>0 — online lúc demand=0 vô ích, nhường END/REST)
                    if soc > 0 and rl < buckets_left and online_pay > 0:
                        v = online_pay + V[b + 1, nsoc_online, np_on, rl]
                        if v > best_v:
                            best_v, best_a = v, 0  # ONLINE
                    # REST (giảm rests_left nếu còn cần)
                    nrl = rl - 1 if rl > 0 else 0
                    v = 0.0 + V[b + 1, soc, pb, nrl]
                    if v > best_v:
                        best_v, best_a = v, 1  # REST
                    # SWAP (nạp đầy; tính như 1 bucket không kiếm tiền)
                    if rl < buckets_left:
                        v = 0.0 + V[b + 1, NS - 1, pb, rl]
                        if v > best_v:
                            best_v, best_a = v, 2  # SWAP
                    # END chỉ hợp lệ khi đã nghỉ đủ (rl==0)
                    if rl == 0:
                        v = bonus_at(pb * PBS)  # kết ca: chốt bonus hiện có (đã gate S2-3)
                        if v > best_v:
                            best_v, best_a = v, 3  # END
                    V[b, soc, pb, rl] = best_v
                    A[b, soc, pb, rl] = best_a

    # reconstruct
    schedule, soc, pb, rl = [], soc0, pts0, R
    proj_points, exp_payout = spi["points_now"], 0.0
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
        elif act == "END":
            ended = True
    exp_payout += bonus_at(proj_points)
    return schedule, exp_payout, proj_points


def _baseline_naive_rest(spi: dict, policy: PolicyBundle, params: dict,
                         demand_scale: float = 1.0) -> float:
    """Baseline: nghỉ R bucket ĐẦU CA (ngây thơ — mất demand sáng), swap khi cạn.
    DP đặt nghỉ vào demand thấp nhất → luôn ≥ baseline này."""
    B, eo, hrs, _ = _forecast_arrays(spi, params, demand_scale)
    if B <= 0:
        return 0.0
    eligible, _hr = _bonus_eligible(params, policy)
    R = _required_rest(B, params)
    ppo = _payout_per_order(policy, params["avg_dist_km"])
    pts, payout = spi["points_now"], 0.0
    soc = params["soc_bands"] - 1 if spi.get("soc_pct") is None else \
        min(params["soc_bands"] - 1, int(spi["soc_pct"] / (100.0 / params["soc_bands"])))
    for i in range(B):
        if i < R:  # nghỉ đầu ca
            continue
        if soc <= 0:
            soc = params["soc_bands"] - 1
            continue  # bucket này đi swap
        et = eo[i] * params["p_accept"]
        payout += et * ppo
        pts += int(round(et * _points_of_hour(policy, hrs[i])))
        soc -= _soc_cost(params)
    payout += policy.bonus_at(pts) if eligible else 0
    return payout


def solve(spi: dict, policy: PolicyBundle, params: dict | None = None) -> dict:
    """spi = shift_plan_input record. Trả solver_report record."""
    p = {**DEFAULT_PARAMS, **(params or {})}
    B = int(spi["buckets_remaining"])
    fc = spi["demand_forecast"]
    forecast_source = "historical_forecast" if spi["source"] in ("MOCK", "REAL") else "dp:fallback"
    confidence = 0.8 if len(fc) >= B and B > 0 else 0.5
    pv = f"policy_v:{policy.version}"

    schedule_acts, exp_payout, proj_points = _solve_dp(spi, policy, p)
    baseline = _baseline_naive_rest(spi, policy, p)
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
        _, ep2, _ = _solve_dp(spi, policy, p, demand_scale=1 - pct)
        bl2 = _baseline_naive_rest(spi, policy, p, demand_scale=1 - pct)
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

    return {
        "schema_version": "1.0.0", "solver": "shift_dp",
        "problem_digest": digest,
        "inputs_used": [{"view_id": f"shift_plan_input:{spi['driver_id']}",
                         "version": spi["view_version"], "freshness": spi["t_now"]}],
        "solution": {
            "schedule": schedule, "next_action": next_action,
            "expected_payout": round(exp_payout, 1), "baseline_payout": round(baseline, 1),
            "delta_payout": round(delta, 1),
            "projected_points": proj_points, "projected_bonus_tier": proj_tier,
        },
        "numbers": numbers, "sensitivity": sensitivity,
        "confidence": confidence, "caveats": caveats, "infeasible_reason": None,
    }
