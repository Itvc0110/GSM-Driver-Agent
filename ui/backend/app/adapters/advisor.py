"""Adapter advisor cho UI: dựng `bonus_gap_input` từ bảng mock → gọi solver S1 THẬT.

Nguyên tắc (CLAUDE §5): backend KHÔNG tự tính lời khuyên — mọi số đến từ
`gsm_core.solvers.bonus_feasibility.solve()` + `PolicyBundle`; adapter chỉ dựng
input từ data và dịch SolverReport → contract `ui/contracts/advice.json`.
Trạng thái IM LẶNG là kết quả hợp lệ (đã đạt mốc cao nhất / hết quỹ giờ).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import polars as pl

from gsm_core.advisor import verifier as V
from gsm_core.policy import PolicyBundle as CorePolicy
from gsm_core.rates import (shrunk_rate, bucket_of_hour, bucket_online_hours_estimated,
                            bucket_rate_samples, median_bucket_rates)
from gsm_core.solvers import bonus_feasibility
from gsm_core.vn_format import render_number_vn

from .mockdata import REPO_ROOT, _table, _stat_row

# Ca khai báo mặc định khi tài xế chưa khai (ASSUMPTION — UI cho sửa qua query param)
DEFAULT_SHIFT_END_MIN = 22 * 60


@lru_cache(maxsize=1)
def policy() -> CorePolicy:
    """Policy DUY NHẤT một nguồn: sim config → to_core_record — cùng đường với mockgen
    (adapter_sim.py L0 policy_bundle), nên UI/advisor/data không bao giờ lệch số policy."""
    from gsm_sim.config import Config
    from gsm_sim.policy import PolicyBundle as SimPolicy
    cfg = Config.load(str(REPO_ROOT / "configs" / "pilot_dongda.yaml"))
    rec = SimPolicy.from_config(cfg).to_core_record()
    rec.setdefault("version", str(cfg.get("meta.policy_bundle_version")))
    return CorePolicy.from_record(rec)


def _hour(iso: str) -> int:
    return int(iso[11:13])


def _min_of_day(iso: str) -> int:
    return _hour(iso) * 60 + int(iso[14:16])


def _trips_of(driver_id: str) -> pl.DataFrame:
    return _table("trips").filter(pl.col("driver_id") == driver_id)


def _points_until(trips: pl.DataFrame, date: str, now_min: int, pol: CorePolicy) -> int:
    day = trips.filter(pl.col("request_time").str.starts_with(date))
    pts = 0
    for iso in day["request_time"].to_list():
        t_min = _hour(iso) * 60 + int(iso[14:16])
        if t_min <= now_min:
            pts += pol.trip_points(_hour(iso))
    return pts


def _hist_rate(trips: pl.DataFrame, driver_id: str, date: str,
               pol: CorePolicy) -> tuple[dict, str]:
    """median **điểm / giờ online TRONG BUCKET** theo bucket, từ ≤7 ngày trước `date` (≥3 ngày mới tin).

    ⚠ `D-ADV-04` (2026-08-06) — **đây là đường SẢN PHẨM và nó từng SAI ĐƠN VỊ**: bản cũ chia
    điểm-của-bucket cho `online_time` **TOÀN NGÀY**, trong khi solver S1 (`bonus_feasibility._walk`)
    nhân con số đó với **TỪNG GIỜ** thuộc bucket ⇒ rate ước NON 2–5× ⇒ S1 phán *"không với tới mốc"*
    về mốc **với tới được**. Vì S1 là solver **duy nhất** đường này chạy (`B6-PARITY`), lỗi đó đập
    thẳng vào card của tài xế thật. Quy ước + estimator nay ở `gsm_core/rates.py` (MỘT nguồn).

    Bảng thật chỉ có TỔNG `online_time`, **không có** `go_online`/`go_offline`
    (`specs/real-data/data-contract-counterfactual.md`) ⇒ giờ-trong-bucket là **XẤP XỈ** từ span hoạt
    động; trả kèm `method` để card/nhật ký nói được đây là xấp xỉ, không phải số đo.

    Bỏ luôn `if p > 0` của bản cũ: ngày ĐÃ online trong bucket mà 0 điểm là **dữ liệu hợp lệ**
    (ADV-05) — loại nó khỏi mẫu làm median thiên LẠC QUAN, đúng chiều ngược với lỗi mẫu số nên hai
    lỗi từng bù trừ nhau và che nhau.
    """
    onl = _table("driver_online_hours_sap_id").filter(pl.col("driver_id") == driver_id)
    oh_by_date = {r["local_date"]: float(r["online_time"]) for r in onl.iter_rows(named=True)}
    days = sorted({iso[:10] for iso in trips["request_time"].to_list() if iso[:10] < date})[-7:]
    per_bucket: dict[str, list[float]] = {}
    method = "none"
    for d in days:
        oh = oh_by_date.get(d, 0.0)
        if oh <= 0:
            continue
        day = trips.filter(pl.col("request_time").str.starts_with(d))
        req = day["request_time"].to_list()
        if not req:
            continue
        comp = day["complete_time"].to_list() if "complete_time" in day.columns else req
        span = (min(_min_of_day(i) for i in req), max(_min_of_day(i) for i in comp))
        bucket_hours, m = bucket_online_hours_estimated(pol, oh, span)
        if not bucket_hours:
            continue
        method = m
        bp: dict[str, float] = {}
        for iso in req:
            b = bucket_of_hour(pol, _hour(iso))
            if b is not None:
                bp[b] = bp.get(b, 0.0) + pol.trip_points(_hour(iso))
        for b, rate in bucket_rate_samples(bp, bucket_hours).items():
            per_bucket.setdefault(b, []).append(rate)
    return median_bucket_rates(per_bucket), method


# ---------- ĐA-01: tỷ lệ nhận/hoàn thành KHÔNG được rò tương lai ----------

# Số quan sát giả của shrinkage. 20 ≈ **hơn một ngày** được chào đơn (median 15 offers/ngày trong
# snapshot) — đủ để một ngày xui không lật kết luận, nhỏ so với ~105 offers của cửa sổ 7 ngày nên
# tài xế có lịch sử vẫn được đánh giá theo chính họ. ASSUMPTION có lập luận; chưa hiệu chỉnh
# bằng dữ liệu thật (ĐA-01 yêu cầu recalibrate 30 seed — chưa làm).
SHRINK_PSEUDO_COUNTS = 20.0

# Cửa sổ lịch sử: 7 ngày TRƯỚC `date` — **đồng bộ với `_hist_rate`** cùng file, không tạo quy
# ước thứ hai (chính "nhiều quy ước cho một khái niệm" đẻ ra lỗi ở UPDATE-075/076).
RATE_WINDOW_DAYS = 7

_RATE_COLS = {
    "acceptance": ("accepted_count", "total_request_calculate_accept"),
    "completion": ("completed_count", "total_request_calculate_complete"),
}


@lru_cache(maxsize=64)
def _pooled_prior(kind: str, date: str) -> float:
    """Prior pooled TOÀN ĐỘI, tính trên các ngày **trước** `date`.

    Phải cắt `< date`: lấy cả ngày hiện tại thì vừa gỡ leak cá nhân xong lại rước leak tập thể.
    """
    k_col, n_col = _RATE_COLS[kind]
    df = _table("driver_statistic_daily").filter(pl.col("local_date") < date)
    n = float(df[n_col].sum() or 0)
    if n <= 0:
        # Ngày đầu tiên của snapshot: KHÔNG có gì để pool. Trả None-an-toàn là không được (caller
        # cần một số), nên dùng chính ngưỡng policy — bảo thủ, và KHÔNG phải 1.0.
        return float(policy().bonus_min_acceptance if kind == "acceptance"
                     else policy().bonus_min_completion)
    return float(df[k_col].sum() or 0) / n


def _rate_asof(driver_id: str, date: str, kind: str) -> float:
    """Tỷ lệ ước lượng **as-of đầu ngày `date`** — chỉ dùng dữ liệu ngày TRƯỚC.

    Thay cho bản cũ `stat.get("acceptance_rate", 1.0) or 1.0`, vốn:
      1. lấy aggregate CẢ NGÀY `date` ⇒ **rò tương lai** (9h sáng đã biết tỷ lệ cuối ngày);
      2. thiếu dữ liệu thì trả **1.0** ⇒ "hoàn hảo" ⇒ gate thưởng đi qua nhầm.
    """
    k_col, n_col = _RATE_COLS[kind]
    df = (_table("driver_statistic_daily")
          .filter((pl.col("driver_id") == driver_id) & (pl.col("local_date") < date))
          .sort("local_date").tail(RATE_WINDOW_DAYS))
    k, n = float(df[k_col].sum() or 0), float(df[n_col].sum() or 0)
    if k > n:  # dữ liệu hỏng → để estimator nổ, không tự chữa
        raise ValueError(f"{kind}: k={k} > n={n} cho {driver_id} trước {date}")
    return round(shrunk_rate(k, n, _pooled_prior(kind, date), SHRINK_PSEUDO_COUNTS), 4)


def build_gi(driver_id: str, date: str, now_min: int,
             shift_end_min: int = DEFAULT_SHIFT_END_MIN) -> dict:
    pol = policy()
    trips = _trips_of(driver_id)
    # (bỏ `_stat_row(driver_id, date)`: sau ĐA-01 không còn trường nào của build_gi đọc thống kê
    #  CỦA CHÍNH NGÀY ĐÓ — giữ lại chỉ mời gọi rò tương lai quay về)
    points_now = _points_until(trips, date, now_min, pol)
    hist_rate, rate_method = _hist_rate(trips, driver_id, date, pol)
    return {
        "schema_version": "1.1.0", "driver_id": driver_id,
        "t_now": f"{date}T{now_min // 60:02d}:{now_min % 60:02d}:00+07:00",
        "points_now": points_now,
        "next_tiers": [[pt, vnd] for pt, vnd in pol.day_bonus_tiers if pt > points_now],
        "historical_points_per_hour": hist_rate,
        # D-ADV-04: bảng thật không có mốc online ⇒ mẫu số là XẤP XỈ; nói ra thay vì im lặng
        "historical_rate_method": rate_method,
        "hours_budget_remaining": round(max(0.0, (shift_end_min - now_min) / 60.0), 3),
        # ĐA-01 (UPDATE-077): ước lượng **as-of**, chỉ từ ngày TRƯỚC + shrinkage về prior pooled.
        # Bản cũ lấy aggregate CẢ NGÀY `date` (rò tương lai) và fallback 1.0 (gate thưởng đi qua
        # nhầm). `stat` của chính ngày đó nay CHỈ còn dùng cho các trường không phải tỷ lệ.
        "acceptance_rate": _rate_asof(driver_id, date, "acceptance"),
        "completion_rate": _rate_asof(driver_id, date, "completion"),
        "policy_bundle_version": pol.version, "view_version": "1.0.0", "source": "MOCK",
    }


def _dataset_seed() -> int:
    """Seed CỦA DATASET đang đọc — một nguồn với `mockdata`, không hằng số.

    C2 §5.2 (UPDATE-076): advice trước đây khai cứng `seed: 0` trong khi data sinh bằng
    `seed_base = 7000`. Cùng một response nói hai điều mâu thuẫn về nguồn gốc của chính nó ⇒
    không truy vết được. Provenance phải đọc từ manifest như mọi envelope khác.
    """
    from app.adapters.mockdata import manifest
    return int(manifest().get("seed_base", 0))


def _num_source(raw: str) -> str:
    if raw.startswith("policy_v"):
        return "MOCK"          # policy bundle mock có nguồn research (sim-policy-bundle-v0)
    if raw.startswith("historical"):
        return "MOCK"          # lịch sử cá nhân từ data mock
    if raw.startswith("dp:"):
        return "ASSUMPTION"    # ước lượng lý thuyết khi thiếu lịch sử
    return "SOLVER"


def provenance(date: str, now_min: int) -> dict:
    """Ba field XUẤT XỨ mà contract `ui/contracts/advice.json` khai `required` + nhãn mock.

    Tách ra thành hàm public vì `routers/advice.py` **cũng** phải trả chúng: nhánh im lặng của
    endpoint (cadence nén) tự dựng dict riêng và **thiếu cả ba** — vi phạm contract có từ trước
    UPDATE-135, soi độc lập 2026-08-03 bắt được (`jsonschema` báo *"'scenario_id' is a required
    property"*), và **không cổng nào phủ**.

    Sửa bằng cách chia sẻ MỘT hàm thay vì chép ba chuỗi sang router — chép là dựng nguồn sự thật
    thứ hai, đúng họ `D-M3-17` mà cycle này đã trả giá hai lần.
    """
    return {"scenario_id": f"mock-realdata:{date}", "seed": _dataset_seed(),
            "data_mode": "mock-realdata", "is_mock": True, "generated_at_min": now_min}


def _advice_raw(driver_id: str, date: str, now_min: int,
                shift_end_min: int = DEFAULT_SHIFT_END_MIN) -> dict:
    """Dựng advice THÔ từ solver. KHÔNG gọi trực tiếp — dùng `advice()` (có guardrail)."""
    if not driver_id.startswith(("d-", "r-")):
        # policy S1 hiện là policy BIKE — không áp bừa cho đội car/premium (không bịa policy)
        return {**provenance(date, now_min),
                "silent": {"is_silent": True, "reason_code": "no_active_channel",
                           "message": "Trợ lý mới phủ đội bike (chính sách điểm/thưởng bike). "
                                      "Đội car/premium sẽ có khi đủ policy — không đoán số."},
                "items": []}
    gi = build_gi(driver_id, date, now_min, shift_end_min)
    report = bonus_feasibility.solve(gi, policy())
    sol = report["solution"]

    base = {
        "scenario_id": f"mock-realdata:{date}", "seed": _dataset_seed(),
        "data_mode": "mock-realdata", "is_mock": True,
        "generated_at_min": now_min,
        # E3.3: ngưỡng chính sách đi CÙNG payload — client đọc, không hardcode (họ D-M3-17)
        "policy_thresholds": _policy_thresholds(),
    }

    if sol.get("already_maxed"):
        # C2 §1b (UPDATE-076): `already_maxed` KHÔNG còn là nhánh sớm vô điều kiện.
        # Đủ điểm mốc cao nhất nhưng tỷ lệ dưới ngưỡng ⇒ chính sách trả **0đ**. Trả silent
        # "không có gì cần chỉnh" lúc đó là trấn an người đang mất tiền mà VẪN CÒN CỨU ĐƯỢC —
        # nguy hiểm hơn hiện số sai vì nó GIẤU cảnh báo. Solver đã kết luận đúng từ AUDIT A1,
        # chỉ là ba consumer không ai đọc `feasible`.
        if sol.get("feasible"):
            return {**base,
                    "silent": {"is_silent": True, "reason_code": "already_on_track",
                               "message": "Bạn đã đạt mốc thưởng ngày cao nhất — không có gì cần chỉnh. Giữ nhịp hiện tại."},
                    "items": []}
        cons = sol.get("constraints") or {}
        if not cons.get("ok_acceptance", True):
            reason_code = "acceptance_below_threshold"
            what = "tỷ lệ nhận của bạn đang dưới ngưỡng chính sách"
        else:
            reason_code = "completion_below_threshold"
            what = "tỷ lệ hoàn thành của bạn đang dưới ngưỡng chính sách"
        # KHÔNG kèm số tiền thưởng: mức thưởng đó chính là thứ đang có nguy cơ KHÔNG được trả.
        # Hiển thị nó ở đây sẽ thành lời hứa. `numbers` để rỗng ⇒ verifier V1 không có gì để
        # neo, nên câu chữ cũng phải không chứa số.
        item = {
            "advice_id": f"s1-{driver_id}-{date}-{now_min}",
            "solver": "S1", "kind": "info",
            "title": "Đủ điểm mốc cao nhất, nhưng thưởng đang có nguy cơ không được trả",
            "message": (f"Bạn đã đủ điểm mốc thưởng cao nhất hôm nay, nhưng {what}. "
                        "Nếu giữ nguyên đến cuối ngày thì phần thưởng ngày sẽ không được trả."),
            "confidence": report["confidence"],
            "reason_code": reason_code,
            "numbers": [], "caveat": " · ".join(report.get("caveats", [])),
        }
        return {**base, "silent": {"is_silent": False}, "items": [item]}

    numbers = [{"name": n, "value": v, "unit": u, "source": s} for n, v, u, s in [
        ("diem_con_thieu", sol["gap_points"], "điểm", "MOCK"),
        ("thuong_moc_ke", sol["tier_vnd"], "vnd", "MOCK"),
    ]]
    # AUDIT S1: hours_needed = None nghĩa là "không đạt được trong hôm nay" — không ép thành số
    if sol.get("hours_needed") is not None:
        numbers.append({"name": "gio_can_them", "value": sol["hours_needed"], "unit": "giờ",
                        "source": _num_source(report["numbers"][2]["source"])})
    if sol.get("trips_needed") is not None:
        numbers.append({"name": "cuoc_can_them", "value": sol["trips_needed"],
                        "unit": "cuốc", "source": "SOLVER"})
    caveat = " · ".join(report.get("caveats", []))

    # D-ADV-04: sau khi sửa mẫu số, advisor bớt bi quan ⇒ số lượt nói "còn với được" TĂNG, và rủi ro
    # MỚI là hứa hẹn ở dải sát biên (đo trên mock: nhóm mới-feasible mong manh hơn nhóm vốn feasible).
    # S1 ĐÃ tính sẵn `sensitivity` với cờ `flips_feasible` — adapter trước đây VỨT nó (cùng lỗi mà
    # `_cliff_item` đã phải đi sửa cho acceptance). Thêm MỘT CÂU cảnh báo, KHÔNG thêm số nào (verifier
    # V1 `check_bare_numbers` không có gì để bắn) và KHÔNG đổi `confidence`.
    if sol.get("feasible") and any(s.get("flips_feasible") for s in (report.get("sensitivity") or [])):
        canh_bao_sat_bien = ("mốc này sát biên: nếu khách vắng hơn thường lệ thì có thể không tới — "
                             "đừng dồn hết giờ vào nó")
        caveat = f"{caveat} · {canh_bao_sat_bien}" if caveat else canh_bao_sat_bien

    if sol["feasible"]:
        item = {
            "advice_id": f"s1-{driver_id}-{date}-{now_min}",
            "solver": "S1", "kind": "bonus_gap",
            "title": f"Còn với được mốc thưởng {_vn(sol['tier_vnd'], 'vnd')} hôm nay",
            "message": (f"Bạn thiếu {_vn(sol['gap_points'], 'points')} để chạm mốc kế "
                        f"(khoảng {_vn(sol['hours_needed'], 'hours')} chạy nữa, "
                        f"{_vn(sol['trips_needed'], 'trips')}). Quỹ giờ còn lại đủ."),
            "confidence": report["confidence"],
            "reason_code": "feasible_gap",
            "numbers": numbers, "caveat": caveat,
        }
        items = [item]
        cliff = _cliff_item(report, driver_id, date, now_min)   # E3.1 — phòng ngừa sát ngưỡng
        if cliff:
            items.append(cliff)
        return {**base, "silent": {"is_silent": False}, "items": items}

    # infeasible — nói thật lý do, không hứa hẹn
    constraints = sol.get("constraints", {})
    if not constraints.get("enough_hours", True):
        reason_code = "insufficient_budget_hours"
    elif not constraints.get("ok_acceptance", True):
        reason_code = "acceptance_below_threshold"
    else:
        reason_code = "completion_below_threshold"
    item = {
        "advice_id": f"s1-{driver_id}-{date}-{now_min}",
        "solver": "S1", "kind": "info",
        "title": "Mốc thưởng kế khó khả thi hôm nay",
        "message": (_infeasible_text(constraints)
                    + " Đừng cố quá — giữ tỷ lệ hoàn thành tốt cho ngày mai."),
        "confidence": report["confidence"],
        "reason_code": reason_code,
        "numbers": numbers, "caveat": caveat,
    }
    items = [item]
    cliff = _cliff_item(report, driver_id, date, now_min)       # E3.1 — phòng ngừa sát ngưỡng
    if cliff:
        items.append(cliff)
    return {**base, "silent": {"is_silent": False}, "items": items}


# ---------------------------------------------------------------------------
# R5-A (UPDATE-071): GUARDRAIL cho đường UI cards.
# Trước R5, `ui/backend/app/` KHÔNG gọi verifier ở bất kỳ đâu — nghĩa là mọi guardrail
# của pipeline C6 (V1 số trần, V2 hứa thu nhập/khuyên đơn, V3 ngôn ngữ lẫn) KHÔNG bảo vệ
# proactive cards, tức đường mà tài xế THỰC SỰ nhìn (DIRECTIVES §12). Nay: mỗi card phải
# qua verifier tầng 1; hỏng thì IM LẶNG (fail-closed, cùng triết lý FAILCLOSED-1).


def _vn(value, unit: str) -> str:
    """Render số theo locale VN — CÙNG hàm với pipeline (không tự format f-string)."""
    return render_number_vn(value, unit) if value is not None else ""


def _policy_thresholds() -> dict:
    """E3.3 (UPDATE-151 r06 THIẾU-6): expose ngưỡng chính sách cho client — UI thôi hardcode
    (họ D-M3-17: client tự đặt ngưỡng khác canonical source). Đi kèm MỌI payload advice."""
    p = policy()
    return {"bonus_min_acceptance": float(p.bonus_min_acceptance),
            "bonus_min_completion": float(p.bonus_min_completion),
            "source": f"policy_v:{p.version}"}


def _cliff_item(report: dict, driver_id: str, date: str, now_min: int) -> dict | None:
    """E3.1 (UPDATE-151 r06 THIẾU-1): cảnh báo PHÒNG NGỪA "tỷ lệ nhận sát ngưỡng thưởng".

    S1 ĐÃ TÍNH sẵn (`sensitivity` param `acceptance_cliff`, CLIFF_MARGIN=0.03) — bản cũ adapter
    chỉ đọc solution/numbers và VỨT toàn bộ sensitivity, nên loại cảnh báo giá trị nhất (phòng
    ngừa TRƯỚC khi rơi ngưỡng — sim gọi là advice_bonus_gate) không bao giờ tới tài xế.
    KHÔNG số tiền, KHÔNG hứa hẹn — chỉ nhắc ranh giới; note lấy từ solver (không tự đặt lời)."""
    cliff = next((s for s in report.get("sensitivity") or []
                  if s.get("param") == "acceptance_cliff"), None)
    if cliff is None:
        return None
    return {
        "advice_id": f"s1-{driver_id}-{date}-{now_min}-cliff",   # giữ namespace s1- (L4-07)
        "solver": "S1", "kind": "info",
        "title": "Tỷ lệ nhận đang sát ngưỡng thưởng",
        "message": str(cliff.get("note") or "Tỷ lệ nhận đang sát ngưỡng chính sách."),
        "confidence": report.get("confidence", 0.5),
        "reason_code": "acceptance_near_threshold",
        "numbers": [], "caveat": "cảnh báo phòng ngừa — không phải cam kết mức thưởng",
    }


def _infeasible_text(constraints: dict) -> str:
    """Lý do (KHÔNG lặp lại title — bài học giọng văn A3 LAYEROUT-6)."""
    if not constraints.get("enough_hours", True):
        return "Quỹ giờ còn lại của ca không đủ để kiếm thêm số điểm còn thiếu."
    if not constraints.get("ok_acceptance", True):
        return ("Tỷ lệ nhận đang dưới ngưỡng chính sách — dù đủ điểm thì thưởng "
                "vẫn không được trả.")
    if not constraints.get("ok_completion", True):
        return ("Tỷ lệ hoàn thành đang dưới ngưỡng chính sách — dù đủ điểm thì thưởng "
                "vẫn không được trả.")
    return "Điều kiện thưởng hôm nay chưa đạt."


_UNIT_KEY = {"điểm": "points", "vnd": "vnd", "giờ": "hours", "cuốc": "trips"}


def _verify_item(item: dict) -> list[str]:
    """Verifier tầng 1 trên nội dung card (title + message)."""
    rendered = [render_number_vn(n["value"], _UNIT_KEY.get(n.get("unit"), "count"))
                for n in item.get("numbers", []) if n.get("value") is not None]
    text = f"{item.get('title', '')} {item.get('message', '')}"
    return (V.check_bare_numbers(text, rendered)
            + V.check_blocklist(text, None))


def advice(driver_id: str, date: str, now_min: int,
           shift_end_min: int = DEFAULT_SHIFT_END_MIN) -> dict:
    """Advice CHO UI — có guardrail. Card nào không qua verifier thì KHÔNG được trả."""
    out = _advice_raw(driver_id, date, now_min, shift_end_min)
    errors: list[str] = []
    kept = []
    for it in out.get("items", []):
        errs = _verify_item(it)
        if errs:
            errors.extend(f"{it.get('advice_id')}: {e}" for e in errs)
        else:
            kept.append(it)
    if errors and not kept:
        return {**out, "items": [],
                "silent": {"is_silent": True, "reason_code": "verify_failed",
                           "message": "Hiện chưa có gợi ý nào đủ chắc chắn để đưa cho bạn. "
                                      "Trợ lý sẽ báo lại khi thông tin rõ ràng hơn."},
                "verify_errors": errors}
    if errors:
        return {**out, "items": kept, "verify_errors": errors}
    return out
