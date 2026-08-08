"""P2b — Ô solver CHỌN có tốt hơn ô NGẪU NHIÊN không? Đo ở MỨC LƯỢT GÁN, không mức ngày.

# Vấn đề nó giải

Sàn nhiễu theo NGƯỜI là **17,2×** hiệu ứng (MAD 55.374đ vs +3.219đ) ⇒ mọi câu hỏi theo người
hoặc nhóm nhỏ **không đo được** ở bất kỳ `n` nào trả nổi. Nhưng câu *"ô solver chọn có tốt hơn ô
ngẫu nhiên không?"* **không cần** đo theo người — nó đo được theo **từng lượt gán**, nơi mẫu
nhiều hơn hàng chục lần và **chưa tích luỹ hỗn loạn cả ngày**.

Đây là phép đo trả lời câu Cường đã chọn: *"S4 — chưa đổi hàm mục tiêu, ĐO TRƯỚC ĐÃ"*.

# Vì sao câu hỏi này đáng đo

Tôi đã tự dẫn từ ma trận cost (`capacity_alloc.py:46-50`) rằng S4 **không tối ưu hoá gì**:
`cost[i,j] = pen_i` (khớp) hoặc `pen_i + 10` (lệch), mà `pen_i = soc/100` **chỉ phụ thuộc HÀNG**.
Cộng hằng vào cả hàng **không đổi lời giải** bài toán gán ⇒ ma trận tương đương **chỉ báo 0/1**,
và Hungarian chỉ giải *"tối đa số tài xế được đúng ô mình muốn"* — mà `target` = ô **gần nhất còn
trần**. Kèm bằng chứng độc lập: `greedy ≡ Hungarian 472/472`.

Nếu đúng, thì ô solver chọn **không hơn** ô ngẫu nhiên, và nên bỏ Hungarian thay bằng quy tắc
5 dòng. Nhưng đó mới là **suy luận**; đây là phép **đo**.

# Thiết kế

| arm | ô đích |
| --- | --- |
| **B** | do solver chọn (đường thật) |
| **SHUF** | **hoán vị** đích **giữa chính các allocation** cùng lượt |

`SHUF` giữ **đa tập đích không đổi** ⇒ trần ô/zone-veto vẫn đúng, cùng số người được điều, cùng
cường độ xáo trộn — **chỉ khác: nó không biết đi đâu**. Đó là đối chứng ngẫu nhiên ở mức lượt gán.

**Đại lượng (per-lượt-gán, không per-ngày):**
- `co_don_20p` — **nhị phân**: tài xế có được chào đơn trong 20′ sau khi được điều không.
  Phương sai bị chặn ⇒ đây là đại lượng CHÍNH.
- `cho_don_ke` — số phút tới đơn kế (chỉ trong nhóm có đơn; **censor 45′**).

⚠ **Không ghép cặp được ở mức sự kiện.** Sau lần phân kỳ đầu tiên, hai thế giới trôi khác nhau,
nên allocation thứ *k* của arm B **không phải** cùng sự kiện với thứ *k* của SHUF. Đây là so
**hai mẫu**, không phải cặp — CI rộng hơn, và phải nói ra.

**Phán quyết ghi TRƯỚC khi thấy số:**
- B **thắng** SHUF ⇒ thông tin của S4 **có thật**, chỉ bị chôn dưới nhiễu ngày ⇒ đáng đầu tư vào
  chọn ô, và lúc đó mới bàn đổi hàm mục tiêu.
- **hoà** ⇒ xác nhận suy luận ma trận cost ở mức mạnh hơn: chọn ô **không đáng gì** ⇒ bỏ
  Hungarian, dồn công sang `slots` (P3) hoặc kênh khác.

Chạy: uv run python research/audit/2026-08-08-do-thuc-cua-sim/p2b-do-o-muc-su-kien.py
"""
from __future__ import annotations

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

from gsm_core.solvers import capacity_alloc as CA   # noqa: E402
from gsm_sim.config import Config                   # noqa: E402
from gsm_sim.parallel import _cfg_with              # noqa: E402
from gsm_sim.runner import run_once                 # noqa: E402

SEEDS = list(range(3300, 3330))     # 30 seed, cùng cửa sổ với 9a–9d
OUT = pathlib.Path(__file__).with_suffix(".json")
CUA_SO = 20.0                       # phút — cửa sổ "có đơn kế"
CENSOR = 45.0                       # phút — cắt đuôi chờ
NB = 3000
_THAT_SOLVE = CA.solve              # hàm thật, giữ để khôi phục


def _phut(iso: str) -> float:
    """ISO → phút-sim. Window chạy 05:00–24:00 nên giờ < 5 nghĩa là đã sang ngày sau."""
    h, m = int(iso[11:13]), int(iso[14:16])
    return h * 60 + m + (1440 if h < 5 else 0)


