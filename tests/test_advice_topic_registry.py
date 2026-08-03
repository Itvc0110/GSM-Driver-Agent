"""🔴 CỔNG: mọi CHỦ ĐỀ lời khuyên phải được phân loại — đo hoặc khuyên mềm, không có ở giữa.

Quyết định Cường 2026-08-03: *"khuyên nghỉ nên defer thành khuyên mềm, không cho vào để đo hiệu
quả trong sim, trong UI cũng không nên có trace đồng ý làm theo hay không làm theo khi gợi ý —
tương tự đối với thời tiết"* → `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`.

## Vì sao cần cổng chứ không chỉ cần sửa code

Hôm nay sản phẩm **chưa có** thẻ nghỉ hay thẻ thời tiết nào (`cards.js` chỉ có brief/nudge/recap),
nên **không có gì phải tháo**. Nhưng mặc định lại sai: `_render(...)` mặc định `actionable=true`
và `AdviceAction.topic` nhận **chuỗi tuỳ ý**. Thẻ mềm đầu tiên ai thêm vào sẽ **tự động** có nút
"Làm theo" và **tự động** vào mẫu số adherence — im lặng, và im lặng đúng hướng có hại.

Đó là mẫu lỗi repo đã trả giá bốn lần (`D-R12` · UPDATE-114 lỗ (a) · `D-M3-13` · `D-M3-15`): thứ
được khai trong tài liệu mà không có đường chạy, hoặc đường chạy mặc định làm điều không ai chọn.
Nên deliverable đúng là **đường ray + cổng**, không phải sửa UI chưa tồn tại.

## Ba bảo đảm

1. `adherence_view` **vắng khoá** của topic mềm (không phải trả `None` — xem docstring của nó).
2. `POST /advice/action` từ chối `followed` cho topic mềm (422 tại boundary).
3. **Fail-closed**: mọi topic xuất hiện như hằng chuỗi trong code phải nằm trong registry ⇒ thêm
   topic mới mà quên khai thì test ĐỎ.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from gsm_core.lifecycle.advice_topics import (ALL_TOPICS, MEASURED_TOPICS, SOFT_TOPICS,
                                             classify, is_soft)
from gsm_core.lifecycle.projections import adherence_drops, adherence_view

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _ev(event_type: str, topic: str, *, did: str = "s1-abc", eid: str | None = None,
        occurred: str = "2026-08-03T09:00:00+07:00") -> dict:
    return {
        "event_id": eid or f"{did}-{event_type}-{topic}", "decision_id": did,
        "display_id": None, "driver_id": "d-1", "run_id": None,
        "event_type": event_type, "reason_code": None,
        "occurred_at": occurred, "observed_at": occurred,
        "actor": "driver", "origin": "ui", "source": "MOCK",
        "context_revision": None, "payload": {"topic": topic}, "schema_version": "1.0.0",
    }


# ---------- (1) khuyên mềm KHÔNG có mẫu số ----------

@pytest.mark.parametrize("topic", sorted(SOFT_TOPICS))
def test_topic_mem_VANG_KHOA_khoi_adherence_view(topic):
    """Vắng khoá, không phải `None`. `None` là tín hiệu 'mẫu số 0 — có thể có bug' mà
    `D-M3-01`/`L4-01` dùng để tìm thước hỏng; trộn ranh giới vào tín hiệu báo lỗi sẽ khiến người
    sau đi 'sửa' một ranh giới đang chạy đúng."""
    view = adherence_view([_ev("decided", topic), _ev("followed", topic)])
    assert view == {}, (
        f"topic mềm {topic!r} vẫn vào adherence_view ⇒ hệ thống đang đo mức nghe lời của lời "
        f"khuyên sức khoẻ: {view}")


def test_topic_DUOC_DO_thi_van_co_mau_so():
    """Đối chứng bắt buộc — cổng không được lọc sạch mọi thứ cho tiện."""
    view = adherence_view([_ev("decided", "nudge"), _ev("followed", "nudge")])
    assert len(view) == 1, view
    row = next(iter(view.values()))
    assert row["decided"] == 1 and row["followed"] == 1
    assert row["decision_adherence"] == 1.0


def test_tron_mem_va_do_thi_chi_con_phan_DO():
    """Ca thật: một tài xế nhận cả thẻ kinh tế lẫn thẻ thời tiết trong cùng ngày."""
    events = [_ev("decided", "nudge", did="s1-eco", eid="e1"),
              _ev("followed", "nudge", did="s1-eco", eid="e2"),
              _ev("decided", "weather", did="s7-wx", eid="e3"),
              _ev("followed", "weather", did="s7-wx", eid="e4")]
    view = adherence_view(events)
    topics = {k[2] for k in view}
    assert topics == {"nudge"}, f"còn topic mềm trong view: {topics}"
    assert next(iter(view.values()))["event_followed"] == 1


def test_loc_o_CA_HAI_vong_decision_va_event():
    """`adherence_view` có HAI đường vào (vòng decision + vòng event). Lọc một vòng để hở vòng
    kia là đúng họ lỗi `L4-01` — sửa một nửa bộ đo hai-tên rồi tưởng xong.

    Ca này chỉ có event `followed` (không `decided`) nên nó CHỈ đi qua vòng event."""
    view = adherence_view([_ev("followed", "weather")])
    assert view == {}, f"vòng EVENT chưa lọc topic mềm: {view}"


def test_event_THIEU_topic_van_bi_loc_neu_quyet_dinh_la_mem():
    """Lỗ hẹp nhưng thật: `sim_events_to_lifecycle` chỉ đặt `payload["topic"]` **khi** `detail` có
    `channel` (`projections.py:344`) ⇒ một event của CÙNG quyết định vẫn có thể thiếu `topic`, và
    `is_soft(None)` là False ⇒ nó lọt vào mẫu số event.

    Vì thế phép kiểm neo vào QUYẾT ĐỊNH, không vào từng event — ranh giới không được phụ thuộc
    việc mọi producer có nhớ điền field hay không (bài học `D-M3-15`)."""
    thieu_topic = _ev("followed", "weather", eid="e-thieu")
    thieu_topic["payload"] = {}                       # producer quên điền topic
    view = adherence_view([_ev("decided", "weather", eid="e-co"), thieu_topic])
    assert view == {}, (
        f"event thiếu `topic` của một quyết định MỀM vẫn vào mẫu số: {view}")


def test_doi_chung_event_thieu_topic_cua_quyet_dinh_DUOC_DO_thi_van_dem():
    """Đối chứng: không được lọc mọi event thiếu topic cho tiện — đó là hành vi cũ hợp lệ."""
    thieu = _ev("followed", "nudge", eid="e2")
    thieu["payload"] = {}
    view = adherence_view([_ev("decided", "nudge", eid="e1"), thieu])
    assert view, "event thiếu topic của quyết định ĐƯỢC ĐO bị lọc oan"
    assert sum(r["event_followed"] for r in view.values()) == 1, view


def test_F3_followed_MEM_khong_lot_vao_TU_SO_cua_topic_duoc_do():
    """🔴 Lỗ do SOI ĐỘC LẬP bắt (2026-08-03), bản đầu của cycle này CÓ lỗ này.

    `decision_state` giải `row["topic"]` = topic của event **đầu tiên** có topic, còn `row["state"]`
    = kết cục của event **cuối**. Nên `decided[nudge]@09:00` + `followed[rest_nudge]@10:00` trên
    CÙNG `decision_id` cho `row["topic"]="nudge"`, `row["state"]="followed"` ⇒ bản đầu chỉ kiểm
    `is_soft(row["topic"])` ở vòng decision ⇒ **một `followed` MỀM vào tử số của topic ĐƯỢC ĐO**,
    `decision_adherence = 1.0`.

    Vòng event đã kiểm cả hai hướng; vòng decision thì chưa ⇒ tuyên bố *"adherence_view là tầng
    thứ hai độc lập"* của chính cycle này chưa đúng ở hướng đó. Nay `_soft_dids` quét CẢ event."""
    events = [_ev("decided", "nudge", did="s1-x", eid="e1",
                  occurred="2026-08-03T09:00:00+07:00"),
              _ev("followed", "rest_nudge", did="s1-x", eid="e2",
                  occurred="2026-08-03T10:00:00+07:00")]
    view = adherence_view(events)
    assert view == {}, (
        "một `followed` của topic MỀM vẫn vào tử số của topic được đo ⇒ hệ thống đang đo mức "
        f"nghe lời của lời khuyên sức khoẻ qua cửa sau: {view}")


