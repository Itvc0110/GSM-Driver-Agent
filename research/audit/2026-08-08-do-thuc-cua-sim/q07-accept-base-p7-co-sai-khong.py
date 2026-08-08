"""Q-07 tiền-plan — `accept_base` của P7 SAI, hay CẢ ĐỘI đều lệch?

# Câu hỏi có thể GIẾT cả hướng đi

Cường quyết: xử Q-07 bằng cách **hiệu chỉnh lại `accept_base` của P7** (0,94 có thể là prior cũ
sai). Nhưng trước khi sửa một con số để test hết đỏ, phải trả lời:

> **Lệch là của RIÊNG P7, hay của CẢ BẢY archetype?**

- Riêng P7 lệch ⇒ `0,94` đúng là **tham chiếu sai** ⇒ hiệu chỉnh là **sửa sự thật**.
- Cả đội cùng lệch một chiều ⇒ đây là **hiện tượng cấu trúc** (số hạng kinh tế kéo mọi người
  xuống), và sửa **riêng P7** chính là **vặn số cho test xanh** — đúng thứ mà comment trong
  `configs/pilot_dongda.yaml` gọi là **che khuyết tật**, và tôi đã đồng ý là không được làm.

⇒ Đây là **falsifier cho chính quyết định vừa được duyệt**. Chạy TRƯỚC khi vào plan mode.

# Đo đúng phép mà cổng realism dùng

`tests/test_sim_realism.py:68-73` cộng dồn `orders_accepted / orders_offered` theo archetype trên
nhiều seed, rồi so với `ARCHETYPES[n].accept_base`, dung sai `ACCEPT_TOL_PP`. Script này **chép
đúng phép đó** — không tự nghĩ ra định nghĩa khác, nếu không sẽ tranh luận trên hai đại lượng.

Đo ở **cả k=6 (hiện hành) và k=8** vì đó chính là hai thế giới đang được đem ra chọn.

⚠ Advisor **TẮT** — `accept_base` là thuộc tính của tài xế, không phải của can thiệp.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/q07-accept-base-p7-co-sai-khong.py
"""
from __future__ import annotations

import json
import pathlib
import statistics as st
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gsm_sim.archetypes import ARCHETYPES        # noqa: E402
from gsm_sim.config import Config                # noqa: E402
from gsm_sim.parallel import _cfg_with           # noqa: E402
from gsm_sim.runner import run_once              # noqa: E402

SEEDS = list(range(3300, 3320))      # 20 seed
KS = (6, 8)
OUT = pathlib.Path(__file__).with_suffix(".json")
KHOA_K = "dispatcher.candidate_ring_k_max"       # ⚠ neo ĐÚNG — `candidate_ring_k` là num CHẾT


def _theo_arch(r) -> dict[str, tuple[int, int]]:
    """Chép ĐÚNG `tests/test_sim_realism.py:68-73` — không tự định nghĩa lại."""
    by: dict[str, list[int]] = {}
    for a in r.actors:
        if a.orders_offered:
            cur = by.setdefault(a.archetype, [0, 0])
            cur[0] += a.orders_accepted
            cur[1] += a.orders_offered
    return {n: (acc, off) for n, (acc, off) in by.items()}


