# UPDATE-042 — PI-5c: S8 PenaltyExplain (UC6) + S9 AnomalyAlert (UC7) — 2 tính năng nhạy cảm nhất

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (Cường duyệt plan PI-5c)
- **Loại:** feature
- **TODO / User story liên quan:** Real-data PI-5c; UC6, UC7; US-F3; §5 guardrail

## Tóm tắt

Hoàn tất **UC1–UC8**: thêm **S8 PenaltyExplain** (giải thích khoản trừ + cách TUÂN THỦ) và **S9 AnomalyAlert** (báo dấu hiệu bất thường **KHÔNG kết tội**). Đây là 2 tính năng dễ gây hại nhất (dạy lách / vu oan) nên **guardrail là phần thiết kế chính**, có test chặn từ khoá. Suite **334 pass**. Phát hiện + fix **1 bug định tuyến do đồng âm tiếng Việt**.

## Guardrail — thiết kế & test

| Rủi ro | Cách chặn (có test) |
|---|---|
| **Dạy lách phạt** (UC6) | Chỉ nêu QUY TẮC + hành động TUÂN THỦ ("nâng tỷ lệ nhận lên 85%"), không mẹo né. Test chặn từ khoá: lách/né phạt/tránh bị phát hiện/qua mặt/đối phó |
| **Kết tội oan** (UC7) | Chỉ "hệ thống **ghi nhận dấu hiệu**"; mô tả HIỆN TƯỢNG không quy kết; bắt buộc `NOT_CONCLUSION` + confidence + khuyến nghị liên hệ hỗ trợ. Test chặn: "gian lận", "đã vi phạm", "đã trục lợi" |
| **Lộ cách phát hiện** | `evidence_ref` KHÔNG mang sang view/message; không nêu ngưỡng phát hiện |
| **Cằn nhằn chuyện đã xong** | Cờ `cleared/confirmed` → im lặng; không cờ mở → im lặng |
| **Bịa vấn đề** | Không khoản trừ + chỉ số đạt → digest trung tính, `notable=False` |
| **Phán xét** | Giọng nêu sự kiện + khoảng cách tới ngưỡng (research: tài xế đã thấy "bị phạt như nhân viên") |

**Quyết định sản phẩm:** UC7 **chỉ hiện ở F3 (sau ca)**, KHÔNG bắn giữa ca (F2) để tránh gây hoang mang khi đang chạy — có test khẳng định `anomaly_alert ∉ F2`.

## Mẫu output THẬT (verify=True)

> **S8:** "kỳ này ghi nhận 1 khoản trừ, tổng **100.000đ** (trừ theo bộ quy tắc ứng xử); tỷ lệ nhận chuyến **80%** đang dưới mức tối thiểu **85%** theo chính sách. Cách cải thiện: tuân thủ bộ quy tắc ứng xử, nâng tỷ lệ nhận chuyến lên mức tối thiểu 85%."
>
> **S9:** "hệ thống ghi nhận 1 dấu hiệu cần xem lại — tỷ lệ/kiểu hủy chuyến khác thường (nên kiểm tra, **độ tin cậy 58%**). Đây là DẤU HIỆU do hệ thống tự động ghi nhận (có thể chưa chính xác), **KHÔNG phải kết luận vi phạm**. Anh/chị kiểm tra lại… liên hệ bộ phận hỗ trợ."

## Adversarial self-review / flaws found

1. **BUG-PI5c-01 — định tuyến sai do ĐỒNG ÂM tiếng Việt**: `"bất thường"` bỏ dấu → `"bat thuong"` **chứa** `"thuong"` (= `"thưởng"`/bonus) ⇒ câu hỏi cảnh báo bị route sang `policy_bonus`. Router lấy intent **đầu tiên** khớp bất kỳ keyword nào.
   - **Fix**: **keyword DÀI NHẤT thắng** (cụm cụ thể > từ đơn) — nguyên tắc chung, không vá riêng ca này. Regression test 4 câu (bao gồm "thưởng" THẬT vẫn về `policy_bonus`).
   - Cùng họ với BUG-C6-01 (đ/Đ) — bỏ dấu tiếng Việt là nguồn lỗi tinh vi, cần cẩn trọng lâu dài.
