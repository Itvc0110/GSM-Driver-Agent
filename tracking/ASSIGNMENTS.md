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
## Lịch sử (tiếp)

| Ngày claim → xong | Người | Việc | Kết quả / bàn giao |
| --- | --- | --- | --- |
| 2026-08-03 → 2026-08-03 | Cường + Khánh (user-authorized agent) | AdviceCheckpoint P0–P5 | **DONE-CODE / V-25 BLOCKED** — UPDATE-126; root 978/4skip, backend 84, Web smoke, comparator 5/5 identical. Flutter analyze/test/device visual chưa chạy vì SDK vắng; flag v2 vẫn off, presenter vẫn template. Không dùng subagent vì runtime không có Luna. |
| 2026-07-26 → 2026-08-03 | Khánh | T-009b (Flutter mobile song song) | Claim path `ui/driver_app/` được chính Cường + Khánh release để thi công AdviceCheckpoint; trạng thái sản phẩm/visual cũ vẫn giữ trong TODO/PENDING-REVIEW. |
| 2026-07-27 → 2026-08-03 | Cường | UI-FARE-01 | Claim path `ui/backend/` + `ui/web/` được chính Cường + Khánh release; V-16 vẫn chờ verdict, không bị đóng bởi việc release path. |
| 2026-07-29 → 2026-08-03 | Cường (agent) | md-refresh + PLAN-cycle-wx Phần B | Claim quá hạn trên `tracking/*` và các path liên quan được chính Cường + Khánh release; các TODO chưa xong vẫn giữ nguyên trạng thái. |
| 2026-08-03 → 2026-08-03 | Cường (agent) | UPDATE-128: kiểm khoá ngoài bằng gọi thật + ranh giới KHUYÊN MỀM KHÔNG ĐO | `.env`/`.env.example`, `ui/backend/app/routers/routing.py`, `ui/backend/app/routers/advice.py`, `src/gsm_core/lifecycle/{advice_topics.py,projections.py}`, `ui/web/js/cards.js`, `ui/web/index.html`, `ui/contracts/advice_action.json`, `specs/{advisor-objective-model-v2,adherence-measurement}.md`, `specs/simulation/{d-m3-04-*,e11-*}`, `tracking/*` + 3 file test mới. **KHÔNG đụng `ui/driver_app/`** (claim đang hoạt động của Khánh) ⇒ phần thời tiết + Flutter là của Khánh (`SOFT-ADVICE-02`). ⚠ Có sửa `routing.py` — file Khánh vừa làm ở UPDATE-120, nhưng claim đó đã ở Lịch sử (DONE-CODE, đã push) nên không còn hoạt động; sửa là **fix lỗi tên miền + nối biến env**, không đụng `quote_distance`/fare. **DONE-CODE**, chờ `V-26`. |
| 2026-08-02 → 2026-08-02 | Khánh (agent) | Audit map lib sim (leafmap) vs UI (Leaflet) — nghi ngờ lệch tọa độ gây OSRM chỉ đường xuyên nhà | **Chỉ audit, KHÔNG sửa code** (Khánh quyết định dừng ở tìm nguyên nhân, chưa fix). Kết luận: không có lệch tọa độ giữa 2 lib (cùng WGS84 `[lat,lng]`, OSRM lon/lat đã convert đúng ở `routing.py:68-69`). Nguyên nhân thật của "chim bay": (1) sim replay Track UI vẽ thẳng giữa 2 đầu mút segment vì `world.py`/`geo.py` RoadMatrix chưa từng có polyline thật — MODEL GAP by-design; (2) `routing.py`'s fallback khi OSRM public chết dùng `generate_street_snapped_segment()` — đường cong sin GIẢ, gắn nhãn sai `source: "hanoi_street_graph_engine"` dù module `hanoi_graph.py` (đồ thị 18 node cũ, neo hành lang Hoàn Kiếm–Royal City, không phải Đống Đa) không hề được import — dead code, không ai nối (cùng họ bẫy #9/V-22 `trajectory.py`). Chưa ghi vào DEFERRED.md/TODO.md — để Khánh/Cường quyết có log tiếp hay không. |
| 2026-08-03 → 2026-08-03 | Khánh (agent) | UPDATE-121: nghiên cứu cơ chế AdviceCheckpoint + vị trí tích hợp Agent | `research/audit/2026-08-03-advice-checkpoint/` (tạo), `research/README.md`, `tracking/{PENDING-REVIEW,TODO,ASSIGNMENTS}.md` — **KHÔNG sửa file code nào**. Kết quả: sim và sản phẩm là ảnh gương lỗi của nhau; `AdvisorPipeline` mồ côi (0 caller sản phẩm); `superseded`/`expired` chưa có producer dù consumer sẵn sàng. Kế hoạch 6 GĐ — **GĐ0 bị chặn bởi Q-13/Q-14/V-21** ⇒ mở `Q-15` hỏi Cường thứ tự. Chưa code theo đúng yêu cầu Khánh. |
| 2026-08-02 → 2026-08-03 | Khánh (agent) | UPDATE-120 (đánh số lại từ 119 — trùng số với `UPDATE-119-week2-report-mentor.md` của Cường): routing 3-tier OSRM→GraphHopper→đường thẳng trung thực (tiếp nối audit ở trên) | `ui/backend/app/routers/routing.py`, `ui/backend/app/models.py`, `ui/web/js/app.js` (chỉ polyline styling + nav-state), `ui/backend/tests/test_routing_api.py`, `.env`/`.env.example` — KHÔNG đụng `quote_distance`/fare logic. **DONE-CODE, đã push origin/main.** 66/66 test `ui/backend/tests` xanh + 935/4skip suite chính, live-test key GraphHopper thật (HTTP 200), visual review cả 3 tier bằng Playwright (screenshot thật) — xem V-24 ở PENDING-REVIEW.md (đổi từ V-23 vì cùng lý do trùng số). Khánh waive visual gate trực tiếp trong hội thoại 2026-08-03 (đồng sở hữu), Cường xem SAU khi đã lên main. |

