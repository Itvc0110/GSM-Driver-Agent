"""ĐA-01 — MỘT cách ước lượng tỷ lệ cho CẢ sim và UI.

Cường (2026-07-27): *"UI và sim phải chung 1 logic, sử dụng cùng 1 luật, 1 database"*.

## Vì sao cần file này

Trước đây **một khái niệm "tỷ lệ nhận" có ba cách tính khác nhau**:

| Nơi | Cách tính | Sai ở đâu |
|---|---|---|
| `gsm_sim/entities.py` property | `accepted/offered`, **0/0 → 1.0** | "chưa có dữ liệu" bị coi là "hoàn hảo" (BUG-DSIM13-02: chặn nhầm lời khuyên đầu ca) |
| `gsm_sim/journey.py` | `accepted/offered`, **0/0 → None** | đúng hơn, nhưng là quy ước THỨ HAI |
| `ui/backend .../advisor.build_gi` | aggregate **CẢ NGÀY** từ `driver_statistic_daily`, thiếu → **1.0** | **rò tương lai** (9h sáng đã biết tỷ lệ cuối ngày) + lại fallback 1.0 |

Ba quy ước cho một sự thật — đúng thứ đã đẻ ra các lỗi của UPDATE-075/076.

## Estimator

    p̂ = (k + m·p0) / (n + m)

Đây là hậu nghiệm trung bình của Beta-Binomial với prior `Beta(m·p0, m·(1−p0))`; `m` là **số quan
sát giả** (đơn vị: "số lần được chào"), nói *"tin prior bằng khoảng m lần chào"*.

Ba tính chất khiến nó thay được cả ba cách trên:

1. `n = 0` ⇒ `p̂ = p0` — **không bao giờ trả 1.0**. Không có bằng chứng thì trả niềm tin trước,
   không trả "hoàn hảo". Đây là điều ĐA-01 yêu cầu tường minh.
2. `n` nhỏ ⇒ co mạnh về prior — một cuốc bị từ chối không lật được kết luận.
3. `n` lớn ⇒ prior mờ dần, bám dữ liệu thật.

**KHÔNG có mặc định cho `p0` và `m`**: caller phải truyền, vì `p0` là số ĐO ĐƯỢC (pooled từ dữ
liệu, tính trên ngày TRƯỚC để không rò tương lai) chứ không phải hằng số bịa ra.
"""

from __future__ import annotations


def shrunk_rate(k: int | float, n: int | float, p0: float, m: float) -> float:
    """Tỷ lệ co về prior: `(k + m·p0) / (n + m)`.

    Args:
        k: số lần thành công (đã nhận / đã hoàn thành).
        n: số lần thử (được chào / đã nhận). `n = 0` hợp lệ ⇒ trả đúng `p0`.
        p0: prior — phải là xác suất **đo được**, không bịa (xem docstring module).
        m: số quan sát giả, `> 0`. Lớn hơn = tin prior hơn.

    Raises:
        ValueError: dữ liệu bất khả (`k > n`, số âm, `p0` ngoài [0,1], `m ≤ 0`).
            **Nổ chứ không lặng lẽ trả số đẹp** — đầu vào hỏng mà trả ra tỷ lệ trông hợp lý là
            cách nhanh nhất để một con số sai đi thẳng tới tài xế.
    """
    if not (0.0 <= p0 <= 1.0):
        raise ValueError(f"p0 phải là xác suất trong [0,1], nhận {p0!r}")
    if m <= 0:
        raise ValueError(f"m (số quan sát giả) phải > 0, nhận {m!r}")
    if k < 0 or n < 0:
        raise ValueError(f"đếm âm là dữ liệu hỏng: k={k!r}, n={n!r}")
    if k > n:
        raise ValueError(f"k > n là dữ liệu hỏng: k={k!r}, n={n!r}")
    return (float(k) + m * p0) / (float(n) + m)
