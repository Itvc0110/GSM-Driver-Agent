# UPDATE-153 — E1b: sửa CÔNG THỨC KÊNH (đợt 1/5 chương trình tối ưu advisor, phần 2)

- **Ngày:** 2026-08-06
- **Loại:** fix (7 bug công thức trong solver/kênh — ĐỔI hành vi sim ở arm advice-ON) + 1 WONTFIX có lý do
- **Liên quan:** UPDATE-151 (r10) · UPDATE-152 (E1a) · plan E1–E5 · F-098-01 · UPDATE-138/142

## Đã sửa (test đỏ-trước `tests/test_e1b_cong_thuc_kenh.py`: 7 đỏ → 8 xanh)

| # | Bug | Fix | File |
| --- | --- | --- | --- |
| ADV-01 🔴 | Band điểm DP floor mỗi bucket (`add_pts//15` với add≈5-11) ⇒ **mốc thưởng ngày không bao giờ vào Bellman** — F-098-01 sửa gate nhưng bonus chưa từng chạy được; nghi phạm chính của Δ=0 tuyệt đối ở s2_only (UPDATE-152) | `points_band_size` 15→**5** (khớp point_normal), `points_bands` 16→49. Reproduce = kịch bản F-098-01 nguyên bản: 45đ, thiếu 15 tới mốc +30.000đ, net −225đ/cuốc — DP cũ trốn lỗ bỏ mốc, DP mới ăn lỗ 675đ lấy 30.000đ; đối chứng: không mốc trong tầm ⇒ vẫn né lỗ | `shift_dp.py` |
| ADV-02 | `shift_extend` không so `need_min` với thời gian ca CÒN LẠI ⇒ kéo ca cả khi mốc đạt trong ca + cấp trọn gói khi chỉ cần một phần | `reachable_in_shift` (trước cadence — họ R-08) + cấp `need_extra×1.15` | `advice_bridge.py` |
| ADV-03 | Lan can `would_exceed_fatigue` đo tại-lúc-khuyên (`online+need`) | Dự phóng CUỐI CA MỞ RỘNG: `online + ca-còn-lại + phần-kéo×1.15` (trước trần — lý do sức khoẻ thắng trần kinh tế) | `advice_bridge.py` |
| ADV-04 | Baseline S2 không nhận tín dụng nghỉ ⇒ **delta thổi phồng hệ thống** | truyền `rest_taken_min/shift_elapsed_min` vào `_required_rest` như nhánh DP | `shift_dp.py` |
| ADV-05 | S1 coi lịch sử 0.0 điểm/giờ là THIẾU dữ liệu ⇒ rơi về lý thuyết dương (lạc quan) | `hist.get(bucket) is not None` — 0.0 là dữ liệu HỢP LỆ (khớp REVIEW-C9) | `bonus_feasibility.py` |
| ADV-07 | Gate accept_lift parse chuỗi tiếng Việt (`"quỹ"`, `"hoàn thành"`) — đổi wording là gate câm im lặng | đọc `solution["constraints"]` typed (enough_hours/ok_acceptance/ok_completion), fail-closed khi thiếu khoá | `advice_bridge.py` |
| ADV-08 | Quota hoãn nghỉ cộng nguyên `minutes_to` (đo giữa hai ĐẦU giờ) — phóng đại tới 59′/lần ⇒ trần 120′ cạn sớm oan | cộng `minutes_to − now%60` (= due − now, khoảng hoãn thật) | `advice_bridge.py` |
| ~~ADV-09~~ 🔴 **ĐÃ SỬA RỒI REVERT trong cùng cycle** | r10 đọc câu docstring *"tối đa một đơn vị cung"* thành bất biến TRÊN TỔNG hai sổ và gọi idle+lệnh-chờ là "đếm đôi". Tôi sửa theo mà **không reproduce với consumer** — suite bắt ngay: `test_market_state_sim_producer.py` ghim **CÓ CHỦ Ý** hai sổ riêng (*"người đang chờ vẫn là cung tại chỗ cho tới khi thực sự đi"* — dispatcher vẫn match được họ; bỏ khỏi `now` là làm `now` NÓI DỐI về cung match-được) | **REVERT** về hành vi cũ + sửa DOCSTRING cho hết mơ hồ ("tối đa một đơn vị **trong mỗi sổ**", ghi rõ vì sao hai sổ + trỏ test ghim). ADV-09 là finding TB **chưa qua vòng phản biện** — tôi đã vi phạm chính caveat của UPDATE-151 (*"finding TB/THẤP chưa verify — không tin sẵn"*). Suite chính là vòng phản biện đã cứu | `market_state.py` (docstring) |

### ADV-06 — WONTFIX CÓ LÝ DO (kênh tắt vẫn log `advice_rest_veto`)

r10 gọi đây là "kênh tắt không trơ về event stream". Soi lại: đó là **THIẾT KẾ CÓ CHỦ Ý** của
D-M3-05 — cổng tầng 5 `health_guardrail_flags` cần baseline *"lan can SỐNG ở arm A"* để tố giác
kịch bản xoá-lan-can (*"sụp về 0 ở B"*); test T1/T2/T4 của `test_rest_rails_guardrail.py` ghim
đúng hành vi này. Sửa theo r10 là **phá gate**. Nợ thật còn lại chỉ là cái TÊN event (advice_*
bắn khi không có advice) — ghi nhận, không đổi trong đợt này (đổi kind = đổi contract audit).

## Sửa test CÓ CHỦ Ý (ngữ nghĩa kênh đổi theo plan đã duyệt)

