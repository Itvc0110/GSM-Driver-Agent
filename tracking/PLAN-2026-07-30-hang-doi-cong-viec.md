# KẾ HOẠCH — hàng đợi công việc còn lại, sắp theo thứ tự thi công

Ngày 2026-07-30 · Trạng thái: `READY` — chờ Cường ra lệnh làm tiếp
`origin/main` = **`3943cb2`** · suite **860 passed / 5 skipped / 0 failed** · cây sạch

Tài liệu này là **thứ tự thi công**, không phải danh sách ước. Mỗi mục có: **vì sao ở vị trí này**,
**chặn cái gì**, **acceptance**, **chi phí**. Ai đọc cũng làm tiếp được mà không cần hỏi lại.

---

## 0. Nguyên tắc sắp thứ tự (đọc trước, vì nó giải thích mọi vị trí bên dưới)

Ba tiêu chí, áp theo đúng thứ tự này:

1. **Cái gì làm SAI những phép đo sau nó?** → lên trước. Cycle này vừa trả giá đúng chỗ đó:
   `D-M3-01` sống được 39 artifact **chỉ vì** cổng hợp lệ (`D-M3-10`) chưa từng được nối.
2. **Cái gì đổi điều ta sẽ NÓI với hội đồng?** → lên trước cái chỉ đổi số nội bộ.
3. **Cái gì rẻ và đóng được một defect đang mở?** → chen vào giữa, không để nó nợ mãi.

⚠ **Chống một sai lầm cụ thể:** đừng đặt "thí nghiệm mới" lên đầu chỉ vì nó thú vị. Mọi Δ A/B hiện
tại được đo bằng một advisor **biết λ chính xác của generator** (`expected_demand_field`) trong khi
tài xế chỉ nhận `λ × nhiễu`. Đó là lý do `T-047` §4 xếp con số chủ lực **+6.016đ vào cột LUNG LAY**.
Vì thế **`E10` (advisor cũng nhiễu) đứng trên mọi thí nghiệm kênh khác** — không phải vì nó mới, mà
vì nó quyết định các Δ khác có nghĩa gì.

---

## 1. `L1-04` — dời `_claim_effect` xuống sau clamp khả thi

**Vị trí:** đầu tiên, vì nó **rẻ, đã có spec, và là defect ĐANG MỞ** trong đường tính liều can thiệp.

**Vấn đề (đo được):** lời khuyên `shift_extend` bất khả thi (kéo ca vượt `time.end_min`) **tiêu token
`_claim_effect`** rồi bị clamp về 0 ⇒ mọi lần hỏi lại trong bucket đó trả `False` ⇒ **38/135 = 28%
quyết định mất hẳn**, không có đường quay lại.

**Đây là thay đổi ĐỔI HÀNH VI THẬT** — không gộp với bất cứ gì khác:
- Sau khi dời, token không cháy ⇒ một lần hỏi sau trong cùng bucket **có thể áp được** ⇒ liều can
  thiệp tăng ⇒ Δ đổi.

**Acceptance:**
- Test đỏ trước: `test_infeasible_extend_does_not_burn_claim` — actor có `shift_end_min` sát
  `world_end_min`; hỏi lần 1 (bất khả) rồi nới `world_end_min` và hỏi lại **trong cùng bucket** ⇒
  phải áp được. Hôm nay lần 2 trả 0.0.
- Δ`net_mean_all` ở **n≥100 ghép cặp CRN** + guardrail 4 tầng ĐA-08 + `others_payout_vnd`.
- `run_ladder` phải cho `verdict: OK` (cổng `D-M3-10` mới nối) — nếu `TREO` thì dừng, không báo Δ.
- Fingerprint per-actor **PHẢI KHÁC** (đó là đúng — đây là đổi hành vi). Ghi rõ trong UPDATE để
  không ai đọc thành nhiễm stream.

**Chi phí:** implement + test ~15′ · đo n=100 ghép cặp ~50–70′ · full suite ~25′ ⇒ **~1,5–2 giờ**.
**Chặn:** không chặn gì. **Spec:** `specs/simulation/d-m3-01-adherence-denominator-fix.md` §5 bước 4.

---

## 2. Cổng THỐNG KÊ của `D-M3-10` — ✅ ĐÃ CHỐT cơ chế, chờ thi công

**Vị trí:** ngay sau `L1-04`, vì `L1-04` là phép đo đầu tiên chạy dưới cổng mới ⇒ nó cho ta dữ liệu
thật để chọn tolerance thay vì đoán.

