"""`D-M3-04-FIX` — hoãn nghỉ = CAM KẾT, nhánh rơi không được là WAIT (+ `D-M3-06`).

Vì sao tồn tại: UPDATE-140 đo được kênh `rest_window` đốt sức khoẻ không đổi lấy gì — hoãn nghỉ
biến thành CHỜ RỖNG (`world.py` cũ: `action := WAIT`; FIX-PRE chứng minh dòng đó là TOÀN BỘ cơ
chế, bit-identical 30/30 seed). Cường chốt (Q-16 + brainstorm 2026-08-05):

1. Hoãn = CAM KẾT: ghi "nghỉ ở giờ X"; tới X ép ở decision point kế; bận trọn giờ X ⇒ trả quyền
   nghỉ ngay (lần REST kế không bị phủ quyết).
2. Nhánh rơi không được là WAIT: không có hành động thay thế có ích ⇒ KHÔNG hoãn, cho nghỉ ngay.
3. Gộp `D-M3-06`: điều kiện hoãn chỉ còn REST (hai nhánh GO_SWAP/GO_CHARGE là code chết, 0/41).

Mỗi test có đối chứng ngược ở cạnh nó khi có thể. File này viết ĐỎ-TRƯỚC (2026-08-05).
"""
from __future__ import annotations

import pytest

from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.behavior import IdleAction, consider_relocate
from gsm_sim.config import Config
from gsm_sim.multiday import run_multiday
from gsm_sim.parallel import _cfg_with
from gsm_sim.policy import PolicyBundle
from gsm_sim.runner import run_once
from gsm_sim.world import rest_commit_gate


# ---------- fixtures ----------

@pytest.fixture(scope="module")
def base_cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def run_a(base_cfg):
    return run_once(base_cfg, seed=1000)


def _rest_bridge(base_cfg, actor_id):
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="single", single_actor_id=actor_id,
                            channels={"shift_plan": False, "accept_lift": False,
                                      "shift_extend": False, "rest_window": True},
                            positioning_overrides="off")
    return AdviceActionBridge(c, PolicyBundle.from_config(base_cfg), seed=1)


def _fresh_actor(run_a, idx=0):
    """Actor thật từ run, đưa về trạng thái 'giữa ca, khoẻ, pin đầy' để rail cũ không chặn."""
    a = run_a.actors[idx]
    a.soc_pct, a.online_min = 90.0, 60.0
    a.rest_deferred_min = 0.0
    a.rest_commit_due_min = None
    a.rest_commit_broken = False
    a.planned_rest_hour = None
    return a


ALT_RELOCATE = lambda _a: (IdleAction.RELOCATE, "8ffffffffffffff")   # noqa: E731
ALT_WAIT = lambda _a: (IdleAction.WAIT, None)                        # noqa: E731


def _defer_setup(base_cfg, run_a, *, hour=9, target=11):
    """Bridge + actor đã dàn cảnh để mọi kiểm KHUNG qua được: chỉ còn alt/cadence/coin quyết."""
    a = _fresh_actor(run_a)
    b = _rest_bridge(base_cfg, a.actor_id)
    a.planned_rest_hour = target          # rest_window_hour ưu tiên kế hoạch hôm qua (D-SIM-10)
    now = float(hour * 60 + 10)
    a.shift_start_min, a.shift_end_min = 0.0, 24 * 60.0
    return b, a, now


# ---------- 1. CAM KẾT được ghi + kế toán đúng đại lượng ----------

def test_commit_ghi_deadline_va_cong_dung_khoang_hoan(base_cfg, run_a):
    """Hoãn thành công ⇒ `rest_commit_due_min` = ĐẦU GIỜ X; `rest_deferred_min` cộng MỘT LẦN
    bằng đúng khoảng hoãn (không phải +2′/tick như bản cũ — cap 120′ nay đếm đúng đại lượng)."""
    b, a, now = _defer_setup(base_cfg, run_a, hour=9, target=11)
    b.coin_follows = lambda *ar, **kw: True          # cô lập: coin luôn nghe
    defer, why, alt = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_RELOCATE)
    assert defer and why == "defer_to_11h"
    assert alt == (IdleAction.RELOCATE, "8ffffffffffffff")
    assert a.rest_commit_due_min == 11 * 60.0        # đầu giờ X, phút tuyệt đối trong ngày
    # E1b ADV-08 (sửa CÓ CHỦ Ý 2026-08-06): khoảng hoãn THẬT = due − now = 120 − 10 = 110
    # (bản đầu của test này ghim nguyên minutes_to=120 — phóng đại phần now%60).
    assert a.rest_deferred_min == pytest.approx(110.0)


def test_doi_chung_coin_khong_nghe_thi_khong_cam_ket(base_cfg, run_a):
    b, a, now = _defer_setup(base_cfg, run_a)
    b.coin_follows = lambda *ar, **kw: False
    defer, why, alt = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_RELOCATE)
    assert not defer and why == "not_followed" and alt is None
    assert a.rest_commit_due_min is None and a.rest_deferred_min == 0.0


