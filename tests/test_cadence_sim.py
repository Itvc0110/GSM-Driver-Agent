"""ĐA-04 trong SIM — bằng chứng washout đã chết + nhịp chung hoạt động.

D-A3-01/D-SIM-14 (nợ CAO từ audit A3): coin tuân thủ được rút LẠI mỗi idle-tick 2′ tới
khi "thành công" ⇒ adherence danh nghĩa 0,30 có hiệu dụng ≈1,0, và **mọi con số A/B đều
kế thừa sai số này**. Cycle này thay bằng `adherence_coin` keyed theo
(decision_id, material_revision) — test dưới đây là thước đo cái chết của washout.
"""

from __future__ import annotations

import pytest

from gsm_core.lifecycle import projections as P
from gsm_sim.config import Config
from gsm_sim.runner import derive_run_id, run_once


def _cfg(cadence=True, **channels):
    c = Config.load("configs/pilot_dongda.yaml")
    ch = {"shift_plan": False, "accept_lift": False,
          "shift_extend": False, "rest_window": False}
    ch.update(channels)
    c.data["advice"].update(enabled=True, coverage="all", single_actor_id=None,
                            channels=ch, positioning_overrides="off")
    c.data["advice"].setdefault("cadence", {})["enabled"] = bool(cadence)
    return c


def _adherence_by_topic(result, cfg):
    lc = P.sim_events_to_lifecycle(result.events)
    view = P.adherence_view(lc)
    agg: dict[str, dict] = {}
    for (_run, _drv, topic), v in view.items():
        a = agg.setdefault(topic, {"decided": 0, "followed": 0, "dismissed": 0,
                                   "suppressed": 0,
                                   "event_decided": 0, "event_followed": 0})
        for k in a:
            a[k] += v[k]
    return agg


NOMINAL = {"P1": 0.55, "P2": 0.50, "P3": 0.30, "P4": 0.75,
           "P5": 0.30, "P6": 0.50, "P7": 0.50}


@pytest.fixture(scope="module")
def run_gate():
    """Kênh accept_lift — chỗ washout nặng nhất (fire mỗi tick 2′ trước ĐA-04)."""
    return run_once(_cfg(accept_lift=True), seed=1000)


def test_washout_dead_two_units_converge(run_gate):
    """Dấu hiệu washout CHẾT: hai đơn vị đo HỘI TỤ.

    Trước ĐA-04: decision 76,9% vs event 53,6% — lệch 23đp vì coin được rút lại mỗi tick
    tới khi thắng (decision "thành công" gần như chắc chắn, event thì không). Sau keyed
    coin, mỗi quyết định đúng MỘT coin ⇒ hai cách đếm phải cho gần cùng một số.
    Đo thật seed 1000: decision 68,1% · event 67,6% (lệch 0,5đp).

    KHÔNG assert bám trung bình danh nghĩa quần thể: người ĐƯỢC khuyên không phải mẫu
    ngẫu nhiên của quần thể (P4 tân binh chiếm ưu thế vì họ mới là người dưới ngưỡng) —
    đúng bài học BUG-EVAL-ARGMAX về chọn lọc mẫu."""
    agg = _adherence_by_topic(run_gate, None)
    a = agg.get("accept_lift")
    assert a and a["decided"] >= 20, f"kịch bản phải sinh đủ mẫu: {agg}"
    dec = a["followed"] / a["decided"]
    ev = a["event_followed"] / a["event_decided"]
    assert abs(dec - ev) <= 0.05, (
        f"decision {dec:.3f} vs event {ev:.3f} lệch >5đp — washout còn sống?")
    # và phải nằm trong dải danh nghĩa của các archetype có mặt (0,30–0,75)
    assert 0.30 <= dec <= 0.80, dec