def test_F3_danh_doi_khai_tuong_minh_loai_CA_quyet_dinh():
    """Ghi lại ĐÁNH ĐỔI, không để nó thành phát hiện của người sau.

    Quyết định trộn topic mềm + topic được đo là **lỗi producer** (hôm nay không đường nào tạo
    được: UI trả 422, sim chỉ có 5 kênh đều được đo). Khi nó xảy ra ta **loại cả quyết định** ⇒
    có thể mất một `decided` hợp lệ. Chọn vậy vì hai sai không cùng hạng: mất mẫu số là mất **độ
    chính xác**, còn để `followed` mềm vào tử số là **phá một ranh giới đã chốt**."""
    events = [_ev("decided", "nudge", did="s1-tron", eid="a1"),
              _ev("displayed", "nudge", did="s1-tron", eid="a2"),
              _ev("dismissed", "weather", did="s1-tron", eid="a3",
                  occurred="2026-08-03T11:00:00+07:00")]
    assert adherence_view(events) == {}, "đánh đổi đã khai: loại CẢ quyết định trộn topic"
    # …và một quyết định SẠCH ngay bên cạnh vẫn phải được đếm (không loại lan)
    sach = adherence_view(events + [_ev("decided", "nudge", did="s1-sach", eid="b1"),
                                    _ev("followed", "nudge", did="s1-sach", eid="b2")])
    assert len(sach) == 1 and next(iter(sach.values()))["decided"] == 1, sach


