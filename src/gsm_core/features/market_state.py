"""L3 `MarketStateView` — mở kênh thông tin CUNG cho solver (T-045a).

Nền: `specs/advisor-objective-model-v2.md` §3 · nghiên cứu
`research/audit/2026-07-27-current-state/19-heatmap-marketstate-nghien-cuu-va-thiet-ke.md`.

## Vì sao view này KHÁC một bản đồ nhiệt thường

GSM đã có bản đồ nhiệt + "Nhiệm Vụ Tiếp Theo" (official 15/04/2026) — ta **không** dựng bản đồ
cầu cạnh tranh. Thứ tài liệu của hãng **không nhắc tới**, và cũng là chỗ ta tạo giá trị:

1. **CUNG ĐANG TỚI** (`supply_incoming`) — số tài xế **đã được khuyên** đi ô đó nhưng chưa tới.
   Không trừ nó thì 90 tài xế hỏi cùng lúc sẽ nhận **cùng một câu trả lời** — đúng *fallacy of
   composition* mà hồ sơ `07` đo được (khuyên diện rộng làm served giảm). Ngành cũng làm vậy:
   heatmap tốt tính theo *"phân bố đội xe hiện tại VÀ tương lai"* (Transportation Science).
2. **TRẦN theo ô** (`capacity_left`) — hết trần thì ô **biến mất khỏi danh sách khuyên**. Đây là
   chống dồn cục ngay từ tầng dữ liệu, trước cả khi tới S4.

## Thiếu dữ liệu phải NÓI RA

Mỗi trường mang nhãn `available / degraded / absent`. Thiếu cung ⇒ `sd_ratio = None`,
`positioning_allowed = False` ⇒ solver **bỏ hẳn** lời khuyên vị trí.

Đây là bài học đã trả giá **hai lần**: `supply_cell_hhi` đọc field không tồn tại và trả **0.0 âm
thầm** (UPDATE-075); `soc_pct = None` ⇒ DP **im lặng giả định pin đầy** (UPDATE-079). Cả hai đều
là "hidden fallback" — trông như có dữ liệu trong khi không có.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"


def build_market_state(
    t_now: str,
    bucket_min: int,
    demand_by_cell: dict[str, float],
    supply_now_by_cell: dict[str, int] | None,
    supply_incoming_by_cell: dict[str, int] | None,
    trips_per_driver_per_bucket: float,
    source: str,
) -> dict:
    """Dựng view. Thuần hàm — không đọc file, không random, không phụ thuộc thời gian thực.

    Args:
        demand_by_cell: cầu KỲ VỌNG trong bucket (PROXY — λ config hoặc mật độ lịch sử).
        supply_now_by_cell: số tài xế RỖI đang ở ô. `None` = không có nguồn ⇒ `absent`.
        supply_incoming_by_cell: số tài xế **đang trên đường tới / đã được khuyên tới**.
            `None` = biết cung tĩnh nhưng không biết ai đang tới ⇒ `degraded`.
        trips_per_driver_per_bucket: năng suất phục vụ — dùng để quy cầu ra **số chỗ**.
    """
    if trips_per_driver_per_bucket <= 0:
        raise ValueError("trips_per_driver_per_bucket phải > 0")

    supply_absent = supply_now_by_cell is None
    incoming_absent = supply_incoming_by_cell is None

    availability = {
        "demand": "degraded",            # luôn là PROXY: λ config / lịch sử, không phải cầu thật
        "supply": "absent" if supply_absent else "available",
        "supply_incoming": "absent" if supply_absent
        else ("degraded" if incoming_absent else "available"),
    }
    positioning_allowed = not supply_absent

    cells: dict[str, dict] = {}
    for cell in sorted(demand_by_cell):
        demand = float(demand_by_cell[cell])
        if supply_absent:
            cells[cell] = {
                "expected_demand": round(demand, 3),
                "supply_now": None, "supply_incoming": None, "supply_effective": None,
                "sd_ratio": None, "capacity_left": None,
            }
            continue

        now = int((supply_now_by_cell or {}).get(cell, 0))
        inc = 0 if incoming_absent else int((supply_incoming_by_cell or {}).get(cell, 0))
        eff = now + inc

        # slots = số tài xế mà ô này còn "nuôi" được trong bucket
        slots = int(demand // trips_per_driver_per_bucket)
        capacity_left = max(0, slots - eff)

        # sd_ratio: cầu trên mỗi tài xế hiệu dụng. `eff == 0` ⇒ dùng mẫu số 1 để giữ HỮU HẠN và
        # vẫn xếp hạng được — trả `inf` sẽ làm mọi ô trống thắng tuyệt đối và tạo dồn cục.
        sd = demand / float(eff) if eff > 0 else demand

        cells[cell] = {
            "expected_demand": round(demand, 3),
            "supply_now": now,
            "supply_incoming": None if incoming_absent else inc,
            "supply_effective": eff,
            "sd_ratio": round(sd, 4),
            "capacity_left": capacity_left,
        }

    # Chỉ xếp hạng ô CÒN TRẦN — ô đã đủ người thì không được khuyên thêm (chống dồn cục ngay
    # từ view). Sort: sd_ratio giảm dần, tie-break theo tên ô để deterministic.
    ranked = (
        [] if supply_absent else
        sorted((c for c, v in cells.items() if (v["capacity_left"] or 0) > 0),
               key=lambda c: (-cells[c]["sd_ratio"], c))
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "t_now": t_now,
        "bucket_min": int(bucket_min),
        "cells": cells,
        "ranked_cells": ranked,
        "availability": availability,
        "positioning_allowed": positioning_allowed,
        "source": source,
    }
