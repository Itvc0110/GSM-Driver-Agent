"""Projections — MỘT LUẬT diễn giải vòng đời advice, dùng chung UI và sim (ĐA-05, Cycle W).

Điều kiện duyệt của Cường (PENDING-REVIEW ĐA-05): *"UI và sim cùng đọc một projection —
một luật, một database"*. Vì thế mọi hàm ở đây là **pure function trên iterable dict**:

- UI/pipeline: `AdviceEventLog.events()` (SQLite rows) → cùng hàm;
- sim: `sim_events_to_lifecycle(result.events, run_id)` (RAM, không SQLite trong tick
  loop — chốt Cường) → cùng hàm.

Projection KHÔNG phải nguồn sự thật — xoá và replay từ events phải ra đúng kết quả
(test + mutation canh). Thứ tự xử lý deterministic: sort theo `(occurred_at, event_id)`,
dedupe theo `event_id` (bản đầu thắng — khớp INSERT OR IGNORE của store).
"""

from __future__ import annotations

from datetime import datetime, timedelta

# Trạng thái KẾT (không bị non-terminal về sau hạ cấp; terminal đến sau — theo thứ tự
# thời gian — được phép thay terminal trước, vd followed rồi superseded).
_TERMINAL = {"followed", "dismissed", "expired", "superseded", "suppressed"}


def _ts(iso: str) -> datetime:
    """Sort theo thời gian THẬT, không theo chuỗi — ba origin ghi ba múi giờ (pipeline
    UTC+00, sim/UI +07:00): '00:30+00:00' < '01:00+07:00' lexicographic nhưng SAU về
    thời gian thật (bug tự bắt bằng test mixed-timezone trước khi review).

    Lan can thứ hai: record naive (không offset) trộn với aware làm `sorted()` nổ
    `TypeError` — schema đã chặn ở `append`, nhưng projections cũng nhận list RAM CHƯA
    qua store (đường sim), nên vẫn phải fail-loud tại đây với thông điệp lần ra được."""
    t = datetime.fromisoformat(iso)
    if t.tzinfo is None:
        raise ValueError(
            f"occurred_at '{iso}' thiếu offset múi giờ — mọi timestamp lifecycle phải "
            f"timezone-aware (trộn naive/aware làm chết toàn bộ projection)")
    return t


def _ordered(events) -> list[dict]:
    seen: set[str] = set()
    out = []
    for e in sorted(events, key=lambda e: (_ts(e["occurred_at"]), e["event_id"])):
        if e["event_id"] in seen:
            continue
        seen.add(e["event_id"])
        out.append(e)
    return out


def decision_state(events) -> dict[str, dict]:
    """Máy trạng thái mỗi decision: decided → displayed → (followed | dismissed |
    expired | superseded); suppressed là nhánh hệ thống của decided.

    Trả {decision_id: {state, displayed, driver_id, run_id, topic, reason_code,
    first_at, last_at}}. Event lạc hậu/duplicate không phá state (replay idempotent).
    """
    st: dict[str, dict] = {}
    for e in _ordered(events):
        did = e["decision_id"]
        row = st.setdefault(did, {
            "state": None, "displayed": False, "driver_id": e["driver_id"],
            "run_id": e.get("run_id"), "topic": (e.get("payload") or {}).get("topic"),
            "reason_code": None, "first_at": e["occurred_at"], "last_at": e["occurred_at"],
        })
        row["last_at"] = e["occurred_at"]
        topic = (e.get("payload") or {}).get("topic")
        if row["topic"] is None and topic is not None:
            row["topic"] = topic
        et = e["event_type"]
        if et == "displayed":
            row["displayed"] = True
            if row["state"] not in _TERMINAL:
                row["state"] = "displayed"
        elif et == "decided":
            if row["state"] is None:
                row["state"] = "decided"
        else:  # terminal
            row["state"] = et
            if e.get("reason_code") is not None:
                row["reason_code"] = e["reason_code"]
    return st


