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
from pydantic import BaseModel, Field, field_validator, model_validator

from app.adapters import advisor, mockdata
from gsm_core.lifecycle.advice_topics import SOFT_TOPICS, classify, is_soft

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

# HỢP NHẤT PR #4 (Cường chốt 2026-08-03) — LỚP HAI TẦNG.
#
# Khánh siết `topic` thành `Literal["brief","nudge","recap"]` ở tầng pydantic. Ý định ĐÚNG: chặn rác
# sớm, trả 422 trước khi bất cứ gì được ghi. Nhưng ba giá trị viết cứng làm **đường ray KHUYÊN MỀM
# không thể chạm tới** — `?topic=weather` bị 422 ở pydantic nên cờ `is_soft_advice`, nhánh
# `no_soft_producer`, và toàn bộ ranh giới Cường duyệt cùng ngày **không bao giờ đi tới được**. Nó
# cũng chặn `positioning`/`accept_lift`/`shift_extend` mà test vòng đời đang dùng.
#
# Giữ ý định của Khánh, đổi NGUỒN của danh sách: suy từ registry thay vì viết cứng — nhưng **hai bề
# mặt KHÁC NHAU**, vì GET và POST hỏi hai câu khác nhau.
#
# 🔴 Và Khánh đúng ở một điểm quan trọng hơn tôi tưởng lúc đầu. Docstring test của anh ấy:
# *"V1 chỉ nhận ba legacy surface; **safety priority không do client khai**"*. Đó chính là phản biện
# đúng cho lỗ `F1` mà soi độc lập bắt ở UPDATE-128: tôi để `is_soft_advice` suy từ **query param do
# CLIENT chọn**, nên một GET là đủ dán nhãn "khuyên mềm" lên một thẻ kinh tế. Bề mặt hẹp của Khánh
# **bịt lỗ đó từ gốc** — client không khai được nữa thì không dán nhãn sai được nữa.
#
# ⇒ GET giữ đúng ba bề mặt của Khánh. Khi có nguồn khuyên mềm thật, **SERVER** đặt `is_soft_advice`
# theo NỘI DUNG thẻ, không theo thứ client hỏi.
TopicGet = Literal[CLIENT_TOPICS]  # type: ignore[valid-type]

