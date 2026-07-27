# CHỈ THỊ CHƯƠNG TRÌNH — Cường, 2026-07-24 (BẢN GHI BỀN, đọc đầu mỗi session)

> File này ghi lại **nguyên văn ý chỉ đạo** của Cường trong 3 lượt trao đổi quan trọng
> (data-luôn-mock / external API / simulation overhaul / C7 / mock UI / keys).
> **Mục đích: chống mất ngữ cảnh khi compaction.** Khi xung đột với hiểu biết trong đầu,
> **file này thắng**. Cập nhật khi Cường ra chỉ thị mới.

## 1. DATA — luôn là MOCK (chốt)

- **Bản publish cuối cùng của chúng ta CHẠY TRÊN MOCK DATA.** Đó là lý do phải gen +
  mở rộng data nhiều vòng.
- **Schema / tên bảng / tên cột = THẬT** (GSM cấp, 13 bảng `l1r`). **Chỉ NỘI DUNG do ta gen.**
- **Defer toàn bộ techstack cloud** (GCP/BigQuery) sang kế hoạch tương lai khi ghép data
  thật của GSM → `DEFERRED D-GCP-01`. Plan PI-3 đã viết sẵn (`specs/real-data/04-*.md`),
  chỉ cần bật khi cần.
- **Hạ tầng LOCAL hết**: database, cache, vectordb (nếu dùng) đều local →
  `DEFERRED D-LOCAL-01`. Ghi chú sẵn chỗ nào sau này gợi ý nâng cấp lên cloud.

## 2. EXTERNAL API — dùng MỌI API có ích

Yêu cầu: nghiên cứu kỹ + đề xuất **lấy được thông tin hữu ích gì**, **API nào cần**,
**dự đoán chi phí**, và **tính năng nào sinh ra từ đó** (vd cảnh báo tắc đường, cảnh báo
sắp mưa, hoặc **dữ liệu để mô hình hóa thành bài toán tối ưu**).

**KEY ĐÃ CÓ (trong `.env`, gitignored) — đã TEST OK 2026-07-24:**

| Dịch vụ | Trạng thái | Dùng để |
|---|---|---|
| **OpenRouter** (`deepseek/deepseek-v4-flash`) | ✅ OK — rẻ nhất (~$0.09/M in) | LLM Composer chính |
| **OpenAI** (`gpt-4o-mini`) | ✅ cấu hình | Fallback LLM |
| **WeatherAPI** | ✅ OK (có forecast + **alerts**) | Cảnh báo mưa, weather-aware F1/F2 |
| **OSRM** (public, **không cần key**) | ✅ OK (2.38km/3.5ph HN) | Route/ETA thật, **route-deviation** UC7 |
| **Stadia Maps** | ✅ OK (geocoding + **tiles**) | Bản đồ cho UI, geocode |
| **Jina Reader** | ✅ OK (fetch greensm.com → 13k ký tự MD) | Crawl policy/sự kiện ảnh hưởng công việc |
| **Langfuse** (US cloud) | ✅ cấu hình | Observability LLM |
| **Google Maps** | ✅ **KHÔNG CẦN** (Cường chốt 2026-07-26) — OSRM + Stadia + OSM thay thế đủ | D-EXT-02 ĐÓNG |

**Lưu ý:** mọi API đều có free tier riêng → **bắt buộc cache local** + fallback offline;
external chỉ là **PROXY/EXTERNAL có nhãn**, KHÔNG bao giờ thành số tài chính/policy (§5).

## 3. MOCK "thật nhất" cho phần thiếu data (`specs/real-data/05-gap-analysis-and-supplements.md`)

- Fetch thật kỹ; **nếu không có dữ liệu thật → tạo data sao cho THẬT NHẤT có thể**.
- **Note rõ cái nào là mock** để sau này lắp hệ thống thật không nhầm…
- …**NHƯNG phải INVISIBLE với advisor agent**: nhãn mock chỉ để **chúng ta** replace sau,
  agent không được nhìn thấy/không được dùng nhãn đó trong lập luận.
  ⇒ Thiết kế: nhãn nguồn nằm ở **tầng data/metadata (manifest, cột `source`)**, KHÔNG
  đưa vào context pack của agent.

## 4. C7 + RÀ SOÁT ĐỊNH KỲ MÔ HÌNH TỐI ƯU

- **Thiết kế, implement core, nâng cấp: AI agent tự lên ý tưởng**; kiểm chứng qua
  **metric + sim đã dựng**; **Cường approve các phần quan trọng**.
