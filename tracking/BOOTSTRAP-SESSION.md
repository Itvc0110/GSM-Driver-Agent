# BOOTSTRAP SESSION — prompt để nạp một AI coding agent mới vào dự án này

Cập nhật: **2026-07-30** · `origin/main` = **`3943cb2`**

**Cách dùng:** mở session mới, paste đoạn trong khung §0 dưới đây. Không cần paste cả file này —
đoạn đó trỏ agent tới đúng các file phải đọc, theo đúng thứ tự.

**Cách bảo trì:** sau mỗi cycle có ý nghĩa, cập nhật **§2 (state)** và **§3 (hàng đợi)** của file này.
Đừng để nó stale — một bootstrap sai còn tệ hơn không có, vì agent sẽ tin nó.

---

## §0. ĐOẠN CẦN PASTE

```text
Bạn là AI coding agent làm việc trong repo GSM-Driver-Agent. Trước khi làm BẤT KỲ việc gì,
đọc theo ĐÚNG thứ tự này — đừng đọc lại toàn bộ lịch sử, hãy đi theo route:

1. CLAUDE.md                                  — harness bắt buộc, thắng mọi tài liệu khác
2. tracking/BOOTSTRAP-SESSION.md              — file này: state hiện tại + hàng đợi + BẪY đã sập
3. tracking/PLAN-2026-07-30-hang-doi-cong-viec.md  — THỨ TỰ THI CÔNG, có acceptance + chi phí
4. tracking/PENDING-REVIEW.md                 — việc Cường đang chờ check; PHẢI nhắc lại sau MỖI update
5. tracking/PROJECT-GRAPH.md                  — chọn route đọc theo task (KHÔNG đọc hết UPDATE)
6. tracking/DEFERRED.md + tracking/TODO.md    — khi task chạm scope/status/claim/policy
7. git log --oneline -8 + git status          — biết mình đang ở đâu; đừng tin ký ức

Sau đó ĐỌC MỤC §3 và §5 của tracking/BOOTSTRAP-SESSION.md rồi báo lại cho tôi:
(a) bạn hiểu state hiện tại là gì, (b) bạn định làm mục nào đầu tiên và vì sao,
(c) có gì trong hàng đợi bạn thấy sai thứ tự.

Đừng bắt đầu code trước khi tôi duyệt. Ngôn ngữ trao đổi: tiếng Việt.
```

---

## §1. Dự án là gì (30 giây)

Hệ thống AI giúp tài xế Xanh SM (GSM) cải thiện thu nhập. Team 2 người: **Cường** + **Khánh**.

Có **hai nửa**, và phân biệt được hai nửa này là điều kiện để hiểu mọi tài liệu:

| | Trả lời câu hỏi gì | Ở đâu |
| --- | --- | --- |
| **SIM** (twin-world A/B, SimPy) | *"Nội dung lời khuyên có giá trị không?"* → đo **TRẦN** giá trị advisor | `src/gsm_sim/` |
| **SẢN PHẨM** (FastAPI + web + Flutter) | *"Advisor nói bao nhiêu là không phiền?"* | `ui/`, `src/gsm_core/` |

⚠ **Nhịp nói (cadence) thuộc SẢN PHẨM, KHÔNG thuộc SIM** — Cường chất vấn 2026-07-29 và agent đã
phải thừa nhận lập luận cũ sai. `advice.cadence.enabled: false` là mặc định **đúng**, không phải bug.

**Ranh giới CỐ ĐỊNH** (đọc `CLAUDE.md` §5, đây chỉ là ba cái bị vi phạm nhiều nhất):
- Agent/LLM **không tự tính** số tài chính/xác suất — mọi số đến từ rule/analytics kiểm chứng được.
- **Sức khoẻ tài xế KHÔNG phải biến để tối ưu.** Đã có phán quyết: **không mô hình hoá hậu quả của
  mệt**, huỷ vĩnh viễn (`specs/advisor-objective-model-v2.md` §1.2b).
- Mock data **phải gắn nhãn mock**. Mọi số trong repo là MOCK; **GSM sẽ không cấp thêm dữ liệu**.

