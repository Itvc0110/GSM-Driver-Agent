"""Router advice: gọi solver S1 thật qua adapter — contract `ui/contracts/advice.json`.

UX-CARDS (DIRECTIVES §12, UPDATE-067): thêm vòng đo adherence EXPLICIT —
POST /action ghi nút bấm (Làm theo/Bỏ qua/Vì sao); GET /actions đọc lại cho khối
"Nhật ký làm-theo" ở màn Cài đặt. Đường đo IMPLICIT (hành vi đổi sau advice) vẫn
nằm ở sim/A-B — hai đường bổ trợ.

ĐA-05 Cycle W: store CANONICAL của action là AdviceEventLog (SQLite append-only,
cùng luật projection với sim — verdict Cường "một luật, một database"); JSONL
`advice_actions.jsonl` GIỮ như debug export song song (quyết định duyệt: "JSONL chỉ
debug/export"). GET /actions đọc từ event log — hàng ghi vào JSONL trước Cycle W
không tự chuyển (mock-only, gitignored — chấp nhận, ghi ở UPDATE-091).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from datetime import date as _date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.adapters import advisor, mockdata
from gsm_core.lifecycle.cadence import (PRESENT, CadenceMemory, decision_bucket,
                                        evaluate, shift_phase)
from gsm_core.lifecycle.event_log import AdviceEventLog

# Lời im lặng nói với tài xế — tôn trọng, không đổ lỗi, không hứa (DIRECTIVES §12.4).
_SILENT_MSG = {
    "dismissed_for_window": "Bạn đã bỏ qua gợi ý này, trợ lý sẽ không nhắc lại trong "
                            "khoảng thời gian này của ca.",
    "shift_budget_exhausted": "Hôm nay trợ lý đã nhắc đủ rồi — để bạn tập trung chạy.",
    "topic_cooldown": "Trợ lý vừa nhắc về việc này, sẽ quay lại sau.",
    "unsafe_while_moving": "Bạn đang chạy — trợ lý sẽ nhắc khi bạn dừng.",
}

router = APIRouter()

TELEMETRY_DIR = mockdata.REPO_ROOT / "data" / "ui-telemetry"
ACTIONS_FILE = TELEMETRY_DIR / "advice_actions.jsonl"

# nút UI → event_type lifecycle ("Vì sao"/expanded = một lần card được XEM KỸ → displayed)
_ACTION_TO_EVENT = {"followed": "followed", "dismissed": "dismissed",
                    "expanded": "displayed"}


def _lifecycle_db() -> Path:
    """Đọc TELEMETRY_DIR tại call-time để monkeypatch của tests có hiệu lực."""
    return TELEMETRY_DIR / "advice_lifecycle.db"


# L4-07(SOI) — giờ BẮT ĐẦU ca: trước đây là HẰNG 06:00 cho MỌI tài xế trong khi
# `shift_end_min` đã là query param ⇒ bất đối xứng, và pha ca (early/mid/late) của tài xế
# ca đêm bị tính sai hoàn toàn. Nay tham số hoá; hằng này chỉ còn là DEFAULT của demo.
DEFAULT_SHIFT_START_MIN = 6 * 60
SHIFT_START_MIN = DEFAULT_SHIFT_START_MIN   # giữ tên cũ cho consumer khác, = default

# L4-09 — `topic` là NAMESPACE của cooldown/dismiss. Client (`cards.js KIND_TOPIC`) chỉ gửi
# ba giá trị này; default cũ `"bonus"` KHÔNG client nào gửi ⇒ namespace mồ côi có cooldown và
# dismiss riêng mà không ai nuôi. Default nay là một topic THẬT.
CLIENT_TOPICS = ("brief", "nudge", "recap")
DEFAULT_TOPIC = "brief"


def _norm_shift_end(shift_end_min: int, start_min: int = DEFAULT_SHIFT_START_MIN) -> int:
    """R-11 (soi đối kháng vòng 2): ca vắt qua nửa đêm.

    Query cho phép `shift_end_min` nhỏ tuỳ ý (`ge=0`), nên ca 22:00→02:00 gửi 120 ⇒
    `shift_len = 120 − 360 < 0` ⇒ `shift_phase` trả `"early"` VĨNH VIỄN ⇒ "im hết pha" biến
    thành "im hết ca", trái đúng verdict đã chốt. Chuẩn hoá: kết ca sớm hơn mở ca nghĩa là
    hôm sau.
    ⚠ Phần còn lại của R-11 (memory lọc theo `date` nên qua 00:00 ngân sách được cấp lại
    giữa ca) KHÔNG sửa ở đây — nó cần khái niệm `shift_id`, không phải một dòng. → `D-R11b`.
    """
    return shift_end_min + 1440 if shift_end_min < start_min else shift_end_min


def _phase_of(at_min: float | None, shift_end_min: int) -> str | None:
    """Pha ca của một mốc thời gian — MỘT công thức duy nhất, dùng ở cả đường ghi lẫn đọc.

    F4 (soi đối kháng 2026-07-29): trước đây `POST /action` tính pha bằng
    `advisor.DEFAULT_SHIFT_END_MIN` **cứng 22:00** rồi lưu vào payload, còn `GET /advice`
    tính bằng `shift_end_min` từ query ⇒ hai công thức cho CÙNG một phút, lệch nhau ngay
    khi ca của tài xế khác ca mặc định. Đúng họ Lỗi #1 (hai lưới thời gian cho một khái
    niệm). Cách sửa KHÔNG phải đồng bộ hai công thức mà là **bỏ một cái**: pha nay luôn
    được tính LÚC ĐỌC từ `at_min` đã lưu; trường `phase` trong payload chỉ còn để debug và
    **không được dùng để quyết định**.
    """
    if at_min is None:
        return None
    end = _norm_shift_end(shift_end_min)
    return shift_phase(float(at_min) - SHIFT_START_MIN, end - SHIFT_START_MIN)


def _cadence_memory(driver_id: str, date: str, phase: str,
                    shift_end_min: int = advisor.DEFAULT_SHIFT_END_MIN) -> CadenceMemory:
    """Dựng ký ức nhịp cho tài xế này HÔM NAY từ store canonical (ĐA-05).

    Đây là nửa UI của "một luật": sim nuôi memory trong RAM, UI đọc lại từ
    `AdviceEventLog` — rồi CẢ HAI gọi cùng `cadence.evaluate`.
    """
    mem = CadenceMemory()
    db = _lifecycle_db()
    if not db.exists():
        return mem
    with AdviceEventLog(db) as log:
        rows = [e for e in log.events()
                if e["origin"] == "ui" and e["driver_id"] == driver_id
                and (e["payload"] or {}).get("date") == date]
    # Ngân sách đếm số lần advisor NÓI = số QUYẾT ĐỊNH, không phải số event. Bản đầu
    # `proactive_count += 1` cho mỗi event ⇒ một card "Vì sao"(displayed) rồi
    # "Làm theo"(followed) tiêu HAI suất — 3 card là advisor im cả ngày (reproduce được).
    # Đúng họ lỗi hai-đơn-vị-đo decision-vs-event mà Cycle W đã trả giá.
    _spoken_ids: set[str] = set()
    for e in rows:
        payload = e["payload"] or {}
        topic = payload.get("topic") or payload.get("card_kind") or "advice"
        if e["event_type"] == "dismissed":
            # Bỏ qua ở PHA nào thì im hết pha đó (Cường chốt 2026-07-29). Chỉ áp cho
            # SẢN PHẨM — sim không có nhánh này (xem cadence.py §ranh giới).
            # F4: pha tính LẠI từ `at_min` bằng công thức của người ĐỌC — không đọc
            # `payload["phase"]` (số đó do đường ghi tính bằng shift_end CỨNG).
            # R-18: KHÔNG fallback về pha của người ĐỌC. Record thiếu `at_min` (bản trước
            # ĐA-04, hoặc POST không gửi — field `default=None`) mà gán vào pha hiện tại thì
            # một cú Bỏ qua cũ thành **lệnh im di động**: hỏi ở pha nào cũng im pha đó. Không
            # biết pha thì bỏ qua record — "không biết" khác "là pha này".
            _ph = _phase_of(payload.get("at_min"), shift_end_min)
            if _ph is not None:
                mem.dismissed_in_phase[topic] = _ph
        elif e["event_type"] in ("displayed", "followed"):
            _spoken_ids.add(e["decision_id"])
            # Cooldown 20′/chủ đề CHỈ chạy nếu có ai nuôi `last_decided_min`. Bản đầu của
            # cycle này quên đúng dòng dưới ⇒ `topic_cooldown` sống ở sim nhưng CHẾT ở sản
            # phẩm, trong khi `_SILENT_MSG` vẫn có sẵn câu cho nó — tức code tự quảng cáo
            # một nhánh không bao giờ chạy. Đó là đúng thứ "một luật" sinh ra để xoá bỏ.
            at = payload.get("at_min")
            if at is not None:
                prev = mem.last_decided_min.get(topic)
                if prev is None or float(at) > prev:
                    mem.last_decided_min[topic] = float(at)
    mem.proactive_count = len(_spoken_ids)
    return mem


@router.get("")
def get_advice(driver_id: str | None = Query(None), date: str | None = Query(None),
               now_min: int = Query(14 * 60, ge=0, le=24 * 60),
               shift_end_min: int = Query(advisor.DEFAULT_SHIFT_END_MIN, ge=0, le=24 * 60),
               is_driving: bool = Query(False),
               topic: Literal["brief", "nudge", "recap"] = Query(DEFAULT_TOPIC),
               shift_start_min: int = Query(DEFAULT_SHIFT_START_MIN, ge=0, le=1439)):
    """ĐA-04: nhịp do LUẬT CHUNG quyết định, không phải wall-clock của client.

    Trước đây `cards.js` tự chọn giờ 09:00/14:00/21:30 và backend luôn trả card ⇒ nút
    "Bỏ qua" của tài xế không đổi được gì (vòng adherence §12 HỞ về hành vi). Nay:
    dismissed trong pha ⇒ im; hết ngân sách ca ⇒ im; đang lái ⇒ hoãn (QUEUE).
    """
    dv = mockdata.default_view()
    did = driver_id or dv["driver_id"]
    d = date or dv["date"]
    phase = shift_phase(now_min - shift_start_min,
                        _norm_shift_end(shift_end_min, shift_start_min) - shift_start_min)
    verdict = evaluate(topic, float(now_min), phase,
                       _cadence_memory(did, d, phase, shift_end_min),
                       is_driving=is_driving)
    if verdict.verdict != PRESENT:
        _note_suppressed(did, d, topic, now_min, verdict.reason)
        return {"scenario_id": f"mock-realdata:{d}",
                "seed": int(mockdata.manifest().get("seed_base", 0)),
                "data_mode": "mock-realdata", "is_mock": True,
                "driver_id": did, "date": d, "items": [],
                "silent": {"is_silent": True, "reason_code": verdict.reason,
                           "message": _SILENT_MSG.get(
                               verdict.reason,
                               "Trợ lý tạm chưa có gì cần nói thêm lúc này.")},
                "cadence": {"verdict": verdict.verdict, "phase": phase,
                            "next_eligible_min": verdict.next_eligible_min}}
    out = advisor.advice(did, d, now_min, shift_end_min)
    _note_shown(did, d, topic, now_min, out.get("items") or [])
    return {**out, "cadence": {"verdict": PRESENT, "phase": phase}}


def _note_suppressed(driver_id: str, date: str, topic: str, now_min: int,
                     reason: str) -> None:
    """Ghi lại việc advisor ĐỊNH NÓI nhưng bị NHỊP CHẶN — L4-04 (phản biện 2026-07-31).

    Sim ghi `advice_suppressed` mỗi lần nhịp chặn (`world.py` drain_suppressed); sản phẩm
    trước đây chỉ trả silent card và KHÔNG ghi gì ⇒ `adherence_view["suppressed"]` của đường
    sản phẩm luôn 0, và hai đường không so được dù dùng chung projection.

    `decision_id` mang hậu tố `-sup` đúng tiền lệ sim: cái bị nén là một CANDIDATE, không
    phải quyết định đã đưa ⇒ KHÔNG được vào mẫu số `decided` (`decision_state` đã tách
    `suppressed` khỏi `decided`).
    """
    bucket = decision_bucket(float(now_min))
    did_key = f"sup-{driver_id}-{date}-{topic}-{bucket}"
    occurred = f"{date}T{now_min // 60:02d}:{now_min % 60:02d}:00+07:00"
    now_iso = datetime.now(timezone.utc).isoformat()
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with AdviceEventLog(_lifecycle_db()) as log:
        log.append({
            "event_id": f"ui-sup-{driver_id}-{date}-{topic}-{bucket}",
            "decision_id": did_key, "display_id": None, "driver_id": driver_id,
            "run_id": None, "event_type": "suppressed", "reason_code": reason or None,
            "occurred_at": occurred, "observed_at": now_iso,
            "actor": "advisor", "origin": "ui", "source": "MOCK", "context_revision": None,
            "payload": {"action": "suppressed", "date": date, "at_min": now_min,
                        "topic": topic},
            "schema_version": "1.0.0",
        })


def _note_shown(driver_id: str, date: str, topic: str, now_min: int,
                items: list[dict]) -> None:
    """Ghi lại việc advisor ĐÃ NÓI — F1 (soi đối kháng 2026-07-29).

    Lỗ hổng trước đó: `GET /advice` trả card nhưng KHÔNG ghi event nào, nên cooldown và
    ngân sách phía SẢN PHẨM chỉ được nuôi khi tài xế **BẤM** nút. Tài xế phớt lờ 20 thẻ ⇒
    ngân sách không hao ⇒ advisor nói mãi. Sim thì ngược lại: `cadence_note_spoken` gọi
    ngay khi NÓI. Tức "một luật" bị hở đúng ở chỗ *đơn vị đếm*: sim đếm **lời nói**, sản
    phẩm đếm **cú bấm**. Nay cả hai đếm lời nói.

    ⚠ Đây là side-effect trên một GET — biết là mùi REST, và chọn có chủ ý: sự thật cần ghi
    là "advisor đã nói", mà chỉ server biết chắc điều đó. Nếu để client POST "đã xem" thì
    một client im lặng sẽ lại làm ngân sách không hao — tức là quay về đúng lỗ hổng này.
    Idempotent nhờ `event_id` chứa `advice_id` (đã mang `now_min`) + `INSERT OR IGNORE`.
    """
    if not items:
        return
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    occurred = f"{date}T{now_min // 60:02d}:{now_min % 60:02d}:00+07:00"
    now_iso = datetime.now(timezone.utc).isoformat()
    # Khoá theo BUCKET QUYẾT ĐỊNH (30′), không theo `advice_id`: `advice_id` mang `now_min`
    # nên nếu khoá theo nó thì mỗi lần client refresh với đồng hồ nhích một phút sẽ thành
    # "một lời khuyên mới" và đốt ngân sách. Cùng lời khuyên trong cùng bucket = MỘT lần nói.
    bucket = decision_bucket(float(now_min))
    with AdviceEventLog(_lifecycle_db()) as log:
        for it in items:
            aid = it.get("advice_id")
            if not aid:
                continue
            log.append({
                "event_id": f"ui-shown-{driver_id}-{date}-{topic}-{bucket}",
                "decision_id": aid, "display_id": None, "driver_id": driver_id,
                "run_id": None, "event_type": "displayed", "reason_code": None,
                "occurred_at": occurred, "observed_at": now_iso,
                "actor": "advisor", "origin": "ui", "source": "MOCK",
                "context_revision": None,
                "payload": {"action": "shown", "card_kind": it.get("kind") or "brief",
                            "date": date, "at_min": now_min, "topic": topic},
                "schema_version": "1.0.0",
            })


# L4-07 (phản biện 2026-07-31, reproduce được): card IM LẶNG vẫn vẽ nút "Làm theo"/"Bỏ qua"
# với `advice_id` do CLIENT BỊA (`cards.js` dùng `brief-{date}` / `recap-{date}` khi advisor
# không có item nào). Một cú bấm ⇒ POST /action ⇒ event log ghi decision+followed cho một lời
# khuyên **advisor CHƯA TỪNG ĐƯA** ⇒ `adherence_view` đếm decided=1/followed=1 ⇒
# `decision_adherence` = 100% cho quyết định MA, đúng lúc advisor im lặng.
#
# Chặn HAI TẦNG: client thôi vẽ nút trên card im lặng (`cards.js`), và boundary này từ chối —
# một tầng thôi thì tầng kia vẫn thủng (client cũ, curl, app khác).
_REAL_ADVICE_ID_PREFIXES = ("s1-", "s2-", "s4-", "s7-")   # namespace của adapter/solver


def is_fabricated_advice_id(advice_id: str) -> bool:
    """True nếu id KHÔNG thuộc namespace advisor thật (client tự chế cho card im lặng)."""
    return not str(advice_id).startswith(_REAL_ADVICE_ID_PREFIXES)


class AdviceAction(BaseModel):
    # X-6 (review batch 2): ID rỗng từng đi xuyên tới store rồi nổ HTTP 500 —
    # boundary validate phải đối xứng với date/at_min (422 tại pydantic).
    advice_id: str = Field(min_length=1)
    driver_id: str = Field(min_length=1)
    # `date` được ghép thành `occurred_at` ISO ⇒ phải đúng dạng NGAY TỪ ĐẦU. Không
    # validate ở đây thì store canonical từ chối SAU khi JSONL đã ghi ⇒ HTTP 500 và hai
    # store lệch nhau vĩnh viễn (review đối kháng reproduce với date='hom-nay').
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    action: str = Field(pattern="^(followed|dismissed|expanded)$")
    card_kind: str = Field(pattern="^(brief|nudge|recap)$")
    # le=1439: 1440 sinh "T24:00:00" — lọt regex schema (`\d{2}`) nhưng `fromisoformat`
    # nổ ⇒ MỘT record độc giết toàn bộ `decision_state` của store đó.
    at_min: int | None = Field(default=None, ge=0, le=1439)
    # ĐA-04: chủ đề của thẻ — cooldown/dismiss là THEO CHỦ ĐỀ, không phải toàn cục
    # (bỏ qua nhắc đổi pin không được khoá miệng cảnh báo mất thưởng).
    topic: Literal["brief", "nudge", "recap"] = "brief"

    @field_validator("advice_id")
    @classmethod
    def _advice_id_must_be_real(cls, v: str) -> str:
        """L4-07: từ chối id client bịa cho card im lặng — 422 tại boundary, không ghi gì."""
        if is_fabricated_advice_id(v):
            raise ValueError(
                f"advice_id {v!r} không thuộc namespace advisor (s1-/s2-/s4-/s7-): "
                f"card IM LẶNG không có quyết định để hành động lên. Hành động trên nó sẽ "
                f"tạo decision+followed MA và bơm adherence lên 100% (L4-07).")
        return v

    @field_validator("date")
    @classmethod
    def _date_exists_on_calendar(cls, v: str) -> str:
        """X-1 (review batch 2): '2026-02-31' khớp regex nhưng không tồn tại — trước
        đây HTTP 200 và record độc persist VĨNH VIỄN (store append-only) rồi giết mọi
        decision_state về sau. Regex không kiểm được lịch — phải parse thật."""
        _date.fromisoformat(v)
        return v


@router.post("/action")
def post_action(body: AdviceAction):
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()
    rec = {**body.model_dump(), "client_ts": now_iso, "is_mock": True}
    occurred = (f"{body.date}T{body.at_min // 60:02d}:{body.at_min % 60:02d}:00+07:00"
                if body.at_min is not None else now_iso)
    # Store CANONICAL ghi TRƯỚC, JSONL debug ghi SAU: nếu canonical từ chối thì không có
    # gì được ghi cả. Thứ tự ngược lại từng làm "debug export" có dữ liệu mà store thật
    # thì không — ngược đúng chiều tin cậy mà ĐA-05 tuyên bố.
    #
    # Idempotency key = (advice, action, GIÂY quan sát). Bản đầu khoá theo `at_min` —
    # nhưng frontend gửi at_min là HẰNG SỐ theo loại card (`cards.js`), nên cửa sổ dedupe
    # là CẢ NGÀY: "Làm theo → đổi ý Bỏ qua → Làm theo lại" bị nuốt còn 2 event và nhật ký
    # hiện NGƯỢC hành động cuối. Theo giây: double-click là một, đổi ý là hai.
    with AdviceEventLog(_lifecycle_db()) as log:
        log.append({
            "event_id": f"ui-{body.advice_id}-{body.action}-{now_iso[:19]}",
            "decision_id": body.advice_id,       # namespace s1-… của adapter (deterministic)
            "display_id": None,
            "driver_id": body.driver_id,
            "run_id": None,
            "event_type": _ACTION_TO_EVENT[body.action],
            "reason_code": "dismissed_for_window" if body.action == "dismissed" else None,
            "occurred_at": occurred,
            "observed_at": now_iso,
            "actor": "driver",
            "origin": "ui",
            "source": "MOCK",
            "context_revision": None,
            "payload": {"action": body.action, "card_kind": body.card_kind,
                        "date": body.date, "at_min": body.at_min,
                        # ĐA-04: `topic` để CadencePolicy đọc lại đúng ngữ cảnh.
                        # KHÔNG còn ghi `phase`: nó từng được tính ở đây bằng
                        # `DEFAULT_SHIFT_END_MIN` CỨNG (F4/Lỗi #16) rồi bị người đọc tin
                        # nhầm. Nay pha luôn tính LÚC ĐỌC từ `at_min` (`_phase_of`) — giữ
                        # lại một trường chết tính bằng công thức khác chỉ để "debug" là
                        # mời gọi đúng cái nhầm lẫn vừa sửa.
                        "topic": body.topic},
            "schema_version": "1.0.0",
        })
    # JSONL: debug export song song (ĐA-05 — không còn là store canonical)
    with ACTIONS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "logged": rec}


@router.get("/actions")
def get_actions(driver_id: str | None = Query(None), limit: int = Query(50, ge=1, le=500)):
    """Đọc từ event log canonical (ĐA-05) — giữ NGUYÊN hình dạng row của contract
    `advice_action.json` để web "Nhật ký làm-theo" không đổi."""
    db = _lifecycle_db()
    if not db.exists():
        return {"is_mock": True, "actions": []}
    with AdviceEventLog(db) as log:
        events = [e for e in log.events() if e["origin"] == "ui"]
    rows = []
    for e in sorted(events, key=lambda e: (e["observed_at"], e["event_id"])):
        p = e["payload"]
        if driver_id and e["driver_id"] != driver_id:
            continue
        rows.append({"advice_id": e["decision_id"], "driver_id": e["driver_id"],
                     "date": p.get("date"), "action": p.get("action"),
                     "card_kind": p.get("card_kind"), "at_min": p.get("at_min"),
                     "client_ts": e["observed_at"], "is_mock": True})
    return {"is_mock": True, "actions": rows[-limit:][::-1]}
