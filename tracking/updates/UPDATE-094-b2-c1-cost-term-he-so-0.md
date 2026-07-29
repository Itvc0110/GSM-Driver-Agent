# UPDATE-094 — B2: số hạng chi phí C1 vào objective S2, hệ số mặc định 0

- **Ngày:** 2026-07-29 (chiều)
- **Người thực hiện:** AI agent dưới claim Cường (PLAN-cycle-wx Phần B — Cường duyệt trong phiên)
- **Loại:** code solver (thay đổi CÓ CỔNG AN TOÀN: mặc định 0 ⇒ bit-identical, có bằng chứng)
- **Hiện thân tầm nhìn:** vế A5 VISION-ALIGNMENT (*"hàm tối ưu đủ biến, cập nhật giá trị
  theo policy"*) — nửa đầu: BIẾN tồn tại trong objective; B3 (kế tiếp) để POLICY quyết
  định giá trị theo (track, as_of).

## Vấn đề

`shift_dp` có đúng 2 số hạng CỘNG, 0 số hạng TRỪ (khảo sát 2026-07-29) — thế giới có chi
phí (`actor.cost_vnd`, T-045b) mà người tối ưu không thấy: đúng mẫu "hai nguồn sự thật"
D-SIM-09. B1 (UPDATE-093) đã cho THƯỚC thấy chi phí trước; B2 cho SOLVER thấy.

## Cơ chế

- `DEFAULT_PARAMS["cash_cost_vnd_per_km"] = 0.0`; docstring giải xung đột spec
  objective-v2 §7 ngay tại chỗ: "fatigue-as-money bị bỏ" vì là SỐ BỊA — C1 có nguồn
  OFFICIAL (điện 70–93đ/km; đổi pin 9.000đ/lượt sau 31/03/2029) nên không vi phạm §5.
- Bellman nhánh ONLINE: giá trị quyết định = **NET** `exp_trips·(ppo − cash_km·avg_dist_km)`;
  gate `online_net > 0` (online mà mỗi cuốc lỗ tiền mặt = vô ích như demand 0).
- **§5 giữ nguyên tách gross/payout/net**: `expected_payout` BÁO CÁO vẫn GROSS (reconstruct
  không đổi) — cost đổi quyết định, không rò vào payout. Test pin.
- `advice_bridge.solver_params` truyền `vehicle.cash_cost_vnd_per_km` — CÙNG khoá config
  với sổ chi phí của world: một nguồn sự thật cho thế giới và người tối ưu.

## Kiểm chứng

| Gì | Kết quả |
|---|---|
| TDD | 5/6 đỏ trước; test thứ 6 (`prohibitive`) lộ bẫy VACUOUS — schedule là list dict nên `"ONLINE" not in schedule` luôn True → sửa bằng `_acts()` helper + docstring ghi bài học T-046 rule 5; sau sửa: mutation MB1 (bỏ trừ cost) làm ĐỎ đúng 2 test (`prohibitive`, `scales`) ⇒ hết vacuous |
| Bộ test | `test_c1_cost_term` (6) + `test_shift_dp` (19) + `test_advice_bridge` + `test_bridge_passes_solver_params` + `test_net_metric` = **58 passed** |
| Bit-identical | fingerprint 5 seed × 2 arm vs HEAD `d362cf2`: **IDENTICAL** (mặc định 0 — cổng an toàn hoạt động) |
| Ngưỡng cơ học | cash 5.000đ/km × 3km > ppo 12.975đ ⇒ ONLINE chết; 1,5km ⇒ sống (test scales — chi phí nhân đúng quãng đường) |
| Sweep 30 seed × cash ∈ {0,70,150,250} | **XONG** (seeds tươi 3100–3129, coverage=all, positioning wait_only; artifact `29-b2-cost-sweep-30seed.json`). **Δnet_mean_all (B−A): +4.000 → +3.822 → +3.618 → +3.363đ — DƯƠNG SIG Ở MỌI MỨC** (CI thấp nhất [1.543, 5.166] vẫn loại 0); Δpayout +4.000đ hằng theo mức (CRN — cash không đổi hành vi vì shift_plan OFF, chỉ trừ tiền km); Δserved +1,38đp SIG. Suy ra km rỗng thêm của kênh vị trí ≈ **2,5 km/người/ngày**; break-even ≈ **1.570đ/km** — GẤP >6 LẦN cận trên chi phí thực (250đ/km). **Kết luận câu hỏi plan B2: kênh vị trí sống khoẻ với chi phí thực ở mọi kịch bản đã biết** |

## Visual verification

`NOT_APPLICABLE` — mặc định 0, fingerprint IDENTICAL; sweep là artifact số (không đổi UI).

## Adversarial self-review / flaws found

1. Bẫy vacuous tự bắt trong chính lượt này (schedule dict) — đã sửa + mutation proof.
2. Chi phí mô hình theo `avg_dist_km` (quãng đường CUỐC) — chưa gồm km đón khách/km rỗng;
   nhất quán với mức thô của DP hiện tại, ghi là giới hạn (C4 chi phí vị thế là số hạng riêng).
3. `_baseline_naive_rest` vẫn tính GROSS — delta so baseline giữ ngữ nghĩa payout cũ;
   khi B3 bật cost theo policy, cân nhắc baseline net cùng lượt đo lại.
4. Sweep chưa xong lúc viết — KHÔNG kết luận gì về ngưỡng dương của positioning cho tới
   khi artifact 29 có số.

## ⏳ Nhắc PENDING-REVIEW

V-01..V-17 · Q-03 · Q-04 · Q-07 · BUG-MOCKGEN-CLI · ĐA-05 code chờ verdict (UPDATE-091) ·
B6-PARITY chờ xếp ưu tiên · kế tiếp: **B3 policy costs + as_of** (sau khi sweep về) ·
format_checker qua plan mode.
