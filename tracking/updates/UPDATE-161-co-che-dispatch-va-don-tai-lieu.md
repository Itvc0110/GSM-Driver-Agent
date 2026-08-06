# UPDATE-161 — Cơ chế "thời gian rảnh KHÔNG tự thành cuốc" (rc-01) + dọn tài liệu điểm-vào + QUOTA-BLOCKED

- **Ngày:** 2026-08-06
- **Loại:** research (cơ chế, đọc code tĩnh — CHƯA đo) + docs (dọn tài liệu điểm-vào) + vận hành (quota)
- **Liên quan:** UPDATE-160 (NO-GO station_choice) · `D-E4-06` · câu hỏi Cường 2026-08-06:
  *"đáng ra thời gian thừa phải vào đơn chứ? đây là do thiết kế sim kém à? tìm root cause?"* +
  *"dọn document đi, phải thật cẩn thận"* + *"quota is filled… document down the progresses"*

## 1. Cơ chế: vì sao "rảnh thêm" không tự thành "cuốc thêm" (rc-01, evidence file:line)

Artifact: `research/audit/2026-08-06-root-cause-idle/rc-01-mechanism.json`.
**Trạng thái phân loại root cause: `UNRESOLVED`** — đây là bản đồ CƠ CHẾ, phép đo phân xử (rc-02/03/04)
bị quota chặn. Không được dùng file này để tuyên bố nguyên nhân cuối.

Điều kiện để một phút rảnh thêm cứu được một đơn-lẽ-ra-chết — phải đúng **đồng thời**:

| Điều kiện | Ràng buộc thật trong code |
| --- | --- |
| đúng **trạng thái** | eligible = **chỉ `state == IDLE`** (`world.py:628`); REST/CHARGING/ENROUTE/ON_TRIP vô hình với dispatcher ⇒ **+235′ nghỉ là không-thể-vớt-đơn THEO THIẾT KẾ** |
| đúng **chỗ** | shortlist hex `k=6` ≈ **2,22 km** + `ETA ≤ 11′` (`dispatcher.py:107-116`, config 142/147) |
| đúng **lúc** | patience đơn: lognormal median 5′, cap 10′ (`demand.py:118-121`, config 153-155) |
| **thắng** phép gán | Hungarian tối thiểu **tổng** ETA toàn batch — cá nhân có thể thua tối ưu toàn cục (`dispatcher.py:118-134`) |
| chưa **đốt lượt** | cooldown cặp 10′ sau decline/SOC-skip (`world.py:641-646`) |

Ba điểm đáng chú ý nhất:

1. 🔴 **`BUG-DISPATCH-SHORTLIST` — đã ghi hồ sơ, CHƯA SỬA**: shortlist hình học 2,22 km **hẹp hơn**
   bán kính ETA-khả-thi ~3,14 km ⇒ loại **âm thầm, không log** tài xế ở dải 2,2–3,1 km. Chính comment
   trong `configs/pilot_dongda.yaml:121-142` tự nhận *"đơn chết dù có người trong tầm với"*. Nợ `T-045c`.
2. 🆕 **Cooldown ≥ đời đơn** (mới, → `D-SIM-K6`): `offer_cooldown_min=10′` (default trong code, config
   không khai) **≥** `patience_max=10′` ⇒ một lần từ chối/SOC-skip giết cặp (đơn, tài xế) vĩnh viễn.
3. **Cầu ngoại sinh, không co giãn** (`demand.py:90-171`; `REVIEW-092-4` DEFERRED) ⇒ thêm cung rảnh
   KHÔNG tạo thêm đơn; chỉ **vớt đơn CHẾT** mới thành trips. Cộng với việc sau đổi pin tài xế đứng ở
   **cell trạm** và bản năng relocate **mù cầu thật** (belief từ config × nhiễu, ring ≤3 ~1 km, chỉ lõi,
   **mất eligibility suốt lúc di chuyển** — `behavior.py:199-238`, `world.py:1121-1123`) ⇒ khớp thẳng
   giả thuyết `D-E4-06(b)`: kênh chọn trạm theo *ít chờ* có thể đặt tài xế **xa cầu hơn** baseline.

**Trả lời sơ bộ cho câu "thiết kế sim kém à?"** — phải tách ba loại, và mới chỉ tách được về mặt cơ chế:
(a) **model choice có chủ đích**: IDLE-only eligibility, cầu ngoại sinh — không phải lỗi, nhưng **giới
hạn trần** của mọi kênh tiết-kiệm-thời-gian; (b) **defect thật đã ghi hồ sơ**: BUG-DISPATCH-SHORTLIST,
cooldown ≥ patience — tồn tại ở **CẢ HAI arm**, muốn quy Δ cho chúng phải chứng minh arm B đẩy tài xế
rảnh vào dải mù **nhiều hơn** arm A; (c) **objective kênh thiếu vế vị trí** (`D-E4-06(b)`). Chưa đo
thì chưa được chọn một trong ba. `UNRESOLVED`.

## 2. Dọn tài liệu điểm-vào (làm TAY, không giao agent)

Chỉ sửa **sự thật đã stale** + thêm con trỏ; **không xoá, không viết lại** nội dung ràng buộc nào.

