"""Dựng KNOWLEDGE GRAPH của toàn bộ tài liệu markdown trong repo — theo cách graphify.

Vì sao tồn tại: 97 file UPDATE + ~40 file tracking/specs tham chiếu nhau bằng ID
(`D-M3-01`, `V-17`, `UPDATE-102`, `T-047`, ...) và bằng link tương đối. Không ai giữ
được đồ thị đó trong đầu ⇒ tài liệu mồ côi, link gãy, và trạng thái xung đột (một ID
đóng ở file này nhưng vẫn "cần làm" ở file kia) sống sót qua nhiều cycle — đúng họ lỗi
"cơ chế bảo vệ chỉ sống trên giấy" (D-M3-08/D-M3-10, lần này áp cho chính tracking).

Cách graphify (https://github.com/Graphify-Labs/graphify) làm: parse deterministic
(tree-sitter AST cho code), KHÔNG cần LLM, chạy local, output graph queryable + report.
Script này làm đúng tinh thần đó cho tầng TÀI LIỆU: regex có chủ đích trên markdown
(việc cài bản PyPI `graphifyy` bị chặn bởi policy môi trường — xem UPDATE-106).

    uv run python scripts/build_doc_graph.py            # ghi graph-out/doc-graph.json + report
    uv run python scripts/build_doc_graph.py --quiet    # chỉ in tóm tắt

Output:
    graph-out/doc-graph.json     — node (file, id) + edge (file→id mention, file→file link)
    graph-out/DOC-GRAPH-REPORT.md — link gãy · file mồ côi · ID xung đột trạng thái · hub

Mọi kết luận của report là MECHANICAL — nó chỉ ra CHỖ ĐÁNG NGỜ; phán quyết
đóng/mở/sửa vẫn phải do người đọc file thật quyết định.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "graph-out"

# Thư mục chứa tài liệu "sống". docs/00-09 pack cũ là DEFERRED (CLAUDE.md §2) — vẫn quét
# để bắt link gãy trỏ vào chúng, nhưng KHÔNG tính chúng là mồ côi (chúng cố ý bị treo).
SCAN_DIRS = ["tracking", "specs", "planning", "research", "docs", "schemas", "ui/contracts"]
ROOT_FILES = ["CLAUDE.md", "AGENTS.md", "MASTER_PROMPT.md", "README.md"]
DEFERRED_PREFIXES = ("docs/00", "docs/01", "docs/02", "docs/03", "docs/04", "docs/05",
                     "docs/06", "docs/07", "docs/08", "docs/09", "contracts/", "templates/")

# Họ ID của repo — mỗi mẫu bắt ĐÚNG quy ước đã dùng, không đoán.
ID_PATTERNS = {
    "UPDATE": re.compile(r"\bUPDATE-(\d{3})\b"),
    "D": re.compile(r"\bD-(?:M3|R|SIM|POL|A3|F098|GCP|ĐA0?4|DA04|\d{3}[a-z]?)[-\w]*\b"),
    "V": re.compile(r"\bV-\d{2}\b"),
    "T": re.compile(r"\bT-0\d{2}\b"),
    "Q": re.compile(r"\bQ-\d{2}\b"),
    "E": re.compile(r"\bE\d{1,2}[ab]?\b(?=[^\w-]|$)"),
    "L": re.compile(r"\bL\d-\d{2}\b"),
    "DA": re.compile(r"\bĐA-\d{2}\b"),
}
# E<number> va chạm với từ thường ("E5" ok, nhưng "E" trong code block thì không) —
# chỉ nhận khi có ngữ cảnh backtick hoặc **bold** quanh nó, hoặc đúng dạng E\d+[ab].
E_CONTEXT = re.compile(r"[`*]E\d{1,2}[ab]?[`*]|\bE\d{1,2}[ab]?\b(?=\s*[—:–-])")

MD_LINK = re.compile(r"\[([^\]]*)\]\(([^)#\s]+)(?:#[^)]*)?\)")

# Trạng thái ĐÓNG trong file canonical: dòng bảng bắt đầu bằng `| ~~ID~~ ✅` hoặc chứa các marker.
CLOSED_MARKERS = ("✅", "HUỶ", "ĐÓNG", "DONE-CODE", "ĐÃ CHỐT", "ĐÃ CHECK XONG", "CORRECTED")
OPEN_HINT = re.compile(r"(cần làm|chưa làm|CHƯA|TODO|sev (CAO|TB)|đang chờ|phải làm|chờ thi công)",
                       re.IGNORECASE)

# File canonical cho từng họ ID — trạng thái ở đây THẮNG mọi chỗ khác.
CANONICAL = {
    "D": "tracking/DEFERRED.md",
    "V": "tracking/PENDING-REVIEW.md",
    "T": "tracking/TODO.md",
}


def _rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def collect_files() -> list[Path]:
    files: list[Path] = []
    for name in ROOT_FILES:
        p = ROOT / name
        if p.exists():
            files.append(p)
    for d in SCAN_DIRS:
        base = ROOT / d
        if base.exists():
            files.extend(sorted(base.rglob("*.md")))
    return files


def canonical_status(fam: str, text: str) -> dict[str, str]:
    """Trạng thái từng ID trong file canonical của họ nó: CLOSED nếu dòng bảng của ID
    mang marker đóng, OPEN nếu không. Chỉ nhìn DÒNG chứa ID ở cột đầu bảng."""
    out: dict[str, str] = {}
    pat = ID_PATTERNS[fam]
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        first_cell = line.split("|")[1] if line.count("|") >= 2 else ""
        ids = set(pat.findall(line if fam == "UPDATE" else first_cell)) or set()
        # findall của UPDATE trả group số; dựng lại tên đầy đủ
        if fam == "UPDATE":
            ids = {f"UPDATE-{g}" for g in ids}
        else:
            ids = set(m.group(0) for m in pat.finditer(first_cell))
        for i in ids:
            closed = any(mk in line for mk in CLOSED_MARKERS) or f"~~{i}~~" in line
            # đừng hạ cấp: một ID có thể xuất hiện nhiều dòng; CLOSED thắng
            if out.get(i) != "CLOSED":
                out[i] = "CLOSED" if closed else "OPEN"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    files = collect_files()
    texts = {_rel(p): p.read_text(encoding="utf-8", errors="replace") for p in files}
    # Link chỉ parse NGOÀI code — cả fenced block LẪN inline span. Hai false positive thật:
    # lần 1: `[x](y)` trong snippet Python của UPDATE-098 (fenced); lần 2: chính câu văn mô
    # tả false positive đó trong UPDATE-106 (inline `[x](y)`) bị parse thành link — công cụ
    # đo tự tạo ra đúng lỗi nó đi tìm, hai lần.
    FENCE = re.compile(r"```.*?```", re.DOTALL)
    INLINE = re.compile(r"`[^`\n]*`")
    link_texts = {rel: INLINE.sub("", FENCE.sub("", t)) for rel, t in texts.items()}

    mentions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))  # id -> file -> n
    links: list[tuple[str, str, bool]] = []  # (src, dst, exists)
    inbound: dict[str, int] = defaultdict(int)

    for rel, text in texts.items():
        # 1. ID mentions
        for fam, pat in ID_PATTERNS.items():
            if fam == "E":
                for m in E_CONTEXT.finditer(text):
                    tok = re.search(r"E\d{1,2}[ab]?", m.group(0)).group(0)
                    mentions[tok][rel] += 1
                continue
            for m in pat.finditer(text):
                tok = f"UPDATE-{m.group(1)}" if fam == "UPDATE" else m.group(0)
                mentions[tok][rel] += 1
        # 2. File links (bỏ code block)
        base = (ROOT / rel).parent
        for m in MD_LINK.finditer(link_texts[rel]):
            target = m.group(2)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (base / target).resolve()
            try:
                dst = resolved.relative_to(ROOT).as_posix()
            except ValueError:
                dst = target
            exists = resolved.exists()
            links.append((rel, dst, exists))
            if exists:
                inbound[dst] += 1

    # 3. Trạng thái canonical + xung đột
    status: dict[str, str] = {}
    for fam, canon in CANONICAL.items():
        if canon in texts:
            status.update(canonical_status(fam, texts[canon]))

    conflicts: list[dict] = []
    for tok, st in sorted(status.items()):
        if st != "CLOSED":
            continue
        for rel, n in mentions.get(tok, {}).items():
            if rel in CANONICAL.values() or rel.startswith("tracking/updates/"):
                continue  # updates là nhật ký lịch sử — được phép nhắc ID đã đóng
            text = texts[rel]
            for line in text.splitlines():
                if tok in line and OPEN_HINT.search(line) and "~~" not in line \
                        and "✅" not in line and "ĐÃ" not in line:
                    conflicts.append({"id": tok, "file": rel, "line": line.strip()[:160]})
                    break

    # 4. Mồ côi: file tracking/specs KHÔNG có inbound link và KHÔNG được nhắc tên
    orphans: list[str] = []
    for rel in texts:
        if not rel.startswith(("tracking/", "specs/")) or rel.startswith("tracking/updates/"):
            continue
        name = Path(rel).name
        if inbound.get(rel, 0) > 0:
            continue
        mentioned = any(name in t for r2, t in texts.items() if r2 != rel)
        if not mentioned:
            orphans.append(rel)

    broken = [(s, d) for s, d, ok in links if not ok]

    OUT.mkdir(exist_ok=True)
    graph = {
        "generated": "scripts/build_doc_graph.py",
        "n_files": len(texts),
        "n_ids": len(mentions),
        "nodes": {
            "files": sorted(texts),
            "ids": {tok: {"status": status.get(tok, "UNTRACKED"),
                          "mentions": dict(sorted(m.items()))}
                    for tok, m in sorted(mentions.items())},
        },
        "edges": {
            "links": [{"src": s, "dst": d, "exists": ok} for s, d, ok in links],
        },
    }
    (OUT / "doc-graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=1),
                                        encoding="utf-8")

    hubs = sorted(((sum(m.values()), tok) for tok, m in mentions.items()), reverse=True)[:15]
    rep = ["# DOC GRAPH REPORT — sinh bởi `scripts/build_doc_graph.py`", "",
           f"{len(texts)} file · {len(mentions)} ID · {len(links)} link "
           f"({len(broken)} GÃY) · {len(conflicts)} xung đột trạng thái · "
           f"{len(orphans)} file nghi mồ côi", "",
           "⚠ Report là MECHANICAL — nó chỉ ra chỗ đáng ngờ; phán quyết phải đọc file thật.", ""]
    rep.append("## 🔴 Link GÃY (đích không tồn tại)\n")
    for s, d in sorted(set(broken)):
        rep.append(f"- `{s}` → `{d}`")
    rep.append("\n## 🔴 Xung đột trạng thái (ID đã ĐÓNG ở canonical nhưng nơi khác nói 'cần làm')\n")
    for c in conflicts:
        rep.append(f"- **{c['id']}** trong `{c['file']}`: {c['line']}")
    rep.append("\n## File nghi MỒ CÔI (không inbound link, không được nhắc tên)\n")
    for o in sorted(orphans):
        rep.append(f"- `{o}`")
    rep.append("\n## Hub — ID được nhắc nhiều nhất\n")
    for n, tok in hubs:
        rep.append(f"- **{tok}** ({status.get(tok, 'UNTRACKED')}): {n} lần")
    (OUT / "DOC-GRAPH-REPORT.md").write_text("\n".join(rep) + "\n", encoding="utf-8")

    print(f"{len(texts)} file · {len(mentions)} ID · {len(broken)} link gãy · "
          f"{len(conflicts)} xung đột · {len(orphans)} nghi mồ côi")
    if not args.quiet:
        print(f"→ {OUT / 'DOC-GRAPH-REPORT.md'}")


if __name__ == "__main__":
    main()
