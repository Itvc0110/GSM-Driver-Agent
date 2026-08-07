"""Ba lỗ đo lường của ĐƯỜNG SẢN PHẨM — phản biện xong 2026-07-31, đều reproduce được.

Nguồn: `tracking/SOI-2026-07-30-mau-so-adherence.md` §4 (13 finding sev CAO, trước đó 16/16
agent phản biện chết quota 3 lần ⇒ tôi tự phản biện bằng đọc code + reproduce qua đường ống
thật). Ba cái dưới đây ĐÚNG; mỗi test là bằng chứng đỏ trước khi sửa.

- L3-03: `followed` LUÔN thắng `dismissed` khi `occurred_at` hoà ⇒ sản phẩm không ghi nhận
  được tài xế ĐỔI Ý (client gửi `at_min` hằng theo loại card ⇒ hoà là mặc định).
- L4-01: sản phẩm ghi `displayed`, sim ghi `decided` ⇒ `event_adherence` vĩnh viễn None ở
  sản phẩm, và tệ hơn: `event_followed > event_decided = 0` là trạng thái BẤT KHẢ không ai bắt.
- L4-07: card IM LẶNG vẫn vẽ nút "Làm theo" với `advice_id` do CLIENT BỊA (`brief-{date}` /
  `recap-{date}`) ⇒ một cú bấm tạo decision+followed cho quyết định advisor CHƯA TỪNG ĐƯA,
  bơm `decision_adherence` lên 100%.
"""
from __future__ import annotations

import textwrap

import pytest

from gsm_core.lifecycle import projections as p


def _ev(event_id, event_type, *, decision_id="s1-abc", occurred="2026-07-31T09:00:00+07:00",
        observed="2026-07-31T02:00:00Z", topic="bonus", actor="driver"):
    return {"event_id": event_id, "decision_id": decision_id, "display_id": None,
            "driver_id": "d-1", "run_id": None, "event_type": event_type,
            "reason_code": None, "occurred_at": occurred, "observed_at": observed,
            "actor": actor, "origin": "ui", "source": "MOCK", "context_revision": None,
            "payload": {"topic": topic}, "schema_version": "1.0.0"}


# ---------- L3-03 ----------

def test_l3_03_doi_y_phai_duoc_ghi_nhan():
    """Tài xế bấm "Làm theo" 14:00 rồi ĐỔI Ý "Bỏ qua" 15:00 trên cùng card.

    `occurred_at` bằng nhau (client gửi `at_min` hằng theo loại card) ⇒ tie-break quyết định
    tất cả. Trước fix: tie-break bằng `event_id` chuỗi, `"...-dismissed-..." < "...-followed-..."`
    ⇒ followed sort SAU ⇒ thắng, BẤT KỂ tài xế bấm gì sau cùng.
    """
    events = [_ev("ui-s1-abc-followed-2026-07-31T14:00:00", "followed",
                  observed="2026-07-31T07:00:00Z"),
              _ev("ui-s1-abc-dismissed-2026-07-31T15:00:00", "dismissed",
                  observed="2026-07-31T08:00:00Z")]
    st = list(p.decision_state(events).values())[0]
    assert st["state"] == "dismissed", (
        "hành động CUỐI của tài xế là 'Bỏ qua' nhưng hệ thống ghi 'followed' — "
        "sản phẩm không ghi nhận được việc đổi ý (L3-03)")


def test_l3_03_thu_tu_dung_khi_occurred_at_khac_nhau():
    """Đối chứng: khi `occurred_at` khác nhau thì thứ tự vốn đã đúng — fix không được
    làm hỏng đường này."""
    events = [_ev("ui-x-dismissed-a", "dismissed", occurred="2026-07-31T09:00:00+07:00"),
              _ev("ui-x-followed-b", "followed", occurred="2026-07-31T10:00:00+07:00")]
    assert list(p.decision_state(events).values())[0]["state"] == "followed"


# ---------- L4-01 ----------

