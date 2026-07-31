"""Scanner ranh giới sức khoẻ (D-M3-08 cơ chế 2) — KHÔNG phải test module (không có test_*).

Chứng minh bằng máy: `fatigue` không xuất hiện trên ĐƯỜNG TỚI TIỀN
(spec advisor-objective-model-v2 §1.2b — "MỆT là LATENT, không ai đọc để tính tiền").

Kiến trúc HAI LỚP (một lớp thì lách được bằng cách viết hàm mới):
1. Quét token CẤM trong các scope đã phân loại MONEY (AST — comment/docstring vô hình,
   nên comment ĐÚNG như `shift_dp.py:36,40` "không phạt fatigue ảo" không bị bắn oan);
2. Cổng toàn vẹn manifest: mọi scope CHẠM token tiền phải được PHÂN LOẠI (hàm mới chạm
   `payout/vnd/...` mà chưa khai ⇒ đỏ ngay — chặn đường lách "viết hàm mới").

Lớp phân loại (manifest ở `tests/_health_boundary_manifest.py`):
- MONEY   — tính/ghi/hiển thị số tiền. Token cấm trong đây ⇒ vi phạm.
- VETO    — được ĐỌC trạng thái mệt để CHẶN lời khuyên (lan can) — khai tường minh.
- NOT_MONEY — chạm chữ tiền nhưng không tính tiền.
- WORLD_PHYSIOLOGY — dành cho Phase B (world mô hình mệt CÓ KIỂM SOÁT). HÔM NAY RỖNG;
  khi E11 mở, cơ chế mệt→tốc-độ của world khai vào đây; advisor/solver đọc F vẫn ĐỎ.

KHÔNG có escape hatch (# noqa) — muốn ngoại lệ phải sửa manifest, có diff review được.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("src/gsm_sim", "src/gsm_core", "ui/backend/app")
MONEY_MARKERS = ("vnd", "payout", "gross", "fare", "revenue", "income", "topup")
FORBIDDEN = ("fatigue",)          # hẹp CÓ CHỦ Ý: rest_*/online_min hợp lệ ở đường ràng buộc


def _iter_files():
    for pkg in PACKAGES:
        yield from sorted((ROOT / pkg).rglob("*.py"))


def _scope_tokens(src: str) -> dict[str, list[tuple[int, str]]]:
    """{qualname: [(lineno, token), ...]} — token = Name/Attribute/arg/keyword/str-const.
    Docstring bị loại; token ngoài mọi hàm rơi vào scope '<toplevel>' (chặn tiêm cấp module)."""
    tree = ast.parse(src)
    doc_ids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                doc_ids.add(id(b[0].value))

    def tok(n):
        if isinstance(n, ast.Name):
            return n.id
        if isinstance(n, ast.Attribute):
            return n.attr
        if isinstance(n, ast.arg):
            return n.arg
        if isinstance(n, ast.keyword) and n.arg:
            return n.arg
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_ids:
            return n.value
        return None

    out: dict[str, list[tuple[int, str]]] = {}

    def collect(stmt, qual):
        for n in [stmt, *ast.walk(stmt)]:
            t = tok(n)
            if t is not None:
                out.setdefault(qual, []).append((getattr(n, "lineno", 0), t))

    def walk(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # chữ ký (args/decorators) thuộc scope CỦA CHÍNH NÓ — tiêm tham số
                # `fatigue: float = 0.0` vào def phải bị bắt (mũi tiêm #4)
                qual = ".".join(stack + [child.name])
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for a in ast.walk(child.args):
                        t = tok(a)
                        if t is not None:
                            out.setdefault(qual, []).append((child.lineno, t))
                walk(child, stack + [child.name])
            else:
                collect(child, ".".join(stack) if stack else "<toplevel>")

    walk(tree, [])
    return out


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def discover(source_override: dict[str, str] | None = None
             ) -> dict[tuple[str, str], list[tuple[int, str]]]:
    """Mọi scope CHẠM token tiền: {(relpath, qualname): [(lineno, token_cấm_thường_hoá)]}.

    `source_override`: {relpath: source} — test tiêm mutation TRONG BỘ NHỚ, không ghi đĩa."""
    hits: dict[tuple[str, str], list] = {}
    for f in _iter_files():
        rel = _rel(f)
        src = (source_override or {}).get(rel) or f.read_text(encoding="utf-8")
        for qual, toks in _scope_tokens(src).items():
            low = [(ln, t.lower()) for ln, t in toks]
            if not any(m in t for _, t in low for m in MONEY_MARKERS):
                continue
            hits[(rel, qual)] = [(ln, t) for ln, t in low
                                 if any(fb in t for fb in FORBIDDEN)]
    return hits


def scan_tree(source_override: dict[str, str] | None = None) -> list[str]:
    """Vi phạm = token cấm trong scope MONEY (hoặc scope CHƯA PHÂN LOẠI — mặc định nghiêm).
    Trả list câu mô tả; rỗng = sạch."""
    from _health_boundary_manifest import MANIFEST
    out = []
    for (rel, qual), bad in discover(source_override).items():
        if MANIFEST.get((rel, qual)) in ("VETO", "NOT_MONEY", "WORLD_PHYSIOLOGY"):
            continue
        for ln, t in bad:
            out.append(f"{rel}:{ln} [{qual}] token cấm {t!r} trong scope "
                       f"{MANIFEST.get((rel, qual), 'CHƯA PHÂN LOẠI')}")
    return sorted(out)


def integrity(source_override: dict[str, str] | None = None) -> tuple[list, list]:
    """(unclassified, dead) — cả hai phải RỖNG. Lớp 2 chống lách + chống manifest mục."""
    from _health_boundary_manifest import MANIFEST
    found = set(discover(source_override).keys())
    unclassified = sorted(k for k in found if k not in MANIFEST)
    dead = sorted(k for k in MANIFEST if k not in found)
    return unclassified, dead
