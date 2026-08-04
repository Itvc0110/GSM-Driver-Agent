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

from gsm_core.lifecycle.advice_topics import classify

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
    """Sắp theo (occurred_at, observed_at, event_id).

    L3-03 (phản biện 2026-07-31, reproduce qua chính hàm này): `occurred_at` của đường SẢN
    PHẨM dựng từ `at_min` mà client gửi — HẰNG SỐ theo loại card (`cards.js KIND_HOURS`) ⇒
    mọi hành động cùng ngày trên cùng card **hoà** ⇒ thế hoà quyết định tất cả. Tie-break cũ
    là `event_id` = `ui-{aid}-{action}-{giây}`, so chuỗi ⇒ `"…-dismissed-…" < "…-followed-…"`
    ⇒ `followed` LUÔN sort sau ⇒ LUÔN thắng, bất kể tài xế bấm gì sau cùng: **sản phẩm không
    ghi nhận được việc đổi ý**. `observed_at` là thời điểm SERVER nhận (`datetime.now(utc)`
    lúc POST) — đúng thứ tự nhân quả thật, và nó có ở mọi event của cả hai đường (sim đặt
    observed_at khi export). `event_id` giữ làm chốt cuối để thứ tự vẫn tất định.
    """
    seen: set[str] = set()
    out = []
    for e in sorted(events, key=lambda e: (_ts(e["occurred_at"]),
                                           str(e.get("observed_at") or ""),
                                           e["event_id"])):
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

    ## KHUYÊN MỀM KHÔNG CÓ MẶT Ở ĐÂY (quyết định Cường 2026-08-03)

    Topic trong `advice_topics.SOFT_TOPICS` (thời tiết, gợi ý nghỉ, giao thông) bị **loại hoàn
    toàn** khỏi view — không phải trả `None`, mà **vắng khoá**. Đo mức nghe lời của lời khuyên
    sức khoẻ là biến sức khoẻ thành chỉ tiêu tối ưu, trái §1.2b; xem
    `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`.

    Vì sao *vắng khoá* chứ không phải *`None`*: `None` là tín hiệu **"mẫu số 0 — có thể có bug"**
    (đúng thứ `D-M3-01`/`L4-01` đã dùng để tìm ra thước hỏng). Nếu khuyên mềm trả `None` thì nó
    lẫn vào đúng tín hiệu báo lỗi ấy, và người sau sẽ đi "sửa" một ranh giới đang hoạt động đúng.
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

    states = decision_state(events)
    # Quyết định nào bị coi là KHUYÊN MỀM — dùng cho CẢ HAI vòng bên dưới.
    #
    # Vì sao không dựa vào `payload["topic"]` của từng event: `sim_events_to_lifecycle` chỉ đặt
    # `topic` **khi** `detail` có `channel` (`:344`), nên một event của cùng quyết định vẫn có thể
    # thiếu `topic` ⇒ `is_soft(None)` = False ⇒ lọt. Neo vào quyết định thì ranh giới không phụ
    # thuộc việc mọi producer có nhớ điền field hay không — bài học `D-M3-15`.
    #
    # 🔴 Quét CẢ event, không chỉ topic đã giải của `decision_state` (soi độc lập 2026-08-03).
    # `decision_state` giải `row["topic"]` = topic của event ĐẦU TIÊN có topic khác None, còn
    # `row["state"]` = kết cục của event CUỐI. Nên ca `decided[nudge]` rồi `followed[rest_nudge]`
    # trên cùng `decision_id` cho `row["topic"] = "nudge"` ⇒ bản đầu chỉ kiểm `is_soft(row[...])`
    # ở vòng decision ⇒ một `followed` MỀM vào **tử số** của topic ĐƯỢC ĐO (đo được:
    # `decision_adherence = 1.0`). Vòng event đã kiểm cả hai hướng, vòng decision thì chưa — tức
    # tuyên bố "adherence_view là TẦNG THỨ HAI độc lập" của chính cycle này chưa đúng ở hướng đó.
    #
    # ⚠ ĐÁNH ĐỔI KHAI TƯỜNG MINH: một `decision_id` mang CẢ topic mềm lẫn topic được đo là **lỗi
    # producer** (không đường nào hôm nay tạo được: UI trả 422, sim chỉ có 5 kênh — đều được đo).
    # Khi nó xảy ra, ta chọn **loại cả quyết định** thay vì giữ phần được đo. Tức có thể mất một
    # `decided` hợp lệ. Chọn vậy vì hai sai không cùng hạng: mất một mẫu số là **mất độ chính xác
    # của phép đo**, còn để `followed` mềm vào tử số là **phá một ranh giới đã chốt**.
    # 🔴 UPDATE-129 (`N9`): tiêu chí loại đổi từ `is_soft` sang `classify(...) != "measured"`.
    #
    # Bản UPDATE-128 chỉ loại topic MỀM, nên topic **CHƯA KHAI** (`classify` → `"unknown"`) đi thẳng
    # vào nhóm ĐƯỢC ĐO — `is_soft("unknown")` trả `False`. Đo được trên store dev bẩn: 52 event mềm
    # bị loại đúng, nhưng khoá `khong_khai_bao` **vẫn lọt vào view**. Tức tầng đọc **fail-OPEN**
    # trong khi UPDATE-128 đã khai nó là fail-closed. Boundary 422 của router chỉ chặn topic lạ MỚI
    # qua đường UI — không chặn bản ghi cũ, đường sim, và đường pipeline (`episode_store`).
    #
    # Vì sao fail-closed là đúng hướng: một topic lạ **có thể là khuyên mềm ai đó quên khai**. Đo nó
    # là tạo đúng thước nghe-lời mà ranh giới cấm. Bỏ sót một mẫu số thì mất độ chính xác; đo nhầm
    # một lời khuyên sức khoẻ thì phá một ranh giới đã chốt — hai sai không cùng hạng.
    #
    # ⚠ `None` vẫn được ĐO, và đó KHÔNG phải sơ suất. `None` = *"producer cũ không có khái niệm
    # topic"* (đường sim không đặt `channel`); `unknown` = *"producer CÓ đặt tên, nhưng chưa ai phân
    # loại cái tên đó"* — cái sau là tín hiệu ai đó vừa thêm gì. Gộp hai cái sẽ vứt dữ liệu sim hợp lệ.
    #
    # Cú loại này KHÔNG được im lặng: `adherence_drops()` bên dưới đếm nó, và
    # `sim_metrics.adherence_flags` TREO khi có `unknown` (Cường chốt 2026-08-03, cùng nguyên tắc
    # `D-M3-10`: mẫu số không đầy đủ thì mọi Δ đều đáng ngờ).
    _soft_dids = {did for did, r in states.items() if classify(r["topic"]) != "measured"}
    _soft_dids |= {e["decision_id"] for e in events
                   if classify((e.get("payload") or {}).get("topic")) != "measured"}

    for did, row in states.items():
        if did in _soft_dids:
            continue          # khuyên mềm: KHÔNG có mẫu số, theo thiết kế (xem docstring)
        agg = _row((row["run_id"], row["driver_id"], row["topic"]))
        if row["state"] == "suppressed":
            # ĐA-04: bị NÉN nghĩa là advisor KHÔNG NÓI — không thuộc mẫu số "đã nói bao
            # nhiêu lần, được nghe bao nhiêu". Đếm riêng để biết nhịp chặn bao nhiêu.
            agg["suppressed"] += 1
            continue
        agg["decided"] += 1
        if row["state"] in ("followed", "dismissed"):
            agg[row["state"]] += 1
    # L4-01 (phản biện 2026-07-31): "advisor ĐÃ NÓI" có HAI TÊN — sim ghi `decided`, sản
    # phẩm ghi `displayed` (`routers/advice.py`). Mẫu số cũ chỉ nhận `decided` ⇒ ở đường sản
    # phẩm `event_decided` = 0 VĨNH VIỄN ⇒ `event_adherence` = None (một nửa bộ đo hai-tên
    # chết im lặng), và tệ hơn: `event_followed` = 1 > `event_decided` = 0 là trạng thái BẤT
    # KHẢ (tử số vượt mẫu số) mà không cổng nào bắt. Gộp `displayed` vào mẫu số event.
    # ⚠ KHÔNG gộp vào `decided` (mẫu số DECISION) — đó là đơn vị khác, `decision_state` đã
    # xử lý `displayed` riêng ở `_TERMINAL` logic.
    _EVENT_SPOKEN = ("decided", "displayed")
    for e in _ordered(events):
        et = e["event_type"]
        if et not in (*_EVENT_SPOKEN, "followed"):
            continue
        topic = (e.get("payload") or {}).get("topic")
        # Phải lọc ở CẢ HAI vòng — vòng decision và vòng event là hai đường vào view khác nhau;
        # lọc một vòng để hở vòng kia là đúng họ lỗi `L4-01` (hai tên cho "advisor đã nói", sửa
        # một nửa rồi tưởng xong).
        #
        # ⚠ Điều kiện ở đây CHỈ là `in _soft_dids`, KHÔNG kèm `classify(topic) != "measured"` nữa —
        # dù bản đầu có cả hai. Lý do bỏ vế thứ hai không phải gọn hơn mà là **nó THỪA và đã đánh
        # lừa chính phép thử của tôi**: `_soft_dids` gom topic từ CẢ `states` LẪN mọi event, còn
        # `decision_state` tạo row cho mọi `decision_id` — nên "event có topic không-được-đo" luôn
        # kéo theo "did nằm trong `_soft_dids`" (đã chứng minh bằng đo). Khi sever-restore tiêm vào
        # MỘT trong hai vế, vế kia vẫn lọc ⇒ cổng XANH ⇒ tôi suýt đọc thành *"cổng không bắn"*.
        # Hai điều kiện dư thừa che nhau làm mutation test **nói dối**. Một điểm enforce, một điểm
        # để sever.
        if e["decision_id"] in _soft_dids:
            continue
        agg = _row((e.get("run_id"), e["driver_id"], topic))
        agg["event_decided" if et in _EVENT_SPOKEN else "event_followed"] += 1
    for agg in view.values():
        agg["decision_adherence"] = (agg["followed"] / agg["decided"]
                                     if agg["decided"] else None)
        agg["event_adherence"] = (agg["event_followed"] / agg["event_decided"]
                                  if agg["event_decided"] else None)
    return view


