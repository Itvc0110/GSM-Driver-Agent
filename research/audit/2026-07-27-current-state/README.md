# Hồ sơ trạng thái hiện tại — data, simulation, UI và Advisor

Ngày đối chiếu: **2026-07-27**

Baseline đã đọc: Git HEAD `7739b3c`

Loại công việc: **research/docs-only** — không sửa runtime, UI, schema hay test.

## Kết luận điều hành

| Chủ đề | Kết luận |
|---|---|
| “Mock 90 ngày” | **FACT:** là 90 ngày nội dung synthetic được sinh theo seed, mang hình dạng 13 bảng `l1r` do GSM cung cấp. Đây **không phải** 90 ngày dữ liệu vận hành thật và cũng không phải “90 ngày gần nhất”; snapshot hiện chạy từ 2026-07-01 đến 2026-09-28. |
| Simulation ↔ UI | **OBSERVED-CODE:** chưa parity end-to-end. Hiện tồn tại ba thế giới dữ liệu: run engine theo seed, snapshot Parquet 90 ngày, và ba cuốc demo hard-code + OSRM. |
| Kiến trúc đích | **DECISION — Cường 2026-07-27:** chọn **B — một canonical run/snapshot, hai projection**. Màn simulation là góc nhìn toàn hệ thống/dispatcher; app là góc nhìn của một tài xế, nhưng cùng identity, clock, policy, payout ledger và provenance. |
| Data có tự cập nhật? | **OBSERVED-CODE:** actor trong một run sim có cập nhật counter/state trong RAM. Snapshot UI, tỷ lệ nhận/hoàn thành, mission và payout **không** được cập nhật bởi cuốc demo hay bởi việc gọi Advisor. Regen là thao tác thủ công; backend còn cache bảng trong process. |
| Advisor đã ship | **OBSERVED-CODE:** core có 9 solver + router/composer/verifier, nhưng app web hiện chỉ nối S1; Flutter còn hard-code. External weather/event/traffic chưa đi vào advice. |
| Ignore/non-compliance | Có intent/design rời rạc về cooldown và “giảm nhắc”, nhưng chưa có lifecycle/store thống nhất. Nút “Bỏ qua” hiện chỉ append JSONL; lần gọi sau không đọc lại để suppress. |
| Mục tiêu tuần/recap | Scope có ý tưởng, S5 xử lý **khoán chính sách**, nhưng chưa có contract/store/UI cho **mục tiêu cá nhân** và recap F3 thật. Ba khái niệm mục tiêu cá nhân, khoán policy và mission cần tách riêng. |
| ĐA-01..03 | **APPROVED-DESIGN — Cường 2026-07-27**, chưa implement trong phiên docs này. |
| ĐA-04..06 | Đã làm giàu thành phương án có dependency, contract và acceptance gate. **DUYỆT 2026-07-27** cùng ĐA-07/08/09 và `specs/advisor-objective-model-v2.md` (Cường: *"oke duyệt hết"*) — ĐA-06 xếp POLISH, phải nhắc duyệt lại trước khi implement. Verdict đầy đủ: `tracking/PENDING-REVIEW.md`. |
| R5 | `MUT10` **ĐÃ GỠ 2026-07-27** (UPDATE-074): khôi phục `_soc_cost`, thêm 2 regression test `bucket_min ≠ 30`, mutation re-apply → đỏ đúng; full suite **533 passed / 4 skipped**. R5-B vẫn **INCOMPLETE**: 2/5 reviewer chết vì quota tháng. |
| Advice có làm tài xế giàu hơn? | **ĐO ĐƯỢC — KHÔNG, và ở 30 seed thì CÓ Ý NGHĨA THỐNG KÊ.** Hồ sơ [`09`](09-baseline-30seed-coverage-all.md): payout **−17.310đ/ngày, CI95 [−29.294, −5.820]**, chỉ 7/30 seed có lợi; cơ chế = cùng giờ online nhưng **+25,9 phút rỗi, −1,6 cuốc**. Tầng hệ thống xấu theo hướng nhất quán nhưng **CI chứa 0** ⇒ chưa kết luận được (đính chính số 10-seed của hồ sơ 07). |

## Đọc theo thứ tự

