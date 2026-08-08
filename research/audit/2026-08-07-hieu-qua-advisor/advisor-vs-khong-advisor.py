"""HIỆU QUẢ ADVISOR so với thế giới KHÔNG CÓ ADVISOR — n=30 seed, ghép cặp CRN.

## Ba arm, và vì sao cần cả ba

| arm | là gì |
| --- | --- |
| **A** | `advice.enabled = False` — thế giới KHÔNG CÓ ADVISOR |
| **B** | `advice.enabled = True`, `coverage: all` — advisor bật (kênh sống: positioning) |
| **N** | **NULL**: advisor TẮT như A, chỉ **rút lại nhiễu niềm tin cá nhân** (`RNG +7919`) |

Arm **N** là **cột hiệu chuẩn**. Không có nó thì mọi `B − A` bị đọc quá tay: hôm nay tôi đã báo
sai một kết luận lớn vì thiếu đúng cột này (`UPDATE-182`) — sàn nhiễu theo NGƯỜI là **17,2×**
hiệu ứng, nên `B − A` chứa cả **hỗn loạn** lẫn **tác dụng**.

⇒ Đại lượng để trích là **`B − A`** cho tác động tổng, và **`N − A`** để biết bao nhiêu phần
trong đó một thế giới **không can thiệp gì** cũng tạo ra được.

## Nguồn

`research/audit/2026-08-07-phan-bien-sim-advisor/pb1b-raw.json.gz` — snapshot per-actor,
3 arm × 30 seed (3300–3329), do vòng phản biện dựng và tôi đã **tự đọc code dựng arm N**
(`pb1b-co-che-va-lat-cat-co-dinh.py`: cùng seed, cùng đơn, `enabled=False`, chỉ đổi khoá RNG).

⚠ Artifact chỉ có **per-actor**. `served_rate` và `đơn hết hạn` là đại lượng HỆ THỐNG, không
nằm ở đây ⇒ script này **không** báo chúng; chúng vẫn là số agent đo mà tôi chưa tự kiểm.

Chạy: uv run python research/audit/2026-08-07-hieu-qua-advisor/advisor-vs-khong-advisor.py
"""
from __future__ import annotations

import gzip
import json
import pathlib
import random
import statistics
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[3]
RAW = ROOT / "research/audit/2026-08-07-phan-bien-sim-advisor/pb1b-raw.json.gz"
OUT = pathlib.Path(__file__).with_suffix(".json")
B = 4000

# (khoá, nhãn, đơn vị, chiều TỐT: +1 tăng là tốt, −1 giảm là tốt)
CHI_SO = [("payout", "payout/tài xế", "đ", +1),
          ("gross", "gross/tài xế", "đ", +1),
          ("trips", "chuyến/tài xế", "", +1),
          ("idle", "phút RẢNH", "′", -1),
          ("empty", "phút chạy RỖNG", "′", -1),
          ("online", "phút online", "′", 0),
          ("offered", "lượt được chào", "", +1)]


def _boot(xs, rng):
    m = sorted(statistics.mean(rng.choices(xs, k=len(xs))) for _ in range(B))
    return (m[int(0.025 * B)], m[int(0.975 * B)])


def main() -> None:
    data = json.load(gzip.open(RAW, "rt", encoding="utf-8"))
    rng = random.Random(20260808)
    out: dict = {"n_seed": len(data), "chi_so": {}}

    print(f"n = {len(data)} seed ghép cặp CRN · 90 tài xế/seed · MOCK (pilot_dongda)\n")
    print(f"{'chỉ số':<18}{'A (không advisor)':>19}{'B − A (advisor)':>26}"
          f"{'N − A (nhiễu thuần)':>26}")
    print("-" * 90)
    for key, nhan, dv, chieu in CHI_SO:
        a_mean, dba, dna = [], [], []
        for row in data:
            A, Bm, N = row["A"], row["B"], row["N"]
            ids = sorted(set(A) & set(Bm) & set(N))
            a_mean.append(statistics.mean(float(A[i][key]) for i in ids))
            dba.append(statistics.mean(float(Bm[i][key]) - float(A[i][key]) for i in ids))
            dna.append(statistics.mean(float(N[i][key]) - float(A[i][key]) for i in ids))
        mb, (lb, hb) = statistics.mean(dba), _boot(dba, rng)
        mn, (ln, hn) = statistics.mean(dna), _boot(dna, rng)
        sb = "SIG" if (lb > 0 or hb < 0) else "ns "
        sn = "SIG" if (ln > 0 or hn < 0) else "ns "
        out["chi_so"][key] = {"nhan": nhan, "A": statistics.mean(a_mean),
                              "B_tru_A": mb, "ci_B": [lb, hb], "sig_B": sb.strip(),
                              "N_tru_A": mn, "ci_N": [ln, hn], "sig_N": sn.strip()}
        print(f"{nhan:<18}{statistics.mean(a_mean):>18,.0f}{dv:<1}"
              f"{mb:>+14,.0f} [{lb:>+7,.0f};{hb:>+7,.0f}] {sb}"
              f"{mn:>+13,.0f} [{ln:>+7,.0f};{hn:>+7,.0f}] {sn}")

    print("\n=== ĐỌC CHO ĐÚNG ===")
    p = out["chi_so"]["payout"]
    print(f"  · Advisor làm payout/tài xế đổi **{p['B_tru_A']:+,.0f}đ** "
          f"= {p['B_tru_A'] / p['A']:+.2%} so với nền {p['A']:,.0f}đ ({p['sig_B']})")
    print(f"  · Thế giới KHÔNG CÓ ADVISOR, chỉ rút lại nhiễu: **{p['N_tru_A']:+,.0f}đ** "
          f"({p['sig_N']}) ⇒ hiệu ứng của advisor KHÔNG phải hiện vật nhiễu")
    print("  · ⚠ `served_rate` và `đơn hết hạn` là đại lượng HỆ THỐNG, KHÔNG có trong artifact")
    print("    per-actor này ⇒ script này không báo chúng.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
