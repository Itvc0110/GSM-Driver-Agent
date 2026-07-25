# UPDATE-045 — SIM-2 "Driver journey": hành trình chi tiết của MỘT tài xế

Ngày: 2026-07-25 · Track: **A (SIM overhaul)** · Phase: **SIM-2 / 5** · Người điều khiển agent: Cường
Spec: `specs/simulation/00-sim-overhaul-master.md` §5 · Chỉ thị: `tracking/DIRECTIVES-2026-07-24.md` §5.6
Tiếp nối: UPDATE-044 (SIM-1, commit `9de4074`)

## 1. Vì sao

Cường xếp phần này là **"ĐẶC BIỆT"**: *theo dõi hành trình 1 tài xế — mở đầu phiên làm việc, nhận
cuốc thật, tỷ lệ nhận/hoàn thành, hành vi random, **đo metric trên đúng driver đó***.

Khảo sát trước khi code cho thấy sim **đã có gần đủ nguyên liệu** (segments phủ enroute/on_trip/
rest/charge/relocate/deadhead; event `go_online`/`end_shift`; counter per-actor). Thiếu đúng **2 lỗ
visibility** và **1 nơi để xem**:

| Thiếu | Hệ quả |
|---|---|
| `order_declined` **không ghi lý do** | Không trả lời được *"vì sao tài xế từ chối cuốc NÀY?"* — đúng câu Cường muốn |
| Bỏ đơn vì pin yếu **không phát event** (chỉ tăng counter) | Tài xế "biến mất" khỏi thị trường một lúc mà timeline không giải thích được |
| `tab_actor` là bảng TỔNG HỢP mọi tài xế | Không có chỗ nào xem được hành trình của MỘT người |

⇒ Cycle này **không mổ engine**: bịt 2 lỗ visibility rồi **lắp ráp** journey từ nguồn sẵn có.

## 2. Đã làm gì

### A. `behavior.py` — quyết định nhận đơn GIẢI TRÌNH ĐƯỢC
`AcceptDecision(accepted, p_accept, net_vnd, z, reason)` + `decide_accept(...)`.
`reason` khi từ chối tách 2 loại **có ý nghĩa sản phẩm khác nhau**:
- `economics` — cuốc dưới trung vị thị trường (z < 0), tài xế chê xa/rẻ ⇒ **dư địa advisor**;
- `base_behavior` — cuốc bình thường/tốt nhưng vẫn rơi theo `accept_base` (mệt, sắp kết ca, tính
  kén) ⇒ **KHÔNG phải chuyện tiền**, advisor khuyên về tiền sẽ vô ích.

`accept_order()` giữ nguyên chữ ký, thành wrapper → không phá caller/test cũ.

### B. `world.py` — bịt 2 lỗ visibility
- `order_declined`: thêm `reason`, `net_vnd`, `pickup_km`, `gross_vnd`, `p_accept`.
- `order_matched`: thêm **cùng bộ số** ⇒ so sánh được cuốc NHẬN vs cuốc BỎ.
- Event mới **`order_skipped_soc`** (`soc_pct`, `need_km`).

### C. `journey.py` — MỚI (thuần lắp ráp, không mô phỏng lại)
`build_journey(result, actor_id) -> DriverJourney`: `sessions` · `timeline` (segment + **idle suy
ra từ khoảng trống**) · `offers` (mọi lần được chào đơn + lý do + kết cục) · `income_curve` ·
`metrics` per-driver. `journey_to_json()` export có nhãn MOCK (SIM-4 dùng lại).

Journey **đọc từ `RunResult`, không tính lại** ⇒ không thể lệch với engine.

### D. Dashboard — tab thứ 5 "🧭 Hành trình 1 tài xế"
Chọn tài xế (nhãn kèm archetype, vd `d-42 · P4 TÂN BINH · 14 cuốc`) → 5 metric · **Gantt timeline
theo phút** · thu nhập tích luỹ · thời gian đi đâu · **bảng từng offer có LÝ DO**.

## 3. Kết quả — journey kể được câu chuyện (seed 1000, tài xế tiêu biểu mỗi archetype)