class _Ghi:
    """Bọc `capacity_alloc.solve`: GHI mọi allocation; tuỳ chọn HOÁN VỊ đích.

    ⚠ `world.py:383` import `capacity_alloc` **cục bộ trong hàm** ⇒ vá namespace của world là
    vô tác dụng (đã thử ở `c9d`, `AttributeError`). Phải vá chính thuộc tính `solve` của module.
    """

    def __init__(self, seed: int, hoan_vi: bool):
        self.rng = random.Random(900000 + seed)   # RNG RIÊNG, không đụng dòng nào của world
        self.hoan_vi = hoan_vi
        self.ban_ghi: list[tuple[float, int, str]] = []

    def __call__(self, ai):
        rep = _THAT_SOLVE(ai)
        allocs = (rep.get("solution") or {}).get("allocations") or []
        if self.hoan_vi and len(allocs) > 1:
            dich = [a["assigned_target"] for a in allocs]
            self.rng.shuffle(dich)          # đa tập KHÔNG đổi ⇒ trần/zone-veto vẫn đúng
            for a, t in zip(allocs, dich):
                a["assigned_target"] = t
        t = _phut(ai["t_now"])
        for a in allocs:
            aid = int(str(a["driver_id"]).split("-")[-1])     # `d-<actor_id>`
            self.ban_ghi.append((t, aid, a["assigned_target"]))
        return rep


def _ket_cuc(r, ban_ghi) -> list[dict]:
    """Với mỗi lượt gán: có được chào đơn trong `CUA_SO` phút không, và sau bao lâu."""
    theo_actor: dict[int, list[float]] = {}
    for e in r.events:
        if e.kind == "order_matched":
            theo_actor.setdefault(int(e.actor_id), []).append(float(e.t_min))
    for v in theo_actor.values():
        v.sort()
    ra = []
    for t, aid, _tgt in ban_ghi:
        ds = theo_actor.get(aid, [])
        ke = next((x for x in ds if x > t), None)
        cho = (ke - t) if ke is not None else None
        ra.append({"cho": min(cho, CENSOR) if cho is not None else None,
                   "co_don": bool(cho is not None and cho <= CUA_SO)})
    return ra


def _boot_ty_le(xs, rng):
    m = sorted(st.mean(rng.choices(xs, k=len(xs))) for _ in range(NB))
    return (m[int(0.025 * NB)], m[int(0.975 * NB)])


