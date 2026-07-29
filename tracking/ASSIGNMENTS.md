# ASSIGNMENTS — Bảng tự nhận việc (self-claim)

Cập nhật thiết kế: 2026-07-20 · Team: **Cường**, **Khánh** · **KHÔNG có ai là người giao việc.**

Cơ chế: công việc sống trong `tracking/TODO.md` và có thể được cập nhật liên tục. **Đầu mỗi session làm việc**, mỗi người chủ động **tự nhận (claim)** việc mình sẽ làm bằng cách thêm dòng vào bảng "Claim đang hoạt động" — để người còn lại nhìn vào là biết tránh nhận trùng việc/đụng file.

## Quy tắc claim

1. **Đầu session**: đọc bảng claim hiện tại → chọn việc trong TODO chưa ai claim → thêm dòng claim (ngày, người, T-###, phạm vi files/folders dự kiến đụng vào, trạng thái `DOING`).
2. **Một việc chỉ một người claim.** Muốn làm chung một mục lớn → tách thành 2 dòng claim với phạm vi files không giao nhau.
3. **Không sửa files nằm trong phạm vi claim đang hoạt động của người kia.** Bắt buộc phải sửa → nhắn trao đổi trước, ghi chú vào dòng claim.
4. **Kết thúc session / xong việc**: cập nhật trạng thái (`DONE` / `PAUSED` + ghi chú bàn giao: đã làm tới đâu, còn gì), rồi chuyển dòng xuống mục Lịch sử. Đồng thời cập nhật trạng thái mục tương ứng trong TODO.
5. **AI coding agent làm việc dưới claim của người đang điều khiển nó** — agent không tự claim, không làm ngoài phạm vi claim đó, và phải kiểm tra bảng này trước khi sửa file.
6. **Claim quá 3 ngày không cập nhật** coi như tự giải phóng (released) — người kia được quyền nhận lại, ghi chú rõ khi làm vậy.

## Claim đang hoạt động

| Ngày | Người | Việc (T-###) | Phạm vi files/folders | Trạng thái | Ghi chú |
| --- | --- | --- | --- | --- | --- |
| 2026-07-26 | Khánh | T-009b (Flutter mobile song song) | `ui/driver_app/` — KHÔNG ai khác đụng | READY | Bắt kịp web qua `ui/contracts/` + `ui/design-tokens.json` + `ui/docs/SCREEN-PARITY.md`; cùng backend FastAPI với web |
| 2026-07-27 | Cường | UI-FARE-01 (đồng nhất giá cuốc demo) | `ui/backend/`, `ui/web/`, pricing tests và tracking/docs liên quan; KHÔNG đụng `ui/driver_app/` | WAITING-VERDICT | Code/tests/technical visual flow complete; user verdict **V-16** (đánh số lại từ V-11) required |
| 2026-07-29 | Cường (agent) | md-refresh toàn repo + PLAN-cycle-wx Phần B (B1..B4) + tích hợp UPDATE-092 | `tracking/*` (trừ updates lịch sử), `planning/*`, `specs/*`, `research/*`, `schemas/*.md`, `CLAUDE.md`, `src/gsm_sim/{parallel,sim_metrics}.py`, `tests/test_net_metric.py`, `ui/` (docs/contracts — phối hợp Khánh), `templates/` (banner), `docs/superpowers/` (banner) | DOING | Cycle W DONE-CODE (UPDATE-091); teammate UPDATE-092 đang tích hợp |

## Lịch sử

| Ngày claim → xong | Người | Việc | Kết quả / bàn giao |
| --- | --- | --- | --- |
| 2026-07-28 → 2026-07-29 | Cường (agent) | Cycle P/R/V/W (T-045a/b, BUG-EVAL-ARGMAX, B-02 registry, ĐA-05 lifecycle store) | UPDATE-083..091; suite 707/5; fingerprint IDENTICAL; ĐA-05 DONE-CODE chờ verdict |
| 2026-07-21 → 2026-07-22 | Khánh | T-004 | Audit nguồn T1 official (sitemap + Driver Center), curate source Bike/RTO/Platform, kiểm tra track/geo/lifecycle và raw evidence. Bàn giao: source register và corpus text-only 7 nguồn current, có provenance + guardrail; HTML/asset/OCR/crawler lặp vẫn loại, không tạo runtime/contract. |
| 2026-07-21 → 2026-07-26 | Khánh | T-009 (UI clone) | Làm ở repo riêng `Quockhanh0712/uiuxgsm` (Stitch web demo + Flutter app + FastAPI gateway + contracts). Bàn giao: `uiuxgsm-main.zip` → Cường quyết định import vào `ui/` làm nền UI thật (UPDATE-059, DIRECTIVES §11). Tiếp nối: T-009b (Flutter song song) |
| 2026-07-21 → 2026-07-27 | Cường | T-018 / SIM successor | Successor SIM-1..5 và SIM-XANH code-complete (UPDATE-044..058); legacy claim released. V-01..V-06, V-08/V-09 còn chờ verdict. |
| 2026-07-26 → 2026-07-27 | Cường | Track UI U0–U4 + UX-CARDS + R1/R4 | Code-complete (UPDATE-059..063, 067..068); claim released, V-10 còn chờ verdict. Thay đổi `ui/contracts/` vẫn phải phối hợp Khánh/T-009b. |
