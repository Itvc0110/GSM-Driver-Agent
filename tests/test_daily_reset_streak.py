"""D-E10-01 — `idle_streak_min` phải được RESET sang ngày mới.

Vì sao (ghi nợ từ cycle E10, spec e10-advisor-noisy §4.1): `idle_streak_min` là **chuỗi rỗi
LIÊN TỤC** (+2,0 mỗi tick WAIT, reset khi được chào hoặc sau relocate — `world.py`). Nó KHÔNG
nằm trong `_DAILY_RESET_*` ⇒ ngày 2 của một run multiday mở màn với streak tồn dư của cuối
ngày 1: tài xế vừa ngủ dậy bị coi như đã đứng chờ liên tục 40 phút.

Vô hại cho sim MỘT NGÀY (mọi artifact tới nay), nhưng là **bẫy nạp sẵn cho `D-M3-04`** (bật
multiday trong A/B): bản năng sốt ruột (`behavior.py` đọc `idle_streak_min`) và trigger E10b
đều đọc biến này ⇒ sai từ phút đầu ngày 2, và sai theo hướng "sốt ruột hơn thực tế".
"""
from __future__ import annotations

from gsm_sim.entities import Actor, FleetType


def _actor() -> Actor:
    return Actor(actor_id=1, archetype="P1", fleet=FleetType.SWAP, home_cell="A",
                 shift_start_min=300.0, shift_end_min=1400.0, demand_prior_sigma=0.2,
                 accept_base=0.9, fatigue_threshold_min=480.0, meal_hour=12)


def test_idle_streak_reset_sang_ngay_moi():
    """Ngày mới = chuỗi rỗi mới. Không reset ⇒ ngày 2 bắt đầu ở mức 'đã chờ 40 phút'."""
    a = _actor()
    a.idle_streak_min = 42.0
    a.reset_for_new_day(soc_pct=95.0, shift_start_min=300.0, shift_end_min=1400.0)
    assert a.idle_streak_min == 0.0, (
        "streak của hôm qua tràn sang hôm nay — bản năng sốt ruột và trigger E10b sẽ đọc "
        "một tài xế vừa ngủ dậy như thể đã đứng chờ liên tục (D-E10-01)")


def test_reset_khong_dong_toi_danh_tinh_va_bo_nho():
    """Đối chứng: reset đúng phạm vi — xoá trạng thái NGÀY, giữ DANH TÍNH và trí nhớ
    liên-ngày (`planned_rest_hour` là bộ nhớ multiday, KHÔNG được xoá)."""
    a = _actor()
    a.planned_rest_hour = 14
    a.idle_streak_min = 30.0
    a.trips_done = 12
    a.reset_for_new_day(soc_pct=95.0, shift_start_min=300.0, shift_end_min=1400.0)
    assert a.planned_rest_hour == 14, "bộ nhớ liên-ngày bị xoá ⇒ 'học từ hôm qua' thành giả"
    assert a.archetype == "P1" and a.actor_id == 1
    assert a.trips_done == 0 and a.idle_streak_min == 0.0
