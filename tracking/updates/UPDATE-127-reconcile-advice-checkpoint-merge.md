# UPDATE-127 — Reconcile main với AdviceCheckpoint P2–P5 trong PR #4

- **Ngày:** 2026-08-03
- **Người thực hiện:** AI agent theo yêu cầu trực tiếp của Cường + Khánh
- **Loại:** docs / merge-reconciliation
- **TODO / User story liên quan:** `D-M3-17`, `D-M3-18`, `V-25`, `CKPT-P1..P5`

## Tóm tắt

Đã merge `origin/main` hiện tại (`87b53ba`) vào branch `feat/advice-checkpoint-p2-p5` và
giải quyết ba conflict tài liệu trong `PENDING-REVIEW.md`, `PROJECT-GRAPH.md` và `TODO.md`.
Không thay đổi code/runtime; các điểm pin UI của UPDATE-121 và AdviceCheckpoint của
UPDATE-126 đều được giữ lại, còn `D-M3-17` được hợp nhất về `FIXED` và `D-M3-18` vẫn mở.

## Chi tiết cập nhật

- Giữ cả hai visual gate từng dùng mã `V-25`, nhưng gắn nguồn `UPDATE-121` và `UPDATE-126`
  ngay trong mã hiển thị để không làm mất gate pin UI hoặc gate AdviceCheckpoint.
- Giữ section AdviceCheckpoint P2–P5 và Codex harness trong graph, đồng thời đưa UPDATE-120
  (tầm pin UI) về đúng vị trí chronological trước section 3.8.
- Loại duplicate/stale `D-M3-17` ở TODO: trạng thái hiện hành là `FIXED` theo UPDATE-121;
  `D-M3-18` tiếp tục `TODO (sev CAO)` vì Flutter chưa đọc cờ `applicable`.
- Không đóng `V-25`; cả hai gate vẫn cần human/device review tương ứng.

## Files bị ảnh hưởng

| File | Hành động (tạo/sửa/xóa) | Ghi chú |
| --- | --- | --- |
| `tracking/PENDING-REVIEW.md` | sửa | Giữ hai gate V-25 và disambiguate theo UPDATE nguồn |
| `tracking/PROJECT-GRAPH.md` | sửa | Giữ UPDATE-120, UPDATE-124/126 và UPDATE-125 trong graph |
| `tracking/TODO.md` | sửa | D-M3-17 = FIXED; D-M3-18 = TODO sev CAO |
| `tracking/updates/UPDATE-127-reconcile-advice-checkpoint-merge.md` | tạo | Evidence cho cycle merge/reconciliation |

## Docs đã cập nhật kèm theo

Đã cập nhật `TODO`, `PROJECT-GRAPH` và `PENDING-REVIEW` như trên. Không đổi `SCOPE`,
`DEFERRED` hay product boundary; không dual-write, không đổi cadence, không bật API v2.

## Assumptions và evidence

| Claim / tham số | Nhãn (`FACT` / `OBSERVED-CODE` / `PROXY` / `MOCK` / `ASSUMPTION` / `UNVERIFIED`) | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| `origin/main` tại `87b53ba` là base PR hiện tại | `OBSERVED-CODE` | `git fetch origin main`, merge conflict tái tạo được | cao | Có thể phải reconcile lại nếu main đổi tiếp |
| Hai V-25 là hai gate độc lập | `FACT` | UPDATE-121 và UPDATE-126 có nội dung, owner/evidence khác nhau | cao | Nếu gộp sẽ mất một yêu cầu visual |
| D-M3-17 đã fixed; D-M3-18 còn mở | `OBSERVED-CODE` | UPDATE-121, `DEFERRED.md`, backend/web flag; Flutter gate còn thiếu | cao | Không được claim production-ready cho battery UI |

## Kiểm chứng

- `git merge-tree origin/main HEAD` xác nhận đúng ba file conflict trước khi sửa.
- `rg '^(<<<<<<<|=======|>>>>>>>)' tracking/{PENDING-REVIEW,PROJECT-GRAPH,TODO}.md` không còn marker.
- `git diff --check` và `git diff --cached --check` được dùng cho docs/merge diff.
- **Không chạy lại full backend** theo chỉ thị của người điều khiển. Không có test/runtime
  behavior thay đổi trong cycle này.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
| --- | --- | --- | --- | --- |
| Docs-only merge reconciliation | không áp dụng | conflict blocks của ba tracking files | marker-free, semantic rows retained | GitHub Actions/PR check sau push |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** docs-only; không đổi UI/runtime.
- **Seed / scenario đã xem:** không áp dụng.
- **Người review + verdict:** không cần visual gate mới; V-25 battery và AdviceCheckpoint vẫn `BLOCKED`/chờ verdict riêng.
- **Lý do:** cycle chỉ hòa giải tài liệu sau merge, không thay đổi cách hiển thị.

## Adversarial self-review / flaws found

1. Rủi ro lớn nhất là resolve theo một nhánh rồi làm mất gate của nhánh kia; đã giữ cả hai
   và thêm source qualifier ngay tại `PENDING-REVIEW`/graph.
2. Rà lại duplicate `D-M3-17`: chỉ giữ trạng thái `FIXED` một lần; không biến `D-M3-18`
   thành `DONE` khi Flutter còn thiếu.
3. Không chạm code, config runtime, solver, cadence hoặc flag `ADVICE_V2_ENABLED`.
4. V-25 vẫn không được coi là reviewed; thiếu Flutter SDK/emulator vẫn là blocker thật.
5. Flaw còn mở: D-M3-18 và hai human visual verdict map về `D-M3-18`/`V-25` trong
   `PENDING-REVIEW.md`; không tự đóng trong PR này.

## Expansion checkpoint (T-039 — bắt buộc sau mỗi phần hoàn thành)

1. **Schema:** không.
2. **Bài toán tối ưu:** không.
3. **Tính năng:** không; chỉ reconcile tracking sau merge.

## Follow-up / defer phát sinh

- Push merge commit lên branch PR #4 và để GitHub Actions chạy theo workflow hiện có.
- Human review vẫn cần cho hai gate `V-25 · UPDATE-121` và `V-25 · UPDATE-126`.
- `D-M3-18` giữ TODO sev CAO cho phần Flutter/field đội pin; không đưa vào scope P2–P5.
