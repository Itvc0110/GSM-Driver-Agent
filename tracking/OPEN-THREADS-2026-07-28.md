# ⚡ RESUME SAU COMPACTION — đọc khối này TRƯỚC, cập nhật 2026-07-29 01:37

> **Prompt tự-mồi cho agent sau compaction** (Cường yêu cầu chuẩn bị): đọc `CLAUDE.md` →
> `tracking/PROJECT-GRAPH.md` → khối này → `PENDING-REVIEW.md` → `git log --oneline -12` +
> `git status`. Compaction KHÔNG miễn trừ §3 (memory `gsm-reread-docs-after-compaction`).

## Trạng thái tại thời điểm ghi

- **Git**: `main` == `origin/main` == `e5d235e`, tree SẠCH. 12 commit hôm nay đã push
  (chuỗi: time-fixes → MarketState → drop-bám-cầu → S4 → BUG-EVAL-ARGMAX → Cycle R/P/E →
  bật positioning mặc định → equilibrium ĐA-09 → **Cycle V gỡ B-02**).
- **Suite xác nhận cuối ĐÃ XANH**: **653 passed / 5 skipped** (14:24, exit 0, 01:42 ngày 29)
  — khớp dự đoán 647+6 guard. KHÔNG còn gì chạy nền. Số đã điền vào UPDATE-090 §Kiểm chứng.
- **UPDATE mới nhất**: 083→090. Số UPDATE kế tiếp: **091** (kiểm remote trước khi đặt).
- **Quota**: session limit đã chạm lúc ~01:20 (4 verify-agent chết) — hạn chế mở agent ồ ạt,
  ưu tiên làm tay + 1 suite/lượt.

## Việc kế tiếp theo thứ tự (đã có verdict, KHÔNG cần hỏi lại)

1. ~~Đọc kết quả suite `bofqb0q04`~~ ✅ XONG (653/5, số đã ghi UPDATE-090, đã push).
2. ~~**Cycle kế — ĐA-05 event store append-only**~~ **DONE-CODE 2026-07-29 (Cycle W,
   UPDATE-091) — chờ verdict Cường, KHÔNG tự đọc thành "đã reviewed".** Đường đến đích
   không thẳng: sau bản đầu, **4 lượt review đối kháng (2 batch × 2 lăng kính) trả 36
   finding có reproduce** — nặng nhất là chính thước đo `adherence_view` báo 0%/2%/100%
   trong khi sự thật 53,6%/52,2%/48,8%, rồi phiên bản sửa đầu lại double-count (54,2%).
   Tất cả đã sửa + test pin theo ground truth; fingerprint IDENTICAL vs TRƯỚC-toàn-bộ-
   Cycle-W (run_once 5 seed × 2 arm + multiday 3 ngày, chạy lại SAU mọi fix). Hồ sơ:
   `research/audit/2026-07-29-cycle-w-review/findings.md`. Verdict adherence của Cường:
   **hai tên** (`decision_adherence` + `event_adherence`), cấm khoá `adherence` trần.
   **Kế tiếp đã duyệt (PLAN-cycle-wx Phần B)**: B1 `net_mean_all` → B2 C1 hệ số 0 →
   B3 policy costs + `as_of` → B4 hai nợ nhỏ. Chi tiết cũ giữ bên dưới để tra cứu:
   ~~**ĐA-05 event store append-only**~~ (VỪA được B-02 mở khoá; Cường đã duyệt design
   từ 27/07, chi tiết `research/audit/2026-07-27-current-state/04-*` §6): SQLite local
   append-only + projections rebuild + JSONL export + EpisodeStore thành legacy adapter;
   sim để RAM chỉ thêm `run_id` (chốt của Cường). **Vào plan mode trước.**
   Thay thế: T-044 envelope v2 (cũng đã mở khoá) hoặc BUG-MOCKGEN-CLI (nhỏ, độc lập).
