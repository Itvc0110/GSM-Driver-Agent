# HÀNG ĐỢI CHỜ CƯỜNG CHECK

Cường (2026-07-26): *"note lại các phần cần tôi check, sẽ check sau, **nhắc lại sau mỗi lần update**"*.

**Quy tắc cho agent:** mỗi lần báo cáo xong một UPDATE, **luôn nhắc lại danh sách mục `⏳ CHỜ` dưới
đây** (ngắn gọn: mã, cái gì, xem ở đâu). Không được im lặng bỏ qua chỉ vì đang bận việc khác.
Khi Cường cho verdict → chuyển sang phần "Đã xong", ghi ngày + kết luận.

> Cường đã **hoãn** (không phải waive) visual gate của SIM-1/SIM-2 để agent chạy tiếp. Vì vậy các
> mục dưới đây **vẫn còn hiệu lực**, chỉ là không chặn commit.

## ⏳ CHỜ CHECK

| Mã | Cần check gì | Xem ở đâu | Từ ngày |
|---|---|---|---|
| **V-01** | **SIM-1 realism** — mật độ tài xế lúc 05-07h (trước đây trống trơn), đuôi đêm 21-23h, cuốc bị huỷ giữa đường đi đón | Dashboard tab 🗺️ Bản đồ H3 + 📈 Theo thời gian, **seed 1000** | 2026-07-25 (UPDATE-044) |
| **V-02** | **Fix visual trạm sạc bị cột H3 đè** — bật/tắt checkbox *"Xem phẳng (2D)"*, kiểm chấm xanh viền trắng có nổi rõ ở cả 2 chế độ không | Dashboard tab 🗺️ Bản đồ H3 | 2026-07-25 (UPDATE-044) |
| **V-03** | **SIM-2 hành trình tài xế** — Gantt timeline, bảng offer có LÝ DO, và đường thu nhập **không có bậc thưởng** ở tân binh (đó là `D-SIM-02`) | Dashboard tab 🧭 Hành trình 1 tài xế → **seed 1000 → `d-30 · P4 TÂN BINH`** | 2026-07-25 (UPDATE-045) |
| **V-04** | **SIM-3 cầu nối advice→action** — bật `advice.enabled=true` + `single_actor_id` = tài xế P4, xem các mốc advice trên timeline và cột theo/không-theo | Dashboard tab 🧭 | 2026-07-26 (UPDATE-046) |
| **V-05** | **SIM-4 thế giới song song** — chạy `uv run python scripts/run_parallel.py --seeds 30`, đọc bảng Δ + CI + `n_pos`. Lưu ý 3 điểm dễ hiểu sai (xem UPDATE-047 §3) | CLI (tab dashboard A/B **chưa làm**) | 2026-07-26 (UPDATE-047) |

## ❓ QUYẾT ĐỊNH CẦN CƯỜNG CHỐT (không phải visual)

| Mã | Cần chốt gì | Vì sao cần Cường | Từ ngày |
|---|---|---|---|
| **Q-01** | **`D-SIM-02`: chính sách thưởng cho tài xế MỚI.** Sim hiện cho tân binh **0đ thưởng**; Cường nói *"hồ sơ mới cũng có nhiều thưởng"*. Cần biết: thưởng tân binh thực tế là gì (mốc? thời hạn? bao nhiêu?) | Đây là **số POLICY thật** — agent không được tự bịa (CLAUDE.md §5). **CHẶN** baseline tân binh của SIM-4 | 2026-07-25 |
| **Q-02** | **`D-EXT-02`: Google Maps API key** hiện không hợp lệ (`REQUEST_DENIED`, 64 hex ≠ định dạng `AIza…`) | Cần key đúng từ Google Cloud Console | 2026-07-24 |
| **Q-03** | **`D-POL-04`: corpus của Khánh** thiếu policy Vận Doanh 23/02/2026 (bỏ phạt ≤70% + khoán tuần) → F0 có thể trích dẫn policy CŨ | File thuộc claim của Khánh, agent không tự sửa | 2026-07-24 |

## ✅ ĐÃ CHECK XONG

*(chưa có — chuyển mục từ bảng trên xuống đây kèm ngày + verdict khi Cường duyệt)*