- **Cần lập kế hoạch KIỂM TRA ĐỊNH KỲ** cách các bài toán tối ưu được thiết lập:
  - các biến có đang được dùng ĐÚNG không?
  - bài toán có được thiết kế LOGIC không?
  - biến này có **thực sự nên** được dùng, hay thậm chí **có mô hình hóa được** không?
  - **Ví dụ Cường đưa:** *mưa không làm đổi vận tốc một khoảng cố định 20%* → nên dùng
    **agent reasoning** hay cách tiếp cận khác (giả sử sau này có biến weather thật).

## 5. SIMULATION OVERHAUL — **PHẦN RẤT QUAN TRỌNG, mảng riêng, docs + plan riêng**

Bối cảnh: **UI do Khánh làm**; **Simulation là phần ĐỘC LẬP** — có thể nối data output
vào sau, bên cạnh UI app.

**Yêu cầu (nguyên văn ý):**
1. Một **giả lập THỰC SỰ** với data đang dùng; tương lai thêm data thì **gán vào sim được**.
2. Tài xế **thực sự nhận cuốc, di chuyển, có mật độ**, v.v. như hiện tại **và hơn thế**.
3. Có **thống kê chung cho các metric**.
4. **Dịch được kết quả gợi ý của advisor → action của actor** trong simulation.
5. **State phải theo đúng data.**
6. **ĐẶC BIỆT — theo dõi hành trình 1 tài xế:**
   - mở đầu phiên làm việc;
   - **các thế giới song song**: khi **tự làm** vs khi **làm theo chỉ dẫn**;
   - có **nhận cuốc thật**, có **tỷ lệ nhận / hoàn thành**, v.v. (**phải làm kỹ**);
   - có **hành vi random**;
   - **đo được metric trên đúng driver đó**;
   - có thể sim **1 tài xế mới thiếu kinh nghiệm**, nhiều hành vi không tối ưu, **hồ sơ
     mới cũng có nhiều thưởng** → **baseline tốt**.
7. **Sim hiện còn nhiều phần rất tệ** — ví dụ **tỷ lệ hoàn thành chuyến tổng đang quá
   thấp so với thực tế** — và **chưa đủ chi tiết**.

## 6. MOCK UI để xem advice — **THAY THẾ bởi §11 (2026-07-26)**

- ~~Xây **mock UI** để **xem advice** (của phía ta; khác với UI clone của Khánh).~~
- Cường 2026-07-26: **không build UI mock nữa** — build thẳng UI thật trên nền UI của Khánh
  (import vào `ui/`). Xem §11 + `tracking/updates/UPDATE-059-*`.
- Ý "Stadia tiles + OSRM vẽ bản đồ/hành trình" vẫn sống — chuyển vào Track UI.

## 7. CÁCH LÀM VIỆC

- **Tập trung vào cái còn THIẾU, xây từng cái một**, nếu không cần gì thêm từ Cường.
- Cường approve các phần quan trọng; còn lại agent tự quyết.

## 8. Trạng thái các TRACK (cập nhật khi tiến triển)

| Track | Nội dung | Trạng thái |
|---|---|---|
| **A. SIM overhaul** | mảng riêng (§5) + chỉ thị SIM-XANH (§10) | ✅ **SIM-1..5 + SIM-XANH P0-P5 XONG** (UPDATE-044..058, manifest sạch `fda8e16`): đường THẬT OSRM (factor median 1.46) · rating/tân-binh/mission trong sim · sweep độ nhạy D-SIM-06 · dashboard palette-validated + Replay + tab A/B · data 90 ngày chuỗi liên tục. **Kế tiếp: Track UI** (§11) rồi **AUDIT** |
| **B. External data** | research + provider offline-first + cache local (§2) | ⏳ key đã có, chưa code |
| **C. Mock UI xem advice** | §6 | ❌ **THAY bằng Track UI (§11)** — không build mock UI riêng nữa |
| **UI. UI thật trên nền Khánh** | §11 | ✅ **U0-U4 XONG 2026-07-26** (UPDATE-059..063) + **UX-CARDS** (UPDATE-067: proactive cards + đo adherence + CI draft) + **R1/R4** (UPDATE-068: mo-phong đồng ngôn ngữ app, playback ×1/×4/×16, feed sự kiện). **Chờ verdict V-10** |
| **AUDIT toàn hệ** | §10.4 | ✅ **A1+A2+A3 XONG 2026-07-27** (UPDATE-064..070; report `research/audit/2026-07-26-full-audit/REPORT.md`): **152 agent · 179 finding · 118 CONFIRMED · 21 fix rows** (UPDATE-071 correction). Còn lại: **6 đề án ĐA-01..06 chờ Cường duyệt** + D-A3-01..06. **R5-A xong; R5-B QUOTA-BLOCKED**; sau đó R2/R3 |
| **D. C7 + rà soát mô hình** | §4 | ⏳ chưa bắt đầu |
| **E. Mock enrichment "thật nhất"** | §3 | ⏳ chưa bắt đầu |

## 9. Những gì ĐÃ XONG trước các chỉ thị này (nền tảng)

