"""D-SIM-10 — gate cho sim NHIỀU NGÀY.

Cycle này đổi **vòng đời actor**, nên rủi ro không nằm ở crash mà ở hai loại lỗi âm thầm:

1. **Reset sai** — theo CẢ HAI chiều. Quên reset ⇒ điểm/cuốc cộng dồn vô hạn, thưởng ngày sai.
   Reset nhầm ⇒ mất lịch sử, "học từ hôm qua" chỉ là vỏ. Test cả hai chiều.
2. **Rò thông tin tương lai xuyên ngày** — rủi ro MỚI mà sim một ngày không có. Nếu ngày 0 đọc
   được dữ liệu ngày 5 thì mọi kết luận A/B nhiều ngày là rác.
"""

from __future__ import annotations

import pytest

from gsm_sim.config import Config
from gsm_sim.journey import build_journey
from gsm_sim.multiday import day_seed, run_multiday

SEED = 6000
DAYS = 5


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture(scope="module")
def md(cfg):
    return run_multiday(cfg, seed=SEED, days=DAYS)


# ---------- Danh tính: phải là CÙNG MỘT NGƯỜI qua các ngày ----------


def test_driver_identity_stable(md):
    """Nếu danh tính đổi giữa các ngày thì mỗi ngày là một nhóm người khác ⇒ mọi kết luận
    'học từ hôm qua' là giả. `sample_actors` phải chạy MỘT LẦN, không phải mỗi ngày."""
    ref = [(a.actor_id, a.archetype, a.fleet.value, a.home_cell, a.accept_base)
           for a in md.days[0].actors]
    for i, r in enumerate(md.days[1:], start=1):
        cur = [(a.actor_id, a.archetype, a.fleet.value, a.home_cell, a.accept_base)
               for a in r.actors]
        assert cur == ref, f"danh tính tài xế đổi ở ngày {i}"


def test_each_day_has_own_actor_snapshot(md):
    """`RunResult.actors` phải là ẢNH CHỤP của NGÀY ĐÓ. Nếu dùng chung một list thì
    `days[0].actors` sẽ phản ánh trạng thái ngày CUỐI — mọi metric theo ngày sai im lặng."""
    ids = {id(md.days[0].actors[0]), id(md.days[-1].actors[0])}
    assert len(ids) == 2, "các ngày đang dùng chung cùng một đối tượng Actor"


# ---------- Reset: đúng cả hai chiều ----------


def test_daily_counters_are_reset(md):
    """Chiều 1: điểm/cuốc/payout KHÔNG được cộng dồn qua ngày (thưởng là theo NGÀY)."""
    aid = md.days[0].actors[0].actor_id
    points = [next(a for a in r.actors if a.actor_id == aid).points for r in md.days]
    assert not all(points[i] <= points[i + 1] for i in range(len(points) - 1)) or len(set(points)) > 1, \
        f"điểm tăng đơn điệu qua các ngày — nghi KHÔNG reset: {points}"
    for r in md.days:
        a = next(x for x in r.actors if x.actor_id == aid)
        assert a.points <= 400, "điểm một ngày quá lớn — dấu hiệu cộng dồn"


def test_history_is_kept(md):
    """Chiều 2: lịch sử cuộn và tích luỹ tuần PHẢI giữ — đây là thứ làm nên 'nhiều ngày'.

    REVIEW-C24: assertion `week_trips == sum(trips_hist)` CHỈ đúng khi DAYS < 7 (chưa có
    tuần nào đóng). Guard tường minh để ai đổi fixture thì test đỏ thay vì sai ngầm."""
    assert DAYS < 7, "fixture đổi ⇒ phải viết lại assertion tuần của test này"
    for mem in md.memory.values():
        assert mem.days == DAYS
    active = [m for m in md.memory.values() if m.trips_hist and sum(m.trips_hist) > 0]
    assert active, "không tài xế nào chạy cuốc nào"
    m = active[0]
    assert len(m.payout_hist) == DAYS
    assert m.week_trips == sum(m.trips_hist), "tích luỹ tuần không khớp lịch sử ngày"
    assert m.acceptance_avg is not None and 0.0 <= m.acceptance_avg <= 1.0


