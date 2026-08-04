# UPDATE-136 — CYCLE NỢ: ranh giới khuyên mềm nay phủ **cả ba** đường ghi

Ngày: **2026-08-03** · Người: Cường (agent) · Trạng thái: **DONE-CODE** · Chờ verdict: **`V-26`**

⚠ Đánh số **129** (không phải 123): Khánh đã dùng **121–127** trong PR #4. Xem §6 về va chạm.

## 1. Vì sao có cycle này

`UPDATE-135` dựng ranh giới **KHUYÊN MỀM KHÔNG ĐO** và tuyên bố nó được thi hành bằng máy. Hai vòng
soi đa tác tử cho thấy tuyên bố đó **đúng một phần**. Cường đồng ý gộp các nợ thành một cycle.

Sáu nợ, và **bốn cái cùng một họ duy nhất** — thứ repo đã trả giá 5 lần và cycle trước lại mắc thêm:

> **ranh giới được khai là kín, nhưng chỉ phủ một phần đường chạy.**

Có **ba** đường ghi vào event log: **UI** (`routers/advice.py`) · **sim** (`world.py` → `channel=`) ·
**pipeline** (`episode_store.py`). UPDATE-135 chỉ bịt đường UI (validator 422). Cycle này bịt hai
đường còn lại, và **chuyển chỗ enforce từ đường GHI sang đường ĐỌC** — vì chỉ đường đọc mới phủ được
cả ba producer lẫn dữ liệu cũ.

## 2. Sáu nợ → sáu thay đổi

| Nợ | Lỗ | Sửa |
| --- | --- | --- |
| **N9** | `adherence_view` **fail-OPEN với topic chưa khai** (`is_soft("unknown")` = `False` ⇒ vào thẳng nhóm ĐƯỢC ĐO) | tiêu chí loại đổi sang `classify(...) != "measured"`, áp cả hai vòng |
| **N1** | `episode_store` **không ghi `topic`** ⇒ mọi quyết định pipeline mặc định ĐƯỢC ĐO | nâng `advice_spec.action_type` → `payload["topic"]`; khai `online` vào registry |
| **N5** | cú loại là **IM LẶNG** — `adherence_flags` không thể thấy một khoá VẮNG | `adherence_drops()` mới (đếm theo lý do) + **TREO** khi `unknown`/`mixed` |
| **N3** | scanner regex quét **3 file**, mù với `channel=<biến>` | AST, quét **91 file**, và **KHAI** vùng mù thay vì im lặng bỏ sót |
| **N4** | không cổng nào canh việc **THU HẸP** registry | bảng `SOFT_MONG_DOI` **viết cứng**, không suy từ registry |
| **N6** | test chỉ assert **HTTP 200** | assert event **thật sự vào store** + `reason_code` |

**N9 + N1 + N5 là một chuỗi nhân quả**, không phải ba việc rời: N1 tạo ra topic chưa khai · N9 quyết
định xử chúng thế nào · N5 làm việc xử đó **nhìn thấy được**. Sửa lẻ cái nào cũng là nửa việc.

### Hai chốt thiết kế dễ đọc sai

**`None` VẪN được đo — có chủ ý.** `None` = *"producer cũ không có khái niệm topic"* (đường sim
không đặt `channel`); `unknown` = *"producer CÓ đặt tên, chưa ai phân loại"*. Gộp hai cái sẽ vứt dữ
liệu sim hợp lệ. Cái thứ hai mới là tín hiệu ai đó vừa thêm gì.

**`drops["soft"]` KHÔNG gắn cờ.** Khuyên mềm bị loại là ranh giới chạy **đúng**, không phải bất
thường. Gắn cờ nó sẽ dạy người đọc bỏ qua cờ — cách nhanh nhất giết một cổng.

**TREO chứ không phải cờ đỏ** (Cường chốt 2026-08-03): mẫu số không đầy đủ thì mọi Δ đáng ngờ —
nguyên tắc `D-M3-10`. Không chọn "chỉ cờ" vì repo có lịch sử **cảnh báo bị bỏ qua**: `D-M3-01` sống
qua **39 artifact** vì không ai chặn.

