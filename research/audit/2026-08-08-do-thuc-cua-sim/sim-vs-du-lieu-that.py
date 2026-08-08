"""ĐỘ THỰC CỦA SIM — và vì sao phép đối chiếu này KHÔNG kiểm chứng được gì.

# ⛔ KẾT QUẢ: PHÉP SO NÀY LÀ VÒNG TRÒN — KHÔNG ĐƯỢC TRÍCH NHƯ BẰNG CHỨNG ĐỘ THỰC

Script chạy xong cho một bảng **đẹp** (mọi chỉ số lệch < 10%, `hoàn thành/được chào` lệch
**0,8%** với tứ phân vị trùng khít). Tôi suýt báo *"sim thực tế trong vòng 10%"*. **Sai.**

`src/gsm_core/mockgen/adapter_sim.py:17-18`:
```python
from gsm_sim.config import Config
from gsm_sim.runner import run_once          # ⇐ CHÍNH engine đang được đem ra "kiểm chứng"
```
`realdata.py:3-5` — *"BIKE simulate qua `adapter_sim.generate_day`… Acceptance theo
**archetype target** + noise"*; `realdata.py:138-141` lấy thẳng `accepted`/`offered` từ
`sim_stats`. ⇒ **Các dòng XE MÁY của `driver_statistic_daily` do chính `gsm_sim` sinh ra**, từ
**cùng bộ `ARCHETYPES`**. Mà xe máy đúng là tập script này lọc vào.

⇒ Bảng dưới so **gsm_sim với gsm_sim**. Mức khớp `−0,8%` không phải bằng chứng — nó gần như là
**đồng nhất thức**. Các dòng ô tô/premium là rule-based (`realdata.py:144-148`,
`prof["target_acceptance"]` + nhiễu Gauss) — cũng là giả định của ta, chỉ khác bộ sinh.

**Hệ quả đúng, phải nói thẳng:** trong repo này **KHÔNG TỒN TẠI neo dữ liệu thật nào**. GSM cấp
**SCHEMA** 13 bảng, không cấp **DỮ LIỆU** (`docs/data-catalog/`, và đúng như đã ghi trong hồ sơ
đối tác). Vậy mọi câu *"sim giống thực tế X%"* dựa trên các bảng này đều **không có căn cứ**, dù
số có đẹp đến đâu.

**Việc đúng phải làm thay:** không đi tìm neo không tồn tại, mà đo **độ bền của kết luận trước
sự bất định về thế giới** — tham số nào chưa neo, và kết luận về advisor có đổi dấu khi tham số
đó sai không. Xem `do-ben-cua-ket-luan.py` cùng thư mục.

Giữ file này lại **làm bằng chứng cho chính lỗi đó**, không xoá.

## Vì sao (ý định ban đầu)

Cường nêu nghi vấn cụ thể: *"trung bình cuốc được nhận, cuốc hoàn thành rất cao; thời gian chờ
để ghép đơn của tài xế thực tế cũng không cao đến mức như trong sim"*. Và mọi kết luận về giá
trị advisor đều **có điều kiện theo độ thực của thế giới** — một advisor tốt trong một thế giới
sai là một kết luận sai.

## Đối chiếu cái gì

| nguồn THẬT | nguồn SIM |
| --- | --- |
| `driver_statistic_daily` ⋈ `driver_online_hours_sap_id` | arm **A** của `pb1b-raw.json.gz` |
| join `(driver_id, local_date)`, **12.805 driver-day** | 30 seed × 90 actor = **2.700 driver-day** |

⚠ Dùng arm **A** (advisor TẮT) làm đại diện cho sim — so arm B với thực tế là so một thế giới
**đã bị can thiệp** với thực tế.

## Hai bẫy đã tránh (cả hai đều từng làm tôi báo số sai)

1. **Ghép hai bảng chưa join.** Bản nháp của script này `zip()` số cuốc của bảng này với giờ
   online của bảng kia ⇒ ghép giờ của tài xế A với cuốc của tài xế B. Nay **join thật** trên
   `(driver_id, local_date)`.
2. **Mẫu số nhiễm loại xe.** Sim `pilot_dongda` là **xe máy**; bảng thật có `car` 2.345 +
   `car-premium` 792 driver-day. So sim-bike với đội-toàn-loại là đúng cơ chế đã làm `mm-03`
   sai ~2× và làm tôi báo sai *"26,7% im lặng"*. Nay **lọc `driver_type` bắt đầu bằng `bike`**,
   và in cả hai cột để thấy lọc có đổi kết luận không.

⚠ Số là **MOCK sinh từ schema thật** (`CLAUDE.md §5`) — đây là đối chiếu *sim ↔ mock-từ-schema*,
**không phải** *sim ↔ số GSM thật*. Nhãn này không được bỏ khi trích.

## Chỉ số then chốt

`cuốc / giờ online` — **độc lập độ dài ca**, nên so được dù phân phối ca khác nhau. Lệch ở đây
nghĩa là **năng suất** của sim sai, không chỉ là khác giờ làm.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/sim-vs-du-lieu-that.py
"""
from __future__ import annotations

