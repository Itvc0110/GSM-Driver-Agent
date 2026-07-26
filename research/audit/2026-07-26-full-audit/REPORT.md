# AUDIT TOÀN HỆ THỐNG — BÁO CÁO TỔNG (A1 · A2 · A3)

Ngày: 2026-07-26 → 27 · Chỉ thị Cường: *"check lại toàn bộ data, hệ thống agent, math modelling
(quan trọng nhất)"* · Quy mô: **152 agent** (A1 87 + verify-11 + A3 54), ~10.2M token subagent.
Dữ liệu thô: `a1_math_findings.json` · `a1_verify11_verdicts.json` · `a3_agent_findings.json`.

## 0. Kết quả một dòng

**168 finding** qua find→refute đối kháng: **118 CONFIRMED** (13 CAO), 0 refuted khi có repro,
**16 lỗi hẹp ĐÃ FIX** kèm regression test đỏ-trước (UPDATE-065/066/069/070), phần còn lại là
3 đề án MODEL GAP + 9 câu hỏi thiết kế chờ Cường chốt.

| Đợt | Phạm vi | Finding | CONFIRMED | CAO | Đã fix |
|---|---|---|---|---|---|
| A1 | 9 solver · estimator · behavior/demand/physics/rating · statistics | 110 | 72 | 13 | 12 |
| A2 | 13 bảng mock · gate schema · nhãn nguồn · F-U2-A | — | — | — | gate mở rộng (5 test) |
| A3 | verifier · pipeline · router/KB · layer outputs · bridge · memory · cadence · time | 69 | 46 | 6 | 4 |

## 1. Những lỗi NẶNG nhất (đã fix, có repro + test)

1. **FAIL-OPEN của pipeline** (A3 FAILCLOSED-1): verify hỏng lần 2 vẫn TRẢ message chưa kiểm cho
   tài xế — giả định "template pass by construction" sai. **Bằng chứng sống**: sau khi thêm
   fail-closed, integration test 3×4 lộ ngay một case thật rơi vào `R6_verify_fail` (số trần lọt
   từ câu infeasible) — tức trước đây case đó đã đi thẳng ra ngoài.
2. **Verifier defuse được bằng từ vô hại** (VBYPASS-3): "Ứng dụng này chắc chắn giúp anh kiếm
   được nhiều hơn" LỌT vì "dung" (trong *ứng dụng*) nằm trong tập phủ định, match substring.
   → phủ định nay phải là token nguyên, chi phối trực tiếp, không qua dấu ngắt câu; test 2 chiều
   (4 câu hứa phải bị bắt · 3 disclaimer thật phải tiếp tục pass).
3. **S2 đọc forecast sai cấu trúc** (S2-2): producer sinh 1 dòng/cell/bucket, solver đọc theo
   INDEX ⇒ demand lệch giờ, mất bucket cuối, **E[payout] sai ~×2**.
4. **Hứa thưởng khi chính sách sẽ trả 0** (S1-1 + S2-3): cả S1 lẫn DP terminal đều cộng thưởng
   mà không xét ngưỡng acceptance/completion.
5. **Rò tương lai** hai chỗ: tuần (S5-1) và **trong ngày** (LAYEROUT-4: 08:00 đã tính điểm cả
   ngày ⇒ "đã đạt mốc cao nhất" lúc sáng sớm).
6. **Ngưỡng chính sách bị in thành tỷ lệ tài xế** (LAYEROUT-1): tolerance 0.5 tuyệt đối cho unit
   `ratio` ⇒ "mức tối thiểu 74%" (thật là 85%).
7. **Dashboard chạy kinh tế học cũ** (BEHAV-2): slider hardcode 6000 trong khi config 21200 —
   mọi lần Cường chỉnh tham số trên dashboard đều chạy baseline SIM-1.
8. **Thống kê tự phong** (STATS-5 + STATS-1): `significant` bật cả khi n=1; `/ab` phán "✅ ổn"
   trên 1 seed với ngưỡng bịa. Nay: cần n≥30, và endpoint 1-seed trả `ok=null`.

