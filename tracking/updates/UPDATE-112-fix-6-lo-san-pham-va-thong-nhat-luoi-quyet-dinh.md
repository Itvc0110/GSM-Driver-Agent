# UPDATE-112 — FIX 6 lỗ đo lường đường SẢN PHẨM + THỐNG NHẤT lưới quyết định (V-21)

Ngày: 2026-07-31 · Trạng thái: `DONE-CODE` · Hướng: **fix lỗi**, theo chỉ đạo Cường
2026-07-31 (*"ưu tiên hoàn thành kế hoạch dang dở, fix lỗi thay vì mở rộng sim"*).

## Bối cảnh — món nợ 3 lần không trả nổi bằng agent

13 finding sev CAO của đường SẢN PHẨM (`tracking/SOI-2026-07-30-mau-so-adherence.md` §4)
**chưa cái nào qua phản biện**: 16/16 agent chết session limit hai lần trước, lần thứ ba
hôm nay 13/14 agent chết sau ~4 phút rồi **hết credit hẳn**.

⇒ Đổi cách: **tự phản biện bằng đọc code + reproduce qua ĐƯỜNG ỐNG THẬT**
(`decision_state`, `adherence_view`, `cadence.evaluate`, `decision_bucket`). Chậm hơn agent
nhưng bằng chứng mạnh hơn — chạy thật, không suy luận.

## Kết quả phản biện: 7 finding kiểm, 6 ĐÚNG, 1 trùng nợ cũ

| Mã | Phán quyết | Sửa |
| --- | --- | --- |
| **L3-03** | ĐÚNG — bấm "Làm theo" 14:00 → đổi ý "Bỏ qua" 15:00 ⇒ ghi `followed`. Đối chứng `occurred_at` khác nhau ⇒ ghi đúng ⇒ nguyên nhân là **thế hoà** | ✅ `_ordered` tie-break thêm `observed_at` (thời điểm SERVER nhận) trước `event_id` |
| **L4-01** | ĐÚNG, **nặng hơn mô tả**: không chỉ `event_adherence=None` — đo được `event_followed=1 > event_decided=0`, **tử số vượt mẫu số**, trạng thái BẤT KHẢ không cổng nào bắt | ✅ `displayed` (sản phẩm) vào **mẫu số EVENT** cùng `decided` (sim) — hai tên của cùng sự kiện "advisor đã nói" |
| **L4-03** | ĐÚNG — `decision_bucket(0)==decision_bucket(25)` mà `min_gap=20` ⇒ phút 21–29 cadence trả PRESENT, card tới tay, nhưng event trùng khoá ⇒ **không ghi, không tiêu ngân sách** | ✅ V-21 (dưới) |
| **L4-07** (PLAN) | ĐÚNG — **nặng nhất**: `cards.js` bịa `advice_id` cho card im lặng, `_render` vẫn vẽ nút ⇒ bấm ⇒ `decision_adherence = 100%` cho quyết định **advisor chưa từng đưa** | ✅ hai tầng: client vẽ nút "Đã hiểu" (không ghi event) + boundary từ chối 422 |
| **L4-04** | ĐÚNG — `GET /advice` trả silent card mà **không ghi event nào** ⇒ mẫu số "advisor ĐỊNH nói nhưng bị nén" mất hẳn ở sản phẩm | ✅ `_note_suppressed` ghi `suppressed` với `decision_id` hậu tố `-sup` (tiền lệ sim; KHÔNG vào mẫu số `decided`) |
| **L4-09** | ĐÚNG — `topic` default `"bonus"`, client chỉ gửi brief/nudge/recap ⇒ **namespace mồ côi** có cooldown/dismiss riêng không ai nuôi | ✅ `CLIENT_TOPICS` + `DEFAULT_TOPIC="brief"`; test canh default phải nằm trong tập thật |
| **L4-07** (SOI) | ĐÚNG — `SHIFT_START_MIN = 6*60` **cứng cho mọi tài xế** trong khi `shift_end_min` đã là query param ⇒ bất đối xứng, pha ca của tài xế ca đêm sai hoàn toàn | ✅ tham số hoá `shift_start_min` |
| **L4-08** | **TRÙNG `D-R21`** (client gửi `at_min` giả) — không phải finding mới; `D-R21` đã phản biện hạ cấp, cố ý chưa sửa | — (fix L3-03 đã giải quyết phần hệ quả) |
| **L4-05** | ĐÚNG về ngữ nghĩa, **sev hạ TB**: `followed` sản phẩm = cú bấm tự khai, sim = đổi hành vi thật. Nhưng khoá projection `(run_id, …)` và UI luôn `run_id=None` ⇒ **đã tách sẵn** | → `D-R22` (rủi ro còn lại là người đọc gộp hai bảng) |

