> **⚠ Đính chính trạng thái 2026-07-29 (đọc trước):** UX-CARDS → DONE-CODE (UPDATE-067, chờ V-10) · Q2 A3 audit → XONG (UPDATE-069/070) · Q5 time-engineering → ĐÃ LÀM (T-045 b0, UPDATE-083: 3 lỗi thời gian, 6 test) · Q6 adherence đa tín hiệu → spec `specs/adherence-measurement.md` + hạ tầng ĐÃ KÍN (Cycle W: store canonical, `decision_adherence`/`event_adherence`) · mục "3 câu cần Cường chốt" → CLOSED (DIRECTIVES §12) · N5 CI → `.github/workflows/ci.yml` đã tồn tại · thứ tự thực tế sau audit: T-041/T-045 → ĐA-08/09 → Cycle V (B-02) → Cycle W (ĐA-05); R1–R4 UI-sim redesign chưa làm; R5-A xong, R5-B QUOTA-BLOCKED.

# BACKLOG — loạt câu hỏi/ý tưởng Cường 2026-07-27 (rạng sáng)

> **STATUS NOTE — 2026-07-27:** đây là backlog lịch sử trước khi audit/reconcile hoàn tất. F0 và
> proactive cards đã chốt trong DIRECTIVES §12; architecture B đã chốt trong §13. “UI sim giống
> UI app” ở R1 nghĩa dùng chung design system, **không** có nghĩa cùng audience/data: simulation
> demo là dispatcher/evaluation view, driver app demo + Advisor là single-driver view. Trạng thái
> mới nhất: `research/audit/2026-07-27-current-state/README.md`.

## 🎯 YÊU CẦU BỔ SUNG đợt 2 (Cường ~02:00) — LÀM SAU KHI XONG AUDIT, mỗi mục PLAN KỸ trước

> Nguyên tắc Cường nhấn mạnh: *"các phần tôi đã yêu cầu phải được làm thật kĩ"* — cái đã làm
> **càng phải double-check lại**; *"luôn plan kĩ trước khi làm bất cứ thứ gì"*.

| # | Yêu cầu | Ghi chú triển khai |
|---|---|---|
| R1 | **UI sim phải GIỐNG UI app** | Khu Mô phỏng hiện là trang desktop riêng — phải đưa về CÙNG ngôn ngữ thiết kế với app tài xế (shell, components, tokens); cân nhắc nhúng thành tab/màn trong app thay vì trang rời |
| R2 | **Hướng người dùng: HIỂU và VISUALIZE quyết định của advisor** | Không chỉ hiện advice — vẽ được VÌ SAO: input nào (điểm/tỷ lệ/quỹ giờ) → solver nào → ràng buộc nào bind → kết luận; dạng decision-trace trực quan (flow ngắn, không phải log thô) |
| R3 | **Show TỐI GIẢN tools/tính năng agent dùng** — học cách show của **CrewAI** | Kiểu agent-execution-trace: mỗi bước 1 dòng gọn (solver được gọi · input digest · output digest · verifier pass/fail), collapse/expand; nghiên cứu UI CrewAI (web research) trước khi thiết kế |
| R4 | **Sim TUA/DỪNG được, SINH ĐỘNG** | Replay đã có ▶/slider — nâng: pause/tốc độ ×1/×4/×16, tua tới sự kiện kế (advice/mission/thưởng), hiệu ứng chuyển động mượt, âm lượng sự kiện (đơn nổ ra, trạm pin bận) |
| R5 | **DOUBLE-CHECK PASS toàn bộ phần đã làm trong đêm** | Track UI (U0-U4) + UX-CARDS + 7 fix audit + A2 gate: rà lại thật kỹ từng cái (một phần trùng A3/A4 + V-10 — phần KHÔNG trùng phải rà riêng, đặc biệt cards.js flow + adapter tiền) |

Thứ tự sau audit: R5 (double-check) → R1+R2+R3 (một cycle UI-sim redesign có plan) → R4 (cùng cycle R1 nếu gọn).

Nguồn: message Cường trong lúc chờ quota reset. Phân loại theo KHẢ THI NGAY (solo, không cần
subagent) / SAU QUOTA (cần agent/workflow) / CẦN CƯỜNG CHỐT. Trạng thái cập nhật tại chỗ.

