"""Dựng PDF cuối từ Week2-Report-Driver-Advisor-Team.md.

Chạy:  uv run python docs/reports/week2/build_pdf.py

Đường đi: Markdown → HTML (+CSS in ấn A4) → Chromium (playwright) → PDF.
Không cần LaTeX, không cần pandoc.

Hai chi tiết đã trả giá để tìm ra, đừng bỏ:
1. `λ̂` viết bằng ký tự Unicode thường bị **lệch dấu mũ** khi Chromium render → thay bằng
   **MathML** (`<math><mover>`) mới đúng. Hàm `_mathify()` làm việc đó.
2. `page.pdf()` cần `emulate_media("print")` để `@media print` có hiệu lực; và `print_background`
   phải bật, nếu không mọi ô màu/nền bảng biến mất.
"""
from __future__ import annotations

import pathlib
import re

import markdown

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "Week2-Report-Driver-Advisor-Team.md"
HTML = HERE / "report.html"
PDF = HERE / "Week2-Bao-cao-ky-thuat-chi-tiet.pdf"

CSS = """
@page { size: A4; margin: 17mm 16mm 18mm 16mm; }
:root{ --xanh:#199e70; --duong:#3987e5; --amber:#c98500; --do:#b03030;
       --muc:#1d2b27; --muc2:#4a5a56; --vien:#d8e2df; --nen:#f4f8f7; }
*{ box-sizing:border-box; }
body{ font-family:"Segoe UI","Calibri",sans-serif; font-size:10.2pt; line-height:1.55;
      color:var(--muc); margin:0; }
h1{ font-size:21pt; color:var(--xanh); margin:0 0 2mm; line-height:1.2;
    border-bottom:3px solid var(--xanh); padding-bottom:3mm; }
h2{ font-size:14pt; color:var(--muc); margin:9mm 0 3mm; padding-bottom:1.5mm;
    border-bottom:1.5px solid var(--vien); page-break-after:avoid; }
h3{ font-size:11.4pt; color:var(--xanh); margin:6mm 0 2mm; page-break-after:avoid; }
h1+p,h2+p,h3+p{ margin-top:0; }
p{ margin:0 0 2.6mm; text-align:justify; }
strong{ color:#0f1a17; }
code{ font-family:"Consolas","Courier New",monospace; font-size:8.8pt;
      background:var(--nen); border:1px solid var(--vien); border-radius:2px; padding:0 1.2mm; }
pre{ background:var(--nen); border:1px solid var(--vien); border-left:3px solid var(--xanh);
     border-radius:3px; padding:3mm 4mm; font-size:8.4pt; line-height:1.45; overflow:hidden;
     page-break-inside:avoid; }
pre code{ background:none; border:none; padding:0; font-size:8.4pt; }
table{ border-collapse:collapse; width:100%; margin:3mm 0 4mm; font-size:8.9pt;
       page-break-inside:avoid; }
th,td{ border:1px solid var(--vien); padding:1.7mm 2.2mm; text-align:left;
       vertical-align:top; }
th{ background:var(--nen); color:#0f1a17; font-weight:600; }
tr:nth-child(even) td{ background:#fbfdfc; }
blockquote{ margin:3mm 0; padding:2.5mm 4mm; background:#fffdf3;
            border-left:3px solid var(--amber); font-size:9.4pt; page-break-inside:avoid; }
blockquote p{ margin:0 0 1.5mm; }
blockquote p:last-child{ margin:0; }
img{ max-width:100%; height:auto; display:block; margin:3mm auto 1.5mm;
     border:1px solid var(--vien); border-radius:3px; page-break-inside:avoid; }
ul,ol{ margin:0 0 3mm; padding-left:6mm; }
li{ margin-bottom:1.4mm; }
hr{ border:none; border-top:1px solid var(--vien); margin:7mm 0; }
.formula{ font-family:"Cambria Math","Times New Roman",serif; font-size:12pt; text-align:center;
          background:var(--nen); border:1px solid var(--vien); border-radius:3px;
          padding:3mm; margin:3mm 0; page-break-inside:avoid; }
math{ font-family:"Cambria Math","Times New Roman",serif; }
h2, h3, table, img, pre, blockquote { break-inside:avoid; }
@media print { a{ color:var(--duong); text-decoration:none; } }
"""


def _mathify(html: str) -> str:
    """λ̂ (lambda + combining circumflex) → MathML; Chromium render ký tự thường bị lệch dấu."""
    mm = "<math><mover><mi>λ</mi><mo>̂</mo></mover></math>"
    return html.replace("λ̂", mm).replace("λ̂", mm)


def build_html() -> str:
    md = SRC.read_text(encoding="utf-8")
    body = markdown.markdown(
        md, extensions=["tables", "fenced_code", "attr_list", "sane_lists", "md_in_html"],
        output_format="html5")
    body = _mathify(body)
    # markdown gói <div class="formula"> thành <p> — bỏ lớp p bọc ngoài để CSS ăn đúng
    body = re.sub(r"<p>(<div class=\"formula\">.*?</div>)</p>", r"\1", body, flags=re.S)
    doc = ("<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
           "<title>Week 2 — Báo cáo kỹ thuật chi tiết</title>"
           f"<style>{CSS}</style></head><body>{body}</body></html>")
    HTML.write_text(doc, encoding="utf-8")
    return doc


def build_pdf() -> None:
    from playwright.sync_api import sync_playwright
    build_html()
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page()
        pg.goto(HTML.as_uri(), wait_until="networkidle", timeout=90_000)
        pg.emulate_media(media="print")
        pg.wait_for_timeout(1200)
        pg.pdf(path=str(PDF), format="A4", print_background=True,
               display_header_footer=True,
               header_template='<div style="font-size:7pt;color:#8a9995;width:100%;'
                               'padding:0 16mm;font-family:Segoe UI">'
                               'Week 2 — Báo cáo kỹ thuật chi tiết · Trần Quốc Khánh · '
                               'Lưu Thiện Việt Cường</div>',
               footer_template='<div style="font-size:7pt;color:#8a9995;width:100%;'
                               'padding:0 16mm;font-family:Segoe UI;display:flex;'
                               'justify-content:space-between"><span>23/07–01/08/2026 · '
                               'số liệu MÔ PHỎNG trên dữ liệu MOCK</span>'
                               '<span>trang <span class="pageNumber"></span>/'
                               '<span class="totalPages"></span></span></div>',
               margin={"top": "20mm", "bottom": "18mm", "left": "0", "right": "0"})
        br.close()
    print(f"  PDF: {PDF.name} ({PDF.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build_pdf()