| File | Sửa gì |
| --- | --- |
| `CLAUDE.md` | ngày 07-30→08-06 · test `809/865` → **1155 + 201 = 1356** (đo sau PR #6) · UPDATE `100 file/106` → **155 file/số cao nhất 160** · trỏ `PLAN-2026-08-06` + `HANDOFF-*` + §5b · "bảy bẫy" → **12 bẫy** |
| `tracking/PROJECT-GRAPH.md` | header reconciled 07-27→**08-06** + coverage thật + đoạn "chương trình hiện hành" (§3.7b, dãy 144–150 của Khánh vs 151–160 của tôi) |
| `tracking/BOOTSTRAP-SESSION.md` | §2 ngày + HEAD `e697e22` + **đếm bằng lệnh** (155/160) · PENDING **31 hàng V-, 3 đóng-gạch + V-19 inline ⇒ ~27 còn cần Cường** · thêm V-31 vào danh sách · sửa "BỎ 115 test" → **201 (và cảnh báo con số này tăng theo thời gian)** |
| `tracking/TODO.md` | header trỏ đúng: điểm vào BOOTSTRAP · lịch trình 08-06 · HANDOFF quota |
| `tracking/DEFERRED.md` | thêm **`D-SIM-K6`** (cooldown ≥ patience) — kèm điều kiện "đo trước, sửa sau" |
| memory `gsm-reread-docs-after-compaction` | route sau compaction trỏ PLAN mới + §5b + HANDOFF |

⚠ **Không đụng** phần nội dung của 31 hàng V-, các phán quyết, hay §5 bẫy — chỉ thêm/sửa số liệu và
con trỏ. Số nào cũng **đếm bằng lệnh** trước khi ghi (bài học "đếm bằng ký ức sai 3 lần").
Riêng **V-15 KHÔNG được gộp vào "đã đóng"**: nó đóng phần phán quyết nhưng **còn chờ Cường chốt 5
mục giá trị §6** — bản BOOTSTRAP cũ ghi "V-15/V-19 đã ĐÓNG" là **quá tay**, đã sửa.

## 3. QUOTA-BLOCKED — hai audit đang dở

`tracking/HANDOFF-2026-08-06-quota-blocked-audit.md` (bản đồ hồi phục + lệnh resume chính xác).
Tóm tắt: root-cause **1/4** agent xong (rc-01 ✅; rc-02/03/04 ⛔), math-model **10/12** artifact
(thiếu mm-04 rest/meal, mm-07 S2-DP + **phản biện** + `00-SUMMARY.md`). `CLAUDE.md` §3.5: `QUOTA-BLOCKED`,
**hạ cap xuống 1**. Cường sẽ ra lệnh nối lại bằng Fable sau.

## Kiểm chứng

- rc-01 là **đọc code tĩnh**, mọi khẳng định có file:line; **không chạy sim, không đo** — đã ghi rõ
  trong chính artifact và ở đây.
- Docs: mọi con số sửa đều lấy từ lệnh chạy trong phiên (`Measure-Object` cho UPDATE; liệt kê hàng V-
  bằng regex; suite 1155+201 lấy từ lần đo sau merge PR #6 ghi trong BOOTSTRAP §2).
- **Chưa kiểm chứng:** tác động định lượng của BUG-DISPATCH-SHORTLIST và D-SIM-K6 (cần rc-03);
  8 artifact math-model **chưa qua phản biện** ⇒ chưa được trích số.

## Visual

`NOT_APPLICABLE` — docs + research, không đổi code/UI/hành vi sim. Server V-31 vẫn sống (:8501, :8000).

## Adversarial self-review / flaws found

1. **Cám dỗ lớn nhất của cycle này: tuyên bố "root cause = vị trí" vì cơ chế nghe rất khớp.** Không
   làm. rc-01 mới loại được H3-dạng-"offer một lần" và làm yếu H4; H1 (lệch pha giờ) vs H2 (lệch vị
   trí) **chưa phân xử được bằng đọc code**. Ghi `UNRESOLVED` đúng protocol.
2. Hai defect (shortlist, cooldown) có ở **cả hai arm** ⇒ chúng giải thích "vì sao world có đơn chết",
   **không** tự động giải thích "vì sao Δ của kênh bằng 0". Đã ghi rõ để không ai suy sai sau này.
3. Việc mở **16 agent** trên 2 workflow trái §3.5 (cap 2) là nguyên nhân trực tiếp làm mất công
   nhiều agent. Điểm cứu: mỗi agent tự `Write` artifact ⇒ **11/16** kết quả nằm trên đĩa, không mất
   trắng. Giữ thiết kế đó; lần sau chia lô.
5. **Số artifact tôi báo đã SAI HAI LẦN trong cùng một cycle** (8 → 9 → 10): agent kịp `Write` rồi mới
   chết, nên **báo cáo lỗi của workflow không phản ánh cái đang có trên đĩa**. Đã ghi cảnh báo "đếm
   lại bằng lệnh" vào HANDOFF. Cùng họ bài học "đừng ghi số bằng ký ức" — biến thể: *đừng ghi số bằng
   ảnh chụp cũ, và đừng tin bản tổng kết của công cụ hơn hiện trạng đĩa*.
4. Dọn docs có rủi ro **quá tay** (đã từng cắt cụt BOOTSTRAP rồi push). Lần này: sửa bằng Edit từng
   đoạn có old_string duy nhất, không dùng script splice, không xoá dòng nào; V-15 là ví dụ cho thấy
   "gộp cho gọn" là sai.

## ⏳ Nhắc PENDING-REVIEW

**V-31** (dashboard `:8501` · web `:8000/app/` — **server đang sống, xem được ngay**) · K-01(b) ACK ·
D-QD4-05 · ~27 mục V- · Q-03/04/07/09/10/13. ⏸ Khánh: 2 test đỏ + 3 việc Flutter.