def adherence_view(events) -> dict[tuple[str | None, str, str | None], dict]:
    """Đếm theo **(run_id, driver_id, topic)** với denominator = số DECISION đã đưa ra.

    `run_id` nằm trong khoá vì sim đặt `driver_id = str(actor_id)`: actor 0 của run A và
    actor 0 của run B là HAI người khác nhau ở hai vũ trụ. Review đối kháng đo được:
    gộp hai run (seed 1000 + 1001) làm 70 khoá tụt còn 55 — 15 tài xế bị trộn chéo, đúng
    use-case A/B mà ĐA-05 sinh ra để phục vụ. Đường UI/pipeline có `run_id=None` nên
    khoá vẫn ổn định.

    ## HAI ĐƠN VỊ, HAI TÊN — verdict Cường 2026-07-29

    Cùng dữ liệu cho hai con số khác nhau tuỳ đơn vị đếm (accept_lift seed 1000:
    **76,9%** theo decision vs **53,6%** theo event — kênh fire mỗi tick 2' nhưng
    decision gộp bucket 30'). Vì thế view trả CẢ HAI, tên đầy đủ, và **cấm khoá
    `adherence` trần** (test canh): số không rõ đơn vị là số sẽ bị đọc sai —
    đúng họ lỗi BUG-EVAL-ARGMAX.

    - `decided/followed/dismissed/suppressed`: đếm theo DECISION (mỗi decision_id một
      lần, kết cục = state cuối). Denominator = decided — khắc BRIDGE-3 vào luật.
    - `event_decided/event_followed`: đếm theo EVENT (mỗi lần advisor nói / mỗi lần theo).
    - `decision_adherence` = followed/decided · `event_adherence` =
      event_followed/event_decided; denominator 0 ⇒ **None** (không bịa 0%).
    """
    # X-3 (review batch 2): hàm lặp `events` HAI lần (decision_state + vòng event) —
    # generator bị tiêu ở lần đầu ⇒ event-count = 0 IM LẶNG (event_adherence=None đọc
    # thành "không có dữ liệu"). Materialize một lần, giữ đúng lời hứa "iterable".
    events = list(events)
    view: dict[tuple[str | None, str, str | None], dict] = {}

    def _row(key):
        return view.setdefault(key, {
            "decided": 0, "followed": 0, "dismissed": 0, "suppressed": 0,
            "event_decided": 0, "event_followed": 0,
        })

    for row in decision_state(events).values():
        agg = _row((row["run_id"], row["driver_id"], row["topic"]))
        if row["state"] == "suppressed":
            # ĐA-04: bị NÉN nghĩa là advisor KHÔNG NÓI — không thuộc mẫu số "đã nói bao
            # nhiêu lần, được nghe bao nhiêu". Đếm riêng để biết nhịp chặn bao nhiêu.
            agg["suppressed"] += 1
            continue
        agg["decided"] += 1
        if row["state"] in ("followed", "dismissed"):
            agg[row["state"]] += 1
    for e in _ordered(events):
        et = e["event_type"]
        if et not in ("decided", "followed"):
            continue
        agg = _row((e.get("run_id"), e["driver_id"],
                    (e.get("payload") or {}).get("topic")))
        agg[f"event_{et}"] += 1
    for agg in view.values():
        agg["decision_adherence"] = (agg["followed"] / agg["decided"]
                                     if agg["decided"] else None)
        agg["event_adherence"] = (agg["event_followed"] / agg["event_decided"]
                                  if agg["event_decided"] else None)
    return view


# ---------- sim adapter: events RAM → lifecycle envelope ----------

