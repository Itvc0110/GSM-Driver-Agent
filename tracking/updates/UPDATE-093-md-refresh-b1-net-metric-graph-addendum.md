# UPDATE-093 — md-refresh toàn repo + B1 `net_mean_all` + graph addendum + merge UPDATE-092

- **Ngày:** 2026-07-29 (sáng, sau khi đóng Cycle W `5364395`)
- **Người thực hiện:** AI agent dưới claim Cường (chỉ thị: *"đọc toàn bộ .md bằng subagent,
  cập nhật cho đúng hiện tại; song song hoá; tạo graph doc; chỉ Fable 5"*)
- **Loại:** docs (2 nhóm audit + sửa) + 1 bước code nhỏ đã duyệt trong PLAN-cycle-wx (B1)

## Cách chạy (SDD — subagent-driven-development)

2 Explore reader audit toàn bộ .md → 2 brief chi tiết (`.superpowers/sdd/task-{1,2}-brief.md`)
→ 2 implementer song song (file rời nhau) + 1 implementer B1 → reviewer. **Session limit sập
giữa chừng** (T1 chết giữa TODO, 2 reviewer + graph synthesizer + analyst chết) ⇒ controller
hoàn tất tay phần còn lại + tự review. Ledger: `.superpowers/sdd/progress.md`.

## Chi tiết

| Khối | Nội dung | Commit |
|---|---|---|
| T2 (nhóm B) | research README/00_SUMMARY (đính chính "advisor làm nghèo" → UPDATE-087; adherence hai tên; equilibrium đã đo; positioning mặc định BẬT), 2 README audit lịch sử (banner + đính chính giữ nguyên câu gốc), schemas/README (**cảnh báo KHÔNG có FormatChecker** — `format:` chỉ tài liệu; entity thứ 4; quy tắc narrowing-không-bump), world-parameters (mốc pin **31/03/2029**, dispatcher thật, drop_demand_alpha), sim-policy-bundle (forced-accept/phạt ≤70% là regime ĐÃ BỎ 23/02/2026), SCREEN-PARITY + `advice_action.json` (max 1439, canonical store), ui/README (chỉ THÊM khối trạng thái — file của Khánh) | `ab4eabc` |
| T1 (nhóm A) | CLAUDE.md (bản đồ repo đầy đủ: 85→86 UPDATE, tách docs/data-catalog + superpowers khỏi DEFERRED, thêm hàng code); planning ×4 (SCOPE M1-M4 PAUSED, PERSONAS 5 product vs 7 sim, RESEARCH đợt 3/4); specs ×17 (status + đính chính: S4/capacity/MarketState/S5-khoán/registry/adherence-join-key... đã code); TODO (**shift_plan đã TẮT** — dòng cũ sai; **k_max 6→12 ĐÃ HOÀN TÁC** → UNRESOLVED/BLOCKED-Q-07, baseline k=6 VẪN hiệu lực; T-045a DONE-CODE; T-044 READY; V-11→V-16); DIRECTIVES 6 đính chính (MUT10 đã gỡ, ĐA-01/05 đã implement, OSRM đã code); BACKLOG/DEFERRED/ASSIGNMENTS; banner 3 templates + 2 docs/superpowers ACTIVE | `df90490` |
| B1 | `net_mean_all`/`cost_mean_all` + per-archetype `net_mean` trong `_cohort_metrics`; `cost_summary` vào `sim_metrics.full_report`; 3 test TDD (net==payout khi cost=0 CHÍNH XÁC; payout KHÔNG ĐỔI khi bật cost — chống rò §5; exact-repeat). Sổ chi phí hết là sổ chết — điều kiện tiên quyết của C1 (B2) | `8fc02ba` |
| Graph | `tracking/PROJECT-GRAPH-2026-07-29-addendum.md`: 19 node (5 reader, khôi phục từ journal sau khi synthesizer chết) — one-line + reads, correction chains mermaid (075/078/081/084 → 086), **7 route đọc theo task**, trạng thái mở. Bổ khuyết cho §3.7 (index của UPDATE-092), không lặp | (commit này) |
| Merge | `origin/main 4dc963b` (UPDATE-092 teammate) merge SẠCH — không conflict; contract `at_min max=1439` giữ đúng; CLAUDE.md/addendum cập nhật theo §3.7 mới | merge commit |

## UPDATE-092 của teammate — tiếp nhận

- 4/4 finding §H-04 của họ **đã được `5364395` sửa** (họ tự verify trên code, §H-04-bis).
- **Sống sót: `format_checker`** — rộng hơn ban đầu (15 schema mang `format:` vô hiệu).
  Docs đã cảnh báo (schemas/README, T2); **fix code phải qua plan mode** (đúng chốt pause).
- **B6-PARITY** (mới, rủi ro lớn nhất theo họ): sản phẩm được A/B đo (5 kênh/9 solver) ≠
  sản phẩm ship cho tài xế (1 solver S1). Đã vào PROJECT-GRAPH board + TODO của họ — tôn trọng,
  không sửa lại.

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| B1 TDD | đỏ trước (ImportError chứng minh bằng stash), 34 test liên quan xanh |
| Post-merge | ui/backend (45) + test_net_metric (3) + test_lifecycle_review_fixes (20) = **68 passed** (final review đính chính: 47→45) |
| Bảo toàn | không revert dòng nào của teammate; ui/README chỉ THÊM khối; 2 README audit lịch sử giữ nguyên câu gốc |
| Chưa kiểm | full suite sau merge (docs-only + B1 đã test đích danh — chạy ở lượt kế); review độc lập T1/T2/B1 (reviewer chết session-limit — controller tự đối chiếu brief↔diff, ghi nhận đây là REVIEW YẾU HƠN chuẩn SDD) |

## Visual verification

`NOT_APPLICABLE` — docs + metric mới (không đổi hành vi sim; B1 có test exact-repeat +
payout-không-đổi). UI contract đổi `maximum` là siết validation, không đổi render.

## Adversarial self-review / flaws found

1. Reviewer độc lập cho T1/T2/B1 **chưa chạy** (session limit) — tự review của controller
   không thay thế được; nếu Cường muốn, chạy lại 3 reviewer sau 11:30.
2. Graph addendum sinh bởi reader agents — controller đã đối chiếu xác suất (node 090/091
  và correction chain khớp file thật) nhưng CHƯA đối chiếu từng edge của 19 node.
3. TODO đánh số lặp 8→9→7 (mục audit) chưa sửa — cosmetic, ghi lại đây.
4. `.superpowers/` gitignored — ledger/brief không vào git; bằng chứng SDD chỉ còn local.

## Bổ sung sau REVIEW CHUẨN SDD (2026-07-29 trưa — đóng flaws #1/#3 ở trên)

Cường yêu cầu *"review chuẩn SDD"* sau khi quota reset — đã chạy đủ vòng:

- **3 task reviewer độc lập** (flaw #1 ĐÓNG): T2 **Approved** (kiểm máy móc câu gốc, số truy
  tận nguồn, tự chạy test 45 passed) · B1 **Needs-fixes** → fixer `b251d6e` giết 2 mutation
  sống sót (per-archetype `net_mean` + `cost_mean_all`, có bằng chứng đỏ→restore→xanh) ·
  T1 **Needs-fixes** (4 Important: nhầm Q-07/Q-05, đánh số TODO — flaw #3 ĐÓNG, DIRECTIVES
  §9 lỡ xoá câu gốc, mâu thuẫn R1/R4 do brief) → fixer `370bbec` xử 7/7.
- **Re-review 2 fix: cả hai Approved** (bằng chứng độc lập từng mục).
- **Final whole-branch review (999cdf9..HEAD): NOT-READY → sửa → READY.** Chốt chặn duy
  nhất: validation §9 PROJECT-GRAPH FAIL vì UPDATE-093 chưa có link trong graph — đã thêm
  row §3.7 + marker đính chính row 091 (trạng thái `DOING` của UPDATE-092 rà tại `66268cc`
  đã lỗi thời) + khôi phục provenance khung giờ peak gốc ở world-parameters + 3 đính chính
  số nhỏ (45 test backend, 87 UPDATE, OPEN-THREADS B1 ✅). Validation §9 chạy lại: xem
  commit — `PROJECT_GRAPH_VALIDATION_OK`. Test cuối của final reviewer: **68 passed**.

## ⏳ Nhắc PENDING-REVIEW

V-01..V-17 ("hỏi lại sau") · Q-03 · Q-04 · Q-07 · BUG-MOCKGEN-CLI · **ĐA-05 code chờ verdict
(UPDATE-091)** · UPDATE-092 board: B6-PARITY cần Cường xếp ưu tiên · kế tiếp theo plan:
**B2 C1 hệ số 0 → B3 policy costs** (cần đo 30–100 seed) · format_checker fix qua plan mode.
