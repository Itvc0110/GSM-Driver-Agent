# UPDATE-031 — Research refresh đợt 3: policy 2026 (khoán tuần, bỏ phạt ≤70%) + đồng bộ docs liên quan

- **Ngày:** 2026-07-24
- **Người thực hiện:** AI agent (yêu cầu Cường: "research vòng nữa, tìm flaw, fill/enrich" + "xem phần nào bị ảnh hưởng, sửa tất cả phần liên quan")
- **Loại:** research + docs
- **TODO / User story liên quan:** T-001/T-012 (research), T-004 (corpus gap), T-038/T-039 (schema/model expansion); US-F0-03, US-F3-02, US-F2-04

## Tóm tắt

Vòng web research mới (2026-07-24) phát hiện research policy đợt 1/2 (dated 2026-07-20) **lỗi thời & thiếu** ở một thay đổi lớn: **Vận Doanh 23/02/2026 BỎ phạt tỷ lệ nhận/hoàn thành ≤70%**, chuyển sang **khoán tuần + truy thu 20% (HN/HCM tới 40%)**. Tạo file refresh + đồng bộ mọi docs bị ảnh hưởng (research/personas/user-stories/spec) và **flag các gap code (schema/solver/mock/corpus) vào DEFERRED cho cycle plan riêng** — không sửa code sản phẩm ở cycle này.

## Chi tiết cập nhật

Tìm & xác minh trên greensm.com (fetch trực tiếp): (1) Vận Doanh 23/02/2026 toàn quốc — khoán tuần, "không xử phạt khi tỷ lệ nhận/hoàn thành ≤70%", truy thu 20%; (2) Vận Doanh HN/HCM 04/05/2026 — clawback "tới 40%"; (3) **mâu thuẫn**: Bộ QTƯX 05/06/2026 (ngày SAU) vẫn liệt kê phạt <70% Nhóm 4 → chưa reconcile; (4) chia sẻ doanh số **75%** là hiện hành (02/03/2026), "91%" là số 2024 HCM lỗi thời; (5) điểm có chiều **service_type** (5-10-15-20-30) ngoài peak/normal 10/5; (6) số khoán/mốc điểm mới **image-locked** → giải bằng data thật GSM.

Impact audit toàn repo (grep research/src/schemas + đọc USER_STORIES/spec §1.7/income-structure): USER_STORIES và PERSONAS **vốn đã version-aware** (không hard-code phạt) → chỉ thêm ghi chú, không rewrite. `PayoutLedger.kind` đã có `deduction`+`week_bonus` → clawback map được vào schema hiện có; nhưng **solver S1/S2 chưa mô hình khoán-tuần/clawback** (model gap) và `policy_bundle.points` thiếu `service_type` (schema gap).

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `research/policy/policy-refresh-2026-07-24.md` | tạo | Refresh đầy đủ + timeline version + image-locked list |
| `research/00_SUMMARY.md` | sửa | Banner đính chính + pointer refresh |
| `research/policy/bonus-programs.md` | sửa | Banner: phạt <70% superseded |
| `research/community/pain-points.md` | sửa | Pain #3 reframe (eligibility, không phạt) |
| `research/economics/income-structure.md` | sửa | Daily→weekly + clawback là deduction; gap#3 update |
| `planning/PERSONAS.md` | sửa | Ghi chú risk-framing (không rewrite cell — vốn version-aware) |
| `planning/USER_STORIES.md` | sửa | Ghi chú F3 threshold = eligibility |
| `specs/core-data-schema-and-advisor-architecture.md` | sửa | §1.7: pain #3 đổi bản chất + model/schema gap (T-039) |
| `tracking/DEFERRED.md` | sửa | +D-POL-01..05 (model/schema/mock/corpus/image-locked gaps) |
| `tracking/updates/UPDATE-031-*.md` | tạo | file này |
| **KHÔNG đụng** `research/policy/t004-*.json` (Khánh), `src/gsm_core/**` | — | corpus gap → D-POL-04 cho owner |

## Docs đã cập nhật kèm theo

