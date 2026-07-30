# Hồ sơ trạng thái hiện tại — data, simulation, UI và Advisor

> **HISTORICAL SNAPSHOT 2026-07-27** (HEAD `7739b3c`) — hiện trạng đọc
> [`../2026-07-29-cycle-w-review/findings.md`](../2026-07-29-cycle-w-review/findings.md) +
> [`tracking/PLAN-cycle-wx-2026-07-29.md`](../../../tracking/PLAN-cycle-wx-2026-07-29.md).
> Không sửa lại nội dung lịch sử phía dưới để giữ evidence trail.

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
| Ignore/non-compliance | Có intent/design rời rạc về cooldown và “giảm nhắc”, nhưng chưa có lifecycle/store thống nhất. Nút “Bỏ qua” hiện chỉ append JSONL; lần gọi sau không đọc lại để suppress.<br>⚠ Đính chính 29-07: Cycle W (UPDATE-091) — canonical = `AdviceEventLog` append-only, validate qua registry trước khi ghi; JSONL chỉ còn debug export; GET /actions đọc từ event log. |
| Mục tiêu tuần/recap | Scope có ý tưởng, S5 xử lý **khoán chính sách**, nhưng chưa có contract/store/UI cho **mục tiêu cá nhân** và recap F3 thật. Ba khái niệm mục tiêu cá nhân, khoán policy và mission cần tách riêng. |
| ĐA-01..03 | **APPROVED-DESIGN — Cường 2026-07-27**, chưa implement trong phiên docs này.<br>⚠ Đính chính: ĐA-01 đã làm (UPDATE-086); ĐA-05 DONE-CODE (UPDATE-091). |
| ĐA-04..06 | Đã làm giàu thành phương án có dependency, contract và acceptance gate. **DUYỆT 2026-07-27** cùng ĐA-07/08/09 và `specs/advisor-objective-model-v2.md` (Cường: *"oke duyệt hết"*) — ĐA-06 xếp POLISH, phải nhắc duyệt lại trước khi implement. Verdict đầy đủ: `tracking/PENDING-REVIEW.md`. |
| R5 | `MUT10` **ĐÃ GỠ 2026-07-27** (UPDATE-074): khôi phục `_soc_cost`, thêm 2 regression test `bucket_min ≠ 30`, mutation re-apply → đỏ đúng; full suite **533 passed / 4 skipped**. R5-B vẫn **INCOMPLETE**: 2/5 reviewer chết vì quota tháng.<br>⚠ Số thời điểm snapshot; 2026-07-29: 707 passed/5 skipped. |
| Advice có làm tài xế giàu hơn? | **ĐO ĐƯỢC — KHÔNG, và ở 30 seed thì CÓ Ý NGHĨA THỐNG KÊ.** Hồ sơ [`09`](09-baseline-30seed-coverage-all.md): payout **−17.310đ/ngày, CI95 [−29.294, −5.820]**, chỉ 7/30 seed có lợi; cơ chế = cùng giờ online nhưng **+25,9 phút rỗi, −1,6 cuốc**. Tầng hệ thống xấu theo hướng nhất quán nhưng **CI chứa 0** ⇒ chưa kết luận được (đính chính số 10-seed của hồ sơ 07).<br>⚠ Đính chính 2026-07-28/29: số đó là của cấu hình 4-kênh CŨ (đã TẮT theo ĐA-07). Cấu hình duyệt hiện hành (chỉ `positioning_overrides: wait_only`): **+6.016đ/người/ngày SIG (n=100 seed)**, served +1,74đp, đơn chết −23,4, Gini & HHI giảm — PASS 9/9 ĐA-08 (UPDATE-087). |

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
10. [`../../../tracking/PLAN-cycle-wx-2026-07-29.md`](../../../tracking/PLAN-cycle-wx-2026-07-29.md) — prompt giàu ngữ cảnh để tiếp tục phiên sau (⚠ 29-07: link cũ `FOLLOWUP-PROMPT-2026-07-27.md` đã chết, thay bằng file này).

## Phương pháp và độ tin cậy

Hồ sơ này được dựng bằng bốn vòng đối chiếu:

1. manifest + generator + **41 JSON Schema** + registry (⚠ 29-07: 44 file — 43 latest + snapshot
   `shift_plan_input@1.0.0`; thêm `market_state_view`, `advice_lifecycle_event`);
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

## ~~Artifact 31–34 — lưới ablation ĐA-04~~ ⚠ **BỊ TREO — đọc artifact 37 thay thế**

> Mọi con số trong mục này đo với arm đối chứng **bị nhiễm ba confound** (xem mục cuối file). Giữ nguyên văn làm hồ sơ về việc kết luận đã sai thế nào — **không được trích cho quyết định**. Số đúng nằm ở artifact 37.

### (nguyên văn bản cũ, 2026-07-29, UPDATE-099)

Bốn file JSON là **một lưới 2×2 đầy đủ**, cùng 30 seed CRN 3160–3189, `coverage=all`,
`positioning_overrides=wait_only`. Đọc chúng như MỘT thí nghiệm, không phải bốn phép đo rời:

| File | Arm | Δ payout/tài xế |
| --- | --- | --- |
| `31-da04-cadence-30seed.json` | `default_positioning` (chỉ kênh vị trí) · `ladder_all` | +4.469đ SIG · +5.701đ SIG |
| `32-da04-ablation-30seed.json` | `ladder_all`, **cadence OFF** | +8.586đ SIG |
| `33-da04-no-shiftplan-30seed.json` | bỏ `shift_plan`, cadence ON | +7.135đ SIG |
| `34-da04-2x2-cell-30seed.json` | bỏ `shift_plan`, cadence OFF | +8.561đ SIG |

**Kết luận rút ra được (và CHỈ rút ra được nhờ ô thứ tư):** bỏ `shift_plan` khi cadence TẮT
gần như vô hại (−25đ) nhưng khi cadence BẬT lại đáng +1.433đ ⇒ tương tác +1.458đ nằm
trọn ở việc kênh đó chiếm suất trong ngân sách chú ý, không phải ở nội dung lời khuyên.
Ba arm đầu **không tách được** confound này.

~~⚠ Δ giữa các arm cách nhau 1,4–2,9k trên SD ~40k/seed ⇒ thứ tự giữa các arm là gợi ý
mạnh, chưa phải kết luận thống kê chắc chắn; số nào dùng để ra quyết định phải chạy lại
ở n≈100.~~ **ĐÃ CHẠY — `35-da04-cost-of-cadence-n100.json`** (100 seed tươi 4000–4099,
ước lượng GHÉP CẶP `B_on−B_off` trên cùng seed, 3 thế giới/seed): giá của nhịp
**−3.048đ CI[−4.117, −2.005] SIG**, gini **−0,0051 SIG** (công bằng hơn — lần đầu có
bằng chứng ghép cặp trực tiếp), served −0,85đp SIG, nhịp có lợi 34/100 seed. Kết luận
n=30 đứng vững. Phân rã FIFO/nội-tại vẫn là số n=30 (lưới 2×2 chưa chạy ở n=100).

## ⚠ Artifact 31–35 BỊ TREO — đọc 36/37 trước (thêm 2026-07-29)

Hai vòng soi đối kháng tìm ra **ba confound** trong arm đối chứng `cadence=off`, tất cả **sau khi** 31–35 đã được đo và báo cáo:

1. **DET-01** — tắt `cadence.enabled` cũng tắt luôn keyed coin ⇒ arm đối chứng có adherence hiệu dụng cao hơn ~10đp (đo: 0,761 vs danh nghĩa 0,588, so với arm ON 0,681 vs 0,603).
2. **R-01** — một lời khuyên được nghe theo bị **áp tác động 2,0–2,5 lần** ở arm OFF (`gate_events/decision_id` = 2,46/2,11/2,02 vs ~1,05 ở ON). Lỗi đúng-sai, không chỉ lỗi đo.
3. **R-09** — ba kênh dùng ba định nghĩa "đã nói" ⇒ ngân sách chia không đồng nhất.

**`36-da04-DET01-corrected.json`** = đo lại với fix (1): giá của nhịp n=100 đi từ **−3.048đ → −2.593đ** (hẹp 15%), và ô `OFF_nosp` của lưới 2×2 đổi **+8.561 → +6.597đ** ⇒ **cấu trúc tương tác của lưới cũ không còn đứng; con số "FIFO tốn 1.458đ" KHÔNG dùng được nữa.**

**`37-da04-all-confounds-fixed.json`** = đo lại **cả 5 arm** với đủ ba fix. Đây là artifact duy nhất được phép trích cho quyết định.

**Kết quả 37 (n=100 ghép cặp):** giá của nhịp **−1.530đ CI[−2.401, −673] SIG** — bằng đúng một nửa con số từng báo (−3.048đ). Mọi chỉ tiêu khác cũng giảm ~½ và vẫn SIG: `gini` −0,0030 · served −0,46đp · đơn hoàn thành −5,47 · payout người khác −140k.

**Lưới 2×2 (30 seed, cả 5 arm):** `ON_all` +5.624 · `OFF_all` +8.488 · `ON_nosp` +7.173 · `OFF_nosp` +6.789 · `ON_pos_only` +4.469. ⇒ bỏ `shift_plan` khi cadence ON **+1.549đ**, khi OFF **−1.700đ** (ĐẢO DẤU so với −25đ của lưới cũ) ⇒ **tương tác +3.249đ**. Giá của nhịp khi CÓ `shift_plan` −2.865đ, khi KHÔNG **+384đ**.
⇒ **Toàn bộ chi phí của nhịp tập trung ở tương tác với `shift_plan`** — nhịp tự nó gần như miễn phí. ⚠ Các hiệu số này là hiệu của ĐIỂM ƯỚC LƯỢNG (không lưu per-seed cho 4 ô ⇒ **không có CI**); chỉ ước lượng ghép cặp n=100 mới có CI hợp lệ.

