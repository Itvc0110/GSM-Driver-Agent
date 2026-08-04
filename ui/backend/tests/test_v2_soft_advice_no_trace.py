"""🔴 CỔNG — đường ghi THỨ TƯ: AdviceCheckpoint v2 không được ghi trace ĐỒNG Ý cho khuyên mềm.

QĐ-4 (Cường chốt 2026-08-04) → `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` §6b.

## Lỗ này tìm ra thế nào, và vì sao nó nguy hiểm hơn một con số sai

Ranh giới *"khuyên mềm KHÔNG đo"* (QĐ-1) được thi hành bằng `classify()` trên registry, phủ **ba**
đường ghi: UI v1 · sim · pipeline. Đọc lại logic sau khi rebase PR #4 thì lộ ra **đường thứ TƯ** —
v2 checkpoint — nằm hoàn toàn ngoài, vì ba lý do độc lập:

1. **store riêng** — `advice_checkpoint.py` ghi nguyên văn *"independent from the legacy v1
   lifecycle store"*; v2 ghi vào `CheckpointStore`, còn ranh giới sống ở `AdviceEventLog`;
2. **từ vựng topic riêng**, giao với registry = **RỖNG**;
3. `rest` **được sinh thật** — `checkpoint.py:134`: `if solver == "S7" or code == "REST"`.

⇒ Đo được 2026-08-04: một checkpoint `rest` nhận `response: accepted` ⇒ **trace đồng ý cho lời
khuyên NGHỈ đang được ghi**. Chưa sinh số sai (`adherence_view` không thấy store v2) — nhưng dữ liệu
**tích luỹ**, và ngày ai đó tính adherence trên store này thì tỷ lệ hiện ra ngay với lịch sử đầy đủ.
**Không ai phải làm gì sai thêm.** Đó là lý do nó nguy hiểm hơn một con số sai.

## Không ai cẩu thả

Hai người làm song song, **mỗi người kín phần mình** — `safety_reserved` trong từ vựng v2 cho thấy
Khánh **có** nghĩ về ranh giới an toàn, chỉ bằng một cách gọi khác. Bài học: với hai nhánh song song,
*"mỗi người kín phần mình"* **không** cộng lại thành kín.

## Vì sao có cả test HTTP lẫn test service

Test HTTP chứng minh **cả chuỗi**: card `rest` sinh thật → `POST /response` → 422 (không phải 409).
Test service chứng minh **chỗ ranh giới nằm**: mọi client khác (Flutter, `curl`, script) đều qua
`record_response`, nên nếu nó chỉ được canh ở router thì cổng hở với client thứ hai.
"""
from __future__ import annotations

import json
import pathlib
import sys

import jsonschema
import pytest
from fastapi.testclient import TestClient

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT / "ui/backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "ui/backend"))

from app.main import app  # noqa: E402
from app.services.advice_checkpoint import (  # noqa: E402
    AdviceCheckpointService, CheckpointConflictError, CheckpointSoftAdviceError)
from gsm_core.lifecycle.advice_topics import classify, is_soft  # noqa: E402

client = TestClient(app)

# Từ vựng v2 (`checkpoint.py::_topic_for_action`) thuộc lớp MỀM.
V2_MEM = ("rest", "safety_reserved")
# Cùng từ vựng đó, phần KINH TẾ — phải giữ được đo.
V2_DUOC_DO = ("bonus_eligibility", "energy", "shift_boundary", "shift_timing",
              "positioning_sim_only")


# ---------------------------------------------------------------- lớp 1: phân loại

@pytest.mark.parametrize("topic", V2_MEM)
def test_topic_MEM_cua_v2_da_nam_trong_registry(topic):
    """Điều kiện tiên quyết: topic v2 nào không có trong registry thì `classify()` trả `"unknown"`
    và **mọi** lan can bên dưới không chạm tới nó — đúng trạng thái trước QĐ-4."""
    assert is_soft(topic), (
        f"`{topic}` (từ vựng v2) chưa thuộc lớp MỀM trong registry ⇒ ranh giới hở lại ở đường v2")