def main() -> None:
    base = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    ket: dict = {"seeds": SEEDS, "k": {}}

    for k in KS:
        blob = json.loads(json.dumps(base))
        cur = blob
        *nhanh, la = KHOA_K.split(".")
        for p in nhanh:
            cur = cur.setdefault(p, {})
        truoc = cur.get(la)
        cur[la] = k
        if truoc is None:
            print(f"⛔ DỪNG — khoá `{KHOA_K}` KHÔNG tồn tại trong config; "
                  f"đặt vào sẽ là khoá MA (đúng lớp lỗi `D-SIM-K7`).")
            sys.exit(1)
        cfg = Config(blob, ROOT)

        cong: dict[str, list[int]] = {}
        for seed in SEEDS:
            r = run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), seed)
            for n, (acc, off) in _theo_arch(r).items():
                c = cong.setdefault(n, [0, 0])
                c[0] += acc
                c[1] += off
        ket["k"][str(k)] = {n: {"realized": acc / off, "accepted": acc, "offered": off,
                                "base": ARCHETYPES[n].accept_base,
                                "lech": acc / off - ARCHETYPES[n].accept_base}
                            for n, (acc, off) in sorted(cong.items()) if off}
        print(f"  ... xong k={k} (khoá `{KHOA_K}`: {truoc} → {k})", flush=True)

    print(f"\n{'arch':<6}{'base':>7}{'realized k=6':>15}{'lệch':>9}"
          f"{'realized k=8':>15}{'lệch':>9}{'  n chào (k=6)':>15}")
    print("-" * 78)
    for n in sorted(ARCHETYPES):
        a6, a8 = ket["k"]["6"].get(n), ket["k"]["8"].get(n)
        if not a6 or not a8:
            continue
        co = "  ⚠" if abs(a8["lech"]) > 0.05 else ""
        print(f"{n:<6}{a6['base']:>7.2f}{a6['realized']:>15.4f}{a6['lech']:>+9.4f}"
              f"{a8['realized']:>15.4f}{a8['lech']:>+9.4f}{a6['offered']:>13,}{co}")

    l6 = [v["lech"] for v in ket["k"]["6"].values()]
    l8 = [v["lech"] for v in ket["k"]["8"].values()]
    ket["tom_tat"] = {"lech_trung_binh_k6": st.mean(l6), "lech_trung_binh_k8": st.mean(l8),
                      "so_arch_lech_am_k8": sum(1 for x in l8 if x < 0), "n_arch": len(l8)}

    print(f"\nlệch TRUNG BÌNH toàn đội: k=6 {st.mean(l6):+.4f} · k=8 {st.mean(l8):+.4f}")
    print(f"số archetype lệch ÂM ở k=8: {sum(1 for x in l8 if x < 0)}/{len(l8)}")

    print("\n=== PHÁN QUYẾT (tiêu chí ghi TRƯỚC khi thấy số) ===")
    p7_8 = ket["k"]["8"].get("P7", {}).get("lech", 0.0)
    khac = [v["lech"] for n, v in ket["k"]["8"].items() if n != "P7"]
    bien = max(abs(x) for x in khac) if khac else 0.0
    if abs(p7_8) > 2 * bien and bien < 0.03:
        print(f"  → P7 là NGOẠI LỆ RÕ (lệch {p7_8:+.4f} vs biên độ các arch khác ≤{bien:.4f})")
        print("    ⇒ `accept_base` 0,94 đúng là THAM CHIẾU SAI ⇒ hiệu chỉnh là SỬA SỰ THẬT.")
    elif sum(1 for x in l8 if x < 0) >= len(l8) - 1:
        print(f"  ⛔ CẢ ĐỘI cùng lệch ÂM ({sum(1 for x in l8 if x < 0)}/{len(l8)}) "
              f"⇒ đây là hiện tượng CẤU TRÚC, không phải prior sai của riêng P7.")
        print("    ⇒ Hiệu chỉnh RIÊNG P7 = VẶN SỐ CHO TEST XANH (che khuyết tật). KHÔNG LÀM.")
        print("    ⇒ Việc đúng: tìm vì sao số hạng kinh tế kéo realized xuống dưới base ở mọi")
        print("      archetype — đó mới là khuyết tật thật, và nó lớn hơn Q-07.")
    else:
        print(f"  → KHÔNG rõ ràng: P7 lệch {p7_8:+.4f}, biên độ arch khác {bien:.4f}.")
        print("    ⇒ Chưa đủ căn cứ để hiệu chỉnh riêng P7. Cần đo thêm trước khi vào plan.")

    OUT.write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
