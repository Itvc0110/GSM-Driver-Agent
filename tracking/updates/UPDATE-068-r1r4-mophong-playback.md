# UPDATE-068 — R1+R4: khu Mô phỏng đồng ngôn ngữ app + playback nâng cao

Ngày: 2026-07-27 (~03:00) · Track: UI/UX (BACKLOG R1/R4, DIRECTIVES §12.5) · Plan duyệt riêng ·
Chạy SONG SONG audit (chỉ đụng `ui/web/mo-phong/*` + CSS additive — vùng không bị agent audit đọc;
backend sim.py cố tình KHÔNG đụng vì refuter STATS-1 đang đọc lúc đó).

## 1. Files & nội dung

- `ui/web/mo-phong/index.html`: header đổi sang pattern app (circle-btn ← · pill "Khu Mô phỏng" ·
  mock-badge — R1); **tab-intro 1 câu hướng người dùng** cho cả 4 tab (giọng app); Replay thêm
  speed chips ×1/×4/×16 + nút **⏭ sự kiện** + khung **event-feed** kiểu CrewAI-terminal.
- `ui/web/mo-phong/mo-phong.js`: SPEEDS (step/interval theo tốc độ, đổi nhịp ngay khi đang chạy);
  `loadEvents()` gộp events từ `/sim/journey` của **top-6 tài xế bận nhất** (endpoint sẵn có, run
  cache — không sửa backend); `pumpFeed` đẩy dòng `[07:42] d-14 · mission +30.000đ` màu theo loại
  event, giữ 40 dòng, auto-scroll; `jumpNextEvent` nhảy slider tới event kế; **flash-ring marker**
  actor vừa có sự kiện (1.8s); kéo slider tay thì seekFeed không dội quá khứ.
- `ui/web/theme.css`: CHỈ THÊM class (.mp-topbar/.feed/.speed-chip/.tab-intro/.flash-ring) —
  không sửa class cũ.

## 2. Kiểm chứng

- `node --check` sạch; live `:8010/app/mo-phong/` 200 (html+js); **theme-sync 4 passed** (class
  cũ không đổi — app không bị ảnh hưởng).
- Hành vi kiểm bằng code-path (play/pause/speed/jump/feed đều thuần client trên data sẵn);
  verdict mắt người: nhập **V-10** — kịch bản thêm: Replay bấm ▶ xem feed chảy + đổi ×16 +
  bấm ⏭ vài lần xem flash marker.

## 3. Flaws / giới hạn (ghi thật)

- Feed chỉ phủ **6 tài xế bận nhất** (chọn để nhẹ — silent cap GHI RÕ ngay trên UI); events
  toàn-cục cần thêm field vào `/sim/replay` — để cycle R2/R3 (sửa backend sau khi audit xong).
- trip_rated không vào feed (journey events không phát nó — đúng thiết kế U3, tránh spam 700 dòng).
- Speed ×16 bỏ qua event giữa 2 frame? KHÔNG — pumpFeed quét theo (tPrev, tNow] nên không sót.

---
**⏳ PENDING-REVIEW:** V-01..V-09 · **V-10** (app + cards + mo-phong playback) · Q-03 · ĐA-01/02/03.
