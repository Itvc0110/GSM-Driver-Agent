"""🔴 Đưa cổng JS `ui/web/tests/cards_soft_gate.mjs` vào suite Python.

## Vì sao phải bọc thay vì để nó chạy riêng

"Suite xanh" của repo này = hai lệnh `pytest` (`D-M3-09`). Một cổng chỉ chạy khi có người nhớ gõ
`node ...` là cổng **tự nguyện** — và repo đã trả giá đủ cho cơ chế tự nguyện: `D-M3-01` sống qua 39
artifact vì cổng canh nó chỉ tồn tại trong tài liệu.

## Vì sao `Nợ 7` không cần jsdom (tiền đề cũ SAI)

`Nợ 7` treo với ghi chú *"cần jsdom/node — quyết định hạ tầng, hỏi Cường riêng"*. Đo 2026-08-04:
node có sẵn, `cards.js` đã là ES module, và `_render` chỉ chạm 6 API DOM ⇒ stub ~40 dòng là đủ.
Không `package.json`, không `npm install`. Chi phí kiểm tiền đề: hai lệnh `Get-Command`.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "ui/web/tests/cards_soft_gate.mjs"


def test_cong_cards_js_ton_tai():
    """Tách khỏi test dưới có chủ ý: nếu file cổng bị xoá/đổi tên thì test này ĐỎ **kể cả trên máy
    không có node** — nơi test kia chỉ `skip`. Một cổng biến mất mà suite vẫn xanh là cách chết
    thường gặp nhất của cổng."""
    assert GATE.is_file(), f"cổng JS biến mất: {GATE}"


@pytest.mark.skipif(shutil.which("node") is None,
                    reason="không có `node` trên máy này — cổng JS KHÔNG chạy được, không phải đã qua")
def test_cards_js_khong_ve_nut_lam_theo_cho_khuyen_mem():
    """Chạy cổng thật bằng node và đòi exit 0.

    ⚠ `skipif` ở đây là một khoảng hở CÓ Ý THỨC: máy không có node sẽ **bỏ qua**, và một cổng bị bỏ
    qua trông y hệt một cổng đã qua trong dòng `pytest -q`. Chấp nhận vì bắt buộc node sẽ chặn cả
    suite trên máy chưa cài — nhưng lý do skip viết rõ *"KHÔNG chạy được, không phải đã qua"* để ai
    đọc log không hiểu nhầm. Nếu về sau CI cố định có node, đổi `skipif` thành `fail`."""
    r = subprocess.run(["node", str(GATE)], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, (
        "cổng khuyên mềm ở tầng CLIENT ĐỎ — backend chặn được DỮ LIỆU nhưng không chặn được CÂU HỎI, "
        "và cái nút chính là câu hỏi:\n" + (r.stdout or "") + (r.stderr or ""))


@pytest.mark.skipif(shutil.which("node") is None, reason="không có `node`")
def test_cong_JS_nay_THUC_SU_kiem_gi_do():
    """Bẫy #9 (cổng quét ra RỖNG thì luôn xanh): đòi cổng in ra một số lượng phép kiểm tối thiểu.

    Nếu ai đó rút ruột file `.mjs` xuống còn `process.exit(0)` thì test trên vẫn xanh — test này thì
    không."""
    r = subprocess.run(["node", str(GATE)], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    so_kiem = (r.stdout or "").count("✓") + (r.stdout or "").count("✗")
    assert so_kiem >= 10, (
        f"cổng JS chỉ chạy {so_kiem} phép kiểm — quá ít, nhiều khả năng nó đã bị rút ruột.\n"
        + (r.stdout or ""))
    assert "ĐỐI CHỨNG" in (r.stdout or ""), (
        "cổng mất phần ĐỐI CHỨNG ⇒ nó không còn phân biệt được 'ranh giới chạy đúng' với "
        "'thẻ nào cũng không có nút'")
