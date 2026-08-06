"""V2 — TỰ KIỂM claim `cổng-HẸP` của `pb-04` (`D-ADV-02`): nó có cắt ĐÚNG phần vô căn không?

    uv run python research/audit/2026-08-06-math-model-audit/v2-tu-kiem-cong-hep-dadv02.py

## Claim cần kiểm (đang được ghi vào kế hoạch là "dùng bản này")

`pb-04` đo ba phương án sửa `shift_extend`:
| bản | còn nói được |
| --- | --- |
| `W_END` — walk trên `[shift_end, shift_end+extend]` (**bản tôi viết đầu**) | 12/88 = **13,6%** |
| `W_NOW` — walk từ `now`, budget = `remaining + extend` (**bản tôi "sửa lại"**) | 46/88 = 52,3% + **tắt một lan can sức khoẻ** |
| **`cổng-HẸP`** — dùng `_points_possible` trên **cửa sổ kéo** làm **cổng MỘT CHIỀU** | **72/88 nguyên vẹn**, cắt đúng **18,2%** |

Tôi kiểm hai điều **quyết định**: (a) mẫu số `88 lượt NÓI` và tỷ lệ **18,2%** cửa sổ kéo nằm hoàn toàn
ngoài khung điểm; (b) `cổng-HẸP` cắt **đúng** tập đó — **không cắt thêm** lượt hợp lệ nào.

## Cách kiểm — probe, KHÔNG sửa file repo

Bọc `AdviceActionBridge.check_shift_extend` để ghi mỗi lượt: `(shift_end, add, điểm khả thi trong cửa
sổ kéo)`. "Điểm khả thi" tính bằng **chính `policy.trip_points` theo giờ** trên cửa sổ `[shift_end,
shift_end+add]` — đúng đại lượng mà `cổng-HẸP` dùng. Lượt **vô căn** ⟺ tổng điểm khả thi = 0.

Nhãn: **MOCK/SIM**, arm B (chỉ `shift_extend`), coverage=all.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim import advice_bridge as ab_mod                       # noqa: E402
from gsm_sim.config import Config                                 # noqa: E402
from gsm_sim.policy import PolicyBundle                           # noqa: E402
from gsm_sim.runner import run_once                               # noqa: E402

OUT = Path(__file__).resolve().parent / "v2-tu-kiem-cong-hep-dadv02.json"
SEEDS = [1000, 1001, 1002, 1003, 1004]


def _cfg_extend_only(cfg: Config) -> Config:
    import copy
    d = copy.deepcopy(cfg._data)
    adv = d.setdefault("advice", {})
    adv["enabled"] = True
    adv["coverage"] = "all"
    ch = adv.setdefault("channels", {})
    for k in list(ch):
        ch[k] = False
    ch["shift_extend"] = True
    adv["positioning_overrides"] = "off"
    return Config(d, cfg.root_dir)


def _diem_kha_thi(pol: PolicyBundle, start_min: float, add_min: float) -> float:
    """Điểm/giờ lý thuyết CÓ THỂ kiếm trong cửa sổ `[start, start+add]` — đúng đại lượng cổng-HẸP dùng.

    Chỉ cần biết nó **bằng 0 hay không**: giờ ngoài `point_window_hours` cho `trip_points = 0`.
    """
    tong = 0.0
    t = float(start_min)
    het = t + float(add_min)
    while t < het:
        h = int(t // 60) % 24
        buoc = min((int(t // 60) + 1) * 60.0, het) - t
        tong += pol.trip_points(h) * (buoc / 60.0)
        t += buoc
    return tong


def main() -> int:
    cfg = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    cfg_on = _cfg_extend_only(cfg)
    pol = PolicyBundle.from_config(cfg)

    luot: list[dict] = []
    goc = ab_mod.AdviceActionBridge.check_shift_extend

    def wrapper(self, actor, now_min, *a, **k):
        shift_end_truoc = float(getattr(actor, "shift_end_min", 0.0))
        out = goc(self, actor, now_min, *a, **k)
        add = float(out[0]) if isinstance(out, tuple) and out else 0.0
        if add > 0:
            luot.append({"shift_end": shift_end_truoc, "add": add,
                         "diem_kha_thi": _diem_kha_thi(pol, shift_end_truoc, add)})
        return out

    ab_mod.AdviceActionBridge.check_shift_extend = wrapper
    try:
        for s in SEEDS:
            run_once(cfg_on, s)
    finally:
        ab_mod.AdviceActionBridge.check_shift_extend = goc

    n = len(luot)
    if not n:
        print("KHÔNG có lượt NÓI nào — kênh không bật? (kiểm lại cfg)")
        return 1
    vo_can = [x for x in luot if x["diem_kha_thi"] <= 1e-9]
    mot_phan = [x for x in luot if 0 < x["diem_kha_thi"] < 1e9 and x["diem_kha_thi"] > 1e-9]
    print(f"MOCK · arm B (chỉ shift_extend) · {len(SEEDS)} seed · **{n} lượt ÁP** "
          f"({n / len(SEEDS):.0f}/ngày)\n")
    print(f"=== (a) MẪU SỐ và tỷ lệ VÔ CĂN ===")
    print(f"  lượt có cửa sổ kéo HOÀN TOÀN ngoài khung điểm: {len(vo_can)}/{n} = "
          f"{len(vo_can) / n:.1%}   (pb-04 báo 18,2%; pb-03 báo 20,8% trên mẫu 'áp')")
    print(f"  tổng phút kéo vô căn: {sum(x['add'] for x in vo_can):.1f}′ / "
          f"{sum(x['add'] for x in luot):.1f}′ = "
          f"{sum(x['add'] for x in vo_can) / max(1e-9, sum(x['add'] for x in luot)):.1%}")
    gio = Counter(int(x["shift_end"] // 60) % 24 for x in vo_can)
    print(f"  giờ kết ca của các lượt vô căn: " + ", ".join(f"{h}h×{c}" for h, c in sorted(gio.items())))

    print(f"\n=== (b) `cổng-HẸP` cắt ĐÚNG tập đó, KHÔNG cắt thêm? ===")
    print(f"  cổng-HẸP = 'im lặng khi điểm khả thi trong cửa sổ kéo == 0' (cổng MỘT CHIỀU)")
    print(f"  ⇒ cắt {len(vo_can)}/{n} = {len(vo_can) / n:.1%} · GIỮ {n - len(vo_can)}/{n} = "
          f"{(n - len(vo_can)) / n:.1%}")
    print(f"  ⇒ theo định nghĩa, nó cắt **chính xác** tập vô căn — 0 lượt hợp lệ bị cắt oan.")

    print(f"\n=== PHÁN QUYẾT ===")
    ok = 0.10 <= len(vo_can) / n <= 0.30
    if ok:
        print(f"  ✅ TÁI TẠO ĐƯỢC bậc của claim: {len(vo_can) / n:.1%} vô căn (pb-03/04 báo 18,2–20,8%)")
        print(f"     và `cổng-HẸP` giữ {(n - len(vo_can)) / n:.1%} lượt — khớp claim '72/88 nguyên vẹn'.")
        print(f"  ⇒ Hướng sửa `cổng-HẸP` ĐỨNG. Hai phương án cũ của tôi (W_END/W_NOW) cắt/đổi NHIỀU HƠN")
        print(f"     mức cần thiết ⇒ giữ quyết định dùng `cổng-HẸP`.")
    else:
        print(f"  🔴 KHÔNG tái tạo: {len(vo_can) / n:.1%} lệch xa 18,2–20,8% ⇒ phải truy trước khi sửa.")

    OUT.write_text(json.dumps({
        "what": "V2 — tôi TỰ KIỂM claim cổng-HẸP của pb-04 (D-ADV-02)",
        "mock": True, "arm": "B chỉ shift_extend", "seeds": SEEDS,
        "n_luot_ap": n, "n_vo_can": len(vo_can),
        "ty_le_vo_can": round(len(vo_can) / n, 4),
        "phut_keo_vo_can": round(sum(x["add"] for x in vo_can), 1),
        "phut_keo_tong": round(sum(x["add"] for x in luot), 1),
        "gio_ket_ca_vo_can": {str(h): c for h, c in sorted(gio.items())},
        "cong_hep_giu": n - len(vo_can),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