# POST thì RỘNG HƠN, và phải vậy: client báo hành động trên một thẻ **server đã đưa** — mà thẻ đó có
# thể là khuyên mềm. Nếu chặn `weather` ở pydantic thì `dismissed` (nút Ẩn) cũng bất khả ⇒ tài xế mất
# cách tắt thẻ phiền, tức phá đúng điều Cường chốt (*"giữ nút ẩn, bỏ nút Làm theo"*). Và nó sẽ làm
# cổng 422 của tôi đỏ **vì lý do khác** cái nó tuyên bố — đúng bẫy `D-M3-17`.
TopicPost = Literal[tuple(sorted(set(CLIENT_TOPICS) | SOFT_TOPICS))]  # type: ignore[valid-type]


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
               topic: TopicGet = Query(DEFAULT_TOPIC),
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
    # `is_soft_advice`: SERVER trả lời "thẻ này có phải khuyên mềm không", client KHÔNG tự suy.
    #
    # Bản đầu của UPDATE-128 để `cards.js` chép danh sách `SOFT_TOPICS` sang JS — tức **nguồn sự
    # thật thứ hai** cho một ranh giới đạo đức, đúng thứ `D-M3-17` vừa trả giá (UI tự tính tầm pin
    # bằng công thức riêng, lệch engine 1,76× mà 1.000 test không thấy vì không test nào so hai
    # bên). Thêm topic mềm mà quên sửa JS thì thẻ đó vẫn vẽ nút "Làm theo". Nay client chỉ đọc
    # cờ này; registry `advice_topics.py` là nguồn DUY NHẤT.
    #
    # 🔴 SOI ĐỘC LẬP 2026-08-03 BẮT MỘT LỖ THẬT Ở BẢN ĐẦU, đã sửa ngay dưới đây. Bản đầu chỉ làm
    # `soft = is_soft(topic)` rồi trả kèm lời khuyên mà advisor sinh ra — nhưng `topic` là **query
    # param do CLIENT chọn** và `advisor.advice()` **không nhận `topic`**. Tái lập được:
    #
    #   GET /api/v1/advice?topic=weather&now_min=840
    #     -> is_soft_advice = True
    #     -> item = {kind: "bonus_gap", title: "Còn với được mốc thưởng 30.000đ hôm nay"}
    #     -> adherence_view = {}          # lời khuyên KINH TẾ thoát khỏi phép đo
    #
    # Tức "một nguồn sự thật" chỉ áp cho **PHÂN LOẠI topic**, chưa buộc vào **NỘI DUNG thẻ**. Một
    # GET là đủ xoá một lời khuyên kinh tế khỏi bảng đo. (Hôm nay chưa có số nào sai: không client
    # nào gửi `topic=weather` — `cards.js` chỉ gửi 3 giá trị hardcode — và không consumer nào đọc
    # `adherence_view` trên đường UI. Nhưng đó là may, không phải cơ chế.)
    #
    # Sửa: (1) `topic` phải nằm trong registry, **fail-closed ở RUNTIME** chứ không chỉ ở test;
    # (2) topic mềm thì KHÔNG được trả lời khuyên do pipeline kinh tế sinh — hôm nay **chưa có
    # nguồn sinh khuyên mềm nào**, nên câu trả lời trung thực là IM LẶNG kèm lý do, không phải
    # gắn nhãn mềm lên một thẻ thưởng.
    # 🔴 HỢP NHẤT PR #4: hai nhánh từng ở đây (`classify(...)=="unknown"` → 422, và `if soft:` →
    # im lặng `no_soft_producer`) NAY LÀ CODE CHẾT và đã bị xoá. Bề mặt GET hẹp của Khánh
    # (`TopicGet` = 3 topic client) chặn cả hai ca **ở pydantic, trước khi vào hàm**.
    #
    # Đây là kết quả TỐT HƠN bản của tôi, và đáng ghi lại vì sao: lỗ `F1` (soi độc lập UPDATE-128)
    # là *"cờ đạo đức suy từ query param do CLIENT chọn"*. Tôi vá bằng cách trả im lặng khi client
    # hỏi topic mềm — tức vẫn để client khai. Khánh **bỏ hẳn quyền khai đó**. Nguyên tắc của anh ấy
    # viết trong test: *"safety priority không do client khai"*.
    #
    # ⇒ `is_soft_advice` nay do SERVER quyết theo NỘI DUNG thẻ. Hôm nay luôn `False` vì chưa có
    # nguồn sinh khuyên mềm; khi Khánh làm thẻ thời tiết thì server đặt cờ theo thẻ, không theo
    # thứ client hỏi. Giữ field trong response (contract) để client không phải tự suy.
    soft = False
    prov = advisor.provenance(d, now_min)

    if verdict.verdict != PRESENT:
        _note_suppressed(did, d, topic, now_min, verdict.reason)
        # HỢP NHẤT PR #4 (2026-08-03): Khánh và tôi độc lập tìm ra CÙNG lỗi này (nhánh im lặng
        # thiếu `scenario_id`/`seed`/`data_mode` mà contract khai `required`) và sửa hai cách.
        # Giữ bản dùng `advisor.provenance()` vì nó chia sẻ MỘT nguồn với adapter thay vì chép ba
        # chuỗi sang router — đúng bài học `D-M3-17`. Đã đo: hai cách cho CÙNG giá trị
        # (`advisor._dataset_seed()` == `mockdata.manifest()["seed_base"]` == 7000), nên đây là
        # chọn cách viết, không phải bác kết quả của Khánh.
        return {**prov, "driver_id": did, "date": d, "items": [],
                "silent": {"is_silent": True, "reason_code": verdict.reason,
                           "message": _SILENT_MSG.get(
                               verdict.reason,
                               "Trợ lý tạm chưa có gì cần nói thêm lúc này.")},
                "topic": topic, "is_soft_advice": soft,
                "cadence": {"verdict": verdict.verdict, "phase": phase,
                            "next_eligible_min": verdict.next_eligible_min}}
    out = advisor.advice(did, d, now_min, shift_end_min)
    _note_shown(did, d, topic, now_min, out.get("items") or [])
    return {**out, "topic": topic, "is_soft_advice": soft,
            "cadence": {"verdict": PRESENT, "phase": phase}}


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
    topic: TopicPost = DEFAULT_TOPIC

    @field_validator("topic")
    @classmethod
    def _topic_phai_duoc_phan_loai(cls, v: str) -> str:
        """Fail-closed ở RUNTIME, không chỉ ở test (soi độc lập 2026-08-03).

        Bản đầu chỉ có cổng `tests/test_advice_topic_registry.py` quét **hằng chuỗi trong 3 file
        .py**. Nhưng runtime thì `topic` là chuỗi tuỳ ý từ client ⇒ một topic chưa phân loại đi
        thẳng vào store và **rơi vào nhóm ĐƯỢC ĐO** (`classify(None|lạ)` → không soft ⇒ có mẫu số).
        Tức "fail-closed" đúng ở tầng phát triển mà **fail-OPEN ở tầng chạy** — đúng khoảng cách
        mà `D-M3-08`/`D-M3-13` đã trả giá: cơ chế được khai là có, nhưng không phủ đường thật.
        """
        if classify(v) == "unknown":
            raise ValueError(
                f"topic {v!r} chưa được phân loại trong `gsm_core.lifecycle.advice_topics`. "
                f"Một topic lạ sẽ IM LẶNG rơi vào nhóm ĐƯỢC ĐO — nếu nó thực ra là khuyên mềm "
                f"thì ta vừa tạo một thước nghe-lời cho lời khuyên sức khoẻ. Khai vào "
                f"MEASURED_TOPICS hoặc SOFT_TOPICS trước khi dùng.")
        return v

    @model_validator(mode="after")
    def _khuyen_mem_khong_nhan_followed(self):
        """Quyết định Cường 2026-08-03: khuyên mềm (thời tiết · gợi ý nghỉ · giao thông) KHÔNG
        có trace đồng ý/không đồng ý.

        `dismissed` vẫn nhận — nó là *"đừng nhắc nữa"* (nhịp nói ĐA-04), không phải *"tôi không
        đồng ý"*. `followed` thì không: nó chỉ có một nghĩa, và nghĩa đó tạo ra một thước nghe-lời
        cho lời khuyên sức khoẻ ⇒ biến sức khoẻ thành chỉ tiêu tối ưu, trái §1.2b.

        Chặn HAI TẦNG như L4-07 đã làm: client không vẽ nút "Làm theo" cho thẻ mềm
        (`cards.js` chế độ `soft`), và boundary này từ chối. Một tầng thôi thì tầng kia vẫn
        thủng — client cũ, `curl`, app Flutter khác bản đều gọi được endpoint này.
        """
        if self.action == "followed" and is_soft(self.topic):
            raise ValueError(
                f"topic {self.topic!r} là KHUYÊN MỀM — không nhận action 'followed'. "
                f"Khuyên mềm được nói vì đúng cho tài xế, KHÔNG kèm phép đo mức nghe lời: đo "
                f"nó là biến sức khoẻ thành chỉ tiêu để tối ưu (§1.2b). Dùng 'dismissed' nếu ý "
                f"bạn là 'đừng nhắc nữa' — đó là nhịp nói, không phải sự đồng thuận. "
                f"Xem tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md")
        return self

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
        topic = p.get("topic")
        rows.append({"advice_id": e["decision_id"], "driver_id": e["driver_id"],
                     "date": p.get("date"), "action": p.get("action"),
                     "card_kind": p.get("card_kind"), "at_min": p.get("at_min"),
                     # `topic` + `is_soft_advice`: soi độc lập 2026-08-03 bắt được — UPDATE-128 sửa
                     # `index.html` để HỨA rằng khối "Nhật ký làm-theo" phân biệt khuyên mềm, nhưng
                     # endpoint này **bỏ rơi `topic`** khi dựng row ⇒ UI không có dữ liệu để phân
                     # biệt. Tức tôi viết một lời hứa vào UI mà không nối đường dữ liệu cho nó —
                     # đúng họ lỗi "tài liệu quảng cáo cơ chế không có đường chạy" mà chính cycle
                     # này dựng cổng để chặn. `topic` ĐÃ có sẵn trong payload, chỉ là không được
                     # mang ra.
                     "topic": topic, "is_soft_advice": is_soft(topic),
                     "client_ts": e["observed_at"], "is_mock": True})
    return {"is_mock": True, "actions": rows[-limit:][::-1]}
