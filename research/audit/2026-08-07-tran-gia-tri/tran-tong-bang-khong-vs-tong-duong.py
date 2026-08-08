"""TRẦN GIÁ TRỊ — kênh nào TỔNG BẰNG KHÔNG, kênh nào TỔNG DƯƠNG?

## Câu hỏi (không có trong tài liệu nào của repo)

Cầu trong sim là **NGOẠI SINH** (`generate_orders` sinh trước, world không tạo thêm đơn). Vậy:

- **Kênh VỊ TRÍ** (positioning, S4 — kênh DUY NHẤT đang ship) chỉ đổi **AI phục vụ đơn nào**.
  Tổng cước bị chặn cứng bởi số đơn **được phục vụ**. Trần của nó = **số đơn HẾT HẠN** — ngoài
  phần đó ra, mỗi chuyến một tài xế giành được là một chuyến tài xế khác mất.
  ⇒ **gần TỔNG BẰNG KHÔNG** giữa các tài xế.

- **Kênh CHẠM MỐC THƯỞNG** (S1 `bonus_feasibility`, S2 `shift_dp`) đổi **số tài xế vượt mốc**.
  Tiền thưởng đến từ **GSM**, không lấy của tài xế khác.
  ⇒ **TỔNG DƯƠNG**.

Nếu đúng, thứ tự ưu tiên hiện tại đang **ngược**: kênh duy nhất được duyệt bật là kênh gần
tổng-bằng-không, còn họ kênh tổng-dương thì 5/6 đang TẮT — và bản án giết `shift_plan` được
tuyên bởi một DP **mù thưởng** (`UPDATE-178`).

## Đo gì

1. **Trần của kênh vị trí** = đơn hết hạn × payout/đơn. Bao nhiêu tiền còn trên bàn?
   Và advisor hiện bắt được bao nhiêu phần trăm của trần đó?
2. **Trần của kênh thưởng** = với mỗi tài xế, khoảng cách tới mốc kế và tiền của bước đó.
   Bao nhiêu người **sát mốc** (trong tầm với của một ca)? Tổng tiền đang bỏ lỡ?
3. **Đối chiếu**: hai trần đó lớn cỡ nào so với nhau, và so với Δ advisor hiện tại (+3.219đ).

⚠ Mọi số là **MOCK** (`pilot_dongda.yaml`). Đây là phép đo TRẦN CẤU TRÚC, không phải dự báo.

Chạy:  uv run python research/audit/2026-08-07-tran-gia-tri/tran-tong-bang-khong-vs-tong-duong.py
"""
from __future__ import annotations

