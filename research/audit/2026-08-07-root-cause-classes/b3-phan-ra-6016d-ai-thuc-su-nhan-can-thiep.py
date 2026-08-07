"""Cycle 9 / B3 — `+6.016đ/người/ngày` là trung bình TOÀN ĐỘI. Ai thực sự nhận can thiệp?

Bối cảnh: `positioning` là kênh **DUY NHẤT** Cường duyệt bật mặc định (PASS 9/9 ĐA-08,
`UPDATE-087`), và `+6.016đ` được trích khắp nơi làm bằng chứng giá trị của advisor.

Agent `mm-08` báo: chỉ **32,2–44,4%** đội thực sự di chuyển ≥1 lần/ngày, và **53,3–63,3%** được
gán ≥1 lần ⇒ nếu đúng thì `+6.016đ` là trung bình trên một mẫu mà **~2/3 người không nhận can
thiệp nào**. Hai cách đọc dẫn tới **hai quyết định ship khác hẳn nhau**:

  (a) hiệu ứng TẬP TRUNG ở ~35% người di chuyển  ⇒ giá trị thật/người được chạm CAO hơn nhiều
  (b) lan toả HỆ THỐNG (người không di chuyển cũng hưởng vì bớt dồn cục) ⇒ đọc như hiện tại

⚠ Đây là số agent báo. Tôi ĐO LẠI, vì trong cùng vòng audit đã có **2/5 finding định lượng sai**
(`M1` đo ở coverage=single; `M5` đếm cả đội car/premium). Cả hai cùng một cơ chế: **mẫu số nhiễm
những ca cố ý không thuộc phạm vi**.

Đại lượng đo (arm B = advisor BẬT, kênh positioning, `coverage: all`):
  · `n_duoc_gan`   — actor có ≥1 event `standby_followed` HOẶC được đưa vào `standby_plan`
  · `n_di_chuyen`  — actor có ≥1 relocate với `reloc_reason == "standby"` (đi THEO lời khuyên)
  · payout theo NHÓM: được-chạm vs không-được-chạm

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/b3-phan-ra-6016d-ai-thuc-su-nhan-can-thiep.py
"""
from __future__ import annotations

import copy
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
from gsm_sim.runner import run_once  # noqa: E402

OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = [3200, 3201, 3202]


def _cfg(bat: bool) -> Config:
    data = copy.deepcopy(yaml.safe_load(
        (ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")))
    adv = data.setdefault("advice", {})
    adv["enabled"] = bat
    adv["coverage"] = "all"
    return Config(data, ROOT)


def main() -> None:
    rows = []
    print(f"{'seed':>6} {'đội':>5} {'được gán':>10} {'ĐI THEO':>9} {'%gán':>7} {'%đi':>7}")
    for seed in SEEDS:
        r = run_once(_cfg(True), seed)
        gan, di = set(), set()
        for e in r.events:
            if e.kind == "standby_followed":
                gan.add(e.actor_id)
            d = e.detail or {}
            if e.kind == "relocate" and d.get("reason") == "standby":
                di.add(e.actor_id)
        n = len(r.actors)
        rows.append({"seed": seed, "n": n, "n_gan": len(gan), "n_di": len(di),
                     "gan_ids": sorted(gan), "di_ids": sorted(di),
                     "payout": {a.actor_id: float(a.payout_vnd) for a in r.actors}})
        print(f"{seed:>6} {n:>5} {len(gan):>10} {len(di):>9} "
              f"{len(gan) / n:>6.1%} {len(di) / n:>6.1%}")

    print("\n=== PAYOUT theo NHÓM (arm advisor BẬT) ===")
    print(f"{'seed':>6} {'được chạm':>22} {'KHÔNG chạm':>22} {'chênh':>12}")
    for row in rows:
        cham = set(row["gan_ids"])
        p = row["payout"]
        a = [v for k, v in p.items() if k in cham]
        b = [v for k, v in p.items() if k not in cham]
        if not a or not b:
            print(f"{row['seed']:>6}  (một nhóm rỗng — bỏ)")
            continue
        ma, mb = statistics.mean(a), statistics.mean(b)
        row["payout_cham"], row["payout_khong"] = ma, mb
        print(f"{row['seed']:>6} {ma:>15,.0f}đ (n={len(a):>2}) "
              f"{mb:>15,.0f}đ (n={len(b):>2}) {ma - mb:>10,.0f}đ")

    print("\n⚠ ĐỌC CHO ĐÚNG: chênh giữa hai nhóm **KHÔNG PHẢI** hiệu ứng nhân quả của advisor.")
    print("  Ai được gán phụ thuộc vị trí/trạng thái — hai nhóm KHÁC NHAU từ trước khi can thiệp")
    print("  (selection). Số này chỉ trả lời: *liều rơi vào bao nhiêu người*, KHÔNG trả lời")
    print("  *mỗi người được chạm hưởng bao nhiêu*. Muốn cái sau phải so CÙNG actor giữa hai arm.")

    OUT.write_text(json.dumps({
        "cau_hoi": "+6.016d la trung binh toan doi — bao nhieu nguoi THUC SU nhan can thiep?",
        "seeds": SEEDS, "rows": [{k: v for k, v in r.items() if k != "payout"} for r in rows],
        "canh_bao": ("chenh giua hai nhom KHONG phai hieu ung nhan qua — co selection; "
                     "chi tra loi 'lieu roi vao bao nhieu nguoi'"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
