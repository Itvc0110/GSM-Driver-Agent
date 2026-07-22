# UPDATE-020 — Khôi phục corpus text-only T-004

- **Ngày:** 2026-07-22
- **Người thực hiện:** AI agent theo yêu cầu của Khánh
- **Loại:** data / docs
- **TODO / User story liên quan:** T-004

## Tóm tắt

Khôi phục vào repository phần có thể đọc và kiểm chứng của T-004: full text đã
fetch cùng metadata/provenance cho bảy nguồn Green SM ưu tiên. Không đưa lại
HTML, ảnh, OCR, asset hay crawler để tránh biến research preparation thành
knowledge runtime hoặc làm phình repository.

## Chi tiết cập nhật

- Thêm corpus JSON có bảy record T1 (`greensm.com`), tổng 78.045 ký tự text.
  Mỗi record có URL, version/hash, thời điểm fetch, cohort nguồn, `f0_tracks`,
  lifecycle/status, policy family và `main_text`.
- Thêm hướng dẫn truy xuất: xác nhận track/city/service trước, lọc exact track,
  dùng `no_current_evidence` khi không có record phù hợp; generic Bike không
  auto-match bất kỳ track F0 nào.
- Source register giờ dẫn tới corpus text-only. Corpus vẫn chỉ là evidence cho
  reviewer; không có fact được duyệt, không có tính tiền/eligibility runtime.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `research/policy/t004-current-policy-text-corpus-2026-07-22.json` | tạo | 7 record text + metadata, không có asset/OCR/HTML |
| `research/policy/T004_TEXT_CORPUS_USAGE.md` | tạo | Cách đọc và guardrail |
| `research/policy/T004_POLICY_SOURCE_REGISTER.md` | sửa | Link tới corpus/hướng dẫn, giữ repository boundary |
| `tracking/TODO.md` | sửa | T-004 phản ánh bàn giao text corpus |
| `tracking/ASSIGNMENTS.md` | sửa | Lịch sử T-004 phản ánh artifact mới |
| `tracking/updates/UPDATE-020-t004-text-only-corpus.md` | tạo | Nhật ký thay đổi này |

## Docs đã cập nhật kèm theo

`TODO`, `ASSIGNMENTS` và source register đã cập nhật. `SCOPE`, `DEFERRED`,
`USER_STORIES` không đổi.

## Kiểm chứng

- Parse JSON thành công: 7/7 record có `main_text`, tổng 78.045 ký tự.
- Tất cả URL là first-party `https://www.greensm.com/`.
- Không có key `images`, `assets`, `ocr_status`, `asset_hints` hoặc
  `asset_blocklist` trong record.
- `git diff --check` không báo lỗi whitespace.

## Follow-up / defer phát sinh

T-011 hoặc task policy-review tương lai phải re-fetch khi SHA nguồn thay đổi và
chỉ reviewer mới chuyển evidence thành `PolicyFact` dùng cho F0. Không có task
mới được tạo trong đợt data handoff này.