## 3. Kiểm chứng

**Suite:** `961 → 971 passed / 4 skipped` (19′43″) · `ui/backend/tests` **115** (không đổi).
Tổng **1.086**. Delta **+10** đúng bằng số test mới của registry ⇒ **behavior-neutral đo được**:
`adherence_view` + `adherence_flags` + `episode_store` đều đổi mà **không test sim nào đổi kết quả**.

Đếm test của 4 file cổng — **lệnh, không ghi tay** (bài học UPDATE-135: số stale 3 lần):

```bash
uv run pytest -q --collect-only tests/test_advice_topic_registry.py \
  tests/test_env_loader_inline_comment.py \
  ui/backend/tests/test_soft_advice_no_trace.py \
  ui/backend/tests/test_osrm_endpoints_wired.py | grep -cE '^(tests|ui)/'
```

### 🔴 SEVER-RESTORE THẬT — và lượt đầu chỉ 2/6

Bốn bước bắt buộc (UPDATE-135 §5c): *tiêm file nguồn thật · chạy `pytest` thật · restore · verify
`sha256`*. Kết quả cuối: **6/6 mũi bị bắt**, `git grep MUTANT` = 0.

Nhưng lượt đầu **2/6**, và **bốn cái không bắt đều do PHÉP THỬ của tôi hỏng, không phải cổng hỏng** —
đúng sự phân biệt tôi vừa hứa ở UPDATE-135 sẽ luôn làm:

| Mũi | Vì sao lượt đầu vô nghĩa |
| --- | --- |
| (a) | Tôi tiêm **một** trong hai dòng `_soft_dids`, nhưng dòng kia **và** vòng event đều còn `!= "measured"` ⇒ hai dòng **dư thừa** cho ca đó. Sever một dòng không sever được *hành vi*. → tiêm thẳng `classify` |
| (c) | Anchor nhiều dòng nối bằng `\n` — file **CRLF**. Bẫy này cắn tôi **lần thứ ba** trong hai cycle |
| (d) | Tôi tiêm vào **chính dòng assert của test** — sửa test cho xanh thì nó xanh. Mũi đúng: làm **scanner mù lại** như bản regex cũ, để cổng đối chứng hai chiều bắn |
| (f) | Anchor không duy nhất (`with AdviceEventLog(...)` xuất hiện 3 lần) |

Sau khi sửa: **5/6**. Cái còn lại — `(c)` N1 — là **gap thật**: tôi sửa `episode_store` mà **quên viết
cổng**. Viết xong ⇒ **6/6**. **Không chạy sever thật thì tôi đã báo "đã sửa N1" với một fix không ai
canh** — lần refactor sau nó biến mất không ai biết.

### Hai chỗ scanner bắt oan, đã thu hẹp

Bản AST đầu bắt `{"channel": "all (accept_lift + …)"}` ở `routers/sim.py` — đó là **nhãn hiển thị**
của response A/B, không phải topic vòng đời. Và nó gắn cờ cả `.get("topic")` lẫn `body.topic`.

Quy tắc chốt: dict chỉ lấy khoá `topic`; và chỉ `ast.Name` mới là vùng mù thật — **một biến có thể
trỏ tới hằng chuỗi mới**, còn `.get()` là **đọc lại** giá trị đã có, không đặt tên mới. *Một cổng hay
bắt oan sẽ bị người ta tắt.*

## 4. Adversarial self-review / flaws found

- **Cổng mới có tự chứng minh đỏ được không:** có, 6/6 bằng pytest thật (§3).
- **Có cổng nào bắt oan không:** có 2, đã thu hẹp trước khi commit (§3).
- **Fix nào không có cổng:** N1 — sever bắt được, đã bổ sung `test_N1_*`.
- **Đổi hình dạng API công khai:** `adherence_flags` thêm tham số `drops` **có mặc định `None`** ⇒
  caller cũ không vỡ; `adherence_audit` thêm khoá `drops` (cộng thêm, không phá).