---

## §2. STATE hiện tại (2026-07-30)

```
origin/main = 3943cb2   (16 commit từ c493d89, fast-forward, cây sạch)
suite       = 860 passed / 5 skipped / 0 failed
              uv run pytest -q                  -> 804 + 5 skip   (809 thu thập)
              uv run pytest -q ui/backend/tests -> 56
UPDATE       = 97 file, mới nhất UPDATE-103
PENDING      = 17 mục V- đang chờ Cường:
              V-01..V-14 (visual/data SIM + Track UI) · V-16 (fare parity gate)
              V-17 (kênh VỊ TRÍ b3/b4) · V-18 (nhịp nói advisor)
              ⚠ V-16/V-17 dễ bị đọc thiếu — agent đã nhiều lần chỉ đọc V-01..V-14 + V-18
```

🔴 **BẮT BUỘC: luôn chạy CẢ HAI lệnh khi nói "suite xanh".** `pyproject.toml` có
`testpaths = ["tests"]` nên `pytest -q` từ root **BỎ 56 test ở `ui/backend/tests/`** — tức bỏ đúng
test của **đường sản phẩm** (`D-M3-09`).

### Cấu hình đang chạy (đọc kỹ, dễ hiểu sai)

| Cờ | Giá trị | Nghĩa |
| --- | --- | --- |
| `advice.enabled` | **false** | Ở config mặc định **advisor im hoàn toàn**. A/B bật cờ này qua `_cfg_with` để đo |
| 4/5 kênh (`shift_plan`, `accept_lift`, `shift_extend`, `rest_window`) | **false** | Tắt theo ĐA-07 — *"không hiệu quả thì TẮT để advisor IM LẶNG"* |
| `positioning_overrides` | **`wait_only`** | Kênh **duy nhất** được duyệt bật. Chỉ ghi đè khi bản năng là ĐỨNG CHỜ |
| `advice.cadence.enabled` | **false** | Nhịp thuộc SẢN PHẨM (xem §1) |

### Vừa xong (2 cycle cuối)

- **`D-M3-01`** — mẫu số adherence hỏng ở 3 tầng. `shift_extend` báo **1,000** trong khi sự thật
  **0,473** (thổi **2,1×**). Đã sửa → **0,475**. Behavior-neutral: fingerprint per-actor 15/15 IDENTICAL.
- **`D-M3-10`** — luật *"mọi arm báo adherence, lệch ⇒ TREO"* **chưa từng được thi hành** (đường ống
  A/B tham chiếu `adherence` **0 lần**; artifact 35–39 **không có khoá nào**). Đó là **lý do trực tiếp**
  `D-M3-01` sống qua 39 artifact. Đã nối cổng **BẤT KHẢ** + 9 test.
- **`T-047`** — spec hợp đồng dữ liệu phản thực, 1.280 dòng, `WAITING-VERDICT`.

---

## §3. HÀNG ĐỢI — đọc `tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` để có acceptance đầy đủ

| # | Việc | Chi phí | Trạng thái |
| --- | --- | --- | --- |
| 1 | **`L1-04`** — dời `_claim_effect` sau clamp khả thi. **28% quyết định `shift_extend` đang mất hẳn** | ~1,5–2 giờ | spec xong, **ĐỔI HÀNH VI** ⇒ UPDATE riêng + n≥100 |
| 2 | **Cổng THỐNG KÊ** của `D-M3-10` | ~1 giờ | ✅ **cơ chế ĐÃ CHỐT**: z Poisson-binomial, `\|z\| > 4` |
| 3 | 🔴 **`E10` advisor-cũng-nhiễu** — **quan trọng nhất còn lại** | ~1–1,5 ngày | chưa thiết kế |
| 4 | 3 tiên quyết cổng `rest_window` (`D-M3-04/05/08`) | ~4–6 giờ | chờ |
| 5 | Cycle **đường SẢN PHẨM** — 13 finding sev CAO | ~1–2 ngày | chưa phản biện |
| 6 | **`E9`** chọn lọc TRONG kênh | ~1 ngày | chờ |