@pytest.mark.parametrize("topic", V2_DUOC_DO)
def test_topic_KINH_TE_cua_v2_van_duoc_do(topic):
    """Đối chứng bắt buộc — không được xếp cả cụm v2 vào mềm cho tiện. Thế là sửa một ranh giới
    bằng cách phá một phép đo, và cái mất đi (mẫu số của kênh kinh tế) im lặng hơn hẳn."""
    assert classify(topic) == "measured"


# ---------------------------------------------------------------- lớp 2: service

class _StoreGia:
    """Chỉ đủ để đi tới ranh giới. `lease()` trả `None` ⇒ `_client_event` nổ
    `CheckpointConflictError` — ta dùng chính điều đó làm mốc *"đã đi QUA cổng mềm"*."""

    def __init__(self, topic: str):
        self.topic = topic

    def checkpoint(self, checkpoint_id):
        return {"checkpoint_id": checkpoint_id, "topic": self.topic}

    def lease(self, checkpoint_id):
        return None


def _goi(topic: str, response: str):
    svc = AdviceCheckpointService.__new__(AdviceCheckpointService)   # bỏ __init__ (mở DB thật)
    svc.store = _StoreGia(topic)
    return svc.record_response("cp-1", display_id="d1", client_event_id="c1",
                               response=response, occurred_at="2026-08-04T09:00:00+07:00")


@pytest.mark.parametrize("topic", V2_MEM)
def test_record_response_TU_CHOI_accepted_cho_topic_MEM(topic):
    """Cổng ở tầng SERVICE — nơi mọi client (web, Flutter, `curl`) đều phải đi qua."""
    with pytest.raises(CheckpointSoftAdviceError) as e:
        _goi(topic, "accepted")
    assert "KHUYÊN MỀM" in str(e.value)


@pytest.mark.parametrize("phan_hoi", ["dismissed", "expanded"])
def test_record_response_VAN_NHAN_dismissed_va_expanded(phan_hoi):
    """`dismissed` = *"đừng nhắc nữa"* (nhịp nói), KHÔNG phải *"tôi không đồng ý"* — chặn nó sẽ làm
    tài xế mất cách tắt thẻ phiền, phá đúng điều Cường chốt (*"giữ nút ẩn, bỏ nút Làm theo"*).
    `expanded` = *"cho tôi xem vì sao"*, cũng không phải sự đồng thuận. Chỉ `accepted` bị cấm: nó
    chỉ có MỘT nghĩa, và nghĩa đó là thước nghe-lời.

    `CheckpointConflictError` ở đây là **kết quả MONG ĐỢI**: nó chứng minh lời gọi đã đi QUA cổng
    mềm và chết ở lease giả — nếu cổng chặn nhầm thì lỗi sẽ là `CheckpointSoftAdviceError`."""
    with pytest.raises(CheckpointConflictError):
        _goi("rest", phan_hoi)


def test_topic_KINH_TE_van_ghi_duoc_accepted():
    """Đối chứng: ranh giới không được chặn cả kênh kinh tế. Test này đỏ ⇒ vòng đo adherence của v2
    đã bị phá — hỏng nặng hơn hẳn lỗi đang sửa."""
    with pytest.raises(CheckpointConflictError):     # KHÔNG phải CheckpointSoftAdviceError
        _goi("bonus_eligibility", "accepted")


