"""ĐỐI CHIẾU SIM ↔ BENCHMARK CÓ NGUỒN CÔNG BỐ — thước đo độ thực DUY NHẤT còn hợp lệ.

# Vì sao file này tồn tại

`sim-vs-du-lieu-that.py` đã chứng minh 13 bảng "dữ liệu thật" **không kiểm chứng được gì** (dòng
xe máy do chính `gsm_sim` sinh). Nhưng tôi đã nói quá lời khi kết luận *"repo không có neo nào"*:

**`research/simulation/realism-benchmarks.md` CÓ neo ngoài thật** — 10 benchmark trích nguồn công
bố (arXiv 2503.13200 · MDPI 15(6):3243 · PMC5993247 · NBER w22083 · NYC/Bắc Kinh · VnExpress
11/2023 · Znews · xanhsm.com · Lyft/Uber). Đó **không** phải số của ta, nên đối chiếu với chúng
**không vòng tròn**.

`tests/test_sim_realism.py` hiện gác **3/10** benchmark (served_rate, completion, cancel).
Bảy cái còn lại **không có cổng nào** — file này đo chúng.

⚠ Một cổng đang có (`test_accept_matches_archetype_base`) là **vòng tròn theo thiết kế**: nó
kiểm sim khớp `accept_base` của **chính sim**. Hữu ích như invariant, **vô giá trị** như bằng
chứng độ thực. Không được đếm vào "đã kiểm độ thực".

# Nguồn số sim

`pb1b-raw.json.gz` arm **A** (advisor TẮT, 30 seed × 90 actor = 2.700 driver-day) — thế giới
"tự nhiên", không phải thế giới đã can thiệp.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/doi-chieu-benchmark-nguon-ngoai.py
"""
from __future__ import annotations

import gzip
import json
import pathlib
import statistics as st
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAW = ROOT / "research/audit/2026-08-07-phan-bien-sim-advisor/pb1b-raw.json.gz"
OUT = pathlib.Path(__file__).with_suffix(".json")

# (nhãn, dải target, đơn vị, nguồn — chép từ realism-benchmarks.md, KHÔNG diễn giải lại)
BENCH = {
    "utilization": ((0.45, 0.55), "%",
                    "ngành 30–60%, ~50% peak (dojobusiness); UberX +30% vs taxi (NBER w22083); "
                    "guardrail: <35% THỪA CUNG, >65% thiếu cung"),
    "trips": ((18, 22), "cuốc",
              "Sàn ĐBTN ~13–15/ngày; GrabBike FT 20–30 cuốc (danviet); target median 18–22"),
    "payout": ((380_000, 480_000), "đ",
               "Sàn ĐBTN 8h=320k, 10h=400k (VnExpress 11/2023); bike 9,2h→318k (Znews); "
               "guarantee 15tr/tháng ≈500–580k/ngày"),
    "idle_giua_cuoc": ((10, 15), "′",
                       "Austin mean 12,8′ (SD 14,5); Toronto <25′ đa số"),
    "decline": ((0.02, 0.05), "%", 'DiDi "seldom decline" khi auto-dispatch; giữ 2–5%'),
}


def _verdict(v: float, lo: float, hi: float) -> str:
    if v < lo:
        return f"❌ THẤP HƠN ({(v - lo) / lo:+.0%} so mép dưới)"
    if v > hi:
        return f"❌ CAO HƠN ({(v - hi) / hi:+.0%} so mép trên)"
    return "✅ TRONG DẢI"