import gzip
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "ui" / "backend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import polars as pl  # noqa: E402

from app.adapters import mockdata  # noqa: E402

RAW = ROOT / "research/audit/2026-08-07-phan-bien-sim-advisor/pb1b-raw.json.gz"
OUT = pathlib.Path(__file__).with_suffix(".json")
MIN_ONLINE_H = 0.5   # bỏ ca cụt: chia cho giờ ~0 làm tỷ số nổ


def _pv(xs) -> dict:
    xs = sorted(float(x) for x in xs if x is not None)
    if not xs:
        return {}
    n = len(xs)
    return {"n": n, "p10": xs[n // 10], "p25": xs[n // 4], "median": xs[n // 2],
            "p75": xs[3 * n // 4], "p90": xs[9 * n // 10], "mean": statistics.mean(xs)}


def _row(ten: str, that: dict, sim: dict, dv: str = "") -> dict:
    if not that or not sim:
        print(f"{ten:<24} (thiếu một bên)")
        return {}
    lech = (sim["median"] - that["median"]) / that["median"] if that["median"] else float("nan")
    print(f"{ten:<24}{that['median']:>8.2f}{dv} [{that['p25']:>5.2f}–{that['p75']:>5.2f}]"
          f"{sim['median']:>10.2f}{dv} [{sim['p25']:>5.2f}–{sim['p75']:>5.2f}]{lech:>+10.1%}")
    return {"that": that, "sim": sim, "lech_median": lech}


def main() -> None:
    # ---------------- THẬT: join hai bảng trên (driver_id, local_date) ----------------
    st = mockdata._table("driver_statistic_daily")
    oh = mockdata._table("driver_online_hours_sap_id")
    j = st.join(oh.select("driver_id", "local_date", "online_time", "driver_type"),
                on=["driver_id", "local_date"], how="inner")
    print(f"join: {st.height} × {oh.height} → {j.height} driver-day khớp")

    bike = j.filter(pl.col("driver_type").str.starts_with("bike"))
    print(f"lọc loại xe: {j.height} → {bike.height} driver-day XE MÁY "
          f"(bỏ {j.height - bike.height} ca ô tô/premium)\n")

    b = bike.filter(pl.col("online_time") >= MIN_ONLINE_H)
    that_trips = b["completed_count"].to_list()
    that_oh = b["online_time"].to_list()
    that_offer = b["total_request_calculate_accept"].to_list()
    that_tph = [t / h for t, h in zip(that_trips, that_oh)]          # ⭐ đã JOIN, cùng hàng

    # ---------------- SIM: arm A (advisor TẮT) ----------------
    data = json.load(gzip.open(RAW, "rt", encoding="utf-8"))
    sim_trips, sim_oh, sim_offer, sim_tph, sim_idle_share = [], [], [], [], []
    for row in data:
        for a in row["A"].values():
            h = float(a["online"]) / 60.0
            sim_trips.append(float(a["trips"]))
            sim_oh.append(h)
            sim_offer.append(float(a["offered"]))
            if h >= MIN_ONLINE_H:
                sim_tph.append(float(a["trips"]) / h)
                sim_idle_share.append(float(a["idle"]) / float(a["online"]))

    print(f"{'chỉ số':<24}{'THẬT xe máy (med [p25–p75])':>26}"
          f"{'SIM arm A':>26}{'lệch':>10}")
    print("-" * 88)
    out: dict = {
        "nguon_that": f"driver_statistic_daily ⋈ driver_online_hours_sap_id, "
                      f"LỌC xe máy, online≥{MIN_ONLINE_H}h ⇒ n={len(that_trips)} (MOCK từ schema GSM)",
        "nguon_sim": f"pb1b-raw arm A (advisor TẮT), n={len(sim_trips)} driver-day",
        "n_that": len(that_trips), "n_sim": len(sim_trips),
    }
    out["gio_online"] = _row("giờ online/ngày", _pv(that_oh), _pv(sim_oh), "h")
    out["cuoc_hoan_thanh"] = _row("cuốc hoàn thành/ngày", _pv(that_trips), _pv(sim_trips))
    out["luot_duoc_chao"] = _row("lượt được chào/ngày", _pv(that_offer), _pv(sim_offer))
    print()
    out["cuoc_moi_gio"] = _row("⭐ CUỐC / GIỜ ONLINE", _pv(that_tph), _pv(sim_tph))

    # ---------------- tỷ lệ nhận / hoàn thành ----------------
    print(f"\n{'tỷ lệ NHẬN (thật)':<24}{_pv(b['acceptance_rate'].to_list())['median']:>8.3f}"
          f"  [{_pv(b['acceptance_rate'].to_list())['p25']:.3f}–"
          f"{_pv(b['acceptance_rate'].to_list())['p75']:.3f}]")
    print(f"{'tỷ lệ HOÀN THÀNH (thật)':<24}{_pv(b['fulfillment_rate'].to_list())['median']:>8.3f}"
          f"  [{_pv(b['fulfillment_rate'].to_list())['p25']:.3f}–"
          f"{_pv(b['fulfillment_rate'].to_list())['p75']:.3f}]")
    sim_done_per_offer = [t / o for t, o in zip(sim_trips, sim_offer) if o > 0]
    that_done_per_offer = [t / o for t, o in zip(that_trips, that_offer) if o > 0]
    out["hoan_thanh_tren_chao"] = _row("⭐ hoàn thành / được chào",
                                       _pv(that_done_per_offer), _pv(sim_done_per_offer))
    print(f"{'SIM % thời gian RẢNH':<24}{_pv(sim_idle_share)['median']:>8.1%}"
          f"  [{_pv(sim_idle_share)['p25']:.1%}–{_pv(sim_idle_share)['p75']:.1%}]"
          f"   ← KHÔNG có đối chiếu THẬT")
    out["ty_le"] = {"that_acceptance": _pv(b["acceptance_rate"].to_list()),
                    "that_fulfillment": _pv(b["fulfillment_rate"].to_list()),
                    "sim_idle_share": _pv(sim_idle_share)}

    print("\n⚠ CHƯA đối chiếu được **thời gian chờ ghép đơn** (câu Cường hỏi): không bảng thật nào")
    print("  có cột đó; `trips` (t_request→t_assign) bị catalog ghi THIẾU CỘT.")
    print("  ⇒ `% thời gian rảnh` của sim hiện **không có neo thực tế** — đó là một lỗ hổng thật.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float),
                   encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