- 13 schema `l1r` khớp CHÍNH XÁC metadata GSM (gate test chống trôi).
- Generator mock 90 ngày / 110 profile (bike/rto/car/employee/premium), 4 vòng verify.
- **9 solver** phủ UC1–UC8; advisor pipeline C6 (router→composer→verifier) template-mode.
- Suite **378 test** xanh. Research đợt 1–4 (policy refresh + app features).

## 10. Chỉ thị bổ sung 2026-07-26 (Cường)

1. **SIM-XANH**: nâng cấp sim hết cỡ cho giống XanhSM thật — chi tiết state/actors/action, bám plan; **OSRM thay detour** những chỗ có thể; dashboard đẹp (taste-skill).
2. **D-SIM-06 TRƯỚC D-SIM-16** (sensitivity trước persistence).
3. **Q-01**: agent tự fetch trên mạng (đã fetch OK — xem PENDING-REVIEW).
4. **Thứ tự**: SIM-XANH → ~~Track C (mock UI advice)~~ **Track UI (§11)** → **AUDIT toàn bộ** data + hệ thống agent + **math modelling (quan trọng nhất)**.

## 11. Chỉ thị 2026-07-26 (Cường) — Track UI: UI thật trên nền UI của Khánh

Nguyên văn ý chính: *"nghiên cứu uiuxgsm-main.zip — phần UI được làm cho tới giờ của Khánh, biến nó
thành 1 phần của project… không cần build UI mock nữa mà build thẳng phần UI, gắn simulation vào
1 phần riêng trong UI, thiết kế lại theo phong cách đó, tông màu…"*

Đã chốt với Cường (AskUserQuestion 2026-07-26):
1. **Web app** là nền chính (tách từ `ui/demo_stitch_app.html`); **Khánh làm Flutter mobile song
   song** theo cơ chế contract-first: 1 backend FastAPI chung + `ui/contracts/` (JSON Schema
   versioned) + `ui/design-tokens.json` + `ui/docs/SCREEN-PARITY.md`; ranh giới file trong ASSIGNMENTS.
2. Sim **port hẳn vào web UI** thành khu "Mô phỏng" (Replay · Hành trình · A/B · heatmap) — UI chỉ
   đọc JSON từ engine, không tự tính.
3. Tông màu **theo Khánh 100%**: light + cyan `#00AFB9` — palette dataviz re-validate trên nền sáng.

Phase U0–U4, kế hoạch chi tiết: plan đã duyệt (xem UPDATE-059). Sau Track UI → AUDIT (giữ nguyên §10.4).

## 12. Chỉ thị 2026-07-27 (Cường, rạng sáng — chốt qua AskUserQuestion)

1. **Scope F0 ĐỔI: bỏ chat hỏi-đáp tự do → giữ dạng TỐI GIẢN**: mục "Chính sách" là FAQ CÓ CẤU
   TRÚC (danh sách câu hỏi định sẵn → trả lời template + citation từ corpus; KHÔNG LLM tự do).
   Corpus policy của Khánh (Q-03) giữ vai trò nguồn trích dẫn. Router/KB C6 phần free-text F0
   thành legacy (không xóa, ghi deprecated khi chạm tới).
2. **Hình thái advisor: PROACTIVE CARDS** (không chatbot): thẻ advice có cấu trúc xuất hiện đúng
   lúc — trước ca (brief) · trong ca (nudge NGẮN chỉ lúc dừng xe/đổi pin — an toàn khi lái) ·
   sau ca (recap); mỗi thẻ có nút **"Làm theo / Bỏ qua"** → log adherence EXPLICIT (nối với đo
   adherence trong sim/D-SIM-04).
3. **Việc song song được duyệt cả 4** (thứ tự tôi tự xếp): UX redesign theo cards + instrumentation
   adherence → web research UX/HCI nuôi thiết kế → UI fancy cho stakeholder → CI draft.
4. Loạt câu hỏi kiểm tra sâu (layer outputs, advice_bridge mapping, memory usage, time engineering,
   "khi nào đưa advice"): nhập vào A3/A4 của AUDIT — chi tiết `tracking/BACKLOG-QUESTIONS-2026-07-27.md`.
5. **Bổ sung ~02:00 (làm SAU audit, plan kỹ từng mục — BACKLOG mục R1-R5)**: UI sim GIỐNG UI app
   (một ngôn ngữ thiết kế); hướng người dùng — HIỂU + VISUALIZE quyết định advisor (decision-trace);
   show tối giản tools/bước agent dùng (học cách show của **CrewAI**); sim TUA/DỪNG được, sinh
   động (tốc độ, nhảy-tới-sự-kiện); **DOUBLE-CHECK lại mọi phần đã làm** — "làm thật kĩ" là chuẩn.
