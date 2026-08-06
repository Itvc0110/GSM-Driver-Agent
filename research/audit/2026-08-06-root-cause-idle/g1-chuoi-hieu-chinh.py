"""G1 — Việc bơm đội 74→90 có phải đang ĐIỀU TRỊ TRIỆU CHỨNG của khuyết tật dispatcher?

    uv run python research/audit/2026-08-06-root-cause-idle/g1-chuoi-hieu-chinh.py

## Câu hỏi (Cường 2026-08-07)

*"Trung bình cuốc được nhận / hoàn thành rất cao, thời gian chờ ghép đơn thực tế cũng không cao như trong
sim. Advisor tối ưu được thời gian thì thời gian đó phải dùng để kiếm tiền — fail này xử lý chưa?"*

## Giả thuyết (chuỗi nhân quả)

Repo ghi nhận dư cung là *"nguyên nhân CƠ CẤU"* (`D-SIM-01`) và bơm đội **74→90** để kéo `served_rate`
lên 0,797. Nhưng số của chính repo cho một tổ hợp **mâu thuẫn**: idle **33,6%** thời gian online, và lúc
một đơn chết vẫn còn trung bình **9,49 tài xế rảnh** — mà **20,25% đơn không được phục vụ**.

Dư cung **và** hụt phục vụ cùng lúc thì nguyên nhân không thể là thiếu người. Giả thuyết:

> **khuyết tật dispatcher** (shortlist hex **2,22 km** hẹp hơn bán kính ETA-khả-thi **3,14 km**)
> → hụt phục vụ → **hiệu chỉnh bơm đội** để đạt `served_rate` → **dư cung** → giá trị biên phút rỗi ≈ 0
> → **mọi kênh advisor tiết-kiệm-thời-gian trượt cổng tiền**.

Nếu đúng: nới shortlist sẽ **tự** nâng `served_rate`, cho phép **hạ đội xe** mà vẫn giữ served — và khi
đội nhỏ lại thì phút rỗi trở nên **khan**, tức advisor có chỗ tạo tiền.

## Ba arm (cùng seed, CRN)

| arm | `candidate_ring_k_max` | `actors.n` | ý nghĩa |
| --- | --- | --- | --- |
| **A0** | 6 (nguyên trạng) | 90 | nền hiện hành |
| **A1** | **8** | 90 | *chỉ* nới shortlist — sweep 12-seed trong config dự báo hết hạn 233→196 |
| **A2** | **8** | **74** | nới shortlist **+ hạ đội về mức trước khi bơm** |

Đọc: `served_rate` · đơn hết hạn · **idle %** (đại lượng quyết định: phút rỗi còn khan không) ·
`trips/tài xế` (realism cá nhân mà `D-SIM-01` nói không thể cùng đạt) · payout mỗi tài xế.

⚠ **Đây là PROBE, không phải đề xuất đổi config.** Nới `k` bị **Q-07 chặn** (k=7 làm `accept_base` P7
lệch −0,053 > dung sai 5pp) ⇒ mọi kết quả ở đây là **bằng chứng cho quyết định của Cường**, không phải
quyết định.

Nhãn: **MOCK/SIM**, arm A (advisor TẮT ở cả ba) — để cô lập **hiệu chỉnh world**, không lẫn advisor.
"""
from __future__ import annotations

import copy
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                                 # noqa: E402
from gsm_sim.runner import run_once                               # noqa: E402

OUT = Path(__file__).resolve().parent / "g1-chuoi-hieu-chinh.json"
SEEDS = [1000, 1001, 1002, 1003, 1004]


def _cfg(base: Config, *, k: int, n_actors: int) -> Config:
    d = copy.deepcopy(base._data)
    d.setdefault("dispatcher", {})["candidate_ring_k_max"] = k
    d.setdefault("actors", {})["n"] = n_actors
    return Config(d, base.root_dir)


def _do(cfg: Config, seed: int) -> dict:
    res = run_once(cfg, seed)
    n_expired = sum(1 for e in res.events if e.kind == "order_expired")
    n_orders = len(res.orders)
    trips = idle = online = payout = 0.0
    n_act = 0
    for a in res.actors:
        trips += float(getattr(a, "trips_done", 0.0))
        idle += float(getattr(a, "idle_min", 0.0))
        online += float(getattr(a, "online_min", 0.0))
        payout += float(getattr(a, "payout_vnd", 0.0))
        n_act += 1
    return {"expired": n_expired, "orders": n_orders,
            "served_rate": (n_orders - n_expired) / max(1, n_orders),
            "trips_per_driver": trips / max(1, n_act),
            "idle_share": idle / max(1e-9, online),
            "payout_per_driver": payout / max(1, n_act),
            "n_actors": n_act}