import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gsm_sim.config import Config  # noqa: E402
from gsm_sim.parallel import _cfg_with  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = [3300, 3301, 3302, 3303, 3304]


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    rows = []
    for seed in SEEDS:
        r = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
        pol = r.policy
        acts = r.actors
        n = len(acts)

        # --- (1) TRẦN kênh VỊ TRÍ: đơn hết hạn còn trên bàn ---
        het_han = sum(1 for st, _ in r.order_states.values() if st == "EXPIRED") \
            if hasattr(r, "order_states") else 0
        if not het_han:
            het_han = sum(1 for e in r.events if e.kind == "order_expired")
        xong = sum(int(a.trips_done) for a in acts)
        payout_tb_chuyen = (sum(float(a.payout_vnd) for a in acts) / xong) if xong else 0.0
        tran_vi_tri = het_han * payout_tb_chuyen

        # --- (2)+(3) TRẦN kênh THƯỞNG, tách theo ĐIỀU KIỆN ---
        # ⚠ `day_bonus` trả 0 khi `acceptance < bonus_min_acceptance` BẤT KỂ điểm.
        # ⇒ có BA nhóm khác nhau, và ba lối can thiệp khác nhau:
        #   (a) ĐỦ điều kiện + sát mốc      → kênh CHỐT MỐC (S1/S2) đưa họ qua vạch
        #   (b) THIẾU điều kiện + đã đủ điểm → mất TOÀN BỘ thưởng vì tỷ lệ nhận; kênh accept_lift
        #   (c) thiếu cả hai                 → cần cả hai, khó nhất
        tiers = list(pol.day_bonus_tiers)
        nguong = float(pol.bonus_min_acceptance)
        tran_a = tran_b = 0.0
        n_a = n_b = 0
        for a in acts:
            p_ = int(a.points)
            acc = float(a.acceptance_rate)
            comp = float(a.completion_rate)
            du_dk = acc >= nguong and comp >= float(pol.bonus_min_completion)
            dat = pol.day_bonus(p_, acc, comp)
            dat_neu_du = pol.day_bonus(p_, 1.0, 1.0)          # thưởng nếu KHÔNG vướng điều kiện
            gap = pol.next_tier_gap(p_)
            if du_dk and gap is not None and gap[0] <= 15:     # (a) sát mốc, đủ điều kiện
                n_a += 1
                tran_a += gap[1] - dat                          # phần TĂNG THÊM
            if (not du_dk) and dat_neu_du > 0:                 # (b) đủ điểm nhưng bị cổng chặn
                n_b += 1
                tran_b += dat_neu_du
        bo_lo, n_sat, chi_tiet = tran_a, n_a, []
        rows.append({"seed": seed, "n_actor": n, "het_han": het_han, "trips": xong,
                     "payout_tb_chuyen": payout_tb_chuyen, "tran_vi_tri": tran_vi_tri,
                     "n_sat_moc": n_a, "tran_thuong": tran_a,
                     "n_bi_cong_chan": n_b, "tran_cong_dieu_kien": tran_b})
        print(f"seed {seed}: hết hạn {het_han:>4} · trần VỊ TRÍ {tran_vi_tri:>12,.0f}đ "
              f"| sát mốc {n_sat:>3}/{n} · trần THƯỞNG {bo_lo:>12,.0f}đ")

    n = statistics.mean([r["n_actor"] for r in rows])
    tv = statistics.mean([r["tran_vi_tri"] for r in rows])
    tt = statistics.mean([r["tran_thuong"] for r in rows])
    hh = statistics.mean([r["het_han"] for r in rows])
    ns = statistics.mean([r["n_sat_moc"] for r in rows])
    print(f"\n=== TRẦN CẤU TRÚC (TB {len(SEEDS)} seed, đội {n:.0f} người, MOCK) ===")
    print(f"  kênh VỊ TRÍ  : {hh:>6.1f} đơn hết hạn ⇒ {tv:>12,.0f}đ/ngày = {tv / n:>9,.0f}đ/người")
    print(f"  kênh CHỐT MỐC: {ns:>6.1f} người sát mốc ⇒ {tt:>12,.0f}đ/ngày = {tt / n:>9,.0f}đ/người")
    nb = statistics.mean([r["n_bi_cong_chan"] for r in rows])
    tb2 = statistics.mean([r["tran_cong_dieu_kien"] for r in rows])
    print(f"  kênh TỶ LỆ NHẬN: {nb:>4.1f} người ĐỦ ĐIỂM mà bị cổng điều kiện chặn "
          f"⇒ {tb2:>12,.0f}đ/ngày = {tb2 / n:>9,.0f}đ/người")
    print(f"  tỷ lệ THƯỞNG/VỊ TRÍ = {tt / tv:.2f}×" if tv else "")
    print(f"\n  Δ advisor ĐANG ĐẠT (đo 30 seed): +3.219đ/người "
          f"= {3219 * n / tv:.1%} trần vị trí · {3219 * n / tt:.1%} trần thưởng" if tv and tt else "")
    print("\n⚠ TRẦN ≠ ĐẠT ĐƯỢC. Đây là chặn trên CẤU TRÚC: kênh vị trí không thể vượt số đơn")
    print("  hết hạn (ngoài đó là lấy của tài xế khác); kênh thưởng bị chặn bởi số người sát mốc.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "cau_hoi": "kenh nao TONG BANG KHONG, kenh nao TONG DUONG, tran moi ben bao nhieu?",
        "seeds": SEEDS, "rows": rows,
        "tran_vi_tri_tb": tv, "tran_thuong_tb": tt, "n_actor": n,
        "het_han_tb": hh, "n_sat_moc_tb": ns,
        "canh_bao": "MOCK; TRAN cau truc, khong phai du bao; 'sat moc' = thieu <= 15 diem",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