# ---------- N9 + N5: topic CHƯA KHAI bị loại (fail-closed) và cú loại KÊU TO ----------

def test_N9_topic_CHUA_KHAI_khong_duoc_vao_mau_so():
    """🔴 `N9` — UPDATE-128 chỉ loại topic MỀM, nên topic **chưa khai** đi thẳng vào nhóm ĐƯỢC ĐO
    (`is_soft("unknown")` = `False`). Đo được trên store dev bẩn: 52 event mềm bị loại đúng, nhưng
    khoá `khong_khai_bao` **vẫn lọt vào view** ⇒ tầng đọc **fail-OPEN** trong khi tài liệu đã khai
    nó là fail-closed.

    Vì sao fail-closed đúng hướng: một topic lạ **có thể là khuyên mềm ai đó quên khai**; đo nó là
    tạo đúng thước nghe-lời mà ranh giới cấm."""
    view = adherence_view([_ev("decided", "topic_la_chua_ai_khai", eid="u1"),
                           _ev("followed", "topic_la_chua_ai_khai", eid="u2")])
    assert view == {}, f"topic chưa khai vẫn vào mẫu số adherence: {view}"


def test_N9_topic_None_VAN_duoc_do():
    """Đối chứng — `None` và `unknown` KHÁC nhau, không được gộp.

    `None` = *"producer cũ không có khái niệm topic"* (đường sim không đặt `channel`);
    `unknown` = *"producer CÓ đặt tên, chưa ai phân loại"*. Loại `None` sẽ vứt dữ liệu sim hợp lệ."""
    e1, e2 = _ev("decided", "x", eid="n1"), _ev("followed", "x", eid="n2")
    e1["payload"], e2["payload"] = {}, {}
    view = adherence_view([e1, e2])
    assert len(view) == 1 and next(iter(view.values()))["decided"] == 1, view