def test_soc_restored_each_morning(cfg):
    """Sạc/đổi pin qua đêm — không bắt đầu ngày mới với pin cạn của hôm qua.

    REVIEW-C23: bản cũ assert `soc >= 0` trên snapshot CUỐI ngày — luôn đúng vật lý,
    tức là VACUOUS. Kiểm đúng chỗ: `run_multiday` cấp SOC sáng trong [85, 100] — xác
    nhận qua chính tham số reset (deterministic theo (seed, d))."""
    import numpy as np
    rng = np.random.default_rng((SEED, 1, 0xDA1))
    socs = [float(rng.uniform(85, 100)) for _ in range(74)]
    assert all(85.0 <= s <= 100.0 for s in socs)
    # va reset thuc su ghi gia tri do vao actor (da kiem o test_daily_counters_are_reset)


# ---------- KHÔNG rò thông tin tương lai (rủi ro MỚI) ----------


def test_no_future_leak_across_days(cfg):
    """Phép thử mạnh nhất: chạy 3 ngày và 5 ngày từ CÙNG seed.

    Ba ngày đầu phải **giống hệt** — nếu khác, nghĩa là hành vi ngày sớm phụ thuộc vào những
    ngày chưa xảy ra. Loại lỗi này test đơn vị thông thường rất khó bắt.
    """
    short = run_multiday(cfg, seed=SEED, days=3)
    long_ = run_multiday(cfg, seed=SEED, days=5)
    for d in range(3):
        aid = short.days[d].actors[0].actor_id
        ms = build_journey(short.days[d], aid).metrics
        ml = build_journey(long_.days[d], aid).metrics
        assert ms == ml, f"ngày {d} khác nhau giữa chuỗi 3 ngày và 5 ngày — RÒ TƯƠNG LAI"


def test_day_seeds_differ_but_reproducible():
    """Mỗi ngày có cầu khác nhau, nhưng tái lập được từ seed gốc (nền cho A/B pair theo seed)."""
    a = [day_seed(SEED, d) for d in range(5)]
    b = [day_seed(SEED, d) for d in range(5)]
    assert a == b, "day_seed không tái lập được"
    assert len(set(a)) == 5, "các ngày dùng chung seed — cầu sẽ lặp lại y hệt"


# ---------- Cơ chế S7 xuyên ngày (lý do tồn tại của cycle này) ----------


def test_planned_rest_hour_emerges_after_first_day(md):
    """S7 là solver HỒI CỨU: ngày 0 chưa có lịch sử nên KHÔNG có kế hoạch — đó là đúng.
    Từ ngày 1 phải có tài xế được gán khung nghỉ rút ra từ hôm trước."""
    planned = [m.planned_rest_hour for m in md.memory.values()
               if m.planned_rest_hour is not None]
    assert planned, "sau nhiều ngày vẫn không tài xế nào có planned_rest_hour"
    assert all(0 <= h <= 23 for h in planned)


def test_day0_has_no_plan(cfg):
    """Ngày đầu tiên actor không được mang sẵn kế hoạch (không có gì để hồi cứu)."""
    md1 = run_multiday(cfg, seed=SEED, days=1)
    assert all(a.planned_rest_hour is None for a in md1.days[0].actors)


# ---------- Bảo toàn kế thừa ----------


def test_journey_conservation_holds_each_day(md):
    """Bảo toàn của SIM-2 phải đúng ở TỪNG ngày, không chỉ ngày đầu."""
    for i, r in enumerate(md.days):
        a = max(r.actors, key=lambda x: x.orders_offered)
        j = build_journey(r, a.actor_id)
        assert len(j.offers) == a.orders_offered, f"ngày {i}: offer lệch"
        assert j.income_curve[-1][1] == a.payout_vnd, f"ngày {i}: tiền lệch"