def adherence_drops(events) -> dict:
    """Đếm những QUYẾT ĐỊNH bị `adherence_view` loại — và VÌ SAO.

    🔴 Vì sao cần (`N5`, người phản biện tìm ra khi **hạ** một finding khác): `adherence_view` loại
    quyết định bằng `continue`, nên cú loại **không để lại dấu vết nào**. Và cổng canh nó —
    `sim_metrics.adherence_flags` — chỉ kiểm `event_decided == 0 and decided > 0`, tức nó **không
    thể thấy một khoá VẮNG MẶT**. Hệ quả: nếu tương lai có producer sinh topic lạ hoặc trộn topic
    thì **mẫu số tụt mà không ai biết**, và mọi Δ tính trên đó trông vẫn bình thường.

    Đó đúng là hình dạng của `D-M3-01` — con số sai sống qua **39 artifact** vì không cơ chế nào
    kêu. Nên hàm này tồn tại để cú loại **nói ra được**.

    Trả về (thêm khoá về sau được, đừng phá khoá cũ):
      `soft`            số quyết định bị loại vì topic KHUYÊN MỀM — **bình thường**, ranh giới đang chạy
      `unknown`         số quyết định bị loại vì topic CHƯA KHAI — **bất thường**, phải TREO
      `mixed`           số quyết định mang CẢ topic được-đo lẫn topic bị-loại — **lỗi producer**
      `topics_unknown`  danh sách tên topic chưa khai (để người sửa biết khai cái gì)

    ⚠ Hàm RIÊNG chứ không nhét vào `adherence_view`: view đó có hai consumer thật
    (`sim_metrics.adherence_audit`, `scripts/probe_adherence_truth.py`) và đổi hình dạng trả về của
    nó là phá hợp đồng đang chạy. Thêm hàm thì cộng thêm, không phá gì.
    """
    events = list(events)
    states = decision_state(events)

    # topic THEO QUYẾT ĐỊNH — gom mọi topic mà các event của cùng `decision_id` mang.
    topics_theo_did: dict[str, set] = {}
    for e in events:
        topics_theo_did.setdefault(e["decision_id"], set()).add(
            (e.get("payload") or {}).get("topic"))
    for did, r in states.items():
        topics_theo_did.setdefault(did, set()).add(r["topic"])

    dem = {"soft": 0, "unknown": 0, "mixed": 0}
    ten_unknown: set[str] = set()
    for did in states:
        cls = {classify(t) for t in topics_theo_did.get(did, {None})}
        if cls <= {"measured"}:
            continue
        if "measured" in cls:
            dem["mixed"] += 1          # trộn: quyết định hợp lệ bị loại CẢ CỤM (đánh đổi đã khai)
        elif "unknown" in cls:
            dem["unknown"] += 1
        else:
            dem["soft"] += 1
        ten_unknown |= {str(t) for t in topics_theo_did.get(did, set())
                        if classify(t) == "unknown"}
    dem["topics_unknown"] = sorted(ten_unknown)
    return dem


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
# SỬA THƯỚC (UPDATE-113, Cường duyệt 2026-07-31 — spec e10-advisor-noisy §5.5 nhánh 3):
# `standby_followed` KHÔNG còn map thành `followed`. Nó chỉ chứng minh việc THI HÀNH
# (actor thật sự dời chỗ), mà thi hành = coin-true ∧ *thi-hành-được*. Các ca coin-true
# nhưng không thi hành là code path THẬT (pop im lặng khi đã đứng đúng ô `world.py`;
# bận tới hết ca; bản năng ≠ WAIT ở chế độ `wait_only`) — đếm chúng thành "không theo"
# làm adherence đo lệch null ~2,4đp, và ở n=100 seed cổng z Poisson-binomial TREO
# (đo được z=−4,40 arm oracle; dự đoán từ preflight n=30 chỉ −2,39 vì chưa đủ power).
#
# Nay `followed` sinh từ `coin_follow_ids` trong detail `standby_alloc` (kết cục COIN tại
# đúng lúc gán — cùng nguồn sự thật với `adherence_coin`), còn tỷ lệ thi hành thành CHỈ
# TIÊU RIÊNG `execution_rate` (`sim_metrics.adherence_audit`). Hai câu hỏi khác nhau:
# "tài xế có NGHE không" vs "nghe rồi có LÀM ĐƯỢC không".
_TERMINAL_ONLY = {
    "advice_suppressed": ("suppressed", "system"),
}
# Kind chứng minh THI HÀNH (không vào tử số adherence; đếm riêng cho execution_rate).
EXECUTION_KINDS = {"standby_followed"}


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
    coin_true = set(detail.get("coin_follow_ids") or [])
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
        if aid in coin_true:
            # Kết cục COIN tại đúng lúc gán — độc lập với việc thi hành được hay không.
            out.append({
                "event_id": f"sim-{run_id}:{aid}:standby_coin:{e.t_min:g}",
                "decision_id": did, "display_id": None, "driver_id": str(aid),
                "run_id": run_id, "event_type": "followed", "reason_code": "coin",
                "occurred_at": iso, "observed_at": iso, "actor": "driver",
                "origin": "sim", "source": "MOCK", "context_revision": None,
                "payload": {"topic": "positioning", "t_min": e.t_min,
                            "sim_kind": "standby_alloc_coin", "target_cell": e.cell},
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