def test_l4_01_event_adherence_song_o_duong_san_pham():
    """Sản phẩm ghi `displayed` (advisor ĐÃ NÓI) + `followed`. `event_adherence` phải tính
    được — trước fix nó là None vì mẫu số chỉ đếm `decided`/`followed`."""
    events = [_ev("ui-shown-d-1-2026-07-31-bonus-18", "displayed", actor="advisor"),
              _ev("ui-s1-abc-followed-2026-07-31T09:05:00", "followed")]
    row = list(p.adherence_view(events).values())[0]
    assert row["event_decided"] >= 1, "advisor ĐÃ NÓI (displayed) mà mẫu số event = 0 (L4-01)"
    assert row["event_adherence"] is not None


def test_l4_01_tu_so_khong_bao_gio_vuot_mau_so():
    """Bất biến: `event_followed <= event_decided`. Vi phạm = thước hỏng, không phải dữ liệu lạ."""
    events = [_ev("ui-shown-x", "displayed", actor="advisor"),
              _ev("ui-y-followed", "followed")]
    row = list(p.adherence_view(events).values())[0]
    assert row["event_followed"] <= row["event_decided"], row


# ---------- L4-07 ----------

def test_l4_07_quyet_dinh_ma_khong_duoc_vao_mau_so():
    """Client bịa `advice_id` cho card IM LẶNG (`brief-{date}`/`recap-{date}`) rồi tài xế
    bấm "Làm theo" ⇒ decision+followed cho lời khuyên advisor CHƯA TỪNG ĐƯA ⇒ adherence 100%.

    Sửa đúng phải chặn ở CLIENT (không vẽ nút trên card im lặng) VÀ ở BOUNDARY (server từ
    chối `advice_id` không tồn tại) — test này canh tầng boundary.
    """
    from app.routers.advice import is_fabricated_advice_id
    assert is_fabricated_advice_id("brief-2026-07-31")
    assert is_fabricated_advice_id("recap-2026-07-31")
    assert not is_fabricated_advice_id("s1-d-1-2026-07-31-540-bonus")


def test_l4_07_post_action_tu_choi_advice_id_bia(monkeypatch, tmp_path):
    """POST /advice/action với id bịa ⇒ 422, KHÔNG ghi event nào."""
    import app.routers.advice as ad
    from fastapi.testclient import TestClient
    from app.main import app

    monkeypatch.setattr(ad, "_lifecycle_db", lambda: tmp_path / "lc.db")
    monkeypatch.setattr(ad, "ACTIONS_FILE", tmp_path / "actions.jsonl")
    monkeypatch.setattr(ad, "TELEMETRY_DIR", tmp_path)
    c = TestClient(app)
    r = c.post("/api/v1/advice/action", json={
        "advice_id": "recap-2026-07-31", "driver_id": "d-1", "date": "2026-07-31",
        "action": "followed", "card_kind": "recap", "at_min": 1290, "topic": "recap"})
    assert r.status_code == 422, r.text
    assert not (tmp_path / "actions.jsonl").exists() or \
        (tmp_path / "actions.jsonl").read_text(encoding="utf-8").strip() == ""


# ---------- L4-04: sản phẩm không bao giờ ghi `suppressed` ----------

def test_l4_04_bi_nen_phai_duoc_ghi_nhan(monkeypatch, tmp_path):
    """Sim ghi event `advice_suppressed` mỗi lần nhịp chặn; sản phẩm trả silent card mà
    KHÔNG ghi gì ⇒ mẫu số "advisor ĐỊNH nói nhưng bị nén" tồn tại ở sim, mất hẳn ở sản
    phẩm ⇒ `adherence_view["suppressed"]` luôn 0 và hai đường không so được.
    """
    import app.routers.advice as ad
    from gsm_core.lifecycle.event_log import AdviceEventLog
    from fastapi.testclient import TestClient
    from app.main import app

    db = tmp_path / "lc.db"
    monkeypatch.setattr(ad, "_lifecycle_db", lambda: db)
    monkeypatch.setattr(ad, "TELEMETRY_DIR", tmp_path)
    c = TestClient(app)
    # nói lần đầu (PRESENT) rồi hỏi lại NGAY trong cooldown ⇒ phải bị nén
    c.get("/api/v1/advice", params={"now_min": 540, "topic": "brief"})
    r = c.get("/api/v1/advice", params={"now_min": 545, "topic": "brief"})
    assert r.json()["silent"]["is_silent"] is True, r.json()
    with AdviceEventLog(db) as log:
        kinds = [e["event_type"] for e in log.events()]
    assert "suppressed" in kinds, f"bị nén mà không ghi event nào: {kinds} (L4-04)"