1. [`01-data-lineage-and-update-model.md`](01-data-lineage-and-update-model.md) — “90 ngày” là gì, schema có gì, data nào cập nhật và cadence nào hiện có/chưa có.
2. [`02-simulation-ui-advisor-parity.md`](02-simulation-ui-advisor-parity.md) — gap hiện tại và kiến trúc B đã chốt.
3. [`03-advisor-ux-goals-recap.md`](03-advisor-ux-goals-recap.md) — năng lực Advisor, ignore UX, mục tiêu tuần, recap đẹp nhưng không gây áp lực.
4. [`04-decision-areas-da01-da06.md`](04-decision-areas-da01-da06.md) — ĐA-01..03 đã duyệt; hướng đi ĐA-04..06 chờ duyệt.
5. [`05-verification-and-review.md`](05-verification-and-review.md) — bằng chứng, blocker, checklist Cường cần kiểm tra/thử nghiệm.
6. [`06-why-advice-loses-money.md`](06-why-advice-loses-money.md) — **(bổ sung 2026-07-27, phiên Claude)** truy nguyên bằng ablation vì sao "làm theo advisor" ra ÍT tiền hơn tự làm: thủ phạm là kênh `accept_lift`; gốc rễ là mô hình coi năng suất là hằng số ngoại sinh. Đề xuất **ĐA-07**.
7. [`07-fleetwide-advice-equilibrium.md`](07-fleetwide-advice-equilibrium.md) — **(bổ sung 2026-07-27)** lần ĐẦU chạy `coverage: all` (advice cho toàn bộ 90 tài xế, 10 seed): chỉ ~36% vị trí percentile tăng thu nhập, `served_rate` giảm 6/10 seed và **đơn hết hạn tăng ~8/ngày** ⇒ khách hàng bị ảnh hưởng. Đề xuất **ĐA-08** (ràng buộc hệ thống trong tiêu chí chấp nhận).
8. [`08-parity-sim-vs-ui.md`](08-parity-sim-vs-ui.md) — **(bổ sung 2026-07-27)** đối chiếu HAI CHIỀU sim ⇄ UI: 8 chỗ hai-nguồn-sự-thật (nặng nhất: cước lệch **4,6×**), rò tương lai trong `advisor.py`, và mẫu hợp nhất đã đúng để nhân rộng. Nền cho cycle C2.
9. [`09-baseline-30seed-coverage-all.md`](09-baseline-30seed-coverage-all.md) — **(bổ sung 2026-07-27)** **SỐ NỀN chuẩn**: 30 seed CRN, `coverage: all`, guardrail 4 tầng. Tác hại **cá nhân có ý nghĩa thống kê**; tác hại **hệ thống chưa đủ bằng chứng** ⇒ đính chính hồ sơ 07. Quyết định thứ tự sửa: objective cá nhân TRƯỚC, equilibrium SAU.
10. [`../../../tracking/FOLLOWUP-PROMPT-2026-07-27.md`](../../../tracking/FOLLOWUP-PROMPT-2026-07-27.md) — prompt giàu ngữ cảnh để tiếp tục phiên sau.

## Phương pháp và độ tin cậy

Hồ sơ này được dựng bằng bốn vòng đối chiếu:

1. manifest + generator + **41 JSON Schema** + registry;
2. backend adapter/router + web/Flutter + sim engine/advice bridge;
3. audit/report/update/git history, gồm attachment của phiên R5 đang dở;
4. đối chiếu chéo docs với code và nguồn UX/HCI chính thức.

Ba lane đọc độc lập bằng subagent đã hoàn tất ở vòng trước: data/sim-UI parity, Advisor UX, và
DA/docs. Một batch fact-check bổ sung ở vòng này bị giới hạn quota; kết quả batch đó **không được
tính như một vòng verify hoàn tất**. Finding `MUT10` do lane R5 phát hiện đã được agent chính tự
kiểm lại độc lập bằng cả source hiện tại và `git show 7739b3c`.

## Ranh giới của tài liệu

- Đây là bản đồ trạng thái và research direction, không phải tuyên bố production-ready.
- Các phần ghi `PROPOSAL` chưa cấp quyền sửa code/contract.
- Số liệu mock chỉ mô tả artefact synthetic, không suy diễn uplift hay hành vi thật của tài xế GSM.
- Không tiếp quản hoặc hoàn tất thay cho phiên R5. Các finding R5 chỉ được lập chỉ mục để không mất dấu.
