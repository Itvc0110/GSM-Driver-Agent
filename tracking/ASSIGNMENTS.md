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
| 2026-07-21 | Cường | T-018 (kế tiếp T-019, T-020) | `src/gsm_sim/`, `configs/`, `tests/`, `specs/simulation-*` + `sim-policy-bundle-v0` + `advisor-optimization-layer-a`, `pyproject.toml` | DOING | Simulator core; AI agent làm dưới claim này |
| 2026-07-26 | Cường | **Track UI** (DIRECTIVES §11, phase U0–U4) | `ui/backend/`, `ui/web/`, `ui/contracts/`, `ui/design-tokens.json`, `ui/docs/` | DOING | Build web app + backend trên nền import T-009 của Khánh; **đổi `ui/contracts/` phải báo Khánh**; AI agent làm dưới claim này |
| 2026-07-26 | Khánh | T-009b (Flutter mobile song song) | `ui/driver_app/` — KHÔNG ai khác đụng | READY | Bắt kịp web qua `ui/contracts/` + `ui/design-tokens.json` + `ui/docs/SCREEN-PARITY.md`; cùng backend FastAPI với web |

## Lịch sử

| Ngày claim → xong | Người | Việc | Kết quả / bàn giao |
| --- | --- | --- | --- |
| | | | |
| 2026-07-21 → 2026-07-22 | Khánh | T-004 | Audit nguồn T1 official (sitemap + Driver Center), curate source Bike/RTO/Platform, kiểm tra track/geo/lifecycle và raw evidence. Bàn giao: source register và corpus text-only 7 nguồn current, có provenance + guardrail; HTML/asset/OCR/crawler lặp vẫn loại, không tạo runtime/contract. |
| 2026-07-21 → 2026-07-26 | Khánh | T-009 (UI clone) | Làm ở repo riêng `Quockhanh0712/uiuxgsm` (Stitch web demo + Flutter app + FastAPI gateway + contracts). Bàn giao: `uiuxgsm-main.zip` → Cường quyết định import vào `ui/` làm nền UI thật (UPDATE-059, DIRECTIVES §11). Tiếp nối: T-009b (Flutter song song) |