| arch | nhận | cuốc | util | idle | payout | thưởng | %thưởng | từ chối vì |
|---|---|---|---|---|---|---|---|---|
| P1 part-time | 0.79 | 9 | 0.55 | 24ph | 116.317đ | **0đ** | 0% | KT 2 · TC 1 |
| P2 full-time | 0.93 | 24 | 0.48 | 138ph | 403.177đ | 60.000đ | 15% | KT 1 |
| P3 top | 0.95 | 18 | 0.27 | **378ph** | 285.046đ | 60.000đ | 21% | KT 1 |
| **P4 tân binh** | **0.79** | 14 | **0.34** | 148ph | **214.400đ** | **0đ** | 0% | **KT 4** |
| P5 lão làng | 0.96 | 20 | 0.44 | 104ph | 295.161đ | 30.000đ | 10% | — |
| P6 sáng sớm | 1.00 | 16 | 0.42 | 119ph | 239.039đ | 30.000đ | 13% | — |
| P7 tối-đêm | 0.90 | 19 | 0.41 | 138ph | 295.927đ | 30.000đ | 10% | KT 1 · TC 1 |

(KT = từ chối vì kinh tế · TC = vì tính cách/mệt)

**P4 tân binh là baseline advisor rõ ràng**: nhận thấp nhất (0.79), util thấp (0.34), payout thấp
nhất trong nhóm full-shift, và **4/4 lần từ chối đều vì KINH TẾ** — tức là có thể tư vấn được.

## 4. Files

| File | Hành động |
|---|---|
| `src/gsm_sim/behavior.py` | sửa — `AcceptDecision` + `decide_accept`; `accept_order` thành wrapper |
| `src/gsm_sim/world.py` | sửa — lý do decline, `order_skipped_soc`, chi tiết trên `order_matched` |
| `src/gsm_sim/journey.py` | **TẠO** |
| `src/gsm_sim/dashboard.py` | sửa — tab 5 "Hành trình 1 tài xế" |
| `tests/test_journey.py` | **TẠO** — 14 test |

## 5. Kiểm chứng

- **Full suite: 405 passed, 5 skipped** (trước 391).
- **RÀNG BUỘC CỨNG — KHÔNG làm trôi SIM-1:** ghi baseline `summarize()` + counter cho seed 42 và
  1000 **TRƯỚC** khi sửa, so lại **SAU** khi sửa → **giống hệt từng con số**. `decide_accept` tiêu
  đúng 1 `rng.random()` như bản cũ ⇒ chuỗi ngẫu nhiên không dịch, nền CRN cho SIM-4 còn nguyên.
- Bảo toàn (test trên **tài xế đại diện của cả 7 archetype**, không chỉ 1 người may mắn):
  offer = accept + decline + skip khớp `orders_offered`; timeline = độ dài phiên (lệch 0.000ph);
  không block chồng nhau; tiền tích luỹ khớp `actor.payout_vnd` và không giảm; cộng mọi driver ra
  đúng metric hệ thống.
- Determinism: cùng seed → journey giống hệt (journey không tiêu RNG).

## 6. Bug thật phát hiện & sửa trong cycle này

**BUG-SIM2-01 — `income_curve` bỏ sót THƯỞNG NGÀY.** Bản đầu chỉ cộng payout từng cuốc
(`on_trip` segment) ⇒ journey báo 343.177đ trong khi `actor.payout_vnd` = 403.177đ, **thiếu đúng
60.000đ**.
- Phát hiện bởi: `test_money_conserved` (không phải do đọc code — test bảo toàn bắt được).
- Root cause: `day_bonus` được cộng vào `payout_vnd` ở nhánh `end_shift` / `day_end_settle`, **không
  nằm trong cuốc nào**.
- Vì sao NGHIÊM TRỌNG với sản phẩm này: thưởng chiếm 20-30% thu nhập tài xế và **chính là thứ
  advisor tối ưu**. Một journey "đúng về cuốc nhưng thiếu thưởng" sẽ dẫn sai mọi kết luận A/B ở SIM-4.
