"""ĐA-05 Cycle W — POST /advice/action ghi store canonical (AdviceEventLog).

Ngữ nghĩa mới đáng test nhất: double-click cùng nút trong CÙNG GIÂY quan sát = MỘT
event (F-3: khoá theo `at_min` từng cho cửa sổ dedupe CẢ NGÀY vì frontend gửi at_min
là hằng số theo loại card — 'Làm theo → Bỏ qua → Làm theo lại' bị nuốt); JSONL vẫn
append đủ (debug export, không canonical).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import advice as advice_router
from gsm_core.lifecycle.event_log import AdviceEventLog

client = TestClient(app)

BODY = {"advice_id": "s1-driver-01-2026-07-29-840", "driver_id": "driver-01",
        "date": "2026-07-29", "action": "followed", "card_kind": "brief",
        "at_min": 840, "topic": "brief"}


@pytest.mark.parametrize("topic", ["safety", "bonus", "energy", "unknown"])
def test_v1_rejects_non_surface_topics(topic):
    """V1 chỉ nhận ba legacy surface; safety priority không do client khai."""
    response = client.get("/api/v1/advice", params={"topic": topic})
    assert response.status_code == 422


def test_v1_driving_silent_response_is_contract_complete(tmp_path, monkeypatch):
    """QUEUE/SUPPRESS vẫn phải mang đủ provenance envelope, không tạo card giả."""
    _patch(tmp_path, monkeypatch)
    body = client.get("/api/v1/advice", params={
        "topic": "brief", "is_driving": True, "now_min": 600,
    }).json()
    assert body["items"] == []
    assert body["silent"]["reason_code"] == "unsafe_while_moving"
    assert isinstance(body["scenario_id"], str) and body["scenario_id"]
    assert isinstance(body["seed"], int)
    assert body["data_mode"] in {"synthetic", "mock-realdata"}
    assert body["is_mock"] is True


class _FrozenDatetime(datetime):
    """F-S8: idempotency khoá theo GIÂY — hai POST thật có thể vắt qua ranh giới giây
    ⇒ test flaky. Đóng băng đồng hồ để test khẳng định đúng ngữ nghĩa, không may rủi."""

    @classmethod
    def now(cls, tz=None):
        return cls(2026, 7, 29, 14, 0, 7, tzinfo=tz or timezone.utc)


def _patch(tmp_path, monkeypatch, freeze: bool = False):
    monkeypatch.setattr(advice_router, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_router, "ACTIONS_FILE", tmp_path / "a.jsonl")
    if freeze:
        monkeypatch.setattr(advice_router, "datetime", _FrozenDatetime)


def test_double_click_is_one_lifecycle_event(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch, freeze=True)
    assert client.post("/api/v1/advice/action", json=BODY).status_code == 200
    assert client.post("/api/v1/advice/action", json=BODY).status_code == 200
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        evs = log.events(decision_id=BODY["advice_id"])
    assert len(evs) == 1, "double-click cùng GIÂY phải là MỘT event (INSERT OR IGNORE)"
    assert evs[0]["event_type"] == "followed" and evs[0]["origin"] == "ui"
    # JSONL debug export vẫn ghi đủ 2 dòng (không phải store canonical)
    assert len((tmp_path / "a.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    # GET đọc từ store canonical ⇒ 1 hàng
    rows = client.get("/api/v1/advice/actions").json()["actions"]
    assert len(rows) == 1 and rows[0]["advice_id"] == BODY["advice_id"]


def test_changing_mind_is_three_events_not_two(tmp_path, monkeypatch):
    """R-07 (soi đối kháng vòng 2): bug F-3 được KỂ trong docstring đầu file nhưng KHÔNG có
    test nào tái hiện — revert nguyên xi bản fix đó thì cả file vẫn xanh.

    Bug: khoá idempotency theo `at_min` (hằng số theo loại card ở `cards.js`) ⇒ cửa sổ
    dedupe là CẢ NGÀY ⇒ "Làm theo → đổi ý Bỏ qua → Làm theo lại" bị nuốt còn 2 event và
    nhật ký hiện NGƯỢC hành động cuối. Fix hiện hành khoá theo GIÂY quan sát."""
    _patch(tmp_path, monkeypatch)

    # Đồng hồ phải NHÍCH giữa các lần bấm. Bản đầu của test này gọi 3 POST trong cùng một
    # giây và đỏ với 2 event — nhưng đó là hành vi ĐÚNG: trong một giây, ba cú bấm là
    # double-click, và thiết kế CÓ Ý gộp chúng. "Đổi ý" là hành vi của người thật qua vài
    # giây, nên test phải dựng đúng thang thời gian đó.
    class _Clock(datetime):
        n = 0

        @classmethod
        def now(cls, tz=None):
            cls.n += 1
            return cls(2026, 7, 29, 14, 0, cls.n, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(advice_router, "datetime", _Clock)
    for act in ("followed", "dismissed", "followed"):
        assert client.post("/api/v1/advice/action",
                           json={**BODY, "action": act}).status_code == 200
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        evs = log.events(decision_id=BODY["advice_id"])
    assert len(evs) == 3, f"đổi ý phải là 3 event, nhận {len(evs)} ⇒ dedupe quá rộng"
    rows = client.get("/api/v1/advice/actions").json()["actions"]
    assert rows[0]["action"] == "followed", "nhật ký phải hiện hành động CUỐI CÙNG"

    # Mặt đối chứng: CÙNG một giây thì vẫn phải gộp (không nới dedupe khi sửa test này).
    _Clock.n = 100
    monkeypatch.setattr(_Clock, "now", classmethod(
        lambda cls, tz=None: cls(2026, 7, 29, 15, 0, 0, tzinfo=tz or timezone.utc)))
    for _ in range(2):
        client.post("/api/v1/advice/action", json={**BODY, "action": "dismissed"})
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        n_dis = len([e for e in log.events(decision_id=BODY["advice_id"])
                     if e["event_type"] == "dismissed"])
    assert n_dis == 2, f"double-click cùng giây phải gộp; tổng dismissed nên là 2, nhận {n_dis}"


def test_calendar_invalid_date_rejected_422(tmp_path, monkeypatch):
    """X-1 (batch 2): `2026-02-31` qua regex `\\d{2}` nhưng không tồn tại trên lịch —
    trước sửa: HTTP 200, record độc persist VĨNH VIỄN (store append-only) rồi giết mọi
    decision_state về sau. Router phải chặn 422 TRƯỚC store."""
    _patch(tmp_path, monkeypatch)
    for bad in ("2026-02-31", "2026-13-01", "2026-00-10"):
        r = client.post("/api/v1/advice/action", json={**BODY, "date": bad})
        assert r.status_code == 422, (bad, r.status_code)
    assert not (tmp_path / "advice_lifecycle.db").exists() or not AdviceEventLog(
        tmp_path / "advice_lifecycle.db").events()
    assert not (tmp_path / "a.jsonl").exists(), "JSONL cũng không được ghi (F-8)"


def test_empty_ids_rejected_422(tmp_path, monkeypatch):
    """X-6: advice_id/driver_id rỗng từng đi xuyên tới store rồi nổ HTTP 500 —
    boundary validate phải đối xứng (422 tại pydantic như date/at_min)."""
    _patch(tmp_path, monkeypatch)
    assert client.post("/api/v1/advice/action",
                       json={**BODY, "advice_id": ""}).status_code == 422
    assert client.post("/api/v1/advice/action",
                       json={**BODY, "driver_id": ""}).status_code == 422


def test_dismiss_and_expand_map_to_lifecycle(tmp_path, monkeypatch):
    _patch(tmp_path, monkeypatch)
    for action, expected in (("dismissed", "dismissed"), ("expanded", "displayed")):
        body = {**BODY, "action": action}
        assert client.post("/api/v1/advice/action", json=body).status_code == 200
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        types = {e["event_type"] for e in log.events()}
    assert types == {"dismissed", "displayed"}
    # dismiss mang reason_code typed (nguyên liệu cho cadence memory ĐA-04)
    with AdviceEventLog(tmp_path / "advice_lifecycle.db") as log:
        dis = [e for e in log.events() if e["event_type"] == "dismissed"]
    assert dis[0]["reason_code"] == "dismissed_for_window"


# ---------- ĐA-04: vòng adherence KÍN VỀ HÀNH VI (nút Bỏ qua đổi advisor) ----------

def test_dismiss_silences_same_topic_in_phase(tmp_path, monkeypatch):
    """Trước ĐA-04: GET /advice stateless — bấm "Bỏ qua" xong hỏi lại vẫn ra card y hệt
    (vòng §12 HỞ về hành vi). Nay: im trong PHA đó (Cường chốt cửa sổ = hết pha)."""
    _patch(tmp_path, monkeypatch)
    q = "?driver_id=driver-01&date=2026-07-29&now_min=600&topic=brief"
    first = client.get("/api/v1/advice" + q).json()
    assert first["cadence"]["verdict"] == "PRESENT"

    assert client.post("/api/v1/advice/action", json={
        **BODY, "action": "dismissed", "at_min": 600, "topic": "brief"}).status_code == 200

    after = client.get("/api/v1/advice" + q).json()
    assert after["items"] == []
    assert after["silent"]["reason_code"] == "dismissed_for_window"
    assert after["silent"]["message"]          # nói tử tế, không đổ lỗi


def test_dismiss_does_not_silence_other_topic(tmp_path, monkeypatch):
    """Bỏ qua nhắc thưởng KHÔNG được khoá miệng cảnh báo chủ đề khác (cooldown theo topic)."""
    _patch(tmp_path, monkeypatch)
    client.post("/api/v1/advice/action", json={
        **BODY, "action": "dismissed", "at_min": 600, "topic": "brief"})
    other = client.get(
        # `rest` (topic bịa) → `nudge` (topic THẬT, được đo): boundary nay fail-closed với topic
        # chưa phân loại. Ý định của test không đổi — chứng minh cooldown theo TỪNG chủ đề.
        # ⚠ Cố ý KHÔNG khai `rest` vào registry: nhắc nghỉ ở sản phẩm phải dùng đúng một tên
        # (`rest_nudge`), và để `rest` ở trạng thái "chưa phân loại" thì ai dùng nó sẽ nhận 422 và
        # buộc phải quyết định — thay vì im lặng rơi vào nhóm được đo.
        "/api/v1/advice?driver_id=driver-01&date=2026-07-29&now_min=600&topic=nudge").json()
    assert other["cadence"]["verdict"] == "PRESENT"


def test_dismiss_expires_next_phase(tmp_path, monkeypatch):
    """Sang PHA mới được nói lại — không im hết ca (giữ đường cho cảnh báo thật)."""
    _patch(tmp_path, monkeypatch)
    client.post("/api/v1/advice/action", json={
        **BODY, "action": "dismissed", "at_min": 600, "topic": "brief"})
    late = client.get(
        "/api/v1/advice?driver_id=driver-01&date=2026-07-29&now_min=1200&topic=brief").json()
    assert late["cadence"]["phase"] != "mid"
    assert late["cadence"]["verdict"] == "PRESENT"


def test_showing_a_card_consumes_budget_without_any_tap(tmp_path, monkeypatch):
    """F1: ngân sách phải hao khi advisor NÓI, không phải khi tài xế BẤM.

    Lỗ hổng cũ: `GET /advice` trả card mà không ghi event nào ⇒ tài xế phớt lờ 20 thẻ thì
    ngân sách không hao ⇒ advisor nói mãi. Sim thì `cadence_note_spoken` ngay khi nói —
    tức "một luật" hở đúng ở ĐƠN VỊ ĐẾM (lời nói vs cú bấm)."""
    _patch(tmp_path, monkeypatch)
    # Dùng tài xế MẶC ĐỊNH (d-19) — `driver-01` của BODY không được kênh nào phủ nên GET
    # luôn trả `no_active_channel` + items rỗng, và một test dựng trên đó sẽ XANH GIẢ.
    q = "/api/v1/advice?topic=brief&now_min="
    seen = [client.get(q + str(m)).json() for m in (600, 630, 660, 690, 720, 750, 780)]
    assert any(r.get("items") for r in seen), "kịch bản phải sinh card thật, không thì test rỗng"
    reasons = [r.get("silent", {}).get("reason_code") for r in seen]
    assert "shift_budget_exhausted" in reasons, (
        f"7 lần NÓI mà ngân sách 6/ca không cạn ⇒ F1 sống lại: {reasons}")


def test_polling_same_bucket_does_not_burn_budget(tmp_path, monkeypatch):
    """Mặt kia của F1: client refresh liên tục trong CÙNG bucket 30′ chỉ là MỘT lần nói.

    Nếu khoá event theo `advice_id` (mang `now_min`) thì đồng hồ nhích một phút đã thành
    "lời khuyên mới" và đốt hết ngân sách trong vài giây — nên khoá theo decision bucket."""
    _patch(tmp_path, monkeypatch)
    dv = client.get("/api/v1/driver/default-view").json()
    for m in range(600, 630, 2):        # 15 lần trong CÙNG bucket 30′
        r = client.get(f"/api/v1/advice?topic=brief&now_min={m}").json()
    # ⚠ Kỳ vọng đổi PRESENT → SUPPRESS ngày 2026-07-31 (UPDATE-112, V-21). Bản cũ pin ĐÚNG
    # LỖI `L4-03`: cooldown 20′ ngắn hơn bucket 30′ nên ở phút 620–628 verdict quay lại
    # PRESENT — card hiện lại thật — trong khi `_note_shown` khoá theo bucket nên KHÔNG ghi
    # event và KHÔNG đốt ngân sách. Tức "một lời khuyên miễn phí". Nay cooldown = bucket
    # (`effective_gap_min`) ⇒ trong cùng bucket luôn SUPPRESS, nhất quán với việc không ghi.
    assert r["cadence"]["verdict"] == "SUPPRESS", "trong cùng bucket phải im, không nói lại"
    mem = advice_router._cadence_memory(dv["driver_id"], dv["date"])
    assert mem.proactive_count == 1, f"15 lần poll = 1 lần nói, nhận {mem.proactive_count}"


def test_phase_uses_one_formula_across_write_and_read(tmp_path, monkeypatch):
    """F4: pha ca phải tính bằng MỘT công thức. Trước đây POST lưu pha tính với
    `DEFAULT_SHIFT_END_MIN` cứng 22:00 còn GET tính với `shift_end_min` từ query ⇒ với ca
    kết thúc sớm (18:00) hai bên cho hai pha khác nhau cho cùng một phút.

    Kịch bản: ca 06:00–18:00 (720′). Bỏ qua lúc 10:00 → elapsed 240/720 = 0,33 ⇒ pha `mid`
    theo công thức của người ĐỌC. Hỏi lại lúc 11:00 (elapsed 300/720 = 0,42, vẫn `mid`) ⇒
    phải IM. Nếu đọc `payload["phase"]` (tính theo ca 22:00: 240/960 = 0,25 ⇒ cũng mid...
    nhưng lúc 11:00 GET tính 300/720=0,42 mid vs 300/960=0,31 mid) — nên dùng mốc gắt hơn:
    16:00 (elapsed 600/720 = 0,83 ⇒ `late` theo ca thật, còn theo ca mặc định 600/960 =
    0,63 ⇒ `mid`). Hai công thức cho hai kết luận khác nhau tại đúng phút này."""
    _patch(tmp_path, monkeypatch)
    SHIFT_END = 18 * 60
    assert client.post("/api/v1/advice/action", json={
        **BODY, "action": "dismissed", "at_min": 16 * 60, "topic": "brief"}).status_code == 200
    r = client.get(f"/api/v1/advice?driver_id=driver-01&date=2026-07-29"
                   f"&now_min={16 * 60 + 30}&shift_end_min={SHIFT_END}&topic=brief").json()
    assert r["cadence"]["phase"] == "late"
    assert r["silent"]["reason_code"] == "dismissed_for_window", (
        "pha của event dismissed phải được tính lại bằng công thức của người ĐỌC "
        f"(ca 06:00–18:00 ⇒ late), không dùng pha đã lưu: {r}")


def test_budget_counts_decisions_not_events(tmp_path, monkeypatch):
    """Ngân sách đếm QUYẾT ĐỊNH, không đếm EVENT.

    Bug tự bắt (lộ ra khi thiết kế D-ĐA04-03): một card "Vì sao"(displayed) rồi
    "Làm theo"(followed) từng tiêu HAI suất — 3 card là advisor im cả ngày. Đúng họ lỗi
    decision-vs-event mà Cycle W đã trả giá 4 lượt review."""
    _patch(tmp_path, monkeypatch)
    # UPDATE-135: dùng topic THẬT thay cho `f"topic-{i}"` bịa. Boundary nay từ chối topic chưa
    # phân loại (fail-closed — một topic lạ sẽ im lặng rơi vào nhóm ĐƯỢC ĐO, và nếu nó thực ra là
    # khuyên mềm thì ta vừa tạo một thước nghe-lời cho lời khuyên sức khoẻ). Đổi này làm test
    # MẠNH hơn: nó chứng minh việc đếm ngân sách đúng trên **từ vựng topic thật**, chứ không phải
    # trên ba chuỗi không bao giờ tồn tại.
    for i, topic in enumerate(("brief", "nudge", "recap")):   # 3 card × (expanded+followed)
        aid = f"s1-driver-01-2026-07-29-{600 + i}"
        for act in ("expanded", "followed"):
            assert client.post("/api/v1/advice/action", json={
                **BODY, "advice_id": aid, "action": act, "at_min": 600 + i,
                "topic": topic}).status_code == 200
    mem = advice_router._cadence_memory("driver-01", "2026-07-29")
    assert mem.proactive_count == 3, (
        f"3 card phải = 3 suất, không phải {mem.proactive_count} (đếm event = double-count)")
    # và ngân sách 6 CHƯA cạn — advisor vẫn được nói
    r = client.get("/api/v1/advice?driver_id=driver-01&date=2026-07-29"
                   "&now_min=700&topic=brief").json()
    assert r["cadence"]["verdict"] == "PRESENT"


def test_topic_cooldown_alive_in_product(tmp_path, monkeypatch):
    """Cooldown 20′/chủ đề phải chạy Ở SẢN PHẨM, không chỉ ở sim.

    Bug tự bắt trong cycle này: `_cadence_memory` quên nuôi `last_decided_min` ⇒ nhánh
    `topic_cooldown` chết ở UI trong khi `_SILENT_MSG` vẫn có câu cho nó. Nửa UI im lặng
    không chạy = "một luật" chỉ đúng một nửa."""
    _patch(tmp_path, monkeypatch)
    assert client.post("/api/v1/advice/action", json={
        **BODY, "action": "expanded", "at_min": 600, "topic": "brief"}).status_code == 200

    soon = client.get("/api/v1/advice?driver_id=driver-01&date=2026-07-29"
                      "&now_min=610&topic=brief").json()
    assert soon["cadence"]["verdict"] == "SUPPRESS"
    assert soon["silent"]["reason_code"] == "topic_cooldown"
    # 620 → 630 (UPDATE-112, V-21): cooldown thực thi = max(20′ cấu hình, 30′ bucket quyết
    # định). Nói lại TRONG cùng bucket là lặp lại chính mình và event bị store dedupe (L4-03).
    assert soon["cadence"]["next_eligible_min"] == 630.0

    later = client.get("/api/v1/advice?driver_id=driver-01&date=2026-07-29"
                       "&now_min=630&topic=brief").json()
    assert later["cadence"]["verdict"] == "PRESENT", "sang bucket mới phải được nói lại"


def test_shift_budget_exhausted_silences_ui(tmp_path, monkeypatch):
    """Ngân sách ca ở SẢN PHẨM: sau 6 lần trợ lý chủ động nói, lần thứ 7 phải IM.

    Đây là nửa UI của cùng luật mà sim dùng — memory dựng từ event log thay vì RAM, nhưng
    gọi cùng `cadence.evaluate`. Không có test này thì "một luật" chỉ đúng ở sim."""
    _patch(tmp_path, monkeypatch)
    # 6 topic THẬT khác nhau (xem ghi chú UPDATE-135 ở test trên). KHÔNG dùng `bonus` trong vòng
    # lặp: lượt GET cuối hỏi `topic=bonus` và phải im vì **ngân sách ca** cạn — nếu `bonus` cũng
    # nằm trong vòng thì `topic_cooldown` bắn trước và test đo sai cơ chế.
    # HỢP NHẤT PR #4: bản của tôi dùng 6 topic PHÂN BIỆT (`positioning`/`accept_lift`/…) — nhưng
    # bề mặt POST hẹp lại chỉ còn topic client + khuyên mềm, và đó là ĐÚNG: kênh SIM không có việc
    # gì trên HTTP API. Lấy bản của Khánh (xoay 3 topic client). Ý định test không đổi — ngân sách
    # đếm theo QUYẾT ĐỊNH, và 6 lần nói phải cạn suất; `topic_cooldown` không xen vào vì đây là
    # POST (nhịp chỉ gác đường GET).
    for i, topic in enumerate(("brief", "nudge", "recap") * 2):
        # `expanded` → event `displayed`, tức advisor đã hiện thẻ cho tài xế xem
        assert client.post("/api/v1/advice/action", json={
            **BODY, "advice_id": f"s1-driver-01-2026-07-29-{600 + i}", "action": "expanded",
            "at_min": 600 + i, "topic": topic}).status_code == 200
    r = client.get("/api/v1/advice?driver_id=driver-01&date=2026-07-29"
                   "&now_min=700&topic=brief").json()
    assert r["items"] == []
    assert r["silent"]["reason_code"] == "shift_budget_exhausted"
    assert "nhắc đủ" in r["silent"]["message"]


def test_driving_queues_advice(tmp_path, monkeypatch):
    """An toàn: đang lái ⇒ HOÃN (QUEUE), không mất lời khuyên."""
    _patch(tmp_path, monkeypatch)
    r = client.get("/api/v1/advice?driver_id=driver-01&date=2026-07-29"
                   "&now_min=600&topic=brief&is_driving=true").json()
    assert r["cadence"]["verdict"] == "QUEUE"
    assert r["silent"]["reason_code"] == "unsafe_while_moving"
