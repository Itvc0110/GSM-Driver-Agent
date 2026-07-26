"""SIM-5 — regen bộ mock 13 bảng `l1r` từ engine HIỆN TẠI + so sánh với bộ cũ.

    uv run python scripts/regen_mock.py --days 90

Vì sao cần: `DIRECTIVES` §1 — *"bản publish cuối cùng CHẠY TRÊN MOCK DATA"*. Bộ sinh trước SIM-1
mang hành vi của một thế giới **đã bị bác bỏ** (served 61.9%, accept 96.3%, completion 99.6%,
không có huỷ-sau-nhận). Mọi solver/advisor thử trên đó là thử sai nền.

Script in **bảng so sánh CŨ → MỚI** để thấy rõ SIM-1..4 đã đổi dữ liệu thế nào; nếu không so thì
không có cách nào biết bộ mới có thật sự tốt hơn hay chỉ khác đi.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import polars as pl                                       # noqa: E402

from gsm_core.mockgen.realdata import generate_realdata    # noqa: E402

FIELDS = [
    ("acceptance_rate", "median", "tỷ lệ nhận (median)"),
    ("acceptance_rate", "p10", "tỷ lệ nhận p10"),
    ("acceptance_rate", "p90", "tỷ lệ nhận p90"),
    ("fulfillment_rate", "median", "tỷ lệ hoàn thành (median)"),
    ("cancellation_rate", "median", "tỷ lệ huỷ (median)"),
    ("completed_count", "median", "cuốc/ngày (median)"),
]


def snapshot(path: Path) -> dict | None:
    f = path / "driver_statistic_daily.parquet"
    if not f.exists():
        return None
    d = pl.read_parquet(f)
    out = {"rows": d.height,
           "acceptance_eq_1": int((d["acceptance_rate"] >= 0.999).sum())}
    for col, stat, _ in FIELDS:
        key = f"{col}.{stat}"
        out[key] = (float(d[col].median()) if stat == "median"
                    else float(d[col].quantile(float(f"0.{stat[1:]}"))))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--seed-base", type=int, default=7000)
    ap.add_argument("--out", default=str(ROOT / "data" / "mock" / "realdata-v1"))
    ap.add_argument("--keep-old", action="store_true", help="giữ bộ cũ ở *-prev để đối chiếu")
    args = ap.parse_args()

    out = Path(args.out)
    before = snapshot(out)

    if args.keep_old and out.exists():
        prev = out.parent / (out.name + "-prev")
        shutil.rmtree(prev, ignore_errors=True)
        shutil.copytree(out, prev)
        print(f"đã giữ bộ cũ tại: {prev}")

    print(f"đang sinh {args.days} ngày (seed_base={args.seed_base})…")
    # `generate_realdata` trả về MANIFEST (không phải counts) — counts nằm trong đó
    manifest = generate_realdata(days=args.days, seed_base=args.seed_base, out_dir=out)
    after = snapshot(out)

    print("\n=== record_counts ===")
    for k, v in sorted((manifest.get("record_counts") or {}).items()):
        print(f"  {k:38s} {int(v):>9,d}")

    if before and after:
        print("\n=== SO SÁNH CŨ → MỚI (driver_statistic_daily) ===")
        print(f"{'chỉ số':32s}{'CŨ':>12s}{'MỚI':>12s}{'đổi':>12s}")
        print(f"{'số driver-day':32s}{before['rows']:>12,d}{after['rows']:>12,d}"
              f"{after['rows']-before['rows']:>+12,d}")
        print(f"{'acceptance = 1.00 (thoái hoá)':32s}{before['acceptance_eq_1']:>12,d}"
              f"{after['acceptance_eq_1']:>12,d}{after['acceptance_eq_1']-before['acceptance_eq_1']:>+12,d}")
        for col, stat, label in FIELDS:
            k = f"{col}.{stat}"
            print(f"{label:32s}{before[k]:>12.4f}{after[k]:>12.4f}{after[k]-before[k]:>+12.4f}")
    else:
        print("\n(không có bộ cũ để so sánh)")

    man = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    print(f"\nengine_commit: {man.get('engine_commit')} · generator: {man.get('generator')}")
    print("MOCK — không phải số thật của GSM.")


if __name__ == "__main__":
    main()