# kind sim → danh sách (event_type, actor) sinh ra từ MỘT event sim.
#
# ## Vì sao không map 1-1 theo kind (review đối kháng đo được, sai ở MỌI kênh)
#
# `followed` của sim KHÔNG nằm ở kind mà ở `detail["followed"]`, và mỗi kênh log theo
# một quy ước khác nhau:
#
# - `advice_given` luôn log, mang `followed` True/False; nhưng `advice_followed` CHỈ log
#   khi advice ĐỔI hành động (`world.py`, BRIDGE-3) ⇒ "nghe lời nhưng advice trùng bản
#   năng" không để lại event nào;
# - `advice_bonus_gate` mang `followed` và KHÔNG có event followed riêng nào;
# - `advice_shift_extend` / `advice_rest_window` CHỈ được log khi đã hoãn ca / đã dời
#   nghỉ ⇒ bản thân sự tồn tại của event nghĩa là ĐÃ THEO;
# - `standby_followed` chỉ có ở người đã theo; mẫu số nằm ở `standby_alloc.assigned_ids`.
#
# Map theo kind cho ra: shift_plan 2,0% · accept_lift 0,0% · shift_extend 0,0% ·
# positioning 100% — trong khi sự thật 52,2% · 53,6% · 100% · 48,8%.
# D-M3-01 (2026-07-30): `_ALWAYS_FOLLOWED` nay RỖNG. Trước đây nó chứa
# {"advice_shift_extend", "advice_rest_window"} với lý lẽ "sự tồn tại của event nghĩa là ĐÃ
# THEO" — lý lẽ đó đúng với hiện trạng LÚC ĐÓ (hai kênh chỉ log khi đã theo) nhưng nó khoá
# `decision_adherence` của hai kênh vào ĐÚNG HAI giá trị: 1,0 hoặc None. Tức tầng này BỎ QUA
# `detail["followed"]`, nên sửa bridge + world mà không sửa đây thì con số VẪN 100%.
#
# Đo được (`scripts/probe_adherence_truth.py`, 3 seed, coverage=all): `shift_extend` báo
# **1,000** trong khi sự thật từ coin là **0,473** theo đơn vị QUYẾT ĐỊNH (sai 2,1×). Nay cả hai kênh đã ghi event
# mang cờ `followed` ở cả hai nhánh (xem `world._NOT_FOLLOWED_KIND`) nên chúng đọc cờ như
# `advice_given`/`advice_bonus_gate`.
#
# ⚠ Giữ tên biến và để RỖNG thay vì xoá: nếu tương lai có kind nào thật sự chỉ tồn tại ở ca
# đã-theo thì chỗ khai báo phải nằm ở đây, kèm lý do đo được — không phải thêm âm thầm.
_ALWAYS_FOLLOWED: set[str] = set()
_FOLLOW_FLAG_KINDS = {"advice_given", "advice_bonus_gate",
                      "advice_shift_extend", "advice_rest_window"}
_DECIDED_KINDS = _ALWAYS_FOLLOWED | _FOLLOW_FLAG_KINDS
# F-S1 (review batch 2): `advice_followed` KHÔNG map — nó là marker BRIDGE-3 (chỉ log
# khi advice ĐỔI hành động) và LUÔN đi kèm `advice_given` cùng tick mang
# `followed=True` ⇒ map cả hai là đếm MỘT lần theo thành HAI (đo được: 655 thay vì
# 631 ⇒ event_adherence 54,2% thay vì 52,2%). `standby_followed` thì PHẢI map — kênh
# vị trí không có event decided mang cờ (mẫu số nằm ở standby_alloc.assigned_ids).
_TERMINAL_ONLY = {
    "standby_followed": ("followed", "driver"),
    "advice_suppressed": ("suppressed", "system"),
}


def _sim_steps(kind: str, detail: dict) -> list[tuple[str, str]]:
    """(event_type, actor) mà một event sim sinh ra — có thể 0, 1 hoặc 2 bước."""
    if kind in _DECIDED_KINDS:
        steps = [("decided", "advisor")]
        if kind in _ALWAYS_FOLLOWED or detail.get("followed"):
            steps.append(("followed", "driver"))
        return steps
    step = _TERMINAL_ONLY.get(kind)
    return [step] if step else []

# Epoch mặc định khi caller không đưa lịch thật của run — CHỈ để mã hoá t_min thành
# ISO so sánh được trong một run; ngày thật nằm ở config của run (xem advice_bridge._iso).
_SIM_EPOCH = "2026-01-01T00:00:00+07:00"


def _iso_from_t_min(t_min: float, epoch_iso: str) -> str:
    t0 = datetime.fromisoformat(epoch_iso)
    return (t0 + timedelta(minutes=float(t_min))).isoformat()