def test_N5_cu_loai_phai_DEM_DUOC_theo_ly_do():
    """🔴 `N5` — `adherence_view` loại bằng `continue` nên cú loại không để lại dấu vết, và
    `adherence_flags` chỉ soi các khoá ĐANG CÓ ⇒ **không thể thấy một khoá VẮNG MẶT**. Đó đúng hình
    dạng `D-M3-01` (số sai sống qua 39 artifact vì không cơ chế nào kêu)."""
    d = adherence_drops([
        _ev("decided", "weather", did="s1-mem", eid="a1"),
        _ev("decided", "topic_la", did="s1-la", eid="b1"),
        _ev("decided", "nudge", did="s1-do", eid="c1"),
        _ev("decided", "nudge", did="s1-tron", eid="d1"),
        _ev("followed", "rest_nudge", did="s1-tron", eid="d2",
            occurred="2026-08-03T10:00:00+07:00"),
    ])
    assert d["soft"] == 1, d
    assert d["unknown"] == 1 and d["topics_unknown"] == ["topic_la"], d
    assert d["mixed"] == 1, d


def test_N5_topic_MEM_khong_bi_gan_co():
    """Khuyên mềm bị loại là ranh giới chạy ĐÚNG, không phải bất thường. Gắn cờ nó sẽ dạy người
    đọc bỏ qua cờ — cách nhanh nhất giết một cổng."""
    from gsm_sim.sim_metrics import adherence_flags
    assert adherence_flags({}, drops={"soft": 9, "unknown": 0, "mixed": 0}) == []


def test_N5_topic_CHUA_KHAI_va_TRON_phai_TREO():
    """Cường chốt 2026-08-03: topic chưa khai ⇒ **TREO**, không phải chỉ cờ đỏ — repo có lịch sử
    cảnh báo bị bỏ qua (`D-M3-01` sống qua 39 artifact vì không ai chặn)."""
    from gsm_sim.sim_metrics import adherence_flags
    f = adherence_flags({}, drops={"soft": 0, "unknown": 2, "mixed": 1,
                                   "topics_unknown": ["topic_la"]})
    assert len(f) == 2, f
    assert all(x.startswith("TREO") for x in f), f
    assert "topic_la" in f[0], "phải nói RÕ topic nào để người sửa biết khai cái gì"


# ---------- N1: đường ghi thứ BA (pipeline) phải mang topic ----------

def test_N1_episode_store_mang_topic_ra_event_log(tmp_path):
    """🔴 `N1` — đường ghi THỨ BA vào event log (UI · sim · **pipeline**). UPDATE-128 chỉ bịt đường
    UI (validator 422), nên mọi quyết định pipeline có `topic=None` ⇒ `classify(None)` = `measured`
    ⇒ chúng **mặc định vào bảng đo**. Nếu pipeline sinh một lời khuyên khuyên mềm thì nó bị đo im
    lặng — đúng ranh giới §1.2c cấm.

    ⚠ Test này tồn tại vì **sever-restore bắt tôi**: tôi sửa `episode_store` xong mà **quên viết
    cổng**, và mũi tiêm "episode_store thôi ghi topic" cho `XANH — KHÔNG BẮT`. Một fix không có cổng
    thì lần refactor sau nó biến mất không ai biết."""
    from gsm_core.advisor.episode_store import EpisodeStore

    with EpisodeStore(tmp_path / "ep.db") as st:
        st.append_episode({"episode_id": "adv-1", "driver_id": "d-1", "feature": "F1",
                           "advice_spec": {"action_type": "rest_window"}})
        st.append_episode({"episode_id": "adv-2", "driver_id": "d-1", "feature": "F1",
                           "advice_spec": {"action_type": "online"}})
        evs = {e["decision_id"]: (e.get("payload") or {}).get("topic")
               for e in st.log.events() if e["origin"] == "pipeline"}
    assert evs == {"adv-1": "rest_window", "adv-2": "online"}, (
        f"`episode_store` không mang `advice_spec.action_type` ra `payload['topic']`: {evs}. "
        f"Không có topic thì quyết định pipeline mặc định vào bảng ĐO.")