**Hiện trạng:** `D-M3-10` đã nối **cổng BẤT KHẢ** (adherence đúng 1,0/0,0 trên mẫu số ≥20 · `decided=0`
· `event_decided=0` trong khi `decided>0`). **Cổng THỐNG KÊ cố ý chưa nối.**

**Vì sao chưa nối, và đây là mục cần chốt:** ngưỡng **0,02** của luật gốc **không áp per-seed được** —
với ~250 quyết định/seed, SE lấy mẫu ≈ **0,03** ⇒ cổng 0,02 mỗi seed **bắn liên tục vì nhiễu**, và
người sửa sẽ **nới ngưỡng thay vì sửa lỗi** (đúng mẫu `D-R20`). Nối một ngưỡng sai **tệ hơn** không
nối, vì nó sẽ bị tắt.

### ✅ ĐÃ CHỐT 2026-07-30 — Cường: *"Bạn chốt, tôi nghiêng về (c)"*

**Chốt (c), nhưng SỬA CƠ CHẾ: dùng kiểm định z Poisson-binomial phân tích, KHÔNG bootstrap.**

Ba phương án ban đầu:

| | Phương án | Phán quyết |
| --- | --- | --- |
| (a) | Giữ 0,02, áp trên TỔNG n seed | ❌ **BÁC** — xem bảng dưới: 0,02 **không phải một ngưỡng**, nó là 0,40σ ở n=100 và 2,83σ ở n=5000 |
| (b) | Tolerance = `k × SE(n)`, k=3 | ❌ **BÁC** — đúng hướng nhưng vẫn có hằng số tự đặt, và bỏ qua **hỗn hợp archetype** |
| (c) | CI bootstrap phải chứa adherence danh nghĩa | ✅ **NHẬN nguyên tắc** (không hằng số tự đặt, tự co theo n) — nhưng **thay bootstrap bằng công thức chính xác** |

**Vì sao sửa cơ chế của (c):** ta **biết chính xác** phân phối null, không cần resample. Mỗi quyết
định `i` là `Bernoulli(p_i)` với `p_i` = adherence danh nghĩa của **archetype của chính tài xế đó**
(`DEFAULT_ADHERENCE`: P1 0,55 · P2 0,50 · P3 0,30 · P4 0,75 · P5 0,30 · P6 0,50 · P7 0,50). Tổng của
chúng là **Poisson-binomial**, có kỳ vọng và phương sai đóng:

```
mu  = Σ p_i / n
var = Σ p_i(1 − p_i) / n²
z   = (adherence_đo − mu) / √var          ⇒  TREO khi |z| > 4
```

Bootstrap resample **các quyết định đã quan sát** ⇒ nó coi mọi quyết định là **trao đổi được**. Công
thức trên **không** — nó dùng `p_i` thật của từng archetype, nên nó **tự xử lý hỗn hợp archetype**
của tập quyết định mà kênh đó thực sự chạm tới. Với một kênh chỉ chạm P3/P5 (p = 0,30) thì null là
0,30, không phải trung bình toàn đội. Bootstrap không phân biệt được điều đó.

Coin là **keyed sha256** (`adherence_coin`), seed nằm trong khoá ⇒ độc lập giữa các khoá và giữa các
seed ⇒ giả định Bernoulli độc lập **đứng vững**. Đây là lý do dùng được công thức đóng.

**Ngưỡng |z| > 4 là DẪN XUẤT, không phải chọn bừa** (`uv run python` tính tại chỗ 2026-07-30):

| Tình huống | z |
| --- | --- |
| 🔴 **Lỗi thật `D-M3-01`** (adherence báo 1,000 trên 101 quyết định, mu 0,500) | **10,0** |
| "Lệch 0,02" ở n=100 | 0,40 |
| "Lệch 0,02" ở n=250 | 0,63 |
| "Lệch 0,02" ở n=1000 | 1,26 |
| "Lệch 0,02" ở n=5000 | 2,83 |

⇒ **Bảng này một mình bác phương án (a):** cùng một "lệch 0,02" là **nhiễu thuần** ở n=100 và **gần
có ý nghĩa** ở n=5000. Một ngưỡng cố định trên hiệu tuyệt đối không thể đúng ở cả hai.

Chọn 4 vì family-wise trên **28 ô** (4 kênh × 7 archetype):

| ngưỡng | per-ô | family-wise 28 ô |
| --- | --- | --- |
| \|z\| > 3,0 | 2,7e-03 | **7,29%** — quá ồn, sẽ bị tắt |
| \|z\| > 3,5 | 4,7e-04 | 1,29% |
| **\|z\| > 4,0** | **6,3e-05** | **0,18%** ✅ |
| \|z\| > 4,5 | 6,8e-06 | 0,02% — chặt hơn mức cần |

