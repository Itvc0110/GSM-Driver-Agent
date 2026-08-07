"""Cycle 1 / D-L4-M5 — ĐO Δ: bao nhiêu event `suppressed` là MA?

`_note_suppressed` (đường sản phẩm) trước Cycle 1 được gọi **trước khi biết advisor có gì để
nói**, trong khi `_note_shown` có cổng `if not items`. ⇒ mỗi lần nhịp chặn một tài xế mà advisor
vốn IM LẶNG vẫn ghi một event `suppressed` vào store canonical.

Agent `L4` báo **660/660 = 100%** là ma và **26,7%** driver-phút có `items == []`.
⚠ Tôi KHÔNG trích thẳng số đó — probe này để **tôi tự đo**, vì cùng vòng đó agent đã sai một
con số định lượng khác (`M1`) do đo ở coverage mặc định.

Đại lượng đo:
  · `n_im_lang`  = số (tài xế, phút) mà `advisor.advice()` trả `items == []`
  · `n_ma`       = trong số ĐÓ, bao nhiêu cái trước đây sẽ bị ghi `suppressed`
                   (= mọi lần nhịp KHÔNG cho hiện, vì bản cũ ghi vô điều kiện)

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/m5-do-delta-event-suppressed-ma.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "ui" / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.adapters import advisor  # noqa: E402
from app.adapters import mockdata  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
PHUT = list(range(6 * 60, 22 * 60, 15))          # 06:00→22:00, mỗi 15′
SHIFT_END = 22 * 60


def main() -> None:
    dv = mockdata.default_view()
    ngay = dv["date"]
    cat = mockdata.catalog()
    # CHỈ đội bike (`d-`/`r-`): `advisor.advice` chặn car/premium ngay ở cửa
    # (`advisor.py:227`, lý do `no_active_channel`) — gộp chúng vào sẽ thổi tỷ lệ "im lặng"
    # bằng những ca advisor CỐ Ý không phủ, không phải ca nhịp chặn. Đây đúng cái bẫy đã làm
    # lượt quét đầu của `mm-03` sai ~2x (đếm cả `ce-*`).
    ds = [r["driver_id"] for r in cat["drivers"]
          if str(r["driver_id"]).startswith(("d-", "r-"))]
    ngay_list = cat["dates"][-3:]
    print(f"ngày {ngay} · {len(ds)} tài xế × {len(PHUT)} mốc = {len(ds) * len(PHUT)} driver-phút\n")

    n_tong = n_im = 0
    theo_gio: dict[int, list[int]] = {}
    for ngay in ngay_list:
      for did in ds:
        for m in PHUT:
            try:
                out = advisor.advice(did, ngay, m, SHIFT_END)
            except Exception:
                continue
            n_tong += 1
            im = not (out.get("items") or [])
            n_im += im
            theo_gio.setdefault(m // 60, [0, 0])
            theo_gio[m // 60][0] += 1
            theo_gio[m // 60][1] += im

    if not n_tong:
        print("KHÔNG dựng được ca nào — kiểm lại mockdata")
        return
    ty = n_im / n_tong
    print(f"driver-phút advisor IM LẶNG (`items == []`): {n_im}/{n_tong} = {ty:.1%}")
    print("\ntheo GIỜ (giờ: im/tổng):")
    for h in sorted(theo_gio):
        t, i = theo_gio[h][0], theo_gio[h][1]
        print(f"  {h:02d}h  {i:>4}/{t:<4} = {i / t:>5.1%}")

    print(f"\n⇒ MỌI lần nhịp chặn rơi vào {ty:.1%} driver-phút này trước đây đều ghi một event")
    print("  `suppressed` MA vào store canonical. Sau Cycle 1 chúng KHÔNG còn được ghi.")
    print("  ⚠ Đây là tỷ lệ driver-phút IM LẶNG, KHÔNG phải tỷ lệ event suppressed bị cắt —")
    print("  hai đại lượng khác nhau; muốn số thứ hai phải đếm trên log THẬT có nhịp chặn.")

    OUT.write_text(json.dumps({
        "cau_hoi": "bao nhieu driver-phut advisor VON IM LANG (=> event suppressed la MA)?",
        "ngay": ngay_list, "n_tai_xe": len(ds), "n_moc": len(PHUT),
        "n_driver_phut": n_tong, "n_im_lang": n_im, "ty_le_im_lang": ty,
        "theo_gio": {str(h): {"tong": v[0], "im": v[1]} for h, v in sorted(theo_gio.items())},
        "canh_bao": ("day la ty le driver-phut IM LANG, KHONG phai ty le event suppressed bi cat"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
