# LỊCH TRÌNH CẢI THIỆN — sim + advisor (Cường yêu cầu 2026-08-06)

> Nguồn: triage toàn bộ nợ mở (DEFERRED/TODO sau UPDATE-158) + bằng chứng chương trình E1–E5.
> Nguyên tắc xếp: (giá trị cho ĐỘ TIN của sim | giá trị cho ADVISOR) / chi phí; nợ chạm ranh giới
> sức khoẻ hoặc chạm độ tin của MỌI phép đo xếp trước tính năng mới.

## Bài học đã docs (mục "thứ học được" — tích luỹ, đọc trước khi làm việc mới)

1. **Kênh chi-phí trơ trong world zero-cost** (ADV-01/E-05); giá trị advisor hiện tập trung họ
   VỊ TRÍ/THỜI GIAN (positioning +4,5k; station_choice wait −66%). → UPDATE-153/155/156.
2. **n nhỏ lừa lặp lại** (3 lần một phiên) → CI n<30 không được vào câu kết luận; và **quan sát
   có thể phụ-thuộc-cửa-sổ-seed** (rest +281 @seeds-1000s vs +19,6 ns @seeds-7000s) — trước khi
   root-cause một "hiệu ứng", đo lại trên cửa sổ seed KHÁC. → UPDATE-140/159.
3. **Đọc nhánh `if` trước, khai thác số tổng hợp sau** — cơ chế nằm trong code, số chỉ là bóng.
4. **Finding review chưa qua phản biện thì phải reproduce với consumer trước khi sửa** (ADV-09).
5. **Metric có ngưỡng kế toán (break 20′) có thể tạo "hiệu ứng" giả khi can thiệp đổi phân phối
   thời lượng segment** — luôn chạy sensitivity ngưỡng trước khi tin. → probe span 2026-08-06.
6. **UI là bản cuối cho stakeholder** — mã hiệu nội bộ ở comment/docs; nhãn từ MỘT nguồn
   (`channel_labels.py`), ID nội bộ không đổi (contract).
7. **Push UPDATE ngay khi được phép commit** — gom local là mời đụng số với remote (2 lần).

## SÓNG 1 — đang chạy / tuần này (độ tin phép đo + quyết định bật kênh)

| # | Việc | Loại | Vì sao trước | Trạng thái |
| --- | --- | --- | --- | --- |
| 1.1 | **Chốt D-E4-03**: span break-sensitivity (đang chạy) → verdict artifact/cơ chế; nếu sạch ⇒ **bật mặc định `station_choice`** (Cường uỷ quyền) + 100 seed xác nhận | advisor | Kênh đầu tiên có sản xuất THẬT (trips +5,5 ✅) đang chờ đúng một kiểm | 🔄 |
| 1.2 | **D-SIM-K3 keyed RNG** (`rng(seed, actor, purpose)` hoặc event tape) | sim 🔴 | Đòn bẩy cao nhất toàn repo: MỌI Δ đang lẫn random-stream divergence — gỡ được thì mọi phép đo A/B sạch hơn hẳn, và loại quan sát "phụ thuộc cửa sổ seed" khỏi bàn | tuần này |
| 1.3 | **Oracle trên config-all sau E1b** (chuẩn 100 seed) — trần nội dung của TOÀN advisor sau khi công thức đã sửa | advisor | Số định hướng đầu tư (khâu nghe vs nội dung) đã có cho kênh ship; cần bản full | sau 1.1 |
| 1.4 | V-31 + K-01(b) ACK + D-QD4-05 — **chờ verdict Cường** | — | Chặn các nhánh liên quan | ⏳ |

## SÓNG 2 — độ tin sim (mô hình sát thực hơn, theo bằng chứng đã đo)

| # | Việc | Vì sao |
| --- | --- | --- |
| 2.1 | **T-045c dispatcher haversine** → xếp hạng theo ETA đường thật (matrix OSRM có sẵn) | 8,3% đơn bị bỏ OAN đã đo — méo mọi số served/expired |
| 2.2 | **D-M3-19 sổ thời gian `online_min`** (tách bucket không chồng lấn) | Sổ lệch ~3% làm mờ mọi phân rã "thời gian đi đâu"; cũng là tiền đề D-QD4-05 |
| 2.3 | **D-A3-01b NO-OP adherence** (lời khuyên không đổi hành vi vẫn đếm followed) | Mọi số adherence tuyệt đối đang thổi; oracle-arm càng phổ biến càng cần số nghe sạch |
| 2.4 | Sweep chi phí ≠ 0 (`D-E4-01`) — đánh thức họ kênh chi-phí khi Cường muốn nhánh 2029 | Mở khoá S2-schedule/end-shift; kèm prereg nếu claim |

## SÓNG 3 — advisor mở rộng (theo meta-finding: họ vị trí trước)

| # | Việc | Vì sao |
| --- | --- | --- |
| 3.1 | **E-07 zone-rotation theo giờ** (`D-E4-04`) — planner feed S4 slots theo bucket | Họ vị trí = nơi có tín hiệu thật; hạ tầng slots sẵn |
| 3.2 | **B6-PARITY**: đường sản phẩm ship 1/9 solver → nối dần S8 (recap) + S2-lite | UI đang là sản phẩm KHÁC sản phẩm đo; S8 là mảnh E3.2 còn nợ |
| 3.3 | E3.4 "còn gỡ kịp" sang UI + đọc UI-idea cards của Khánh (UPDATE-149 của Khánh) để gộp lộ trình card | Trần 3,5k/ngày ở khâu THUYẾT PHỤC — UX card là đòn bẩy chính |
| 3.4 | `D-E4-05` meal-timing — CHỈ nếu Cường muốn (cùng cơ chế kênh đã đo ns) | Kỳ vọng thấp, để cuối |

## SÓNG 4 — vệ sinh & vận hành

| # | Việc |
| --- | --- |
| 4.1 | `D-E5-01` dedupe test còn lại theo r13 (~2-4′/suite) + đo thời gian chuẩn khi máy rảnh |
| 4.2 | K-03 + demo_trace_neutrality (2 F cuối — **của Khánh**, HANDOFF đã ghi) |
| 4.3 | D-M3-18 phần backend (field đội pin) khi bảng dữ liệu có nguồn |
| 4.4 | D-VIS-01 multiday replay — BẮT BUỘC trước khi cân nhắc bật lại `rest_window` |

## KHÔNG LÀM (và vì sao — để không ai đào lại)

- Bật lại `shift_plan`/`rest_window` không qua prereg mới — luật cũ còn hiệu lực.
- "Sửa" count_supply hai-sổ, veto-khi-kênh-tắt, hay nới POLICY_LOCKED/`SPAN_P90_RISE_TOL` —
  đều là THIẾT KẾ có test ghim (ADV-09/ADV-06 đã soi).
- Đổi TÊN topic/ID nội bộ cho "dễ hiểu" — nhãn hiển thị đã có nguồn riêng; đổi ID là phá contract.