3. Sau đó cân nhắc: nợ UI card `standby_zone` (CHẶN bởi Q-04 chưa duyệt — đừng làm trước).

## Chờ Cường (KHÔNG tự quyết)

V-01..V-17 visual ("hỏi lại sau") · Q-03 corpus Khánh · Q-04 UX proposal · Q-07 dispatch H3
(đang theo (c)) · BUG-MOCKGEN-CLI mới ghi (pre-existing, reviewer reproduce).

## Bốn bài học phiên này PHẢI giữ (đã trả giá)

1. Con số lặp lại qua các can thiệp KHÁC NHAU = red flag của THƯỚC ĐO (BUG-EVAL-ARGMAX).
2. Test viết cho bug phải chứng minh ĐỎ khi bug quay lại; skip-khi-đối-tượng-tắt = lan can
   chết không giấy báo tử (T-046 quy tắc 5+6).
3. Không chạy suite nền song song với mutation-testing trên cùng file.
4. TDD phủ logic; review đối kháng phủ input thù địch — hai lớp bắt hai họ lỗi khác nhau.

---

# Việc dang dở + ý tưởng kiến trúc của Cường — phiên 2026-07-28

Ghi theo yêu cầu Cường: *"Document lại những phần dang dở và ý tưởng của tôi để không quên trong
phiên"*. File này là **bộ nhớ của phiên**, không phải quyết định đã chốt. Mục nào được chốt thì
chuyển sang `DIRECTIVES` / `TODO` / `DEFERRED` rồi xoá khỏi đây.

---

# PHẦN A — Ý TƯỞNG KIẾN TRÚC CỦA CƯỜNG (mới, chưa có spec)

## A1. Agent làm ROUTER trên không gian solver, có điều kiện theo CHÍNH SÁCH

> Cường (2026-07-28): *"Ý của tôi khi nói agent lo reasoning là để agent check chính sách để đưa ra
> quyết định dùng tool — ở đây là bài toán nào để tối ưu hóa doanh thu của tài xế, ví dụ chính sách
> free đổi pin hết hạn thì bỏ biến đó hay là điền arg về giá sạc pin là −xx việt nam đồng thay vì
> 0 đồng."*

**Đây KHÔNG phải "agent tự bịa số"** — ranh giới `CLAUDE.md §5` vẫn nguyên. Agent làm hai việc
khác hẳn:

| Agent quyết định | Agent KHÔNG quyết định |
|---|---|
| **bài toán nào** đang có nghĩa (solver nào gọi) | giá trị các con số |
| **biến nào còn sống** (pin miễn phí ⇒ bỏ số hạng chi phí pin) | mức chi phí là bao nhiêu |
| **điền arg nào** vào solver (`swap_cost = 0` hay `= −9.000`) | 9.000 lấy ở đâu ra |

Con số vẫn đến từ `policy_bundle` versioned; agent chỉ **đọc trạng thái chính sách rồi định hình
bài toán**. Đây là chỗ reasoning có giá trị thật mà rule cứng làm dở: số lượng tổ hợp
(cohort × ngày × chương trình khuyến mãi × loại xe) quá lớn để viết `if` tay.

**Ví dụ cụ thể đang có sẵn để thử:**

```
as_of ≤ 2029-03-31, tài xế Platform độc quyền
   ⇒ chi phí năng lượng = 0  ⇒ BỎ HẲN số hạng pin khỏi objective
                              (không phải đặt 0 — bỏ, để solver không tốn chiều state)

as_of > 2029-03-31
   ⇒ swap_fee = 9.000đ/lượt + thuê pin 175k/tháng
   ⇒ BẬT số hạng pin, và SOC trở thành biến kinh tế chứ không chỉ ràng buộc vật lý

đội sạc cắm, mọi thời điểm
   ⇒ cash_cost ≈ 70–93 đ/km  ⇒ số hạng luôn sống
```

**Chưa có gì cho việc này.** Router hiện tại (`gsm_core/advisor/router.py`) là zero-ML theo keyword
intent, **không đọc policy**.

