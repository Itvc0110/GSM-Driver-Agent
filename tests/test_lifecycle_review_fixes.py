"""Cycle W đóng — test cho các finding review đối kháng (hồ sơ
`research/audit/2026-07-29-cycle-w-review/findings.md`).

Batch 1 (F-1..F-8/W-1..W-8): nhóm F-1/F-2/F-5/F-7 sửa ở `66268cc` — reproduce giữ làm
regression; nhóm F-6/W-6/W-4b/W-7 + A2 hai-tên sửa trong Phần A.
Batch 2 (X-1..X-7 input thù địch · F-S1..F-S13 kỷ luật): TDD đỏ trước, sửa cùng lượt.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from gsm_core.lifecycle import projections as P
from gsm_core.schema_registry import SchemaRegistry
from gsm_sim.config import Config
from gsm_sim.runner import derive_run_id, run_once

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "research" / "policy" / "t004-current-policy-text-corpus-2026-07-22.json"


def _cfg_all() -> Config:
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="all", single_actor_id=None,
                            channels={"shift_plan": True, "accept_lift": True,
                                      "shift_extend": True, "rest_window": True},
                            positioning_overrides="wait_only")
    return c


@pytest.fixture(scope="module")
def run_b():
    return run_once(_cfg_all(), seed=1000)


@pytest.fixture(scope="module")
def view_b(run_b):
    return P.adherence_view(P.sim_events_to_lifecycle(run_b.events))


def _agg(view) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for (_run, _drv, topic), v in view.items():
        a = out.setdefault(topic, {})
        for k, val in v.items():
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                a[k] = a.get(k, 0) + val
    return out


# ---------- D-M3-01: cổng HAI PHÍA — pin adherence vào ground truth ĐỘC LẬP ----------


def test_shift_extend_adherence_matches_coin_truth():
    """`decision_adherence` phải khớp COIN, không chỉ "khác 1,0".

    Vì sao cần test này dù `test_decision_level_matches_ground_truth` đã có: cổng ở đó
    (`ext_adh < 0.99`) là **MỘT PHÍA**. Soi độc lập (`L5-06`) chỉ ra nó sẽ **xanh** trên một
    con số sai theo chiều THẤP — và đúng như vậy: bản vá giữa kỳ của `D-M3-01` cho 0,394
    trong khi sự thật 0,473 (**−7,9đp**), mà cổng một phía vẫn xanh.

    Ground truth ở đây ĐỘC LẬP với event log: mỗi lần `coin_follows` được gọi là một lần
    advisor NÓI, giá trị trả về là tài xế có nghe theo. Gộp theo QUYẾT ĐỊNH (bucket 30′ +
    `material_revision`) — **cùng đơn vị** với `decision_adherence`.

    ⚠ Đừng so với tỷ lệ theo LẦN HỎI (327/1051 = 0,311): trộn hai đơn vị cho ra "sai 3,2×"
    thay vì 2,1× — chính lỗi mà bản đính chính đầu tiên mắc lại (`L5-05`).
    """
    from gsm_core.lifecycle.cadence import decision_bucket
    from gsm_sim import advice_bridge as AB

    decisions: dict[tuple, bool] = {}
    orig = AB.AdviceActionBridge.coin_follows

    def spy(self, actor, topic, now_min, material_revision, bucket_min=None):
        out = orig(self, actor, topic, now_min, material_revision, bucket_min)
        if topic == "shift_extend":
            decisions[(actor.actor_id,
                       decision_bucket(now_min, bucket_min), material_revision)] = out
        return out

    AB.AdviceActionBridge.coin_follows = spy
    try:
        r = run_once(_cfg_all(), seed=1000)
    finally:
        AB.AdviceActionBridge.coin_follows = orig

    n_dec = len(decisions)
    n_fol = sum(1 for v in decisions.values() if v)
    assert n_dec > 0, "kênh shift_extend không nói lần nào — test mất ý nghĩa"
    truth = n_fol / n_dec

    agg = _agg(P.adherence_view(P.sim_events_to_lifecycle(r.events)))
    reported = agg["shift_extend"]["followed"] / agg["shift_extend"]["decided"]

    # HAI PHÍA: |báo − thật| nhỏ. 0,03 đủ chặt để bắt cả hai lỗi đã xảy ra thật
    # (mẫu số hụt ⇒ +0,53đp; tử số hụt ⇒ −7,9đp) và đủ lỏng cho làm tròn bucket biên ca.
    assert abs(reported - truth) < 0.03, (
        f"adherence BÁO {reported:.3f} vs COIN {truth:.3f} "
        f"(lệch {reported - truth:+.3f}) — thước đo lệch ground truth độc lập. "
        f"Chiều DƯƠNG = mẫu số hụt (D-M3-01); chiều ÂM = tử số hụt (nhánh 'đồng ý nhưng "
        f"bất khả thi' không được log). {n_fol}/{n_dec} quyết định theo coin.")


# ---------- F-1 regression: khớp GROUND TRUTH của sim (đã sửa 66268cc) ----------

def test_decision_level_matches_ground_truth(run_b, view_b):
    """Trước sửa: 2,0%/0,0%/0,0%/100% vs sự thật 52,2%/53,6%/100%/48,8%."""
    ev = run_b.events
    agg = _agg(view_b)

    # shift_plan: due() 30' = đúng bucket ⇒ decision ↔ event 1-1
    gt_given = sum(1 for e in ev if e.kind == "advice_given")
    gt_follow = sum(1 for e in ev if e.kind == "advice_given" and e.detail.get("followed"))
    assert agg["shift_plan"]["decided"] == gt_given
    assert agg["shift_plan"]["followed"] == gt_follow

    # shift_extend: mẫu số = MỌI lần advisor nói; tử số = lần MANG CỜ followed.
    #
    # D-M3-01 (2026-07-30): bản trước của ba dòng này là
    #     gt_ext = sum(1 for e in ev if e.kind == "advice_shift_extend")
    #     assert agg["shift_extend"]["decided"]  == gt_ext
    #     assert agg["shift_extend"]["followed"] == gt_ext
    # — assert CẢ HAI bằng CÙNG MỘT biến đếm ⇒ **đồng nhất thức**, adherence = 1,0 luôn,
    # test KHÔNG BAO GIỜ đỏ được. Tức chính test regression của họ lỗi F-1 ("mẫu số chỉ
    # chứa người đã theo") lại KHẮC đúng lỗi đó thành kỳ vọng cho một kênh khác. Hai kênh
    # bên trên/dưới (`shift_plan` :62-65, `positioning` :73-76) pin bằng HAI đại lượng
    # khác nhau — đúng; chỉ kênh này bị pin tautology.
    #
    # Sự thật đo được (`scripts/probe_adherence_truth.py`, 3 seed, coverage=all): advisor
    # nói 1051 lần, nghe theo 327 ⇒ adherence THẬT 0,311, trong khi event log cho 1,000
    # ⇒ con số đã báo ("43/43 = 100% · Ground truth 100% ✓") thổi lên 2,1× so với đơn vị
    # QUYẾT ĐỊNH (0,473). ⚠ 0,311 là đơn vị LẦN HỎI — trộn hai đơn vị cho ra 3,2× SAI.
    gt_ext_decided = sum(1 for e in ev if e.kind == "advice_shift_extend")
    gt_ext_followed = sum(1 for e in ev if e.kind == "advice_shift_extend"
                          and e.detail.get("followed"))
    assert agg["shift_extend"]["decided"] == gt_ext_decided
    assert agg["shift_extend"]["followed"] == gt_ext_followed
    # Cổng chống tái phát: adherence = 1,0 nghĩa là mẫu số chỉ chứa người đã theo.
    # ⚠ KHÔNG được nới ngưỡng — nới là xoá đúng cái test này sinh ra để bắt.
    #
    # ⚠ Phải tính tỷ lệ TỪ HAI TỔNG, không đọc `agg["decision_adherence"]`: `_agg` cộng dồn
    # MỌI trường số, nên trường đó là TỔNG TỶ LỆ của ~86 tài xế (đo được 28,67), không phải
    # một tỷ lệ. Bản đầu của assert này đọc thẳng nó và báo "adherence 28,67" — lỗi đơn vị
    # của test, không phải lỗi của code.
    ext_adh = agg["shift_extend"]["followed"] / agg["shift_extend"]["decided"]
    assert ext_adh < 0.99, (
        f"adherence {ext_adh:.3f} ≈ 1,0 ⇒ mẫu số chỉ chứa người ĐÃ THEO (D-M3-01)")
    # ⚠ Cổng trên là MỘT PHÍA: nó xanh trên một con số sai theo chiều THẤP. Cổng hai phía
    # nằm ở `test_shift_extend_adherence_matches_coin_truth` — pin vào ground truth ĐỘC LẬP.

    # positioning: mẫu số = người ĐƯỢC GÁN (planner), không phải người đã theo.
    # ⚠ Tử số đổi nghĩa 2026-07-31 (UPDATE-113 SỬA THƯỚC): trước đây pin vào số lần THI
    # HÀNH (`standby_followed`) — nhưng thi hành = coin-true ∧ *thi-hành-được*, nên nó đếm
    # hụt các ca coin-true-không-thi-hành (pop im lặng / bận / bản năng ≠ WAIT). Bias ~2,4đp
    # đó làm cổng z TREO arm oracle ở n=100 (z=−4,40). Tử số nay là kết cục COIN tại lúc gán
    # (`coin_follow_ids`); tỷ lệ thi hành sống ở chỉ tiêu RIÊNG `execution_rate`.
    assigned = sum(e.detail.get("n_assigned", 0) for e in ev if e.kind == "standby_planner")
    coin_true = sum(len(e.detail.get("coin_follow_ids") or [])
                    for e in ev if e.kind == "standby_alloc")
    executed = sum(1 for e in ev if e.kind == "standby_followed")
    assert agg["positioning"]["decided"] == assigned, "mẫu số phải gồm người KHÔNG theo"
    assert agg["positioning"]["followed"] == coin_true, "tử số phải là kết cục COIN"
    assert executed <= coin_true, "thi hành không thể vượt số người đã nghe"


# ---------- A2: hai tên, không bao giờ gọi trống là 'adherence' (verdict Cường) ----------

def test_event_level_counters_present(run_b, view_b):
    """Hai đơn vị đo phải CÙNG có mặt và cùng khớp ground truth đếm từ event thô.

    ⚠ Bản gốc (Cycle W) còn khẳng định `decided < event_decided` với lý lẽ *"accept_lift
    fire mỗi tick ⇒ decision gộp bucket nên ít hơn event"*. **ĐA-04 (UPDATE-099) xoá bỏ
    chính tiền đề đó**: cooldown 20′/topic khiến mỗi bucket 30′ chỉ còn một lần nói, nên
    hai con số BẰNG NHAU (58 == 58) — đó là hiệu ứng mong muốn, không phải hồi quy.
    Bất biến còn đúng ở mọi cấu hình là `decided <= event_decided`; phần "gộp bucket" nay
    được kiểm ở arm cadence TẮT, nơi tiền đề spam vẫn còn."""
    ev = run_b.events
    agg = _agg(view_b)
    gt_gate = sum(1 for e in ev if e.kind == "advice_bonus_gate")
    gt_gate_f = sum(1 for e in ev if e.kind == "advice_bonus_gate" and e.detail.get("followed"))
    assert agg["accept_lift"]["event_decided"] == gt_gate
    assert agg["accept_lift"]["event_followed"] == gt_gate_f
    assert agg["accept_lift"]["decided"] <= gt_gate, "decision không được VƯỢT event"


def test_decision_level_still_collapses_buckets_without_cadence():
    """Giữ lại sức mạnh gốc của test trên, ở đúng chỗ tiền đề còn đúng.

    Tắt cadence ⇒ `accept_lift` lại fire mỗi tick ⇒ decision-level PHẢI gộp bucket và
    nhỏ hơn hẳn event-level. Nếu một ngày nào đó phép gộp bucket hỏng, test này đỏ dù
    arm mặc định (có cadence) trông vẫn bình thường."""
    c = _cfg_all()
    c.data["advice"].setdefault("cadence", {})["enabled"] = False
    agg = _agg(P.adherence_view(P.sim_events_to_lifecycle(run_once(c, seed=1000).events)))
    ev_n = agg["accept_lift"]["event_decided"]
    dec_n = agg["accept_lift"]["decided"]
    assert dec_n < ev_n, f"không cadence thì decision phải gộp bucket: {dec_n} vs {ev_n}"


def test_no_bare_adherence_key_and_both_rates_named(view_b):
    """Cấm khoá 'adherence' trần — hai tỉ lệ phải mang TÊN ĐẦY ĐỦ (BUG-EVAL-ARGMAX:
    số không rõ đơn vị là số sẽ bị đọc sai)."""
    some = False
    for row in view_b.values():
        assert "adherence" not in row, "cấm khoá 'adherence' không rõ đơn vị"
        assert "decision_adherence" in row and "event_adherence" in row
        if row["decision_adherence"] is not None:
            some = True
            assert 0.0 <= row["decision_adherence"] <= 1.0
    assert some, "phải có ít nhất một hàng có tỉ lệ tính được"


# ---------- F-2 regression: khoá tách run ----------

def _ev(**kw) -> dict:
    b = {"event_id": "e", "decision_id": "d", "display_id": None, "driver_id": "0",
         "run_id": None, "event_type": "decided", "reason_code": None,
         "occurred_at": "2026-07-29T08:00:00+07:00",
         "observed_at": "2026-07-29T08:00:00+07:00", "actor": "advisor",
         "origin": "sim", "source": "MOCK", "context_revision": None,
         "payload": {"topic": "shift_plan"}, "schema_version": "1.0.0"}
    b.update(kw)
    return b


def test_adherence_key_separates_runs():
    view = P.adherence_view([
        _ev(event_id="a1", decision_id="dA", run_id="runA"),
        _ev(event_id="b1", decision_id="dB", run_id="runB"),
    ])
    assert len(view) == 2, f"actor 0 của hai run là HAI người: {view}"


# ---------- F-5 regression: decision_id theo bucket của planner ----------

def test_decision_id_bucket_follows_config():
    """`bucket_min=15` từng làm 23 phân công dùng chung decision_id ⇒ event bị nuốt.

    ⚠ Đổi 2026-07-31 (V-21, UPDATE-112): lưới định danh quyết định nay là MỘT SỐ DUY NHẤT
    (`DECISION_BUCKET_MIN`) cho mọi kênh — `advice.bucket_min` chỉ còn là CHU KỲ CHẠY của
    planner. Ràng buộc cũ (bucket không được rộng hơn nhịp planner) nay được canh bằng
    guard FAIL-LOUD thay vì bằng một lưới riêng: `bucket_min=15` là cấu hình KHÔNG HỢP LỆ
    và phải NỔ ngay, thay vì chạy tiếp rồi nuốt event im lặng."""
    import pytest
    from gsm_core.policy_locks import PolicyLockViolation  # noqa: F401  (khác loại, ghi rõ)
    c = _cfg_all()
    c.data["advice"]["bucket_min"] = 15
    with pytest.raises(ValueError, match="NGẮN HƠN lưới quyết định"):
        run_once(c, seed=1000)

    # Đường hợp lệ: planner thưa hơn lưới ⇒ chạy được, decision_id vẫn duy nhất per gán
    c2 = _cfg_all()
    c2.data["advice"]["bucket_min"] = 60
    r = run_once(c2, seed=1000)
    ids = [e.detail["decision_id"] for e in r.events if e.kind == "standby_followed"]
    assert ids, "kịch bản phải sinh standby_followed — rỗng là test vacuous (F-S6)"
    assert len(set(ids)) == len(ids)


# ---------- F-7 regression: adapter tôn trọng Event.run_id ----------

def test_adapter_rejects_conflicting_run_id(run_b):
    with pytest.raises(ValueError, match="run_id"):
        P.sim_events_to_lifecycle(run_b.events, run_id="TOI-BIA-RA")


def test_adapter_multiday_mixed_runs_keep_own_run_id():
    from gsm_sim.multiday import run_multiday
    res = run_multiday(_cfg_all(), seed=1000, days=2)
    lc = P.sim_events_to_lifecycle([e for d in res.days for e in d.events])
    assert len({e["run_id"] for e in lc}) == 2


# ---------- F-6: count_episodes chỉ đếm decision của PIPELINE ----------

def test_count_episodes_ignores_ui_and_sim_events(tmp_path):
    """Trước sửa: 12 episode + 1 event UI + 3 event sim ⇒ count = 16 (thổi phồng)."""
    from gsm_core.advisor.episode_store import EpisodeStore
    from gsm_core.lifecycle.event_log import AdviceEventLog
    db = tmp_path / "ep.db"
    with EpisodeStore(db) as store:
        for i in range(3):
            store.append_episode({"episode_id": f"adv-{i}", "driver_id": "d-1",
                                  "feature": "F1", "message": "m", "confidence": 0.5,
                                  "fallback_used": True})
        with AdviceEventLog(db) as log:
            log.append(_ev(event_id="ui-1", decision_id="s1-x", origin="ui",
                           actor="driver", event_type="followed"))
            log.append(_ev(event_id="sim-1", decision_id="slth-x", origin="sim",
                           run_id="r1"))
        assert store.count_episodes() == 3, "UI/sim event không phải episode pipeline"


# ---------- W-6: recorder không được bịa verify verdict ----------

def test_recorder_gets_none_when_verify_not_run(tmp_path):
    """R5 out-of-taxonomy KHÔNG chạy verify ⇒ recorder phải nhận passed=None,
    không phải True (bịa) hay False (ép kiểu bool(None))."""
    from gsm_core.advisor.observability import ObservabilityRecorder
    from gsm_core.advisor.pipeline import AdvisorPipeline
    rec = ObservabilityRecorder(parquet_path=tmp_path / "obs.parquet")
    pipe = AdvisorPipeline(corpus_path=CORPUS, store_path=tmp_path / "ep.db",
                           llm_mode="off", recorder=rec)
    req = {"schema_version": "1.0.0", "request_id": "r1", "driver_id": "d-1",
           "feature": "F1", "free_text_query": "thời tiết sao Hỏa thế nào hôm nay",
           "l3_view_refs": [], "session_id": "s1",
           "t_request": "2026-07-01T18:00:00+07:00", "trigger_source": "user_ask"}
    pipe.handle(req, solver_reports=[], kb_track=None)
    pipe.close()
    assert rec.rows, "recorder phải có row"
    assert rec.rows[-1]["verifier_passed"] is None, (
        f"chưa verify mà recorder ghi {rec.rows[-1]['verifier_passed']!r}")


# ---------- W-4b: T24:00:00 phải bị schema chặn ----------

def test_hour_24_rejected_by_schema():
    reg = SchemaRegistry(ROOT / "schemas")
    bad = _ev(occurred_at="2026-07-29T24:00:00+07:00")
    assert reg.validate("advice_lifecycle_event", bad), (
        "T24:00:00 lọt schema nhưng giết datetime.fromisoformat ⇒ một record độc "
        "đánh sập toàn bộ decision_state")


# ---------- W-7: AdvisorPipeline sở hữu store ⇒ phải đóng được ----------

def test_pipeline_close_releases_db(tmp_path):
    from gsm_core.advisor.pipeline import AdvisorPipeline
    db = tmp_path / "ep.db"
    with AdvisorPipeline(corpus_path=CORPUS, store_path=db, llm_mode="off"):
        pass
    db.unlink()  # PermissionError [WinError 32] nếu connection còn giữ file


# ============ BATCH 2 — X-* (input thù địch) + F-S* (kỷ luật) ============

# ---------- F-S1: event_followed không được double-count ----------

def test_event_followed_not_double_counted(run_b, view_b):
    """Sim log MỘT lần theo bằng HAI event cùng decision_id (`advice_given` mang
    followed=True + `advice_followed` BRIDGE-3 khi advice đổi hành động). Trước sửa:
    event_followed shift_plan = 631 + 24 = 655 ⇒ event_adherence 54,2% thay vì 52,2%
    — lỗi nằm ngay trong thước đo A2 vừa xây, đúng họ BUG-EVAL-ARGMAX."""
    ev = run_b.events
    agg = _agg(view_b)
    gt = sum(1 for e in ev if e.kind == "advice_given" and e.detail.get("followed"))
    assert gt > 0
    assert agg["shift_plan"]["event_followed"] == gt


def test_event_adherence_bounded(view_b):
    for row in view_b.values():
        if row["event_adherence"] is not None:
            assert 0.0 <= row["event_adherence"] <= 1.0


# ---------- F-S7: pin decision-level accept_lift bằng GT tính độc lập ----------

def test_accept_lift_decision_level_pinned_to_gt(run_b, view_b):
    """GT decision-level tính ĐỘC LẬP: decision = (actor, bucket 30'); followed nếu có
    ít nhất một tick followed=True trong bucket. `<` suông có thể xanh khi bucketing
    hỏng kiểu 'gộp cả ngày' (T-046 rule 5)."""
    dec, fol = set(), set()
    for e in run_b.events:
        if e.kind != "advice_bonus_gate":
            continue
        key = (e.actor_id, int(e.t_min // 30))
        dec.add(key)
        if e.detail.get("followed"):
            fol.add(key)
    agg = _agg(view_b)
    assert dec and agg["accept_lift"]["decided"] == len(dec)
    assert agg["accept_lift"]["followed"] == len(fol)


# ---------- X-1 + F-S4: ngày LỊCH không hợp lệ phải bị chặn tại append ----------

def test_calendar_invalid_timestamps_rejected(tmp_path):
    """Regex không kiểm được lịch (2026-02-31 khớp mọi pattern) — boundary phải parse
    THẬT. Trước sửa: 5 dạng ngày độc persist VĨNH VIỄN vào store append-only (POST
    trả 200) rồi giết mọi decision_state về sau."""
    from gsm_core.lifecycle.event_log import AdviceEventLog
    bads = ["2026-02-31T08:00:00+07:00", "2026-13-01T08:00:00+07:00",
            "2026-07-45T08:00:00+07:00", "2026-07-29T08:00:00+25:00"]
    with AdviceEventLog(tmp_path / "cal.db") as log:
        for i, bad in enumerate(bads):
            with pytest.raises(ValueError):
                log.append(_store_ev(event_id=f"x{i}", occurred_at=bad))
        assert log.events() == []


def _store_ev(**kw) -> dict:
    b = _ev()
    b["payload"] = {}
    b.update(kw)
    return b


# ---------- X-2: derive_run_id digest — normalize numpy/date, từ chối kiểu lạ ----------

def test_run_id_digest_normalizes_numpy_and_rejects_sets():
    """default=str từng cho: np.int64(30) ≠ 30 (cùng semantic, khác ID) · set ⇒ ID đổi
    theo process (phá exact-repeat) · datetime vs chuỗi ISO ⇒ CÙNG ID (khác semantic,
    chiều nguy hiểm W-1)."""
    np = pytest.importorskip("numpy")
    base = Config.load("configs/pilot_dongda.yaml")
    a = Config(copy.deepcopy(base.data), base.root_dir)
    a.data["advice"]["bucket_min"] = np.int64(60)
    b = Config(copy.deepcopy(base.data), base.root_dir)
    b.data["advice"]["bucket_min"] = 60
    assert derive_run_id(a, 7) == derive_run_id(b, 7)
    c = Config(copy.deepcopy(base.data), base.root_dir)
    c.data["advice"]["weird"] = {1, 2}
    with pytest.raises(TypeError):
        derive_run_id(c, 7)


# ---------- X-3: adherence_view phải nhận được generator ----------

def test_adherence_view_accepts_generator():
    """Trước sửa: `decision_state` tiêu thụ generator ⇒ vòng event-level đếm 0 IM LẶNG
    (event_adherence=None đọc thành 'không có dữ liệu')."""
    evs = [_ev(event_id="g1"),
           _ev(event_id="g2", event_type="followed",
               occurred_at="2026-07-29T09:00:00+07:00")]
    view = P.adherence_view(e for e in evs)
    row = next(iter(view.values()))
    assert row["event_decided"] == 1 and row["event_followed"] == 1


# ---------- X-4: _offer_events fail-loud khi thiếu decision_id ----------

def test_offer_missing_decision_id_fails_loud():
    """assigned có người mà decision_ids thiếu ⇒ mẫu số hụt IM LẶNG — mở lại đúng lỗ
    F-1 từ hướng producer. Phải nổ (nhất quán triết lý fail-loud của F-7)."""
    from gsm_sim.world import Event
    ev = [Event(t_min=60.0, actor_id=-1, kind="standby_alloc", cell="c",
                detail={"n_assigned": 2, "assigned_ids": [1, 2],
                        "decision_ids": {"1": "slth-r-1-positioning-2"}},
                run_id="r")]
    with pytest.raises(ValueError, match="decision_id"):
        P.sim_events_to_lifecycle(ev)


# ---------- X-5: DB ngoại lai không PRIMARY KEY phải bị từ chối lúc mở ----------

def test_foreign_db_without_pk_rejected(tmp_path):
    """Không PK ⇒ INSERT OR IGNORE hết tác dụng — append cùng event_id trả True cả hai
    lần, idempotency chết KHÔNG MỘT TIẾNG ĐỘNG (đo được: 2 row)."""
    import sqlite3
    from gsm_core.lifecycle.event_log import AdviceEventLog
    db = tmp_path / "nopk.db"
    con = sqlite3.connect(db)
    con.execute("""CREATE TABLE advice_events (
        event_id TEXT, decision_id TEXT, display_id TEXT, driver_id TEXT,
        run_id TEXT, event_type TEXT, reason_code TEXT, occurred_at TEXT,
        observed_at TEXT, actor TEXT, origin TEXT, source TEXT,
        context_revision TEXT, schema_version TEXT, payload TEXT)""")
    con.commit()
    con.close()
    with pytest.raises(ValueError, match="PRIMARY KEY"):
        AdviceEventLog(db)


# ---------- X-7: ndarray phải nổ TƯỜNG MINH, không im lặng mất shape ----------

def test_normalize_ndarray_fails_loud_not_scalarized(tmp_path):
    """`.item()` từng biến np.array([5]) thành 5 (mất shape im lặng — mâu thuẫn
    'GIỮ NGUYÊN GIÁ TRỊ') và nổ ValueError lạc đề với array nhiều phần tử."""
    np = pytest.importorskip("numpy")
    from gsm_core.lifecycle.event_log import AdviceEventLog
    with AdviceEventLog(tmp_path / "nd.db") as log:
        with pytest.raises(TypeError):
            log.append(_store_ev(event_id="n1", payload={"arr": np.array([5])}))
        with pytest.raises(TypeError):
            log.append(_store_ev(event_id="n2", payload={"arr": np.array([1, 2])}))
        assert log.events() == []