def _offer_events(e, run_id: str, epoch_iso: str) -> list[dict]:
    """`standby_alloc` mang `assigned_ids` ⇒ sinh event `decided` cho TỪNG người được
    gán (kể cả người sau đó không theo).

    Không có bước này thì mẫu số kênh vị trí chỉ gồm người ĐÃ theo ⇒ adherence luôn
    100% (đo được trước khi sửa: 36/36 trong khi sự thật 42/86)."""
    detail = e.detail or {}
    ids = detail.get("assigned_ids") or []
    iso = _iso_from_t_min(e.t_min, epoch_iso)
    out = []
    for aid in ids:
        did = detail.get("decision_ids", {}).get(str(aid))
        if not did:
            # X-4: silent-drop ở đây mở lại đúng lỗ F-1 (mẫu số positioning hụt im
            # lặng) từ hướng producer — fail-loud nhất quán với F-7.
            raise ValueError(
                f"standby_alloc t={e.t_min}: actor {aid} có trong assigned_ids nhưng "
                f"không có decision_id (decision_ids có: "
                f"{sorted(detail.get('decision_ids', {}))}) — producer lệch, mẫu số "
                f"positioning sẽ hụt im lặng nếu bỏ qua")
        out.append({
            "event_id": f"sim-{run_id}:{aid}:standby_offer:{e.t_min:g}",
            "decision_id": did, "display_id": None, "driver_id": str(aid),
            "run_id": run_id, "event_type": "decided", "reason_code": None,
            "occurred_at": iso, "observed_at": iso, "actor": "advisor",
            "origin": "sim", "source": "MOCK", "context_revision": None,
            "payload": {"topic": "positioning", "t_min": e.t_min,
                        "sim_kind": "standby_alloc", "target_cell": e.cell},
            "schema_version": "1.0.0",
        })
    return out


def sim_events_to_lifecycle(sim_events, run_id: str | None = None,
                            epoch_iso: str = _SIM_EPOCH) -> list[dict]:
    """Map sim events (RAM) → advice_lifecycle_event hợp lệ theo schema.

    `run_id` lấy từ **chính `Event.run_id`** (W4 đã stamp mọi event); tham số chỉ là
    fallback cho Event dựng tay. Truyền `run_id` MÂU THUẪN với event ⇒ ValueError:
    trước khi sửa, hàm ghi cột `run_id` theo tham số trong khi `decision_id` nhúng
    run_id thật ⇒ record TỰ MÂU THUẪN vẫn pass schema (rủi ro thật ở multiday, nơi mỗi
    ngày một run_id nhưng caller dễ gộp rồi truyền một giá trị).

    Deterministic thuần theo input (không uuid/wall-clock) — exact-repeat của sim giữ
    nguyên. Event trùng khoá tự nhiên (actor, kind, t_min) được đánh hậu tố theo thứ tự.
    """
    out: list[dict] = []
    used: dict[str, int] = {}
    for e in sim_events:
        detail = e.detail or {}
        ev_run = getattr(e, "run_id", "") or None
        if ev_run and run_id and ev_run != run_id:
            raise ValueError(
                f"run_id mâu thuẫn: Event mang '{ev_run}' nhưng caller truyền "
                f"'{run_id}' — bỏ tham số để dùng run_id của chính event")
        rid = ev_run or run_id
        if e.kind == "standby_alloc":
            out.extend(_offer_events(e, rid, epoch_iso))
            continue
        steps = _sim_steps(e.kind, detail)
        if not steps or "decision_id" not in detail:
            continue
        payload = {k: v for k, v in detail.items()
                   if k not in ("decision_id", "assigned_ids", "decision_ids")}
        payload["t_min"] = e.t_min
        payload["sim_kind"] = e.kind
        if "channel" in detail:
            payload["topic"] = detail["channel"]
        iso = _iso_from_t_min(e.t_min, epoch_iso)
        for event_type, actor in steps:
            base = f"sim-{rid}:{e.actor_id}:{e.kind}:{event_type}:{e.t_min:g}"
            n = used.get(base, 0)
            used[base] = n + 1
            out.append({
                "event_id": base if n == 0 else f"{base}-{n}",
                "decision_id": detail["decision_id"],
                "display_id": None,
                "driver_id": str(e.actor_id),
                "run_id": rid,
                "event_type": event_type,
                "reason_code": detail.get("reason"),
                "occurred_at": iso,
                "observed_at": iso,
                "actor": actor,
                "origin": "sim",
                "source": "MOCK",
                "context_revision": None,
                "payload": payload,
                "schema_version": "1.0.0",
            })
    return out
