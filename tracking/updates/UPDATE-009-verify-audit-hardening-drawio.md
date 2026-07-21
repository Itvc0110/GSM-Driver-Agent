# UPDATE-009 — Verify A13/heatmap, red-team audit hardening, drawio v2 trang SIM

- **Ngày:** 2026-07-21
- **Người thực hiện:** AI agent (Claude Code), theo 3 yêu cầu của Cường (1: verify kỹ T-023 + điều kiện advice khu vực; 2: audit bắt flaw/gap/vague; 3: cập nhật drawio + rà thêm) — thực thi theo approve tổng ("mọi quyết định thiết kế")
- **Loại:** research-verify / spec-hardening / diagram
- **TODO liên quan:** T-023 (DONE có verdict), T-018/T-019/T-020 (spec hardened), D-009/D-010 (mới)

## Tóm tắt

(1) Verify chuyên sâu: **A13 "Đăng ký Ca Làm Việc" = UNVERIFIED** (nguồn duy nhất là trang AI-generated; không dấu vết official/báo chí/diễn đàn sau 3,5 tháng; dangkyxanhsm.vn kiểm search nội bộ không có bài); **Xanh KHÔNG có heatmap demand cho tài xế** (Grab có, Be không) và không ràng buộc khu vực realtime → **advice khu vực theo heatmap mock = tính năng BỔ SUNG, không chồng đè** → mở CÓ ĐIỀU KIỆN với 5 điều kiện an toàn. Phát hiện thêm tính năng official "Danh sách chuyến hẹn giờ" (A14). (2) Red-team audit trả 11 flaws + 8 gaps + 10 vague + 7 insights → vá bằng 2 spec mới + DoD tách 2 tầng + harmonize toàn bộ mâu thuẫn số liệu. (3) Drawio v2 thêm trang 8 "SIM — Twin-world 3 arm" + cập nhật F2; validate PASS 8 trang.

## Chi tiết cập nhật

### Verify (yêu cầu 1)

- `research/simulation/action-space.md`: A13 verdict UNVERIFIED + bằng chứng; thêm A14 "Danh sách chuyến hẹn giờ" (advisor được nhắc xem — không tự đề xuất chuyến); §Phạm vi advisor viết lại: advice khu vực mở CÓ ĐIỀU KIỆN (5 điều kiện: chỉ giữa cuốc/trước ca · cảnh báo tỷ lệ nhận · capacity-aware · nhãn mock + không hứa thu nhập · shift-aware flag OFF).
- `planning/SCOPE.md` F2 + `planning/USER_STORIES.md` US-F2-04 (mới): phản ánh ranh giới mở.
- `tracking/TODO.md` T-023 DONE kèm verdict; follow-up kiểm changelog in-app → T-013.

### Audit hardening (yêu cầu 2) — vá theo bảng ưu tiên BLOCKER của audit

