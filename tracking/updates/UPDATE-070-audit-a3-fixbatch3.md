# UPDATE-070 — AUDIT A3 (agent-system) + fix batch 3: 5 lỗi CAO, trong đó có FAIL-OPEN

Ngày: 2026-07-27 · Track: AUDIT · Workflow A3: **54 agent** (8 finder + refuter từng finding),
3.7M token. Kết quả thô: `research/audit/2026-07-26-full-audit/a3_agent_findings.json`
(46 CONFIRMED · 23 design/thấp). Report tổng: `.../REPORT.md`.

## 1. Fix đã vào (5, mỗi cái regression test đỏ-trước)

| ID | Bản chất | Fix |
|---|---|---|
| **FAILCLOSED-1 (CAO)** | Pipeline **FAIL-OPEN**: verify hỏng lần 2 vẫn trả message chưa kiểm cho tài xế ("template pass by construction" là giả định sai) | `AdvisorPipeline.safe_degrade()` — hạ về thông báo an toàn KHÔNG số, `residual_path=R6_verify_fail`, giữ verify_errors; schema thêm R6 |
| **VBYPASS-3 (CAO)** | Cửa sổ phủ định 15 ký tự **substring** → "Ứng dụng này chắc chắn giúp anh kiếm được nhiều hơn" LỌT ("dung" ⊂ "ứng dụng") | Phủ định phải là TOKEN nguyên + chi phối trực tiếp (regex `\b(...)\b[^,.;:!?]{0,12}$`), bỏ "dung" |
| **LAYEROUT-1 (CAO)** | `_vn` tolerance 0.5 tuyệt đối cho unit `ratio` ⇒ ngưỡng 0.85 render thành 74% ("mức tối thiểu 74%" — sai chính sách) | Tolerance THEO UNIT (`ratio` 0.005) + chọn entry GẦN NHẤT |
| **LAYEROUT-2 (CAO)** | Template hứa "còn thiếu X để đạt mốc" trong khi S1 kết luận INFEASIBLE | `_gap_sentence()`: rẽ nhánh feasible / infeasible (nói thật + lý do theo **constraints**, không chèn chuỗi thô) / already_maxed |
| **LAYEROUT-4 (CAO)** | View l1r gộp TRỌN NGÀY ⇒ 08:00 sáng đã "đạt mốc thưởng cao nhất" (rò tương lai trong ngày) | Cắt `complete_time <= t_now` — khớp với UI adapter vốn đã đúng |

**Bằng chứng fail-open là THẬT**: ngay khi bật fail-closed, `test_advisor_integration` (3 driver ×
4 feature) lộ một case rơi vào `R6_verify_fail` — số trần lọt từ câu infeasible tôi vừa viết.
Tôi sửa tiếp câu đó (diễn giải bằng nhãn constraints thay vì chuỗi lý do có số) → verify pass.
Trước đây case tương tự đã đi thẳng ra ngoài mà không ai biết.

## 2. Tests

`tests/test_audit_a3_fixes.py` (TẠO, **12 test**): 4 test lỗi CAO + 8 test **hai chiều** cho
negation (4 câu hứa phải BỊ BẮT · 3 disclaimer thật phải TIẾP TỤC PASS · 1 control).
Đỏ 4/4 trước fix. Suite advisor liên quan: 93→**110 passed** sau khi thêm.

## 3. A3 trả lời 4 câu hỏi Cường (chi tiết trong REPORT §2)

- **Layer outputs/giọng nói**: 3 lỗi số đã fix; 5 vấn đề giọng văn → D-A3-05 / ĐA-06.
- **Bridge → action**: `consult()` **9.065-9.536 lần/ngày**; **adherence washout** (coin re-roll
  mỗi tick ⇒ 0.3 hiệu dụng ≈1.0) + 41/70 "followed" là NO-OP ⇒ **số adherence đang bị thổi** (D-A3-01, CAO).
- **Memory**: `completion_hist` chết; EpisodeStore write-only; 3 store không join được (D-A3-02/04).
- **Cadence**: không có MỘT định nghĩa (sim 4 trigger vs UI giờ cố định vs §12 pha ca) → ĐA-04.
- **Time**: nền TỐT; 3 lỗi kế toán thời gian (D-A3-03).

## 4. Kiểm chứng

- Batch 2 (UPDATE-069) full suite: **519 passed, 4 skipped**. Batch 3 chạy sau khi thêm 12 test
  — số ghi trong commit message KHÔNG có (quy tắc), đọc ở đây sau khi suite xong.
- `ui/backend/tests`: 23 passed (không đụng). R5 spot-check UX-CARDS: nudge chặn khi đang lái ✓,
  cước demo không chạm payout ✓, mọi số card từ API ✓ (+ thêm guard recap khi hồ sơ chưa tải).

## 5. Chờ Cường

**6 đề án ĐA-01..06** (PENDING-REVIEW) — không tự cài. **D-A3-01..06** trong DEFERRED.

---
**⏳ PENDING-REVIEW:** V-01..V-09 · **V-10** · Q-03 · **ĐA-01..ĐA-06**.