# ---------- L4-09: `topic` default "bonus" là namespace mồ côi ----------

def test_l4_09_topic_default_khong_phai_namespace_mo_coi():
    """Client chỉ gửi brief/nudge/recap (`cards.js KIND_TOPIC`). Default `"bonus"` không
    client nào gửi ⇒ nó là namespace riêng có cooldown/dismiss riêng, không ai nuôi."""
    import inspect
    import app.routers.advice as ad
    from app.routers.advice import CLIENT_TOPICS
    sig = inspect.signature(ad.get_advice)
    default = sig.parameters["topic"].default
    assert getattr(default, "default", default) in CLIENT_TOPICS, (
        f"topic default {default!r} không nằm trong tập topic client thật {CLIENT_TOPICS} "
        f"⇒ namespace mồ côi (L4-09)")


# ---------- L4-07(SOI): pha ca dùng hằng SHIFT_START_MIN cho MỌI tài xế ----------

def test_l4_07soi_gio_bat_dau_ca_phai_tham_so_hoa():
    """`shift_end_min` là query param nhưng `shift_start` là HẰNG 06:00 cho mọi tài xế —
    bất đối xứng, và pha ca (early/mid/late) của tài xế ca đêm bị tính sai hoàn toàn.

    ⚠ ĐÍNH CHÍNH 2026-08-07 (Cycle 1): test này **CHỈ kiểm chữ ký hàm có tham số** — nó KHÔNG
    kiểm một pha nào cả, nên nó **xanh với một bản tham-số-hoá làm NỬA VỜI**. Và đó chính là
    thứ đã xảy ra: `get_advice` nhận `shift_start_min` và dùng đúng ở `:195`, nhưng `_phase_of`
    vẫn đọc **hằng module** `SHIFT_START_MIN` ⇒ **hai công thức pha trong CÙNG một request**.
    Test vi phân bên dưới mới là cái kiểm được tính chất đó."""
    import inspect

    import app.routers.advice as ad
    assert "shift_start_min" in inspect.signature(ad.get_advice).parameters, (
        "giờ bắt đầu ca chưa tham số hoá — pha ca vẫn dùng hằng 06:00 cho mọi tài xế")


# ---------- Cycle 1 / A2: TEST VI PHÂN — hai đường tính pha phải KHỚP ----------

_CA = [
    ("ca ngày  06:00→22:00", 6 * 60, 22 * 60),
    ("ca chiều 14:00→23:00", 14 * 60, 23 * 60),
    ("ca đêm   22:00→02:00", 22 * 60, 2 * 60),      # vắt nửa đêm
]


def _pha_duong_doc(now_min: float, start: int, end: int) -> str:
    """Công thức của đường ĐỌC (`get_advice`) — nguồn canonical."""
    from app.routers.advice import _norm_shift_end
    from gsm_core.lifecycle.cadence import shift_phase
    return shift_phase(now_min - start, _norm_shift_end(end, start) - start)


@pytest.mark.parametrize("ten,start,end", _CA)
@pytest.mark.parametrize("ty_le", [0.1, 0.5, 0.9])          # early / mid / late
def test_A2_hai_duong_tinh_pha_phai_KHOP(ten, start, end, ty_le):
    """`_phase_of` (đường DISMISS) phải cho cùng pha với đường ĐỌC trên mọi ca.

    Lệch ở đây nghĩa là: nút **"Bỏ qua"** của tài xế hoặc vô tác dụng, hoặc làm advisor im ở
    một pha **chưa hề bị tắt** — với **mọi** tài xế không mở ca đúng 06:00."""
    from app.routers.advice import _norm_shift_end, _phase_of

    do_dai = _norm_shift_end(end, start) - start
    at = start + ty_le * do_dai
    at_wrap = at % 1440                      # mốc thời gian THẬT trong ngày (ca đêm vắt qua)
    mong_doi = _pha_duong_doc(at, start, end)
    thuc_te = _phase_of(at_wrap, end, start)
    assert thuc_te == mong_doi, (
        f"{ten} tại {ty_le:.0%} ca: đường ĐỌC nói '{mong_doi}' nhưng `_phase_of` nói "
        f"'{thuc_te}' — hai công thức pha trong cùng một request")