**4,0 giữ được cả hai đầu:** bắt lỗi thật (z=10) với biên **2,5×**, và bắn oan **0,18%** mỗi lần chạy.
Đó là điều kiện để cổng **không bị tắt vì nhiễu** — nguyên nhân đã giết ngưỡng 0,02.

**Acceptance (phải chứng minh được, không chỉ mô tả):**
1. Arm dựng adherence lệch danh nghĩa **0,10** ở n≥250 ⇒ **TREO**.
2. Arm lệch **0,01** ở n≥250 ⇒ **OK** (không bắn oan).
3. Dựng lại đúng trạng thái `D-M3-01` (adherence 1,000) ⇒ **TREO**, và z báo ra ≈10.
4. Một kênh chỉ chạm **P3/P5** (p=0,30) với adherence đo 0,30 ⇒ **OK** — chứng minh null theo hỗn hợp
   archetype, không theo trung bình toàn đội. Đây là test mà bootstrap **không** vượt được.

**Chi phí sau khi đã chốt:** ~1 giờ (công thức đóng, không cần resample).
**Chặn:** không, nhưng để lâu thì mọi artifact mới chỉ có nửa cổng.

---

## 3. 🔴 `E10` — arm "ADVISOR CŨNG NHIỄU": việc quan trọng nhất còn lại

**Vị trí:** trên mọi thí nghiệm kênh khác. **Không phải vì mới — vì nó quyết định các Δ khác có
nghĩa gì.**

**Vấn đề:** advisor nhận `expected_demand_field` = **đúng λ** mà generator dùng
(`orders_per_day × hour_share × cell_weight`, `src/gsm_sim/demand.py:76`), trong khi tài xế chỉ nhận
`λ × nhiễu per-actor` (`world._actor_demand_hint`, σ = 0,10–0,60 theo archetype).

⇒ `T-047` §4 hàng 1 xếp **+6.016đ/người/ngày** (con số chủ lực của dự án, UPDATE-087) vào cột
**LUNG LAY**, và ghi rõ: *"không phải sai 2× mà **sai về bản chất nguồn tin**"*. Ngoài đời tín hiệu
tốt nhất là mật độ cuốc **ĐÃ phục vụ** (không có unserved) — thiên lệch có hệ thống về nơi **đã có**
tài xế, tức **đúng hướng làm herding TỆ HƠN**.

**Hai arm, làm theo thứ tự:**

### 3a. `E10a` — advisor dùng cầu ĐÃ THỰC HIỆN
Thay `expected_demand` bằng ước lượng cuốn từ cuốc đã hoàn thành trong k bucket gần nhất.
- Bẫy: **KHÔNG được đọc `orders` chưa phục vụ** — đó là future leak, và cũng không tồn tại ngoài đời.
- Bẫy: cửa sổ cuốn k là **tham số mới** ⇒ phải quét độ nhạy, không chọn k vì nó cho Δ dương.

### 3b. `E10b` — advisor dùng THỜI GIAN CHỜ (trả lời trực tiếp câu hỏi của Cường 2026-07-30)
Điều kiện kích hoạt đổi từ `capacity_left == 0` sang **chờ trung vị của tài xế IDLE trong ô** vượt
ngưỡng.
- 🔴 Bẫy lớn nhất: phải gộp **theo Ô**, **không** theo từng người. Chờ của một tài xế là **nhiễu
  Poisson** ⇒ luật per-driver sẽ bắn trên vận rủi trong một ô thật sự tốt. Đây đúng kỷ luật mẫu số
  của `D-M3-01`.
- Bẫy: giữ `supply_incoming` để hãm dao động (khuyên đi làm chờ ở ô đích tăng ⇒ vòng phản hồi).
- Dữ liệu **đã có sẵn**: `actor.idle_by_hour` tồn tại và đang nuôi S7 `idle_reduction` cho
  `rest_window`; chỉ chưa nối vào positioning. Chi phí thấp hơn tưởng.

**Acceptance chung cho E10:** so **ba** arm trên cùng seed ghép cặp n≥100 — `oracle-λ` (hiện tại) ·
`E10a` · `E10b`. Câu hỏi cần trả lời **không phải** "arm nào tốt nhất" mà:
> **+6.016đ còn lại bao nhiêu khi advisor mất λ?**

Nếu nó sụp về gần 0 thì đó là **kết quả quan trọng nhất dự án từng đo**, và nó phải được báo đúng
như vậy — không được im lặng chọn arm oracle để trình bày.

