"""CỔNG boundary: `POST /advice/action` từ chối `followed` cho KHUYÊN MỀM.

Quyết định Cường 2026-08-03 → `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`.

Tầng thứ hai của cùng một ranh giới: `tests/test_advice_topic_registry.py` canh đường ĐỌC
(`adherence_view` không được có mẫu số cho topic mềm), file này canh đường GHI (không được ghi
`followed` vào store ngay từ đầu). Hai tầng vì một tầng thôi thì tầng kia vẫn thủng — đúng lý do
`L4-07` đã phải chặn cả ở `cards.js` lẫn ở boundary: client cũ, `curl`, và app Flutter khác bản
đều gọi được endpoint này.

Vì sao `dismissed` VẪN nhận: nó mang nghĩa *"đừng nhắc nữa trong pha này"* (nhịp nói ĐA-04, thứ
giữ cho advisor không làm phiền) — không phải *"tôi không đồng ý"*. Cùng một cú bấm, hai vai; chỉ
vai thứ hai bị cấm. Cường chốt nguyên văn: *"Giữ nút ẩn, bỏ nút Làm theo"*.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT / "ui/backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "ui/backend"))

from app.main import app  # noqa: E402
from app.routers import advice as advice_router  # noqa: E402
from gsm_core.lifecycle.advice_topics import MEASURED_TOPICS, SOFT_TOPICS  # noqa: E402

client = TestClient(app)

# `advice_id` phải thuộc namespace solver thật, nếu không L4-07 chặn trước và ta sẽ đo sai lý do
# 422 (đúng bẫy đã sập ở D-M3-17: test đỏ vì lý do khác cái mình nghĩ).
BODY = {"advice_id": "s7-rest-2026-08-03", "driver_id": "d-1", "date": "2026-08-03",
        "card_kind": "nudge", "at_min": 14 * 60}


@pytest.fixture(autouse=True)
def _co_lap_store(tmp_path, monkeypatch):
    """Cô lập store telemetry — soi độc lập 2026-08-03 bắt được bản đầu **ghi vào
    `data/ui-telemetry` THẬT**.

    Hai cái giá của việc không cô lập, cả hai đều làm cổng yếu đi mà vẫn xanh:
    1. Test làm bẩn dữ liệu dev, và kết quả phụ thuộc thứ tự chạy;
    2. tệ hơn — trên một store đã bẩn, nhịp nói (`cadence`) có thể NÉN mọi lượt GET ⇒ assert
       *"đường được đo vẫn có mẫu số"* đi qua **nhánh im lặng** và không còn chứng minh gì.
       Tức cổng vẫn xanh nhưng vì lý do khác cái nó tuyên bố — đúng bẫy #2 của repo.

    Dùng cùng khuôn `_patch` của `test_lifecycle_actions.py` (`TELEMETRY_DIR` + `ACTIONS_FILE`).
    """
    monkeypatch.setattr(advice_router, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_router, "ACTIONS_FILE", tmp_path / "a.jsonl")


@pytest.mark.parametrize("topic", sorted(SOFT_TOPICS))
def test_khuyen_mem_KHONG_nhan_followed(topic):
    r = client.post("/api/v1/advice/action", json={**BODY, "action": "followed", "topic": topic})
    assert r.status_code == 422, (
        f"topic mềm {topic!r} vẫn ghi được 'followed' (HTTP {r.status_code}) ⇒ hệ thống đang "
        f"tạo thước nghe-lời cho lời khuyên sức khoẻ")
    assert "KHUYÊN MỀM" in r.text, r.text[:400]


@pytest.mark.parametrize("topic", sorted(SOFT_TOPICS))
def test_khuyen_mem_VAN_nhan_dismissed(topic):
    """`dismissed` = 'đừng nhắc nữa' — phải sống, không thì tài xế mất cách tắt thẻ phiền.

    🔴 `N6` — bản đầu chỉ assert **HTTP 200**. Soi độc lập tiêm `AdviceEventLog.append` thành no-op
    (kịch bản thật: ai đó đọc ranh giới là *"không lưu trace khuyên mềm"* rồi ném cả `dismissed`)
    ⇒ endpoint vẫn trả 200 và cổng **vẫn xanh 51/51**, trong khi nhịp nói đã chết — tài xế bấm Ẩn
    mà thẻ vẫn hiện lại.

    Nay assert **HÀNH VI**: event phải THẬT SỰ vào store. Fixture `autouse` đã cô lập nên đọc lại
    rẻ và tất định."""
    aid = f"s7-{topic}-2026-08-03"
    r = client.post("/api/v1/advice/action",
                    json={**BODY, "advice_id": aid, "action": "dismissed", "topic": topic})
    assert r.status_code == 200, r.text[:400]

    from gsm_core.lifecycle.event_log import AdviceEventLog
    with AdviceEventLog(advice_router._lifecycle_db()) as log:
        evs = [e for e in log.events()
               if e["decision_id"] == aid and e["event_type"] == "dismissed"]
    assert evs, (
        f"POST trả 200 nhưng KHÔNG có event `dismissed` nào vào store cho topic {topic!r} ⇒ nhịp "
        f"nói chết: tài xế bấm Ẩn mà thẻ vẫn hiện lại. HTTP 200 không chứng minh đã ghi.")
    assert (evs[0].get("payload") or {}).get("topic") == topic, evs[0]
    assert evs[0]["reason_code"] == "dismissed_for_window", (
        "thiếu `reason_code` ⇒ `cadence` không biết đây là lệnh im trong pha")


@pytest.mark.parametrize("topic", sorted(SOFT_TOPICS))
def test_khuyen_mem_VAN_nhan_expanded(topic):
    """"Vì sao" phải sống: khuyên mềm vẫn cần giải thích được, chỉ không được đo sự đồng thuận."""
    r = client.post("/api/v1/advice/action", json={**BODY, "action": "expanded", "topic": topic})
    assert r.status_code == 200, r.text[:400]


def test_topic_DUOC_DO_van_nhan_followed():
    """Đối chứng — cổng không được chặn cả kênh kinh tế cho tiện. Nếu test này đỏ thì vòng đo
    adherence của sản phẩm đã bị phá, tệ hơn hẳn lỗi đang sửa."""
    r = client.post("/api/v1/advice/action",
                    json={**BODY, "action": "followed", "topic": "nudge"})
    assert r.status_code == 200, r.text[:400]


@pytest.mark.parametrize("topic,mem", [("weather", True), ("rest_nudge", True), ("nudge", False)])
def test_GET_actions_mang_topic_va_co_mem_ra_toi_UI(topic, mem):
    """🔴 Nợ do soi độc lập bắt (2026-08-03) — và nó là lỗi **cycle này tự tạo**.

    UPDATE-128 sửa `ui/web/index.html` để **HỨA** rằng khối *"Nhật ký làm-theo"* phân biệt khuyên
    mềm (*"chỉ có nút Ẩn, và cú bấm đó chỉ nghĩa đừng nhắc nữa"*). Nhưng `GET /advice/actions`
    **bỏ rơi `topic`** khi dựng row ⇒ UI **không có dữ liệu** để phân biệt. Tức tôi viết một lời hứa
    vào UI mà không nối đường dữ liệu cho nó — đúng họ lỗi *"tài liệu quảng cáo cơ chế không có
    đường chạy"* mà **chính cycle này dựng cổng để chặn**.

    Đây là test HÀNH VI (gọi thật POST rồi GET, kiểm dữ liệu đi hết đường), không phải test từ vựng
    — vì hai cổng `test_cards_js_*` đã bị soi độc lập chỉ ra là đo từ vựng."""
    aid = "s1-d-1-2026-08-03-840"
    assert client.post("/api/v1/advice/action", json={
        **BODY, "advice_id": aid, "action": "dismissed", "topic": topic}).status_code == 200

    r = client.get("/api/v1/advice/actions", params={"driver_id": "d-1"})
    assert r.status_code == 200, r.text[:300]
    rows = [a for a in r.json()["actions"] if a["advice_id"] == aid]
    assert rows, f"POST xong mà GET /actions không thấy bản ghi nào cho {aid}"
    a = rows[0]
    assert a.get("topic") == topic, (
        f"`GET /actions` không mang `topic` ra ({a.get('topic')!r}) ⇒ UI không thể phân biệt "
        f"khuyên mềm với lời khuyên được đo, dù `index.html` đã hứa là phân biệt được")
    assert a.get("is_soft_advice") is mem, (
        f"cờ `is_soft_advice` sai cho topic {topic!r}: {a.get('is_soft_advice')!r}")


def test_app_js_dung_co_mem_khi_ve_nhat_ky():
    """Tầng client của cùng lời hứa. Yếu hơn test hành vi (repo không có runner JS) — ghi rõ."""
    code = (ROOT / "ui/web/js/app.js").read_text(encoding="utf-8")
    code = re.sub(r"//.*$", "", code, flags=re.M)
    assert "is_soft_advice" in code, (
        "`app.js` không đọc `is_soft_advice` ⇒ nhật ký vẫn hiện 'Bỏ qua' cho thẻ mềm, và người đọc "
        "sẽ hiểu thành 'tài xế không đồng ý' — đúng vai-2 mà ranh giới cấm")


# ---------- BỀ MẶT GET: client KHÔNG khai được topic mềm (hợp nhất PR #4) ----------

@pytest.mark.parametrize("topic", ["brief", "nudge", "recap"])
def test_GET_advice_tra_co_is_soft_advice(topic):
    """Server phải TRẢ LỜI 'thẻ này có phải khuyên mềm không' — client không tự suy.

    ⚠ Viết lại khi hợp nhất PR #4. Bản đầu cho client hỏi `?topic=weather` rồi kiểm cờ trả về —
    nhưng đó CHÍNH LÀ lỗ `F1`: cờ đạo đức suy từ thứ client chọn. Khánh siết bề mặt GET còn ba
    topic client (*"safety priority không do client khai"*), tức **bỏ hẳn quyền khai đó** — một
    cách vá tốt hơn cách của tôi. Nay cờ luôn `False` ở GET vì chưa có nguồn sinh khuyên mềm; khi
    có, SERVER đặt nó theo NỘI DUNG thẻ."""
    r = client.get("/api/v1/advice", params={"topic": topic, "now_min": 14 * 60})
    assert r.status_code == 200, r.text[:300]
    b = r.json()
    assert b.get("is_soft_advice") is False, b.get("is_soft_advice")
    assert b.get("topic") == topic, "server phải vọng lại topic để client khỏi đoán"


@pytest.mark.parametrize("topic", sorted(SOFT_TOPICS))
def test_GET_KHONG_cho_client_khai_topic_MEM(topic):
    """🔴 Bảo đảm MẠNH HƠN bản đầu của tôi: client **không khai được** topic mềm ở GET.

    Bản đầu trả `items=[] + silent.no_soft_producer` — tức vẫn để client khai rồi mới từ chối
    nội dung. Bề mặt hẹp chặn ở pydantic, nên không thể dán nhãn 'khuyên mềm' lên một thẻ kinh tế
    bằng một GET (lỗ `F1`)."""
    assert client.get("/api/v1/advice",
                      params={"topic": topic, "now_min": 840}).status_code == 422


def test_GET_tu_choi_topic_KHONG_thuoc_be_mat():
    """Khánh: *"V1 chỉ nhận ba legacy surface"*. `bonus` là mặc định LỊCH SỬ, `positioning` là kênh
    SIM — không client nào được khai chúng qua HTTP."""
    for t in ("bonus", "positioning", "rest_window", "mot_topic_la"):
        assert client.get("/api/v1/advice",
                          params={"topic": t, "now_min": 840}).status_code == 422, t


def test_POST_be_mat_RONG_HON_GET_va_phai_vay():
    """POST báo hành động trên thẻ **server đã đưa** — thẻ đó có thể là khuyên mềm. Chặn `weather`
    ở pydantic sẽ làm `dismissed` (nút Ẩn) bất khả ⇒ tài xế mất cách tắt thẻ phiền, phá đúng điều
    Cường chốt. Nên POST rộng hơn GET, và ranh giới `followed` do validator NGỮ NGHĨA giữ."""
    r = client.post("/api/v1/advice/action",
                    json={**BODY, "action": "dismissed", "topic": "weather"})
    assert r.status_code == 200, r.text[:300]
    r2 = client.post("/api/v1/advice/action",
                     json={**BODY, "action": "followed", "topic": "weather"})
    assert r2.status_code == 422 and "KHUYÊN MỀM" in r2.text, r2.text[:300]


@pytest.mark.parametrize("topic", ["brief", "nudge", "recap"])
def test_MOI_nhanh_cua_GET_advice_deu_KHOP_contract(topic):
    """Vi phạm contract **có từ TRƯỚC** UPDATE-128: nhánh IM LẶNG thiếu cả ba field
    `scenario_id`/`seed`/`data_mode` mà `ui/contracts/advice.json` khai `required`. Khánh và tôi
    độc lập tìm ra và sửa hai cách (đã đo: cùng cho seed 7000). Cổng này quét **mọi nhánh** bằng
    chính schema trong repo — không phải danh sách field tôi tự nhớ."""
    import json

    import jsonschema

    sch = json.loads((ROOT / "ui/contracts/advice.json").read_text(encoding="utf-8"))
    r = client.get("/api/v1/advice", params={"topic": topic, "now_min": 14 * 60})
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    thieu = [k for k in sch.get("required", []) if k not in body]
    assert not thieu, f"topic={topic!r}: thiếu field `required`: {thieu}; có: {sorted(body)}"
    jsonschema.validate(body, sch)


def _cards_js_khong_comment() -> str:
    """`cards.js` đã BỎ hết comment — cổng dưới đây không được thoả mãn bằng một dòng chú thích.

    Bản đầu của cổng này chỉ làm `"is_soft_advice" in src`, và soi độc lập gọi đúng nó là **cổng
    trang trí**: nó XANH kể cả khi `cards.js` không còn một chỗ nào THỰC SỰ đọc `a.is_soft_advice`,
    bởi chính đoạn comment dài giải thích cờ đó đã chứa chuỗi ấy. Đúng bẫy #2 của repo — test khắc
    lời giải thích thành bằng chứng.
    """
    src = (ROOT / "ui/web/js/cards.js").read_text(encoding="utf-8")
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)          # block comment
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in src.splitlines())


def test_cards_js_THUC_SU_doc_co_cua_server():
    """Phải có lời gọi/đọc thật `a.is_soft_advice`, không phải chỉ nhắc tên nó trong chú thích.

    🔴 **Bản đầu của cổng này là TRANG TRÍ về hành vi — chứng minh bằng sever-restore THẬT
    (2026-08-03):** tiêm lỗi bỏ `isSoft` khỏi phép tính `mode` trong `cards.js` ⇒ thẻ mềm hiện lại
    nút "Làm theo", mà **29/29 test vẫn XANH**. Soi độc lập đã cảnh báo đúng chỗ này, và tôi chỉ
    tin sau khi tự tiêm.

    Vì sao bản đầu hở: nó chỉ đòi ba CHUỖI tồn tại **ở đâu đó** trong file (`is_soft_advice`,
    `'soft'`, `isSoft`) — mà cả ba vẫn còn sau mutation (chúng nằm ở tham số hàm, ở nhánh render,
    ở `logAction`). Đòi "chuỗi tồn tại" không bao giờ chặn được "chuỗi bị bỏ khỏi ĐÚNG một biểu
    thức".

    Nay neo vào **chính biểu thức quyết định chế độ**. ⚠ Vẫn là cổng trên VĂN BẢN NGUỒN, không phải
    test hành vi — repo không có runner JS. Nói rõ giới hạn đó ở đây thay vì để người đọc tưởng nó
    mạnh hơn; fix thật cần jsdom/node và là một quyết định hạ tầng (ghi ở UPDATE-128 §7d)."""
    code = _cards_js_khong_comment()
    assert re.search(r"\bis_soft_advice\b", code), (
        "`cards.js` KHÔNG còn chỗ nào (ngoài chú thích) đọc `is_soft_advice` ⇒ client lại tự "
        "quyết thẻ nào là mềm, hoặc mất luôn chế độ soft")
    assert re.search(r'["\']soft["\']', code), "chưa có chế độ render `soft` trong CODE"
    # 🔒 Neo vào PHÉP TÍNH `mode`: `isSoft` phải xuất hiện trong CHÍNH biểu thức gán `mode`.
    # Đây là chỗ mutation (f) tấn công, và là chỗ duy nhất quyết định thẻ mềm có nút "Làm theo".
    m = re.search(r"const\s+mode\s*=\s*([^;]+);", code)
    assert m, "không tìm thấy phép tính `const mode = …` trong cards.js"
    assert "isSoft" in m.group(1), (
        f"phép tính chế độ render KHÔNG dùng `isSoft`: `{m.group(1).strip()[:90]}` ⇒ thẻ khuyên "
        f"mềm sẽ rơi vào nhánh `actionable` và hiện nút 'Làm theo'. Đây chính là mutation mà "
        f"sever-restore 2026-08-03 chứng minh bản cổng đầu KHÔNG bắt được.")
    # và `soft` phải là một nhánh THẬT của biểu thức đó, không phải chuỗi ở nơi khác
    assert re.search(r'["\']soft["\']', m.group(1)), (
        f"biểu thức mode không có nhánh 'soft': `{m.group(1).strip()[:90]}`")


def test_cards_js_KHONG_chep_lai_danh_sach_topic_mem():
    """Chặn tái phát nguồn sự thật thứ hai — quét trên CODE, và bắt mọi cách chép, không chỉ
    `new Set([...])` như bản đầu (soi độc lập: *"thoả mãn được bằng một cách viết khác"*)."""
    code = _cards_js_khong_comment()
    xau = [t for t in sorted(SOFT_TOPICS) if re.search(rf'["\']{re.escape(t)}["\']', code)]
    assert not xau, (
        f"`cards.js` lại nhắc tên topic mềm {xau} trong CODE ⇒ nguồn sự thật thứ hai cho một ranh "
        f"giới đạo đức (họ lỗi D-M3-17). Client chỉ được đọc `is_soft_advice` từ server.")