def test_M5_khong_ghi_suppressed_khi_advisor_von_IM_LANG(monkeypatch, tmp_path):
    """R-08 cho đường SẢN PHẨM: nén một lời khuyên **KHÔNG TỒN TẠI** thì không được ghi sổ.

    Sim đã áp nguyên tắc này cho **5 kênh**; sản phẩm thì `_note_shown` có cổng `if not items`
    còn `_note_suppressed` **không** ⇒ mọi lần nhịp chặn một tài xế mà advisor vốn im lặng vẫn
    ghi một event `suppressed` MA vào store canonical, thổi mẫu số của chính phép đo."""
    import app.routers.advice as ad

    ghi: list[tuple] = []
    monkeypatch.setattr(ad, "_note_suppressed",
                        lambda *a, **k: ghi.append(a))
    # advisor KHÔNG có gì để nói
    monkeypatch.setattr(ad.advisor, "advice",
                        lambda *a, **k: {"driver_id": "d-1", "date": "2026-07-05", "items": []})
    monkeypatch.setattr(ad.advisor, "provenance", lambda *a, **k: {})
    monkeypatch.setattr(ad, "_cadence_memory", lambda *a, **k: ad.CadenceMemory())

    class _V:
        verdict, reason, next_eligible_min = "SILENT", "topic_cooldown", None
    monkeypatch.setattr(ad, "evaluate", lambda *a, **k: _V())

    _goi = dict(driver_id="d-1", date="2026-07-05", now_min=840, shift_end_min=22 * 60,
                is_driving=False, topic="brief", shift_start_min=6 * 60)
    ad.get_advice(**_goi)
    assert ghi == [], (
        "ghi event `suppressed` trong khi advisor vốn IM LẶNG — nén một lời khuyên không tồn "
        "tại. Cùng nguyên tắc R-08 mà sim đã sửa cho 5 kênh")

    # ...và vế NGƯỢC: có gì để nói mà bị nén thì PHẢI ghi (chống test-ghim-vô-hiệu)
    monkeypatch.setattr(ad.advisor, "advice",
                        lambda *a, **k: {"driver_id": "d-1", "date": "2026-07-05",
                                         "items": [{"kind": "bonus_gap"}]})
    ad.get_advice(**_goi)
    assert len(ghi) == 1, "có lời khuyên thật bị nén mà KHÔNG ghi ⇒ mất mẫu số suppressed"


def test_A11_cadence_memory_khong_nhan_tham_so_KHONG_DUNG():
    """Chữ ký nói ký ức nhịp có phạm vi theo PHA, thân hàm dựng ký ức cho CẢ NGÀY.

    Một tham số khai mà không đọc là lời hứa sai với người đọc kế tiếp — cùng họ với chính
    `L4-07` ở trên (khai `shift_start_min` rồi không dùng ở đường thứ hai)."""
    import ast
    import inspect

    import app.routers.advice as ad
    src = inspect.getsource(ad._cadence_memory)
    cay = ast.parse(textwrap.dedent(src))
    ham = cay.body[0]
    ten_tham_so = {a.arg for a in ham.args.args}
    dung = {n.id for n in ast.walk(ham) if isinstance(n, ast.Name)}
    thua = sorted(ten_tham_so - dung - {"self"})
    assert not thua, (
        f"`_cadence_memory` khai tham số nhưng KHÔNG đọc: {thua} — chữ ký nói một đằng, "
        f"thân hàm làm một nẻo")