**Chi phí:** thiết kế + brainstorm/plan ~2–3 giờ · implement ~3–4 giờ · đo 3 arm × n=100 ~3–4 giờ
⇒ **~1–1,5 ngày làm việc**. **Chặn:** cách trình bày con số chủ lực với hội đồng.

---

## 4. Ba tiên quyết của cổng `rest_window` (`D-M3-04` · `D-M3-05` · `D-M3-08`)

**Vị trí:** sau `E10`, vì cổng tiền-đăng-ký của `rest_window` đo Δ tiền — và Δ tiền trong chế độ
oracle-λ có cùng vấn đề ở §3.

| Mã | Việc | Ghi chú |
| --- | --- | --- |
| `D-M3-04` | `planned_rest_hour` **chưa từng chạy trong A/B** (chỉ có ở `multiday.py:166/232`) ⇒ kênh nói **0/873 lần**, và bậc thang `rest_window` **bit-identical với `s2_only`** cả 5 seed | Hoặc bật multiday trong A/B, hoặc gắn nhãn "arm trùng" vào mọi artifact |
| `D-M3-05` | Guardrail tầng 5: `rest_min_total` · `veto_fired_n` · `max_continuous_drive_min` | Phải có **TRƯỚC** khi đo, không thêm sau |
| `D-M3-08` | **4/6 cơ chế enforce của khung BA LỚP không tồn tại**: `POLICY_LOCKED_KEYS`, `test_no_fatigue_in_payout_path`, và 3 chỉ tiêu tầng 5 | `C2′` **không được đo** trước khi cả 4 có thật |

**Cổng tiền-đăng-ký** đã khoá ở `tracking/QUYET-DINH-2026-07-30-nam-diem.md` §3.3 — **không sửa sau
khi đã đo**. Kỳ vọng của tôi ghi trước: **gần 0** (trần kênh ≤29% do lan can sức khoẻ).

**Chi phí:** ~4–6 giờ cho cả ba.

---

## 5. Đường SẢN PHẨM — 13 finding sev CAO chưa phản biện

**Vị trí:** cycle **riêng**, không chen vào sim. Chạm cùng lúc là không quy được nhân quả cho Δ nào.

Nặng nhất, tôi **đã tự kiểm bằng đọc code** (không phải claim của agent):

| Mã | Cái gì sai |
| --- | --- |
| `L3-03` | 🔴 **`followed` LUÔN thắng `dismissed`** bất kể tài xế bấm gì sau cùng — `occurred_at` là hằng số theo loại card ⇒ phá thế hoà bằng chuỗi `event_id`, `"d" < "f"` ⇒ **sản phẩm không thể ghi nhận tài xế đổi ý** |
| `L4-01` | Sản phẩm ghi `displayed`, sim ghi `decided` ⇒ **`event_adherence` ở sản phẩm vĩnh viễn `None`** — một nửa bộ đo hai-tên chết im lặng |
| `L4-03` | Cooldown 20′ vs khoá event bucket 30′ ⇒ **khe advisor nói MIỄN PHÍ** (card tới tay mà không event, không tiêu ngân sách) — họ lỗi `F-1` sống lại |
| `L4-04` | `GET /advice` có default `topic="bonus"` mà **không client nào gửi** ⇒ namespace mồ côi có cooldown/dismiss riêng |
| `L4-07` | Card IM LẶNG vẫn vẽ kèm nút "Làm theo" với `advice_id` do **client bịa** ⇒ một cú bấm tạo decision+followed cho quyết định advisor **chưa từng đưa ra** |
| `L4-09` | Pha ca sản phẩm dùng hằng `SHIFT_START_MIN = 6*60` cho **mọi** tài xế — wall-clock quay lại đúng chỗ ĐA-04 tuyên bố đã bỏ |

⚠ **Chưa cái nào qua phản biện đối kháng** (16/16 agent phản biện fail vì session limit, **hai lần**).
Danh sách đầy đủ: `tracking/SOI-2026-07-30-mau-so-adherence.md` §4.

**Chi phí:** ~1–2 ngày. **Chặn:** mọi kết luận từ sim áp cho sản phẩm.

---

## 6. `E9` — chọn lọc TRONG một kênh (lever thay `E1`)

**Vị trí:** sau `E10`, cùng lý do.

`E1` (4 cơ chế trọng tài ngân sách) đã **`DEFERRED-CÓ-ĐIỀU-KIỆN`** (`D-M3-07`) vì **NULL-0**: giải
thưởng +2.207đ **đã bị ĐA-07 lấy bằng một dòng YAML** (+2.259đ SIG), và ở cấu hình sản phẩm giá của
nhịp = **−259đ ns** ⇒ trọng tài khéo hơn có headroom ≈ **0đ**. Spec đầy đủ vẫn lưu ở
`specs/simulation/e1-budget-arbitration-4-mechanisms.md`.