## Lịch sử

| Ngày claim → xong | Người | Việc | Kết quả / bàn giao |
| --- | --- | --- | --- |
| 2026-07-28 → 2026-07-29 | Cường (agent) | Cycle P/R/V/W (T-045a/b, BUG-EVAL-ARGMAX, B-02 registry, ĐA-05 lifecycle store) | UPDATE-083..091; suite 707/5; fingerprint IDENTICAL; ĐA-05 DONE-CODE chờ verdict |
| 2026-07-21 → 2026-07-22 | Khánh | T-004 | Audit nguồn T1 official (sitemap + Driver Center), curate source Bike/RTO/Platform, kiểm tra track/geo/lifecycle và raw evidence. Bàn giao: source register và corpus text-only 7 nguồn current, có provenance + guardrail; HTML/asset/OCR/crawler lặp vẫn loại, không tạo runtime/contract. |
| 2026-07-21 → 2026-07-26 | Khánh | T-009 (UI clone) | Làm ở repo riêng `Quockhanh0712/uiuxgsm` (Stitch web demo + Flutter app + FastAPI gateway + contracts). Bàn giao: `uiuxgsm-main.zip` → Cường quyết định import vào `ui/` làm nền UI thật (UPDATE-059, DIRECTIVES §11). Tiếp nối: T-009b (Flutter song song) |
| 2026-07-21 → 2026-07-27 | Cường | T-018 / SIM successor | Successor SIM-1..5 và SIM-XANH code-complete (UPDATE-044..058); legacy claim released. V-01..V-06, V-08/V-09 còn chờ verdict. |
| 2026-07-26 → 2026-07-27 | Cường | Track UI U0–U4 + UX-CARDS + R1/R4 | Code-complete (UPDATE-059..063, 067..068); claim released, V-10 còn chờ verdict. Thay đổi `ui/contracts/` vẫn phải phối hợp Khánh/T-009b. |
