# HANDOFF 2026-08-06 — hai audit đang DỞ vì QUOTA-BLOCKED (nối lại khi Cường mở Fable)

> **Cường 2026-08-06:** *"quota is filled… document down the progresses of the agents on advancing
> the sim and advisors, root cause, etc. I will give direct order to continue with Fable later"*.
> File này là bản đồ hồi phục: cái gì XONG, cái gì DỞ, lệnh nối lại chính xác, và kết quả đã cứu
> được. Theo `CLAUDE.md` §3.5: đã ghi `QUOTA-BLOCKED`, **hạ cap xuống 1** cho tới khi Cường mở lại.

## 0. Nối lại thế nào (lệnh chính xác — dán được)

Hai workflow đều **resume được**: agent đã xong replay từ cache (không tốn token), chỉ agent lỗi
chạy thật.

| Workflow | Lệnh nối lại |
| --- | --- |
| Root-cause idle | `Workflow({scriptPath: "<session>/workflows/scripts/root-cause-idle-not-trips-wf_73fcc763-da8.js", resumeFromRunId: "wf_73fcc763-da8"})` |
| Audit math-model | `Workflow({scriptPath: "<session>/workflows/scripts/math-model-audit-wf_3b54202c-73c.js", resumeFromRunId: "wf_3b54202c-73c"})` |

`<session>` = `C:\Users\Cuong\.claude\projects\c--Users-Cuong-...-GSM-Driver-Agent\2a13ca96-bcc3-4a9e-8498-c8711d248f18`.
⚠ Nếu session mới không còn cache (resume chỉ same-session): **đọc artifact đã có ở
`research/audit/2026-08-06-*/`** rồi chạy lại RIÊNG phần thiếu — danh sách ở §1/§2 dưới.

---

## 1. Root-cause *"thời gian thừa không vào đơn"* — 1/4 agent xong

**Câu hỏi Cường:** kênh chọn-trạm giải phóng −698 phút-đội/ngày ở trạm, nhưng thời gian đó vào
idle (+520′) và nghỉ (+235′ SIG) chứ không vào cuốc (payout ns). *"Đáng ra thời gian thừa phải vào
đơn chứ? Đây là do thiết kế sim kém à?"*

### ✅ XONG: `rc-01-mechanism.json` — bản đồ cơ chế dispatch/demand (evidence file:line đầy đủ)

Bảy phát hiện cơ chế (đọc code tĩnh, **chưa đo** — nên chưa phải phân loại root cause cuối):

1. **Eligible nhận đơn = CHỈ `state == IDLE`** (`world.py:628`). REST/CHARGING/ENROUTE/ON_TRIP đều
   vô hình với dispatcher ⇒ **+235′ nghỉ là thời gian KHÔNG THỂ vớt đơn *theo thiết kế*** — đây là
   model choice có chủ đích, không phải bug.
2. **Bán kính bắt đơn cứng**: shortlist hex `k=6` ≈ **2,22 km** + `ETA ≤ 11′` (`dispatcher.py:107-116`,
   config `142,147`). Rảnh ngoài bán kính = vô hình với đơn, **rảnh bao lâu cũng vô ích**.
3. 🔴 **`BUG-DISPATCH-SHORTLIST` — đã ghi hồ sơ, CHƯA SỬA**: hex 2,22 km **hẹp hơn** bán kính
   ETA-khả-thi ~3,14 km ⇒ loại **âm thầm** tài xế ở dải 2,2–3,1 km, không log. Comment trong chính
   `configs/pilot_dongda.yaml:121-142` tự nhận *"đơn chết dù có người trong tầm với"*. Nợ `T-045c`.
4. 🔴 **Cooldown giết cặp vĩnh viễn**: `offer_cooldown_min = 10′` (default, config không override)
   **≥ `patience_max` 10′** ⇒ một lần từ chối/SOC-skip là cặp (đơn, tài xế) chết hẳn, dù tài xế rảnh
   suốt phần đời còn lại của đơn (`world.py:171-172,641-646` · config `155`).
5. **Đơn KHÔNG phải offer-một-lần**: nằm hàng đợi, thử lại **mỗi tick 5 giây** tới hết patience
   (median 5′, cap 10′) — giả thuyết H3 dạng "offer một lần rồi chết" bị **BÁC**.
6. **Match không còn euclid-greedy**: Hungarian tối thiểu **tổng** ETA (đường thật + hệ số OSRM) từ
   UPDATE-080. Phần euclid còn sót đúng là shortlist ở mục 3. Hệ quả phụ: cá nhân có thể **thua phép
   gán toàn cục** (đơn được giao cho người khác cho tổng rẻ hơn).
7. **Sau đổi pin: IDLE ngay nhưng đứng ở CELL TRẠM** (`world.py:1243,1287`) — và bản năng đi tìm chỗ
   khi rảnh **mù cầu thật**: relocate theo *belief từ config × nhiễu*, ring 1–3 (~0,35–1 km), chỉ
   trong lõi, **và mất eligibility suốt lúc di chuyển** (`behavior.py:199-238`, `world.py:1121-1123`).
   ⇒ khớp thẳng với giả thuyết D-E4-06(b): kênh chọn trạm theo *ít chờ* có thể đặt tài xế xa cầu hơn.
8. **Cầu hoàn toàn ngoại sinh**, không co giãn theo cung/chờ (`demand.py:90-171`; `REVIEW-092-4`
   DEFERRED) ⇒ tổng đơn KHÔNG tăng khi có thêm cung rảnh; **chỉ vớt được đơn CHẾT mới thành trips**.