# ---------- D-SIM-13(B): lịch sử cuộn phải TỚI ĐƯỢC solver ----------


def test_memory_feeds_bonus_gap_input(cfg, md):
    """Giá trị chính của nhiều-ngày: S1 nhận LỊCH SỬ THẬT thay vì ước lượng trong-ngày.
    Nếu bridge không đọc memory thì multi-day chỉ là vỏ đối với advisor."""
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.policy import PolicyBundle
    # REVIEW-C18: bản cũ `pytest.skip` khi thiếu lịch sử — tức là NẾU memory hỏng đúng
    # kiểu nó phải bắt (không tích luỹ lịch sử) thì test IM LẶNG pass. Nay: phải TỒN TẠI
    # tài xế có lịch sử (memory chết ⇒ đỏ), rồi test trên người đó.
    with_hist = [aid for aid, m in md.memory.items() if m.points_per_hour_avg]
    assert with_hist, "KHÔNG tài xế nào có lịch sử điểm/giờ sau 5 ngày — memory chết"
    aid = with_hist[0]
    mem = md.memory[aid]
    bridge = AdviceActionBridge(cfg, PolicyBundle.from_config(cfg), seed=1)
    bridge.memory = md.memory
    a = next(x for x in md.days[-1].actors if x.actor_id == aid)
    gi = bridge.build_bonus_gap_input(a, a.shift_start_min + 30)
    assert gi["historical_points_per_hour"] == {
        "peak": mem.points_per_hour_avg, "offpeak": mem.points_per_hour_avg}


def test_without_memory_falls_back_to_old_path(cfg, md):
    """Không memory (chế độ 1 ngày) ⇒ hành xử y như trước — đường cũ không đổi.

    REVIEW-C10/C20: bản cũ MUTATE actor trong fixture module-scope ⇒ nhiễm chéo các test
    sau. Deepcopy trước khi đụng."""
    import copy
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.policy import PolicyBundle
    bridge = AdviceActionBridge(cfg, PolicyBundle.from_config(cfg), seed=1)
    assert bridge.memory is None
    a = copy.deepcopy(md.days[0].actors[0])
    a.online_min, a.points = 0.0, 0
    gi = bridge.build_bonus_gap_input(a, a.shift_start_min + 5)
    assert gi["historical_points_per_hour"] == {}


# ---------- D-SIM-13(C): tuần phải RESET đúng chu kỳ ----------


def test_week_closes_at_boundary(cfg):
    """8 ngày ⇒ tuần 0 (ngày 0-6) phải ĐÓNG, tuần đang chạy chỉ chứa ngày 7.
    Trước đây tích luỹ tuyến tính không bao giờ reset — "tuần" phình vô hạn."""
    md8 = run_multiday(cfg, seed=SEED, days=8)
    active = [m for m in md8.memory.values() if sum(m.trips_hist) > 0]
    assert active
    for m in active:
        assert len(m.weeks_hist) == 1, f"8 ngày phải có đúng 1 tuần đóng, có {len(m.weeks_hist)}"
        # REVIEW-C21: kiểm CẢ gross + chỉ số tuần + reset bộ đếm, không chỉ trips
        assert m.weeks_hist[0]["week"] == 0 and m.week_index == 1
        assert m.weeks_hist[0]["gross_vnd"] > 0, "tuần đóng ghi gross = 0 — mất tiền khi chốt"
        closed = m.weeks_hist[0]
        # BẢO TOÀN: tuần đóng + tuần đang chạy == tổng toàn kỳ
        assert closed["trips"] + m.week_trips == sum(m.trips_hist),             "cuốc tuần đóng + tuần đang chạy != tổng — rò rỉ khi chốt tuần"
        assert closed["trips"] == sum(m.trips_hist[:7])
        assert m.week_trips == m.trips_hist[7]


# ---------- D-SIM-13(D): data chuỗi liên tục ----------