2. **Định dạng tiền không nhất quán**: digest solver dùng `f"{x:,}"` → `"100,000đ"` trong khi message hiển thị `"100.000đ"`. Cùng số, 2 định dạng — nguy cơ LLM copy sai format. **Fix**: tách `gsm_core/vn_format.py` làm MỘT nguồn định dạng, solver + advisor dùng chung (`context_pack` re-export để không phá import cũ).
3. **`notable=False` vẫn trả report** (không rỗng) → composer/template tự quyết im lặng; đúng thiết kế (solver báo cáo sự thật, tầng trình bày quyết định nói hay không).
4. **Chưa kiểm**: câu chữ với LLM live (mới template); từ khoá chặn là danh sách hữu hạn — LLM live có thể diễn đạt khác ⇒ khi bật live phải thêm verifier rule cho UC7 (ghi follow-up).
5. **Ngưỡng `CLIFF_MARGIN=0.03`** (sát ngưỡng) là ASSUMPTION.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| `schemas/l3/{penalty_explain_input,anomaly_alert_input}.schema.json` | tạo |
| `schemas/advisor/solver_report.schema.json` (enum +2), `schemas/CHANGELOG.md`, `schema_registry.py`, `tests/test_schemas.py` | sửa |
| `src/gsm_core/solvers/{penalty_explain,anomaly_alert}.py` | tạo |
| `src/gsm_core/features/from_l1r.py` | sửa (+2 derivation) |
| `src/gsm_core/vn_format.py` | **tạo** (1 nguồn định dạng VN) |
| `src/gsm_core/advisor/{router,context_pack,templates}.py` | sửa (wiring F3 + fix router longest-match) |
| `tests/test_penalty_anomaly.py` | tạo (21 test, phần lớn là guardrail) |

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Guardrail chặn được dạy lách/kết tội (template) | `OBSERVED-CODE` | test chặn từ khoá + đọc output | Cao (template) / TB (live) | rủi ro đạo đức nếu live diễn đạt khác |
| Cột `driver_penalization_ATA`/`public_frauds` | `TBC-với-GSM` (ENGINEER) | ta tự thiết kế | TB | phải map lại khi GSM cấp cột thật |
| Router longest-match đúng cho tiếng Việt | `OBSERVED-CODE` | 4 case regression | TB | đồng âm khác có thể còn |
| UC7 chỉ F3 (không bắn giữa ca) | `ASSUMPTION` (sản phẩm) | tránh hoang mang khi đang chạy | TB | có thể muốn cảnh báo sớm hơn |

## Kiểm chứng
`tests/test_penalty_anomaly.py` **21 pass**; full suite **334 pass**. Chạy thật trên `generate_realdata` → 2 view + 2 report hợp schema; e2e F3 verify pass, message không chứa từ kết tội/dạy lách. **CHƯA kiểm chứng:** LLM live; cột thật 2 bảng ENGINEER.

## Visual verification
- **Status:** `NOT_APPLICABLE` (chưa UI) — sample text ở mục "Mẫu output THẬT".

## Expansion checkpoint (T-039)
1. **Schema:** 2 view mới; 2 bảng nguồn vẫn ENGINEER → cần cột thật (D-POL-05).
2. **Bài toán tối ưu:** **UC1–UC8 đã phủ hết** bằng 9 solver. Ứng viên tiếp: đo hiệu quả campaign reposition; eval chất lượng advice (C7).
3. **Tính năng:** UC7 khi có kênh push → cân nhắc cảnh báo sớm (event_trigger) với ngưỡng severity cao.

## Follow-up / defer phát sinh
- **Verifier rule riêng cho UC7 khi bật LLM live** (chặn kết tội ở tầng verifier, không chỉ template).
- Map lại 2 bảng ENGINEER khi GSM cấp cột thật.
- **PI-3 DataSource** + **C7 EXP** là 2 mục lớn còn lại của roadmap.
