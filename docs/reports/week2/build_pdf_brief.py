"""Dựng PDF bản BRIEF (gửi stakeholder/mentor đọc nhanh) từ Week2-Bao-cao-Brief.md.

Chạy:  uv run python docs/reports/week2/build_pdf_brief.py

Khác `build_pdf.py` (bản kỹ thuật chi tiết) ở chỗ: lề rộng hơn, chữ to hơn, ảnh chiếm nhiều chỗ
hơn, không có khối công thức. Mục tiêu ~4 trang, đọc một lượt là hiểu.
"""
from __future__ import annotations

import pathlib
import re

import markdown

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "Week2-Bao-cao-Brief.md"
HTML = HERE / "brief.html"
PDF = HERE / "Week2-Bao-cao-Brief.pdf"

CSS = """
@page { size: A4; margin: 15mm 15mm 16mm 15mm; }
:root{ --xanh:#199e70; --duong:#3987e5; --amber:#c98500;
       --muc:#1d2b27; --muc2:#4a5a56; --vien:#dbe5e2; --nen:#f4f8f7; }
*{ box-sizing:border-box; }
body{ font-family:"Segoe UI","Calibri",sans-serif; font-size:10.6pt; line-height:1.6;
      color:var(--muc); margin:0; }
h1{ font-size:23pt; color:var(--xanh); margin:0 0 1mm; line-height:1.15;
    border-bottom:3px solid var(--xanh); padding-bottom:2.5mm; }
h1+h3{ font-size:10.4pt; color:var(--muc2); font-weight:500; margin:0 0 5mm;
       border:none; padding:0; }
h2{ font-size:14.5pt; color:var(--xanh); margin:8mm 0 2.5mm; page-break-after:avoid; }
h3{ font-size:11.5pt; color:var(--muc); margin:5mm 0 2mm; page-break-after:avoid; }
p{ margin:0 0 2.8mm; text-align:justify; }
strong{ color:#0c1512; }
em{ color:var(--muc2); }
table{ border-collapse:collapse; width:100%; margin:3mm 0 4mm; font-size:9.6pt;
       page-break-inside:avoid; }
th,td{ border:1px solid var(--vien); padding:2mm 2.4mm; text-align:left; vertical-align:top; }
th{ background:var(--nen); color:#0c1512; font-weight:600; }
/* bang 2 cot chi de xep anh -> bo vien cho thoang */
table:has(img) th, table:has(img) td{ border:none; padding:1mm 1.5mm; }
table:has(img) td{ font-size:9pt; color:var(--muc2); text-align:center; }
blockquote{ margin:3.5mm 0; padding:3mm 4.5mm; background:#fffdf3;
            border-left:3.5px solid var(--amber); font-size:9.9pt; page-break-inside:avoid; }
blockquote p{ margin:0; }
img{ max-width:100%; height:auto; display:block; margin:2mm auto 1mm;
     border:1px solid var(--vien); border-radius:4px; page-break-inside:avoid;
     /* chan anh chiem ca trang: dieu quyet dinh do dai ban brief */
     max-height:76mm; width:auto; object-fit:contain; }
/* anh dien thoai (doc) trong bang 2 cot -> cho cao hon mot chut */
table:has(img) img{ max-height:88mm; }
/* bieu do (ngang, ratio > 2) -> cho rong het khung */
p > img{ max-height:66mm; }
ul,ol{ margin:0 0 3mm; padding-left:6.5mm; }
li{ margin-bottom:1.8mm; }
hr{ border:none; border-top:1px solid var(--vien); margin:6mm 0; }
h2, h3, table, img, blockquote { break-inside:avoid; }
"""


def build_html() -> str:
    body = markdown.markdown(
        SRC.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "attr_list", "sane_lists"],
        output_format="html5")
    doc = ("<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\">"
           "<title>Week 2 Report — Driver Advisor Team</title>"
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
                               'padding:0 15mm;font-family:Segoe UI">Week 2 Report — '
                               'Driver Advisor Team</div>',
               footer_template='<div style="font-size:7pt;color:#8a9995;width:100%;'
                               'padding:0 15mm;font-family:Segoe UI;display:flex;'
                               'justify-content:space-between"><span>23/07–01/08/2026 · '
                               'số liệu MÔ PHỎNG trên dữ liệu giả lập</span>'
                               '<span>trang <span class="pageNumber"></span>/'
                               '<span class="totalPages"></span></span></div>',
               margin={"top": "18mm", "bottom": "16mm", "left": "0", "right": "0"})
        br.close()
    print(f"  PDF brief: {PDF.name} ({PDF.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build_pdf()