- **`specs/sim-policy-bundle-v0.md` (MỚI — vá F1/F2/G3/G6)**: fare 13k+4.3k/km MOCK; share 75% flat (snapshot 02/03/2026); điểm 10/5 theo giờ ĐẶT; **mốc thưởng NGÀY mock = tuần÷7** (60/100/160/200đ → 30k/60k/115k/170k) + điều kiện ≥85%/85%; kỷ luật = cờ trong run 1 ngày; chi phí per track (thuê RTO 60k/ngày, sạc ~10k, đổi pin 0đ/9k); đội xe P2/P4 swap 100%, P1 sạc cắm, P3/P5 50/50; assumption log PB1–PB5.
- **`specs/advisor-optimization-layer-a.md` (MỚI — vá F8 + G1/G4/G5 + F3/F4/F5/F6/F7)**: behavior model B-arm functional form (utilities, Ê kinh nghiệm cá nhân với σ_arch định lượng P4 0.6→P3 0.1, acceptance logistic, chọn trạm quen p=0.7, battery_stranded event); DP lớp A trên (bucket×SOC-band×state) với pseudocode + tie-break deterministic; `advisor_information ∈ {oracle, product_proxy}` (headline = product_proxy, station state trễ 5ph); `advice_scope ∈ {product_only, sim_extended}` (ablation bắt buộc — tách hiệu quả từ đòn bẩy product không có); arm C định nghĩa lại (cùng trigger engine, content random-safe, chấp nhận Δ âm); adherence sweep {0/default/100%} vào DoD; divergence index vào event log; proximal outcome 90ph; §4 harmonize chốt: run window 05–24h + warm-up 1h, orders renormalize trong window, tick field 15ph, N=50 pilot, UNSEEN = expire-khi-bận, zone weights res 9, **OD buffer ring k≤4**, runtime ước 600–900 runs (giờ-cấp, song song theo seed).
- **`specs/simulation-pilot-world.md`**: DoD tách **DoD-core (T-018)** vs **DoD-eval (T-019+T-020)** (vá F9); thêm tiền đề policy bundle + OD boundary.
- `tracking/DEFERRED.md`: D-009 (đa loại đơn Express/Ngon), D-010 (hàng đợi sau pilot: kịch bản tuần/trust, counterfactual branch, regime sweep, mất điện trạm, adoption 70%, res 8/N=500, ĐBTN).
- `tracking/TODO.md`: T-018 READY (audit-hardened), T-019/T-020 trỏ spec đủ để code.
- Các câu hỏi V1–V10 của audit: áp dụng default đề xuất theo approve tổng của Cường (V1 snapshot verify mới nhất; V2 mốc ngày; V3 có 2 scope; V4 cả hai, headline noisy; V5 random-safe; V6 window 05–24h; V7 buffer ring; V8 A13 loại khỏi pilot; V10 50/50). **V9 (ai claim T-018/019/020) — duy nhất còn chờ Cường/Khánh tự claim trong ASSIGNMENTS trước khi code.**

### Drawio (yêu cầu 3)

- Thêm **trang 8 "SIM — Twin-world 3 arm"**: SHARED (CRN/trace/dispatcher/policy bundle) → 3 arm A/B/C → phân lớp biến A/B/C → EVALUATOR (Δ 3 chiều, metrics 3 tầng, adherence twin-diff, sweep) → VIZ; note ranh giới sim-vs-product + nhãn MOCK.
- Trang F2: subtitle + node 3 + GUARDRAIL cập nhật advice khu vực có điều kiện (capacity-check, cảnh báo tỷ lệ nhận, không hứa thu nhập).
- Validate: XML parse PASS, 8 trang đúng tên, refs sạch, bounds trong canvas.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| specs/sim-policy-bundle-v0.md · specs/advisor-optimization-layer-a.md | tạo |
| specs/simulation-pilot-world.md (DoD 2 tầng) | sửa |
| research/simulation/action-space.md (A13 verdict, A14, phạm vi advisor) | sửa |
| flow image/GSM_Driver_Income_AI_Agentv2.drawio (trang SIM + F2) | sửa |
| planning/SCOPE.md (F2) · planning/USER_STORIES.md (US-F2-04) | sửa |
| tracking/TODO.md (T-018/019/020/023) · tracking/DEFERRED.md (D-009/D-010) | sửa |
| tracking/updates/UPDATE-009-...md | tạo |

## Kiểm chứng

- Verify A13: đa kênh (official site search nhiều biến thể, Play listing, báo chí, video, diễn đàn, search nội bộ dangkyxanhsm.vn); lỗ hổng duy nhất = changelog in-app 03–04/2026 (cần thiết bị thật — T-013).
- Drawio: parser UTF-8 PASS (8 trang, refs, bounds).
- CHƯA kiểm chứng: các default V1–V10 là quyết định thiết kế theo approve tổng — Cường có thể override từng cái; tham số behavior model/policy bundle là MOCK chờ calibration (T-021); runtime là ước lượng.

## Follow-up

- **Cường/Khánh claim T-018/T-019/T-020 trong ASSIGNMENTS trước khi code (V9 — theo CLAUDE.md §3).**
- Sau duyệt bản cập nhật này → vào plan mode implement T-018 (yêu cầu 3 của Cường đợt trước).
- Toàn bộ thay đổi UPDATE-007/008/009 chưa commit — commit khi Cường yêu cầu.