def test_topic_CHUA_KHAI_cung_bi_tu_choi_FAIL_CLOSED():
    """Ghim một ĐÁNH ĐỔI, không để nó thành phát hiện của người sau.

    Tầng ĐỌC (`adherence_view`) loại topic chưa khai — Cường chốt 2026-08-03 *"TREO kết quả, như
    D-M3-10"*. Nếu tầng GHI lại nhận nó thì ranh giới có **hai tiêu chuẩn cho cùng một tình huống**,
    và cái lỏng hơn luôn là cái quyết định.

    Giá phải trả: một cú bấm nhận 422 khi ai đó thêm topic mà quên khai. Chấp nhận vì lỗi đó
    **thấy được**, còn cho qua là lỗi **im lặng** — và nếu topic lạ hoá ra là lời khuyên sức khoẻ
    (`fatigue`, `hydration`…) thì im lặng ấy chính là trace đồng thuận QĐ-1 cấm. Hai sai không
    cùng hạng.

    Thực tế nhánh này không tới được ở bản ship: ba cổng registry ĐỎ trước khi topic lạ kịp ra."""
    with pytest.raises(CheckpointSoftAdviceError) as e:
        _goi("mot_topic_chua_ai_khai", "accepted")
    assert "CHƯA được phân loại" in str(e.value), (
        "thông điệp phải nói đúng nguyên nhân — lẫn với thông điệp 'khuyên mềm' sẽ khiến người sửa "
        "đi phân loại lại một topic đã đúng thay vì khai topic mới")


def test_topic_chua_khai_KHONG_chan_dismissed():
    """Fail-closed chỉ áp cho `accepted`. Chặn `dismissed` của một topic chưa khai sẽ làm tài xế
    kẹt với một thẻ không tắt được — hình phạt rơi vào người không gây ra lỗi."""
    with pytest.raises(CheckpointConflictError):     # tới được lease ⇒ đã qua cổng
        _goi("mot_topic_chua_ai_khai", "dismissed")


def test_checkpoint_KHONG_TON_TAI_van_la_404_khong_bi_nuot_thanh_ranh_gioi():
    """Lỗi 'không tìm thấy' và lỗi 'không được phép' phải giữ hai thông điệp. Nếu `topic is None`
    (checkpoint không tồn tại) bị coi là 'chưa phân loại' thì client nhận 422 cho một ID sai — đọc
    log sẽ tưởng ranh giới bắn, trong khi thật ra chỉ là gõ nhầm ID."""
    from app.services.advice_checkpoint import CheckpointNotFoundError

    class _StoreRong:
        def checkpoint(self, checkpoint_id):
            return None

    svc = AdviceCheckpointService.__new__(AdviceCheckpointService)
    svc.store = _StoreRong()
    with pytest.raises(CheckpointNotFoundError):
        svc.record_response("cp-missing", display_id="d1", client_event_id="c1",
                            response="accepted", occurred_at="2026-08-04T09:00:00+07:00")


