# UPDATE-019 — T-004 official-source survey and compact handoff

- **Ngày:** 2026-07-22
- **Người thực hiện:** AI agent theo yêu cầu Khánh
- **Loại:** research handoff / repository hygiene
- **Phạm vi:** T-004; không triển khai T-011, không thay đổi T-009 hay simulator.

## Quá trình tóm tắt

1. Quét sitemap chính chủ Green SM và các trang con Driver Center; chỉ chấp nhận
   `greensm.com`/`cdn.xanhsm.com`, không dùng community, login/App hay trang báo.
2. Review lead Bike/RTO/driver-policy, loại marketing, concert, tuyển dụng và
   campaign hết hạn khỏi policy hiện hành. Từ 30 source card T1 đã audit, chọn
   bảy trang current có giá trị nhất cho policy/vận hành Bike.
3. Tách nghiêm ba track `core_owned`, `platform`, `rto`. Bike generic được giữ
   là `green_bike_unspecified`, không suy luận thành xe công ty và không auto-map
   vào F0. Nguồn không nêu Hà Nội vẫn hữu ích cho conduct/operational đúng track;
   tiền, thưởng, phí và eligibility vẫn cần scope phù hợp.
4. Crawl thử toàn văn và ảnh để đánh giá evidence/OCR. Kết quả chỉ là input
   reviewer: không có số nào trở thành policy fact, input tính tiền hay context
   agent. OCR/reviewer chỉ được mở lại bằng một task policy riêng.
5. Theo quyết định giảm footprint, xóa toàn bộ crawler/test, raw HTML/text,
   manifest, ảnh và vision transcription (~11.6 MB), plan lặp và UPDATE-010…018.
   Không biến bước chuẩn bị dữ liệu thành code/runtime debt.

## Output giữ lại

- `research/policy/T004_POLICY_SOURCE_REGISTER.md`: bảy URL official current,
  cohort, vai trò, discovery entrypoint và guardrail dùng lại sau này.
- `tracking/TODO.md` / `tracking/ASSIGNMENTS.md`: trạng thái và lịch sử ngắn.

## Handoff cho T-011 hoặc OCR/reviewer sau này

- Re-fetch trang official từ source register, ghi version/hash/effective date
  mới trước khi tạo bất kỳ evidence record nào.
- Reviewer phải xác nhận mọi ngày, tiền, tỷ lệ, ngưỡng, service và cohort từ
  text/ảnh gốc. OCR chưa review là `OCR_UNVERIFIED`.
- F0 luôn yêu cầu track chính xác; thiếu track thì hỏi lại, không trả số hoặc
  eligibility. Archive/campaign/customer promotion không vào agent context.

## Kiểm chứng

- Không còn reference tới crawler, raw corpus hoặc UPDATE-010…018 đã xóa.
- Không đụng `src/gsm_sim/`, T-009 hoặc runtime/contract.
- Thay đổi được tách trên nhánh `codex/t004-source-register` trước commit/push;
  kiểm tra merge với `origin/main` phải hoàn tất trước khi đề nghị merge.