## ✅ `38-e5-2x2-perseed-n100.json` — lưới 2×2 lần đầu CÓ CI (thêm 2026-07-29)

Đóng đúng lỗ hổng mà artifact 37 tự ghi ra ở trên: 100 seed (4200–4299) × **4 world/seed**,
**lưu per-seed cả 4 ô** rồi bootstrap ⇒ tương tác có CI hợp lệ.

| Ước lượng (`net_mean_all`, đ/tài xế/ngày) | mean | CI95 | |
| --- | --- | --- | --- |
| **TƯƠNG TÁC ngân sách FIFO** | **+2.207** | [+1.077, +3.372] | **SIG** |
| Giá của nhịp **khi CÓ** `shift_plan` | −2.466 | [−3.420, −1.570] | **SIG** |
| Giá của nhịp **khi KHÔNG có** `shift_plan` | **−259** | [−1.111, **+589**] | **ns** |
| Bỏ `shift_plan` khi nhịp BẬT | +2.259 | [+1.161, +3.323] | **SIG** |
| Bỏ `shift_plan` ở TRẦN (nhịp tắt) | **+53** | [−974, +1.102] | **ns** |

Tương tác cũng SIG trên: `gini_payout` +0,0043 · `served_rate` +0,52đp · `orders_completed`
+6,28 · `expired_n` −7,33 · `others_payout` +195.979đ.

**Hai đính chính mà artifact này bắt buộc:**

1. *"Nhịp tự nó gần như miễn phí"* — trước chỉ là **điểm ước lượng +384đ**; nay là
   **−259đ với CI trùm 0** ⇒ có bằng chứng thống kê rằng **không phân biệt được với 0**.
   Chi phí của nhịp **không** nằm ở việc advisor nói ít, mà ở **cách chia ngân sách**.
2. **`−1.700đ` ở dòng trên là NHIỄU n=30 — đã bị bác.** Ở n=100, bỏ `shift_plan` ở trần chỉ
   **+53đ ns** ⇒ `shift_plan` **trung tính khi đứng một mình**, KHỚP kết luận ĐA-07, không
   ngược. Nhưng nó **độc hại dưới ngân sách FIFO** (+2.259đ SIG) vì chiếm suất của kênh có
   tác dụng ⇒ ĐA-07 giữ TẮT là đúng, với lý do mạnh hơn lý do ban đầu.

⇒ Artifact được phép trích cho quyết định về **độ lớn tương tác**: **38** (không phải 34/37).

## ✅ `39-da07-recheck-tran-n100.json` — phép đo ĐỘC LẬP xác nhận artifact 38 (thêm 2026-07-29)

Cùng câu hỏi (`shift_plan` đáng bao nhiêu ở TRẦN, nhịp TẮT), **bộ seed khác**, ước lượng ghép cặp
riêng, n=100:

| Ước lượng | mean | CI95 | |
| --- | --- | --- | --- |
| **GIÁ TRỊ của `shift_plan`** (có − không, ở trần) | **−451đ** | [−1.499, +608] | **ns** |
| Trần giá trị advisor, đủ kênh (`all` − A) | +7.666đ | [+6.615, +8.662] | **SIG** |
| Trần giá trị advisor, bỏ `shift_plan` (`nosp` − A) | **+8.117đ** | [+7.022, +9.232] | **SIG** |

`served_rate` +2,48đp → +2,67đp · `orders_completed` +29,8 → +32,0 · `expired_n` −32,5 → −34,3
(tất cả SIG); riêng phần đóng góp của `shift_plan` trên MỌI chỉ tiêu đều **ns**.

**Hai phép đo độc lập nay KHỚP NHAU** — đây là điều n=30 không cho được:

| | artifact 38 (seed 4200–4299) | artifact 39 (seed khác) |
| --- | --- | --- |
| `shift_plan` đứng một mình | **+53đ ns** (bỏ nó) | **−451đ ns** (có nó) |
| Kết luận | trung tính | trung tính |

⇒ `D-ĐA07-recheck` **ĐÓNG**. Ô **−1.700đ** của lưới n=30 là **nhiễu**, đã bị hai phép đo n=100 độc
lập bác. ĐA-07 (*"`shift_plan` không hiệu quả ⇒ giữ TẮT"*) **đúng**, và lý do mạnh hơn lý do ban
đầu: kênh **trung tính khi đứng một mình** nhưng **độc hại dưới ngân sách FIFO** (+2.259đ SIG khi
bỏ nó lúc nhịp bật). Và ở n=100 thì **bỏ nó còn hơi TỐT hơn** (+8.117 vs +7.666), ngược hẳn thứ tự
của lưới n=30 (6.789 < 8.488).

**Cái KHÔNG đổi qua mọi bước:** `gini_payout` −0,0051 SIG — kết luận *"nhịp mua công bằng bằng tiền"* vững; chỉ GIÁ là thứ bị báo cao hơn thực tế. Thêm `D-R08`: con số "2.670 lần bị nén" cũng phóng đại ~47% vì ba kênh đếm "bị nén" trước khi biết có nội dung khuyên hay không.

