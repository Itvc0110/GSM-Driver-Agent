"""V1 — TỰ KIỂM arm NULL của `pb-02` (`D-M3-20`): nhiễu trôi-stream có thật bằng cả hiệu ứng không?

    uv run python research/audit/2026-08-06-math-model-audit/v1-tu-kiem-arm-null-dm320.py

## Vì sao phải tự kiểm

`pb-02` (agent) báo: dựng arm NULL (kênh `rest_window` **BẬT**, coin **luôn từ chối** ⇒ **đúng 0 can
thiệp**) rồi đo, được `SD_nhiễu / SD_tổng-quan-sát = 1,12 · 1,22 · 1,05` ⇒ *"nhiễu trôi-stream một mình
giải thích toàn bộ độ phân tán của Δ post-FIX"*, và `A == B_fix` **60/60**.

Hai con số đó đang **đỡ một quyết định Cường phải ra** (duyệt plan `D-M3-20`). Hôm nay tôi đã trả giá vì
tin số của agent hơn số của repo (`UPDATE-173`: rút lại đính chính 65,3%). ⇒ **"tác tử báo" ≠ "tôi đo"**.

## Thiết kế (tối thiểu nhưng đủ phân xử)

Ba arm, **cùng seed** (CRN):
- **A**   : `advice.enabled = False` — nền
- **Bnull**: kênh `rest_window` BẬT + `coin_follows` patch → **luôn False** ⇒ **0 can thiệp thật**
- (không dựng B_fix ở đây: fix chưa được duyệt để viết)

Nếu `Bnull ≠ A` thì **toàn bộ** chênh lệch là **nhiễu trôi-stream thuần** — vì không một lời khuyên nào
được thi hành. Đo `SD` của chênh lệch đó theo seed rồi so với **nửa-độ-rộng-CI** của bộ số acceptance
`UPDATE-142` (nguồn: `research/audit/` hoặc chính UPDATE) để biết nhiễu chiếm bao nhiêu phần.

⚠ Chạy **multiday** (`run_multiday`) vì `pb-01` đã chỉ ra: run **1 ngày** cho **0 lượt** tới dòng 916
(kênh trơ hoàn toàn) ⇒ đo 1 ngày sẽ ra `Δ = 0` và kết luận sai là "không có nhiễu".

Nhãn: **MOCK/SIM**.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim import advice_bridge as ab_mod                       # noqa: E402
from gsm_sim.config import Config                                 # noqa: E402

OUT = Path(__file__).resolve().parent / "v1-tu-kiem-arm-null-dm320.json"
SEEDS = [7000, 7001, 7002, 7003, 7004, 7005]
DAYS = 3


def _cfg_rest_on(cfg: Config) -> Config:
    """Bản sao cfg với advice bật + CHỈ kênh rest_window, coverage=all."""
    import copy
    d = copy.deepcopy(cfg._data)
    adv = d.setdefault("advice", {})
    adv["enabled"] = True
    adv["coverage"] = "all"
    ch = adv.setdefault("channels", {})
    for k in list(ch):
        ch[k] = False
    ch["rest_window"] = True
    adv["positioning_overrides"] = "off"
    return Config(d, cfg.root_dir)


def _metrics(md) -> dict:
    """Ba đại lượng mà UPDATE-142 dùng làm acceptance của D-M3-04-FIX."""
    rest = span = 0.0
    payout = 0.0
    spans = []
    for day in md.days:
        for a in day.actors:
            rest += float(getattr(a, "rest_min", 0.0))
            payout += float(getattr(a, "payout_vnd", 0.0))
            spans.append(float(getattr(a, "online_min", 0.0)))
    spans.sort()
    if spans:
        span = spans[min(len(spans) - 1, int(len(spans) * 0.90))]
    return {"rest_min_total": rest, "work_span_p90": span, "payout_total": payout}


def main() -> int:
    from gsm_sim.multiday import run_multiday
    cfg = Config.load(str(ROOT / "configs" / "pilot_dongda.yaml"))
    cfg_on = _cfg_rest_on(cfg)

    goc_coin = ab_mod.AdviceActionBridge.coin_follows
    rows = []
    for s in SEEDS:
        md_a = run_multiday(cfg, s, DAYS)
        m_a = _metrics(md_a)
        ab_mod.AdviceActionBridge.coin_follows = lambda self, *a, **k: False   # 0 can thiệp
        try:
            md_n = run_multiday(cfg_on, s, DAYS)
        finally:
            ab_mod.AdviceActionBridge.coin_follows = goc_coin
        m_n = _metrics(md_n)
        rows.append({"seed": s, **{f"d_{k}": m_n[k] - m_a[k] for k in m_a},
                     **{f"A_{k}": m_a[k] for k in m_a}})
        print(f"  seed {s}: Δrest {rows[-1]['d_rest_min_total']:+9.1f}′ · "
              f"Δspan_p90 {rows[-1]['d_work_span_p90']:+7.1f}′ · "
              f"Δpayout {rows[-1]['d_payout_total']:+12.0f}đ")

    print(f"\n=== ARM NULL (kênh BẬT, coin LUÔN từ chối ⇒ 0 can thiệp) · {len(SEEDS)} seed × "
          f"{DAYS} ngày ===")
    ket = {}
    for k, nhan in (("rest_min_total", "rest_min_total"), ("work_span_p90", "work_span_p90"),
                    ("payout_total", "payout đội")):
        ds = [r[f"d_{k}"] for r in rows]
        nen = statistics.mean([r[f"A_{k}"] for r in rows])
        sd = statistics.stdev(ds) if len(ds) > 1 else 0.0
        khac0 = sum(1 for d in ds if abs(d) > 1e-9)
        print(f"  {nhan:16s} SD nhiễu {sd:12.1f} ({sd / nen:6.2%} nền {nen:12.1f}) · "
              f"|max| {max(abs(d) for d in ds):11.1f} · khác 0 ở {khac0}/{len(ds)} seed")
        ket[k] = {"sd": round(sd, 2), "sd_pct_nen": round(sd / nen, 5) if nen else None,
                  "max_abs": round(max(abs(d) for d in ds), 2), "khac_0": khac0}

    print("\n=== PHÁN QUYẾT ===")
    if all(v["khac_0"] > 0 for v in ket.values()):
        print("  ⇒ arm NULL KHÁC arm A dù 0 can thiệp ⇒ **nhiễu trôi-stream TỒN TẠI** (claim gốc đứng).")
        print("     Đối chiếu bộ acceptance UPDATE-142 (nửa-CI ⇒ SD ≈ nửaCI/1,96×√30):")
        for k, nuaci in (("rest_min_total", 50.25), ("work_span_p90", 6.6), ("payout_total", None)):
            if nuaci is None:
                continue
            sd142 = nuaci / 1.96 * (30 ** 0.5)
            print(f"       {k:16s} SD_nhiễu {ket[k]['sd']:8.1f} vs SD_UPDATE-142 ≈ {sd142:8.1f} "
                  f"⇒ tỷ số {ket[k]['sd'] / sd142:5.2f}")
    else:
        print("  ⇒ 🔴 arm NULL == arm A ở một hoặc nhiều đại lượng ⇒ claim của pb-02 KHÔNG tái tạo được"
              " ở thiết kế này; phải truy vì sao (có thể do số ngày/seed hoặc cách patch coin).")

    OUT.write_text(json.dumps({
        "what": "V1 — tôi TỰ KIỂM arm NULL của pb-02 (D-M3-20)",
        "mock": True, "seeds": SEEDS, "days": DAYS,
        "thiet_ke": "A = advice off · Bnull = rest_window ON + coin_follows luôn False (0 can thiệp)",
        "per_seed": rows, "tong_hop": ket,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nartifact → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
