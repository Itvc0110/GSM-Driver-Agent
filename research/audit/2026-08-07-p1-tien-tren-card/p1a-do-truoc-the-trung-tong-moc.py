"""P1a — ĐO TRƯỚC KHI SỬA: bao nhiêu thẻ trưng TỔNG mốc thay vì phần KIẾM THÊM?

## Vì sao phải đo lại (đây là rủi ro tôi tự ghi vào plan)

Agent `pb5` báo **111/1.129 thẻ (9,83%)**. Nhưng `points_now` đi qua `bonus_gap_input`, mà
**Cycle B0 (`UPDATE-167`) vừa sửa mẫu số bucket của S1** ⇒ phân phối `feasible` đã đổi **SAU** khi
agent đo. So "111 → 0" mà không đo lại là so **hai đại lượng khác nhau** — đúng cơ chế đã làm
`+6.016đ` không tái tạo được.

## Cơ chế được đo

`policy.bonus_at` là thang **THAY THẾ** (`bonus = tier_vnd`, không cộng dồn — `policy.py:104-110`).
Thẻ `feasible_gap` trưng `sol["tier_vnd"]` = **TỔNG của mốc** ngay cạnh *"khoảng X giờ chạy nữa"*.
Phần **thật sự** đổi được bằng công sức thêm = `tier_vnd − bonus_at(points_now)`.

Thẻ chỉ hiện với người **đủ điều kiện** (`feasible = enough_hours and ok_acc and ok_comp`,
`bonus_feasibility.py:178`) ⇒ `bonus_at(points_now)` đúng là phần họ **thật sự đã chốt**.

⚠ **CHỈ quét đội bike** (`d-`/`r-`): `advisor.py:227` chặn car/premium ngay ở cửa. Đếm cả `ce-*`
là bẫy đã làm lượt quét đầu của `mm-03` sai ~2× và làm tôi báo sai 26,7% hôm nay.

Chạy:  uv run python research/audit/2026-08-07-p1-tien-tren-card/p1a-do-truoc-the-trung-tong-moc.py
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "ui" / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.adapters import advisor, mockdata  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
GIO = [14 * 60, 17 * 60, 20 * 60]          # ba mốc hỏi trong ca
SHIFT_END = 22 * 60


def main() -> None:
    cat = mockdata.catalog()
    ds = [r["driver_id"] for r in cat["drivers"]
          if str(r["driver_id"]).startswith(("d-", "r-"))]
    ngay_list = cat["dates"][-3:]
    pol = advisor.policy()
    print(f"{len(ngay_list)} ngày × {len(ds)} tài xế BIKE × {len(GIO)} mốc = "
          f"{len(ngay_list) * len(ds) * len(GIO)} lượt\n")

    n_luot = n_feasible = n_sai = 0
    tong_thoi = 0
    boi_so: collections.Counter = collections.Counter()
    vi_du: list[dict] = []
    for ngay in ngay_list:
        for did in ds:
            for m in GIO:
                try:
                    out = advisor.advice(did, ngay, m, SHIFT_END)
                except Exception:
                    continue
                n_luot += 1
                for it in (out.get("items") or []):
                    if it.get("reason_code") != "feasible_gap":
                        continue
                    n_feasible += 1
                    nums = {n["name"]: n["value"] for n in (it.get("numbers") or [])}
                    tier = nums.get("thuong_moc_ke")
                    if tier is None:
                        continue
                    # điểm hiện tại phải lấy từ input của solver, không có trên thẻ
                    gi = advisor.build_gi(did, ngay, m, SHIFT_END)
                    p_now = int(gi["points_now"])
                    da_chot = int(pol.bonus_at(p_now))
                    bien = int(tier) - da_chot
                    # SAU bản vá: thẻ chỉ "sai" khi TEXT không nêu phần tăng thêm.
                    txt = f"{it.get('title','')} {it.get('message','')}"
                    from app.adapters.advisor import _vn as _vnf
                    da_neu_bien = (bien != int(tier)) and (_vnf(bien, "vnd") in txt)
                    if da_chot > 0 and not da_neu_bien:
                        n_sai += 1
                        tong_thoi += int(tier) - bien
                        boi_so[round(int(tier) / bien, 2) if bien else float("inf")] += 1
                        if len(vi_du) < 5:
                            vi_du.append({"driver": did, "date": ngay, "now_min": m,
                                          "points_now": p_now, "da_chot": da_chot,
                                          "the_trung": int(tier), "bien_that": bien,
                                          "title": it.get("title", "")[:90]})

    print(f"lượt gọi advice          : {n_luot}")
    print(f"thẻ `feasible_gap`       : {n_feasible}")
    print(f"⭐ thẻ TRƯNG TỔNG MỐC     : {n_sai}"
          + (f" = {n_sai / n_feasible:.2%} thẻ feasible" if n_feasible else ""))
    print(f"   tổng tiền bị THỔI     : {tong_thoi:,}đ")
    if boi_so:
        print("   bội số (thẻ trưng / biên thật):")
        for k, v in sorted(boi_so.items()):
            print(f"     {k}× → {v} thẻ")
    print("\nví dụ:")
    for v in vi_du:
        print(f"  {v['driver']} {v['date']} {v['now_min']}′ · điểm {v['points_now']} · "
              f"đã chốt {v['da_chot']:,}đ · thẻ trưng {v['the_trung']:,}đ · "
              f"BIÊN THẬT {v['bien_that']:,}đ")
        print(f"     \"{v['title']}\"")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "cau_hoi": "bao nhieu the feasible_gap trung TONG moc thay vi phan KIEM THEM?",
        "ngay": ngay_list, "n_tai_xe_bike": len(ds), "moc_gio": GIO,
        "n_luot": n_luot, "n_feasible": n_feasible, "n_sai": n_sai,
        "ty_le_sai": (n_sai / n_feasible) if n_feasible else None,
        "tong_tien_thoi_vnd": tong_thoi,
        "boi_so": {str(k): v for k, v in boi_so.items()},
        "vi_du": vi_du,
        "canh_bao": ("CHI doi bike (d-/r-); dem ca ce-* la bay da lam mm-03 sai ~2x. "
                     "Do LAI sau Cycle B0 vi B0 doi phan phoi feasible."),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
