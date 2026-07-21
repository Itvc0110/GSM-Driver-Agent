# SPEC — Khung thời gian gợi ý, vòng đời biến & memory (v1.1)

Cập nhật: 2026-07-21 · Trạng thái: **APPROVED** (Cường 2026-07-21: "approve mọi quyết định thiết kế") — hybrid trigger + cooldown defaults + phân lớp A/B/C có hiệu lực; hiệu chỉnh số liệu chi tiết qua UPDATE khi build.
Trả lời yêu cầu #3 (robust optimization: biến bền vững vs biến để reasoning) và #4 (chia khung thời gian, feed/inject biến, persistent vs session memory) của Cường 2026-07-21. Timestep phân tầng cho simulator: xem `specs/simulation-pilot-world.md` §timestep (research đợt 4).

## 1. Khi nào hệ thống đưa ra/cập nhật gợi ý (trả lời #4 — chọn HYBRID: cả hai)

Kết hợp **event-driven** (rời rạc theo sự kiện) + **fixed anchors** (mốc thời gian cố định) + debounce. Lý do: chỉ event-driven thì bỏ lỡ các mốc chuyển pha quan trọng của ngày (đầu/cuối khung điểm thưởng); chỉ fixed-time thì phản ứng chậm với thay đổi đột ngột (SOC tụt, mưa).

### 1.1 Ba loại trigger

| Loại | Trigger cụ thể | Advice có thể phát |
| --- | --- | --- |
| **Event-driven** (theo cuốc/state) | hoàn thành cuốc; từ chối/bỏ lỡ đơn; SOC qua ngưỡng (40%/25%/15%); vào/ra trạng thái nghỉ-sạc; tỷ lệ nhận đổi qua mốc cảnh báo; voucher/policy mới áp cho hồ sơ | tiếp tục/nghỉ/sạc; cảnh báo ngưỡng hồ sơ; cập nhật thưởng |
| **Fixed anchors** (mốc trong ngày) | mở app đầu ca (F1); trước đầu khung cao điểm ~30ph (nhắc online sớm — điểm tính theo giờ khách ĐẶT); giữa trưa (cửa sổ sạc/nghỉ); trước cuối khung điểm vàng ~20ph; cuối ca (F3) | kế hoạch ca; nhắc vào khung; gợi ý cửa sổ sạc; tổng kết |
| **Threshold-crossing** (dẫn xuất) | khoảng cách tới mốc thưởng tuần co lại đủ nhỏ ("còn N cuốc = đạt mốc"); demand proxy lệch mạnh so với baseline giờ đó (mưa/sự kiện); queue trạm vượt ngưỡng | "chốt mốc"; cơ hội bất thường; đổi giờ sạc |

### 1.2 Debounce & friction budget

- Mỗi advice có `valid_from/expires_at`; advice mới cùng chủ đề **supersede** advice cũ.
- **Cooldown theo chủ đề** (mặc định: ≥20 phút giữa 2 advice cùng loại) + **budget/ca** (mặc định ≤6 advice chủ động/ca, không tính trả lời khi tài xế hỏi) — tài xế bận, spam là phản tác dụng (adherence giảm — xem `research/simulation/evaluation-methodology.md`).
- Ưu tiên khi trùng: an toàn/SOC > ngưỡng hồ sơ (nguy cơ phạt) > mốc thưởng > tối ưu demand.
- Đang on-trip: chỉ queue lại, phát khi về idle (mô phỏng "không đọc màn hình khi chạy").

### 1.3 Cửa sổ tối ưu hóa (rolling)

Mỗi lần trigger, bài toán gợi ý nhìn **phần còn lại của ca** (horizon = end-of-shift dự kiến), chia bucket 30 phút; nhưng chỉ trình bày **hành động kế tiếp** + lý do. Re-plan toàn cửa sổ khi: trigger sự kiện lớn (SOC, mưa, policy đổi) hoặc mỗi 60 phút (whichever first). Đây là rolling-horizon nhẹ — không phải MPC đầy đủ của pack cũ (vẫn deferred D-001).

## 2. Phân lớp biến: bền vững → tối ưu hóa; bất định → reasoning (trả lời #3)

Nguyên tắc top-down đã chốt trong SCOPE: **không chốt cứng toàn bộ biến**. Chia 3 lớp theo *độ bền của semantics và khả năng thu thập*:

