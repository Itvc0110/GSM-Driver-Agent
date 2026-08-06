# UPDATE-151 — Review toàn diện advisor bằng 21 agent (7 reader · 3 debate · 10 phản biện + 1 trọng tài)

- **Ngày:** 2026-08-05
- **Loại:** research (0 dòng code) — theo chỉ thị Cường *"review lại phần advisors, cải thiện để đem lại kết quả tốt hơn"*
- **Evidence:** `research/audit/2026-08-05-advisor-review/r01..r23.json` (kết quả THÔ từng agent, mỗi claim kèm file:line)
- **Quota:** lượt 1 sập session-limit (2/18 agent) → ghi QUOTA-BLOCKED, retry đúng MỘT lần theo CLAUDE.md §3.5 khi Cường ra lệnh → 21/21 xong, 0 lỗi. Vòng phản biện: **9/10 finding CAO đứng vững, 1 BỊ BÁC** (r22: đường WAIT→GO_SWAP đã tồn tại qua shift_plan — claim "không có choice point chủ động" chỉ đọc nhánh bản năng).

## Kết quả chính (chi tiết + bằng chứng trong r*.json)

1. **3 bug CÔNG THỨC sev CAO trong kênh** (r10): ADV-01 S2 DP floor điểm mỗi bucket ⇒ mốc thưởng ngày gần như không lái được lịch; ADV-02 `shift_extend` không so `need_min` với thời gian ca CÒN LẠI ⇒ kéo ca vô ích; ADV-03 lan can `would_exceed_fatigue` đo mệt tại-lúc-khuyên thay vì dự phóng cuối ca. +9 finding TB/THẤP (ADV-04 baseline không tín dụng nghỉ ⇒ delta S2 thổi phồng; ADV-05 S1 coi lịch sử 0.0 là thiếu dữ liệu; ADV-06 kênh tắt không trơ về event stream; ADV-07 gate parse chuỗi tiếng Việt; ADV-08 kế toán phút hoãn phóng đại tới 59′/lần; ADV-09 count_supply đếm đôi…).
2. **Đo per-archetype** (r07): toán ĐÚNG (mean không chọn lọc, bootstrap theo seed) nhưng (F1-CAO) **CLI run_parallel CRASH** khi in ladder (KeyError trên `n_actors_scope`) ⇒ số P1..P7 hiện không in ra được; (F2-CAO) coverage mặc định `single` pha loãng Δ per-archetype ~1/k; (F3) `n_insufficient` so hằng 30; (F5) 14 cổng hai chiều không hiệu chỉnh đa kiểm định; (F6) `xveto_*`/`commit_*` lọt significance HAI CHIỀU — lỗ Goodhart; công suất: P3 cần ~500 seed, P2 ~150 để ngang all-cohort@30.
3. **UI nhắc tiêu cực thu nhập** (r06): ĐÃ có cảnh báo acceptance/completion dưới ngưỡng (S1); **THIẾU-CAO**: cảnh báo PHÒNG NGỪA "sát ngưỡng" — S1 đã tính sẵn `acceptance_cliff` mà adapter vứt bỏ; SOC pill hardcode 25 ≠ engine 20 (họ D-M3-17); S8 penalty có solver+template nhưng không nối recap; backend không expose ngưỡng nào.
4. **Pin swap-vs-charge** (r03, verify đứng): cross-fleet là **vô nghĩa vật lý** (pack 1,5 vs 3,5 kWh); bản khả thi = "đổi pin SỚM trước giờ đỉnh" trong đội swap (rule so thời gian, không cần solver mới); **2 nhóm cứng che**: fleet confound 100% với archetype, `charge_min` lưỡng đỉnh (mean vô nghĩa), phía TIỀN chưa mô hình (swap_fee=0 và điện=0) ⇒ **mọi metric pin phải báo THEO FLEET**.
5. **Arm oracle-adherence** (r04): chưa có; đường rẻ nhất = override `advice.adherence_by_archetype={P1..P7:1.0}` trên **cfg GỐC** (bẫy ORACLE-03: override chỉ ở arm B ⇒ cổng |z|>4 treo oan); coin sha256 không tiêu RNG; so oracle-vs-realistic là biến-thể-vs-biến-thể ⇒ cần 100 seed + caveat D-SIM-K3.
6. **8 hướng mở rộng kênh** (r05, neo action+solver có sẵn): CAO = E-01 station-choice (cần verdict D-004b), E-02 meal-timing (tái dùng commit gate), E-03 charge-timing chủ động; TB = E-04 shift-start, **E-05 end-shift theo giá trị biên (RẺ NHẤT — đường thi hành ĐÃ NỐI SẴN)**, E-06 weekly pacing, E-07 zone-rotation (cần verdict D-004); THẤP = E-08.
7. **Bug ngoài kênh** (r08): fixable-ngay = probe spy sai chữ ký · `n_insufficient` · `format_checker` thiếu (timestamp rác lọt 15 schema) · mockgen CLI crash · nhãn MOCK cho SOC proxy trên UI (T-045e — vi phạm §5); cần-thiết-kế = B6-PARITY (UI ship **1/9 solver**) · T-045c (haversine bỏ oan 8,3% đơn) · D-A3-01b (NO-OP đếm followed) · D-QD4-05+D-M3-19 (chờ Cường).
8. **Lọc test — phán quyết trọng tài** (r13, sau khi BÊN CẮT tự ĐO 800s/28 file): **không BO trắng file nào**; BÁC toàn bộ nhánh "hạ xuống nightly" (CI chưa active — hạ = xoá lặng lẽ); DUYỆT: conftest cache session-scoped (3 điều kiện cứng: cache deepcopy/frozen · cặp determinism giữ ≥1 run TƯƠI · `test_parallel_worlds` NGOÀI cache) + dedupe trong-file theo danh sách + bundle realdata ⇒ tiết kiệm **~3,5–5 phút/lượt suite**, thêm 3–4′ khi CI bật.
9. **Deferred triage** (r09): 3 hàng TODO stale (FIX/FIX-PRE/D-M3-06 đã xong); D-M3-07 "2 lỗi sửa ngay" đã hết hiệu lực một nửa (topic default đã fix; `budget_mode` chưa tồn tại trong code).

## Adversarial self-review

- 1/10 claim CAO bị vòng phản biện bác (đã ghi trên) — đúng tỷ lệ lịch sử ~1/4-1/10 finding soi là sai; các claim còn lại đều được verify ĐỘC LẬP đọc lại file:line.
- Chưa kiểm: các finding TB/THẤP **chưa qua phản biện** (chỉ CAO được verify) — khi thi công từng cái phải tự reproduce trước, đúng root-cause protocol.
- Số phút tiết kiệm suite là ƯỚC LƯỢNG của trọng tài từ phép đo mẫu của bên cắt.

## Follow-up

Kế hoạch thi công theo đợt trình Cường qua plan mode ngay sau update này (E1 bug → E2 đo oracle/per-archetype → E3 UI → E4 kênh mới → E5 test).