## ⚡ LÀM NGAY ĐƯỢC (solo — đang/sẽ chạy trong lúc chờ)

| # | Việc | Trạng thái |
|---|---|---|
| N1 | **Re-verify MOCK data 30-seed** (`scripts/verify_realdata_stats.py`) — "checking the MOCK data all over again" tầng thống kê | ✅ 2026-07-27: bike-gaps=0, driver-days bike 3232/car 1059 — sạch |
| N2 | **Quyết định scope F0**: Cường chốt "GIỮ TỐI GIẢN" (FAQ cấu trúc + template + citation, không LLM tự do, không chat) → đã ghi DIRECTIVES §12.1 | ✅ ghi xong |
| N3 | **Hình thái advisor**: Cường chốt **PROACTIVE CARDS** + nút Làm theo/Bỏ qua (đo adherence explicit) → DIRECTIVES §12.2; design note + implement = việc UX-CARDS bên dưới | ✅ chốt — triển khai ở UX-CARDS |
| N4 | **UI fancy cho stakeholder** — được duyệt; làm SAU/CÙNG UX-CARDS (không đánh bóng thứ sắp đổi) | ĐƯỢC DUYỆT — hàng đợi |
| N5 | **Draft CI pipeline** — được duyệt; draft `.github/workflows/` (kích hoạt cần remote/billing — Cường quyết khi push) | ĐƯỢC DUYỆT — hàng đợi |
| UX-CARDS | **Redesign luồng advice trên web UI theo proactive cards** + instrumentation adherence (advice_id → follow/dismiss log, contract mới) — việc chính được ưu tiên | 🔨 KẾ TIẾP (xen kẽ audit) |

## 🕑 SAU QUOTA (cần agent — đã xếp hàng trong kế hoạch audit)

| # | Việc | Ghi chú |
|---|---|---|
| Q1 | Verify 11 finding A1 treo + **S2 bundle fix** | đầu hàng đợi |
| Q2 | **A3 agent-system audit** — trong đó CÓ SẴN các câu Cường hỏi: "output của từng layer + format + cách AI nói với tài xế" (template/tone/verifier), "pipeline convert output→action của actor" (advice_bridge mapping + BEHAV-3 throttle + D-SIM-14), "core dùng memory/former states đúng chưa" (DriverMemory→S1 + episode_store), "khi nào give advice" (gate + cadence — nối ĐA-01) | mở rộng scope A3 theo 4 câu này |
| Q3 | **Quét toàn repo/docs bằng subagent** — consistency docs vs code sau 3 track dồn dập (SCOPE/specs/flow drawio vs hiện trạng) | thêm vào A4 |
| Q4 | **Web research phần mơ hồ**: (a) app tài xế thật (Grab/Be/XanhSM) đưa advice/nudge thế nào — benchmark UX; (b) nghiên cứu HCI về driver-distraction & notification khi đang lái (an toàn!); (c) chính sách GSM mới nếu có | WebSearch/WebFetch — có thể thử trước quota, ưu tiên sau A3 |
| Q5 | **"Time engineering" trong sim đủ tốt chưa** — độ phân giải tick, event-time (DEMAND-4 đã confirmed lỗi sampling), răng cưa giờ (D-SIM-19), timezone conventions (S8S9-2) — gom thành mục audit riêng trong A4 | A4 |
| Q6 | **Đo "tài xế có làm theo không" NHIỀU CÁCH cùng lúc** — sim đã có: adherence coin + `advice_given/followed` events + A/B paired; THIẾU: đo từ data hành vi (so trước/sau advice trên realized), multi-signal (explicit dismiss/accept trên UI + hành vi im lặng); thiết kế instrumentation contract cho UI (advice_id → driver action log) | brainstorm + spec sau N3 |

## ❓ CẦN CƯỜNG CHỐT (đã hỏi qua AskUserQuestion 2026-07-27)

1. Xác nhận **bỏ F0 policy Q&A** khỏi minimum scope (đổi tuyên bố scope gốc — cần xác nhận tường minh).
2. Hình thái advisor khi không còn chat: proactive cards / hybrid (cards + hỏi-lại-được) / khác.
3. Ưu tiên việc song song kế tiếp (fancy UI vs UX research vs CI).
