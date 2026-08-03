# Hướng dẫn: sửa nội dung rồi in lại PDF

## HAI bản PDF — dùng cho hai mục đích khác nhau

| Bản | File | Độ dài | Gửi cho ai |
| --- | --- | --- | --- |
| **Brief** | `Week2-Bao-cao-Brief.pdf` | **6 trang** | Mentor / stakeholder đọc một lượt. Không có tên biến, không ký hiệu toán, nhiều hình |
| **Kỹ thuật chi tiết** | `Week2-Bao-cao-ky-thuat-chi-tiet.pdf` | **30 trang** | Người muốn kiểm phương pháp: thiết kế mô phỏng, luồng dữ liệu theo từng trường, guardrails, nguồn từng con số |

Bản brief **không phải bản rút gọn tự động** — nó viết lại bằng ngôn ngữ thường ngày và dùng **bộ
biểu đồ riêng** (`fig-brief-*.png`) có nhãn tiếng Việt thay cho tên arm/ký hiệu.

## Kiến trúc: mỗi bản một nguồn

```
Week2-Bao-cao-Brief.md                  ← SỬA Ở ĐÂY cho bản brief
        │  build_pdf_brief.py  →  brief.html  →  Week2-Bao-cao-Brief.pdf

Week2-Report-Driver-Advisor-Team.md     ← SỬA Ở ĐÂY cho bản chi tiết
        │  build_pdf.py        →  report.html →  Week2-Bao-cao-ky-thuat-chi-tiet.pdf
```

File `.html` là dẫn xuất — **đừng sửa tay**.

Sửa `.md` rồi chạy:

```bash
uv run python docs/reports/week2/build_pdf_brief.py   # bản brief
uv run python docs/reports/week2/build_pdf.py         # bản chi tiết
```

Nếu đổi số trong biểu đồ, chạy thêm (sinh **cả 7** hình: 4 bản kỹ thuật + 3 bản brief):

```bash
uv run python docs/reports/week2/make_figures.py
```

⚠ Ảnh screenshot trong `assets/` **đã được crop** bỏ viền nền (script crop nằm trong UPDATE-119).
Nếu chụp lại UI thì phải crop lại, không thì bản brief sẽ phồng từ 6 lên ~9 trang.

## Phụ thuộc (đã cài trong `.venv` của repo)

`markdown` · `playwright` + chromium (`uv run playwright install chromium`) · `matplotlib` ·
`pypdf` (để tự kiểm) · `pymupdf` (render trang ra ảnh để xem).

## Hai cái bẫy đã trả giá để tìm ra — đừng bỏ

1. **`λ̂` viết bằng ký tự Unicode thường bị lệch dấu mũ** khi Chromium render. `build_pdf.py` có
   hàm `_mathify()` tự đổi sang MathML. Nếu bạn thêm công thức mới có dấu mũ, dùng MathML hoặc
   thêm vào `_mathify()`.
   Trong biểu đồ matplotlib thì dùng mathtext: `r"$\hat\lambda$"`.
2. **`print_background=True` là bắt buộc** — thiếu nó thì mọi nền bảng, ô màu, khung code biến mất
   khỏi PDF (nhìn vẫn "có chữ" nên rất dễ không phát hiện).

## Cách tự kiểm PDF sau khi in (nên làm mỗi lần)

Đừng tin "file đã tạo" là xong. Ba bước:

```bash
# (1) đếm trang + trích text kiểm dấu tiếng Việt
uv run python -c "
from pypdf import PdfReader
r = PdfReader('docs/reports/week2/Week2-Bao-cao-ky-thuat-chi-tiet.pdf')
t = '\n'.join(p.extract_text() or '' for p in r.pages)
print('trang:', len(r.pages), '| ky tu:', len(t))
for w in ['Tài xế','KQ-GIỮ','điểm phần trăm','Poisson-binomial']:
    print(('OK ' if w in t else 'MAT'), w)"

# (2) kiem so BI CAM khong xuat hien tran lan
uv run python -c "
from pypdf import PdfReader
r = PdfReader('docs/reports/week2/Week2-Bao-cao-ky-thuat-chi-tiet.pdf')
t = '\n'.join(p.extract_text() or '' for p in r.pages)
for bad in ['6.016','809','865']:
    print(bad, '->', t.count(bad), 'lan')"

# (3) render trang ra anh de XEM THAT (layout, anh, bang)
uv run python -c "
import fitz
d = fitz.open('docs/reports/week2/Week2-Bao-cao-ky-thuat-chi-tiet.pdf')
for i in (0, 11, 16):
    d[i].get_pixmap(dpi=110).save(f'page_{i:02d}.png')
print('da render')"
```

**Về bước (2):** `6.016` được phép xuất hiện **chỉ khi** kèm ngữ cảnh *"không tái lập được / số
cũ"* — xem `AUDIT-CHECKLIST-cho-Khanh.md` §1.1. `809` và `865` **phải là 0 lần** (số test cũ đã
stale).

## Nếu muốn đổi cách trình bày

CSS của bản chi tiết nằm trong biến `CSS` của `build_pdf.py`; bản brief ở `build_pdf_brief.py` (có thêm `max-height` cho ảnh — chính chỗ quyết định số trang). Vài chỗ hay cần sửa:

| Muốn gì | Sửa ở đâu |
| --- | --- |
| Lề trang | `@page { margin: ... }` và tham số `margin=` của `pg.pdf()` |
| Cỡ chữ thân bài | `body { font-size: 10.2pt }` |
| Cỡ chữ bảng (bảng nhiều cột đang 8,9pt) | `table { font-size: ... }` |
| Header/footer | `header_template` / `footer_template` trong `build_pdf.py` |
| Màu chủ đề | biến `--xanh` (đang khớp màu brand `#199e70`) |

## Ảnh

Trong `assets/`. Nguồn:

- `ui-driver-app-*.png`, `ui-track-mo-phong.png` — **do Khánh cung cấp**
- `ui-track-0*.png`, `dashboard-*.png` — chụp tự động bằng Playwright 01/08/2026
- `fig-*.png` — sinh bằng `make_figures.py`, **đọc số từ artifact JSON** (sửa số trong artifact thì
  chạy lại script, đừng sửa ảnh)

Muốn chụp lại UI: mở backend rồi chạy lại đoạn Playwright (xem `UPDATE-119`).

```bash
cd ui/backend && uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8077
```

## Xuất bản cho mentor

Cả hai PDF đã self-contained (ảnh nhúng sẵn). Gửi mentor **`Week2-Bao-cao-Brief.pdf`** trước — đọc
một lượt là hiểu; kèm **`Week2-Bao-cao-ky-thuat-chi-tiet.pdf`** cho ai muốn kiểm phương pháp. Nếu
mentor hỏi nguồn của một con số cụ thể thì gửi thêm `NGUON-SO-LIEU.md`.