def test_be_mat_DEMO_cua_Khanh_van_di_qua_cong():
    """🔀 Kiểm sau rebase PR #5 — Khánh thêm bề mặt HTTP **thứ hai** ghi phản hồi:
    `POST /demo/sessions/{sid}/advice/{cid}/response` (`routers/demo.py`).

    Câu hỏi bắt buộc: đó có phải **đường ghi thứ NĂM** né cổng không? Đo được: **KHÔNG** —
    `DemoSessionRegistry.record_demo_response` uỷ quyền thẳng cho
    `AdviceCheckpointService.record_response`, tức đi qua đúng lan can QĐ-4.

    Cổng này ghim điều đó lại. Nếu ai đó "tối ưu" bằng cách gọi thẳng `store.append_event` trong
    `demo_session.py` thì ranh giới hở lại **im lặng** — đúng cách lỗ v2 ban đầu ra đời.

    ⚠ Giới hạn đã khai: đây là kiểm **CẤU TRÚC** (AST), không phải hành vi. Nó chứng minh *lời gọi
    tồn tại*, không chứng minh *mọi nhánh đều đi qua nó*. Kiểm hành vi đầy đủ cần dựng một demo
    session thật — ghi là việc của Khánh (`HANDOFF` §1.1c cùng vùng)."""
    import ast

    src = (ROOT / "ui/backend/app/services/demo_session.py").read_text(encoding="utf-8")
    fn = next((n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.FunctionDef) and n.name == "record_demo_response"), None)
    assert fn is not None, "`record_demo_response` đổi tên/biến mất — cổng đang canh hàm không còn"
    goi = {ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
    assert any(g.endswith("record_response") for g in goi), (
        f"bề mặt demo KHÔNG còn đi qua `record_response` (các lời gọi: {sorted(goi)}) ⇒ ranh giới "
        f"khuyên mềm hở ở đường thứ NĂM. Mọi đường ghi phản hồi phải đi qua MỘT lan can.")
    assert not any("append_event" in g for g in goi), (
        "`record_demo_response` gọi thẳng `append_event` ⇒ ghi vòng qua cổng")


def test_loi_ranh_gioi_la_LOP_RIENG_khong_phai_conflict():
    """`409 conflict` nghĩa *"trạng thái không cho phép LÚC NÀY"* — hàm ý thử lại có thể được.
    Ranh giới thì **vĩnh viễn không được phép** ⇒ `422`. Dùng lại `CheckpointConflictError` sẽ dạy
    người đọc log rằng cứ thử lại là qua — sai hẳn bản chất."""
    assert CheckpointSoftAdviceError is not CheckpointConflictError
    assert not issubclass(CheckpointSoftAdviceError, CheckpointConflictError)


# ---------------------------------------------------------------- lớp 3: HTTP đầu-cuối

class _S2RestOrchestrator:
    """Sinh một candidate `rest` qua **ĐÚNG đường mà sản phẩm đi**: S2 (`shift_dp`) trả một lịch có
    `action = "REST"` ở bucket hiện tại.

    🔴 Bản đầu của test này dùng một orchestrator giả trả `solver_set=["S7"]`. **Soi độc lập
    2026-08-04 bác bỏ**, và nó đúng — hai sự thật độc lập:

    1. **S7 KHÔNG chạy ở sản phẩm.** `ProductSolverOrchestrator` chỉ gọi `bonus_feasibility` (S1,
       `advice_checkpoint.py:176`) và `shift_dp` (S2, `:210`). S7 = `solvers/idle_reduction.py`,
       chỉ sống ở sim.
    2. **Contract CẤM tổ hợp đó**: `advice_v2.json` — `solver_set.items.enum = ["S1","S2"]`. Thẻ do
       bản cũ dựng ra là một thẻ **vi phạm schema**, và test cũ không bắt vì nó không validate.

    ⇒ Cổng cũ canh một kịch bản **không tồn tại được**, trong khi đường THẬT
    (`S2 → code "REST" → _topic_for_action → "rest"`, `checkpoint.py:134`) **không test nào phủ**.
    Đúng họ lỗi mà cả cycle này đang chống: *cơ chế bảo vệ canh một nhánh không có đường chạy*.
    Lần này tôi là người mắc.
    """

    def solve(self, driver_id, t_now, shift_start_min, shift_end_min, surface="nudge"):
        from app.services.advice_checkpoint import (ProductSolverResult,
                                                    _normalize_with_artifacts)
        snapshot = {
            "driver_id": driver_id, "surface": surface, "trigger_type": "poll",
            "observed_at": t_now,
            "freshness_deadline": "2026-08-04T09:20:00+07:00",
            "shift_end": "2026-08-04T18:00:00+07:00",
            "data_mode": "mock-realdata", "is_mock": True, "run_id": None,
        }
        # `normalize_shift_plan` lấy `schedule[0]` làm hành động HIỆN TẠI. `rest_min_per_4h` của
        # `shift_dp` là **sàn sinh lý**, nên một lịch mở đầu bằng REST là output bình thường của S2.
        report = {"confidence": 0.8, "numbers": [], "caveats": [],
                  "solution": {"schedule": [{"action": "REST"}, {"action": "ONLINE"}]}}
        candidate, artifacts = _normalize_with_artifacts(
            "S2", snapshot, {"driver_id": driver_id}, report,
            f"s2-{driver_id}-2026-08-04-540")
        return ProductSolverResult(
            candidates=[candidate], artifacts=artifacts, solver_set=["S2"])


def _the_rest(monkeypatch, tmp_path) -> dict:
    from app.routers import advice_v2

    monkeypatch.setenv("ADVICE_V2_ENABLED", "1")
    monkeypatch.setattr(advice_v2, "TELEMETRY_DIR", tmp_path)
    monkeypatch.setattr(advice_v2, "ORCHESTRATOR_FACTORY", _S2RestOrchestrator)
    body = client.get("/api/v2/advice", params={
        "surface": "nudge", "driver_id": "d-mem", "date": "2026-08-04",
        "now_min": 540, "shift_start_min": 360, "shift_end_min": 1080,
        "is_driving": False,
    }).json()
    card = body["items"][0]
    assert card["topic"] == "rest", (
        "kịch bản không còn dựng được một thẻ MỀM ⇒ ba test dưới sẽ xanh mà không kiểm gì. "
        f"Nhận được topic={card['topic']!r}")
    # 🔴 Lan can chống tái phát lỗi bản đầu: thẻ dùng làm vật thử phải **hợp lệ theo contract**.
    # Bản cũ dựng một thẻ `solver_set=["S7"]` — tổ hợp mà `advice_v2.json` CẤM — nên cổng canh một
    # trạng thái không tồn tại được. Validate ở đây làm điều đó bất khả: một kịch bản giả mà schema
    # bác thì test ĐỎ ngay, thay vì âm thầm chứng minh một thứ vô nghĩa.
    schema = json.loads((ROOT / "ui/contracts/advice_v2.json").read_text(encoding="utf-8"))
    jsonschema.validate(body, schema)
    ack = client.post(f"/api/v2/advice/{card['checkpoint_id']}/display", json={
        "display_id": card["display_id"], "client_event_id": "mount-1",
        "mounted_at": "2026-08-04T09:00:01+07:00"})
    assert ack.status_code == 200
    return card


def test_HTTP_the_MEM_tu_choi_accepted_bang_422(monkeypatch, tmp_path):
    """Đầu-cuối: thẻ nghỉ sinh thật → `accepted` → **422**. Đây là con đường mà một client thật
    (`driver_app` của Khánh) sẽ đi."""
    card = _the_rest(monkeypatch, tmp_path)
    r = client.post(f"/api/v2/advice/{card['checkpoint_id']}/response", json={
        "display_id": card["display_id"], "client_event_id": "resp-1",
        "response": "accepted", "occurred_at": "2026-08-04T09:00:02+07:00"})
    assert r.status_code == 422, (
        f"thẻ MỀM vẫn ghi được trace ĐỒNG Ý (HTTP {r.status_code}) — ranh giới QĐ-1 hở ở đường v2")
    assert "KHUYÊN MỀM" in r.json()["detail"], (
        "422 đúng số nhưng sai lý do ⇒ có thể tới từ pydantic chứ không phải ranh giới")


@pytest.mark.parametrize("phan_hoi", ["dismissed", "expanded"])
def test_HTTP_the_MEM_van_nhan(phan_hoi, monkeypatch, tmp_path):
    """Cổng không được đóng quá tay: tài xế vẫn phải ẩn được thẻ nghỉ."""
    card = _the_rest(monkeypatch, tmp_path)
    r = client.post(f"/api/v2/advice/{card['checkpoint_id']}/response", json={
        "display_id": card["display_id"], "client_event_id": f"resp-{phan_hoi}",
        "response": phan_hoi, "occurred_at": "2026-08-04T09:00:02+07:00"})
    assert r.status_code == 200, (
        f"`{phan_hoi}` bị chặn ⇒ tài xế mất cách tắt thẻ phiền; Cường chốt GIỮ nút ẩn "
        f"(HTTP {r.status_code}: {r.text})")