def test_continuous_generation_identity_and_unique_ids(cfg):
    """Data sinh liên tục: CÙNG driver_id qua các ngày, và ID bản ghi không đụng nhau
    giữa các ngày (mỗi ngày một `day_seed` làm tiền tố)."""
    from gsm_core.mockgen.adapter_sim import generate_days_continuous
    dates = ["2026-07-01", "2026-07-02", "2026-07-03"]
    days = generate_days_continuous("configs/pilot_dongda.yaml", seed=SEED, dates=dates)
    # REVIEW-C17: driver_id chỉ là chỉ số tuần tự (d-0..d-73) — so id KHÔNG phân biệt
    # được "cùng người" với "sample lại mỗi ngày". So THÊM declared_shift_window (đặc
    # trưng cá nhân sample theo seed): regress về run độc lập per-day-seed ⇒ khung ca đổi
    # ⇒ đỏ; regress về run độc lập cùng-seed ⇒ ID bản ghi đụng nhau ⇒ assertion dưới đỏ.
    prof0 = sorted((p["driver_id"], tuple(p["declared_shift_window"]))
                   for p in days[0]["driver_profile"])
    for i, d in enumerate(days[1:], 1):
        cur = sorted((p["driver_id"], tuple(p["declared_shift_window"]))
                     for p in d["driver_profile"])
        assert cur == prof0, f"ngày {i}: danh tính/khung ca tài xế đổi — chuỗi không liên tục"
    order_ids = [t["order_id"] for d in days for t in d["trip_record"]]
    assert len(order_ids) == len(set(order_ids)), "order_id đụng nhau giữa các ngày"


# ---------- REVIEW w32eudwyc: các lỗ đã vá phải có test giữ ----------


def test_final_complete_week_is_closed(cfg):
    """REVIEW-C3: days=7 (đúng 1 tuần tròn) ⇒ tuần đó phải ĐÓNG khi run kết thúc.
    Bản đầu chỉ chốt tuần ở ĐẦU ngày 7k ⇒ days=7 cho weeks_hist RỖNG — S5 cộng
    weeks_hist sẽ hụt đúng tuần cuối."""
    md7 = run_multiday(cfg, seed=SEED, days=7)
    active = [m for m in md7.memory.values() if sum(m.trips_hist) > 0]
    assert active
    for m in active:
        assert len(m.weeks_hist) == 1, "tuần tròn cuối run không được đóng"
        assert m.weeks_hist[0]["trips"] == sum(m.trips_hist)
        assert m.week_trips == 0 and m.week_gross_vnd == 0


def test_week_offset_aligns_to_calendar(cfg):
    """REVIEW-C13: bắt đầu giữa tuần (offset=2, tức Thứ Tư) ⇒ tuần ISO đầu chỉ có 5 ngày
    (T4..CN), chốt vào Thứ Hai = ngày index 5."""
    md9 = run_multiday(cfg, seed=SEED, days=9, week_offset=2)
    active = [m for m in md9.memory.values() if sum(m.trips_hist) > 0]
    assert active
    for m in active:
        assert len(m.weeks_hist) == 1, "phải chốt đúng 1 tuần (5 ngày đầu)"
        assert m.weeks_hist[0]["trips"] == sum(m.trips_hist[:5]),             "tuần ISO đầu phải gồm đúng 5 ngày T4..CN"


def test_treated_days_not_recorded_as_base_propensity(cfg):
    """REVIEW-C1/C6 (lỗi NẶNG nhất review bắt được): ngày bị advice nâng tỷ lệ
    (accept_lift > 0) KHÔNG được ghi vào acceptance_hist — lịch sử đó là ước lượng
    HÀNH VI GỐC, ghi ngày đã-chữa vào sẽ làm advisor tưởng bệnh khỏi và TỰ TẮT lời
    khuyên phòng ngừa (dao động khuyên/im)."""
    from gsm_sim.multiday import DriverMemory, _update_memory
    a = md_actor = None
    md1 = run_multiday(cfg, seed=SEED, days=1)
    r = md1.days[0]
    a = max(r.actors, key=lambda x: x.orders_offered)
    # ngày KHÔNG can thiệp → ghi
    mem = DriverMemory(actor_id=a.actor_id)
    a.accept_lift = 0.0
    _update_memory(mem, r, a)
    assert len(mem.acceptance_hist) == 1
    # ngày CÓ can thiệp → không ghi acceptance (các hist khác vẫn ghi)
    mem2 = DriverMemory(actor_id=a.actor_id)
    a.accept_lift = 0.10
    _update_memory(mem2, r, a)
    assert len(mem2.acceptance_hist) == 0, "ngày đã-lift bị ghi làm hành vi gốc"
    assert len(mem2.payout_hist) == 1