**Lever thay thế:** `shift_plan` trung tính khi đứng một mình (+53đ ns · −451đ ns, hai phép đo n=100
độc lập) nghĩa là lời khuyên **tốt và tệ của nó triệt tiêu nhau**. Cả 4 cơ chế của `E1` đều *chia
suất GIỮA các kênh*; **không** cơ chế nào **chọn lọc TRONG một kênh**. Artifact 38/39 không nói gì
về lever này.

**Chi phí:** ~1 ngày.

---

## 7. Mục cần Cường chốt (không đo được)

| # | Câu hỏi | Ở đâu |
| --- | --- | --- |
| 2 | **4 mục của `T-047`** ở phụ lục spec | `specs/real-data/data-contract-counterfactual.md` §9.2 |
| 3 | **`V-18`** — nhịp nói advisor (UPDATE-099) | `tracking/PENDING-REVIEW.md` |
| 4 | **`V-01`…`V-14`** — 14 mục visual/data | idem |
| 5 | **`B6-PARITY`** — UI chỉ chạy 1/9 solver; Khánh có thể nhận | `tracking/DEFERRED.md` |

---

## 8. Việc KHÔNG làm, và vì sao (để không ai đào lại)

| Việc | Vì sao không |
| --- | --- |
| Mô hình hoá **hậu quả của mệt** | **HUỶ VĨNH VIỄN** — quyết định nguyên tắc, không mở lại bằng dữ liệu mới. Mọi cơ chế tạo `∂payout/∂F`, một tỷ giá sức-khoẻ↔tiền; viết vào *world* thay *objective* chỉ xoá NHÃN. `specs/advisor-objective-model-v2.md` §1.2b |
| `E1` — 4 cơ chế trọng tài ngân sách | Headroom ≈ 0đ (`D-M3-07`). Mở lại **chỉ khi** bật một kênh ÂM |
| Sửa `window_past` của `rest_window` | Hạ ưu tiên (`D-M3-06`): trần ≤17,8%, và kênh này về bản chất không đáng định giá bằng tiền |
| Thêm "chờ lâu" làm **input thứ hai** cho luật positioning hiện tại | Sẽ đo ra ≈0: advisor **đã biết λ chính xác**, chờ là mẫu **nhiễu của chính λ đó** ⇒ giảm thông tin. Đúng chỗ của nó là **thay** λ trong `E10b`, không phải thêm vào |
| Xin GSM cấp thêm dữ liệu | Cường chốt 2026-07-30: **không có data thật từ GSM hay được cung cấp gì thêm** |

---

## 9. Nợ kỹ thuật nhỏ, chen vào khi có khe

- `D-M3-02` — đưa `fingerprint_actors` vào `src/gsm_sim/sim_metrics.py` và **thay `assert_crn`** ở mọi
  test "kênh tắt ⇒ bit-identical". Bản chạy được đã có trong `scripts/probe_adherence_truth.py`.
- `D-M3-09` — cân nhắc thêm `ui/backend/tests` vào `testpaths`; phải kiểm xung đột `conftest`/fixture
  giữa hai cây test trước.
- `D-M3-03` — comment sai `behavior.py:157` (*"xác suất tăng theo fatigue"* — code là hằng `0.3`) +
  nhãn ASSUMPTION cho `fatigue_threshold_min` (240′ của Điều 64 áp **ô tô**, đoàn pilot là **bike 100%**).
- Đo lại adherence ở **30 seed** trước khi đưa số 0,47 vào artifact công bố (hiện 3 seed).
- Soi độc lập tầng **L2 (`world.py`)** — đã chạy được một lần, nhưng 16 agent phản biện fail cả hai lần.

---

## 10. Trạng thái để bắt đầu lại

```
origin/main = 3943cb2   (16 commit từ c493d89)
suite       = 860 passed / 5 skipped / 0 failed
              uv run pytest -q            -> 804 + 5 skip  (809 thu thập)
              uv run pytest -q ui/backend/tests -> 56
cây làm việc = sạch
```

⚠ **Luôn chạy CẢ HAI lệnh** khi nói "suite xanh" (`D-M3-09`).

⏳ **PENDING-REVIEW** (lệ CLAUDE.md §3.1 — hoãn ≠ waive): **V-15 đã đóng**; còn mở **V-01…V-14** và
**V-18**, cộng mục ❓/⛔ trong `tracking/PENDING-REVIEW.md`.