def test_N1_moi_action_type_cua_pipeline_deu_da_phan_loai():
    """Từ vựng `action_type` của pipeline phải nằm trong registry — nếu không, `adherence_view`
    sẽ loại nó (fail-closed) và `adherence_flags` TREO. Tức quên khai ⇒ mất phép đo, không phải
    ra số sai; nhưng vẫn phải bắt sớm ở đây."""
    from gsm_core.advisor.templates import _advice_spec
    mac_dinh = _advice_spec(None, None)["action_type"]
    assert classify(mac_dinh) == "measured", (
        f"`action_type` mặc định của pipeline là {mac_dinh!r} nhưng chưa phân loại ⇒ MỌI quyết "
        f"định pipeline không có action sẽ bị loại khỏi mẫu số và TREO mọi lần đo")
    for act in ("rest_window", "shift_plan"):
        assert classify(act) == "measured", act


# ---------- (2) fail-closed: topic lạ phải ĐỎ, không im lặng rơi vào 'được đo' ----------

def test_topic_chua_khai_thi_classify_tra_unknown():
    assert classify("mot_topic_chua_ai_khai") == "unknown"
    assert classify("weather") == "soft" and classify("nudge") == "measured"
    assert classify(None) == "measured"      # đường ghi cũ không đặt topic


# Chỗ scanner KHÔNG quyết được (`channel=<biến>`, f-string…) — mỗi dòng phải có lý do, đúng khuôn
# `CHUA_DUNG` của `tests/test_config_flags_wired.py`. Danh sách này là nơi DUY NHẤT được phép "mù".
KHONG_QUYET_DUOC: dict[str, str] = {
    "src/gsm_sim/world.py::channel=topic_s":
        "`drain_suppressed()` trả topic tại RUNTIME; giá trị đến từ `advice_bridge`, cùng 5 kênh "
        "đã khai ở MEASURED_TOPICS. Không có nhánh nào sinh tên khác.",
    "src/gsm_sim/world.py::channel=topic_nf":
        "`drain_spoken_outcomes()` — cùng lý do topic_s: kết cục của quyết định ĐÃ NÓI, mang lại "
        "chính channel của kênh đó.",
    "ui/backend/app/routers/advice.py::dict[topic]=topic":
        "`_note_shown`/`_note_suppressed` ghi lại chính `topic` mà `get_advice` nhận từ query "
        "param. Giá trị đó ĐÃ qua fail-closed ở boundary (`classify(topic) == 'unknown'` ⇒ 422 — "
        "xem `get_advice` và `AdviceAction._topic_phai_duoc_phan_loai`), nên tới đây nó chắc chắn "
        "đã được phân loại. Đây là vùng mù DUY NHẤT có lan can chạy TRƯỚC nó.",
}


