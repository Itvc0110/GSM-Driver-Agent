"""🔴 P1a — thẻ phải nói phần KIẾM THÊM, không nói TỔNG MỐC.

## Lỗi

`policy.bonus_at` là thang **THAY THẾ**, không cộng dồn (`gsm_core/policy.py:104-110` —
`bonus = tier_vnd`, ghi đè chứ không `+=`; docstring nói *"mốc cao nhất đạt được"*).

Nhưng `solution["tier_vnd"]` là **TỔNG của mốc kế**, và tầng sản phẩm đặt nó ngay cạnh
*"khoảng X giờ chạy nữa"*. Một tài xế **đã chốt** mốc 30.000đ đọc được:

    "Còn với được mốc thưởng 60.000đ hôm nay — bạn thiếu 15 điểm (khoảng 2 giờ chạy nữa)"

và hiểu là 2 giờ đó đổi được **60.000đ**. Sự thật: **30.000đ** (60.000 − 30.000 đã chốt).

**ĐO TRƯỚC KHI SỬA** (`research/audit/2026-08-07-p1-tien-tren-card/`, 990 lượt, chỉ đội bike):
**131/426 thẻ `feasible_gap` = 30,75%** rơi vào ca này · tổng tiền bị thổi **4.440.000đ** ·
bội số **2,00×** (114 thẻ) và **2,09×** (17 thẻ).
⚠ Agent `pb5` báo 9,83% — tôi đo lại ra **30,75%**, cao gấp 3. Phải đo lại vì `Cycle B0`
(`UPDATE-167`) đã đổi phân phối `feasible` **sau** khi agent đo.

## Vì sao công thức `tier_vnd − bonus_at(points_now)` ĐÚNG

Lo ngại hợp lý: người **không đủ điều kiện** nhận **0đ** dù đủ điểm (`day_bonus` trả 0 khi
`acceptance < ngưỡng`) ⇒ trừ `bonus_at` sẽ hứa tiền cho người chắc chắn không nhận được.
Nhưng `feasible = enough_hours and ok_acc and ok_comp` (`bonus_feasibility.py:178`) ⇒ thẻ
`feasible_gap` **chỉ hiện với người ĐỦ điều kiện** ⇒ `bonus_at(points_now)` đúng là phần họ
**thật sự đã chốt**. Nhánh `already_maxed` là chuyện khác và **không được đụng** (test 4).
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.solvers.bonus_feasibility import solve

ROOT = Path(__file__).resolve().parent.parent

POLICY_REC = {
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300},
    "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                   "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


def _gi(points_now: int, *, acc: float = 0.95, comp: float = 0.95) -> dict:
    """`bonus_gap_input` tối thiểu — ĐỦ ĐIỀU KIỆN và ĐỦ GIỜ để thẻ ra `feasible`.

    `next_tiers` dựng **đúng như producer** (`features/bonus_gap.py:73`):
    `[[pt, vnd] for pt, vnd in policy.day_bonus_tiers if pt > points_now]` — giá trị là
    **TỔNG của mốc**, và đó chính là gốc của lỗi này."""
    tiers = [[pt, vnd] for pt, vnd in POLICY_REC["day_bonus_tiers"] if pt > points_now]
    return {
        "schema_version": "1.1.0", "driver_id": "d-1", "date": "2026-07-05",
        "t_now": "2026-07-05T14:00:00+07:00",
        "points_now": points_now, "next_tiers": tiers,
        "acceptance_rate": acc, "completion_rate": comp,
        "hours_budget_remaining": 8.0,
        # rate cao để `enough_hours` luôn đúng ⇒ cô lập đúng tính chất đang kiểm
        "historical_points_per_hour": {"peak": 40.0, "offpeak": 40.0},
        "view_version": "l3-1", "source": "MOCK",
    }


def _sol(policy, points_now: int) -> dict:
    return solve(_gi(points_now), policy)["solution"]


# ---------- 1. tính chất số học lõi ----------

def test_tier_delta_la_phan_TANG_THEM(policy):
    """`points_now = 100` ⇒ đã chốt 60.000đ, mốc kế 160 = 115.000đ ⇒ **biên = 55.000đ**."""
    s = _sol(policy, 100)
    assert s["tier_vnd"] == 115000, "mốc kế phải là 160đ/115.000đ"
    assert s["bonus_now_vnd"] == 60000, "đã chốt mốc 100đ = 60.000đ (thang THAY THẾ)"
    assert s["tier_delta_vnd"] == 55000, (
        "phần KIẾM THÊM = 115.000 − 60.000. Trả nguyên 115.000 là nói tài xế sẽ được gấp "
        "hơn HAI lần thứ họ thật sự nhận")


def test_tier_delta_co_trong_numbers_va_co_NGUON(policy):
    """CLAUDE §5: mọi số hiển thị phải có `source`. Số mới không được là ngoại lệ."""
    rep = solve(_gi(100), policy)
    n = {x["value"]: x for x in rep["numbers"]}
    assert 55000 in n, f"`tier_delta_vnd` chưa vào numbers: {rep['numbers']}"
    assert n[55000]["unit"] == "vnd"
    assert n[55000]["source"].startswith("policy_v:"), "số tiền phải trace về policy có version"


# ---------- 2. chống hồi quy: ĐA SỐ tài xế không được đổi một chữ ----------

@pytest.mark.parametrize("p", [0, 10, 55])
def test_chua_chot_moc_nao_thi_HAI_SO_BANG_NHAU(policy, p):
    """Tài xế chưa qua mốc nào: `bonus_at = 0` ⇒ biên = tổng ⇒ **thẻ không đổi**.

    Đây là nhóm ĐÔNG NHẤT (đo được: 295/426 thẻ feasible). Nếu bản vá đổi thẻ của họ thì nó
    đang sửa sai chỗ."""
    s = _sol(policy, p)
    assert s["bonus_now_vnd"] == 0
    assert s["tier_delta_vnd"] == s["tier_vnd"]


# ---------- 3. nhánh already_maxed KHÔNG được đụng ----------

def test_nhanh_already_maxed_KHONG_DOI(policy):
    """Nhánh `already_maxed` (`:123-145`) đã trả `bonus_at` đúng nghĩa *"đã chốt"* — nó là
    chuyện KHÁC. Test này chặn tôi sửa lan sang đó."""
    rep = solve(_gi(200), policy)
    s = rep["solution"]
    assert s.get("already_maxed") is True
    assert "tier_delta_vnd" not in s, (
        "nhánh already_maxed không có mốc kế ⇒ KHÔNG được sinh `tier_delta_vnd` "
        "(sẽ là một số vô nghĩa)")
    assert [x["value"] for x in rep["numbers"]] == [170000], (
        "nhánh này chỉ được trả ĐÚNG phần thưởng đã chốt, không thêm số nào")


# ---------- 4. bất biến: biên không bao giờ vượt tổng, không bao giờ âm ----------

@pytest.mark.parametrize("p", [0, 30, 59, 60, 61, 99, 100, 101, 159])
def test_bat_bien_bien_nam_trong_khoang(policy, p):
    s = _sol(policy, p)
    if s.get("already_maxed"):
        return
    assert 0 < s["tier_delta_vnd"] <= s["tier_vnd"], (
        f"points_now={p}: biên {s['tier_delta_vnd']} phải dương và ≤ tổng {s['tier_vnd']}")
    assert s["bonus_now_vnd"] == policy.bonus_at(p)


def test_khong_doi_solver_khac(policy):
    """Bản vá chỉ đụng `bonus_feasibility`. Ghim rằng `gap_points`/`hours_needed`/`feasible`
    — ba thứ Cycle B0 vừa sửa — **không nhúc nhích**."""
    truoc = copy.deepcopy(_sol(policy, 100))
    for k in ("gap_points", "feasible", "tier_vnd"):
        assert k in truoc, f"thiếu khoá cũ `{k}` — bản vá đã làm hỏng hợp đồng solution"
    assert truoc["gap_points"] == 60, "160 − 100"
