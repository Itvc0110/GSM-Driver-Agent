# UPDATE-090 — Cycle V: gỡ B-02/ARCH-VERSION — registry đa phiên bản, upcaster, backward-compat bằng record thật

- **Ngày:** 2026-07-29 (bắt đầu 28)
- **Người thực hiện:** AI agent, dưới claim của **Cường** (mạch *"hướng tốn thời gian, khó,
  nhiều giá trị nhất"*)
- **Loại:** architecture (schema/validate layer) — KHÔNG đổi hành vi sim/solver
- **Mở khoá:** **ĐA-05** (event store append-only cần replay qua migration) · **T-044/ĐA-06**
  (*"schema versioned + upcaster ngay từ v2.0.0 — phải gỡ B-02 TRƯỚC"*)

## Vấn đề (audit `01-*` §8)

Registry cũ: 1 entity ↔ 1 file, `schema_version.const` một giá trị, không ai đọc version của
PAYLOAD. Hệ quả sống: **5 đợt additive đã ship mà const không đổi** — và chính **Cycle R
(28/07)** thêm 2 trường rest vào `shift_plan_input` cũng không bump. "1.0.0" mô tả nhiều hình
dạng; backward compatibility là quy ước tác giả, không phải tính chất được kiểm.

## Cơ chế mới

- **File versioned, chọn theo RECORD**: latest giữ tên `{entity}.schema.json`; lịch sử
  `{entity}@{version}.schema.json`; `validate` route theo `record["schema_version"]`;
  version lạ/null ⇒ **fail-loud kèm danh sách đã biết** (không silent-fallback).
- **Upcaster** (`gsm_core/upcasters.py`): pure function từng-bậc, chuỗi tự nối, có chặn-treo.
- **Bump thật đầu tiên — trả nợ Cycle R**: `shift_plan_input` 1.0.0 → **1.1.0**; snapshot
  `@1.0.0` dựng từ hình dạng git-cũ; bridge (có emit 2 trường) khai 1.1.0, producer l1r/features
  (không emit) giữ 1.0.0 — **hai version sống song song hợp lệ**.
- **Backward-compat là ĐIỀU ĐƯỢC TEST**: record 1.0.0 THẬT đã persist trong
  `data/mock/realdata-v1/*.parquet` validate pass qua registry mới
  (`test_persisted_old_records_still_validate`) — đúng câu audit chốt.
- **Vá lỗ `market_state_view`** (Explore agent tìm ra): view T-045a emit `schema_version` mà
  không có schema/entity nào — nay có schema + entity + test payload thật cả nhánh absent.
- Manifest generator: `schema_versions` đọc từ registry, hết hardcode "1.0.0".

## Review đối kháng (ultracode Workflow: 4 lăng kính → 24 finding → phản biện từng cái)

**7 CONFIRMED bằng reproduce thật — đã sửa hết trong cycle:**

| # | Finding (reviewer tự chạy repro) | Fix |
|---|---|---|
| 1 | ⭐ File `@version` rác (`{}`) ⇒ record BỊA validate **PASS im lặng** | từ chối lúc load: const-trong-file phải == version-trên-tên |
| 2 | Upcaster quên stamp ⇒ upcast **treo vô hạn** (repro 10.001 vòng) | mỗi bậc phải TIẾN thật + trần len(known); ValueError nêu chỗ kẹt |
| 3 | Tên file `@1.0.1-rc1` ⇒ ValueError **mù** đánh sập mọi validate của entity | lỗi nêu đúng file + entity |
| 4 | Thiếu const ⇒ bare KeyError không ngữ cảnh | `_const_of` nêu entity + path |
| 5 | `schema_version: null` âm thầm route latest | fail-loud riêng cho null |
| 6 | Entity lạ ⇒ bare KeyError từ LAYER_OF | ValueError tường minh |
| 7 | Manifest hardcode `{e: "1.0.0"}` trong khi version nay load-bearing | đọc từ registry (cả generate lẫn realdata) |
| — | README bước snapshot ghi "copy file hiện tại" — SAI khi hình dạng đã bị sửa tại chỗ | sửa: snapshot từ git HEAD trước thay đổi |

**Phát hiện NGOÀI scope (pre-existing, reviewer reproduce bằng chạy thật):** entrypoint
`python -m gsm_core.mockgen.generate` crash tại `generate.py:50` trước cả verify_round1 —
đường CLI không test nào phủ. KHÔNG do Cycle V (diff không đụng đường đó). Ghi
**BUG-MOCKGEN-CLI** vào TODO.

**4 verifier chết vì session limit** ⇒ 4 finding chỉ PLAUSIBLE: tôi tự kiểm 2 cái có nghĩa
(upcast tạo registry mới mỗi lần gọi — đã sửa bằng `_registry()` cache; `build_l1r_schemas.py`
version-unaware — hôm nay vô hại vì l1r toàn 1.0.0, ghi chú vào script là việc của lần bump l1r
đầu tiên). 2 cái còn lại trùng nội dung #3/#4.

## Files

`src/gsm_core/schema_registry.py` (viết lại + 6 guard) · `src/gsm_core/upcasters.py` (mới) ·
`schemas/l3/shift_plan_input{,@1.0.0}.schema.json` · `schemas/l3/market_state_view.schema.json`
· `src/gsm_sim/advice_bridge.py` (khai 1.1.0) · `src/gsm_core/mockgen/{generate,realdata}.py`
(manifest) · `tests/test_schema_versioning.py` (17 test) · un-pin `tests/test_schemas.py`
(map `LATEST_VERSIONS` tường minh) + `tests/test_l1r_schemas.py` · `schemas/{README,CHANGELOG}.md`.

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| TDD | 10 đỏ trước → xanh; 6 guard mới đều viết SAU khi reviewer reproduce |
| Mutation | MV1 route-all-latest → 2 đỏ · MV2 bỏ upcaster → 2 đỏ · restore xanh |
| Full suite (trước hardening) | **647 passed / 5 skipped** |
| Targeted sau hardening | 84 passed (versioning + schemas + l1r + mockgen + realdata gates) |
| Record persist cũ | 13 bảng × 3 dòng validate pass (parquet + giải mã cột JSON-string) |
| Full suite cuối | **653 passed / 5 skipped** (14:24, sau toàn bộ hardening — khớp dự đoán 647+6 guard) |

## Visual verification

`NOT_APPLICABLE` — tầng schema/validate, không đổi output sim/UI (test bit-identical:
placebo/absent giữ nguyên; suite 647 xanh).

## Adversarial self-review / flaws found

1. **Review đối kháng bắt được 7 lỗi mà TDD của tôi không bắt** — mọi lỗi đều ở lớp "kẻ thù là
   file hỏng/con người nhầm", còn test của tôi chỉ phủ happy-path + mutation code. Bài học
   ghi vào T-046: TDD phủ LOGIC, adversarial review phủ INPUT THÙ ĐỊCH — cần cả hai.
2. Bump l1r đầu tiên trong tương lai sẽ đòi sửa `build_l1r_schemas.py` (đang version-unaware)
   — ghi chú tại chỗ, chưa sửa trước (YAGNI).
3. Họ `ui/contracts/*` vẫn KHÔNG version — nợ riêng đã ghi TODO từ trước, cycle này không đụng.
4. `versions()` lru_cache không invalidate khi thêm file lúc runtime — chấp nhận (schema đổi
   = deploy mới), ghi để ai làm hot-reload sau này biết.

## ⏳ Nhắc PENDING-REVIEW

V-01..V-17 (Cường: "hỏi lại sau") · Q-03/Q-04/Q-07 · ~~B-02~~ **GỠ** · BUG-MOCKGEN-CLI mới ·
nợ UI card standby_zone · đề xuất kế tiếp: **ĐA-05 event store** (vừa được mở khoá).