⚠ **Lệch mã phát hiện được**: `PLAN` §5 và `SOI` §4 dùng **cùng mã `L4-07` cho hai finding
khác nhau**. Cả hai đều đúng, cả hai đã sửa; ghi lại để đánh số lại khi có dịp.

## V-21 — thi hành "MỘT SỐ DUY NHẤT" (Cường 2026-07-31)

Cường chốt: *"mọi thứ phải được thống nhất… tất cả dùng chung 1 số, không có mismatch"*.
Hoá ra không phải hai lưới mà **ba** (`D-R17` đã ghi nợ): cooldown 20′ · decision_id 30′ ·
kênh vị trí 60′.

- **Lưới quyết định = cooldown = `DECISION_BUCKET_MIN` (30′) cho MỌI kênh.**
  `CadenceConfig.effective_gap_min = max(min_gap_config, decision_bucket_min)` — **luật dẫn
  xuất**, không hằng số mới. `min_gap = 20′` giữ nguyên là baseline Cường duyệt
  (`D-ĐA04-02`) nhưng nay là **SÀN**, trần do nhịp sinh quyết định áp đặt.
- **`advice.bucket_min = 60′` hết kiêm hai vai**: chỉ còn là *chu kỳ chạy* của planner vị
  trí, không còn là lưới định danh quyết định. Tham số `bucket_min` **bỏ khỏi chữ ký** của
  `_decision_id`, `coin_follows`, `cadence_note_spoken`, `_outcome_key` — không ai truyền
  lưới riêng lại được.
- **Ràng buộc cũ được giữ bằng guard fail-loud** thay vì bằng lưới thứ ba: lý do lưới 60′
  ra đời là *bucket không được rộng hơn nhịp planner, nếu không hai lần gán gộp một
  decision_id* (đo được **23 event mất** khi `bucket_min=15`). Nay `advice_bridge.__init__`
  nổ `ValueError` nếu `bucket_min < DECISION_BUCKET_MIN`.
- **Bất biến mới có test quét toàn dải phút một ca**: hai lần được phép nói KHÔNG BAO GIỜ
  rơi cùng một bucket quyết định. Chứng minh đỏ: sever luật dẫn xuất về 20′ ⇒ đỏ ngay.

## Files

- **TẠO** `ui/backend/tests/test_product_adherence_leaks.py` (9 test)
- **SỬA** `src/gsm_core/lifecycle/projections.py` (L3-03, L4-01) ·
  `src/gsm_core/lifecycle/cadence.py` (`effective_gap_min`, `decision_bucket_min`) ·
  `src/gsm_sim/world.py` + `src/gsm_sim/advice_bridge.py` (một lưới + guard, bỏ tham số) ·
  `ui/backend/app/routers/advice.py` (L4-04/07/09) · `ui/web/js/cards.js` (L4-07 client) ·
  `tests/test_cadence_policy.py` (+2 test bất biến) ·
  `ui/backend/tests/test_lifecycle_actions.py` (2 test **đang pin chính lỗi L4-03** → pin
  hành vi đúng, có ghi chú tại chỗ) · SOI + DEFERRED (`D-R22`) + PENDING-REVIEW.

