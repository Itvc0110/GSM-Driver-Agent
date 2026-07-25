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
| **Google Maps** | ❌ **KEY KHÔNG HỢP LỆ** (`REQUEST_DENIED`, 64 hex ≠ `AIza…`) | → `D-EXT-02`, cần key đúng |

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

## 6. MOCK UI để xem advice

- Xây **mock UI** để **xem advice** (của phía ta; khác với UI clone của Khánh).
- Có Stadia Maps tiles + OSRM → có thể vẽ bản đồ/hành trình.

## 7. CÁCH LÀM VIỆC

- **Tập trung vào cái còn THIẾU, xây từng cái một**, nếu không cần gì thêm từ Cường.
- Cường approve các phần quan trọng; còn lại agent tự quyết.

## 8. Trạng thái các TRACK (cập nhật khi tiến triển)

| Track | Nội dung | Trạng thái |
|---|---|---|
| **A. SIM overhaul** | mảng riêng, docs+plan riêng (§5) | 🟡 **ĐANG LÀM** — spec master: `specs/simulation/00-sim-overhaul-master.md` (chẩn đoán đo thật: served 61.9% quá thấp; accept 96.3%/complete 99.6% quá sạch). Lộ trình SIM-1..SIM-5 |
| **B. External data** | research + provider offline-first + cache local (§2) | ⏳ key đã có, chưa code |
| **C. Mock UI xem advice** | §6 | ⏳ chưa bắt đầu |
| **D. C7 + rà soát mô hình** | §4 | ⏳ chưa bắt đầu |
| **E. Mock enrichment "thật nhất"** | §3 | ⏳ chưa bắt đầu |

## 9. Những gì ĐÃ XONG trước các chỉ thị này (nền tảng)

- 13 schema `l1r` khớp CHÍNH XÁC metadata GSM (gate test chống trôi).
- Generator mock 90 ngày / 110 profile (bike/rto/car/employee/premium), 4 vòng verify.
- **9 solver** phủ UC1–UC8; advisor pipeline C6 (router→composer→verifier) template-mode.
- Suite **378 test** xanh. Research đợt 1–4 (policy refresh + app features).