### Lớp A — Biến bền vững (đưa vào bài toán tối ưu đa biến có ràng buộc)

Semantics ổn định, luôn đo được trong mọi phiên, ít khả năng bị loại bỏ:

| Biến | Nguồn | Vai trò trong optimization |
| --- | --- | --- |
| Thời gian còn lại của ca, quỹ giờ | session | ràng buộc cứng |
| SOC pin / km còn lại | telemetry (sim) | ràng buộc cứng + chi phí cơ hội sạc |
| Vị trí cell H3 hiện tại | session | trạng thái |
| Doanh thu/payout lũy kế hôm nay, khoảng cách tới target | ledger | mục tiêu |
| Điểm thưởng lũy kế + bảng mốc (versioned) | policy bundle | mục tiêu phụ (step function) |
| Tỷ lệ nhận/hoàn thành hiện tại vs ngưỡng policy (versioned) | hồ sơ | ràng buộc mềm→cứng khi sát ngưỡng |
| Demand proxy theo cell×giờ (mock, có uncertainty) | world state | hệ số kỳ vọng |
| Queue/capacity trạm đổi pin (khi có) | world state | ràng buộc tài nguyên + anti-herding |
| Giá cuốc trung bình theo giờ | mock/policy | hệ số |

→ Bài toán lớp A: chọn chuỗi hành động {online, nghỉ, sạc, kết ca} trên các bucket 30ph còn lại của ca, maximize kỳ vọng payout + giá trị mốc thưởng đạt được − chi phí (mệt mỏi/quá giờ), ràng buộc SOC/quỹ giờ/ngưỡng hồ sơ/capacity. Giải bằng rule/DP/greedy đơn giản, kiểm chứng được, deterministic theo input — **không** LLM.

### Lớp B — Biến bán bền vững (feature flag: bật vào optimization khi đủ dữ liệu, rơi về reasoning khi thiếu)

Thu thập được không đều đặn hoặc chất lượng dao động:

- Thời tiết dự báo (có API thì thành hệ số demand; không có thì reasoning "trời có vẻ mưa → …").
- Sự kiện địa phương (concert, lễ) — khi có feed sự kiện thì boost demand proxy; không thì reasoning từ tin tức.
- Phân phối tài xế xung quanh (supply field) — trong sim luôn có; ngoài đời chưa chắc thu thập được.
- Trạng thái chi tiết pin trong tủ trạm (app VinFast có nhưng chưa chắc lấy được qua API).

Mỗi biến lớp B có cờ `available_this_session`; pipeline optimization đọc cờ để quyết định đưa vào constraint/hệ số hay bỏ qua. **Đây là cơ chế "robust với biến bị thêm/bớt"**: bài toán lớp A không đổi cấu trúc khi lớp B thiếu — chỉ mất độ chính xác, và caveat được ghi vào output.

### Lớp C — Biến bất định cao (chỉ dành cho agent reasoning, có guardrail)

Chưa mô hình hóa được hoặc mô hình hóa quá phức tạp so với giá trị:

- Sở thích/tâm trạng/thói quen cá nhân tài xế diễn đạt bằng lời ("hôm nay muốn về sớm", "ngại chạy khu X").
- Trade-off nhiều chiều khó cân đo (mệt vs gần mốc thưởng vs mưa sắp đến).
- Diễn giải chính sách mới chưa được cấu trúc hóa vào policy bundle.
- Tổng hợp bài học sau ca (F3) từ nhiều pattern.

Guardrail giữ nguyên (CLAUDE.md §5): reasoning phải log + confidence + tắt được về rule/template; **không tạo số tài chính/policy** — số luôn từ lớp A/B.

### Quy trình di chuyển biến giữa các lớp

Biến mới đề xuất → vào lớp C (reasoning thử nghiệm, log lại) → nếu chứng minh giá trị + thu thập ổn định → thăng cấp lớp B (feature flag) → khi semantics + nguồn ổn định lâu dài → lớp A (vào optimization). Ngược lại biến lớp A mất nguồn thu thập → giáng cấp B (flag off) mà không phá cấu trúc bài toán. Mọi thăng/giáng cấp ghi vào tracking/updates.

