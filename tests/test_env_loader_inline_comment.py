"""🔴 CỔNG: `.env.example` copy thành `.env` phải cho GIÁ TRỊ DÙNG ĐƯỢC, không phải giá trị rác.

Lỗi thật, do soi độc lập tìm ra 2026-08-03 — và nó là lỗi **do chính UPDATE-128 làm nặng thêm**:
tôi thêm chú thích dài **cùng dòng** với biến trong `.env.example`, trong khi `load_env` chỉ
`split("=", 1)` rồi `strip()` mà **không cắt chú thích**. Ai làm đúng lời dặn dòng 1 của file đó
(*"copy thành .env và điền giá trị thật"*) nhận được:

| Biến | Giá trị nạp thật |
| --- | --- |
| `OSRM_BASE_URL` | `'https://router.project-osrm.org   # KHÔNG cần key. Có cổng: …'` |
| `GRAPHHOPPER_API_KEY` | `'# graphhopper.com Directions API, tier 2 — ⚠ ĐỔI TÊN …'` |

Hai hậu quả, và cái thứ hai tệ hơn hẳn:

1. URL mang khoảng trắng ⇒ `urllib` nổ `InvalidURL` ⇒ bị `except Exception` **nuốt** ⇒ mirror B
   mất **lặng lẽ**.
2. Chuỗi chú thích là **truthy** ⇒ nó **vượt qua** guard `if not api_key: return None` ⇒ gọi
   GraphHopper thật với khoá rác ⇒ 401 sau ~5 s. Tầng 2 *trông như đã cấu hình* mà chết — đúng
   thứ `.env.example` mới được sửa để cảnh báo, và cách sửa đó lại dẫn người ta vào bẫy.

⚠ Điểm đắt nhất: chú thích tôi thêm vào để CẢNH BÁO *"thiếu biến này thì tier 2 chết lặng lẽ"*
chính là thứ tạo ra một cách chết lặng lẽ MỚI. Cổng này canh cả hai đầu — bộ nạp phải cắt chú
thích, VÀ `.env.example` phải nạp ra được giá trị hợp lệ.
"""
from __future__ import annotations

import pathlib

import pytest

from gsm_core.advisor.llm_client import _strip_inline_comment, load_env

ROOT = pathlib.Path(__file__).resolve().parents[1]

_KHOA_URL = ("OSRM_BASE_URL", "OPENROUTER_BASE_URL", "OPENAI_BASE_URL",
             "WEATHER_BASE_URL", "JINA_READER_URL", "STADIA_BASE_URL", "LANGFUSE_HOST")


def test_cat_chu_thich_inline():
    assert _strip_inline_comment("https://a.test   # ghi chú") == "https://a.test"
    assert _strip_inline_comment("abc123   # khoá thật của tôi") == "abc123"
    assert _strip_inline_comment("# chỉ có chú thích") == ""


def test_KHONG_pha_gia_tri_chua_dau_thang_hop_le():
    """Đối chứng bắt buộc: `#` là ký tự hợp lệ trong mật khẩu và trong URL fragment. Cắt quá tay
    còn tệ hơn không cắt — nó làm hỏng một giá trị ĐANG đúng."""
    assert _strip_inline_comment("p@ss#word") == "p@ss#word"          # không có space trước #
    assert _strip_inline_comment("https://a.test/x#frag") == "https://a.test/x#frag"
    assert _strip_inline_comment('"giá trị  # trong nháy"') == "giá trị  # trong nháy"
    assert _strip_inline_comment("'sk-abc  # thật'") == "sk-abc  # thật"


def test_env_example_copy_thanh_env_cho_gia_tri_DUNG_DUOC(monkeypatch, tmp_path):
    """Ca thật: copy `.env.example` → `.env` rồi nạp. Mọi biến nạp ra phải KHÔNG chứa `#`."""
    src = (ROOT / ".env.example").read_text(encoding="utf-8")
    p = tmp_path / ".env"
    p.write_text(src, encoding="utf-8")

    for line in src.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            monkeypatch.delenv(line.split("=", 1)[0].strip(), raising=False)
    load_env(p)

    xau = []
    for line in src.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k = line.split("=", 1)[0].strip()
        import os
        v = os.environ.get(k, "")
        if "#" in v:
            xau.append(f"{k}={v[:70]!r}")
    assert not xau, (
        "biến nạp từ `.env.example` còn mang chú thích ⇒ giá trị rác, và mọi guard `if not x` "
        f"cho nó đi qua: {xau}")


@pytest.mark.parametrize("k", _KHOA_URL)
def test_moi_bien_URL_trong_env_example_la_URL_dung_duoc(monkeypatch, tmp_path, k):
    """Cắt chú thích chưa đủ — phải chứng minh giá trị **dùng được làm URL**. `urllib` nổ
    `InvalidURL` với khoảng trắng, và ở `try_osrm` lỗi đó bị `except Exception` nuốt."""
    import os
    import urllib.parse

    src = (ROOT / ".env.example").read_text(encoding="utf-8")
    p = tmp_path / ".env"
    p.write_text(src, encoding="utf-8")
    monkeypatch.delenv(k, raising=False)
    load_env(p)
    v = os.environ.get(k)
    if not v:
        pytest.skip(f"{k} để trống trong .env.example (chờ người dùng điền)")
    u = urllib.parse.urlsplit(v)
    assert u.scheme in ("http", "https"), f"{k}={v!r} thiếu scheme dùng được"
    assert u.netloc and " " not in u.netloc, (
        f"{k}={v!r} có host chứa khoảng trắng ⇒ urllib nổ InvalidURL và lỗi bị nuốt lặng lẽ")


def test_bien_khoa_trong_env_example_hoac_RONG_hoac_la_khoa_that(monkeypatch, tmp_path):
    """Biến khoá trong file MẪU phải **rỗng** (chờ điền) — không được là một chuỗi truthy nào
    khác, vì truthy nghĩa là nó vượt được mọi guard `if not key`."""
    import os
    src = (ROOT / ".env.example").read_text(encoding="utf-8")
    p = tmp_path / ".env"
    p.write_text(src, encoding="utf-8")
    xau = []
    for line in src.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k = line.split("=", 1)[0].strip()
        if not k.endswith("_API_KEY") and not k.endswith("_KEY"):
            continue
        monkeypatch.delenv(k, raising=False)
        load_env(p)
        v = os.environ.get(k, "")
        if v and not v.startswith(("sk-", "pk-", "AIza")):
            xau.append(f"{k}={v[:50]!r}")
    assert not xau, (
        "biến KHOÁ trong `.env.example` có giá trị truthy không phải khoá thật ⇒ nó vượt qua "
        f"`if not api_key` rồi gọi API với rác (401 sau ~5s, tier trông như đã cấu hình): {xau}")
