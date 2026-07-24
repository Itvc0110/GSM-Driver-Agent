"""Xuất mọi parquet trong 1 thư mục ra CSV (review tay/Excel).

CSV utf-8-sig (Excel mở tiếng Việt đúng). Gitignored theo data/mock. Regen được.

Chạy:  uv run python scripts/parquet_to_csv.py [--dir data/mock/realdata-v1]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/mock/realdata-v1")
    ap.add_argument("--out", default=None, help="mặc định = <dir>/csv")
    args = ap.parse_args()
    src = (ROOT / args.dir)
    out = Path(args.out) if args.out else (src / "csv")
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob("*.parquet"))
    if not files:
        raise SystemExit(f"Không có parquet trong {src} — gen trước bằng mockgen.realdata")
    for p in files:
        df = pl.read_parquet(p)
        csv_path = out / f"{p.stem}.csv"
        # utf-8-sig để Excel đọc tiếng Việt đúng
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            f.write(df.write_csv())
        print(f"{p.stem:28s} {df.height:>7d} rows -> {csv_path}")
    print(f"OK: {len(files)} CSV in {out}")


if __name__ == "__main__":
    main()
