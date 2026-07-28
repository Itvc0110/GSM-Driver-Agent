"""Trần trạm của S4 phải scale theo ĐỘ DÀI BUCKET thật (b0-C).

## Vì sao có file này

`derive_allocation_input` tính `capacity = throughput_nominal_per_hour × (BUCKET_MIN/60)` với
`BUCKET_MIN = 30` **hằng số module**. Ai gọi nó với nhịp khác 30′ sẽ nhận trần sai mà **không có
tín hiệu nào**.

Phát hiện khi đang lập kế hoạch T-045a b3: batch tick của `_standby_planner` chạy mỗi
`advice.bucket_min = 60′`. Gọi thẳng hàm này thì **trần chỉ còn một nửa** ⇒ S4 từ chối lời khuyên
một cách vô cớ ⇒ tôi sẽ đọc số `unassigned` cao thành *"chống dồn cục hiệu quả"*, trong khi thực
tế chỉ là đơn vị thời gian bị lệch.

Đây đúng mẫu lỗi **T-046** *"sửa một tầng, tầng khác không biết"* — lần này bắt được **trước** khi
viết consumer, nhờ đọc kỹ producer thay vì tin chữ ký hàm.
"""

from __future__ import annotations

import pytest

from gsm_core.features.allocation import derive_allocation_input

T_NOW = "2026-07-01T09:00:00+07:00"
STATIONS = [{"station_id": "st-1", "throughput_nominal_per_hour": 6.0},
            {"station_id": "st-2", "throughput_nominal_per_hour": 12.0}]
ZONES = [{"zone": "z-1", "capacity": 4}]


def _cap(ai, station_id):
    return next(e["capacity"] for e in ai["station_capacity"] if e["station_id"] == station_id)


def test_default_bucket_unchanged():
    """Không truyền gì ⇒ giữ nguyên hành vi cũ (30′). Bản sửa không được đổi kết quả sẵn có."""
    ai = derive_allocation_input(T_NOW, [], STATIONS, ZONES)
    assert _cap(ai, "st-1") == 3       # 6/giờ × 0,5h
    assert _cap(ai, "st-2") == 6       # 12/giờ × 0,5h


def test_capacity_scales_with_explicit_bucket_min():
    """Bucket 60′ phải cho trần **gấp đôi** bucket 30′ — cùng trạm, cùng throughput.

    Nếu tham số bị bỏ qua (hằng số module thắng) thì hai vế bằng nhau và test ĐỎ.
    """
    c30 = _cap(derive_allocation_input(T_NOW, [], STATIONS, ZONES, bucket_min=30), "st-1")
    c60 = _cap(derive_allocation_input(T_NOW, [], STATIONS, ZONES, bucket_min=60), "st-1")
    assert c60 == 2 * c30, (
        f"bucket 60′ cho trần {c60}, bucket 30′ cho {c30} — trần KHÔNG theo độ dài bucket, "
        f"nên caller chạy nhịp 60′ sẽ bị cắt mất một nửa sức chứa mà không có cảnh báo")


def test_bucket_min_must_be_positive():
    """Bucket ≤ 0 là vô nghĩa — phải nổ ngay, không âm thầm trả trần 0 (tương đương 'cấm hết')."""
    with pytest.raises(ValueError):
        derive_allocation_input(T_NOW, [], STATIONS, ZONES, bucket_min=0)


def test_zone_capacity_is_not_time_scaled():
    """Trần ZONE là *số tài xế đứng cùng lúc*, không phải thông lượng ⇒ **không** nhân theo giờ.

    Trạm pin và khu vực chờ là hai loại ràng buộc khác nhau; gộp chung một phép scale là sai đơn
    vị. Ghi thành test để không ai "tiện tay" nhân cả hai.
    """
    z30 = derive_allocation_input(T_NOW, [], STATIONS, ZONES, bucket_min=30)["zone_supply"][0]
    z60 = derive_allocation_input(T_NOW, [], STATIONS, ZONES, bucket_min=60)["zone_supply"][0]
    assert z30["capacity"] == z60["capacity"] == 4
