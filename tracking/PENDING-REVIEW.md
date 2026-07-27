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
| **V-06** | **SIM-5 data mới + bộ metric** — dashboard chạy trên bộ 90 ngày vừa regen; kiểm `sim_metrics.full_report` (chờ khách, mật độ hex×giờ). Tab ⚖️ A/B vẫn CHƯA làm (nợ SIM-4) | Dashboard + `scripts/regen_mock.py` | 2026-07-26 (UPDATE-049) |
| ~~**V-07**~~ | **SUPERSEDED 2026-07-27 bởi UPDATE-052 (D-SIM-10 DONE-CODE):** sim nhiều ngày đã được ưu tiên và triển khai; không còn là quyết định mở hướng. | UPDATE-050 → UPDATE-052 | closed as decision; visual verdicts remain separate |
| **V-08** | **Sim nhiều ngày + data liên tục** — (a) bảng ngày-qua-ngày UPDATE-052 §4 L1: biến động **5→18 cuốc/ngày** của cùng tài xế có hợp lý không? (b) UPDATE-053 §2: **autocorr ngày-qua-ngày ≈ 0** (chưa có persistence hành vi — ngày nghỉ/thói quen/ốm) có chấp nhận được cho bản publish mock, hay cần `D-SIM-16` trước? | UPDATE-052 §4 + UPDATE-053 §2 | 2026-07-26 |
| **V-09** | **SIM-XANH dashboard mới** — thứ tự xem: tab **Replay** (kéo slider quanh 07:00/18:00), tab **Hành trình** (d-41 P4: Gantt palette mới + vạch advice + sao/mission/tân binh), tab **Thế giới song song** (bấm Chạy cặp A/B; heatmap độ nhạy nếu sweep xong) | `uv run --extra viz streamlit run src/gsm_sim/dashboard.py` (UPDATE-057 §7) | 2026-07-26 |
| **V-10** | **Track UI — web app thật trên nền Khánh** (UPDATE-059..063). Thứ tự xem: (1) **App tài xế** `http://localhost:8010/app/` — Xanh Now (pill payout DATA THẬT d-19 · demand hex cyan · badge mock), bấm 🤖 **Trợ Lý Xanh** đổi 3 khung giờ (9h feasible / 19h nói thật không khả thi / 21h30 im lặng), màn **Thu nhập** (payout mặc định · gross tách · est_net "—"), **Cài đặt** đổi hồ sơ (thử `cp-0` → bot im lặng đúng "chưa phủ đội car"); (2) **Khu Mô phỏng** `/app/mo-phong/` — Replay bấm ▶ quanh 07:00/18:00, Hành trình (Gantt + income 4 nguồn + marker sự kiện + bảng offer), A/B bấm chạy cặp (~40s, đọc warning 1-seed), Độ nhạy (heatmap ✳). Server: `uv run uvicorn app.main:app --app-dir ui/backend --port 8010` | UPDATE-063 §Kịch bản | 2026-07-26 |
| **V-11** | **Fare parity gate** — tại `/app/` chạy incoming → active → completed; đối chiếu route API và UI `gross=19.450đ`, `payout=14.588đ`, `sim-policy-v0 · MOCK` cho fixture 3,5km; kiểm tra income pill/chart/ledger không đổi. Mở `/app/mo-phong/` và đối chiếu offer gross với engine `PolicyBundle`. | UPDATE-073 §Visual verification | 2026-07-27 |

## ❓ QUYẾT ĐỊNH CẦN CƯỜNG CHỐT (không phải visual)

| Mã | Cần chốt gì | Vì sao cần Cường | Từ ngày |
|---|---|---|---|
| ~~Q-01~~ | ✅ **RESOLVED-BY-FETCH 2026-07-26** (Cường cho phép tự fetch): cấu trúc thật từ greensm.com — bike: combo 810k (clawback nếu <200 cuốc/tháng×2 tháng), mốc ≥50 cuốc/7 ngày đầu, bảo lãnh doanh thu 90 ngày (số image-locked → PROXY); taxi 3M/90 ngày làm tham chiếu. Mô hình hoá ở Phase 2 SIM-XANH với nhãn nguồn + confidence; SỐ THẬT vẫn chờ GSM (D-POL-05) | — | đóng 2026-07-26 |
| ~~Q-02~~ | ✅ **CLOSED 2026-07-26** (Cường hỏi free alternatives): KHÔNG cần Google key — OSRM (routing, không key, đã test) + Stadia (tiles/geocode) + OSM data (geometry/trạm đã dùng từ đầu). OSRM đưa vào SIM ở Phase 1 SIM-XANH | — | đóng 2026-07-26 |
| **Q-03** | **`D-POL-04`: corpus của Khánh** thiếu policy Vận Doanh 23/02/2026 (bỏ phạt ≤70% + khoán tuần) → F0 có thể trích dẫn policy CŨ | File thuộc claim của Khánh, agent không tự sửa | 2026-07-24 |
| **ĐA-01** | **Estimator thống nhất (shrinkage)** cho acceptance/completion — thay ≥5 estimator rời rạc + fallback 1.0 bịa. Đọc: `research/audit/2026-07-26-full-audit/README.md` §ĐA-01. Ảnh hưởng calibration ⇒ phải chạy lại sweep 30 seed sau khi duyệt | Đổi hành vi advice trên diện rộng — Cường chốt trước khi cài | 2026-07-27 |
| **ĐA-02** | **Mission knapsack biết CỬA SỔ GIỜ** — B1 (loại mission ngoài cửa sổ + cap effort) làm ngay được; B2 (cuốc đếm chung cho mission lồng nhau) **chặn bởi D-POL-05** (chính sách đếm thật của GSM) | Cần chốt B1 làm ngay hay chờ trọn gói | 2026-07-27 |
| **ĐA-03** | **Gói S2 còn lại**: p_accept/avg_dist cá nhân hoá (đường tham số đã mở ở UPDATE-069, call site chưa truyền) | Đổi số E[payout] mọi advice F1/F2 | 2026-07-27 |
| **ĐA-04** | **AdviceCadencePolicy dùng chung** (sim + UI): anchor theo PHA CA thay wall-clock, priority, cooldown; kèm sửa **adherence washout** (D-A3-01) | Hiện có 3 cadence khác nhau; Δ A/B đang đo trên cadence product không ship | 2026-07-27 |
| **ĐA-05** | **Hợp nhất store adherence**: advice_id content-addressable, chọn store canonical (EpisodeStore vs jsonl vs sim events) | Quyết định kiến trúc — vòng đo §12 đang hở | 2026-07-27 |
| **ĐA-06** | **Một giọng nói**: template trả `list[card]` theo `ui/contracts/advice.json` thay vì blob 5-solver; thống nhất xưng hô | Hiện UI cards và pipeline C6 là 2 giọng, không map được sang nhau | 2026-07-27 |

## ✅ ĐÃ CHECK XONG

*(chưa có — chuyển mục từ bảng trên xuống đây kèm ngày + verdict khi Cường duyệt)*