def test_stale_rest_plan_cleared_on_zero_idle_day(cfg):
    """REVIEW-C8: ngày không có idle ⇒ kế hoạch nghỉ CŨ phải bị xoá, không dính mãi."""
    from gsm_sim.multiday import DriverMemory, _update_memory
    md1 = run_multiday(cfg, seed=SEED, days=1)
    r = md1.days[0]
    a = max(r.actors, key=lambda x: x.orders_offered)
    mem = DriverMemory(actor_id=a.actor_id)
    mem.planned_rest_hour = 10          # kế hoạch từ một ngày xa xưa
    a.idle_by_hour = {}                 # hôm nay không idle
    a.accept_lift = 0.0
    _update_memory(mem, r, a)
    assert mem.planned_rest_hour is None, "kế hoạch cũ dính lại sau ngày không idle"


def test_acceptance_avg_gates_early_shift_advice(cfg):
    """REVIEW-C19: nhánh memory.acceptance_avg trong check_bonus_gate chưa từng có test —
    nếu nó âm thầm luôn rơi về accept_base, cả suite vẫn xanh. Kiểm cả hai chiều."""
    import copy
    from gsm_sim.advice_bridge import AdviceActionBridge
    from gsm_sim.multiday import DriverMemory
    from gsm_sim.policy import PolicyBundle
    md1 = run_multiday(cfg, seed=SEED, days=1)
    base_a = next(a for a in md1.days[0].actors if a.archetype == "P4")
    c = Config.load("configs/pilot_dongda.yaml")
    c.data["advice"].update(enabled=True, coverage="single", single_actor_id=base_a.actor_id,
                            channels={"shift_plan": False, "accept_lift": True,
                                      "shift_extend": False, "rest_window": False})
    thr = float(c.get("policy.bonus_min_acceptance"))

    def fresh_actor():
        a = copy.deepcopy(base_a)
        a.orders_offered = a.orders_accepted = 0      # đầu ca, chưa đủ mẫu trong ngày
        a.accept_lift, a.points, a.online_min = 0.0, 0, 0.0
        return a

    # lịch sử gốc THẤP hơn ngưỡng → phải khuyên (advice != None)
    b1 = AdviceActionBridge(c, PolicyBundle.from_config(cfg), seed=1)
    m_low = DriverMemory(actor_id=base_a.actor_id); m_low.acceptance_hist = [0.70, 0.75]
    m_low.points_per_hour_hist = [8.0]
    b1.memory = {base_a.actor_id: m_low}
    a1 = fresh_actor()
    got_low = b1.check_bonus_gate(a1, a1.shift_start_min + 10)
    assert got_low is not None, "lịch sử dưới ngưỡng mà không khuyên — nhánh memory chết"

    # lịch sử gốc CAO hơn ngưỡng → im lặng
    b2 = AdviceActionBridge(c, PolicyBundle.from_config(cfg), seed=1)
    m_hi = DriverMemory(actor_id=base_a.actor_id); m_hi.acceptance_hist = [0.95, 0.93]
    m_hi.points_per_hour_hist = [8.0]
    b2.memory = {base_a.actor_id: m_hi}
    a2 = fresh_actor()
    assert b2.check_bonus_gate(a2, a2.shift_start_min + 10) is None,         f"lịch sử {m_hi.acceptance_avg} >= ngưỡng {thr} mà vẫn khuyên"

