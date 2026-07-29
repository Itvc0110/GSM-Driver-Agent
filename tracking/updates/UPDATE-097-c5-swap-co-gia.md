# UPDATE-097 — C5: SWAP có GIÁ tại sự kiện — SOC thành biến kinh tế trọn vẹn

- **Ngày:** 2026-07-29 (chiều muộn) · **Loại:** solver + policy (cổng an toàn fee=0)
- **Người thực hiện:** AI agent dưới claim Cường (plan C5 duyệt trong phiên — "làm theo
  thứ tự bạn đề xuất")
- **Hiện thân tầm nhìn:** hoàn tất cụm bước 2 spec objective-v2 §6 (C1+C5); VISION §0
  tầng "thực tại đổi ở CHÍNH SÁCH".

## Cơ chế

| Mảnh | Nội dung |
|---|---|
| Nguyên tắc | KHÔNG bịa hàm phạt phi tuyến (số bịa — lý do C2-fatigue bị bác). Giá THẬT của sự kiện swap từ policy; "phi tuyến" nổi nội sinh: DP tự tránh swap thừa, tự xếp swap theo giá |
| `policy.py` | battery term mang `per: "swap"`; **CHỐNG ĐẾM KÉP**: cash_per_km chỉ còn nền by_track, khấu hao fee/range (150đ/km) chuyển vào `reason` làm tham khảo — một đồng trừ đúng một lần |
| `shift_dp` | `DEFAULT_PARAMS["swap_fee_vnd"]=0`; nhánh SWAP `v = −fee + V[...]` (fee=0 giữ tie-break Cycle R); đường `policy_costs_as_of`: battery ACTIVE ⇒ tự điền fee (explicit thắng); solution expose `expected_swap_cost_vnd` + `baseline_swap_cost_vnd` — **delta/payout GIỮ GROSS** (§5), consumer đủ số để tính net công bằng cho CẢ HAI lịch |
| bridge | `swap_fee_vnd` từ `vehicle.swap_fee_vnd` — cùng khoá với sổ chi phí world |

Hành vi pin bằng test: fee làm DP **dời swap lên đầu ca** ở thế hoà (cùng thành phần lịch,
cùng gross — vị trí đổi do tie-break); fee > lãi đuôi mỏng ⇒ **bỏ hẳn swap** (REST/END).

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| TDD | 7 test đỏ trước → xanh (`test_c5_swap_cost.py`); 2 test B3 đổi kỳ vọng theo chống-đếm-kép (ghi lý do trong test) |
| Bộ test | c5 + b3 + c1 + shift_dp + net_metric + advice_bridge + bridge_params = **74+49 passed** (hai lượt) |
| Mutation MC1 | bỏ `−fee` ⇒ ĐỎ đúng 2 test chủ đích (`fee_kills_marginal_swap`, `solver_policy_path`) → restore xanh |
| Fingerprint | 5 seed × 2 arm vs HEAD `0b2dd2b`: **IDENTICAL** (mặc định 0) |

## HIỆU NĂNG (artifact `30-c5-swapfee-30seed.json`, 30 seed tươi 3130–3159, coverage=all)

Kênh đo: `s2_only` (shift_plan ON — kênh duy nhất dùng S2; các kênh khác OFF):

| Kịch bản | Δnet_mean_all (B−A) | CI95 | SIG | Δpayout | Δserved |
|---|---|---|---|---|---|
| Hôm nay (fee 0) | −1.627đ | [−3.800, +698] | ns | −1.627đ | −0,35đp |
| 2029 (fee 9.000đ) | **−1.981đ** | [−3.739, **−196**] | **✅ ÂM SIG** | −1.781đ | −0,28đp |

**Đọc kết quả:** (1) lời khuyên S2 CÓ đổi khi pin có giá (payout hai kịch bản khác nhau —
solver phản ứng với fee đúng thiết kế); (2) nhưng kênh shift_plan vẫn KHÔNG tạo giá trị,
và trong thế giới 2029 nó **âm có ý nghĩa** ⇒ **bằng chứng độc lập thứ ba** cho điều khoản
bản-cuối ĐA-07 (Cường: "không hiệu quả thì TẮT để advisor im lặng") — giữ `shift_plan:
false`. Model gap của S2 (action space thô, không thấy vị trí) vẫn là gốc, C5 không cứu
được kênh này — nó chỉ làm solver THÀNH THẬT hơn về chi phí.
**Config mặc định KHÔNG đổi** ⇒ số tham chiếu hệ thống giữ nguyên: **Δnet +4.000đ SIG**
(positioning wait_only, artifact 29).

## Visual verification
`NOT_APPLICABLE` — fingerprint IDENTICAL; artifact số.

## Adversarial self-review / flaws found
1. Tie-break dời swap về đầu ca khi hoà — hợp lệ về giá trị nhưng có thể lệch trực giác
   ("đổi pin sớm khi chưa cần"); ghi nhận, nếu cần ưu tiên vị trí muộn thì là tie-break
   policy riêng (không phải bug).
2. Fee áp cho MỌI swap của lịch DP kể cả swap "bắt buộc vật lý" — đúng kinh tế (vẫn phải
   trả tiền) nhưng nghĩa là arm A (bản năng) không bị tính fee trong THƯỚC solver — thước
   sim (`net_mean_all`) thì tính cả hai qua sổ world → nhất quán ở tầng đo hệ thống.
3. `battery_rent_vnd_month` vẫn là nợ (chưa có quy tắc phân bổ — không bịa).

## ⏳ Nhắc PENDING-REVIEW
V-01..V-17 · Q-03 · Q-04 · Q-07 · BUG-MOCKGEN-CLI · ĐA-05 chờ verdict (UPDATE-091) ·
B6-PARITY chờ xếp ưu tiên · format_checker qua plan mode · kế tiếp đề xuất: ĐA-04 cadence
hoặc B6-PARITY theo ưu tiên Cường.