- `test_shift_extend_rails.py` ×3: kịch bản cũ (ca còn 400′) nay hợp lệ là `reachable_in_shift`
  — dựng lại với ca sắp kết (còn 5–20′) để rail/grant thật sự bị gọi; docstring ghi rõ vì sao.
- `test_rest_commit.py` ×1: pin quota 120→110 (ADV-08 — khoảng hoãn thật).
- `test_advice_time_encoding.py` ×3 (suite bắt sau lượt đầu): fixture hỏi ở `now=1200` khi ca còn
  230-240′ — nay hợp lệ là `reachable_in_shift` ⇒ không chạm được nhánh b0-A/L1-04/ghost mà các
  test này sinh ra để kiểm. Dời `now` sát giờ kết ca (1420/1425/1430) + **ép coin=True** (coin là
  hash tất định theo bucket — dời bucket là đổi coin, mà coin không phải chủ thể của ba test này).

## Kiểm chứng

| Cổng | Kết quả |
| --- | --- |
| Test đỏ-trước E1b | 7 đỏ → **8 passed** (kèm 1 đối chứng ngược) |
| Consumer công thức (f098 pins · shift_dp · advice_bridge · extend_rails · rest_commit · solver_properties) | **129 passed** |
| ADV-08/09 consumers (rest_commit · standby_capacity · market_demand_override) | **35 passed** |
| Behavior-neutral config MẶC ĐỊNH (advice OFF) | fingerprint **15/15 IDENTICAL** vs HEAD (5 seed × {1-day, d0, d1}) |
| Pin f098 quan trọng | `test_bucket30_no_band_crossing_is_not_a_bug` vẫn XANH — B=1 với 45+11=56 < 60 thì SWAP vẫn đúng, PBS=5 không "sửa nhầm" ca thật sự lỗ |
| Ladder 30 seed TRƯỚC/SAU | ✅ Cả hai artifact ở `research/audit/2026-08-06-e1b/`. **Kỳ vọng khai trước SAI — và lý do tìm được là một phát hiện:** `s2_only` **bit-identical** trước/sau (target Δ=0,0 · cohort +728,1 [−100; +1.991] giống hệt từng chữ số). Không phải fix không vào sim (`solver_params` không override band) mà là **kinh tế của config hiện tại**: `cash_cost_vnd_per_km = 0` ⇒ `online_net ≥ 0` luôn ⇒ ONLINE thắng REST/END bất kể bonus ⇒ mốc thưởng KHÔNG có cơ hội đổi `schedule[0]`. ADV-01 là bug THẬT của solver (unit test cash>0 chứng minh) nhưng tác động in-sim tại config hiện tại **≈ 0**; nó sẽ CÓ tác động khi chi phí thật bật (sau 31/03/2029, hoặc sweep C1/C5) và trên đường SẢN PHẨM dùng `policy_costs_as_of`. Arm `all`: target 22.631 → 21.685 [6.720; 36.667] · cohort −264 → +98 ns — dịch nhẹ từ ADV-02/03/08/09, không đọc là hiệu ứng (n=30, hai bản code) |
| Hệ quả cho ĐA-07 | **KHÔNG đề xuất mở lại** — S2 in-sim không đổi hành vi ⇒ verdict "có hại" của ĐA-07 (vốn đến từ tương tác ngân sách FIFO, Q-09) không bị E1b thách thức. Đề xuất mở lại chỉ hợp lệ khi có sweep chi phí ≠ 0 kèm prereg |
| Suite chính (2 lượt) | Lượt 1: 10 F — **suite bắt 5 test ghim ngữ nghĩa cũ** (time_encoding ×3 → sửa fixture CÓ CHỦ Ý; market_state ×2 → lộ ADV-09 sai, REVERT). Lượt 2 sau sửa: **1106 passed / 5 failed / 4 skipped** — đúng 5 F đỏ sẵn (`K-01`×3 · `K-02` · `K-03`), **0 hồi quy** |

## Adversarial self-review / flaws found

1. **PBS=5 tăng state DP ×3** (~70k ô với B=36) — chưa đo runtime tác động lên ladder; sẽ đọc từ
   thời gian chạy ladder SAU so với TRƯỚC. Nếu chậm đáng kể: cân nhắc band thích nghi (5 khi gần
   mốc, 15 khi xa) — CHƯA làm, khai nợ.
2. **ADV-03 dùng phần-kéo TRƯỚC trần** trong dự phóng (need_extra×1.15 chưa cap) — bảo thủ có chủ
   ý: trần chỉ thu nhỏ và ca vượt trần đã có `cap_unreachable`; nhưng nghĩa là một ca "trần sẽ cắt
   xuống mức an toàn" vẫn bị chặn vì sức khoẻ. Chấp nhận: thà chặn nhầm về phía an toàn (§1.2b).
3. **`online_min` vẫn là proxy mệt** (gộp nghỉ) — ADV-03 sửa PHÉP CHIẾU, không sửa ĐẠI LƯỢNG;
   `D-QD4-05` vẫn treo chờ Cường, đổi đại lượng phải làm CẢ HAI kênh cùng lúc.
4. **Chưa kiểm:** tương tác ADV-01 × ADV-04 trên delta S2 (hai fix cùng kéo delta hai hướng — chỉ
   ladder SAU trả lời được); `count_supply` mới với planner S4 ở coverage all (test đi qua nhưng
   chưa đo phân bố HHI trước/sau — sẽ thấy ở ladder).

## Follow-up

- Điền bảng ladder TRƯỚC/SAU + suite khi hai job nền xong (cùng phiên).
- E2 (arm oracle + per-archetype) bắt đầu sau khi đọc ladder SAU.