def _scan_topics(paths) -> tuple[set[str], set[str]]:
    """Quét topic/channel bằng **AST**, trả `(literal thấy được, chỗ KHÔNG quyết được)`.

    🔴 Vì sao bỏ regex (`N3`, soi độc lập 2026-08-03): bản regex chỉ quét **3 file** và chỉ khớp
    `channel="literal"`. Nó **mù** với `channel=<biến>` — idiom đang dùng ở **2/7** chỗ trong
    `world.py` — và mù với mọi file ngoài 3 file đó. Soi độc lập tiêm `channel=_CH_WEATHER` và
    scanner **không thấy**, cổng vẫn xanh.

    Điểm khác quan trọng nhất với bản cũ **không phải AST** mà là: bản cũ **im lặng bỏ sót**, bản
    mới **nói ra là nó không biết**. Một scanner không thể phân giải biến — điều nó phải làm là
    khai điều đó ra, chứ không phải giả vờ đã quét hết. Đó đúng là ranh giới giữa một cổng và một
    cổng trang trí.
    """
    import ast

    thay: set[str] = set()
    mu: set[str] = set()
    for p in paths:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        rel = p.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            # (1) lời gọi có keyword `channel=` / `topic=`
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg not in ("channel", "topic"):
                        continue
                    if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        thay.add(kw.value.value)
                    elif isinstance(kw.value, ast.Name):
                        mu.add(f"{rel}::{kw.arg}={ast.unparse(kw.value)[:40]}")
            # (2) dict literal `{"topic": "…"}` — CHỈ khoá `topic`, không lấy `channel`.
            #     `channel=` là kwarg của `log()` ở `world.py` (producer thật), còn `{"channel": …}`
            #     trong một dict response là **nhãn hiển thị** — vd `routers/sim.py:174` để chuỗi
            #     "all (accept_lift + shift_extend + …)" cho UI đọc. Gộp hai thứ vào một là bắt oan,
            #     và một cổng hay bắt oan sẽ bị người ta tắt.
            elif isinstance(node, ast.Dict):
                for k, v in zip(node.keys, node.values):
                    if not (isinstance(k, ast.Constant) and k.value == "topic"):
                        continue
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        thay.add(v.value)
                    elif isinstance(v, ast.Name):
                        # CHỈ `Name` mới là vùng mù thật: một biến có thể trỏ tới hằng chuỗi MỚI
                        # (đúng cách soi độc lập tiêm: `channel=_CH_WEATHER`). Còn `.get("topic")`
                        # hay `body.topic` là ĐỌC LẠI một giá trị đã tồn tại — không đặt tên mới,
                        # nên không phải chỗ topic lạ chui vào hệ thống.
                        mu.add(f"{rel}::dict[topic]={ast.unparse(v)[:40]}")
            # (3) gán `X_TOPICS = (...)` — vd CLIENT_TOPICS
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if not (isinstance(t, ast.Name) and t.id.endswith("TOPICS")):
                        continue
                    if isinstance(node.value, (ast.Tuple, ast.List, ast.Set)):
                        thay |= {e.value for e in node.value.elts
                                 if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    return {t for t in thay if t}, mu


def _topic_literals_in_src() -> set[str]:
    thay, _ = _scan_topics(_FILES_QUET)
    return thay


_FILES_QUET = sorted(
    [p for p in (ROOT / "src").rglob("*.py")]
    + [p for p in (ROOT / "ui/backend/app").rglob("*.py")])


def test_moi_topic_trong_CODE_deu_da_duoc_phan_loai():
    """Cổng fail-closed. Thêm một kênh/chủ đề mới mà quên khai vào registry ⇒ ĐỎ ở đây, chứ
    không im lặng rơi vào bảng đo."""
    chua_khai = sorted(_topic_literals_in_src() - ALL_TOPICS)
    assert not chua_khai, (
        f"topic có trong code nhưng CHƯA phân loại: {chua_khai}. Thêm vào MEASURED_TOPICS "
        f"(lời khuyên kinh tế — đo mức nghe lời là hợp lệ) hoặc SOFT_TOPICS (khuyên mềm — "
        f"KHÔNG đo). Đừng để mặc định quyết hộ.")


def test_scanner_nay_THUC_SU_tim_thay_gi():
    """Bẫy #9: cổng quét mà quét ra RỖNG thì luôn xanh và vô nghĩa. Chứng minh nó thấy thật."""
    thay = _topic_literals_in_src()
    assert len(thay) >= 5, f"scanner chỉ thấy {thay} — quá ít, chắc AST đã mục"
    assert {"rest_window", "positioning", "brief"} <= thay, thay


def test_scanner_KHAI_duoc_cho_no_KHONG_biet():
    """🔴 `N3` — điểm khác quan trọng nhất giữa bản AST và bản regex cũ.

    Một scanner **không thể** phân giải `channel=<biến>` hay f-string. Bản regex cũ **im lặng bỏ
    sót** chúng (soi độc lập tiêm `channel=_CH_WEATHER` ⇒ scanner không thấy, cổng vẫn xanh). Bản
    mới **khai ra là nó không biết**, và mỗi vùng mù phải có một dòng lý do trong `KHONG_QUYET_DUOC`.

    Tức: biến một sự im lặng thành một dòng khai báo có chủ ý — đúng khuôn `CHUA_DUNG` của
    `test_config_flags_wired.py`. Thêm một `channel=<biến>` mới mà không khai ⇒ ĐỎ."""
    _, mu = _scan_topics(_FILES_QUET)
    chua_khai = sorted(mu - set(KHONG_QUYET_DUOC))
    assert not chua_khai, (
        f"scanner gặp chỗ KHÔNG quyết được mà chưa ai khai: {chua_khai}. Nếu biến đó chỉ mang các "
        f"topic đã khai thì thêm vào `KHONG_QUYET_DUOC` kèm LÝ DO; nếu nó có thể mang tên mới thì "
        f"đổi sang hằng chuỗi. Đừng để scanner im lặng bỏ qua — đó là cách bản regex cũ hở.")


def test_KHONG_QUYET_DUOC_khong_chua_cho_DA_giai_duoc():
    """Đối chứng hai chiều (khuôn `test_CHUA_DUNG_khong_duoc_chua_co_DA_noi`): một chỗ đã thành
    hằng chuỗi mà vẫn nằm trong danh sách mù là **nhãn sai** — nó dạy người đọc rằng còn vùng mù
    ở đó trong khi không còn."""
    _, mu = _scan_topics(_FILES_QUET)
    thua = sorted(set(KHONG_QUYET_DUOC) - mu)
    assert not thua, f"khai 'không quyết được' nhưng scanner nay giải được: {thua}"


# ---------- (3) chống THU HẸP registry (N4) ----------

# Bảng kỳ vọng VIẾT CỨNG — cố ý KHÔNG suy từ registry.
SOFT_MONG_DOI = {"weather", "rest_nudge", "traffic"}


def test_pin_SOFT_TOPICS_chong_thu_hep():
    """🔴 `N4` — soi độc lập tiêm thật: chuyển `traffic` sang `MEASURED_TOPICS` làm **5 test case
    biến mất ÂM THẦM**, suite vẫn xanh.

    Nguyên nhân: **mọi** cổng canh ranh giới đều `parametrize`/loop trên **chính `SOFT_TOPICS`**.
    Tự tham chiếu thì phủ được việc MỞ RỘNG (thêm topic ⇒ tự có test) nhưng **mù hoàn toàn với việc
    THU HẸP** — bỏ một topic ra thì các test của nó đơn giản là không tồn tại nữa, và "0 test chạy"
    trông y hệt "0 test hỏng".

    Bảng dưới đây viết cứng nên thu hẹp ⇒ ĐỎ. Đổi phạm vi ranh giới là **quyết định sản phẩm** (nó
    đổi thứ được đo và thứ không), nên bắt buộc phải sửa DÒNG NÀY — tức có người ký tên vào."""
    assert SOFT_TOPICS == SOFT_MONG_DOI, (
        f"`SOFT_TOPICS` đổi mà bảng kỳ vọng chưa đổi.\n"
        f"  thiếu (bị THU HẸP — nguy hiểm, test của nó biến mất âm thầm): "
        f"{sorted(SOFT_MONG_DOI - SOFT_TOPICS)}\n"
        f"  thừa (mới thêm): {sorted(SOFT_TOPICS - SOFT_MONG_DOI)}\n"
        f"Đổi phạm vi khuyên mềm là quyết định sản phẩm — sửa `SOFT_MONG_DOI` có chủ ý, đừng sửa "
        f"cho test xanh.")


def test_hai_tap_KHONG_giao_nhau():
    assert not (MEASURED_TOPICS & SOFT_TOPICS)
    assert is_soft("weather") and not is_soft("rest_window")


def test_rest_window_dang_o_nhanh_CO_DIEU_KIEN():
    """`rest_window` (HOÃN nghỉ = `C2′`) hiện ở nhóm ĐƯỢC ĐO vì Cường chọn *"thử D-M3-04 trước"*
    (2026-08-03). Test này KHÔNG khẳng định đó là đích cuối — nó ghim trạng thái hiện tại để việc
    chuyển sang khuyên mềm là một thay đổi TƯỜNG MINH, có người sửa test, chứ không phải một cái
    trượt tay. Luật quyết định: `specs/simulation/d-m3-04-multiday-prereg-locked.json`."""
    assert "rest_window" in MEASURED_TOPICS
    assert "rest_nudge" in SOFT_TOPICS, (
        "`rest_nudge` (GỢI Ý nghỉ khi quá sức) khác `rest_window` (HOÃN nghỉ) — cái đầu là "
        "khuyên mềm, cái sau là kênh thời-điểm đang chờ D-M3-04")