def main() -> None:
    data = json.load(gzip.open(RAW, "rt", encoding="utf-8"))
    U, T, P, IDL, OFF, TR = [], [], [], [], [], []
    for r in data:
        for a in r["A"].values():
            on = float(a["online"])
            if on <= 0:
                continue
            occ = on - float(a["idle"]) - float(a["empty"]) - float(a["rest"])
            U.append(occ / on)
            T.append(float(a["trips"]))
            P.append(float(a["payout"]))
            OFF.append(float(a["offered"]))
            TR.append(float(a["trips"]))
            if a["trips"] > 0:
                IDL.append(float(a["idle"]) / float(a["trips"]))   # idle GIỮA CUỐC

    do = {
        "utilization": st.median(U),
        "trips": st.median(T),
        "payout": st.median(P),
        "idle_giua_cuoc": st.median(IDL),
        # `decline` xấp xỉ: 1 − hoàn thành/được chào. ⚠ KHÔNG cùng định nghĩa với "từ chối"
        # (gồm cả huỷ sau nhận + đơn bị cắt lúc 24:00) ⇒ đây là CẬN TRÊN, đánh dấu PROXY.
        "decline": 1.0 - (sum(TR) / sum(OFF) if sum(OFF) else 0.0),
    }

    print(f"n = {len(U)} driver-day · arm A (advisor TẮT) · MOCK pilot_dongda\n")
    print(f"{'benchmark':<18}{'target':>16}{'SIM đo được':>16}   verdict")
    print("-" * 92)
    ket = {}
    for k, ((lo, hi), dv, nguon) in BENCH.items():
        v = do[k]
        pct = dv == "%"
        ft = (f"{lo:.0%}–{hi:.0%}" if pct else
              (f"{lo:,.0f}–{hi:,.0f}" if hi > 100 else f"{lo:g}–{hi:g}"))
        fv = f"{v:.1%}" if pct else (f"{v:,.0f}" if v > 100 else f"{v:.2f}")
        sao = " (PROXY)" if k == "decline" else ""
        print(f"{k:<18}{ft:>16}{fv:>16}   {_verdict(v, lo, hi)}{sao}")
        ket[k] = {"target": [lo, hi], "sim": v, "verdict": _verdict(v, lo, hi), "nguon": nguon}

    print("\n=== ĐỌC CHO ĐÚNG ===")
    print("  · `utilization` **34,1%** rơi ĐÚNG DƯỚI guardrail *'<35% = THỪA CUNG'* của chính")
    print("    tài liệu benchmark ⇒ thế giới sim là thế giới **thừa cung**, theo tiêu chuẩn của nó.")
    print("  · Đó KHÔNG phải tai nạn: `configs/pilot_dongda.yaml:217-231` ghi rõ `actors.n` được")
    print("    **sweep để trúng dải served_rate 80–85%** (65→77,7% · 70→78,8% · 74→80,4%),")
    print("    rồi 74→90. ⇒ **`served_rate ≈ 0,797` là một THIẾT ĐẶT, không phải phát hiện.**")
    print("  · Cái giá chưa ai viết ra: vặn cung lên để mua `served_rate` đã **kéo tụt**")
    print("    `utilization` và `cuốc/tài xế` — hai benchmark khác, cả hai đều đang TRƯỢT.")
    print("  · `trips` trượt còn có nguyên nhân CƠ CẤU đã ghi sẵn ở config:227 — cầu một quận")
    print("    1.200 đơn/ngày ⇒ trần tuyệt đối 1200/90 ≈ 13,3 cuốc/người kể cả phục vụ 100%.")
    print("    Tức benchmark 18–22 **không thể đạt** trong phạm vi một quận. Đây là giới hạn")
    print("    PHẠM VI, không phải bug — nhưng nó khoá trần của payout theo.")
    print("\n  ⇒ Hệ quả cho ADVISOR: trong thế giới thừa cung, giải phóng thời gian tài xế có ít")
    print("    giá trị vì không đủ đơn hấp thụ. Đây là lời giải thích CẤU TRÚC cho việc kênh vị")
    print("    trí chỉ bắt 6,8% trần của nó — và là lý do phải đo `B−A` theo ĐỘ CHẶT thị trường")
    print("    (`do-ben-cua-ket-luan.py`), chứ không chỉ tại một điểm n=90.")

    OUT.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