SCOPE: không đổi. TODO: thêm mục research đợt 3. DEFERRED: +D-POL-01..05. USER_STORIES/PERSONAS/spec: ghi chú (trên).

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| Vận Doanh 23/02/2026 bỏ phạt ≤70% + khoán tuần + truy thu 20% | `FACT` (official) | greensm.com fetch 2026-07-24 | Cao | F0 vẫn nói phạt → sai |
| HN/HCM clawback "tới 40%" | `FACT` (official, image-partial) | greensm.com 04/05/2026 | TB | clawback_rate model sai mức |
| Mâu thuẫn 23/02 vs 05/06 (phạt) chưa reconcile | `OBSERVED` (2 official) | 2 URL greensm.com | Cao | F0 phải hedge; cần data thật |
| Chia sẻ 75% hiện hành; 91% lỗi thời | `FACT` | greensm.com 02/03/2026 | Cao | dùng nhầm 91% |
| Số khoán tuần/mốc điểm mới | `image-locked / TBD` | ảnh official | — | phải pull data thật, không đoán |
| PERSONAS/USER_STORIES version-safe | `OBSERVED-CODE` | đọc file | Cao | — |

## Kiểm chứng

Mỗi con số cross-check ≥1 URL official + effective date (bảng timeline trong file refresh). Fetch trực tiếp 4 trang greensm.com (vận-doanh, QTƯX, thêm-mốc-điểm, thu-nhập). Docs-only → **không chạy test code** (không đụng `src/`); full suite không đổi (162 từ UPDATE-030). **Chưa kiểm chứng:** số image-locked (khoán tuần tối thiểu, clawback active theo market, bảng mốc mới) — để TBD, cần data thật GSM; reconcile mâu thuẫn phạt cần bản policy active của driver thật.

### Seeds và scenarios

| Run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| WebFetch greensm.com ×4 | trích text policy hiện hành | số trong ảnh |
| grep impact audit research/src/schemas | 14+19+8 file chạm khái niệm liên quan | — |

## Visual verification

- **Status:** `NOT_APPLICABLE` — research/docs, không simulator/UI.

## Adversarial self-review / flaws found

1. **Trông đúng nhưng có thể sai:** kết luận "bỏ phạt <70%" dựa 1 trang vận-doanh; nhưng QTƯX 05/06 (SAU) vẫn ghi phạt → **KHÔNG kết luận tuyệt đối**, đã đóng khung là "mâu thuẫn cần data thật", F0 phải hedge. Không tự "sửa" corpus theo phía nào.
2. **Freshness:** research vẫn có thể sót policy sau 05/06/2026 (hôm nay 24/07); các số quan trọng image-locked → chủ động đẩy sang data thật thay vì đoán.
3. **Không over-reach:** KHÔNG sửa schema/solver/mock/corpus (chỉ flag) — tránh đổi contract/số tài chính ngoài cycle plan; giữ ranh giới §5 (agent không tự tạo số policy).
4. **Ownership:** không đụng corpus T-004 của Khánh (D-POL-04 để owner xử lý).
5. **Flaw còn mở → map:** D-POL-01..05.

## Expansion checkpoint (T-039)

1. **Schema:** `policy_bundle.points`+service_type; `weekly_quota`/`clawback_rate` versioned; review `forced_accept_below`. (D-POL-02)
2. **Bài toán tối ưu:** "gap tới khoán tuần (VND/tuần) + tránh clawback" = **bài toán feasibility mới** gần S1 nhưng đơn vị doanh số tuần — ứng viên solver mới/mở rộng S1. (D-POL-01)
3. **Tính năng:** F0 cảnh báo "chính sách vừa đổi: phạt→khoán tuần" đúng US-F0-03 (cần corpus có version); F3 đổi cảnh báo "sát ngưỡng phạt" → "tiến độ khoán tuần + eligibility thưởng".

## Follow-up / defer phát sinh

- D-POL-01 (MODEL, sev cao), D-POL-02 (SCHEMA, sev TB), D-POL-03 (MOCK regen), D-POL-04 (CORPUS — owner Khánh, sev cao F0), D-POL-05 (image-locked → data thật). Mỗi cái = cycle plan riêng khi mở.
- C7 harness (kế hoạch trước) **tạm dừng**: nên chạy SAU khi nền policy này ổn (eval set F0 phải phản ánh policy hiện hành, không dạy phạt cũ).