def test_suppressed_not_in_adherence_denominator(run_gate):
    """Bị NÉN ≠ "nói mà không được nghe": suppressed phải đứng NGOÀI mẫu số.

    Bug tự bắt trong cycle này: suppressed lọt vào `decided` kéo decision_adherence
    xuống 0,25 trong khi event-level 0,68 — sai theo đúng kiểu ngược lại với washout."""
    agg = _adherence_by_topic(run_gate, None)
    a = agg["accept_lift"]
    assert a["decided"] <= a["event_decided"], (
        "decided (decision) không được vượt event_decided — dấu hiệu suppressed lọt vào")
    # R-04 (soi đối kháng vòng 2): dòng dưới đây TRƯỚC ĐÂY là
    #   assert decided == followed + dismissed + (decided - followed - dismissed)
    # — một ĐỒNG NHẤT THỨC đại số, đúng với mọi bộ số, không kiểm gì cả. Nó được viết ra
    # để "kiểm cấu trúc đếm nhất quán" nhưng thực chất là một dòng trang trí. Bất biến
    # THẬT phải nói được điều gì sai nếu suppressed lọt vào mẫu số:
    assert a["suppressed"] > 0, "kịch bản phải có lần bị nén, không thì test rỗng"
    assert a["followed"] + a["dismissed"] <= a["decided"], "hai nhánh không vượt mẫu số"
    # và mẫu số decision KHÔNG được chứa suppressed: cộng chúng vào phải VƯỢT event_decided
    # (chính là cái mà mutation 'leak đối xứng' sẽ làm)
    assert a["decided"] + a["suppressed"] > a["event_decided"], (
        "nếu suppressed nằm trong `decided` thì bất đẳng thức này không thể chặt")


def test_recheck_does_not_reroll(run_gate):
    """Cùng một quyết định (cùng bucket) không được có hai kết cục khác nhau."""
    per_decision: dict[str, set] = {}
    for e in run_gate.events:
        if e.kind != "advice_bonus_gate":
            continue
        per_decision.setdefault(e.detail["decision_id"], set()).add(
            bool(e.detail.get("followed")))
    assert per_decision, "phải có event bonus_gate"
    flip = {k: v for k, v in per_decision.items() if len(v) > 1}
    assert not flip, f"{len(flip)} quyết định bị RE-ROLL (washout): {list(flip)[:3]}"