**Phát biểu lại nghịch lý cho chính xác:** "rảnh thêm" chỉ thành "phục vụ thêm" khi rảnh **đúng chỗ**
(≤2,2 km/11′ quanh điểm đón) × **đúng lúc** (trùng cửa sổ patience 5–10′) × **đúng trạng thái**
(IDLE, không phải nghỉ/di chuyển/sạc) × **thắng phép gán toàn cục** × **chưa từ chối đơn đó**.

**Phân loại cuối: `UNRESOLVED`** — cần số đo (H1 lệch-pha-giờ vs H2 lệch-vị-trí vs H3 defect
dispatcher). ⚠ Lưu ý phản biện đã ghi sẵn: `BUG-DISPATCH-SHORTLIST` tồn tại ở **CẢ HAI arm**, muốn
quy Δ cho nó phải chứng minh arm B đẩy tài xế rảnh vào dải mù **nhiều hơn** arm A.

### ⛔ CHƯA CHẠY (quota): rc-02 · rc-03 · rc-04

- **rc-02 số nền** — rút từ artifact có sẵn (không chạy sim): đơn chết/ngày nền = %tổng đơn; 698
  phút-đội = bao nhiêu phút/tài xế; quy đổi "nếu chuyển đổi hoàn hảo thì +bao nhiêu trips" so với Δ
  đo được. Thước quy đổi có sẵn: positioning +6.016đ SIG ↔ đơn chết −23,4.
- **rc-03 probe chồng lấn** (việc chính) — instrument 5 seed A/B: với mỗi đơn CHẾT, đếm tài xế IDLE
  eligible trong bán kính tại thời điểm hết hạn (arm A vs B); bản đồ (cell × giờ) của Δidle so với
  bản đồ đơn chết; lệch pha giờ hay lệch vị trí. **Đây là phép đo phân xử H1/H2/H3.**
- **rc-04 verdict** — phản biện rc-03 rồi phân loại BUG/MODEL GAP/CALIBRATION GAP/VISIBILITY GAP,
  trả lời thẳng *"thiết kế sim có kém không"*, ghi `rc-00-VERDICT.md`.

---

## 2. Audit MATH-MODELLING kênh + solver — **10/12** artifact xong, chưa tổng hợp

Charter đầy đủ: `research/audit/2026-08-06-math-model-audit/README.md` (5 câu hỏi/item, ranh giới,
lớp lỗi mẫu station_choice). **Chưa ai đọc nội dung 8 file này** — chúng là dữ liệu thô chưa qua
phản biện, **không được trích số vào kết luận** cho tới khi qua bước phản biện (bài học ADV-09:
~1/4 finding review là sai vì không đọc consumer).

| Đã có | Còn thiếu (quota) |
| --- | --- |
| `mm-01` positioning · `mm-02` shift family · `mm-03` accept_lift · `mm-05` battery family (có bản redesign objective D-E4-06(b)) · `mm-06` S1 · `mm-08` S4 · `mm-09` penalty/khoán/knapsack · `mm-10` idle/anomaly/f3 · `mm-11` information-set · `mm-12` extensibility-map | `mm-04` rest_window/meal · `mm-07` S2 DP math · **`mm-13` phản biện** · **`00-SUMMARY.md`** |

⚠ **Đếm lại bằng lệnh trước khi tin bảng này** (`Get-ChildItem research\audit\2026-08-06-math-model-audit -Filter "mm-*.json"`):
con số này đã đổi **hai lần** trong lúc tôi viết file (8 → 9 → 10) vì agent kịp `Write` artifact rồi
mới chết ⇒ báo cáo lỗi của workflow **không** phản ánh đúng cái đã có trên đĩa.

⚠ **Thứ tự nối lại quan trọng**: chạy 4 finder thiếu → **phản biện** → tổng hợp. Bỏ qua phản biện là
lặp lại đúng lỗi ADV-09 đã sập.

---

## 3. Trạng thái các việc khác (không bị quota chặn)

- ✅ **UPDATE-160 đã chốt + push** (`e697e22`): `station_choice` **NO-GO bật mặc định** — chấm máy
  theo ĐA-08 trên n=100: FAIL 1a (tiền −33đ ns) + FAIL 1b (P1 −3.863đ ÂM-SIG). Reopen `D-E4-06`.
- ✅ **La bàn quyết định** `BOOTSTRAP-SESSION.md` §5b (Cường hỏi: quyết định nào thì đọc file nào).
- 🟢 **Server đang sống**: dashboard `:8501` · web demo `:8000/app/` ⇒ **V-31 xem được ngay**.
- ⏭ **Việc lớn kế tiếp theo lịch trình** (chưa động): **`D-SIM-K3` keyed RNG** — đòn bẩy cao nhất
  toàn repo (mọi Δ đang lẫn random-stream divergence; nó cũng là điều kiện reopen (a) của D-E4-06).
- ⏳ Cường: **V-31** · K-01(b) ACK · D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13.
- ⏸ Khánh: 2 test đỏ (demo_trace_neutrality, K-03) · Flutter (policy_thresholds, thẻ cliff, cờ tầm pin).

## 4. Bài học rút ra từ chính sự cố quota này

Tôi mở **hai workflow (16 agent) song song** trong khi `CLAUDE.md` §3.5 quy định **tối đa 2 phiên
đồng thời**, queue `2 → 2 → 1`. Hậu quả: 3 agent chết giữa chừng, mất một phần công. Lần sau: fan-out
lớn phải **chia lô và persist artifact sau mỗi lô** (may là 9/16 artifact đã kịp ghi ra đĩa nên
không mất trắng — thiết kế "mỗi agent tự Write artifact" đã cứu vãn; giữ nguyên thiết kế đó).
