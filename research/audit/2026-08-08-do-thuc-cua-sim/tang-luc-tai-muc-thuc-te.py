"""TĂNG LỰC tại đội 60 — mức gần benchmark ngành nhất, nơi kết luận đang KHÔNG phân giải được.

# Vì sao chỉ đo một mức

`do-ben-cua-ket-luan.py` (20 seed/mức) cho: đội 60 → `Δpayout = +1.572đ` CI[−1.280; +4.284]
**ns**. Đó là mức có **13,7 cuốc/tài xế** — gần dải benchmark 18–22 hơn hẳn mức hiện hành (10,0),
tức **thế giới thực tế nhất** trong 5 mức đã chạy.

`ns` ở đó có **hai cách đọc hoàn toàn khác nhau** và 20 seed không tách được:
1. hiệu ứng thật sự **nhỏ hơn** khi cung khan (khớp cơ chế *"advisor là công cụ phân bổ thặng
   dư"* mà bảng đơn điệu đã gợi ra);
2. hiệu ứng **tương đương** nhưng 20 seed **thiếu lực**.

⇒ Chạy thêm **60 seed** (tổng **80**) tại đúng mức đó. Nửa-độ-rộng CI co theo `1/√n`:
2.782 → ~1.391 ⇒ nếu điểm ước lượng giữ ~+1.572 thì CI sẽ **loại 0**, và câu trả lời là (2).
Nếu điểm ước lượng **tụt về 0** khi thêm mẫu thì câu trả lời là (1).

⚠ **Đây là câu hỏi có thể trả lời SAI theo cả hai hướng**, nên ghi trước tiêu chí đọc — không
đợi thấy số rồi mới chọn cách diễn giải.

⚠ Seed **3320–3379** là seed MỚI, không chồng lấn 3300–3319 đã dùng ⇒ gộp được thành 80 mẫu
độc lập. Arm NULL giữ nguyên để cổng placebo vẫn chạy ở cỡ mẫu lớn hơn.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/tang-luc-tai-muc-thuc-te.py
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import random
import statistics as st
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# nạp module cũ (tên có gạch nối) để dùng LẠI `NoisyWorld` + `_do` — không chép lại, tránh
# hai định nghĩa lệch nhau rồi so hai đại lượng khác nhau.
_spec = importlib.util.spec_from_file_location(
    "_doben", pathlib.Path(__file__).with_name("do-ben-cua-ket-luan.py"))
_dob = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_dob)          # type: ignore[union-attr]

from gsm_sim import runner as RUNNER      # noqa: E402
from gsm_sim.config import Config         # noqa: E402
from gsm_sim.parallel import _cfg_with    # noqa: E402
from gsm_sim.runner import run_once       # noqa: E402
from gsm_sim.world import World           # noqa: E402

N_DOI = 60
SEEDS_MOI = list(range(3320, 3380))       # 60 seed MỚI
CU = pathlib.Path(__file__).with_name("do-ben-cua-ket-luan.json")
OUT = pathlib.Path(__file__).with_suffix(".json")


def main() -> None:
    base = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    blob = json.loads(json.dumps(base))
    blob["actors"]["n"] = N_DOI
    cfg = Config(blob, ROOT)

    rows = []
    for k, seed in enumerate(SEEDS_MOI, 1):
        A = _dob._do(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed))
        B = _dob._do(run_once(_cfg_with(cfg, enabled=True, actor_id=None, channels=None,
                                        coverage="all"), seed))
        RUNNER.World = _dob.NoisyWorld
        try:
            N = _dob._do(run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None),
                                  seed))
        finally:
            RUNNER.World = World
        rows.append({"A": A, "B": B, "N": N})
        if k % 10 == 0:
            print(f"  ... {k}/{len(SEEDS_MOI)} seed mới", flush=True)

    trung = sum(1 for r in rows if r["N"]["_fp"] == r["A"]["_fp"])
    rng = random.Random(20260808)
    out: dict = {"n_doi": N_DOI, "seeds_moi": SEEDS_MOI,
                 "placebo_trung_khit": f"{trung}/{len(rows)}",
                 "PLACEBO_VO_HIEU": trung == len(rows)}

    print(f"\n{'chỉ số':<16}{'20 seed (cũ)':>26}{'60 seed (mới)':>26}{'gộp 80 seed':>26}")
    print("-" * 94)
    cu = json.loads(CU.read_text(encoding="utf-8"))["muc"][str(N_DOI)]
    for w in ("payout_mean", "trips_mean", "expired_n", "idle_mean", "served_rate"):
        moi = [r["B"][w] - r["A"][w] for r in rows]
        lo_m, hi_m = _dob._boot(moi, rng)
        # gộp: cũ chỉ còn trung bình, nên gộp có TRỌNG SỐ theo n (không có mẫu thô của lượt cũ)
        n_cu, n_moi = 20, len(rows)
        gop_mean = (cu[w]["B_tru_A"] * n_cu + st.mean(moi) * n_moi) / (n_cu + n_moi)
        out[w] = {"cu": cu[w], "moi": {"mean": st.mean(moi), "ci95": [lo_m, hi_m],
                                       "sig": "SIG" if (lo_m > 0 or hi_m < 0) else "ns"},
                  "gop_mean_co_trong_so": gop_mean, "n_gop": n_cu + n_moi}
        print(f"{w:<16}{cu[w]['B_tru_A']:>+14,.1f} {cu[w]['sig_B']:<4}"
              f"[{cu[w]['ci_B'][0]:>+7,.0f};{cu[w]['ci_B'][1]:>+7,.0f}]"
              f"{st.mean(moi):>+14,.1f} {out[w]['moi']['sig']:<4}"
              f"[{lo_m:>+7,.0f};{hi_m:>+7,.0f}]"
              f"{gop_mean:>+16,.1f}")

    # arm NULL ở cỡ mẫu mới
    dn = [r["N"]["payout_mean"] - r["A"]["payout_mean"] for r in rows]
    ln, hn = _dob._boot(dn, rng)
    out["null_payout"] = {"mean": st.mean(dn), "ci95": [ln, hn],
                          "sig": "SIG" if (ln > 0 or hn < 0) else "ns"}
    print(f"\narm NULL (payout, 60 seed mới): {st.mean(dn):+,.0f}đ "
          f"[{ln:+,.0f}; {hn:+,.0f}] {out['null_payout']['sig']}")
    if out["PLACEBO_VO_HIEU"]:
        print("⛔ PLACEBO VÔ HIỆU — arm N trùng khít arm A, KHÔNG được đọc là đã hiệu chuẩn")
    else:
        print(f"✅ arm NULL có phương sai thật ({trung}/{len(rows)} trùng khít)")

    p = out["payout_mean"]["moi"]
    print("\n=== TRẢ LỜI (tiêu chí đã ghi TRƯỚC khi thấy số) ===")
    if p["sig"] == "SIG":
        print(f"  → (2) THIẾU LỰC: với 60 seed, Δpayout = {p['mean']:+,.0f}đ {p['sig']} "
              f"⇒ hiệu ứng CÓ ở mức thực tế nhất, 20 seed chỉ không đủ mẫu.")
    else:
        print(f"  → (1) hoặc vẫn thiếu lực: Δpayout = {p['mean']:+,.0f}đ vẫn ns "
              f"[{p['ci95'][0]:+,.0f}; {p['ci95'][1]:+,.0f}].")
        print("     Đọc điểm ước lượng: tụt về ~0 ⇒ hiệu ứng THẬT SỰ nhỏ khi cung khan;")
        print("     giữ nguyên ~+1.500đ ⇒ vẫn là vấn đề cỡ mẫu, cần n lớn hơn nữa.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