**Vì sao `E10` đứng trên mọi thí nghiệm kênh khác** — và đây là điều một agent mới dễ bỏ sót:

Advisor nhận `expected_demand_field` = **đúng λ mà generator dùng** (`src/gsm_sim/demand.py:76`),
trong khi tài xế chỉ nhận `λ × nhiễu per-actor`. Ngoài đời advisor **không bao giờ** có λ. Vì thế
`T-047` §4 hàng 1 xếp con số chủ lực **+6.016đ/người/ngày vào cột LUNG LAY** — *"không phải sai 2× mà
sai về bản chất nguồn tin"*. `E10` phải trả lời:

> **+6.016đ còn lại bao nhiêu khi advisor mất λ?**

Nếu nó sụp về gần 0 thì đó là kết quả quan trọng nhất dự án từng đo, và **phải báo đúng như vậy** —
không được im lặng chọn arm oracle để trình bày.

### Việc KHÔNG làm (đọc `PLAN-...-hang-doi` §8 trước khi đề xuất bất cứ gì)

Mô hình hoá **hậu quả của mệt** (huỷ vĩnh viễn) · **`E1`** 4 cơ chế trọng tài ngân sách (headroom ≈0đ,
`D-M3-07`) · sửa **`window_past`** · **xin GSM thêm dữ liệu** · thêm "chờ lâu" làm **input thứ hai**
cho luật positioning (sẽ đo ra ≈0 — xem §5 bẫy #7).

---

## §4. Tài liệu source-of-truth (đọc khi task chạm tới)

| File | Khi nào đọc |
| --- | --- |
| `specs/advisor-objective-model-v2.md` | Bất cứ gì chạm hàm mục tiêu. **§1.2b** = ranh giới sức khoẻ, C2 huỷ, `C2′` thay |
| `specs/real-data/data-contract-counterfactual.md` | Bất cứ gì chạm dữ liệu. **§4 (dòng 746)** = 17 kết luận xếp VỮNG/LUNG LAY/KHÔNG THỂ KIỂM |
| `specs/simulation/d-m3-01-adherence-denominator-fix.md` | Chạm adherence / mẫu số / thước đo |
| `specs/adherence-measurement.md` | Bản đồ chung hai đường đo. ⚠ **ĐỌC ĐÍNH CHÍNH 2026-07-30** — nó đảo một kết luận của spec: **hai đường hiện KHÔNG JOIN ĐƯỢC** (topic rời nhau · sản phẩm không emit `decided` · `followed` mang hai nghĩa · kênh không giao nhau) |
| `research/audit/2026-07-27-current-state/README.md` | **TRƯỚC KHI TRÍCH BẤT KỲ SỐ NÀO.** Có cảnh báo chung: artifact 31–39 đo bằng thước chưa được kiểm, và 31–35 **BỊ TREO** |
| `tracking/QUYET-DINH-2026-07-30-nam-diem.md` | 5 quyết định V-15 + **cổng TIỀN-ĐĂNG-KÝ** của `rest_window` (khoá, không sửa sau khi đo) |

---

## §5. 🔴 BẢY BẪY ĐÃ SẬP THẬT — đọc trước khi tin bất kỳ con số nào

Đây là phần giá trị nhất của file này. Mỗi bẫy dưới đây **đã làm một con số bị báo sai cho Cường**.

**1. Đo bằng thước chưa được kiểm.** `shift_extend` báo adherence **1,000** suốt **39 artifact** vì
event chỉ được ghi khi tài xế ĐÃ THEO ⇒ mẫu số chỉ chứa người đã theo ⇒ 1,0 **theo cấu trúc**.
Họ lỗi này có tên: **`BUG-EVAL-ARGMAX`**. ⇒ **Trước khi tin một Δ, kiểm cổng `verdict` của arm đó.**

**2. Test không thể ĐỎ.** Test regression của họ lỗi `F-1` lại **khắc chính lỗi đó thành kỳ vọng**:
assert cả `decided` và `followed` bằng **CÙNG một biến đếm** ⇒ đồng nhất thức. ⇒ **Mọi cổng mới phải
được CHỨNG MINH là đỏ được**, không chỉ mô tả.

**3. Trộn ĐƠN VỊ.** `decision_adherence` đếm theo **QUYẾT ĐỊNH** (gộp bucket 30′); coin đếm theo
**LẦN HỎI**. Trộn hai cái cho ra "sai 3,2×" thay vì **2,1×** — và cho ra "LỆCH" **oan** cho một kênh
đang đúng. ⇒ **Luôn nói rõ đơn vị. Cấm khoá `adherence` trần.**

**4. Cơ chế bảo vệ chỉ sống trên giấy.** Hai lần: `D-M3-08` (4/6 cơ chế enforce của khung BA LỚP
không tồn tại) và `D-M3-10` (cổng hợp lệ A/B tham chiếu `adherence` 0 lần). ⇒ **`grep` xem cơ chế
mình vừa viết trong tài liệu có tồn tại trong code không.**

**5. Arm đối chứng KHÔNG sạch.** `DET-01`: tắt cờ `cadence.enabled` cũng tắt luôn keyed coin ⇒ arm
đối chứng có adherence cao hơn ~10đp vì lý do không liên quan. Con số đã báo **−3.048đ**, sự thật
**−1.530đ**. ⇒ **Đo adherence hiệu dụng của arm đối chứng TRƯỚC khi tin Δ.**

**6. `assert_crn` KHÔNG phải bằng chứng bit-identical.** Nó chỉ so danh sách đơn, mà đơn sinh **ngoài**
world ⇒ trả `True` dù mọi quỹ đạo actor đã lệch. ⇒ **Dùng fingerprint PER-ACTOR** (bản chạy được ở
`scripts/probe_adherence_truth.py`).

**7. "Cơ chế đúng, ĐỘ LỚN sai" — sập 3 lần.** `DET-01` sai 5,7× · chẩn đoán `window_past` sai 5,4× ·
mức thổi 3,2× vs 2,1×. ⇒ **Soi độc lập bắt được cơ chế nhưng thường sai độ lớn. Tự đo lại độ lớn
trước khi trích.** (~1/4 finding của soi độc lập là sai hoặc phóng đại.)

### Bẫy vận hành

- `pytest -q` từ root **bỏ 56 test** đường sản phẩm (§2).
- `_cfg_with(..., coverage=...)` mặc định `"single"`; truyền `actor_id=None` cùng nó ⇒ **không ai được
  advisor phủ** ⇒ bạn đang đo cái tắt của chính mình.
- `_agg()` trong test **cộng dồn mọi trường số**, kể cả `decision_adherence` ⇒ trường đó là **tổng tỷ
  lệ** của ~86 tài xế, không phải một tỷ lệ.
- So hash bằng `awk` trên file **CRLF** cho kết quả "KHÁC" sai.
- `TaskStop` để lại child python chiếm CPU (suite 18′ → 90′).
- Con số nào định trích thì **mở artifact JSON gốc** ra đọc — nhiều artifact (31–35) **BỊ TREO**.

---

## §6. Quy trình bắt buộc (rút gọn — bản đầy đủ ở `CLAUDE.md` §3/§4/§4b)

1. **Plan mode trước** mọi thay đổi code/contract/docs quan trọng. Hỏi lại điều chưa rõ, đừng đoán.
2. **UPDATE-### sau mỗi thay đổi** có ý nghĩa, theo `tracking/updates/UPDATE_TEMPLATE.md`. Phải có mục
   **`Adversarial self-review / flaws found`** — không được bỏ vì test xanh.
3. **Nhắc lại `PENDING-REVIEW` sau MỖI update.** Hoãn ≠ waive.
4. **Chỉ commit/push khi Cường yêu cầu.**
5. Bất biến deterministic: **exact-repeat**. Regression stochastic: **≥5 seed**. Phân phối/hiệu chỉnh:
   **≥30 seed**. So biến thể-vs-biến thể: **≥100 seed** ghép cặp.
6. Chưa reproduce hoặc chưa chứng minh root cause ⇒ ghi **`UNRESOLVED`**, không ghi "fixed".