- **`adherence_view` KHÔNG đổi hình dạng trả về** — nó có 2 consumer thật
  (`sim_metrics.adherence_audit`, `scripts/probe_adherence_truth.py`); mọi thông tin mới đi qua hàm
  RIÊNG `adherence_drops()`.
- **Vùng mù còn lại (khai, không giấu):** scanner không phân giải được biến — 3 chỗ đã khai trong
  `KHONG_QUYET_DUOC` kèm lý do; nếu một biến nào đó về sau mang tên mới thì scanner **không** thấy,
  nhưng tầng đọc fail-closed + TREO sẽ bắt lúc đo.
- **Chưa làm:** `Nợ 7` (cổng `cards.js` cần jsdom/node — quyết định hạ tầng) · hợp nhất taxonomy
  `action_type` ↔ `MEASURED_TOPICS` (→ `DEFERRED`, là điều kiện để hai đường đo join được).

## 5. Visual status

**`NOT_APPLICABLE`** — không đổi UI nào. B6 chỉ sửa test; `cards.js`/`app.js` không đụng trong cycle
này. Ghi rõ lý do thay vì ghi REVIEWED.

## 6. 🔴 VA CHẠM VỚI PR #4 CỦA KHÁNH — chưa hợp nhất

Phát hiện khi `git fetch` trước lúc đặt số: Khánh đã merge PR #4 (7 commit, 69 file, +6.693 dòng) và
**độc lập sửa đúng hai lỗi cycle trước của tôi vừa sửa**:

| Chỗ | Khánh | Tôi | Đánh giá |
| --- | --- | --- | --- |
| `reason_code` enum thiếu 4 mã ĐA-04 | thêm đúng 4 mã | thêm 4 mã + `no_soft_producer` | **không xung đột** — hợp nhất là lấy HỢP. Hai người độc lập tìm ra cùng một drift là **bằng chứng tốt**, không phải trùng lặp phí |
| nhánh im lặng thiếu `scenario_id`/`seed`/`data_mode` | viết thẳng 3 field, seed từ `mockdata.manifest()` | hàm chung `advisor.provenance()` | cùng kết quả — **đã đo: cả hai nguồn seed = 7000** |
| **`topic: Literal["brief","nudge","recap"]`** | siết ở pydantic | `classify()` theo registry | 🔴 **XUNG ĐỘT THIẾT KẾ** |

**Vì sao cái thứ ba là xung đột thật:** ý định của Khánh đúng (chặn rác sớm), nhưng `Literal` ba giá
trị làm **đường ray khuyên mềm không thể chạm tới** — `GET /advice?topic=weather` bị 422 ở tầng
pydantic, nên cờ `is_soft_advice`, nhánh `no_soft_producer`, và toàn bộ ranh giới Cường duyệt sáng
nay **không bao giờ đi tới được**. Nó cũng chặn `positioning`/`accept_lift`/`shift_extend` — 5 chỗ
trong `test_lifecycle_actions.py` mà tôi vừa đổi sang topic thật.

**Cường chốt hướng hợp nhất (2026-08-03): lớp hai tầng — giữ `Literal` của Khánh nhưng lấy danh sách
từ registry.** Khi thi công thì lộ ra kết quả **tốt hơn cả hai bản gốc**, và nó bắt đầu từ việc đọc
kỹ docstring test của Khánh: *"V1 chỉ nhận ba legacy surface; **safety priority không do client
khai**"*.

🔴 **Câu đó chính là phản biện đúng cho lỗ `F1` của tôi.** `F1` (soi độc lập, UPDATE-135) là *"cờ đạo
đức suy từ query param do CLIENT chọn"* — một GET đủ dán nhãn "khuyên mềm" lên thẻ kinh tế. Tôi vá
bằng cách **trả im lặng** khi client hỏi topic mềm, tức **vẫn để client khai**. Khánh **bỏ hẳn quyền
khai đó**. Vá gốc, không vá triệu chứng.

⇒ Hợp nhất thành **HAI bề mặt khác nhau**, và sự khác nhau có lý do:

| | Bề mặt | Vì sao |
| --- | --- | --- |
| **GET** (`TopicGet`) | `brief · nudge · recap` | Client hỏi *loại thẻ*; **SERVER** quyết nội dung và tính mềm |
| **POST** (`TopicPost`) | + `weather · rest_nudge · traffic` | Client báo hành động trên thẻ **server đã đưa** — thẻ đó có thể mềm. Chặn ở pydantic thì `dismissed` (nút Ẩn) bất khả ⇒ **phá đúng điều Cường chốt** (*"giữ nút ẩn"*), và làm cổng 422 của tôi đỏ **vì lý do khác** cái nó tuyên bố (bẫy `D-M3-17`) |

**Hệ quả: hai nhánh của tôi thành CODE CHẾT và đã bị xoá** — `classify(topic)=="unknown"` → 422, và
`if soft:` → `no_soft_producer`. Pydantic chặn trước cả hai. Xoá luôn mã `no_soft_producer` khỏi
`advice.json`: giữ một `reason_code` **không có đường phát** chính là mẫu *"khai mà không có đường
chạy"* mà cycle này đi bịt. 5 test của tôi viết lại theo bề mặt mới; test ngân sách **lấy bản của
Khánh** (kênh sim không có việc gì trên HTTP API).

**Numbering:** `origin/main` có **HAI file UPDATE-121** và **HAI mục V-25** — va chạm có sẵn. Khánh đã
tự phân biệt V-25 bằng số UPDATE; tôi theo đúng quy ước đó và **không đổi tên gì của Khánh**. Việc
của tôi: `122 → 128`, cycle này `129`, mục review `V-26`.

### 6b. Kết quả sau hợp nhất — và ba test ĐỎ **có sẵn** trên main

`ui/backend/tests` **131 passed**. Suite chính: **1.011 passed / 4 skipped / 3 failed**.

**Ba lỗi đó KHÔNG do cycle này** — chứng minh bằng chạy cùng một lệnh trên `origin/main` sạch
(worktree tách rời): cả ba đỏ ở **cả hai** cây.

| Test | Nguyên nhân |
| --- | --- |
| `test_shadow_comparator_ignores_only_diagnostic_metadata` · `test_run_once_wires_shadow_trace_...` | `from scripts.compare_checkpoint_shadow import …` — **`scripts/` không có `__init__.py`** |
| `test_safety_topic_presents_even_while_driving` | `cadence.evaluate` trả `QUEUE` thay vì `PRESENT` — file cycle này không đụng |

⚠ **Hai lỗi đầu XANH khi chạy `python -m pytest` và ĐỎ khi chạy `uv run pytest`** — vì `python -m`
thêm CWD vào `sys.path`. Đúng họ lỗi cả phiên này đi bịt: *lệnh chạy khác nhau cho kết quả khác nhau,
và không ai thấy vì không ai chạy cả hai*. Đây cũng chính là lý do `CLAUDE.md` bắt chạy **cả hai**
lệnh pytest.

🔴 **Tôi suýt kết luận NGƯỢC.** Lần so đầu tiên tôi chạy worktree bằng `python -m pytest` còn cây
chính bằng `uv run pytest`, rồi đọc ra *"xanh trên main, đỏ ở cây tôi ⇒ lỗi do tôi"*. Phép so không
đồng nhất. Đây là lần thứ tư trong phiên tôi suýt quy kết nhân quả từ một quan sát lệch — và cả bốn
lần cứu được đều nhờ **đo lại cho đối xứng**, không nhờ nghĩ kỹ hơn.

**Không tự sửa ba test đó** (quy ước: không sửa code PR owner). Đã ghi `PENDING-REVIEW` để báo Khánh
kèm cách tái lập chính xác.

---

⏸ **PENDING-REVIEW: 24 mục** — `V-26` (ranh giới khuyên mềm; phần (b) luật quyết định D-M3-04 đã
ĐÓNG, còn (a) chờ Cường đọc văn bản) · `V-25` · `V-24` · V-01…V-23.