def main() -> int:
    base = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    arms = {
        "A0 k=6 n=90 (nguyên trạng)": _cfg(base, k=6, n_actors=90),
        "A1 k=8 n=90 (chỉ nới shortlist)": _cfg(base, k=8, n_actors=90),
        "A2 k=8 n=74 (nới + hạ đội)": _cfg(base, k=8, n_actors=74),
    }
    ket: dict[str, dict] = {}
    for ten, cfg in arms.items():
        rows = [_do(cfg, s) for s in SEEDS]
        agg = {k: statistics.mean([r[k] for r in rows]) for k in rows[0]}
        ket[ten] = agg
        print(f"{ten}")
        print(f"   served_rate {agg['served_rate']:.4f} · hết hạn {agg['expired']:6.1f}/ngày "
              f"· idle {agg['idle_share']:6.1%} thời gian online")
        print(f"   trips/tài xế {agg['trips_per_driver']:5.2f} · "
              f"payout/tài xế {agg['payout_per_driver']:10.0f}đ · đội {agg['n_actors']:.0f}\n")

    a0, a1, a2 = (ket[k] for k in arms)
    print("=== PHÂN XỬ GIẢ THUYẾT ===")
    print(f"(1) Nới shortlist MỘT MÌNH có nâng served không?")
    print(f"    served {a0['served_rate']:.4f} → {a1['served_rate']:.4f} "
          f"({(a1['served_rate'] - a0['served_rate']) * 100:+.2f}đp) · "
          f"hết hạn {a0['expired']:.1f} → {a1['expired']:.1f} ({a1['expired'] - a0['expired']:+.1f}/ngày)")
    print(f"(2) Nới + HẠ ĐỘI: served có GIỮ được ở mức nền không?")
    print(f"    served {a2['served_rate']:.4f} vs nền {a0['served_rate']:.4f} "
          f"({(a2['served_rate'] - a0['served_rate']) * 100:+.2f}đp)")
    print(f"(3) Phút rỗi có trở nên KHAN không? (điều kiện để advisor tạo được tiền)")
    print(f"    idle {a0['idle_share']:.1%} → {a2['idle_share']:.1%} "
          f"({(a2['idle_share'] - a0['idle_share']) * 100:+.1f}đp)")
    print(f"(4) Realism CÁ NHÂN (trips/tài xế, benchmark 18–22):")
    print(f"    {a0['trips_per_driver']:.2f} → {a2['trips_per_driver']:.2f} "
          f"({a2['trips_per_driver'] - a0['trips_per_driver']:+.2f})")

    giu_served = (a2["served_rate"] - a0["served_rate"]) > -0.01
    khan_hon = a2["idle_share"] < a0["idle_share"] - 0.02
    print("\n=== KẾT LUẬN SƠ BỘ ===")
    if giu_served and khan_hon:
        print("  ⇒ GIẢ THUYẾT ĐỨNG: nới dispatcher cho phép HẠ ĐỘI mà GIỮ served, và phút rỗi khan hơn")
        print("     ⇒ việc bơm đội 74→90 ĐANG điều trị triệu chứng của khuyết tật shortlist,")
        print("     và nó là NGUYÊN NHÂN GỐC làm mọi kênh tiết-kiệm-thời-gian trượt cổng tiền.")
    elif giu_served:
        print("  ⇒ MỘT PHẦN: hạ đội vẫn giữ served, nhưng phút rỗi CHƯA khan đi đáng kể ⇒ cần hạ sâu hơn")
        print("     hoặc còn nút thắt khác (cooldown, patience) — chưa đủ để kết luận chuỗi nhân quả.")
    else:
        print("  ⇒ 🔴 GIẢ THUYẾT BỊ LÀM YẾU: hạ đội làm served TỤT ⇒ dư cung KHÔNG thuần là bù cho")
        print("     khuyết tật dispatcher; phần 'cơ cấu' mà D-SIM-01 nói là THẬT ở mức đáng kể.")

    OUT.write_text(json.dumps({
        "what": "G1 — bơm đội có phải điều trị triệu chứng của khuyết tật dispatcher?",
        "mock": True, "advisor": "TẮT ở cả ba arm", "seeds": SEEDS,
        "arms": ket,
        "canh_bao": "PROBE, không phải đề xuất đổi config. Nới k bị Q-07 chặn (accept_base P7 lệch 5pp).",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
