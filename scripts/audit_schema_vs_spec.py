"""Audit: mock l1r có ĐÚNG bảng/cột như metadata GSM Cường cung cấp không?

SPEC = chép nguyên từ metadata Cường gửi 2026-07-24 (13 bảng, danh sách cột).
So sánh: tên bảng (full path), SỐ cột, TÊN cột (thiếu/thừa/sai thứ tự).
Cột META của ta (`schema_version`, `source`) được tách riêng — là chủ ý (CLAUDE.md §5
bắt buộc gắn nhãn mock), không tính là "sai spec".

Chạy:  uv run python scripts/audit_schema_vs_spec.py [--data data/mock/realdata-v1]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent
from gsm_core.mockgen.gsm_spec import SPEC, META_COLS  # NGUỒN SỰ THẬT dùng chung


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/mock/realdata-v1")
    args = ap.parse_args()
    d = ROOT / args.data

    ok_tables = miss_tables = 0
    col_issues: list[str] = []
    print(f"{'entity':38s} {'spec':>5s} {'ta':>4s} {'meta':>5s}  verdict")
    print("-" * 78)
    for full_path, (entity, spec_cols) in SPEC.items():
        p = d / f"{entity}.parquet"
        if not p.exists():
            miss_tables += 1
            print(f"{entity:38s} {'-':>5s} {'-':>4s} {'-':>5s}  ❌ THIẾU FILE ({full_path})")
            continue
        ok_tables += 1
        cols = pl.read_parquet(p).columns
        biz = [c for c in cols if c not in META_COLS]
        n_meta = len(cols) - len(biz)
        if spec_cols is None:
            print(f"{entity:38s} {'ENG':>5s} {len(biz):>4d} {n_meta:>5d}  ⚙ ENGINEER (spec chưa có cột)")
            continue
        missing = [c for c in spec_cols if c not in biz]
        extra = [c for c in biz if c not in spec_cols]
        same_order = biz == spec_cols
        if not missing and not extra and same_order:
            verdict = "✅ KHỚP HOÀN TOÀN"
        elif not missing and not extra:
            verdict = "⚠ đủ cột nhưng SAI THỨ TỰ"
            col_issues.append(f"{entity}: sai thứ tự cột")
        else:
            verdict = f"❌ thiếu={missing} thừa={extra}"
            col_issues.append(f"{entity}: thiếu={missing} thừa={extra}")
        print(f"{entity:38s} {len(spec_cols):>5d} {len(biz):>4d} {n_meta:>5d}  {verdict}")

    print("-" * 78)
    print(f"Bảng: {ok_tables}/13 có file; {miss_tables} thiếu. Vấn đề cột: {len(col_issues)}")
    for i in col_issues:
        print("  -", i)
    print(f"\nCột META của ta (chủ ý §5 nhãn mock): {sorted(META_COLS)}")


if __name__ == "__main__":
    main()
