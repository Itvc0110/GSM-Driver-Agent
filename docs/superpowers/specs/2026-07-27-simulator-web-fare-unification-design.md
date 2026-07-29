> ✅ **ACTIVE — thuộc UI-FARE-01 (UPDATE-073, chờ verdict V-16); KHÔNG thuộc pack DEFERRED D-001.**

# Thiết kế đồng nhất giá cuốc Simulator và Web Driver UI

Ngày: 2026-07-27
Trạng thái: APPROVED trong hội thoại 2026-07-27
Task: UI-FARE-01

## Mục tiêu

Dùng `sim-policy-v0` làm nguồn tính giá MOCK duy nhất cho Simulator và cuốc demo Web. Backend UI phải gọi `gsm_sim.policy.PolicyBundle`, không chép các giá trị fare/share vào Python hoặc JavaScript.

## Before / After

| Thành phần | Trước | Sau |
|---|---|---|
| Simulator | `PolicyBundle.gross_fare()` và `driver_payout_from_gross()` | Giữ nguyên, là canonical source |
| Route API | `round(distance_km * 24000)` | Quote bằng Simulator policy cho cả OSRM và fallback |
| `/trip/step` | Fare tĩnh 116k/85k/145k | `fare_vnd=null`; route quote chịu trách nhiệm giá |
| Web UI | Chỉ hiện fare, thiếu provenance/payout | Hiện gross, trip payout, policy version, MOCK |
| Ledger | Demo không cộng payout | Giữ nguyên và kiểm chứng trước/sau |

## Kiến trúc

`ui/backend/app/adapters/sim_pricing.py` là adapter mỏng: nạp `configs/pilot_dongda.yaml`, tạo `gsm_sim.policy.PolicyBundle`, rồi trả quote gồm gross, payout cuốc, share, policy version và nhãn synthetic/mock. OSRM/fallback chỉ quyết định quãng đường và geometry; không sở hữu pricing.

`RouteCalculateResponse.fare_vnd` tiếp tục có nghĩa gross để giữ tương thích, đồng thời thêm `driver_payout_vnd`, `driver_share`, `fare_policy_version`, `data_mode` và `is_mock`. `TripStepResponse.fare_vnd` trở thành nullable và generator luôn trả `null`.

Web chỉ render quote từ route response. Hoàn thành demo chỉ ghi `S.demoTrips`; không thay đổi `S.state.money`, payout pill hoặc biểu đồ thu nhập.

## Invariants và giới hạn

- Cùng `distance_km` phải cho gross/payout byte-exact giữa UI adapter và Simulator policy.
- Fare basis là `total_dist_km` đã làm tròn và trả về route response.
- Gross khác trip payout; trip payout không gồm day bonus, mission hoặc newbie.
- `sim-policy-v0` luôn mang nhãn MOCK, không được gọi là bảng giá GSM hiện hành.
- `ui/driver_app/` và legacy `ui/demo_stitch_app.html` ngoài scope.
- Hai route provider có thể trả distance khác nhau; đồng nhất là cùng policy/công thức, không phải ép distance bằng nhau.

## Acceptance

- 3,5 km trả gross 19.450đ và payout 14.588đ với config hiện hành.
- OSRM và fallback đều gọi cùng quote path.
- `/trip/step` không còn fare tĩnh.
- UI hiển thị gross/payout/version/MOCK ở incoming, active và history.
- Simulator journey vẫn bảo toàn bốn nguồn payout.
- V-11 phải được ghi nhận trung thực; user có thể cho phép commit/push trước verdict người dùng.
