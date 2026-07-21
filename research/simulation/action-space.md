# Research — Action space của tài xế Xanh SM Bike (đợt 4 + verify đợt 5)

Ngày: 2026-07-21 (verify chuyên sâu cùng ngày) · Nguồn: T-022, T-023 · Phục vụ: actor model trong `specs/simulation-twin-world.md` §5 + phạm vi advisor (T-023)
Trả lời yêu cầu #1 của Cường: nghiên cứu action mà actor tài xế có thể thực hiện → chốt khả năng AI Advisor lên các action. Giả định: track được vị trí.
Quy ước: **[T1]** official · **[T2]** báo chí · **[T3]** blog/aggregator · **[T4]** unofficial/AI-gen (chỉ lead) · **[ĐỢT 1-3]** research nội bộ · **[ƯỚC LƯỢNG]**.

## A. Hành vi TRÊN APP

| # | Action | Track? | Advisor khuyên? | Advice nếu được | Nguồn chính |
| --- | --- | --- | --- | --- | --- |
| A1 | Bật online / tắt offline | ✅ app event | ✅ CÓ — cốt lõi F1/F2 | Timing online (trước khung cao điểm — điểm tính theo **giờ khách đặt**), timing nghỉ | [T3] + PDF Q&A official 12/2025 [ĐỢT 2] |
| A2 | **"Offline khi kết thúc chuyến"** — hoàn thành cuốc hiện tại rồi tự offline (Bike từ 30/10/2023) | ✅ | ✅ CÓ | Kết ca/nghỉ "mềm" KHÔNG phải từ chối cuốc — cách advisor khuyên nghỉ/sạc/kết ca đúng chuẩn | **[T1]** [greensm](https://www.greensm.com/news/ra-mat-tinh-nang-ngung-nhan-chuyen-trong-hanh-trinh) |
| A3 | "Nhận chuyến tự động" — hệ thống **ép bật đến 23h59** khi acceptance ngày <50% (15/7/2025); toggle tự do [ƯỚC LƯỢNG] | ✅ state | ⚠️ chỉ cảnh báo ngưỡng, không khuyên bật/tắt để né đơn | "Tỷ lệ nhận X%, <50% ép auto-accept, <70% phạt 100–200k/tuần, 3 tuần khóa" (diễn giải policy versioned) | [T2] [nguoiquansat](https://nguoiquansat.vn/xanh-sm-manh-tay-voi-tai-xe-luoi-nhan-cuoc-he-thong-se-tu-dong-bat-nhan-chuyen-den-23h59-231666.html) |
| A4 | Nhận/từ chối đơn khi đơn nổ (vuốt) | ✅ + acceptance rate | ❌ KHÔNG khuyên đơn cụ thể (ranh giới cứng); ✅ giải thích hệ quả tỷ lệ lên thưởng (HN ≥85%/85%) | Policy-explain + cảnh báo ngưỡng | [T3] + [ĐỢT 2] |
| A5 | Hủy chuyến; "Hủy chuyến hợp lệ" (6/5/2025) — **tái xác minh 2026-07-21: vẫn chỉ Taxi + Car Platform, KHÔNG Bike**; Bike hủy sai → 200k/lần + mất thưởng tuần | ✅ + cancel rate | ❌ không khuyên hủy cụ thể; F0 trả lời luật khi hỏi, `unknown` cho Bike | Policy-explain versioned | **[T1]** [greensm](https://www.greensm.com/vn-vi/news/tinh-nang-huy-chuyen-hop-le) |
| A6 | Loại đơn Bike: khách + Xanh Express (giao hàng) + Xanh SM Ngon (đồ ăn); cohort **"chuyên Food"** có policy riêng (02/03/2026, thưởng đến 4.000đ/đơn). Cơ chế tự chọn loại dịch vụ: KHÔNG tìm thấy — là thuộc tính đăng ký [ƯỚC LƯỢNG] | ✅ loại đơn trong event | ⚠️ giải thích policy từng loại/cohort (F0); không khuyên đơn cụ thể | So sánh cohort policy | **[T1]** [chuyên Food](https://www.greensm.com/vn-vi/news/xanh-sm-ngon-cap-nhat-chinh-sach-thu-nhap-tai-xe-chuyen-food), [Xanh Express](https://www.greensm.com/vn-vi/news/xanh-sm-express-huong-dan-quy-trinh-thuc-hien-dich-vu-giao-hang-sieu-toc) |
| A7 | Xem "Chương trình thưởng"/điểm từng cuốc/doanh thu/lịch sử | ✅ | ✅ CÓ — advisor là lớp diễn giải các số này | Tiến độ mốc tuần, khoảng cách chỉ tiêu (F1/F2/F3) | **[T1]** PDF Q&A [ĐỢT 2] |
| A8 | Ví 2 tầng (trên = ký quỹ; dưới = doanh thu+thưởng, rút được); thưởng về ví **thứ Tư**, rút **thứ Năm**, tiền về thứ Sáu | ✅ | ✅ CÓ (nhẹ) | Nhắc lịch thưởng/rút; giải thích cơ chế ví (F0) | **[T1]** [xanhsm](https://www.xanhsm.com/news/tai-xe-xanh-sm-nap-tien-de-dang-rut-tien-nhanh-chong); chi tiết 2 ví [T4 — đối chiếu app] |
| A9 | Tủ đổi pin: tìm tủ + xem pin còn/hết qua app **VinFast E-Scooter** (app riêng); quét QR đổi. **Đặt chỗ trước: CHƯA CÓ** (vẫn "dự kiến", check 2026-07-21) | ⚠️ event ở app VinFast; suy từ vị trí | ✅ CÓ (timing) | "Đổi pin lệch đỉnh 11–13h/17–19h; kiểm tra trạng thái tủ trước khi đến" | [T3] + **[T1]** [VinFast](https://vinfastauto.com/vn_vi/dich-vu-pin-xe-may-dien) |
| A10 | Navigation/map, thông báo real-time | ✅ | ✅ (kênh phát advice) | Đẩy nhắc theo hybrid timing | [T3] |
| A11 | CSKH 1900 2088 / hotline tài xế 1555 / khiếu nại vi phạm trong app (48h) | ✅ | ❌ ngoài scope (D-006/D-007) — chỉ trỏ kênh official khi hỏi | — | [T3]+[T1] |
| A12 | Đăng ký gói tài xế FT/PT × dài/ngắn hạn (15/11/2025; đổi gói 1 lần/tuần trước CN) | ✅ thuộc tính hồ sơ | ✅ CÓ (F0/F1) | So sánh policy gói theo persona | **[T1]** [greensm](https://www.greensm.com/news/xanh-sm-bike-da-dang-goi-dang-ky-linh-hoat-thoi-gian-chay) |
| A13 | "Đăng ký Ca Làm Việc" — **VERDICT: UNVERIFIED (verify chuyên sâu 2026-07-21)**: sau ~3,5 tháng từ ngày claim ra mắt, KHÔNG có dấu vết trên site official/báo chí/video/diễn đàn; nguồn gốc duy nhất truy được là ai-hay.vn (AI-generated); dangkyxanhsm.vn kiểm search nội bộ KHÔNG có bài; các "nguồn khớp" đều là snippet AI dẫn lại từ chính ai-hay. Khả năng cao là nội dung AI bịa/ngoại suy. Lỗ hổng kiểm chứng duy nhất: changelog in-app 03–04/2026 (không index) — cần thiết bị thật (T-013) | — | ❌ KHÔNG dùng làm giả định thiết kế. Nếu sau này verify được qua app thật: bật config flag "shift-aware mode" (xem §Phạm vi advisor) | — | Verify đa kênh: [greensm quy định nội bộ 30/03/2026](https://www.greensm.com/news/cap-nhat-van-quy-dinh-noi-bo-chung-tai-xe-xanh-car-2026) (không nhắc ca), [Play listing net.gsm.driver.app](https://play.google.com/store/apps/details?id=net.gsm.driver.app), [update v2.22.0](https://www.greensm.com/vn-vi/news/cap-nhat-ung-dung-xanh-sm-driver); nguồn claim: [ai-hay T4](https://ai-hay.vn/quy-dinh-ca-lam-viec-cua-xanh-sm-bike-pN1UmIoGqJy) |
| A14 | **"Danh sách chuyến hẹn giờ"** (official 26/06/2026): tài xế chủ động chọn chuyến đặt trước từ danh sách; gần giờ đón chưa ai nhận → về luồng phát chuyến thường | ✅ app event | ⚠️ advisor được **nhắc tài xế xem danh sách** (tính năng official) — KHÔNG tự đề xuất chuyến cụ thể | "Sắp tới khung rảnh — kiểm tra danh sách chuyến hẹn giờ" | **[T1]** [greensm](https://www.greensm.com/vn-vi/news/tinh-nang-danh-sach-chuyen-hen-gio-chu-dong-nhan-chuyen-toi-uu-thu-nhap) |

## B. Hành vi VẬT LÝ ngoài app

| # | Action | Track? | Advisor khuyên? | Nguồn |
| --- | --- | --- | --- | --- |
| B1 | Đứng chờ tại chỗ (idle) | ✅ GPS + online | ✅ mức thời gian ("giờ này demand thấp, cân nhắc nghỉ") — KHÔNG chọn điểm đứng hộ | [ƯỚC LƯỢNG] + blog ca đêm [T1] |
| B2 | Cruising/relocate sang khu khác (rời điểm bão hòa) | ✅ GPS | ❌ product (không reposition); ✅ **actor trong SIM tự làm** | [ĐỢT 2] |
| B3 | Tránh mưa/tắt app chờ hết mưa (đa số tắt: sợ tai nạn, không xem được map; niềm tin "bật app mà từ chối thì mai ít khách") | ✅ offline + weather | ✅ CÓ (an toàn + timing); không khuyên "cố chạy mưa ăn giá cao" | **[T2]** [Thanh Niên](https://thanhnien.vn/vi-sao-tai-xe-xe-om-cong-nghe-so-troi-mua-185240524164840842.htm) |
| B4 | Đi đổi pin tại trạm (queue đỉnh trưa + chiều tối; thao tác <2ph) | ✅ GPS đến trạm; SOC future (D-002) | ✅ CÓ (timing lệch đỉnh) | [ĐỢT 1-3] |
| B5 | Sạc tại nhà buổi trưa (đội sạc cắm: sáng chạy → trưa sạc 3–4h → chiều chạy) | ⚠️ suy: GPS "nhà" + offline dài | ✅ CÓ — F3 chỉ ra "sạc giờ cao điểm" chưa tối ưu | [ĐỢT 1-2] ≥3 nguồn |
| B6 | Nghỉ ăn/nghỉ ngắn | ⚠️ suy | ✅ CÓ (dead hours 13–16h — assumption) | [ĐỢT 2] |
| B7 | Kết ca sớm/muộn (qua A1/A2) | ✅ | ✅ CÓ — "còn X cuốc đạt mốc, cân nhắc +1h" (trade-off, không hứa chắc) | [ƯỚC LƯỢNG]+A2 [T1] |
| B8 | **Multi-app song song: KHÔNG khả thi/bị cấm với Bike** — FAQ cấm dùng xe Xanh SM chạy app khác; cấm đồng phục hãng khác; 1 thời điểm 1 loại dịch vụ | ⚠️ khó track | ❌ (vi phạm, không dạy lách). Sim: actor mặc định KHÔNG multi-app — **khác giả định sim Grab-like thường gặp** | [T3]+**[T1]** quy tắc ứng xử |
| B9 | **BỊ CẤM** (loại khỏi advisor; sim chỉ dùng làm noise có nhãn): bắt khách ngoài app (200k–1tr); gian lận/cuốc ảo (nhóm 1: chấm dứt + ≥2tr); nhận không đón; sai loại dịch vụ (200k); xí chỗ tủ pin | một phần | ❌ TUYỆT ĐỐI | **[T1]** quy tắc ứng xử (≥4 bản: 21/6/2024→05/06/2026 — Policy KB theo effective date) |

## Action set chốt cho SIM actor (input cho T-018/T-023)

- **Lớp app (event rời rạc):** `go_online` · `go_offline` · `set_offline_after_trip` (A2 — có thật cho Bike) · `accept_order`/`decline_order` (decline vô hiệu khi `forced_auto_accept` — bật khi acceptance ngày <50%, reset 23h59) · `cancel_trip(reason)` (mọi cancel Bike tính vào rate) · `complete_trip` (loại dịch vụ là thuộc tính đơn).
- **Lớp vật lý (semi-Markov trên H3):** `wait_at_cell` · `relocate_to_cell` (sim-only đối với advisor) · `go_to_swap_station → queue → swap_battery` (90s, tủ 6 slot) · `charge_at_home(≈3–4h)` (đội sạc cắm) · `rest(duration)` · `start_shift`/`end_shift` · `weather_response` (offline khi mưa xác suất cao).
- **State kèm actor:** acceptance/completion/cancel rate, điểm tuần, SOC, vị trí, cờ `forced_auto_accept`, gói tài xế.
- **Không mô hình hóa:** multi-app (B8), hành vi cấm (B9) — trừ scenario noise có nhãn.
- **V2 chờ xác minh:** `register_shift(timeslot, ≤3 areas)` (A13).

## Phạm vi advisor — PRODUCT vs SIM (T-023, cập nhật sau verify + quyết định Cường 2026-07-21)

**Kết luận xung đột hệ thống (verify đợt 5):** Xanh **không có heatmap demand cho tài xế** (khác Grab — Grab có heatmap + push cá nhân hóa; Be cũng không có); không có bằng chứng ràng buộc khu vực realtime hay phạt khi rời khu (mô tả app official: tài xế "linh hoạt chọn thời gian và khu vực hoạt động"); cơ chế phát cuốc = tự phát chuyến gần + ép tỷ lệ nhận (auto-accept <50%, phạt <70%). → **Advice khu vực theo heatmap phân phối là tính năng BỔ SUNG, không chồng đè tối ưu sẵn có của Xanh.**

- **PRODUCT được phép:** timing online/offline/kết ca (A1/A2/B7); timing nghỉ/sạc/đổi pin (B4–B6/A9); tiến độ mốc thưởng versioned (A7); cảnh báo ngưỡng + hệ quả (A3/A4 — thuần diễn giải); ví/lịch thưởng (A8); so sánh gói/cohort (A6/A12); cảnh báo thời tiết (B3); nhắc xem "Danh sách chuyến hẹn giờ" (A14 — official).
- **PRODUCT được phép CÓ ĐIỀU KIỆN (mở theo quyết định Cường 2026-07-21):** **gợi ý khu vực đứng chờ theo heatmap demand mock** (B1-điểm/B2) — với các điều kiện an toàn BẮT BUỘC:
  1. chỉ khuyên vị trí **giữa các cuốc / trước ca** — không bao giờ khuyên nhận/từ chối/hủy đơn cụ thể;
  2. kèm cảnh báo "đơn có thể được phát trong lúc di chuyển; từ chối ảnh hưởng tỷ lệ nhận cuốc" (vì Xanh phạt <70% + auto-accept <50%);
  3. **capacity-aware** (tính bão hòa cung, không dồn mọi tài xế về 1 khu — cơ chế ledger/staggering như advice sạc);
  4. trình bày dạng xác suất/bất định + **nhãn mock** (phân phối là mock, không phải heatmap thật GSM); không hứa thu nhập;
  5. **"shift-aware mode" config flag** (mặc định OFF): nếu A13 sau này verify được qua app thật, advisor chuyển sang khuyên trong khuôn khổ (chọn 3 khu vực nào khi đăng ký; trong ca chỉ gợi ý trong khu đã đăng ký).
- **PRODUCT cấm:** nhận/từ chối/hủy đơn cụ thể (A4/A5); B8/B9; can thiệp matching/dispatch/pricing.
- **SIM:** actor đầy đủ relocate + decline/cancel theo behavior model; fleet-awareness/anti-herding theo SCOPE §5b; advisor arm A trong sim dùng cùng điều kiện an toàn trên (capacity ledger).

## Gaps

1. A13 — verdict UNVERIFIED (chi tiết ở bảng); lỗ hổng duy nhất còn lại: changelog in-app Green SM Driver 03–04/2026 — cần thiết bị thật (T-013) trước khi thay đổi verdict.
2. Cơ chế chọn/bật loại dịch vụ trong app — không có mô tả công khai.
3. Toggle auto-accept lúc bình thường.
4. "Hủy chuyến hợp lệ" cho Bike — vẫn `unknown`.
5. Đặt chỗ tủ pin — chưa ra mắt (đến 2026-07-21).
6. Screenshot flow app driver — cần người thật mở app/video (T-013).