## 2. Trả lời trực tiếp các câu hỏi của Cường (A3)

**"Output từng layer + cách AI nói với tài xế"** — chạy pipeline thật và đọc như tài xế: câu mở
đầu F1 là digest máy ("bucket", "E[payout]"); F3 tự mâu thuẫn ("không có gì cần chỉnh" rồi báo
thiếu điểm); hai loại "mốc thưởng" đứng cạnh nhau không giải thích; caveats solver bị vứt.
→ 3 lỗi số/logic đã fix; phần giọng văn vào R-list (LAYEROUT-3/6/7/11/12).

**"Pipeline convert output → action của actor"** — đo thật: `consult()` gọi **9.065-9.536
lần/ngày**, coin adherence rút lại mỗi tick tới khi "thành công" (**CADENCE-2 washout**: adherence
danh nghĩa 0.3 nhưng hiệu dụng ≈1.0); 41/70 "followed" là advice NO-OP (ONLINE→None) ⇒ **con số
adherence trong mọi kết luận A/B đang bị thổi**. Chỉ 3/9 solver có kênh tác động thật.

**"Core dùng memory/former states đúng chưa"** — `completion_hist` ghi mà **chết** (S1 vẫn nhận
1.0 đầu ca); EpisodeStore **write-only** (cột shown/accepted không ai ghi); ba nơi lưu trạng thái
advice không join được (episode uuid · UI jsonl · sim events) ⇒ vòng adherence §12 đang HỞ.

**"Khi nào đưa advice"** — **không tồn tại một định nghĩa**: sim (4 trigger, 21 advice/ca, có lúc
2 advice cùng phút), UI (giờ đồng hồ cố định 9h/14h/21h30 — lệch pha ca thật tới 5 giờ), §12 (pha
ca). ⇒ đề án **AdviceCadencePolicy** dùng chung (anchor theo pha ca + priority + cooldown).

**"Time engineering đủ tốt chưa"** — verdict: **nền TỐT** (DES phút-liên-tục, censor tường minh,
CRN-safe), nhưng: idle có **hai nguồn sự thật** lệch nhau, hoạt động bị censor cuối ngày bị dán
nhãn "idle", `time.warmup_min` là knob chết, multiday không có day-of-week (chặn khoán tuần).

## 3. Đề án chờ Cường duyệt (không tự cài)

- **ĐA-01 shrinkage estimator** (D-SIM-18): refuter đã kiểm toán học + repro (P(raw<ngưỡng|n=5,
  p=0.9)=0.41 → shrunk 0.08). Lưu ý khi duyệt: prior phải là **pooled counts**, và `m` ảnh hưởng
  advice "cứu ngày xui" ⇒ calibrate sweep 30 seed.
- **ĐA-02 knapsack biết cửa sổ giờ** (S6-1/2/3) — B1 hẹp làm ngay được sau duyệt; B2 chờ policy
  đếm thật của GSM (D-POL-05).
- **ĐA-03 gói S2 còn lại**: p_accept/avg_dist cá nhân hoá (đường tham số đã mở, call site chưa truyền).
- **ĐA-04 (mới, từ A3) AdviceCadencePolicy** + **ĐA-05 hợp nhất store adherence** + **ĐA-06 một
  giọng nói** (template trả list[card] theo `advice.json` thay vì blob, thống nhất xưng hô).

## 4. Giới hạn trung thực của audit này

- Refuter xác nhận gần như mọi finding (0 refuted có repro) — vẫn mang rủi ro thiên vị xác nhận;
  mọi fix đều được TÔI đọc code + viết test đỏ-trước, không fix theo lời agent.
- Không phủ: LLM live path đo thực nghiệm (chỉ đọc code), hiệu năng, bảo mật, Flutter của Khánh.
- Mỗi finder tự khai phần không kiểm được — xem trường `coverage` trong 2 file JSON.
