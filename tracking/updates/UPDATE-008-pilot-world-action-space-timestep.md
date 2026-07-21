# UPDATE-008 — Research đợt 4: action space, pilot Đống Đa 50 actors, timestep; spec pilot-world

- **Ngày:** 2026-07-21
- **Người thực hiện:** AI agent (Claude Code), theo 4 yêu cầu đợt 2 của Cường (0: lưu + đồng bộ toàn bộ; 1: action space; 2: pilot 1 quận/50 actors; 3: timestep; 4: approve mọi thiết kế + arm C)
- **Loại:** research / spec / docs-sync
- **TODO liên quan:** T-017 (DONE — Cường approve), T-022 (DONE), T-023 (DONE nháp v1, 1 điểm chờ Cường), T-018 (READY)

## Tóm tắt

Ghi nhận approve toàn bộ thiết kế + chốt **arm C placebo** vào 2 spec (đổi trạng thái APPROVED). Research đợt 4 hoàn tất bằng 3 agent web song song; toàn bộ findings lưu vào `research/simulation/`; viết spec tổng hợp `specs/simulation-pilot-world.md` (READY FOR BUILD, có Definition of Done); đồng bộ SCOPE/TODO/README/00_SUMMARY/memory.

## Chi tiết cập nhật

1. **Approve + arm C** (yêu cầu #4): `simulation-twin-world.md` v1.1 (APPROVED; arm C định nghĩa đầy đủ — cùng tần suất/loại advice nhưng nội dung naive; báo cáo Δ(A−B), Δ(C−B), Δ(A−C)=giá trị intelligence); `advice-timing-state-memory.md` v1.1 (APPROVED); T-017 DONE.
2. **Action space** (yêu cầu #1) — `research/simulation/action-space.md`: 13 app actions + 9 physical actions, mỗi action 4 cột (track được? / advisor được khuyên? / loại advice / nguồn T1-T4). Phát hiện chính: tính năng official **"Offline khi kết thúc chuyến"** (Bike, 30/10/2023) = cơ chế kết ca "mềm" advisor khuyên được mà không đụng ranh giới từ chối đơn; cờ `forced_auto_accept` (acceptance <50% ép bật đến 23h59); **multi-app bị cấm** với xe Xanh SM → actor model không cần mô hình hóa (khác sim Grab-like); "Hủy chuyến hợp lệ" tái xác minh vẫn chỉ Taxi/Car; cohort "chuyên Food" có policy riêng. Action set ghi vào twin-world §2.3. **Chờ Cường quyết:** advice quanh "Đăng ký Ca Làm Việc" (A13 — nguồn T3/T4 chưa verify; khung giờ hợp lệ F1, chọn khu vực vượt ranh giới).
3. **Pilot world** (yêu cầu #2) — `research/simulation/pilot-world-dongda.md` + data OSM thật copy vào `research/simulation/data/`: chọn **Đống Đa** (so 3 ứng viên: mật độ cao nhất HN ~40k/km², mix demand đại diện — 26 BV + 13 ĐH + TTTM/chợ, 11 tủ pin thật, đúng nơi ghi nhận quá tải); H3 **res 9** chính (85 cells lõi, polyfill thật bằng h3-py trên polygon 5 phường proxy — caveat bỏ cấp quận 7/2025) + res 8 cho heatmap; demand 2 cách độc lập giao nhau → **15–22k đơn bike/ngày quận, central 18k**; scale 50 actors → `orders_per_day=1.200` (900–1.800), khớp ngược 15–30 cuốc/actor; bản đồ: 11 tủ pin + 26 BV + 13 ĐH tọa độ thật, office-weight mock dọc trục chính.
4. **Timestep** (yêu cầu #3) — `research/simulation/timestep-design.md`: kiến trúc phân tầng T0 pure-DES / T1 dispatch tick **5s** / T2 bucket **15ph** / T3 advisor anchor **30ph** / T4 viz nội suy (không frame trong sim); sensitivity protocol timestep-halving trên cùng seed; determinism cho CRN 3-arm (priority tường minh cùng-timestamp, sort key ổn định, RNG per (entity,purpose), **pre-generate exogenous trace** dùng chung — đã xác minh source SimPy heap).
5. **Spec tổng hợp** — `specs/simulation-pilot-world.md` (READY FOR BUILD): bảng thế giới chốt, 3 arm, actor model, 5 kịch bản pilot (gồm stress herding 11 tủ × 50 actors), output/viz, **DoD 5 mục** (determinism test, sensitivity, calibration 15–30 cuốc, capacity-ledger proof, Δ 3 arm ≥20 seeds), đường mở rộng toàn HN giữ nguyên kiến trúc. Lưu ý hiệu chỉnh khi build: grid_disk k ở res 9 cần quy đổi tương đương bán kính res 8 (k=4–6).
6. **Đồng bộ** (yêu cầu #0): SCOPE §5b (pilot + approve + arm C), 00_SUMMARY (mục 11–16 đợt 3), research/README (folder simulation đầy đủ), TODO (T-017/T-022/T-023 DONE, T-018 READY), memory file cập nhật.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| research/simulation/action-space.md · pilot-world-dongda.md · timestep-design.md | tạo |
| research/simulation/data/{battery_nodes,batt_dd,poi_dd,dd_geom}.json | tạo (OSM snapshot 2026-07-21, ODbL) |
| specs/simulation-pilot-world.md | tạo |
| specs/simulation-twin-world.md (v1.1 APPROVED + arm C + action set §2.3) · specs/advice-timing-state-memory.md (v1.1) | sửa |
| planning/SCOPE.md (§5b pilot) · research/00_SUMMARY.md · research/README.md · tracking/TODO.md | sửa |
| tracking/updates/UPDATE-008-...md | tạo |

## Kiểm chứng

- OSM data: query Overpass chạy thật (144 node toàn HN khớp research đợt 3; 11 node Đống Đa; polyfill h3-py 4.5.0 thật trên polygon). Demand quận: 2 phương pháp độc lập giao nhau (tăng độ tin).
- CHƯA kiểm chứng: A13 "Đăng ký Ca Làm Việc" (T3/T4 lead); toggle auto-accept tự do; cơ chế chọn loại dịch vụ; số 5s/15ph/30ph là đề xuất cần sensitivity khi build; toàn bộ chuỗi demand kế thừa sai số mock 170k.
- Không có code chạy trong update này — spec READY, build là T-018 (chưa claim).

## Follow-up / defer phát sinh

- **1 điểm chờ Cường** (ghi tại T-023): có cho advisor nhắc quanh "Đăng ký Ca Làm Việc" không nếu verify được (khung giờ OK / khu vực vượt ranh giới).
- T-013 mở rộng: xác minh A13 + screenshot app driver khi có người thật join group/mở app.
- T-018 build theo spec pilot (DoD 5 mục); T-021 calibration.
- Toàn bộ thay đổi đợt này chưa commit (cùng các file UPDATE-007) — commit khi Cường yêu cầu.
