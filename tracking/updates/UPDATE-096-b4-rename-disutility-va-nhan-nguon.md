# UPDATE-096 — B4: hoàn tất rename disutility + nhãn dải nguồn driver_share

- **Ngày:** 2026-07-29 (chiều) · **Loại:** rename thuần + nhãn nguồn (KHÔNG đổi hành vi)
- **Người thực hiện:** AI agent dưới claim Cường (PLAN-cycle-wx B4 — mục cuối Phần B)

## Nội dung

1. `accept_cost_per_pickup_km_vnd` → **`pickup_disutility_vnd_per_km`** ở config +
   `world.py` (attr `pickup_disutility_km`) + dashboard ×2 — đóng nợ "hai tên một sự
   thật" (hàm behavior.py đã đổi từ Cycle P): 3.000đ/km là DISUTILITY CẢM NHẬN, không
   phải tiền mặt (tiền thật 30–250đ/km — đọc nhầm là lệch 10–20×). GIÁ TRỊ không đổi.
2. `driver_share: 0.75` mang nhãn: CẬN DƯỚI của dải mâu thuẫn nguồn **[0,75–0,91]**
   (91% official image-locked / 90→85% / 84,5% / 75%) — chọn bảo thủ, chờ D-POL-05.

## Kiểm chứng + HIỆU NĂNG (nề nếp mới: báo sau mỗi update)

| Gì | Kết quả |
|---|---|
| TDD | 2 test đỏ trước → xanh (`test_b4_rename_disutility.py`); grep 0 tham chiếu cũ còn sót |
| Fingerprint | 5 seed × 2 arm vs HEAD `edfb2e5`: **IDENTICAL** |
| **Hiệu năng** | **KHÔNG ĐỔI** (rename thuần) — số tham chiếu hiện hành giữ nguyên: Δnet_mean_all **+4.000đ/người/ngày SIG** [2.130, 5.857], Δserved **+1,38đp SIG**, bền tới cash 250đ/km (+3.363đ SIG) — artifact 29, n=30 seed tươi |

## Visual verification
`NOT_APPLICABLE` — fingerprint IDENTICAL; dashboard chỉ đổi nhãn slider.

## Adversarial self-review / flaws found
1. Không giữ fallback đọc key cũ (chọn fail-visible thay silent-compat): config ngoài
   repo còn key cũ sẽ rơi về default 3000 — trùng giá trị hiện hành nên vô hại hôm nay;
   ghi chú tại config.
2. PHẦN B (B1→B4) HOÀN TẤT. Còn nối production `policy_costs_as_of` khi bundle mang costs.

## ⏳ Nhắc PENDING-REVIEW
V-01..V-17 · Q-03 · Q-04 · Q-07 · BUG-MOCKGEN-CLI · ĐA-05 chờ verdict (UPDATE-091) ·
B6-PARITY chờ xếp ưu tiên · format_checker qua plan mode.