# ---------- 2. Nhánh rơi = WAIT ⇒ KHÔNG hoãn (điều 2 của Cường) ----------

def test_alt_wait_thi_khong_hoan(base_cfg, run_a):
    """Không có hành động thay thế có ích ⇒ không hoãn — TRƯỚC cadence/coin (lời khuyên không
    tồn tại thì không nén, đúng lý lẽ R-08). Mutation 'cho hoãn với WAIT' phải làm test này ĐỎ."""
    b, a, now = _defer_setup(base_cfg, run_a)
    b.coin_follows = lambda *ar, **kw: True
    spoken = []
    b.cadence_note_spoken = lambda *ar, **kw: spoken.append(ar)
    defer, why, alt = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_WAIT)
    assert not defer and why == "no_alt_action" and alt is None
    assert a.rest_commit_due_min is None
    assert spoken == [], "alt=WAIT mà vẫn note_spoken — thứ tự kiểm sai (phải TRƯỚC cadence)"


# ---------- 3. Cổng ép cam kết (world.rest_commit_gate) ----------

def test_gate_ep_rest_trong_gio_X(run_a):
    a = _fresh_actor(run_a)
    a.rest_commit_due_min = 11 * 60.0
    assert rest_commit_gate(a, 11 * 60.0 + 5) == "kept"
    assert a.rest_commit_due_min is None             # cam kết đã tiêu


def test_gate_chua_toi_gio_thi_im(run_a):
    a = _fresh_actor(run_a)
    a.rest_commit_due_min = 11 * 60.0
    assert rest_commit_gate(a, 10 * 60.0 + 59) is None
    assert a.rest_commit_due_min == 11 * 60.0        # còn nguyên


def test_gate_qua_gio_X_thi_vo_va_tra_quyen(run_a):
    """Bận trọn giờ X (decision point đầu tiên rơi sau X+60′) ⇒ cam kết VỠ + quyền nghỉ trả lại."""
    a = _fresh_actor(run_a)
    a.rest_commit_due_min = 11 * 60.0
    assert rest_commit_gate(a, 12 * 60.0 + 1) == "broken"
    assert a.rest_commit_due_min is None and a.rest_commit_broken is True


def test_gate_khong_cam_ket_thi_khong_lam_gi(run_a):
    a = _fresh_actor(run_a)
    assert rest_commit_gate(a, 11 * 60.0) is None
    assert a.rest_commit_broken is False


# ---------- 4. Quyền nghỉ đã trả ⇒ CẤM phủ quyết tới khi nghỉ thật ----------

def test_commit_broken_rail_chan_moi_phu_quyet(base_cfg, run_a):
    b, a, now = _defer_setup(base_cfg, run_a)
    a.rest_commit_broken = True
    b.coin_follows = lambda *ar, **kw: True
    defer, why, alt = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_RELOCATE)
    assert not defer and why == "commit_broken"


def test_doi_chung_khong_broken_thi_van_hoan_duoc(base_cfg, run_a):
    b, a, now = _defer_setup(base_cfg, run_a)
    b.coin_follows = lambda *ar, **kw: True
    defer, _, _ = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_RELOCATE)
    assert defer


def test_rail_suc_khoe_dung_TREN_cam_ket(base_cfg, run_a):
    """Đang có cam kết mở mà MỆT THẬT ⇒ nghỉ ngay (không tiếp tục né REST). Sức khoẻ > cam kết."""
    b, a, now = _defer_setup(base_cfg, run_a)
    a.rest_commit_due_min = 11 * 60.0
    a.online_min = a.fatigue_threshold_min + 30
    defer, why, _ = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_RELOCATE)
    assert not defer and why == "fatigued"


def test_cam_ket_mo_tiep_tuc_ne_rest_khong_coin_lai_khong_cong_quota(base_cfg, run_a):
    """Trước giờ X, bản năng lại muốn nghỉ: tiếp tục né bằng hành động có ích, KHÔNG rút coin
    lần nữa (quyết định đã ra), KHÔNG cộng thêm `rest_deferred_min` (đã book một lần)."""
    b, a, now = _defer_setup(base_cfg, run_a)
    a.rest_commit_due_min = 11 * 60.0
    a.rest_deferred_min = 120.0                      # đã book từ lúc cam kết
    b.coin_follows = lambda *ar, **kw: (_ for _ in ()).throw(AssertionError("coin bị rút lại"))
    defer, why, alt = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_RELOCATE)
    assert defer and why == "committed" and alt[0] == IdleAction.RELOCATE
    assert a.rest_deferred_min == 120.0              # không cộng thêm


def test_cam_ket_mo_ma_het_viec_thi_nghi_som(base_cfg, run_a):
    """Cam kết mở + alt=WAIT ⇒ nghỉ sớm (world nhánh REST sẽ xoá cam kết) — quy tắc no-WAIT áp
    ở MỌI quyết định, không chỉ lúc cam kết."""
    b, a, now = _defer_setup(base_cfg, run_a)
    a.rest_commit_due_min = 11 * 60.0
    defer, why, _ = b.should_defer_rest(a, now, 9, lambda ac, h: {"c": 1.0}, 20.0, ALT_WAIT)
    assert not defer and why == "commit_rest_early"