**Đối chiếu luồng hiện tại (kết quả kiểm tra theo yêu cầu #3):** flow v2 + SCOPE đã tuân thủ *nguyên tắc* (rule/analytics tính số, agent reasoning có điều kiện + guardrail — CLAUDE.md §1/§5, drawio L1/F0), NHƯNG trước spec này chưa có: (a) phân lớp biến tường minh A/B/C; (b) cơ chế feature-flag thăng/giáng cấp; (c) định nghĩa trigger/cooldown; (d) tách persistent vs session memory. 4 phần đó là đóng góp mới của spec này + `simulation-twin-world.md`; SCOPE §1 đã được cập nhật trỏ tới đây.

## 3. Persistent memory vs session state (trả lời #4 phần sau)

### 3.1 Persistent (giữ qua các phiên — hồ sơ hành vi tài xế)

| Nhóm | Biến | Dùng cho |
| --- | --- | --- |
| Hồ sơ | track hợp tác, thâm niên, loại xe, khu nhà (cell làm mờ) | policy mapping, cá nhân hóa |
| Hành vi dài hạn | phân bố giờ online theo thứ; số cuốc/doanh thu theo ngày (rolling 4–8 tuần); pattern sạc (giờ quen, trạm quen); tỷ lệ nhận/hoàn thành lịch sử | baseline cá nhân F1/F3; phát hiện lệch pattern |
| Tương tác advice | lịch sử advice: phát/xem/theo (taxonomy adherence); chủ đề hay bị ignore; trust score | điều chỉnh tần suất + loại advice; không punitive |
| Mục tiêu | target payout các kỳ trước, kết quả đạt/không | đề xuất default target |
| Chú thích reasoning | các insight lớp C đã được xác nhận đúng/sai | học dần cho cá nhân hóa |

Nguyên tắc: chỉ lưu mức tổng hợp/cell làm mờ (không tọa độ thô), có version + ngày; tài xế xem/sửa/xóa được (kế thừa nguyên tắc privacy pack cũ vẫn hợp lý).

### 3.2 Session (reset mỗi ca — feed vào optimization)

SOC hiện tại, cell hiện tại, trạng thái hoạt động, doanh thu/điểm/cuốc lũy kế hôm nay, quỹ giờ còn lại, target hôm nay, advice đang hiệu lực + cooldown counters, demand/supply/queue snapshot mới nhất, cờ `available_this_session` của biến lớp B, danh sách sự kiện đã xử lý (dedupe).

### 3.3 Luồng feed/inject

```text
[Persistent store] ──(load đầu ca, làm giàu prior)──▶ [Session state]
[World feeds: demand proxy, weather?, queue?] ──(inject theo trigger §1)──▶ [Session state]
[Session state] ──▶ Optimization lớp A (+B nếu flag on) ──▶ options + số liệu
[Session state + persistent] ──▶ Agent reasoning lớp C (diễn giải, cá nhân hóa, trade-off) ──▶ advice text
                                    │ log + confidence + fallback template
[Kết quả ca (F3)] ──(aggregate, cuối ca)──▶ [Persistent store]  # không ghi realtime từng event
```

- Inject biến cập nhật = **immutable snapshot** có timestamp; optimization luôn chạy trên snapshot nhất quán (không đọc state đang mutate).
- Sau mỗi ca: job tổng hợp session → cập nhật persistent (rolling stats), rồi xóa session chi tiết theo retention.

## 4. Ánh xạ vào simulator

Twin-world sim (specs/simulation-twin-world.md) dùng đúng cấu trúc này: actor có persistent memory (kinh nghiệm demand cá nhân, trust) qua các ngày sim; session state mỗi ngày; advisor arm A chạy đúng trigger §1 + phân lớp §2. Nhờ vậy kết quả sim kiểm chứng trực tiếp thiết kế production sau này.

## 5. Việc mở tiếp

- Cường/Khánh review 2 quyết định thiết kế: (a) hybrid trigger + cooldown defaults; (b) ranh giới lớp A/B/C như trên.
- T-011 (contract v2) phải bao gồm: advice envelope (spec + validity + confidence + trigger), session snapshot schema, persistent profile schema (đã có nháp trường trong PERSONAS).
- Khi build sim: calibrate cooldown/budget bằng chính sim (sweep tần suất advice → adherence/hiệu quả).
