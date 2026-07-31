"""🔴 D-M3-16a — CỔNG: chỉ được có MỘT bảng màu cho trạng thái hoạt động.

Quét `D-M3-15` (UPDATE-117) tìm ra `trajectory.STATE_COLORS` là **bảng màu thứ hai** và nó
**xung đột** với `dashboard_theme.ACTIVITY_COLORS` — bảng mà dashboard thật đang dùng:

| Trạng thái | `trajectory.STATE_COLORS` | `dashboard_theme.ACTIVITY_COLORS` |
| --- | --- | --- |
| `enroute` | cam `(255,165,0)` | **xanh dương** `#3987e5` |
| `relocate` | vàng `(255,205,86)` | **hồng** `#d55181` |

Hôm nay vô hại vì `trajectory` **không được import ở đâu**. Nhưng một nhãn trong docstring chỉ
ngăn được người *đọc* nó — cổng này ngăn được cả người không đọc:

- `trajectory` chưa ai import ⇒ chấp nhận lệch, nhưng đòi **nhãn cảnh báo còn nguyên** trong
  docstring (nếu ai xoá nhãn mà chưa thống nhất màu thì đỏ);
- có ai import `trajectory` ⇒ hai bảng **phải khớp** cho mọi trạng thái chung, nếu không UI sẽ
  có hai cách đọc cùng một trạng thái (`CLAUDE.md` §4b: *"UI tự recompute khác engine"*).

Không tự chọn hướng giải quyết: xoá module hay hợp nhất màu là **`V-22`, quyết định của Cường**.
Cổng chỉ đảm bảo không ai nối lại module trong lúc màu còn lệch.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRAJ = ROOT / "src/gsm_sim/trajectory.py"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _importers() -> list[str]:
    """File nào import `trajectory` (trừ chính nó và các file test/manifest chỉ NHẮC TÊN)."""
    out = []
    for pat in ("src/**/*.py", "scripts/*.py", "ui/**/*.py"):
        for p in ROOT.glob(pat):
            if p == TRAJ:
                continue
            txt = p.read_text(encoding="utf-8", errors="replace")
            if re.search(r"^\s*(from\s+\S*trajectory\s+import|import\s+\S*trajectory)",
                         txt, re.M):
                out.append(p.relative_to(ROOT).as_posix())
    return out


def test_neu_trajectory_duoc_import_thi_mau_PHAI_khop():
    from gsm_sim.dashboard_theme import ACTIVITY_COLORS
    from gsm_sim.trajectory import STATE_COLORS

    importers = _importers()
    chung = set(STATE_COLORS) & set(ACTIVITY_COLORS)
    lech = []
    for k in sorted(chung):
        b = ACTIVITY_COLORS[k]
        if not (isinstance(b, str) and b.startswith("#")):
            continue                                   # `idle` trỏ SURFACE_DIM — bỏ qua
        if tuple(STATE_COLORS[k]) != _hex_to_rgb(b):
            lech.append(f"{k}: trajectory={tuple(STATE_COLORS[k])} vs theme={b}")

    if importers:
        assert not lech, (
            f"`trajectory` ĐANG được import bởi {importers} nhưng bảng màu còn lệch: {lech}. "
            f"Hai cách đọc cùng một trạng thái — hợp nhất màu trước khi nối (V-22).")
    else:
        # Trạng thái hiện nay: module chưa ai import, lệch được TẠM chấp nhận — nhưng phải có
        # nhãn, vì nhãn là thứ duy nhất cảnh báo người nối lại.
        assert lech, (
            "hai bảng màu nay đã KHỚP — cập nhật/xoá cổng này và nhãn trong trajectory.py, "
            "đừng để lại một cảnh báo không còn đúng (nhãn sai còn tệ hơn không nhãn).")


def test_nhan_canh_bao_trong_trajectory_con_nguyen():
    """Nếu ai xoá nhãn mà chưa hợp nhất màu, người nối lại sẽ không còn cảnh báo nào."""
    doc = TRAJ.read_text(encoding="utf-8")[:4000]
    for phai_co in ("KHÔNG CÓ ĐƯỜNG CHẠY", "BẢNG MÀU THỨ HAI", "D-M3-15"):
        assert phai_co in doc, (
            f"nhãn cảnh báo thiếu {phai_co!r} trong docstring `trajectory.py` — nhãn là thứ "
            f"duy nhất chặn người nối lại module trong lúc màu còn lệch (V-22)")


def test_dashboard_van_dung_dung_MOT_nguon_mau():
    """Dashboard phải lấy màu từ `dashboard_theme`, không tự định nghĩa bảng thứ ba."""
    dash = (ROOT / "src/gsm_sim/dashboard.py").read_text(encoding="utf-8")
    assert "ACTIVITY_COLORS" in dash, "dashboard không còn dùng ACTIVITY_COLORS — kiểm lại nguồn"
    assert "STATE_COLORS" not in dash, (
        "dashboard nay dùng `STATE_COLORS` của trajectory — nếu đó là ý định thì phải hợp nhất "
        "hai bảng trước (V-22), vì màu `enroute`/`relocate` đang khác nhau")