- Fix: `_income_curve` cộng cả 2 nguồn, `metrics` tách `trip_payout_vnd` / `day_bonus_vnd` /
  `bonus_share`. Thêm test khoá riêng + chống vacuous (bắt buộc có tài xế thực sự nhận thưởng).

## 7. Adversarial self-review / flaws found

1. **Trôi RNG** — rủi ro số 1 của cycle này (refactor đúng chỗ rút số ngẫu nhiên). Đã chặn bằng
   so baseline trước/sau, không phải bằng suy luận. ✅
2. **Idle suy ra, không phải sim ghi** — dễ sai nhất. Đã khoá bằng bảo toàn thời gian + chống
   chồng lấn trên cả 7 archetype. ✅
3. **Journey tính lại số thay vì đọc engine** — đã tránh: mọi số lấy từ `RunResult`/`Actor`. ✅
4. **Vacuous test** — `test_day_bonus_included_in_income` có thể xanh giả nếu KHÔNG ai nhận thưởng;
   đã thêm assert bắt buộc tồn tại thưởng > 0. ✅
5. **Nhãn MOCK** — export có `source: MOCK` + manifest; tab dashboard ghi rõ MOCK. ✅

**FLAW / MODEL GAP ghi nhận (không che):**

- **F-SIM2-A (TRUNG BÌNH → SIM-4) — tài xế mới nhận thưởng 0đ, TRÁI với thực tế.** Đo được: P4
  (tân binh) và P1 (part-time) đều `day_bonus = 0` vì không đủ điểm chạm mốc. Nhưng Cường nói rõ
  *"hồ sơ mới cũng có nhiều thưởng"* (§5.6). ⇒ Sim hiện **thiếu chính sách thưởng riêng cho tài xế
  mới**. Đây là bằng chứng ĐO ĐƯỢC củng cố quyết định hoãn: phần này thuộc SIM-4 và phụ thuộc
  `D-POL-01/02` (khoán tuần + clawback chưa vào schema). **Không được so A/B tân binh ở SIM-4 trước
  khi vá gap này**, nếu không sẽ đánh giá thấp thu nhập tân binh một cách hệ thống.
- **F-SIM2-B (THẤP) — P3 (top) idle 378ph, util chỉ 0.27** dù ca dài nhất. Chưa điều tra, chưa kết
  luận. Có thể là hành vi thật (ca 11-12h thì idle nhiều) hoặc dấu hiệu P3 bị đặt ở khung/cell
  thưa cầu. Soi ở SIM-5 khi có metric theo giờ đầy đủ.
- **F-SIM2-C (THẤP) — `outcome="censored"`** cho đơn còn dở lúc 24:00 là đúng nhưng chưa tách khỏi
  "đang chạy dở" trên UI; số nhỏ, không ảnh hưởng tỷ lệ.

## 8. Docs đã cập nhật kèm theo

- `specs/simulation/00-sim-overhaul-master.md` — SIM-2 → DONE, SIM-3 kế tiếp.
- `tracking/TODO.md` — Track A mục 2 DONE + ghi F-SIM2-A là điều kiện chặn của SIM-4.
- `tracking/DEFERRED.md` — F-SIM2-A (D-SIM-02).
- SCOPE/USER_STORIES: **không đổi**.

## 9. Visual review

**Status: `DEFERRED` (V-03 trong `tracking/PENDING-REVIEW.md`)** — Cường hoãn check 2026-07-26,
cho phép chạy tiếp. Tab mới **🧭 Hành trình 1 tài xế** trên dashboard
(`uv run --extra viz streamlit run src/gsm_sim/dashboard.py`). Đề nghị xem **seed 1000 →
`d-42 · P4 TÂN BINH`**: Gantt timeline, bảng offer có lý do (4 lần từ chối đều `economics`),
và đường thu nhập **không có bậc thưởng** (F-SIM2-A).

## 10. Follow-up

- **SIM-3 Advice→Action** — sẵn sàng bắt đầu.
- F-SIM2-A → `D-SIM-02`, **chặn** phần baseline tân binh của SIM-4.
- Chưa kiểm chứng: journey mới chưa nối vào `mockgen` (SIM-5); `data/mock/realdata-v1/` vẫn là bộ
  sinh trước SIM-1, cần regen.