## Kiểm chứng

- 9 test sản phẩm: **5 đỏ + 1 xanh đối chứng, rồi thêm 3 đỏ** TRƯỚC fix → 9 xanh sau.
- 2 test bất biến cadence: sever luật dẫn xuất ⇒ đỏ; khôi phục ⇒ 25/25 xanh.
- UI suite **65/65** · nhóm cadence/advice sim **55/55** · nhóm lifecycle sim **99/99**.
- Full suite CẢ HAI lệnh (chạy lại sau toàn bộ thay đổi): **889 passed + 5 skipped + 65 UI
  = 959 / 0 fail**.
- **Đo lại E10**: thống nhất lưới đổi coin key của kênh vị trí (60′→30′) ⇒ realization
  ai-nghe-lời đổi. Đo lại arm `oracle` + `real` n=100 để kiểm kết luận **57–65%** còn sống
  trong CI hay không — kết quả ghi ở phần dưới/commit. Nếu lệch ngoài CI thì đó là finding
  phải báo, không phải làm ngơ.

## Nhãn evidence

Reproduce chạy trên đường ống thật, không mock projection. **Mọi con số adherence của đường
SẢN PHẨM trước hôm nay đều có thể nhiễm 6 lỗi trên — không dùng lại.** Số của đường SIM
không nhiễm các lỗi UI, nhưng bị ảnh hưởng bởi thống nhất lưới (xem đo lại E10).

## Visual review

`NOT_APPLICABLE` cho backend/projections. ⚠ `cards.js` ĐỔI UI: card im lặng nay hiện nút
**"Đã hiểu"** thay vì "Làm theo"/"Bỏ qua" ⇒ **bổ sung vào V-18** khi Cường xem sản phẩm.

## Adversarial self-review / flaws found

- Tôi tự phản biện chính finding của mình ⇒ rủi ro thiên vị. Đối trọng: mỗi kết luận có
  **reproduce chạy được** + **đối chứng ngược** (L3-03 test thứ hai chứng minh fix không
  làm hỏng đường `occurred_at` khác nhau).
- Hai test cũ bị sửa kỳ vọng (620→630, PRESENT→SUPPRESS) — **không phải nới test cho xanh**:
  chúng đang pin chính hành vi lỗi `L4-03`, và ghi chú lý do nằm ngay tại chỗ sửa.
- `is_fabricated_advice_id` dùng allowlist prefix ⇒ solver mới thêm namespace mà quên cập
  nhật ⇒ action hợp lệ bị 422. Đánh đổi có chủ ý (fail-loud > âm thầm nhiễm số).
- `observed_at` do server đặt ⇒ nếu sau này có đường offline sync hàng loạt, thứ tự là thứ
  tự tới server chứ không phải thứ tự bấm. Chưa có đường đó; ghi nhận.
- Cooldown hiệu dụng tăng 20→30′ ⇒ **advisor nói thưa hơn ở sản phẩm**. Đây là hệ quả thật
  của việc thống nhất, không phải tác dụng phụ ngoài ý: nói lại trong cùng một quyết định
  là lặp lại chính mình.

## Follow-up

- 6 finding chưa phản biện: `L3-04`, `L4-02`, `L4-06`, `L5-03/04` (+ `L1-02`, `L3-02`,
  `L5-01/02` ở danh sách sev CAO) — làm tiếp bằng tay.
- `D-R22` (followed hai nghĩa) · `D-R21`/`L4-08` (bỏ `KIND_HOURS` — cycle UI riêng).
- ⏳ **PENDING-REVIEW 20 mục chờ Cường**: V-01..V-14, V-16, V-17, **V-18** (nay kèm card im
  lặng mới), V-20, V-21 (đã có hướng chốt, đóng khi đo lại E10 xong). V-19 ✅ verdict OK.