# ---------- 5. Reset ngày — bẫy D-E10-01 ----------

def test_cam_ket_khong_song_qua_dem(run_a):
    a = _fresh_actor(run_a)
    a.rest_commit_due_min, a.rest_commit_broken = 11 * 60.0, True
    a.reset_for_new_day(soc_pct=95.0, shift_start_min=6 * 60.0, shift_end_min=16 * 60.0)
    assert a.rest_commit_due_min is None and a.rest_commit_broken is False


# ---------- 6. consider_relocate — extraction thuần ----------

def test_consider_relocate_tra_wait_khi_khong_hint(run_a, base_cfg):
    import random
    a = _fresh_actor(run_a)
    action, target = consider_relocate(a, None, 9, None, random.Random(1), {})
    assert action == IdleAction.WAIT and target is None


# ---------- 7. Tích hợp: D-M3-06 + bảo toàn cam kết + event ----------

def _multiday_b(seed, days=3):
    cfg = _cfg_with(Config.load("configs/pilot_dongda.yaml"), enabled=True, actor_id=None,
                    channels={"shift_plan": False, "accept_lift": False, "shift_extend": False,
                              "rest_window": True, "positioning_overrides": "wait_only"},
                    coverage="all")
    return run_multiday(cfg, seed, days=days)


def test_tich_hop_co_che_co_duong_chay_va_bao_toan():
    """(a) Cơ chế PHẢI có đường chạy — cả CAM KẾT lẫn ÉP (chống D-R12 'sống trên giấy');
    (b) bảo toàn: made ≥ kept + broken + cleared (phần dư = cam kết còn mở cuối ngày);
    (c) khúc GIỮA: mỗi cam kết áp một relocate `rest_defer` NGAY tick đó — mũi sever
    'nhánh rơi lùi về WAIT' phải làm assert này đỏ (bài học j8/UPDATE-138: đừng chỉ kiểm
    hai đầu).

    ⚠ `advice_rest_window` là kind DÙNG CHUNG với bản ghi không-theo của nhánh drain
    (D-M3-01) ⇒ made phải lọc `followed=True` — không lọc là đếm lời khuyên bị TỪ CHỐI
    thành cam kết (chính tôi mắc 2026-08-05: đọc 5 thành cam kết trong khi chỉ có 2)."""
    tong = {"made": 0, "kept": 0, "broken": 0, "cleared": 0, "reloc": 0}
    for seed in (7000, 7001, 7002):
        md = _multiday_b(seed)
        made = kept = broken = cleared = reloc = 0
        for d in range(3):
            for e in md.days[d].events:
                if e.kind == "advice_rest_window":
                    # đối chứng D-M3-06: không lượt hoãn nào đến từ swap/charge
                    assert e.detail.get("deferred_from") in (None, "rest"), e.detail
                    made += e.detail.get("followed") is True
                kept += e.kind == "advice_rest_commit_kept"
                broken += e.kind == "advice_rest_commit_broken"
                cleared += e.kind == "advice_rest_commit_cleared"
                reloc += (e.kind == "relocate"
                          and e.detail.get("reason") == "rest_defer")
        assert kept + broken + cleared <= made, (seed, made, kept, broken, cleared)
        assert reloc >= made, (seed, reloc, made)   # khúc giữa: cam kết ⇒ relocate NGAY
        for k, v in zip(tong, (made, kept, broken, cleared, reloc)):
            tong[k] += v
    assert tong["made"] > 0, f"0 cam kết ở cả 3 seed × 3 ngày — cơ chế chết trên giấy: {tong}"
    assert tong["kept"] > 0, f"0 lần ÉP thành công — cổng cam kết chết trên giấy: {tong}"


def test_go_swap_khong_bi_hoan_du_kenh_bat(base_cfg, run_a):
    """`D-M3-06`: bản năng chọn GO_SWAP/GO_CHARGE thì KHÔNG đi qua đường hoãn — should_defer_rest
    giờ chỉ được hỏi cho REST. Kiểm ở world: SOC thấp ⇒ event charge/swap vẫn sinh bình thường
    và không có advice_rest_window nào mang deferred_from ≠ rest (đã kiểm ở test tích hợp);
    ở đây kiểm điều kiện tĩnh: world không còn tham chiếu GO_SWAP/GO_CHARGE cạnh should_defer_rest."""
    import inspect

    import gsm_sim.world as W
    src = inspect.getsource(W.World._actor_proc)
    i = src.find("should_defer_rest")
    assert i > 0
    window = src[max(0, i - 600):i]
    assert "GO_SWAP" not in window and "GO_CHARGE" not in window, \
        "điều kiện hoãn vẫn nhắc GO_SWAP/GO_CHARGE — nhánh chết chưa gỡ (D-M3-06)"
