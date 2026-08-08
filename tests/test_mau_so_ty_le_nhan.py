"""Cycle 1 — mẫu số tỷ lệ nhận phải là tập tài xế THẬT SỰ QUYẾT ĐỊNH.

## Lỗi được ghim

`world.py:647` tăng `orders_offered` **TRƯỚC** cổng pin ở `:654-664`. Pin không đủ ⇒
`orders_soc_skipped += 1` rồi `continue` — **`decide_accept` KHÔNG BAO GIỜ được gọi**. Lượt đó
vẫn nằm trong mẫu số của `acceptance_rate`, tức tính vào tài xế một lượt **họ chưa từng được hỏi**.

Hậu quả **không phải chỉ là báo cáo**: `world.py:552`/`:1092` đưa `acceptance_rate` thẳng vào
`policy.day_bonus`, mà hàm này trả **0** khi `acceptance < bonus_min_acceptance` **bất kể điểm**.
Đo được (advisor TẮT, 900 driver-day): **46 = 5,11%** bị đẩy xuống dưới ngưỡng CHỈ vì skip-pin,
**33** trong số đó thực sự mất tiền, tổng **108.000đ/ngày** trên đội 90.

Đo cũng cho thấy đây là nguyên nhân của khoảng lệch `realized vs accept_base` ở **7/7 archetype**
(trung bình −0,0241 → **−0,0061** khi bỏ skip-pin khỏi mẫu số; riêng P7 −0,0416 → −0,0083).

Artifact: `research/audit/2026-08-08-do-thuc-cua-sim/Q07-KET-QUA-tien-de-sup.md`.

⚠ Đây **không** phải "sửa cho test xanh": tôi đã chạy falsifier trước và nó bác giả thuyết
"prior của P7 sai" — xem docstring của `q07-accept-base-p7-co-sai-khong.py`.
"""

from __future__ import annotations

import pytest

from gsm_sim.entities import Actor, FleetType


def _actor(**kw) -> Actor:
    """Actor tối thiểu; chỉ các trường đếm là quan trọng cho nhóm test này."""
    a = Actor(actor_id=1, archetype="P2", fleet=FleetType.SWAP, home_cell="x",
              accept_base=0.95, demand_prior_sigma=0.3, fatigue_threshold_min=600.0,
              shift_start_min=420.0, shift_end_min=1020.0, meal_hour=12)
    for k, v in kw.items():
        setattr(a, k, v)
    return a


def test_mau_so_loai_luot_bi_chan_vi_pin():
    """Lượt bị chặn vì pin KHÔNG phải quyết định của tài xế ⇒ không được vào mẫu số.

    20 lượt được định tuyến tới, 4 lượt bị chặn vì pin ⇒ tài xế chỉ **được hỏi 16 lần**,
    nhận 15 ⇒ 15/16, KHÔNG phải 15/20.
    """
    a = _actor(orders_offered=20, orders_soc_skipped=4, orders_accepted=15)
    assert a.acceptance_rate == pytest.approx(15 / 16)
    assert a.acceptance_rate != pytest.approx(15 / 20)


def test_orders_decided_la_khai_niem_TUONG_MINH():
    """Đặt TÊN cho đại lượng thay vì rải `offered - skipped` khắp nơi.

    Ba consumer khác nhau (property, `journey`, `mockgen`) phải dùng **cùng một** định nghĩa;
    nếu mỗi chỗ tự trừ tay thì sẽ lệch nhau đúng như `orders_offered` đã lệch khỏi ý nghĩa của nó.
    """
    a = _actor(orders_offered=20, orders_soc_skipped=4)
    assert a.orders_decided == 16


def test_khong_co_skip_thi_KHONG_DOI_MOT_CHU():
    """Chống hồi quy cho ĐA SỐ tài xế: không có skip-pin ⇒ y hệt trước bản vá.

    Đo được `% skip pin` chỉ 0,3–3,6% tuỳ archetype ⇒ phần lớn driver-day KHÔNG được phép đổi.
    """
    a = _actor(orders_offered=20, orders_soc_skipped=0, orders_accepted=15)
    assert a.acceptance_rate == pytest.approx(15 / 20)
    assert a.orders_decided == 20


def test_moi_luot_deu_bi_skip_khong_no_chia_0():
    """`decided == 0` ⇒ 1.0, giữ ĐÚNG quy ước 0/0 sẵn có — không được ném exception.

    ⚠ Đo được **0/450** driver-day rơi vào ca này, nhưng không được dựa vào may mắn: một seed
    khác hoặc một config pin khắc nghiệt hơn là đủ để nó xảy ra, và lúc đó sim sẽ CRASH.

    Quy ước 1.0 cho 0/0 là **cố ý giữ nguyên** (`BUG-DSIM13-02`): consumer nào cần phân biệt
    "chưa biết" với "hoàn hảo" thì phải đi qua `_acc_estimate`, không đọc thẳng property này.
    """
    a = _actor(orders_offered=6, orders_soc_skipped=6, orders_accepted=0)
    assert a.acceptance_rate == 1.0
    assert a.orders_decided == 0


def test_chua_duoc_chao_lan_nao_van_giu_quy_uoc_cu():
    """0 offer ⇒ 1.0 như trước bản vá (không được đổi ngữ nghĩa nhân tiện)."""
    a = _actor(orders_offered=0, orders_soc_skipped=0, orders_accepted=0)
    assert a.acceptance_rate == 1.0


def test_thuong_khong_con_bi_tuoc_vi_pin():
    """⭐ Test DUY NHẤT chạm tới TIỀN — ba cái trên có thể xanh mà tài xế vẫn mất thưởng.

    Dựng đúng hình dạng đã đo: tài xế **đủ điểm**, tỷ lệ nhận NHIỄM rơi dưới ngưỡng 0,85 trong
    khi tỷ lệ SẠCH ở trên. Trước bản vá `day_bonus` trả 0; sau bản vá phải trả > 0.
    """
    from gsm_sim.policy import PolicyBundle

    pol = PolicyBundle(
        base_fare_vnd=12000, base_km=2.0, per_km_vnd=4000, driver_share=0.75,
        point_peak=15, point_normal=10,
        point_window_hours=frozenset(range(6, 23)), point_peak_hours=frozenset([7, 8, 17, 18]),
        day_bonus_tiers=((100, 30000), (160, 60000)),
        bonus_min_acceptance=0.85, bonus_min_completion=0.90, version="test-v0",
    )
    # 19 lượt định tuyến tới, 3 bị chặn vì pin ⇒ được hỏi 16, nhận 15.
    #   nhiễm = 15/19 = 0,7895  < 0,85  ⇒ thưởng bị TƯỚC
    #   sạch  = 15/16 = 0,9375  ≥ 0,85  ⇒ đủ điều kiện
    a = _actor(orders_offered=19, orders_soc_skipped=3, orders_accepted=15,
               orders_completed=15, points=170)
    assert a.acceptance_rate >= pol.bonus_min_acceptance, (
        "tỷ lệ nhận SẠCH phải qua ngưỡng — nếu đỏ ở đây thì bản vá mẫu số chưa vào")
    assert pol.day_bonus(a.points, a.acceptance_rate, a.completion_rate) > 0, (
        "tài xế đủ điểm và thật sự nhận 15/16 lượt được hỏi — không được mất thưởng vì "
        "3 lượt hệ thống bỏ qua do pin")
