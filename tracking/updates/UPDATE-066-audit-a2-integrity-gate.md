# UPDATE-066 — AUDIT A2: gate integrity mở rộng cho 13 bảng mock

Ngày: 2026-07-27 · Track: **AUDIT** · Sau batch 1 (`c540f33`).

## 1. Bối cảnh (A2 findings)

Gate cũ chỉ kiểm tên bảng + tên/thứ tự cột — không kiểm kiểu, nullability, quan hệ giữa bảng;
4 bảng `spec_cols=None` bị skip. Đây là test-gap (VISIBILITY), không phải bug sống.

## 2. Files

- `tests/test_l1r_integrity_gate.py` (TẠO, 5 test): kiểu cột ỔN ĐỊNH giữa các dòng (int/float
  một họ, bool tách riêng) · cột khoá không null/rỗng (7 bảng) · **FK mission không mồ côi**
  (earn_history/progress → catalog) · driver_id mọi bảng ⊆ universe · trips: gross>0,
  commission≤gross, request≤complete.
- **Giới hạn trung thực ghi trong docstring**: metadata GSM không kèm dtype/nullability chính
  thức → gate chỉ ép NHẤT QUÁN NỘI BỘ, không thay được so khớp dtype với bảng thật (data gap
  cho D-POL-05/GSM).

## 3. Kiểm chứng

- Gate mới: **5 passed** (27s) — generator hiện SẠCH theo các bất biến này (pass-ngay là kỳ vọng
  đúng cho việc đóng lỗ coverage; giá trị nằm ở chặn trôi tương lai).
- Không đổi code sản phẩm — test-only ⇒ full suite không cần chạy lại (batch 1 vừa xanh 504).
- Visual: NOT_APPLICABLE.

## 4. Trạng thái AUDIT sau update này

A1 ✅ findings + batch fix 1 · **A2 ✅ đóng** (F-U2-A trả lời + gate mở rộng; D-SIM-08 giữ DEFERRED)
· A3 ⏳ chờ quota (2:20am) · A4 ⏳. Hàng chờ sau quota: verify 11 finding treo → S2 bundle fix →
A3 workflow → A4 report + đề án.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · V-09 · **V-10 (Track UI)** · Q-03.
