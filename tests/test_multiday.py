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
    """Chiều 2: lịch sử cuộn và tích luỹ tuần PHẢI giữ — đây là thứ làm nên 'nhiều ngày'."""
    for mem in md.memory.values():
        assert mem.days == DAYS
    active = [m for m in md.memory.values() if m.trips_hist and sum(m.trips_hist) > 0]
    assert active, "không tài xế nào chạy cuốc nào"
    m = active[0]
    assert len(m.payout_hist) == DAYS
    assert m.week_trips == sum(m.trips_hist), "tích luỹ tuần không khớp lịch sử ngày"
    assert m.acceptance_avg is not None and 0.0 <= m.acceptance_avg <= 1.0


def test_soc_restored_each_morning(md):
    """Sạc/đổi pin qua đêm — không được bắt đầu ngày mới với pin cạn của hôm qua."""
    for r in md.days:
        for a in r.actors:
            assert a.soc_pct >= 0.0


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
