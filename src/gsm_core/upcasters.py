"""Upcaster — nâng record phiên bản CŨ lên hình dạng LATEST, từng bậc, pure function.

Cycle V (2026-07-28, gỡ B-02): consumer cần hình dạng mới (vd ĐA-05 replay event store qua
migration) gọi `upcast(entity, record)`; validate thuần tuý thì KHÔNG cần upcast —
`SchemaRegistry.validate` đã route theo version của record.

Quy tắc viết upcaster (T-044 sẽ dựa vào đây cho envelope v2):

1. **Pure**: không mutate input, trả dict MỚI. Có test canh.
2. **Từng bậc**: `(entity, from_version) -> record ở version KẾ TIẾP`; chuỗi dài do `upcast`
   tự nối — không viết upcaster nhảy cóc (n² hàm khi nhiều version).
3. Additive-optional ⇒ upcaster chỉ stamp version (trường optional vắng mặt vẫn hợp lệ ở
   latest). Đổi NGỮ NGHĨA/xoá trường ⇒ upcaster phải dịch dữ liệu thật và đó là dấu hiệu nên
   cân nhắc MAJOR bump thay vì minor.
"""

from __future__ import annotations

from typing import Callable

# (entity, from_version) -> hàm nâng lên version KẾ TIẾP trong registry.versions(entity)
UPCASTERS: dict[tuple[str, str], Callable[[dict], dict]] = {}


def _register(entity: str, from_version: str):
    def deco(fn):
        UPCASTERS[(entity, from_version)] = fn
        return fn
    return deco


@_register("shift_plan_input", "1.0.0")
def _spi_100_to_110(record: dict) -> dict:
    """1.0.0 → 1.1.0 (Cycle R thêm `rest_taken_min`/`shift_elapsed_min`, additive-optional).

    Record 1.0.0 không biết nghỉ-đã-nghỉ ⇒ KHÔNG bịa giá trị (đặt 0.0 là khẳng định "chưa nghỉ
    phút nào" — sai sự thật). Vắng mặt = `_required_rest` dùng công thức mù-state cũ, đúng
    hành vi record đó từng có. Chỉ stamp version."""
    return {**record, "schema_version": "1.1.0"}


from functools import lru_cache


@lru_cache(maxsize=1)
def _registry():
    """Registry dùng chung cho mọi lời gọi upcast — bản đầu tạo instance MỚI mỗi lần gọi,
    tức lru_cache per-instance của registry vô dụng và mỗi upcast đọc lại file từ đĩa."""
    from pathlib import Path

    from .schema_registry import SchemaRegistry
    return SchemaRegistry(Path(__file__).resolve().parents[2] / "schemas")


def upcast(entity: str, record: dict) -> dict:
    """Nâng `record` lên hình dạng LATEST của entity, nối chuỗi từng bậc.

    Record đã ở latest ⇒ trả về chính nó (identity). Kẹt giữa chừng (thiếu upcaster cho một
    bậc) ⇒ ValueError tường minh — không trả nửa vời.

    ## Lan can chống TREO (review đối kháng Cycle V reproduce: 10.001 vòng)

    Upcaster quên stamp version (lỗi kinh điển của mỗi lần bump tương lai) làm vòng while cũ
    lặp VÔ HẠN — treo còn tệ hơn lỗi mù vì không có traceback nào để lần. Nay mỗi bậc phải
    TIẾN THẬT: version output phải nằm trong danh sách đã biết và LỚN HƠN version input;
    số bậc bị chặn bởi len(known)."""
    reg = _registry()
    known = reg.versions(entity)
    order = {v: i for i, v in enumerate(known)}
    cur = record.get("schema_version")
    if cur not in order:
        raise ValueError(f"{entity}: version '{cur}' không nằm trong {list(known)}")
    if cur == known[-1]:
        return record
    out = record
    for _ in range(len(known)):
        if out["schema_version"] == known[-1]:
            return out
        frm = out["schema_version"]
        step = UPCASTERS.get((entity, frm))
        if step is None:
            raise ValueError(
                f"{entity}: thiếu upcaster từ {frm} — chuỗi đứt, không trả kết quả nửa vời")
        out = step(out)
        nxt = out.get("schema_version")
        if nxt not in order or order[nxt] <= order[frm]:
            raise ValueError(
                f"{entity}: upcaster từ {frm} trả version '{nxt}' không TIẾN "
                f"(đã biết: {list(known)}) — quên stamp version? Fail-loud thay vì treo.")
    return out