### Câu hỏi thiết kế còn mở

1. Router đọc policy ở tầng nào — trước khi chọn solver, hay solver tự khai báo điều kiện sống?
2. Khi policy làm một biến chết, output có phải nói ra không (*"hiện không tính chi phí pin vì đang
   miễn phí tới 31/03/2029"*)? Tôi nghiêng về **có** — nếu không thì tài xế không hiểu vì sao lời
   khuyên đổi sau ngày đó.
3. Ranh giới fallback: policy thiếu/mâu thuẫn ⇒ agent im lặng hay dùng bản bảo thủ nhất?

## A2. Cache kết quả solver

> Cường: *"còn liên quan đến cache kết quả để không kéo tools hay phải tính nhiều lần cùng 1 bài"*

Hiện có `episode_store` (exact-key cache, kiêm `DecisionRecord`) từ C6 — nhưng khoá theo *câu hỏi*,
không theo *bài toán*. Ý tưởng: khoá cache = **problem digest** (input view đã chuẩn hoá +
`policy_version` + `as_of` bucket), để:

- 90 tài xế cùng ô, cùng bucket, cùng policy ⇒ **một** lần giải;
- policy đổi ⇒ digest đổi ⇒ **tự động invalidate**, không cần dọn tay;
- `SolverReport` đã có `problem_digest` sẵn — **chưa ai dùng nó làm khoá cache**.

⚠ Bẫy phải tránh: cache theo digest mà quên `as_of` thì lời khuyên buổi sáng bị dùng lại buổi tối.

## A3. Thiết kế lại / nâng cấp các bài toán tối ưu hoá hiện tại

Cường nêu chung với A1/A2. Neo vào bằng chứng đã đo trong phiên:

- hồ sơ `18-*`: bỏ REST+SWAP ⇒ Δ = **+0đ, CI [0,0]** — advisor là no-op tuyệt đối nếu không có 2
  kênh này; 94% đầu ra là `ONLINE` → không dịch được thành hành động;
- ⇒ không gian hành động của solver **thô hơn** của tài xế, và biến có đòn bẩy (**vị trí**) không
  nằm trong bài toán;
- ⇒ T-045a đang mở kênh vị trí; nhưng việc **định hình lại objective theo policy sống/chết** (A1)
  là tầng trên nó.

---

# PHẦN B — VIỆC DANG DỞ TRONG PHIÊN NÀY

## B1. Đã xong (đã commit hoặc đang ở working tree)

| | trạng thái |
|---|---|
| **b0-A** ba lỗi thời gian: nhãn bucket mất NGÀY · bucket MA sau 24:00 · hoãn ca quá đời thế giới | ✅ 6 test, mutation-proof M1/M2/M3 |
| **b0-B** đính chính comment `bucket_min: 60 (khớp l1r)` — l1r thực tế 30 | ✅ |
| **b0-C** `derive_allocation_input(bucket_min=…)` | ✅ 4 test, mutation-proof |
| **b1** `MarketStateView` core | ✅ 9 test (từ trước) |
| **b2** `Actor.enroute_cell` + `gsm_sim/market_state.py` | ✅ 11 test, mutation-proof W1/W2 |
| Hồ sơ chi phí `research/economics/driver-cost-structure-2026.md` | ✅ |
| Full suite | ✅ **605 passed / 5 skipped** |

**Đính chính đã ghi**: nghi ngờ *"UPDATE-047 nhánh `all` đã nhiễm lỗi bucket"* là **SAI** — đo
0/1197. Số cũ sạch, nhưng sạch do tình cờ (`demand_field` không có giờ 0), không do thiết kế.

## B2. Chưa làm — trong phạm vi T-045a đã duyệt

- **b0-D** `_sample_drop` cân theo cầu. Cường đã chốt *"sửa trước"*. Đo được: điểm trả khách
  **anti-tương quan** với cầu (**−0,226**); 10 ô cầu cao nhất chiếm 30,3% lượt ĐẶT nhưng chỉ
  **2,2%** lượt TRẢ; **82,3%** trả ngoài lõi ⇒ buộc deadhead. Cơ chế: vùng được phép trả 316 ô,
  lõi chỉ 85 (26,9%), và distance-decay còn đẩy ra vành ngoài.
- **b3** batch tick `_standby_planner` + S4 `capacity_alloc` + cờ `positioning_overrides`
  (`off` mặc định | `wait_only` | `wait_and_relocate` — Cường chốt **đo cả hai**).
- **b4** đo 30 seed × 3 nhánh. ⚠ **9 tiêu chí, không phải 7** — thêm 2 veto từ phát hiện hôm nay:
  **tỷ lệ km chạy rỗng không tăng** (nay **40,2%**) và **số lần đổi pin không tăng** (nay 118).

## B3. Chưa làm — phát sinh trong phiên, chưa được duyệt

> ⛔ **ĐÍNH CHÍNH 2026-07-29 (UPDATE-092) — HAI MỤC ĐẦU ĐÃ LÀM XONG Ở CYCLE P. ĐỪNG LÀM LẠI.**
> File này là **bộ nhớ của PHIÊN 28/07**, không phải trạng thái hiện hành. Verify bằng code
> trước khi claim bất kỳ mục nào bên dưới.

- ~~**T-045b tách hai khái niệm bị gộp**~~ ✅ **XONG (Cycle P)** — đã đổi tên
  `pickup_disutility_vnd_per_km` (`behavior.py:58, 86-91, 105, 114`), sổ chi phí tiền mặt tách
  riêng ở `actor.cost_vnd` (`world.py:97-98, 349-352`), config có `vehicle.swap_fee_vnd: 0` +
  `cash_cost_vnd_per_km: 0` (`configs/pilot_dongda.yaml:268-269`). **Còn lại:** cả hai mặc định
  **0** ⇒ chưa ai quét độ nhạy với số thật (30–250đ/km).
  <br>*Nội dung cũ:* `behavior.py:86` tính `net = gross − pickup_km × 3.000đ` (cảm nhận/disutility)
  nhưng `payout_vnd` không trừ gì.
- ~~**①` PolicyBundle` đọc `effective_from/to`**~~ ✅ **PHẦN LỚN XONG (Cycle P)** —
  `gsm_core/policy.py:29-34` khai field, `:54-55` đọc từ record, `:58-72` `is_valid_at()` với
  **tri-state đúng** (`None` = KHÔNG BIẾT ≠ "còn hiệu lực"); sim đọc ở `advice_bridge.py:151-158`,
  world cảnh báo ở `world.py:100-103`. **Còn lại 3 điểm hẹp:** (a) solver **chưa nhận `as_of` theo
  từng request** — mới kiểm 1 lần lúc khởi tạo world cho `_BASE_DATE`; (b) ngoài hạn **chỉ `log`,
  chưa fail-closed**; (c) `configs/pilot_dongda.yaml` **không đặt** `meta.policy_effective_from`
  ⇒ thực tế luôn `None` ⇒ lan can chưa từng chạy.
- **② quét độ nhạy số image-locked** (`driver_share ∈ [0,75–0,91]`) — gộp vào b4.
- **③ corpus hồi quy vàng**: N ca `(driver_state, as_of)` → advice kỳ vọng; đổi bundle ⇒ diff cho
  biết **câu nào đổi**. Cycle riêng sau b4.
- **④ registry đa phiên bản + re-run lịch sử** — **chặn bởi `B-02/ARCH-VERSION`**, cũng đang chặn
  ĐA-05/ĐA-06. Không đụng trước khi gỡ B-02.

## B4. Nợ cũ dễ rơi (không thuộc T-045a)

- **T-045c** dispatcher bỏ đơn oan (293/3.520 = 8,3%). Đọc code: đường code đó **đã biến mất** khi
  viết lại Hungarian — nhưng **chưa đo lại** để xác nhận về 0 ⇒ chưa được ghi DONE.
- **T-045e** `soc_pct` ba nguồn. UI xong (Q-06). **l1r còn nguyên**: `soc_pct = None` ⇒ `shift_dp`
  **im lặng giả định pin đầy** — khuyên tài xế 15% pin y như 100%.
- **T-041 1b'** chạy lại so ghép cặp **n≈105 seed** để kết luận dấu của fix BUG-S2-PARAMS.
- **T-042 3b** nối `shrunk_rate` vào SIM (còn hai estimator). Sẽ lệch baseline ⇒ đo lại.
- **T-042 4–8** ledger 4 nguồn · `bonus_at` vs `day_bonus` · `cards.js` ghép chuỗi tiền ngoài
  verifier · `SourceEnvelope` · trường `feasible` thừa.
- **T-046** quét `DEFAULT_PARAMS` 8 solver còn lại + `test_l3_views_derivable_from_l1r`.
- **Hàng đợi visual `V-01`…`V-16`** chưa ai xem; b4 sẽ đẻ thêm một mục.

---

# PHẦN C — TRẢ LỜI CÂU HỎI "STRUCTURED DATA HAY THUẦN TEXT?"

Hiện trạng **đã đo trong repo**, không phải phỏng đoán:

| Khoản | Structured? | Ở đâu |
|---|---|---|
| Chiết khấu (`driver_share`) | ✅ **có** | `schemas/l0/policy_bundle.schema.json` |
| Cước, điểm, mốc thưởng, ngưỡng, khoán tuần | ✅ có | như trên |
| Governance: `bundle_id` · `version` · `effective_from/to` · `source_url` · `track` · `service` | ✅ có, thiết kế tốt | như trên |
| **Giá đổi pin · giá điện · thuê pin · bảo dưỡng · thuế** | ❌ **không có ở BẤT KỲ schema nào** | mới chỉ văn xuôi trong `driver-cost-structure-2026.md` |
| Corpus policy dạng text (trích dẫn F0) | ✅ có, **nhưng tách rời** | `research/policy/t004-*.json` (claim Khánh) |

⇒ Kết luận: **structured data đã lo phần policy TIỀN CƯỚC/THƯỞNG, chưa lo phần CHI PHÍ.** Và hai
thế giới (bundle số ↔ corpus text) **chưa nối nhau** — trích dẫn không trỏ tới trường số nào.

**Đề nghị**: mở rộng `policy_bundle` thêm nhánh `costs` (`swap_fee_vnd`, `battery_rent_vnd_per_month`,
`free_swap_until`, `energy_vnd_per_kwh`, `maintenance_vnd_per_km`), mỗi trường mang
`effective_from/to` + `source_url` + `confidence` + `cohort` — **cùng cơ chế governance đã có**,
không phát minh cơ chế mới. Đây là điều kiện để A1 hoạt động.

---

# PHẦN D — THỨ TỰ ĐỀ NGHỊ (chưa chốt)

```
① PolicyBundle đọc effective_from/to        ← rẻ, chặn A1
   ↓
b0-D _sample_drop bám cầu                    ← Cường đã chốt "sửa trước"
   ↓
b3 + b4 (9 tiêu chí, ② quét độ nhạy gộp vào)
   ↓
T-045b tách cash_cost / disutility           ← cần duyệt, đổi hành vi
   ↓
A1 router theo policy + A2 cache theo digest ← cần spec riêng
   ↓
③ corpus vàng
   ↓
B-02 → ④ registry đa phiên bản → ĐA-05/06
```

⚠ Mỗi mũi tên đổi hành vi là **một lần đo lại baseline**. Đã đo lại 3 lần trong 2 ngày
(gốc → dispatcher tầng 2 → sốt ruột). `_sample_drop` là lần thứ 4.