def main() -> None:
    cfg = Config(yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")),
                 ROOT)
    cfg_b = _cfg_with(cfg, enabled=True, actor_id=None, channels=None, coverage="all")

    # ---- CỔNG 0: DỤNG CỤ ĐO KHÔNG ĐƯỢC LÀM NHIỄU PHÉP ĐO ----------------------------------
    # Recorder của arm B chỉ GHI, không sửa `rep`. Phải chứng minh bằng vân tay, không bằng
    # lập luận — nếu nó lệch dù một đồng thì mọi so sánh dưới đây là so hai thế giới khác nhau.
    _fp = lambda r: round(sum(float(a.payout_vnd) for a in r.actors), 4)   # noqa: E731
    sach = _fp(run_once(cfg_b, SEEDS[0]))
    _g = _Ghi(SEEDS[0], False)
    CA.solve = _g
    try:
        co_may = _fp(run_once(cfg_b, SEEDS[0]))
    finally:
        CA.solve = _THAT_SOLVE
    if sach != co_may:
        print(f"⛔ DỪNG — recorder LÀM ĐỔI thế giới: {sach:,.0f} vs {co_may:,.0f}")
        sys.exit(1)
    print(f"✅ cổng 0: recorder trung tính (vân tay payout trùng khít, {len(_g.ban_ghi)} lượt "
          f"gán ghi được ở seed {SEEDS[0]})\n")

    kq: dict[str, list] = {"B": [], "SHUF": []}
    n_alloc = {"B": 0, "SHUF": 0}
    lap: dict[str, list] = {}
    try:
        for k, seed in enumerate(SEEDS, 1):
            for arm, hv in (("B", False), ("SHUF", True)):
                ghi = _Ghi(seed, hv)
                CA.solve = ghi
                try:
                    r = run_once(cfg_b, seed)
                finally:
                    CA.solve = _THAT_SOLVE
                kq[arm].extend(_ket_cuc(r, ghi.ban_ghi))
                n_alloc[arm] += len(ghi.ban_ghi)
                # ⚠ Một tài xế có thể được điều NHIỀU LẦN/ngày ⇒ các quan sát KHÔNG độc lập,
                # CI bootstrap sẽ hẹp hơn sự thật. Đo mức lặp để biết sai lệch cỡ nào.
                lap.setdefault(arm, []).append(
                    len(ghi.ban_ghi) / max(1, len({a for _t, a, _c in ghi.ban_ghi})))
            print(f"  ... {k}/{len(SEEDS)} seed · B {n_alloc['B']} lượt · "
                  f"SHUF {n_alloc['SHUF']} lượt", flush=True)
    finally:
        CA.solve = _THAT_SOLVE

    rng = random.Random(20260808)
    out: dict = {"n_seed": len(SEEDS), "cua_so_min": CUA_SO, "censor_min": CENSOR,
                 "n_alloc": n_alloc}

    # --- đại lượng CHÍNH: tỷ lệ có đơn trong 20′ ---
    p = {}
    for arm in ("B", "SHUF"):
        xs = [1.0 if x["co_don"] else 0.0 for x in kq[arm]]
        lo, hi = _boot_ty_le(xs, rng)
        p[arm] = {"n": len(xs), "ty_le": st.mean(xs), "ci95": [lo, hi]}

    print(f"\n{'':<20}{'B (solver chọn)':>24}{'SHUF (mù)':>24}")
    print("-" * 68)
    for nhan, lay in (("có đơn ≤20′", lambda a: f"{p[a]['ty_le']:.2%}"),
                      ("CI95", lambda a: f"[{p[a]['ci95'][0]:.2%}; {p[a]['ci95'][1]:.2%}]"),
                      ("n lượt gán", lambda a: f"{p[a]['n']:,}")):
        print(f"{nhan:<20}{lay('B'):>24}{lay('SHUF'):>24}")

    # --- hiệu hai mẫu, bootstrap độc lập ---
    xb = [1.0 if x["co_don"] else 0.0 for x in kq["B"]]
    xs_ = [1.0 if x["co_don"] else 0.0 for x in kq["SHUF"]]
    d = sorted(st.mean(rng.choices(xb, k=len(xb))) - st.mean(rng.choices(xs_, k=len(xs_)))
               for _ in range(NB))
    lo, hi = d[int(0.025 * NB)], d[int(0.975 * NB)]
    sig = lo > 0 or hi < 0
    out["co_don_20p"] = {"B": p["B"], "SHUF": p["SHUF"],
                         "hieu": st.mean(xb) - st.mean(xs_), "ci95": [lo, hi],
                         "sig": "SIG" if sig else "ns"}
    print(f"\n⭐ HIỆU (B − SHUF) tỷ lệ có đơn ≤20′: "
          f"{(st.mean(xb) - st.mean(xs_)):+.2%} [{lo:+.2%}; {hi:+.2%}] "
          f"{'SIG' if sig else 'ns'}")

    # --- phụ: thời gian chờ trong nhóm CÓ đơn ---
    for arm in ("B", "SHUF"):
        w = [x["cho"] for x in kq[arm] if x["cho"] is not None]
        out.setdefault("cho_don_ke", {})[arm] = {
            "n": len(w), "median": st.median(w) if w else float("nan"),
            "mean": st.mean(w) if w else float("nan")}
    cb, cs = out["cho_don_ke"]["B"], out["cho_don_ke"]["SHUF"]
    print(f"   chờ tới đơn kế (censor {CENSOR:.0f}′): "
          f"B median {cb['median']:.2f}′ · SHUF median {cs['median']:.2f}′")

    print("\n=== PHÁN QUYẾT (tiêu chí ghi TRƯỚC khi thấy số) ===")
    if sig and st.mean(xb) > st.mean(xs_):
        print("  → B THẮNG: thông tin của S4 CÓ THẬT ở mức lượt gán, chỉ bị chôn dưới nhiễu ngày.")
        print("    ⇒ Đáng đầu tư vào chọn ô; lúc này mới bàn đổi hàm mục tiêu.")
    elif sig:
        print("  → SHUF thắng B — ô solver chọn TỆ HƠN ngẫu nhiên. Phải điều tra trước khi tin.")
    else:
        print("  → HOÀ: chọn ô KHÔNG đáng gì, xác nhận suy luận ma trận cost ở mức mạnh hơn")
        print("    (greedy ≡ Hungarian 472/472 · cost = hằng-theo-hàng + chỉ báo 0/1).")
        print("    ⇒ Bỏ Hungarian, thay bằng quy tắc 'gửi tới ô gần nhất còn trần';")
        print("      dồn công sang LIỀU (`slots` theo đĩa, P3) hoặc kênh khác.")
        print(f"    ⚠ Lực: n = {p['B']['n']:,} vs {p['SHUF']['n']:,} lượt; CI hiệu rộng "
              f"{(hi - lo):.2%} ⇒ chỉ loại được hiệu ứng lớn hơn ~{max(abs(lo), abs(hi)):.1%}.")

    print("\n⚠ So HAI MẪU, không ghép cặp: sau phân kỳ đầu tiên hai thế giới trôi khác nhau,")
    print("  allocation thứ k của B không phải cùng sự kiện với thứ k của SHUF.")
    lb = st.mean(lap["B"]) if lap.get("B") else float("nan")
    out["lap_moi_tai_xe"] = {"B": lb, "SHUF": st.mean(lap["SHUF"]) if lap.get("SHUF") else None}
    print(f"⚠ Mỗi tài xế được điều trung bình {lb:.2f} lần/ngày ⇒ quan sát KHÔNG hoàn toàn độc")
    print("  lập, CI bootstrap hẹp hơn sự thật. Lặp càng gần 1,00 thì sai lệch càng nhỏ.")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
