"""E10 — advisor cũng nhiễu: "+6.016đ còn lại bao nhiêu khi advisor mất λ?"

Khung đo theo `specs/simulation/e10-advisor-noisy.md` (spec là nguồn sự thật; UPDATE-108).
Lệnh được THÊM DẦN theo thứ tự thi công §8 — argparse chỉ nhận lệnh đã implement
(bài học `D-R12`: không quảng cáo nhánh không chạy).

    uv run python scripts/measure_e10.py preflight   # §5.5 — cổng z gộp trên B_oracle, 30 seed

Mọi số là MOCK (`configs/pilot_dongda.yaml`). Seeds đo 5000–5099 · tuning/probe 5100–5129
(disjoint — spec §5.3). Artifact prefix `41-e10-*`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with, aggregate_adherence, nominal_adherence
from gsm_sim.parallel import PairResult
from gsm_sim.runner import Config, run_once
from gsm_sim.sim_metrics import ADHERENCE_Z_MAX, adherence_audit, poisson_binomial_z

CONFIG = "configs/pilot_dongda.yaml"
OUT = Path("research/audit/2026-07-27-current-state")
MEASURE_SEEDS = list(range(5000, 5100))      # đo chính (n=100, tươi)
TUNING_SEEDS = list(range(5100, 5130))       # probe / preflight / tune k* (disjoint)


def arm_verdict(audits: list[dict], nominal: dict[str, float],
                seeds: list[int] | None = None) -> dict:
    """Verdict adherence cho MỘT arm — đi qua đường ống THẬT (`aggregate_adherence`).

    KHÔNG recompute cổng ở đây (T-046: hai đường tính là hai cơ hội lệch nhau). PairResult
    chỉ được đắp tối thiểu vì `aggregate_adherence` đọc mỗi `adherence_b`; nếu sau này nó
    đọc thêm trường khác, test T1 sẽ đỏ và người sửa phải đắp thêm — fail-loud đúng ý.

    ⚠ `by_channel_archetype` PHẢI đi xuyên qua nguyên vẹn — cổng thống kê sống bằng nó;
    rơi khoá này là cổng im lặng vĩnh viễn (bẫy BOOTSTRAP §5#4, test T1 canh).
    """
    # seed THẬT, không phải index: `aggregate_adherence` gắn "seed {pr.seed}" vào từng flag —
    # dùng index thì artifact chỉ ra sai seed và người đọc đi tìm nhầm run (soi 2026-07-31).
    sd = list(seeds) if seeds is not None else list(range(len(audits)))
    pairs = [PairResult(seed=sd[i], actor_id=-1, a={}, b={}, system_a={}, system_b={},
                        adherence_b=au)
             for i, au in enumerate(audits)]
    return aggregate_adherence(pairs, nominal=nominal)


def pooled_channel_z(audits: list[dict], nominal: dict[str, float],
                     channel: str) -> tuple[float, float, int, int]:
    """z Poisson-binomial GỘP mọi seed cho một kênh — trả (z, mu, followed, n).

    Cùng toán với cổng (`poisson_binomial_z` — một nguồn sự thật); chỉ phần cộng dồn
    làm tại chỗ vì `aggregate_adherence` không trả totals per-archetype ra ngoài.
    Preflight cần CON SỐ z (kể cả khi < 4) để ghi vào prereg, không chỉ cần cờ TREO.
    """
    fol, ps = 0, []
    for au in audits:
        for key, row in (au.get("by_channel_archetype") or {}).items():
            ch, _, arche = key.partition("|")
            p = nominal.get(arche)
            if ch != channel or p is None:
                continue
            fol += int(row.get("followed") or 0)
            ps += [p] * int(row.get("decided") or 0)
    if not ps:
        return (0.0, 0.0, 0, 0)
    return (poisson_binomial_z(fol, ps), sum(ps) / len(ps), fol, len(ps))


def cmd_preflight() -> None:
    """§5.5 — cổng z gộp CHƯA TỪNG chạy trên positioning: đo z thật trên B_oracle 30 seed.

    Dự đoán ĐĂNG KÝ TRƯỚC (spec §6.5#4): SẼ bắn (z 1-seed ước ~13 vì gap coin-vs-execution —
    pop im lặng `world.py:781-785`, bận tới hết ca, instinct ≠ WAIT). Số ước phải TỰ ĐO lại
    ở đây trước khi trích (bẫy "cơ chế đúng độ lớn sai").
    """
    base = Config.load(CONFIG)
    _assert_env_neutral(base)
    cfg = _cfg_with(base, enabled=True, actor_id=None,
                    channels=CHANNEL_LADDER["positioning"], coverage="all")
    nominal = nominal_adherence(base)
    audits, rows = [], []
    for i, s in enumerate(TUNING_SEEDS):
        r = run_once(cfg, s)
        au = adherence_audit(r)
        pos = (au.get("by_channel") or {}).get("positioning") or {}
        if not int(pos.get("decided") or 0):
            raise SystemExit(f"seed {s}: positioning decided=0 — coverage/cấu hình sai "
                             f"(bẫy `_cfg_with` default single), DỪNG")
        audits.append(au)
        rows.append({"seed": s,
                     "decided": int(pos["decided"]), "followed": int(pos.get("followed") or 0),
                     "decision_adherence": (round(pos["followed"] / pos["decided"], 4)
                                            if pos["decided"] else None),
                     "by_archetype": {k: v for k, v in
                                      (au.get("by_channel_archetype") or {}).items()
                                      if k.startswith("positioning|")},
                     "flags": au.get("flags") or []})
        if (i + 1) % 10 == 0:
            print(f"  preflight: {i + 1}/{len(TUNING_SEEDS)}", flush=True)

    agg = arm_verdict(audits, nominal, TUNING_SEEDS)
    z, mu, fol, n = pooled_channel_z(audits, nominal, "positioning")
    fired = abs(z) > ADHERENCE_Z_MAX
    artifact = {
        "what": "E10 preflight §5.5 — cổng z gộp trên arm B_oracle (positioning wait_only, "
                "coverage all), thước HIỆN HÀNH (followed = coin ∧ thi hành được)",
        "mock": True, "config": CONFIG, "seeds": TUNING_SEEDS,
        "prediction_preregistered": "SẼ bắn — z 1-seed ước ~13 (spec §5.5/§6.5#4; số ước, "
                                    "chính phép đo này là phép kiểm)",
        "z_pooled_positioning": round(z, 3), "null_mu": round(mu, 4),
        "followed_total": fol, "decided_total": n,
        "adherence_pooled": round(fol / n, 4) if n else None,
        "gate_threshold": ADHERENCE_Z_MAX, "gate_fired": fired,
        "verdict_pipeline": agg["verdict"], "flags_pipeline": agg["flags_per_seed"],
        "rows": rows,
    }
    out = OUT / "41-e10-preflight-n30.json"
    out.write_text(json.dumps(artifact, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"preflight -> {out}")
    print(f"z gộp positioning = {z:+.2f} (null mu={mu:.3f}, đo {fol}/{n} = {fol / n:.3f})")
    print("NHÁNH:", "🔴 |z| > 4 ⇒ STOP-0b: sửa THƯỚC (mini-cycle §5.5 — Cường đã duyệt "
                    "nhánh này 2026-07-31), KHÔNG nới ngưỡng" if fired
          else "✅ |z| ≤ 4 ⇒ giữ thước, ghi số vào prereg, đi tiếp bước 2")


# ===================== Bước 5 — probe / tune / histprior / prereg =====================
#
# Cả ba lệnh cùng tiêu thụ 30 run World A tuning (5100–5129, probe.wait_stats bật).
# Chạy World A ba lần là phí 2/3 máy ⇒ trích xuất per-seed được CACHE một lần
# (`41-e10-tuning-cache.json`); lệnh nào cần thì đọc, thiếu thì tự build.

TUNING_CACHE = OUT / "41-e10-tuning-cache.json"
PREREG = Path("specs/simulation/e10-prereg-locked.json")
T_GRID = [15.0, 20.0, 25.0, 30.0, 35.0]
T_DEAD = [45.0, 60.0]                 # LOẠI cấu trúc (impatience 20′×2 cụt streak ~40–44′)
K_GRID = [1, 2, 3, 4, 6]
NMIN_GRID = [1, 2, 3]


def _tuning_cache() -> dict:
    if TUNING_CACHE.exists():
        return json.loads(TUNING_CACHE.read_text(encoding="utf-8"))
    base = Config.load(CONFIG)
    _assert_env_neutral(base)
    cfg_a = _cfg_with(base, enabled=False, actor_id=None, channels=None)
    cfg_a.data["probe"] = {"wait_stats": True}   # observer log-only — fingerprint-checked (T18)
    per_seed, demand_field = {}, None
    for i, s in enumerate(TUNING_SEEDS):
        r = run_once(cfg_a, s)
        if demand_field is None:
            from gsm_sim.demand import expected_demand_field
            demand_field = {str(h): dict(cells) for h, cells in
                            expected_demand_field(r.grid, cfg_a).items()}
        per_seed[str(s)] = {
            "pickups": [[e.t_min, e.cell] for e in r.events if e.kind == "pickup"],
            "probe": [{"t": e.t_min, "cells": e.detail["cells"],
                       "streaks": e.detail["streaks"]}
                      for e in r.events if e.kind == "probe_wait_stats"],
        }
        if (i + 1) % 10 == 0:
            print(f"  tuning cache: {i + 1}/{len(TUNING_SEEDS)}", flush=True)
    cache = {"config": CONFIG, "seeds": TUNING_SEEDS, "bucket_min": 60,
             "start_min": int(base.get("time.start_min")),
             "trips_per_hour_est": float(base.get("advice.trips_per_hour_est")),
             "demand_field": demand_field, "per_seed": per_seed}
    TUNING_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"tuning cache -> {TUNING_CACHE}")
    return cache


def cmd_probe() -> None:
    """§4.7 control-run trên World A: phân phối W(c) · firing-rate theo (T, n_min) ·
    fallback khối · WAIT-persistence proxy · precision/recall vs λ (thước hậu-kiểm) ·
    phân phối đếm pickup (chốt dải min_n). Mọi quyết định ở đây là TRƯỚC-Δ — hợp lệ."""
    from gsm_sim.market_state import wait_fired_cells   # CÙNG luật với planner — 1 nguồn sự thật
    cache = _tuning_cache()
    b, start = cache["bucket_min"], cache["start_min"]
    tphe = cache["trips_per_hour_est"]
    dem_f = {int(h): c for h, c in cache["demand_field"].items()}

    med_all, med_n2 = [], []
    fire = {(t, n): 0 for t in T_GRID + T_DEAD for n in NMIN_GRID}
    n_ticks = 0
    idle_ge2, idle_tot = 0, 0
    persist_wait, persist_n = 0, 0
    prec_hit, prec_n, rec_hit, rec_n = 0, 0, 0, 0
    per_cell_counts: list[int] = []
    hourly_totals: dict[int, list[int]] = {}

    for s, row in cache["per_seed"].items():
        # phân phối đếm pickup per (bucket, cell) + per hour
        cnt: dict[int, dict[str, int]] = {}
        for t, c in row["pickups"]:
            cnt.setdefault(int(t // b), {}).setdefault(c, 0)
            cnt[int(t // b)][c] += 1
        for idx, cells in cnt.items():
            per_cell_counts += list(cells.values())
            hourly_totals.setdefault(idx, []).append(sum(cells.values()))

        probes = row["probe"]
        for j, pr in enumerate(probes):
            stats = {c: (int(v[0]), float(v[1])) for c, v in pr["cells"].items()}
            # CHỈ đếm tick VẬN HÀNH: probe tick từ t=0 mỗi 60′ nên 5 tick đầu (trước
            # start_min=300) mọi actor còn OFFLINE ⇒ stats rỗng. Đưa chúng vào mẫu số làm
            # firing-rate loãng ~21% — đúng họ lỗi "% câm thổi bởi bucket cấu trúc" mà spec
            # §3.3 đã vá cho estimator (soi 2026-07-31).
            if int(pr["t"]) < start:
                continue
            n_ticks += 1
            for c, (n, med) in stats.items():
                med_all.append(med)
                if n >= 2:
                    med_n2.append(med)
            for t in T_GRID + T_DEAD:
                for n_min in NMIN_GRID:
                    fire[(t, n_min)] += len(wait_fired_cells(stats, t, n_min))
            idle_tot += sum(n for n, _ in stats.values())
            idle_ge2 += sum(n for n, _ in stats.values() if n >= 2)
            # precision/recall của fired(T=30, n=2) so "ô dưới hoà vốn theo λ" (hậu-kiểm):
            # underfed(c) ⇔ n_idle ≥ 2 ∧ λ(c, hour) < n_idle × trips_per_hour_est
            hour = (int(pr["t"]) // 60) % 24
            lam_h = dem_f.get(hour, {})
            fired = wait_fired_cells(stats, 30.0, 2)
            underfed = {c for c, (n, _) in stats.items()
                        if n >= 2 and float(lam_h.get(c, 0.0)) < n * tphe}
            prec_hit += len(fired & underfed); prec_n += len(fired)
            rec_hit += len(fired & underfed); rec_n += len(underfed)
            # WAIT-persistence proxy: actor trong ô fired còn NGUYÊN ô + streak tăng ở tick sau
            if j + 1 < len(probes):
                nxt = probes[j + 1]["streaks"]
                for aid, (cell, streak) in pr["streaks"].items():
                    if cell in fired:
                        persist_n += 1
                        nx = nxt.get(aid)
                        if nx and nx[0] == cell and float(nx[1]) > float(streak):
                            persist_wait += 1

    import numpy as np
    pcs = np.asarray(per_cell_counts)
    firing = {f"T={t:g},n_min={n}": round(fire[(t, n)] / n_ticks, 3)
              for t in T_GRID + T_DEAD for n in NMIN_GRID}
    idle_share_ge2 = idle_ge2 / idle_tot if idle_tot else 0.0
    art = {
        "what": "E10 probe §4.7 — control-run World A (log-only), 30 seed tuning",
        "mock": True, "seeds": cache["seeds"], "n_probe_ticks": n_ticks,
        "W_median_per_cell_percentiles": {p: round(float(np.percentile(med_all, p)), 1)
                                          for p in (10, 25, 50, 75, 90, 99)} if med_all else {},
        "W_median_cells_n_ge2_percentiles": {p: round(float(np.percentile(med_n2, p)), 1)
                                             for p in (10, 25, 50, 75, 90, 99)} if med_n2 else {},
        "firing_cells_per_bucket": firing,
        "idle_share_in_cells_ge2": round(idle_share_ge2, 4),
        "block_fallback_active": bool(idle_share_ge2 < 0.20),
        "wait_persistence_proxy_T30": (round(persist_wait / persist_n, 4) if persist_n else None),
        "precision_fired_vs_underfed_T30": (round(prec_hit / prec_n, 4) if prec_n else None),
        "recall_fired_vs_underfed_T30": (round(rec_hit / rec_n, 4) if rec_n else None),
        "pickup_per_cell_bucket_percentiles": {p: float(np.percentile(pcs, p))
                                               for p in (50, 75, 90, 99)} if len(pcs) else {},
        "pickup_hourly_total_min": (int(min(min(v) for v in hourly_totals.values()))
                                    if hourly_totals else 0),
        "stop3_check_T30_nmin2": {"firing_rate": firing.get("T=30,n_min=2"),
                                  "verdict": ("CÂM CẤU TRÚC — STOP-3"
                                              if fire[(30.0, 2)] == 0 else "SỐNG")},
    }
    (OUT / "41-e10-probe-n30.json").write_text(json.dumps(art, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    print(f"probe -> {OUT / '41-e10-probe-n30.json'}")
    print(f"firing T=30/n=2: {firing.get('T=30,n_min=2')} ô/bucket · idle_share_ge2 = "
          f"{idle_share_ge2:.3f} · persistence = {art['wait_persistence_proxy_T30']}")


def cmd_tune() -> None:
    """§6.2 — k*: MAE dự báo one-step-ahead REALIZED-ONLY (0 oracle trong tiêu chí), shadow
    trên World A tuning. Dùng ĐÚNG class estimator (một nguồn sự thật, chống recompute lệch).
    min_pickups=1 khi tuning (đánh giá cửa sổ per se). Poisson deviance báo kèm MÔ TẢ."""
    import math
    from gsm_sim.demand_estimator import RealizedDemandEstimator
    from gsm_sim.world import Event
    cache = _tuning_cache()
    b, start = cache["bucket_min"], cache["start_min"]
    first_op = start // b
    core_cells = sorted({c for cells in cache["demand_field"].values() for c in cells})
    scores = {k: [] for k in K_GRID}
    dev = {k: [] for k in K_GRID}
    for s, row in cache["per_seed"].items():
        events = [Event(t_min=float(t), actor_id=-1, kind="pickup", cell=c)
                  for t, c in row["pickups"]]
        actual: dict[int, dict[str, int]] = {}
        for t, c in row["pickups"]:
            actual.setdefault(int(t // b), {}).setdefault(c, 0)
            actual[int(t // b)][c] += 1
        last_idx = 1440 // b
        for k in K_GRID:
            est = RealizedDemandEstimator(events, start_min=start, bucket_min=b,
                                          window_buckets=k, min_pickups=1)
            for idx in range(first_op + 1, last_idx):
                lam = est.estimate(idx)
                n_i = actual.get(idx, {})
                mae = sum(abs(lam.get(c, 0.0) - n_i.get(c, 0)) for c in core_cells)
                scores[k].append(mae)
                d = 0.0
                for c in core_cells:
                    n, l = n_i.get(c, 0), max(lam.get(c, 0.0), 1e-9)
                    d += 2 * ((n * math.log(n / l) if n else 0.0) - (n - l))
                dev[k].append(d)
    table = {k: round(sum(v) / len(v), 4) for k, v in scores.items()}
    k_star = min(K_GRID, key=lambda k: (table[k], k))   # tie ⇒ k nhỏ hơn
    art = {"what": "E10 tune §6.2 — k* realized-only (MAE one-step-ahead trên COUNTS)",
           "mock": True, "seeds": cache["seeds"], "criterion": "mae_one_step_realized_v1",
           "min_pickups_tuning": 1, "mae_by_k": table,
           "poisson_deviance_by_k_descriptive": {k: round(sum(v) / len(v), 2)
                                                 for k, v in dev.items()},
           "k_star": k_star}
    (OUT / "41-e10-tune-kstar.json").write_text(json.dumps(art, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    print(f"tune -> {OUT / '41-e10-tune-kstar.json'}")
    print("MAE theo k:", table, "=> k* =", k_star)


def cmd_histprior() -> None:
    """§5.1 — prior lịch sử cho arm B_hist: TRUNG BÌNH pickups per (hour, cell) của 30 run
    World A tuning. ⚠ CẤM tuyệt đối dùng cùng seed với seeds ĐO (5000–5099): cùng trace =
    biết trước đơn hôm nay = future leak xuyên thế giới. Deterministic, tính một lần."""
    cache = _tuning_cache()
    n_runs = len(cache["seeds"])
    acc: dict[int, dict[str, float]] = {}
    for s, row in cache["per_seed"].items():
        for t, c in row["pickups"]:
            hour = (int(t) // 60) % 24
            acc.setdefault(hour, {}).setdefault(c, 0.0)
            acc[hour][c] += 1.0
    prior = {h: {c: round(v / n_runs, 4) for c, v in sorted(cells.items())}
             for h, cells in sorted(acc.items())}
    art = {"what": "E10 hist prior — mean pickups per (hour, cell), 30 run World A tuning",
           "mock": True, "seeds_source": cache["seeds"],
           "forbidden_for_seeds": "5000-5099 (đo) — cùng seed = future leak xuyên thế giới",
           "unit": "pickups/hour (bucket 60′)", "prior": prior}
    (OUT / "41-e10-hist-prior.json").write_text(json.dumps(art, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
    print(f"histprior -> {OUT / '41-e10-hist-prior.json'} ({sum(len(v) for v in prior.values())} ô-giờ)")


def cmd_prereg() -> None:
    """§6.1 — sinh file khoá từ artifact probe/tune/preflight. Sau khi COMMIT file này:
    CẤM đổi k/T/n_min/min_pickups sau khi nhìn bất kỳ Δ nào; cấm nới z; cấm dời T headline."""
    probe = json.loads((OUT / "41-e10-probe-n30.json").read_text(encoding="utf-8"))
    tune = json.loads((OUT / "41-e10-tune-kstar.json").read_text(encoding="utf-8"))
    pref = json.loads((OUT / "41-e10-preflight-n30.json").read_text(encoding="utf-8"))
    locked = {
        "locked_at": "2026-07-31", "spec": "specs/simulation/e10-advisor-noisy.md",
        "k_star": tune["k_star"], "k_criterion": tune["criterion"], "k_grid": K_GRID,
        "T_headline": 30.0, "T_grid": T_GRID, "T_excluded_structural": T_DEAD,
        "n_min_headline": 2, "n_min_grid": NMIN_GRID,
        "min_pickups": 5, "min_pickups_grid": [1, 3, 5, 10],
        "block_fallback": {"active": probe["block_fallback_active"],
                           "rule": "idle_share_ge2 < 0.20 => grid_disk r=1",
                           "measured_idle_share_ge2": probe["idle_share_in_cells_ge2"]},
        "seeds_measure": "5000-5099", "seeds_tuning": "5100-5129",
        "preflight_z_positioning": pref["z_pooled_positioning"],
        "ruler_fix_applied": False,
        "firing_rate_T30_nmin2": probe["firing_cells_per_bucket"].get("T=30,n_min=2"),
        "stop3": probe["stop3_check_T30_nmin2"],
        "metric_chinh": "net_mean_all (mean payout MỌI actor); Δ_X(s)=B_X(s)−A(s); "
                        "arm-vs-arm = hiệu-của-hiệu per seed; bootstrap CI 5000, seed 12345",
        "expected_registered": "spec §6.5 — bảng kỳ vọng trung thực (in lại cạnh kết quả)",
        "pingpong_rule": {"threshold": 0.10, "window_buckets": 2,
                          "action": "cooldown 1 bucket theo ô-nguồn rồi đo lại"},
    }
    PREREG.write_text(json.dumps(locked, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"prereg -> {PREREG}")
    print("⚠ COMMIT file này TRƯỚC khi chạy worldA/arm — sau commit mọi tham số bị KHOÁ.")


# ============================ Bước 6 — worldA / arm / sens / diff ============================
#
# Quy tắc thi công (mỗi cái là một lỗi skeleton phản biện bắt — spec §5.6): PREREG lazy-load
# theo lệnh; guardrail truy cập CỨNG `g[k]` (KeyError nổ — `if k in g` là hidden fallback);
# GUARD_KEYS đủ 4 tầng KỂ CẢ starved_hours_n; JSON seed key string — normalize; worldA
# không có verdict; thứ tự STOP trong diff.

GUARD_KEYS = ("served_rate", "orders_completed", "total_payout_vnd", "expired_n",
              "wait_median_min", "gini_payout", "station_hhi", "supply_cell_hhi",
              "starved_hours_n")
SENS_SEEDS = list(range(5000, 5030))     # n=30 — CHỈ đọc CHIỀU, nhãn n_insufficient
OP_BUCKETS = list(range(6, 24))          # bucket vận hành sau bucket-5 (cold cấu trúc)


def _assert_env_neutral(cfg: "Config") -> None:
    """Spec §5.2 pre-register: mọi run E10 phải ở env NEUTRAL.

    Vì sao fail-loud chứ không ghi chú: `expected_demand_field` KHÔNG nhân `env.demand_factor`
    (`demand.py:86`) trong khi `generate_orders` CÓ (`:135-137`) ⇒ chạy trên mưa/event thì
    "oracle" của B_oracle hết là λ của generator, và mọi diag bias so λ̂ với λ đổi nghĩa ÂM
    THẦM. Các lệnh đo là invocation CLI rời nhau nên ai đổi config giữa chừng sẽ trộn hai thế
    giới mà không cổng nào bắn (soi 2026-07-31).
    """
    env = (cfg.data.get("environment") or {})
    scen = str(env.get("scenario", "dry_weekday"))
    fac = float(env.get("demand_factor", 1.0) or 1.0)
    if scen != "dry_weekday" or abs(fac - 1.0) > 1e-9:
        raise SystemExit(f"env KHÔNG neutral (scenario={scen!r}, demand_factor={fac}) — "
                         f"E10 đòi dry_weekday/1.0 (spec §5.2), DỪNG")


def _prereg() -> dict:
    if not PREREG.exists():
        raise SystemExit("CHƯA có e10-prereg-locked.json — chạy probe/tune/histprior/prereg "
                         "và COMMIT trước khi đo (spec §6.1)")
    return json.loads(PREREG.read_text(encoding="utf-8"))


def _hist_prior() -> dict:
    art = json.loads((OUT / "41-e10-hist-prior.json").read_text(encoding="utf-8"))
    return art["prior"]


def _arm_overrides(arm: str, locked: dict) -> dict:
    """Khoá advice per arm (§5.1). Trả dict để GHI vào artifact — không giấu cấu hình."""
    over: dict = {}
    if arm == "oracle":
        pass                                        # đường hiện hành, không đổi gì
    elif arm == "hist":
        over["market_demand_override"] = _hist_prior()
    elif arm == "real":
        over["market_demand_source"] = "realized"
        over["realized_demand"] = {"window_buckets": locked["k_star"],
                                   "min_pickups": locked["min_pickups"]}
    elif arm == "wait":
        over["market_demand_source"] = "realized"
        over["realized_demand"] = {"window_buckets": locked["k_star"],
                                   "min_pickups": locked["min_pickups"]}
        over["positioning_trigger"] = "wait"
        over["positioning_wait"] = {"threshold_min": locked["T_headline"],
                                    "min_idle": locked["n_min_headline"]}
    elif arm == "waitoracle":
        over["positioning_trigger"] = "wait"
        over["positioning_wait"] = {"threshold_min": locked["T_headline"],
                                    "min_idle": locked["n_min_headline"]}
    else:
        raise SystemExit(f"arm lạ: {arm}")
    return over


def _cfg_for(over: dict) -> "Config":
    import copy
    base = Config.load(CONFIG)
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data.setdefault("advice", {}).update(copy.deepcopy(over))
    _assert_env_neutral(c)
    return _cfg_with(c, enabled=True, actor_id=None,
                     channels=CHANNEL_LADDER["positioning"], coverage="all")


def _hourly_pickups(events) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in events:
        if e.kind == "pickup":
            h = str((int(e.t_min) // 60) % 24)
            out[h] = out.get(h, 0) + 1
    return out


def _row_common(r) -> dict:
    import numpy as np
    from gsm_sim.sim_metrics import system_guardrail
    g = system_guardrail(r)
    return {"net_mean_all": round(float(np.mean([a.payout_vnd for a in r.actors])), 2),
            **{k: g[k] for k in GUARD_KEYS},        # truy cập CỨNG — thiếu khoá là nổ
            "pickups_by_hour": _hourly_pickups(r.events)}


def cmd_worldA() -> None:
    """Arm A (advice off) × 100 seed đo — chạy MỘT lần, mọi arm diff với file này.
    DET-01: arm đối chứng cũng bị audit adherence (assert by_channel RỖNG, không giả định)."""
    _prereg()                                       # khoá phải tồn tại trước khi đo
    base = Config.load(CONFIG)
    _assert_env_neutral(base)
    cfg = _cfg_with(base, enabled=False, actor_id=None, channels=None)
    rows = []
    for i, s in enumerate(MEASURE_SEEDS):
        r = run_once(cfg, s)
        au = adherence_audit(r)
        if au.get("by_channel"):
            raise SystemExit(f"seed {s}: World A có adherence by_channel {au['by_channel']} "
                             f"— arm đối chứng KHÔNG SẠCH (DET-01), dừng")
        rows.append({"seed": s, **_row_common(r)})
        if (i + 1) % 10 == 0:
            print(f"  worldA: {i + 1}/{len(MEASURE_SEEDS)}", flush=True)
    art = {"what": "E10 World A (advice off), n=100 — KHÔNG có verdict (không phải arm B)",
           "mock": True, "config": CONFIG, "seeds": MEASURE_SEEDS, "rows": rows}
    (OUT / "41-e10-worldA-n100.json").write_text(json.dumps(art, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
    print(f"worldA -> {OUT / '41-e10-worldA-n100.json'}")


def _volume(r) -> dict:
    """Decomposition VOLUME §5.4 — B2 làm arm realized ít đích/nhiều ứng viên cơ học;
    thiếu bảng này thì "tin kém" và "khối lượng khác" bị kể thành một chuyện."""
    n_cand = n_asg = n_coin = n_exec = n_fired = n_into_fired = 0
    cold = cold_b5 = 0
    # ⚠ THỨ TỰ EVENT: planner log `standby_alloc` TRƯỚC `standby_planner` trong CÙNG tick
    # ⇒ phải buffer alloc rồi so với fired của ĐÚNG tick đó. Bản đầu so với fired của tick
    # TRƯỚC ⇒ false positive "veto thủng" ở seed 5019 (0 vi phạm thật khi ghép đúng — ô fired
    # bucket N−1 được làm đích ở bucket N là dynamics hợp lệ, không phải lỗ).
    pending_alloc: list = []
    for e in r.events:
        if e.kind == "standby_alloc":
            pending_alloc.append(e)
        elif e.kind == "standby_planner":
            n_cand += int(e.detail.get("n_candidates") or 0)
            n_asg += int(e.detail.get("n_assigned") or 0)
            n_coin += int(e.detail.get("n_follow") or 0)
            fired_now = set(e.detail.get("fired_cells") or [])
            n_fired += len(fired_now)
            n_into_fired += sum(int(al.detail.get("n_assigned") or 0)
                                for al in pending_alloc if al.cell in fired_now)
            pending_alloc = []
        elif e.kind == "standby_followed":
            n_exec += 1
        elif e.kind == "demand_est_cold":
            idx = int(e.detail.get("idx", -1))
            if idx in OP_BUCKETS:
                cold += 1
            elif idx == OP_BUCKETS[0] - 1:
                cold_b5 += 1        # bucket 5: cold CẤU TRÚC (n_buckets=0) — báo riêng §3.3
    return {"n_candidates": n_cand, "n_assigned": n_asg, "n_coin_true": n_coin,
            "n_executed": n_exec, "n_fired_cells": n_fired,
            "n_assigned_into_fired_cells": n_into_fired,   # kỳ vọng 0 (zone-veto)
            "cold_buckets_op": cold, "pct_cold_op": round(cold / len(OP_BUCKETS), 4),
            "cold_bucket5_structural": cold_b5}   # §3.3: KHÔNG tính vào %, báo riêng


def _run_arm(arm: str, seeds: list[int], locked: dict, tag: str) -> None:
    over = _arm_overrides(arm, locked)
    cfg = _cfg_for(over)
    nominal = nominal_adherence(Config.load(CONFIG))
    audits, rows = [], []
    for i, s in enumerate(seeds):
        r = run_once(cfg, s)
        au = adherence_audit(r)
        pos = (au.get("by_channel") or {}).get("positioning") or {}
        vol = _volume(r)
        if vol["n_assigned_into_fired_cells"]:
            raise SystemExit(f"seed {s}: {vol['n_assigned_into_fired_cells']} người bị gán "
                             f"VÀO ô fired — zone-veto thủng, dừng")
        if arm in ("oracle", "hist", "real") and not int(pos.get("decided") or 0):
            raise SystemExit(f"seed {s}: positioning decided=0 ở arm capacity-trigger — "
                             f"coverage/cấu hình sai, dừng")
        audits.append(au)
        rows.append({"seed": s, **_row_common(r),
                     "decided": int(pos.get("decided") or 0),
                     "followed": int(pos.get("followed") or 0),
                     "by_archetype": {k: v for k, v in
                                      (au.get("by_channel_archetype") or {}).items()
                                      if k.startswith("positioning|")},
                     "volume": vol, "flags": au.get("flags") or []})
        if (i + 1) % 10 == 0:
            print(f"  arm {arm}: {i + 1}/{len(seeds)}", flush=True)
    agg = arm_verdict(audits, nominal, seeds)
    n_zero = sum(1 for row in rows if row["decided"] == 0)
    if arm in ("wait", "waitoracle") and not sum(row["decided"] for row in rows):
        # Spec §5.2 + STOP-3: trigger câm HOÀN TOÀN ⇒ world B bit-identical A ⇒ Δ=0 mọi seed
        # ⇒ cmd_diff sẽ phân lớp "KQ-SỤP (MDE=0)" — báo "mất λ hết giá trị" trong khi sự thật
        # là "advisor không nói câu nào". Fail-loud tại đây, không để lọt xuống diff.
        raise SystemExit(f"arm {arm}: decided=0 POOLED trên {len(seeds)} seed — trigger CÂM "
                         f"cấu trúc (STOP-3), KHÔNG được báo Δ. Dừng.")
    if arm in ("wait", "waitoracle"):
        print(f"  arm {arm}: {n_zero}/{len(seeds)} seed có decided=0 (fire thưa là dự kiến)")
    z, mu, fol, n = pooled_channel_z(audits, nominal, "positioning")
    art = {"what": f"E10 arm B_{arm} (§5.1)", "mock": True, "config": CONFIG,
           "overrides": {k: (f"<hist prior {sum(len(v) for v in over[k].values())} ô-giờ>"
                             if k == "market_demand_override" else v)
                         for k, v in over.items()},
           "channels": "positioning (wait_only)", "coverage": "all", "seeds": seeds,
           "ruler_fix_applied": False,
           "verdict": agg["verdict"], "flags": agg["flags_per_seed"],
           "z_pooled_positioning": round(z, 3), "adherence_pooled": (round(fol / n, 4) if n else None),
           "decided_total": n, "n_seeds_decided_zero": n_zero, "rows": rows}
    out = OUT / f"41-e10-arm-{tag}.json"
    out.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"arm {arm} -> {out} · verdict: {agg['verdict']} · z={z:+.2f}")


def cmd_arm() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: measure_e10.py arm <oracle|hist|real|wait|waitoracle>")
    arm = sys.argv[2]
    locked = _prereg()
    seeds = SENS_SEEDS if arm == "waitoracle" else MEASURE_SEEDS
    tag = f"{arm}-n{len(seeds)}"
    _run_arm(arm, seeds, locked, tag)


def cmd_armvar() -> None:
    """Đo MỘT biến thể ở n=100 (khám phá, ngoài prereg — phải gắn nhãn khi báo).

        uv run python scripts/measure_e10.py armvar wait T=15

    Sinh ra vì G-SENS đo lại bằng thước mới (UPDATE-113) cho `wait-T15` **DƯƠNG SIG ở n=30**
    trong khi headline T=30 vẫn SỤP ⇒ giả thuyết "E10b sụp vì QUÁ HIẾM, không phải vì tín
    hiệu sai" cần n=100 để kiểm. Headline KHÔNG đổi (prereg khoá T=30).
    """
    if len(sys.argv) < 4:
        raise SystemExit("usage: measure_e10.py armvar <arm> <KEY=VAL> (vd: wait T=15)")
    arm, kv = sys.argv[2], sys.argv[3]
    key, _, val = kv.partition("=")
    locked = _prereg()
    over = _arm_overrides(arm, locked)
    if key == "T":
        over["positioning_wait"] = {"threshold_min": float(val),
                                    "min_idle": locked["n_min_headline"]}
    elif key == "k":
        over["realized_demand"] = {"window_buckets": int(val),
                                   "min_pickups": locked["min_pickups"]}
    else:
        raise SystemExit(f"key la: {key}")
    _run_arm_with_over(arm, over, MEASURE_SEEDS, f"{arm}-{key}{val}-n100-EXPLORATORY")


def _run_arm_with_over(arm, over, seeds, tag):
    """Như `_run_arm` nhưng nhận override dựng sẵn (dùng cho biến thể khám phá)."""
    import numpy as np
    cfg = _cfg_for(over)
    nominal = nominal_adherence(Config.load(CONFIG))
    audits, rows = [], []
    for i, s in enumerate(seeds):
        r = run_once(cfg, s)
        au = adherence_audit(r)
        pos = (au.get("by_channel") or {}).get("positioning") or {}
        rows.append({"seed": s, **_row_common(r),
                     "decided": int(pos.get("decided") or 0),
                     "followed": int(pos.get("followed") or 0),
                     "by_archetype": {k: v for k, v in
                                      (au.get("by_channel_archetype") or {}).items()
                                      if k.startswith("positioning|")},
                     "volume": _volume(r), "flags": au.get("flags") or []})
        audits.append(au)
        if (i + 1) % 20 == 0:
            print(f"  {tag}: {i + 1}/{len(seeds)}", flush=True)
    agg = arm_verdict(audits, nominal, seeds)
    z, mu, fol, n = pooled_channel_z(audits, nominal, "positioning")
    art = {"what": f"E10 biến thể KHÁM PHÁ {tag} — NGOÀI prereg, gắn nhãn khi báo",
           "mock": True, "exploratory": True, "overrides": over, "seeds": seeds,
           "verdict": agg["verdict"], "flags": agg["flags_per_seed"],
           "z_pooled_positioning": round(z, 3), "decided_total": n, "rows": rows}
    out = OUT / f"41-e10-{tag}.json"
    out.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{tag} -> {out} · verdict: {agg['verdict']} · z={z:+.2f}")


def cmd_sens() -> None:
    """G-SENS §6.4 — biến thể n=30 (5000–5029, World A đã có trong worldA file): CHỈ đọc
    CHIỀU, nhãn n_insufficient, cấm trích độ lớn (variant-vs-variant cần n≈105)."""
    locked = _prereg()
    variants: list[tuple[str, dict]] = []
    for k in locked["k_grid"]:
        if k != locked["k_star"]:
            variants.append((f"real-k{k}", {**_arm_overrides("real", locked),
                                            "realized_demand": {"window_buckets": k,
                                                                "min_pickups": locked["min_pickups"]}}))
    for t in locked["T_grid"]:
        if t != locked["T_headline"]:
            variants.append((f"wait-T{t:g}", {**_arm_overrides("wait", locked),
                                              "positioning_wait": {"threshold_min": t,
                                                                   "min_idle": locked["n_min_headline"]}}))
    for nm in locked["n_min_grid"]:
        if nm != locked["n_min_headline"]:
            variants.append((f"wait-nmin{nm}", {**_arm_overrides("wait", locked),
                                                "positioning_wait": {"threshold_min": locked["T_headline"],
                                                                     "min_idle": nm}}))
    for mp in locked["min_pickups_grid"]:
        if mp != locked["min_pickups"]:
            variants.append((f"real-minn{mp}", {**_arm_overrides("real", locked),
                                                "realized_demand": {"window_buckets": locked["k_star"],
                                                                    "min_pickups": mp}}))
    print(f"sens: {len(variants)} biến thể × {len(SENS_SEEDS)} seed")
    for name, over in variants:
        cfg = _cfg_for(over)
        rows = []
        for s in SENS_SEEDS:
            r = run_once(cfg, s)
            pos = (adherence_audit(r).get("by_channel") or {}).get("positioning") or {}
            rows.append({"seed": s, **{k: v for k, v in _row_common(r).items()
                                       if k != "pickups_by_hour"},
                         "decided": int(pos.get("decided") or 0)})
        art = {"what": f"E10 sensitivity {name} — n=30, CHỈ CHIỀU, n_insufficient",
               "mock": True, "overrides": {k: v for k, v in over.items()
                                           if k != "market_demand_override"},
               "seeds": SENS_SEEDS, "n_insufficient": True, "rows": rows}
        (OUT / f"41-e10-sens-{name}.json").write_text(
            json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  sens {name}: xong", flush=True)


def _load_rows(name: str) -> dict[int, dict]:
    art = json.loads((OUT / name).read_text(encoding="utf-8"))
    return {int(r["seed"]): r for r in art["rows"]}, art


def cmd_diff() -> None:
    """Thứ tự STOP (§5.6): verdict B_oracle → STOP-1 tái lập trần → verdict từng arm →
    phân lớp §6.3. Arm TREO chỉ báo verdict+flags, loại khỏi diff (không KeyError dây chuyền)."""
    import numpy as np
    from gsm_sim.parallel import bootstrap_ci
    a_rows, _ = _load_rows("41-e10-worldA-n100.json")

    def paired(rows_b: dict[int, dict], key: str = "net_mean_all") -> list[float]:
        seeds = sorted(set(a_rows) & set(rows_b))
        return [rows_b[s][key] - a_rows[s][key] for s in seeds]

    out: dict = {"what": "E10 diff — STOP chain + phân lớp §6.3", "mock": True,
                 "prereg": _prereg(), "arms": {}}
    arms = {}
    for arm, fname in [("oracle", "41-e10-arm-oracle-n100.json"),
                       ("hist", "41-e10-arm-hist-n100.json"),
                       ("real", "41-e10-arm-real-n100.json"),
                       ("wait", "41-e10-arm-wait-n100.json"),
                       ("waitoracle", "41-e10-arm-waitoracle-n30.json")]:
        p = OUT / fname
        if p.exists():
            rows, art = _load_rows(fname)
            arms[arm] = {"rows": rows, "verdict": art["verdict"], "flags": art["flags"],
                         "z": art["z_pooled_positioning"]}
    if "oracle" not in arms:
        raise SystemExit("thiếu arm oracle — chưa đo xong, diff vô nghĩa")

    # STOP-0b đã pass (preflight z=-2.39); STOP theo thứ tự:
    if arms["oracle"]["verdict"] != "OK":
        out["STOP"] = f"verdict B_oracle: {arms['oracle']['verdict']} — thước hỏng, DỪNG TẤT CẢ"
        print(out["STOP"])
        (OUT / "41-e10-diff.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
        return
    d_oracle = paired(arms["oracle"]["rows"])
    lo, hi = bootstrap_ci(d_oracle)
    mde = 1.96 * float(np.std(d_oracle, ddof=1) / np.sqrt(len(d_oracle)))
    out["stop1_delta_oracle"] = {"mean": round(float(np.mean(d_oracle)), 1),
                                 "ci": [round(lo, 1), round(hi, 1)], "n": len(d_oracle),
                                 "mde": round(mde, 1), "ref_update087": 6016}
    if lo <= 0 <= hi or hi < 0:
        # DỪNG THẬT, không chỉ ghi chú: mọi lớp §6.3 và mọi R đo TƯƠNG ĐỐI so với trần
        # Δ_oracle. Trần sụp ⇒ "còn R% của trần" vô nghĩa và "KQ-GIỮ" vô nghĩa. Phân lớp tiếp
        # trên trần đã sụp là sinh nhãn sai đúng lúc người đọc dễ tin nhất (soi 2026-07-31).
        if hi < 0:
            out["STOP"] = ("STOP-1: Δ_oracle ÂM — kết quả ĐẢO CHIỀU (báo đúng tên, KHÔNG gộp "
                           "vào 'không tái lập'). Dừng phân lớp.")
        else:
            verdict = ("tái lập UNDERPOWERED (CI chứa cả 0 lẫn +6.016, MDE>6.016)"
                       if (lo <= 6016 <= hi and mde > 6016) else "KHÔNG TÁI LẬP TRẦN")
            out["STOP"] = (f"STOP-1: CI(Δ_oracle) ∋ 0 — {verdict}; chạy lại bộ seed UPDATE-087 "
                           f"để tách 'seed tươi' khỏi 'code/config drift'. Dừng phân lớp.")
        out["arms_raw_no_classification"] = {a_: {"verdict": arms[a_]["verdict"], "z": arms[a_]["z"]}
                                             for a_ in arms}
        print(out["STOP"])
        (OUT / "41-e10-diff.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
        return

    for arm in ("hist", "real", "wait", "waitoracle"):
        if arm not in arms:
            continue
        rec: dict = {"verdict": arms[arm]["verdict"], "z": arms[arm]["z"],
                     "flags": arms[arm]["flags"][:5]}
        if arms[arm]["verdict"] != "OK":
            rec["note"] = "TREO — chỉ báo verdict, KHÔNG báo Δ (STOP-2)"
            out["arms"][arm] = rec
            continue
        d = paired(arms[arm]["rows"])
        lo_x, hi_x = bootstrap_ci(d)
        # Hiệu-của-hiệu ghép THEO SEED, không theo index: hai arm có thể khác bộ seed
        # (waitoracle n=30, hoặc arm chạy thiếu). Ghép index + min(len) sẽ trừ seed 5000 của
        # arm này cho seed 5031 của arm kia rồi truncate IM LẶNG (soi 2026-07-31).
        common = sorted(set(arms[arm]["rows"]) & set(arms["oracle"]["rows"]) & set(a_rows))
        dd = ([(arms[arm]["rows"][s]["net_mean_all"] - a_rows[s]["net_mean_all"])
               - (arms["oracle"]["rows"][s]["net_mean_all"] - a_rows[s]["net_mean_all"])
               for s in common] if arm != "waitoracle" else None)
        if arm == "waitoracle":
            # n=30 < MIN_SEEDS_FOR_VARIANT_COMPARISON=100. Spec §6.4: CHỈ đọc CHIỀU. Ghi
            # mean/CI vào artifact là mời người đọc trích độ lớn (soi 2026-07-31).
            sign = "dương" if lo_x > 0 else ("âm" if hi_x < 0 else "không phân biệt được với 0")
            rec["direction_only_n30"] = {"sign": sign, "n": len(d),
                                         "warning": "n_insufficient — CẤM trích độ lớn"}
            out["arms"][arm] = rec
            continue
        rec["delta_vs_A"] = {"mean": round(float(np.mean(d)), 1),
                             "ci": [round(lo_x, 1), round(hi_x, 1)], "n": len(d),
                             "mde": round(1.96 * float(np.std(d, ddof=1) / np.sqrt(len(d))), 1)}
        if dd is not None:
            lo_d, hi_d = bootstrap_ci(dd)
            # MDE của HIỆU-CỦA-HIỆU: thiếu nó thì KQ-GIỮ không tách được "không suy giảm"
            # khỏi "không đủ mạnh để phát hiện suy giảm" (spec §5.3 đòi MDE cho mọi CI ∋ 0).
            mde_d = 1.96 * float(np.std(dd, ddof=1) / np.sqrt(len(dd)))
            rec["delta_vs_oracle"] = {"mean": round(float(np.mean(dd)), 1),
                                      "ci": [round(lo_d, 1), round(hi_d, 1)],
                                      "n_paired_seeds": len(dd), "mde": round(mde_d, 1)}
            if lo_x > 0 and lo_d > 0:
                # Lớp thứ 5 — spec §6.3 tự nhận "4 lớp loại trừ nhau" nhưng KHÔNG vét cạn:
                # arm mất λ mà THẮNG oracle SIG rơi xuyên bảng. Đây là kết quả đáng soi nhất
                # (dấu hiệu thước hỏng / L2 leak) — không được để nó thành nhãn None.
                rec["lop"] = (f"KQ-VƯỢT-ORACLE (dd=+{np.mean(dd):.0f}, CI trọn dương) — KHÔNG "
                              f"có trong bảng §6.3; soi thước/L2 TRƯỚC khi báo")
            elif lo_x > 0 and lo_d <= 0 <= hi_d:
                rec["lop"] = (f"KQ-GIỮ (MDE_dd={round(mde_d, 1)}) — kèm caveat L1+L2 nguyên "
                              f"văn, phát biểu YẾU về ngoài đời")
            elif lo_x > 0 and hi_d < 0:
                r_ratio = float(np.mean(d)) / float(np.mean(d_oracle)) if np.mean(d_oracle) else None
                rec["lop"] = f"KQ-CÒN-MỘT-PHẦN (R≈{r_ratio:.0%} — mô tả phụ)" if r_ratio else "KQ-CÒN-MỘT-PHẦN"
            elif lo_x <= 0 <= hi_x:
                rec["lop"] = f"KQ-SỤP (MDE={rec['delta_vs_A']['mde']})"
            elif hi_x < 0:
                rec["lop"] = "KQ-ÂM (kết quả hợp lệ, không phải bug — §1)"
        else:
            rec["note_n30"] = "chẩn đoán CHIỀU, n=30 — cấm trích độ lớn"
        vols = [r["volume"] for r in arms[arm]["rows"].values()]
        rec["volume_mean"] = {k: round(float(np.mean([v[k] for v in vols])), 2)
                              for k in vols[0]} if vols else {}
        out["arms"][arm] = rec

    # G-GUARD: tầng hệ thống nào suy giảm SIG (hiệu ghép cặp, hướng xấu)
    worse_dir = {"served_rate": -1, "orders_completed": -1, "total_payout_vnd": -1,
                 "expired_n": +1, "wait_median_min": +1, "gini_payout": +1,
                 "station_hhi": +1, "supply_cell_hhi": +1, "starved_hours_n": +1}
    for arm in out["arms"]:
        if "delta_vs_A" not in out["arms"][arm]:
            continue
        bad = []
        for k, sign in worse_dir.items():
            dk = paired(arms[arm]["rows"], key=k)
            lo_k, hi_k = bootstrap_ci(dk)
            if (sign > 0 and lo_k > 0) or (sign < 0 and hi_k < 0):
                bad.append({k: [round(lo_k, 4), round(hi_k, 4)]})
        out["arms"][arm]["g_guard_sig_worse"] = bad
        if bad:
            out["arms"][arm]["g_guard_label"] = "đạt cá nhân, HẠI HỆ THỐNG — đọc trước khi khen Δ"
    # G-HERD (đăng ký trước): supply_cell_hhi(B_real) ≥ B_oracle?
    if "real" in arms and arms.get("real", {}).get("verdict") == "OK":
        hhi_real = [r["supply_cell_hhi"] for r in arms["real"]["rows"].values()]
        hhi_or = [r["supply_cell_hhi"] for r in arms["oracle"]["rows"].values()]
        out["g_herd_hhi"] = {"real_mean": round(float(np.mean(hhi_real)), 5),
                             "oracle_mean": round(float(np.mean(hhi_or)), 5),
                             "note": "corr B1 đọc từ lệnh bias; chỉ được nói 'nhất quán với "
                                     "censoring', CẤM 'xác nhận herding'"}
    (OUT / "41-e10-diff.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"diff -> {OUT / '41-e10-diff.json'}")
    for arm, rec in out["arms"].items():
        lab = (rec.get("lop") or rec.get("note")
               or (f"CHIỀU {rec['direction_only_n30']['sign']} (n=30, cấm trích độ lớn)"
                   if "direction_only_n30" in rec else "KHÔNG PHÂN LỚP ĐƯỢC — đọc artifact"))
        print(f"  {arm}: {lab} · Δ={rec.get('delta_vs_A', {}).get('mean')} "
              f"CI={rec.get('delta_vs_A', {}).get('ci')}")


def cmd_bias() -> None:
    """§3.6 — B1..B5 + diagnostic L2, trên 3 seed đo đầu (5000–5002), 3 thế giới (A /
    B_oracle / arm đích). λ CHỈ làm thước chấm hậu-kiểm — đặc quyền của sim, sống ở script.

    Lệch khai báo so spec (ghi cả vào artifact): s_c của B1 dùng **n_idle per-cell từ probe
    log-only** cho CẢ BA thế giới (một định nghĩa — null baseline so được), thay vì
    supply_eff của demand_est (chỉ arm realized có). supply_eff vẫn được đối chiếu ở arm
    realized (`b1_supply_crosscheck`)."""
    import math
    import numpy as np
    from scipy.stats import pearsonr, spearmanr

    arm = sys.argv[2] if len(sys.argv) > 2 else "real"
    locked = _prereg()
    seeds = MEASURE_SEEDS[:3]
    b = 60
    base = Config.load(CONFIG)
    from gsm_sim.demand import expected_demand_field

    def _run_with_probe(over: dict | None, enabled: bool, s: int):
        import copy as _copy
        c = Config(_copy.deepcopy(base.data), base.root_dir)
        if over:
            c.data.setdefault("advice", {}).update(_copy.deepcopy(over))
        c.data["probe"] = {"wait_stats": True}
        cfg = _cfg_with(c, enabled=enabled, actor_id=None,
                        channels=CHANNEL_LADDER["positioning"] if enabled else None,
                        coverage="all")
        return run_once(cfg, s)

    lam_field = None
    worlds = {"A": (None, False), "oracle": ({}, True),
              arm: (_arm_overrides(arm, locked), True)}
    ev: dict[str, list] = {}
    orders0 = None
    for name, (over, en) in worlds.items():
        ev[name] = []
        for s in seeds:
            r = _run_with_probe(over, en, s)
            ev[name].append(r.events)
            if lam_field is None:
                lam_field = expected_demand_field(r.grid, r.config)
            if name == "A" and orders0 is None:
                orders0 = {o.order_id: float(o.t_min) for o in r.orders}
    core = sorted({c for cells in lam_field.values() for c in cells})

    def _shares(d: dict[str, float]) -> dict[str, float]:
        t = sum(d.values()) or 1.0
        return {c: d.get(c, 0.0) / t for c in core}

    def _b1_pairs(events_list):
        pairs = []
        for events in events_list:
            pick: dict[int, dict[str, int]] = {}
            idle: dict[int, dict[str, int]] = {}
            for e in events:
                if e.kind == "pickup":
                    pick.setdefault(int(e.t_min // b), {}).setdefault(e.cell, 0)
                    pick[int(e.t_min // b)][e.cell] += 1
                elif e.kind == "probe_wait_stats":
                    idle[int(e.t_min // b)] = {c: int(v[0])
                                               for c, v in e.detail["cells"].items()}
            for idx in OP_BUCKETS:
                if idx not in pick or idx not in idle:
                    continue
                hour = (idx * b // 60) % 24
                pn = _shares({c: float(n) for c, n in pick[idx].items()})
                pl = _shares(lam_field.get(hour, {}))
                sc = _shares({c: float(n) for c, n in idle[idx].items()})
                for c in core:
                    pairs.append((pn[c] - pl[c], sc[c]))
        e_, s_ = zip(*pairs)
        return {"pearson": round(float(pearsonr(e_, s_)[0]), 4),
                "spearman": round(float(spearmanr(e_, s_)[0]), 4), "n_pairs": len(pairs)}

    art: dict = {"what": f"E10 bias §3.6 — arm {arm} vs null A/B_oracle, 3 seed 5000–5002",
                 "mock": True, "seeds": seeds, "arm": arm,
                 "b1_corr_residual_supply": {name: _b1_pairs(ev[name]) for name in ev},
                 "b1_wording": "chỉ được nói 'nhất quán với censoring' — CẤM 'xác nhận herding'"}

    # B2/B3/B4 — cần λ̂ per bucket: đọc từ event demand_est của arm realized
    if any(e.kind == "demand_est" for events in ev[arm] for e in events):
        r2, tv_now, tv_lag, ov_lam, ov_self = [], [], [], [], []
        crosscheck_ok = True
        k = locked["k_star"]
        for events in ev[arm]:
            idle = {int(e.t_min // b): {c: int(v[0]) for c, v in e.detail["cells"].items()}
                    for e in events if e.kind == "probe_wait_stats"}
            prev_lam = None
            for e in events:
                if e.kind != "demand_est":
                    continue
                idx = int(e.detail["idx"])
                hour = (idx * b // 60) % 24
                lam_hat = {c: float(v[1]) for c, v in e.detail["cells"].items()}
                sup_logged = {c: v[0] for c, v in e.detail["cells"].items()}
                idle_b = idle.get(idx, {})
                for c, s_log in sup_logged.items():
                    if s_log is not None and idle_b and c in idle_b and s_log < idle_b[c]:
                        crosscheck_ok = False     # supply_eff ≥ idle-only phải đúng
                lam_h = lam_field.get(hour, {})
                r2.append(sum(lam_hat.values()) / (sum(lam_h.values()) or 1.0))
                ph, pl = _shares(lam_hat), _shares(lam_h)
                tv_now.append(0.5 * sum(abs(ph[c] - pl[c]) for c in core))
                lag_h = {}
                for hh in range(max(hour - k, 5), hour):
                    for c, v in lam_field.get(hh, {}).items():
                        lag_h[c] = lag_h.get(c, 0.0) + v / k
                plag = _shares(lag_h)
                tv_lag.append(0.5 * sum(abs(ph[c] - plag[c]) for c in core))
                top = lambda d: set(sorted(d, key=lambda c: (-d.get(c, 0.0), c))[:10])
                ov_lam.append(len(top(lam_hat) & top(lam_h)) / 10.0)
                if prev_lam is not None:
                    ov_self.append(len(top(lam_hat) & top(prev_lam)) / 10.0)
                prev_lam = lam_hat
        art["b2_level_ratio_Rb"] = {"mean": round(float(np.mean(r2)), 4),
                                    "p10": round(float(np.percentile(r2, 10)), 4),
                                    "p90": round(float(np.percentile(r2, 90)), 4)}
        art["b3_lag_tv"] = {"tv_vs_lambda_now": round(float(np.mean(tv_now)), 4),
                            "tv_vs_lambda_lagged_window": round(float(np.mean(tv_lag)), 4),
                            "doc": "tv_lag < tv_now ⇒ λ̂ giống quá khứ hơn hiện tại = trailing lag"}
        art["b4_rank_overlap10"] = {"vs_lambda_mean": round(float(np.mean(ov_lam)), 4),
                                    "self_stability_mean": (round(float(np.mean(ov_self)), 4)
                                                            if ov_self else None)}
        art["b1_supply_crosscheck"] = ("OK — supply_eff(demand_est) ≥ idle-only(probe) mọi ô"
                                       if crosscheck_ok else "🔴 LỆCH — xem lại đường log")

    # B5 — attribution thời điểm ĐÓN (1 seed World A): t_pickup − t_order
    delays = [e.t_min - orders0[e.detail["order_id"]]
              for e in ev["A"][0] if e.kind == "pickup" and e.detail.get("order_id") in orders0]
    art["b5_pickup_delay_min"] = {p: round(float(np.percentile(delays, p)), 2)
                                  for p in (50, 75, 90, 99)}
    # Diagnostic L2 (kèm mọi KQ-GIỮ): đội xe World A đã "giải mã" λ tới đâu
    sp = []
    for events in ev["A"]:
        byh: dict[int, dict[str, int]] = {}
        for e in events:
            if e.kind == "pickup":
                byh.setdefault((int(e.t_min) // 60) % 24, {}).setdefault(e.cell, 0)
                byh[(int(e.t_min) // 60) % 24][e.cell] += 1
        for hour, cnt in byh.items():
            lam_h = lam_field.get(hour, {})
            if len(cnt) < 5:
                continue
            a = [_shares({c: float(n) for c, n in cnt.items()})[c] for c in core]
            l = [_shares(lam_h)[c] for c in core]
            sp.append(float(spearmanr(a, l)[0]))
    art["l2_spearman_pickupA_vs_lambda_per_hour"] = {"mean": round(float(np.mean(sp)), 4),
                                                     "n_hours": len(sp)}
    out = OUT / f"41-e10-bias-{arm}.json"
    out.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"bias {arm} -> {out}")
    print("B1 corr:", art["b1_corr_residual_supply"])


COMMANDS = {"preflight": cmd_preflight, "probe": cmd_probe, "tune": cmd_tune,
            "armvar": cmd_armvar,
            "histprior": cmd_histprior, "prereg": cmd_prereg,
            "worldA": cmd_worldA, "arm": cmd_arm, "sens": cmd_sens, "diff": cmd_diff,
            "bias": cmd_bias}


if __name__ == "__main__":
    # console Windows mặc định cp1252 — không in nổi tiếng Việt (đã crash 1 lần sau khi
    # artifact ghi xong; đo không mất, chỉ mất dòng tóm tắt)
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit(f"usage: measure_e10.py {{{'|'.join(sorted(COMMANDS))}}} "
                         f"(lệnh khác thêm dần theo spec §8)")
    COMMANDS[sys.argv[1]]()