def test_cadence_caps_and_suppression_events():
    """Ngân sách/cooldown thật sự nén, và mỗi lần nén để lại reason TYPED (không spam)."""
    r = run_once(_cfg(accept_lift=True, shift_extend=True, rest_window=True), seed=1000)
    sup = [e for e in r.events if e.kind == "advice_suppressed"]
    assert sup, "phải có event advice_suppressed khi nhịp nén"
    reasons = {e.detail.get("reason") for e in sup}
    assert reasons <= {"topic_cooldown", "shift_budget_exhausted", "dismissed_for_window",
                       "duplicate_window", "rest_would_override_productive_action"}, reasons
    # R-15: đòi CẢ HAI, không phải "một trong hai" — gõ nhầm key ở lớp parse config (cooldown
    # hiệu dụng 2′ ⇒ `topic_cooldown` biến mất) vẫn xanh nhờ budget nếu dùng `&`.
    assert {"topic_cooldown", "shift_budget_exhausted"} <= reasons, reasons
    # không spam: mỗi (actor, topic, reason, bucket) chỉ một event
    keys = [(e.actor_id, e.detail.get("channel"), e.detail.get("reason"),
             int(e.t_min // 20)) for e in sup]
    assert len(keys) == len(set(keys)), "event suppressed bị lặp — dedupe hỏng"


def test_cadence_config_actually_parsed_from_yaml():
    """R-15: pin độ lớn ở ĐÚNG LỚP có thể hỏng — lớp PARSE, không phải dataclass mặc định.

    `test_defaults_match_approved_baseline` pin `CadenceConfig()`, nhưng nếu bridge đọc sai
    key từ YAML thì dataclass vẫn đúng còn hành vi thì sai — test kia không đỏ.

    ⚠ Bản đầu còn assert `cadence_enabled is True`. Nay mặc định của sim là **False** (nhịp
    thuộc SẢN PHẨM — xem `test_mac_dinh_cua_config_ship_khong_co_nhip`); nhưng **độ lớn 20/6
    vẫn phải parse đúng** vì arm "sản phẩm-như-thiết-kế" dùng chúng."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.policy import PolicyBundle as SimPolicy
    c = Config.load("configs/pilot_dongda.yaml")
    b = AdviceActionBridge(c, SimPolicy.from_config(c), seed=1)
    assert b.cadence_cfg.min_gap_min_per_topic == 20.0, b.cadence_cfg
    assert b.cadence_cfg.max_proactive_per_shift == 6, b.cadence_cfg


def test_budget_respected_per_driver():
    """≤6 proactive/ca cho các kênh tính ngân sách (positioning ngoài budget — có căn cứ)."""
    r = run_once(_cfg(accept_lift=True, shift_extend=True, rest_window=True), seed=1000)
    per_actor: dict[int, int] = {}
    budgeted = {"advice_bonus_gate", "advice_shift_extend", "advice_rest_window",
                "advice_given"}
    for e in r.events:
        if e.kind in budgeted:
            per_actor[e.actor_id] = per_actor.get(e.actor_id, 0) + 1
    assert per_actor, "phải có advice"
    worst = max(per_actor.values())
    assert worst <= 6, f"vượt ngân sách 6/ca: max={worst}"


def test_exact_repeat_with_cadence():
    """R-14 (soi đối kháng vòng 2): so CẢ `cell` và `detail`.

    Bản đầu chỉ so `(t_min, actor_id, kind)` — trong khi `detail` chứa `decision_id`,
    `followed`, `reason`: đúng những trường mọi projection join theo. Nondeterminism ở đó
    lọt lưới, dù CLAUDE.md đòi bit-identical. Chi phí siết = 0 nếu code vốn đã đúng."""
    a = run_once(_cfg(accept_lift=True), seed=1000)
    b = run_once(_cfg(accept_lift=True), seed=1000)
    key = lambda r: [(e.t_min, e.actor_id, e.kind, e.cell, e.detail) for e in r.events]
    assert key(a) == key(b)


def test_world_a_untouched_crn():
    """CRN: bật code advice mà KHÔNG phủ ai ⇒ thế giới A không đổi một bit.

    R-13 (soi đối kháng vòng 2): bản đầu là
        assert summarize(run_once(base, 1000)) == summarize(run_once(base, 1000))
    — **so một biểu thức với chính nó**. Nó chỉ kiểm determinism, KHÔNG kiểm điều tên test
    tuyên bố. Kịch bản lọt lưới: code advice tiêu thêm một draw từ stream CHUNG dù đã tắt ⇒
    lệch NHẤT QUÁN cả hai lần ⇒ xanh, trong khi thế giới A của mọi phép so A/B đã khác."""
    from gsm_sim.metrics import summarize
    base = Config.load("configs/pilot_dongda.yaml")
    armed = Config.load("configs/pilot_dongda.yaml")
    armed.data["advice"].update(enabled=True, coverage="none", single_actor_id=None,
                                positioning_overrides="off",
                                channels={"shift_plan": True, "accept_lift": True,
                                          "shift_extend": True, "rest_window": True})
    a, b = run_once(base, seed=1000), run_once(armed, seed=1000)
    assert summarize(a) == summarize(b), "bật code advice mà không phủ ai vẫn đổi thế giới A"
    key = lambda r: [(e.t_min, e.actor_id, e.kind, e.cell) for e in r.events]
    assert key(a) == key(b)


# ---------- CỜ CẤU HÌNH PHẢI THẬT SỰ ĐIỀU KHIỂN ĐƯỢC ----------

def test_coin_is_keyed_even_when_cadence_off(monkeypatch):
    """DET-01: cờ `cadence.enabled` CHỈ được điều khiển NHỊP, không được đổi CƠ CHẾ rút coin.

    Bản đầu có nhánh `if not cadence_enabled: rng.random()` ⇒ arm đối chứng của mọi ablation
    vừa mất nhịp vừa hồi sinh washout (đo thật: adherence hiệu dụng arm OFF +0,173 so danh
    nghĩa, arm ON +0,078) ⇒ mọi Δ "giá của nhịp" thổi phồng. Test này khoá bằng hai bất biến
    KHÔNG phụ thuộc số liệu: (a) hỏi lại cùng quyết định ra cùng câu trả lời; (b) `self.rng`
    không bị coin tiêu."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.policy import PolicyBundle as SimPolicy
    c = _cfg(cadence=False, accept_lift=True)
    b = AdviceActionBridge(c, SimPolicy.from_config(c), seed=7)
    actor = type("A", (), {"actor_id": 3, "archetype": "P3",
                           "shift_start_min": 360.0, "shift_end_min": 1080.0})()

    # (a) deterministic: 15 lần hỏi lại trong cùng bucket ⇒ MỘT câu trả lời
    ans = {b.coin_follows(actor, "accept_lift", 600.0 + 2 * i, "lift") for i in range(15)}
    assert len(ans) == 1, f"cadence off vẫn phải MỘT coin/quyết định, nhận {ans}"

    # (b) rng của bridge KHÔNG bị coin tiêu (nếu bị, bật/tắt kênh sẽ xê dịch stream khác)
    before = b.rng.bit_generator.state["state"]["state"]
    for i in range(20):
        b.coin_follows(actor, "accept_lift", 600.0 + 2 * i, "lift")
    assert b.rng.bit_generator.state["state"]["state"] == before, "coin vẫn tiêu self.rng"


def test_cadence_state_does_not_leak_across_days():
    """Trạng thái nhịp phải RESET mỗi ngày — ngân sách là ngân sách MỖI CA.

    Lăng kính determinism nghi ngờ `_suppressed_seen`/`_effect_applied`/`_cadence_mem` tồn
    tại xuyên ngày trong sim nhiều ngày. Đọc code thì KHÔNG (mỗi ngày `multiday` dựng `World`
    mới, `World` dựng bridge mới) — nhưng đó là bất biến do KIẾN TRÚC, không do luật, nên nó
    sẽ vỡ im lặng nếu ai đó tái dùng World để tiết kiệm. Test này biến nó thành luật.

    Nếu rò: ngày 2 thừa hưởng ngân sách đã cạn của ngày 1 ⇒ advisor im từ đầu ngày 2, và
    mọi Δ nhiều-ngày sai theo một chiều không ai nhìn ra."""
    from gsm_sim.multiday import run_multiday
    res = run_multiday(_cfg(accept_lift=True, shift_extend=True, rest_window=True),
                       seed=1000, days=2)
    spoken = {"advice_bonus_gate", "advice_shift_extend", "advice_rest_window", "advice_given"}
    per_day = [len([e for e in d.events if e.kind in spoken]) for d in res.days]
    assert len(per_day) == 2, per_day
    assert all(n > 0 for n in per_day), (
        f"ngày nào cũng phải có lời khuyên; {per_day} ⇒ ngân sách rò qua ngày")
    # ngân sách 6/ca phải được tôn trọng TỪNG NGÀY, không phải cộng dồn
    for i, d in enumerate(res.days):
        per_actor: dict[int, int] = {}
        for e in d.events:
            if e.kind in spoken:
                per_actor[e.actor_id] = per_actor.get(e.actor_id, 0) + 1
        assert per_actor and max(per_actor.values()) <= 6, (i, max(per_actor.values()))


def test_suppressed_events_are_not_phantom():
    """R-08: chỉ ghi "bị nén" khi THẬT SỰ có lời khuyên để nói.

    Ba kênh từng hỏi `cadence_allows` ở ĐẦU hàm — trước khi biết có nội dung gì — nên mỗi
    tick "không có gì để nói" vẫn ghi một event nén cho một lời khuyên KHÔNG TỒN TẠI. Đo
    được 50% tổng số nén là ma (`accept_lift` 93%, `rest_window` **100%**), và chính con số
    ma đó làm tôi chẩn đoán sai rằng "rest_window chết đói ngân sách".

    Bất biến kiểm ở đây: **một kênh chưa từng NÓI thì cũng không được có event bị NÉN** —
    nếu nó chưa bao giờ có gì để nói thì không có gì để nén."""
    r = run_once(_cfg(accept_lift=True, shift_extend=True, rest_window=True), seed=1000)
    spoken = {"advice_bonus_gate": "accept_lift", "advice_shift_extend": "shift_extend",
              "advice_rest_window": "rest_window"}
    said = {ch for k, ch in spoken.items() if any(e.kind == k for e in r.events)}
    nen = {(e.detail or {}).get("channel") for e in r.events if e.kind == "advice_suppressed"}
    ma = nen - said - {"positioning", "shift_plan"}   # shift_plan cố ý KHÔNG sửa (xem #23)
    assert not ma, (
        f"kênh {ma} có event bị NÉN nhưng chưa từng NÓI ⇒ nén một lời khuyên không tồn tại")


def test_one_decision_one_effect_application():
    """R-01: MỘT quyết định được nghe theo ⇒ ĐÚNG MỘT lần áp tác động.

    Chạy ở arm `cadence=off` — nơi không có cooldown nên cùng một quyết định bị hỏi lại
    nhiều lần và keyed coin trả CÙNG câu trả lời. Trước fix, mỗi lần hỏi lại đều cộng thêm
    `accept_lift` ⇒ arm đối chứng nhận liều can thiệp mạnh gấp 2,0–2,5 lần, và Δ của nó
    không còn là "giá của nhịp".

    Bất biến: **số event có `lift_applied > 0` = số QUYẾT ĐỊNH riêng biệt được nghe theo**.
    (Mutation bỏ `_claim_effect` từng bị bắt bởi một test dedupe KHÔNG liên quan — bắt được
    do may. Test này bắt đúng chỗ.)"""
    r = run_once(_cfg(cadence=False, accept_lift=True), seed=1000)
    gate = [e for e in r.events if e.kind == "advice_bonus_gate"]
    assert gate, "kịch bản phải sinh event bonus_gate"
    # tên trường trong event là `lift` (không phải `lift_applied` của dataclass) — kiểm bằng
    # dữ liệu thật thay vì đoán: bản đầu của test này đoán sai tên và cho 0/58, suýt đọc
    # thành "R-01 sống lại" trong khi code đúng. Cùng bài học Lỗi #7.
    assert "lift" in gate[0].detail, sorted(gate[0].detail)
    applied = [e for e in gate if float(e.detail.get("lift", 0) or 0) > 0]
    followed_ids = {e.detail["decision_id"] for e in gate if e.detail.get("followed")}
    assert len(applied) == len(followed_ids), (
        f"{len(applied)} lần ÁP TÁC ĐỘNG cho {len(followed_ids)} quyết định được nghe theo "
        "⇒ một quyết định bị áp nhiều lần (R-01 sống lại)")
    # và phải có ít nhất một quyết định BỊ HỎI LẠI, không thì test rỗng
    assert len(gate) > len(followed_ids), "kịch bản phải có hỏi-lại, không thì không kiểm được gì"


def test_cadence_disabled_returns_to_baseline():
    """Tắt cadence ⇒ KHÔNG còn event nén nào (disabled factor quay về baseline).

    Bẫy đã gặp nhiều lần trong repo này: thêm cờ nhưng nhánh tắt vẫn đi qua code mới ⇒
    "so có/không tính năng" thật ra so hai biến thể của tính năng."""
    budgeted = {"advice_bonus_gate", "advice_shift_extend", "advice_rest_window",
                "advice_given"}

    def _worst(r):
        per: dict[int, int] = {}
        for e in r.events:
            if e.kind in budgeted:
                per[e.actor_id] = per.get(e.actor_id, 0) + 1
        return max(per.values()) if per else 0

    off = run_once(_cfg(cadence=False, accept_lift=True, shift_extend=True,
                        rest_window=True), seed=1000)
    on = run_once(_cfg(cadence=True, accept_lift=True, shift_extend=True,
                       rest_window=True), seed=1000)
    assert not [e for e in off.events if e.kind == "advice_suppressed"]
    assert [e for e in on.events if e.kind == "advice_suppressed"], "arm bật phải có nén"
    # R-05 (soi đối kháng vòng 2): hai assertion trên chỉ kiểm sự VẮNG MẶT của telemetry —
    # một mutation nén thật nhưng không ghi event sẽ sống sót, và lưới 2×2 sẽ so "ON vs ON
    # không log". Bất biến phải nói về HÀNH VI: tắt cadence ⇒ ngân sách 6/ca KHÔNG còn hiệu
    # lực ⇒ phải tồn tại tài xế vượt 6.
    assert _worst(off) > 6, f"tắt cadence mà không ai vượt 6/ca ⇒ ngân sách vẫn sống: {_worst(off)}"
    assert _worst(on) <= 6, f"bật cadence phải tôn trọng trần 6/ca, nhận {_worst(on)}"


def test_count_positioning_in_budget_flag_is_alive():
    """Cờ `count_positioning_in_budget` phải ĐỔI được hành vi — nếu không nó là cờ CHẾT.

    Mặc định False (positioning ngoài ngân sách vì là kênh dương SIG duy nhất). Bật lên
    thì positioning phải bắt đầu ăn ngân sách ⇒ số lần nói về vị trí giảm."""
    from gsm_sim.metrics import summarize

    def _run(flag: bool):
        c = _cfg(accept_lift=True, shift_extend=True, rest_window=True)
        c.data["advice"]["positioning_overrides"] = "wait_only"
        c.data["advice"]["cadence"]["count_positioning_in_budget"] = flag
        r = run_once(c, seed=1000)
        pos_sup = {e.detail.get("reason") for e in r.events
                   if e.kind == "advice_suppressed"
                   and e.detail.get("channel") == "positioning"}
        n_assigned = sum(int(e.detail.get("n_assigned", 0))
                         for e in r.events if e.kind == "standby_alloc")
        return pos_sup, n_assigned, summarize(r)

    # Bất biến về CƠ CHẾ, không về độ lớn: cờ tắt ⇒ positioning KHÔNG hề đi qua cổng nhịp
    # (call site short-circuit) ⇒ không có event nén nào của nó; cờ bật ⇒ nó chịu cổng như
    # mọi kênh khác ⇒ phải xuất hiện.
    #
    # ⚠ Bản đầu của test này khẳng định `n_on < n_off` — một hiệu ứng CÓ HƯỚNG chứ không
    # phải bất biến: khi positioning tiêu ngân sách, các kênh khác cạn suất sớm hơn, và
    # tổng số người được gán là kết quả TƯƠNG TÁC, có thể tăng hoặc giảm. Test đó đỏ ngay
    # khi R-01/R-09 đổi động lực (80 vs 79) dù cờ vẫn hoạt động hoàn hảo. Đúng loại test
    # giòn mà soi đối kháng cảnh báo — khẳng định cơ chế, đừng khẳng định số emergent.
    sup_off, n_off, sum_off = _run(False)
    sup_on, n_on, sum_on = _run(True)

    assert not sup_off, f"cờ TẮT: positioning không được đi qua cổng nhịp, nhận {sup_off}"
    assert sup_on, "cờ BẬT: positioning phải chịu cổng nhịp — không thấy event nén ⇒ cờ CHẾT"
    assert sum_on != sum_off, "cờ đổi mà kết quả y hệt ⇒ cờ không tới được engine"


# ---------- NHỊP THUỘC SẢN PHẨM: sim mặc định KHÔNG có nhịp ----------

@pytest.mark.parametrize("seed", [1000, 1001, 1002, 2000, 3160])
def test_tat_nhip_khong_lam_washout_song_lai(seed):
    """PHẢN CHỨNG cho quyết định "nhịp thuộc sản phẩm" (Cường chất vấn 2026-07-29).

    Lập luận cũ của tôi: *"cooldown/ngân sách phải có ở sim vì A/B phải đo đúng thứ sẽ ship"*.
    Cường chỉ ra nó SAI: sim đo **trần giá trị của lời khuyên**; im-sau-khi-bị-bỏ-qua và ngân
    sách chú ý là ràng buộc **UX của sản phẩm**.

    Nhưng trước khi đổi mặc định, phải loại một khả năng: **cooldown có đang gánh một phần tính
    ĐÚNG ĐẮN của phép đo mà tôi chưa nhận ra?** Nếu tắt nhịp làm hai đơn vị adherence tách ra
    thì washout sống lại và quyết định này SAI.

    Bản ĐẦU của test này đòi *hai đơn vị adherence hội tụ* — và nó **ĐỎ cả 5 seed**
    (decision 0,674 vs event 0,500). Tôi đã suýt kết luận "cooldown gánh tính đúng đắn, không
    được đổi mặc định". **Sai.** Đo tiếp thì ra nguyên nhân khác hẳn: **hiệu ứng chọn lọc — số
    lần HỎI phụ thuộc CÂU TRẢ LỜI.** Không cooldown thì bucket bị bỏ qua bị hỏi lại **4,93
    lần**, bucket được nghe theo chỉ **2,38 lần** (được nghe theo ⇒ `acc` tăng ⇒ kênh thôi hỏi).
    Nên event-level **đếm thiếu** các bucket followed.

    Bằng chứng washout KHÔNG sống lại: **decision-level lệch so danh nghĩa +0,057 ở arm TẮT vs
    +0,055 ở arm BẬT** — như nhau. Washout thổi phồng DECISION-level; ở đây decision-level ổn
    định, chỉ event-level lệch.

    ⇒ Bất biến ĐÚNG (test dưới đây): **decision-level phải sát danh nghĩa ở CẢ HAI arm**.
    ⇒ **LUẬT ĐO MỚI**: ở arm không-nhịp, **KHÔNG dùng event-level adherence** — chỉ dùng
    decision-level. `_adherence_by_topic` vẫn trả cả hai; đọc sai cột là đọc sai 17 điểm %."""
    NOM = {"P1": .55, "P2": .50, "P3": .30, "P4": .75, "P5": .30, "P6": .50, "P7": .50}
    for cadence in (True, False):
        r = run_once(_cfg(cadence=cadence, accept_lift=True), seed)
        a = _adherence_by_topic(r, None).get("accept_lift")
        assert a and a["decided"] >= 20, f"seed {seed} cadence={cadence} thiếu mẫu"
        dec = a["followed"] / a["decided"]
        ids = {e.actor_id for e in r.events if e.kind == "advice_bonus_gate"}
        arch = {x.actor_id: x.archetype for x in r.actors}
        nom = sum(NOM.get(arch[i], .5) for i in ids) / max(len(ids), 1)
        assert abs(dec - nom) <= 0.12, (
            f"seed {seed} cadence={cadence}: decision {dec:.3f} vs danh nghĩa {nom:.3f} "
            "lệch >12đp ⇒ washout hoặc lỗi họ khác")


def test_mac_dinh_cua_config_ship_khong_co_nhip():
    """Mặc định `configs/pilot_dongda.yaml` phải là **KHÔNG NHỊP** — sim đo trần.

    Chiều ngược của test cũ (`test_cadence_config_actually_parsed_from_yaml` từng pin
    `enabled is True`). Nhịp không bị XOÁ — vẫn bật được bằng cờ để chạy arm "sản phẩm-như-
    thiết-kế"; chỉ đổi MẶC ĐỊNH."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.policy import PolicyBundle as SimPolicy
    c = Config.load("configs/pilot_dongda.yaml")
    b = AdviceActionBridge(c, SimPolicy.from_config(c), seed=1)
    assert b.cadence_enabled is False, (
        "sim mặc định phải KHÔNG có nhịp — nhịp là ràng buộc UX của sản phẩm")
    # nhưng cơ chế vẫn còn nguyên và bật được
    c2 = Config.load("configs/pilot_dongda.yaml")
    c2.data["advice"]["cadence"]["enabled"] = True
    b2 = AdviceActionBridge(c2, SimPolicy.from_config(c2), seed=1)
    assert b2.cadence_enabled is True and b2.cadence_cfg.min_gap_min_per_topic == 20.0
    # và mặc định phải cho 0 event nén
    r = run_once(_cfg_ship(), seed=1000)
    assert not [e for e in r.events if e.kind == "advice_suppressed"], (
        "config mặc định vẫn sinh event nén ⇒ nhịp chưa thật sự tắt")


def _cfg_ship():
    """Config SHIP nguyên bản — không ghi đè gì (dùng để kiểm mặc định thật)."""
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="all", single_actor_id=None,
                            channels={"shift_plan": True, "accept_lift": True,
                                      "shift_extend": True, "rest_window": True})
    return c


# ---------- RANH GIỚI SIM ↔ SẢN PHẨM (chỉ thị Cường 2026-07-29) ----------

def test_sim_never_suppresses_by_dismiss(run_gate):
    """Cường: *"việc đo hiệu quả của phần mềm trong sim không nên bị ảnh hưởng bởi việc
    tắt gợi ý khi xế bấm nút bỏ qua; sim là để đo hiệu quả của 1 xã hội driver tuân theo
    lời khuyên so với 1 xã hội driver khi chưa có hệ thống và làm việc với quy tắc
    random."*

    ⇒ `dismissed_for_window` là cơ chế của SẢN PHẨM THẬT (UI), KHÔNG được xuất hiện
    trong sim. Sim mô hình hoá "nghe hay không nghe" bằng adherence coin — không có nút
    bấm. Test này khoá ranh giới đó lại để không ai vô tình nối dismiss vào sim rồi làm
    bẩn phép đo A/B."""
    reasons = {e.detail.get("reason") for e in run_gate.events
               if e.kind == "advice_suppressed"}
    assert "dismissed_for_window" not in reasons, reasons
    r2 = run_once(_cfg(accept_lift=True, shift_extend=True, rest_window=True), seed=1001)
    reasons2 = {e.detail.get("reason") for e in r2.events if e.kind == "advice_suppressed"}
    assert "dismissed_for_window" not in reasons2, reasons2


def test_sim_cadence_memory_has_no_dismiss_state():
    """Cùng ranh giới, kiểm ở tầng cấu trúc: bridge KHÔNG BAO GIỜ nuôi `dismissed_in_phase`
    (nếu ai đó thêm, test này đỏ và buộc họ đọc lại chỉ thị ở trên)."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.policy import PolicyBundle as SimPolicy
    c = _cfg(accept_lift=True)
    b = AdviceActionBridge(c, SimPolicy.from_config(c), seed=1)
    mem = b._mem(0)
    assert mem.dismissed_in_phase == {}
    import inspect
    src = inspect.getsource(AdviceActionBridge)
    assert "dismissed_in_phase[" not in src, "sim không được ghi dismissed (UI-only)"
    # R-19: grep source né được bằng `.update({...})`/`setattr`. Kiểm thêm ở RUNTIME sau một
    # run thật — bằng chứng ranh giới được GIỮ, không phải bằng chứng về cú pháp.
    from gsm_sim.runner import run_once as _run
    cfg2 = _cfg(accept_lift=True, shift_extend=True, rest_window=True)
    b2 = AdviceActionBridge(cfg2, SimPolicy.from_config(cfg2), seed=1000)
    _run(cfg2, seed=1000)
    for m2 in b2._cadence_mem.values():
        assert m2.dismissed_in_phase == {}, "sim nuôi dismissed ⇒ ranh giới bị phá"
