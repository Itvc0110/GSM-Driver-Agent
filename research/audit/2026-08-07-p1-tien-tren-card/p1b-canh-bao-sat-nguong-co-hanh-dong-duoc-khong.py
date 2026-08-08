"""P1b — ĐO TRƯỚC KHI QUYẾT SHIP: cảnh báo "sát ngưỡng" có HÀNH ĐỘNG ĐƯỢC không?

## Câu hỏi trong plan của tôi SAI đại lượng — sửa lại ở đây

Plan ghi: *"đo bao nhiêu lượt còn đủ quỹ giờ để KÉO tỷ lệ LÊN trên ngưỡng"*. Đọc code thì
cliff bắn khi **`0,85 ≤ acceptance < 0,88`** (`bonus_feasibility.py:236`, `CLIFF_MARGIN=0.03`) —
tức tài xế **ĐANG TRÊN ngưỡng**. Cảnh báo là **PHÒNG NGỪA** (*"vài lần từ chối nữa có thể mất
TOÀN BỘ thưởng dù đủ điểm"*), không phải lời gọi sửa tỷ lệ.

⇒ Đại lượng đúng: **còn MẤY LẦN TỪ CHỐI nữa thì rơi xuống dưới ngưỡng?**

    a = accepted_count, o = total_request_calculate_accept (số lượt CHÀO)
    sau k lần từ chối:  a / (o + k) < 0,85   ⇒   k > a/0,85 − o

`k = 1` ⇒ cảnh báo **cực kỳ đáng nói**. `k ≥ 20` ⇒ nhiễu.

## Phán quyết ship

- Đa số ca có **k nhỏ** (1–3) ⇒ **SHIP**: đây là cảnh báo cứu được toàn bộ thưởng ngày.
- Đa số ca **k lớn** hoặc **hết ca** ⇒ **ĐỪNG SHIP** — im lặng đúng hơn một cảnh báo không
  hành động được (fallback đã ghi trong plan).

⚠ CHỈ đội bike (`d-`/`r-`) — `advisor.py:227` chặn car/premium ở cửa.
⚠ `accepted_count`/`total_request_*` là số **CẢ NGÀY** (end-of-day), còn `gi["acceptance_rate"]`
là as-of. Dùng số ngày để ước `k` là **xấp xỉ trên** — ghi nhãn, không giấu.

Chạy: uv run python research/audit/2026-08-07-p1-tien-tren-card/p1b-canh-bao-sat-nguong-co-hanh-dong-duoc-khong.py
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "ui" / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.adapters import advisor, mockdata  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
GIO = [14 * 60, 17 * 60, 20 * 60]
SHIFT_END = 22 * 60


def main() -> None:
    cat = mockdata.catalog()
    ds = [r["driver_id"] for r in cat["drivers"]
          if str(r["driver_id"]).startswith(("d-", "r-"))]
    ngay_list = cat["dates"][-3:]
    pol = advisor.policy()
    nguong = float(pol.bonus_min_acceptance)
    margin = 0.03

    n_luot = n_cliff_sinh = n_cliff_toi_tay = 0
    k_dist: collections.Counter = collections.Counter()
    gio_con: list[float] = []
    vi_du: list[dict] = []
    for ngay in ngay_list:
        for did in ds:
            row = mockdata._stat_row(did, ngay) or {}
            a = row.get("accepted_count")
            o = row.get("total_request_calculate_accept")
            for m in GIO:
                try:
                    out = advisor.advice(did, ngay, m, SHIFT_END)
                    gi = advisor.build_gi(did, ngay, m, SHIFT_END)
                except Exception:
                    continue
                n_luot += 1
                acc = float(gi["acceptance_rate"])
                if not (nguong <= acc < nguong + margin):
                    continue
                n_cliff_sinh += 1
                # cảnh báo có tới tay tài xế không?
                if any("sát ngưỡng" in (it.get("title", "") + it.get("message", "")
                                        + str(it.get("caveat", "")))
                       for it in (out.get("items") or [])):
                    n_cliff_toi_tay += 1
                if a and o:
                    k = max(1, math.ceil(a / nguong - o + 1e-9))
                    k_dist[min(k, 10)] += 1
                    if len(vi_du) < 6:
                        vi_du.append({"driver": did, "date": ngay, "now_min": m,
                                      "acc": round(acc, 4), "a": a, "o": o, "k_tu_choi": k})
                gio_con.append(float(gi.get("hours_budget_remaining") or 0.0))

    print(f"lượt gọi advice                     : {n_luot}")
    print(f"lượt Ở TRONG DẢI sát ngưỡng         : {n_cliff_sinh}"
          + (f" = {n_cliff_sinh / n_luot:.2%}" if n_luot else ""))
    print(f"lượt cảnh báo TỚI TAY tài xế        : {n_cliff_toi_tay}")
    if gio_con:
        gio_con.sort()
        print(f"quỹ giờ còn lại lúc cảnh báo (giờ)  : "
              f"p25 {gio_con[len(gio_con)//4]:.1f} · trung vị "
              f"{gio_con[len(gio_con)//2]:.1f} · p75 {gio_con[3*len(gio_con)//4]:.1f}")
    if k_dist:
        tong = sum(k_dist.values())
        print(f"\n⭐ CÒN MẤY LẦN TỪ CHỐI NỮA THÌ RƠI (n={tong}):")
        for k in sorted(k_dist):
            nhan = f"{k}" if k < 10 else "≥10"
            print(f"     {nhan:>3} lần → {k_dist[k]:>4} lượt = {k_dist[k]/tong:>5.1%}")
        nho = sum(v for k, v in k_dist.items() if k <= 3)
        print(f"\n  ⇒ {nho}/{tong} = {nho/tong:.1%} số ca chỉ cần **≤3 lần từ chối** là mất "
              f"TOÀN BỘ thưởng ngày")
    print("\nví dụ:")
    for v in vi_du:
        print(f"  {v['driver']} {v['date']} {v['now_min']}′ · nhận {v['a']}/{v['o']} = "
              f"{v['acc']:.3f} ⇒ **{v['k_tu_choi']} lần từ chối** là rơi dưới {nguong}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "cau_hoi": "canh bao sat nguong co HANH DONG DUOC khong? (con may lan tu choi thi roi)",
        "nguong": nguong, "cliff_margin": margin,
        "ngay": ngay_list, "n_tai_xe_bike": len(ds), "moc_gio": GIO,
        "n_luot": n_luot, "n_trong_dai": n_cliff_sinh, "n_toi_tay": n_cliff_toi_tay,
        "k_phan_bo": {str(k): v for k, v in sorted(k_dist.items())},
        "vi_du": vi_du,
        "canh_bao": ("accepted_count/total_request_* la so CA NGAY (end-of-day) con "
                     "gi.acceptance_rate la as-of => k la XAP XI TREN. Chi doi bike."),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
