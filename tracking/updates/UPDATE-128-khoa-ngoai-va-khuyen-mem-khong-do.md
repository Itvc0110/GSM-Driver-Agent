# UPDATE-128 — Khoá ngoài kiểm bằng GỌI THẬT + ranh giới "KHUYÊN MỀM KHÔNG ĐO"

Ngày: **2026-08-03** · Người: Cường (agent) · Trạng thái: **DONE-CODE** · Chờ verdict: **`V-26`**

## 1. Vì sao có cycle này

Chỉ thị Cường 2026-08-03, ba việc:

1. Kiểm `OSRM_BASE_URL` có cần đổi ở end của Cường không (Khánh bôi đen vì rate limit); nạp
   `GRAPHHOPPER_API_KEY`; **kiểm các khoá còn lại còn hoạt động không**.
2. *"tôi duyệt D-M3-04, việc khuyên nghỉ nên defer thành khuyên mềm, không cho vào để đo hiệu quả
   trong sim, trong UI cũng không nên có trace đồng ý làm theo hay không làm theo khi gợi ý — tương
   tự đối với thời tiết, Khánh đang lo phần đó"*.
3. *"nhưng làm docs note lại, kiểm tra mọi docs liên quan và cập nhật"*.

Hai điểm agent **không tự đoán**, đã hỏi lại và Cường chốt cùng ngày:

| Điểm mờ | Cường chốt |
| --- | --- |
| `D-M3-04` **chính là** phép A/B đo Δ tiền của `rest_window`; "duyệt nó" và "không đo khuyên nghỉ" chỉ hai hướng ngược nhau | *"thử D-M3-04 trước, nếu có ý nghĩa thì giữ, không thì revert và khuyên mềm"* |
| Bỏ trace đồng ý/không đồng ý thì cơ chế im lặng trong pha (ĐA-04, đã duyệt) xử lý sao? | *"Giữ nút ẩn, bỏ nút Làm theo"* |

## 2. Files bị ảnh hưởng

**Tạo:**

| File | Vai trò |
| --- | --- |
| `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md` | Văn bản quyết định (QĐ-1/2 vô điều kiện · QĐ-3 có điều kiện) |
| `src/gsm_core/lifecycle/advice_topics.py` | Registry `MEASURED_TOPICS` / `SOFT_TOPICS` + `classify()` fail-closed |
| `tests/test_advice_topic_registry.py` | Cổng đường ĐỌC — topic mềm không có mẫu số |
| `ui/backend/tests/test_soft_advice_no_trace.py` | Cổng đường GHI (422) + cờ server + contract mọi nhánh |
| `ui/backend/tests/test_osrm_endpoints_wired.py` | Cổng `OSRM_BASE_URL` + tên miền + nhãn `source` |
| `tests/test_env_loader_inline_comment.py` | Cổng chú thích inline của `.env` (F2) |

🔴 **CỐ Ý KHÔNG ghi số test từng file ở đây.** Tôi đã ghi rồi ghi sai **ba lần liên tiếp** trong cùng
một cycle: đầu tiên `11/11/7`, sửa thành `15/25/8`, và soi độc lập đo lại vẫn lệch (`soft_advice`
thành **29** trong lúc tôi đang sửa những chỗ khác). Nguyên nhân không phải bất cẩn một lần — nó là
**cấu trúc**: con số nằm trong prose ở 5 chỗ khác nhau, mỗi lần thêm một test là 5 chỗ cùng stale, và
không gì buộc chúng đồng bộ.

⇒ Cách chữa không phải "cẩn thận hơn" mà là **bỏ con số khỏi prose** và để lại **lệnh đếm**:

```bash
uv run pytest -q --collect-only tests/test_advice_topic_registry.py \
  tests/test_env_loader_inline_comment.py \
  ui/backend/tests/test_soft_advice_no_trace.py \
  ui/backend/tests/test_osrm_endpoints_wired.py | grep -cE '^(tests|ui)/'
```

Đo 2026-08-03 (một lần, có mốc thời gian): **63** test trên 4 file (15 · 11 · 29 · 8). Nếu con số này
lệch lúc bạn đọc thì **lệnh trên là đúng, dòng này là sai** — đó là toàn bộ ý của việc để lệnh lại.
Cùng họ với `+6.016đ`: một con số đúng lúc viết, sai lúc đọc, không ai đếm lại.

**Sửa:**

| File | Đổi gì |
| --- | --- |
| `.env` (gitignored) | +`GRAPHHOPPER_API_KEY` · comment giải thích `OSRM_BASE_URL` không điều khiển routing · nhãn CHẾT cho `GOOGLE_MAPS_API_KEY` |
| `.env.example` | Mô tả 3 tầng nay ĐÚNG · cảnh báo hai mirror cùng IP · cảnh báo `.env` gitignore nên khoá không tự sang đồng đội · `UPDATE-119`→`120` |
| `ui/backend/app/routers/routing.py` | `osrm_endpoints()` mới đọc `OSRM_BASE_URL`; xoá mirror sai tên miền; nhãn `source` phân biệt 2 mirror |
| `src/gsm_core/lifecycle/projections.py` | `adherence_view` loại topic mềm ở **CẢ HAI** vòng |
| `ui/backend/app/routers/advice.py` | `model_validator` từ chối `followed` cho topic mềm (422) |
| `ui/web/js/cards.js` | Chế độ render thứ ba `soft` (nút **Ẩn**, không "Làm theo"); **đọc cờ `is_soft_advice` của server**, không tự tra danh sách |
| `ui/web/index.html` | Khối "Nhật ký làm-theo" khai ngoại lệ có chủ ý cho khuyên mềm |
| `ui/contracts/advice_action.json` | v1.1: **thêm `topic`** (contract drift — API nhận từ ĐA-04 mà contract không khai) + ranh giới khuyên mềm |
| `ui/contracts/advice.json` | +`topic` +`is_soft_advice` (server trả lời, client không suy) |
| `specs/advisor-objective-model-v2.md` | **§1.2c MỚI** — tầng thứ ba của tỷ giá |
| `specs/adherence-measurement.md` | **BỔ SUNG 2026-08-03** — có lớp lời khuyên câu trả lời đúng là *không đo* |
| `specs/simulation/d-m3-04-multiday-prereg-locked.json` | **+`luat_quyet_dinh`** (ghi TRƯỚC khi đo) |
| `specs/simulation/d-m3-04-multiday-ab-brief.md` | Trạng thái: PHÉP THỬ CÓ ĐIỀU KIỆN + đèn xanh |
| `specs/simulation/e11-plan-nghi-co-gia-tri.md`, `e11-fatigue-world-brief.md` | Khung cảnh báo: E11 **mất trụ V1** |
| `tracking/{TODO,DEFERRED,PENDING-REVIEW,PROJECT-GRAPH,BOOTSTRAP-SESSION}.md` | Trạng thái + bẫy #12 + `V-26` + `D-M3-19` |

## 3. Chi tiết — (a) khoá ngoài

Kiểm bằng **gọi HTTP thật** từng khoá, không đọc code. 9/9 xong:

| Khoá / endpoint | Kết quả |
| --- | --- |
| `router.project-osrm.org` (gạch NGANG) | **HTTP 200 `code:"Ok"`** ✅ |
| `router.project.osrm.org` (dấu CHẤM — **code đang viết thế**) | ❌ **`CERTIFICATE_VERIFY_FAILED: Hostname mismatch`** |
| `routing.openstreetmap.de` | **HTTP 200 `code:"Ok"`** ✅ |
| `GRAPHHOPPER_API_KEY` | **thiếu ở `.env`**; khoá Cường cấp → **HTTP 200, tuyến thật** ✅ |
| `WEATHER_API_KEY` | **200** — Hà Nội `localtime 2026-08-03 11:05` ✅ |
| `JINA_API_KEY` · `STADIA_MAPS_API_KEY` · `OPENROUTER_API_KEY` · `OPENAI_API_KEY` · `LANGFUSE` | **200** cả 5 ✅ |
| `GOOGLE_MAPS_API_KEY` | ❌ **`REQUEST_DENIED "The provided API key is invalid"`**; 64 hex (không `AIza…`); **0 code đọc** |

**Trả lời câu Cường hỏi:** giữ `OSRM_BASE_URL=https://router.project-osrm.org` là **đúng, không cần
đổi**. Nhưng trước cycle này nó **không phải** thứ điều khiển routing của driver-app — người đọc nó
duy nhất là `scripts/fetch_osrm_matrix.py`. Sau cycle này biến **có người đọc thật**.

Và **đổi mirror không chữa được rate limit**: `router.project-osrm.org` cùng `routing.openstreetmap.de`
**cùng phân giải về `5.148.170.168`** (cùng hạ tầng FOSSGIS) ⇒ cùng một hạn mức. Thứ thật sự đỡ là
**tầng 2 GraphHopper** (vừa nạp) + cache.

Đo lại 3 tầng sau khi sửa (gọi thật, 2 điểm Đống Đa):

```
tầng 1  openstreetmap_de_osrm_real        2,4 km · 4′
tầng 2  graphhopper_real                  2,4 km · 5′     ← trước cycle này: None (chết lặng)
tầng 3  fallback_straight_line_estimate   1,4 km · 4′  route_is_real_road=False
```

Tầng 1 và 2 khớp nhau 2,4 km — một phép đối chứng chéo tốt. Tầng 3 ngắn hơn 1,7× đúng như kỳ vọng
của đường thẳng, và nó khai `route_is_real_road=False`.

**Lỗi thứ tư tự tìm được khi sửa:** nhãn `source` gắn cứng `openstreetmap_de_osrm_real` cho **cả
hai** mirror ⇒ mirror thứ hai trả lời thì nhãn **nói sai nguồn**. Cùng họ lỗi mà `UPDATE-120` vừa
sửa ở tầng 3 (`hanoi_street_graph_engine` cho một đồ thị không tồn tại). Đã tách thành
`project_osrm_real`.

## 4. Chi tiết — (b) ranh giới KHUYÊN MỀM

**Lỗ được bịt.** `specs/advisor-objective-model-v2.md` §1.2b chặn tỷ giá sức-khoẻ↔tiền ở **tầng
objective** (`C2` huỷ) và **tầng world** (không mô hình hoá hậu quả mệt). Cả hai **không nói gì** về
việc *sản phẩm đếm mức nghe lời*. Nên tỷ giá bị chặn ở sim vẫn mọc lại được ở UI — bằng một trường
trong event log, im lặng, và **không cổng nào bắt**.

Cơ chế cụ thể: một khi `rest_adherence` tồn tại như **một con số trong bảng**, nó sẽ bị nhìn như thứ
cần cải thiện — và *"cải thiện tỷ lệ tài xế chịu nghỉ"* là tối ưu hoá **trên** sức khoẻ.

**Hai vai của `dismissed`** — phần dễ hỏng nhất, nên tách rõ trong mọi tài liệu:

| Vai | Nghĩa | Khuyên mềm |
| --- | --- | --- |
| Nhịp nói (ĐA-04) | *"đừng nhắc nữa trong pha này"* | ✅ GIỮ |
| Thước adherence | *"tài xế KHÔNG đồng ý"* | 🚫 CẤM |

`followed` bị cấm thẳng — nó **chỉ có một nghĩa**, và nghĩa đó là vai 2.

**Vì sao *vắng khoá* chứ không phải `None`:** `None` là tín hiệu *"mẫu số 0 — có thể có bug"*, đúng
thứ `D-M3-01`/`L4-01` đã dùng để tìm ra thước hỏng. Nếu khuyên mềm trả `None` thì nó lẫn vào tín
hiệu báo lỗi, và người sau sẽ đi "sửa" một ranh giới đang chạy đúng.

**`D-M3-04` thành phép thử có điều kiện.** Câu *"nếu có ý nghĩa thì giữ"* đã được dịch thành tiêu
chí máy chấm được và ghi vào prereg **trước khi đo** (khoá `luat_quyet_dinh`):

- **GIỮ** ⟺ Δ payout ngày 1..2 dương **SIG** + tầng 5 không suy giảm + 0 STOP-A..D;
- **REVERT → khuyên mềm** ⟺ Δ ≤ 0, hoặc ns, hoặc STOP bắn.

⚠ Prereg đã khoá **2026-08-01** kỳ vọng **Δ ≤ 0** (world β=0) ⇒ **REVERT là nhánh dự đoán trước**.
Nếu nó xảy ra thì phép đo **thành công**, không phải kênh thất bại.

## 5. Kiểm chứng

| Việc | Kết quả |
| --- | --- |
| Khoá ngoài | **9/9 gọi thật** (§3); 3 tầng routing đo lại sau khi sửa |
| `uv run pytest -q ui/backend/tests` | **115 passed / 0 skipped** (nền trước cycle: 78) |
| `uv run pytest -q tests/test_advice_topic_registry.py` | **15 passed** (13 + 2 test của F3) |
| `uv run pytest -q tests/test_env_loader_inline_comment.py` | **11 passed** (cổng MỚI cho F2; **đỏ 3/11 trước khi sửa**) |
| `uv run pytest -q` (suite chính) | **961 passed / 4 skipped / 0 failed** (20′19″) — xem §5b |
| **Tổng suite (CẢ HAI lệnh)** | **1.076** = 961 + 115. Trước cycle: 1.013 = 935 + 78 ⇒ **+63 test** |
| Prereg JSON | parse lại OK; `STOP_conditions`/`cam_vinh_vien` vẫn ở cấp 1 (tôi lồng sai một lần, tự bắt bằng parse) |
| 🔴 **SEVER-RESTORE — ĐỌC §5c, BẢN GHI CŨ ĐÃ KHAI QUÁ** | **8/8 mũi bị bắt bởi `pytest` THẬT** (đo lại 2026-08-03 sau khi soi độc lập bác bằng chứng cũ). Chi tiết + vì sao ba dòng "2/2 · 4/4 · 3/3" cũ **không đứng được**: §5c |
| Đối chứng ngược | topic **được đo** vẫn có mẫu số (`decided=1`, `decision_adherence=1.0`); `followed` cho `nudge` vẫn **200**; endpoint trả `is_soft_advice=False` cho `nudge`/`brief` — cổng không chặn cả kênh kinh tế cho tiện |

**Chưa kiểm chứng — nói rõ:**

- **`cards.js` chỉ kiểm bằng ĐỌC NGUỒN**, không có test hành vi (repo không có test runner JS). Yếu
  hơn hẳn các cổng Python. Ghi ở đây thay vì để người đọc tưởng nó mạnh hơn. **Nay đỡ hơn một bậc**:
  phần *quyết định* (topic nào là mềm) đã chuyển sang server và **có** test hành vi so hai bên; chỉ
  phần *render* còn dựa vào đọc nguồn.
- **Flutter (`ui/driver_app/`) chưa kiểm** — claim đang hoạt động của Khánh. Nếu app đó thêm thẻ mềm
  thì boundary 422 chặn được `followed`, nhưng **nút vẫn có thể được vẽ** ⇒ tài xế bấm và thấy lỗi.
  → `SOFT-ADVICE-02`.
- **Cổng fail-closed chỉ quét 3 file** (`world.py`, `projections.py`, `advice.py`) bằng regex. Topic
  sinh động (ghép chuỗi runtime) thì nó không thấy. Cùng vùng mù với 3 cổng tĩnh của UPDATE-118.
- **`OSRM_BASE_URL` không có cổng "phải phân giải được"** — cổng kiểm chuỗi URL, **không gọi mạng**.
  Cố ý: test phụ thuộc mạng là test giả xanh/giả đỏ. Hệ quả: một tên miền sai **kiểu khác** (không
  khớp mẫu `project.osrm`) vẫn lọt.

### 5b. Suite chính — và một chuyện về quy trình phải ghi lại

**`961 passed / 4 skipped / 0 failed`** (20′19″) — đo trên code **sau khi sửa 4 lỗi của vòng soi**.
Tổng cả hai lệnh: **1.076** (961 + 115); trước cycle là 1.013 (935 + 78) ⇒ **+63 test**.

⚠ Con số `ui/backend/tests` trong file này đã stale **ba lần** (101 → 108 → 111 → thật **115**) vì tôi
sửa test rồi không đo lại. Xem khung ở §2 về vì sao cách chữa là **bỏ số khỏi prose, để lại lệnh**.

Hai lượt đo, mỗi lượt delta khớp đúng dự đoán — đó là cách kiểm rằng không có gì đổi ngoài ý muốn:

| Lượt | Kết quả | Delta | Khớp với |
| --- | --- | --- | --- |
| sau thân cycle | 948 / 4 skip (26′08″) | **+13** vs 935 | đúng 13 test `test_advice_topic_registry.py` |
| sau sửa vòng soi 1 | 961 / 4 skip (20′07″) | **+13** vs 948 | 11 test `test_env_loader_inline_comment.py` + 2 test F3 |
| **sau sever THẬT + sửa vòng soi 2** | **961 / 4 skip (19′53″)** | **0** vs 961 | **dự đoán trước là 0** — mọi thay đổi lượt này nằm trong `ui/` (không được `testpaths` thu) và `sever_THAT.py` restore byte-identical có verify `sha256` |

🔒 **Lượt thứ ba là lượt tôi tin.** Hai lượt đầu đo *trước* khi `sever_THAT.py` chạm `src/`. Dù nó
restore có verify hash, tôi vẫn đo lại — vì cả cycle này là bài học về việc **đừng tuyên bố mạnh hơn
bằng chứng**, và "đã restore nên chắc không đổi" là một suy luận, không phải một phép đo. Delta 0
được **dự đoán trước rồi mới đo**, nên nó là một phép kiểm chứ không phải một quan sát tiện lợi.
Kèm hai đối chứng cây: `git grep MUTANT` rỗng và `git diff --stat -- src tests` chỉ hiện **2 file tôi
cố ý sửa** (`llm_client.py`, `projections.py`).

⚠ Ghi lại một vết nhỏ: `git` cảnh báo `LF will be replaced by CRLF` ở `llm_client.py` — edit của tôi
chèn dòng LF vào một file CRLF. Vô hại (git normalize khi commit) nhưng đáng biết, vì **CRLF đã cắn
tôi hai lần trong chính cycle này**: một lần làm mũi sever (c) không tiêm được, và trước đó là bẫy
`awk`/hash đã ghi ở `BOOTSTRAP` §5.

**Kỳ vọng đã được xác nhận:** `projections.adherence_view` bị sửa **hai lần** (lọc topic mềm, rồi neo
`_soft_dids` vào cả event) nhưng **không test sim nào đổi kết quả** — vì không kênh sim nào dùng topic
mềm, nên bộ lọc là **no-op trên dữ liệu sim**. Đây là bằng chứng behavior-neutral mạnh hơn suy luận:
961 test bao gồm toàn bộ test adherence/sim, và chúng giữ nguyên qua cả hai lượt sửa.

Kèm **bằng chứng cấu trúc** (kiểm bằng `grep`, không bằng lập luận): `projections` chỉ được import ở
`sim_metrics.py:498` (trong một hàm ĐO) và `episode_store.py` (`decision_state`). **`world.py` không
import nó** ⇒ đường quyết định của sim không hề chạm tới thay đổi này ⇒ fingerprint per-actor không thể
đổi. Vì thế tôi **không** chạy lại fingerprint 15/15 — và nói rõ ở đây là một lựa chọn có lý do, không
phải một bước bị bỏ.

🔴 **Suite xanh = chạy CẢ HAI lệnh** (`pyproject.toml` có `testpaths=["tests"]` nên lệnh từ root bỏ
**115** test đường sản phẩm — `D-M3-09`).

⚠ **Chuyện quy trình đã trả giá ~15 phút máy, ghi lại để khỏi lặp:** tôi khởi động suite ở nền **rồi
mới** sửa `projections.py` (thêm `_soft_dids`). pytest import module lúc collection, nên bản đang chạy
đo **code cũ** ⇒ kết quả của nó vô giá trị và phải chạy lại từ đầu. Khi `TaskStop` nó thì đúng bẫy đã
ghi ở §5: **để lại python con** (dọn tay 1 tiến trình). ⇒ **Quy tắc: chỉ khởi động suite khi đã ngừng
sửa file mà nó thu.** Vùng an toàn để làm song song là `ui/` — `testpaths=["tests"]` nên sửa ở đó không
làm kết quả stale (chính vì vậy phần "một nguồn sự thật" ở §7 mới làm được song song).

### 5c. 🔴 BẰNG CHỨNG SEVER-RESTORE CŨ KHÔNG ĐỨNG ĐƯỢC — tôi đã khai quá, và đây là bản đúng

Soi độc lập 2026-08-03 (lăng kính "tái lập") bác **bằng chứng**, không bác **kết luận**. Họ đúng, và
đây là finding đắt nhất cả vòng vì nó nói về **độ trung thực của bản ghi**, không về một dòng code.

**Ba dòng cũ ("2/2 · 4/4 · 3/3 mũi bắn") dựa trên 4 script mà KHÔNG script nào chạy `pytest`** —
`grep -c pytest` trên cả bốn = **0**. Cụ thể chúng làm gì:

| Script | Thực tế nó làm | Vấn đề |
| --- | --- | --- |
| `sever_osrm.py` | **chép lại tay** hai assert (`if not any(...)`, `re.search(...)`) | đo bản chép, không đo cổng |
| `sever_soft.py` mũi 4 | `"_khuyen_mem_khong_nhan_followed" in src` | **KHÔNG TIÊM GÌ** — không bao giờ đỏ được, mà tôi vẫn đếm vào "4/4" |
| `sever_single_source.py` | dựng **chuỗi JS GIẢ** rồi chạy regex do chính script viết | không chạm `cards.js` thật |
| `sever_hardened.py` | tự định nghĩa `khong_dedupe()` mới — **không bao giờ** bỏ `dict.fromkeys` khỏi `routing.py` | severs một hàm tưởng tượng |

⇒ **Bản ghi mạnh hơn bằng chứng.** Đúng thứ repo trừng phạt, và tôi tự làm — trong cùng cycle mà tôi
dựng cổng để chặn nó ở người khác.

**Đã làm lại cho đúng** (`scratchpad/sever_THAT.py`): backup → **tiêm vào file NGUỒN THẬT** → chạy
**`pytest` THẬT** trên file test thật → restore → verify `sha256`. Kết quả:

| Mũi | Tiêm gì | Kết quả |
| --- | --- | --- |
| (a) | `projections.is_soft` → luôn `False` | **ĐỎ** `1 failed` |
| (b) | bỏ validator chặn `followed` cho topic mềm | **ĐỎ** `1 failed` |
| (c) | nhãn `source` về lại kiểu so CHUỖI có scheme | **ĐỎ** `1 failed, 5 passed` |
| (d) | bỏ `dict.fromkeys` (dedupe URL) | **ĐỎ** `1 failed, 4 passed` |
| (e) | bỏ cắt chú thích inline trong `load_env` | **ĐỎ** `1 failed, 2 passed` |
| (f) | **bỏ `isSoft` khỏi phép tính `mode` trong `cards.js`** | **ĐỎ** `1 failed, 27 passed` — *nhưng xem dưới* |
| (g) | bỏ fail-closed cho topic lạ (GET) | **ĐỎ** `1 failed, 17 passed` |
| (h) | nhánh soft trả lại thẻ KINH TẾ | **ĐỎ** `1 failed, 14 passed` |

**8/8 mũi bị bắt**, `git grep MUTANT` = **0** sau restore.

🔴 **Mũi (f) là chỗ soi độc lập ĐÚNG và tôi phải sửa code test.** Lượt sever thật ĐẦU TIÊN cho
`XANH — KHÔNG BẮT`: **29/29 test xanh** khi thẻ mềm đã hiện lại nút "Làm theo". Vì cổng cũ chỉ đòi ba
**chuỗi tồn tại ở đâu đó** trong file, mà cả ba vẫn còn sau mutation (ở tham số hàm, ở nhánh render,
ở `logAction`). *Đòi "chuỗi tồn tại" không bao giờ chặn được "chuỗi bị bỏ khỏi ĐÚNG một biểu thức".*
Đã neo lại vào **chính biểu thức `const mode = …`**; sau đó mũi (f) mới ĐỎ.

⚠ **Mũi (c) lần đầu KHÔNG TIÊM ĐƯỢC** vì tôi neo hai dòng nối bằng `\n` trong khi file là **CRLF** —
đúng bẫy đã ghi ở `BOOTSTRAP` §5. Nếu tôi không đọc kỹ output thì `7/8` sẽ bị đọc thành *"một cổng
không bắn"* trong khi sự thật là *"phép thử của tôi hỏng"*. **Hai lỗi đó rất khác nhau.**

**Bài học rút ra, đắt nhất của cả cycle:** một script sever *"chạy được và in ĐỎ"* **không** chứng
minh cổng bắn — nó chỉ chứng minh cái script tự viết ra thì đỏ. Chứng minh thật cần đúng bốn bước:
**tiêm vào file thật · chạy runner thật · restore · verify hash**. Ba trong bốn script cũ của tôi
thiếu ít nhất hai bước, và cái thứ tư thiếu cả bốn.

## 6. Docs đã cập nhật kèm theo

`SCOPE` **không đổi** (không mở/đóng feature nào). `TODO` +4 mục (`SOFT-ADVICE-01/02`, `D-ENV-01/02`)
và sửa dòng `D-M3-04`. `DEFERRED` +`D-M3-19`. `PENDING-REVIEW` +`V-26`. `PROJECT-GRAPH` +node
UPDATE-128, **và sửa một lỗi đánh số còn sót từ lần rebase với Khánh**: nhãn `UPDATE-120` trỏ file
`UPDATE-121-*`. `BOOTSTRAP-SESSION` §1 (ranh giới +tầng ba) · §2 (24 mục PENDING) · §3 hàng 4
(D-M3-04) · **§5 bẫy #12 MỚI** · §"Vừa xong".

## 6b. 🔴 SOI ĐỘC LẬP ĐA TÁC TỬ — và nó bắt được lỗi THẬT trong chính cycle này

Cường yêu cầu review song song (2026-08-03). Chạy **11 tác tử / 3 pha**: 5 chiều soi độc lập → mỗi
chiều một người **phản biện** (nhiệm vụ: BÁC BỎ) → tổng hợp. Thu **44 finding**, **16 sống sót**.

⚠ **PHỦ SÓT — phải nói trước khi nói kết quả:** **3/9 tác tử lỗi API** (`ENOTFOUND` /
connection-closed). Hệ quả cụ thể:

| Chiều | Tình trạng |
| --- | --- |
| code ranh giới mềm · code routing | ✅ soi **và** phản biện đầy đủ |
| **số liệu** (truy nguyên từng con số, gọi lại 9 khoá) | ❌ **KHÔNG CHẠY** — chiều này chưa được phủ chút nào |
| docs-vs-code · chất lượng cổng | ⚠ soi xong (12 + 12 finding) nhưng **người phản biện lỗi** ⇒ findings **CHƯA qua phản biện** |

⇒ Với hai chiều `⚠`, tôi **tự kiểm bằng đo** 4 claim đếm được và **cả 4 đều ĐÚNG** (xem §7). Nhưng
phần còn lại của hai chiều đó, và **toàn bộ** chiều số liệu, vẫn là **vùng chưa phủ** — không được
đọc UPDATE này như "đã soi xong".

**`bi_bac_bo = 0`** — không finding nào bị bác. Nhưng người phản biện **có** làm việc: họ **hạ độ
lớn** (một finding từ `CHẶN-COMMIT` → `CAO`) kèm bằng chứng, đúng bẫy #7 (*"đúng cơ chế, sai độ
lớn"*). Ví dụ họ bác bốn lập luận thổi phồng: *"store append-only ⇒ không gỡ được"* là **sai**
(mỗi event giữ `payload.topic` riêng, projection replay được); *"test là tautology"* là **phóng
đại** (cổng vẫn bắt được router giữ danh sách thứ hai).

### Bốn lỗi THẬT đã sửa trong cycle này (chi tiết ở §7)

| # | Lỗi | Mức |
| --- | --- | --- |
| **F1** | `is_soft_advice` suy từ **query param client chọn**, không từ nội dung thẻ ⇒ `GET ?topic=weather` trả thẻ **KINH TẾ** (`bonus_gap`, *"Còn với được mốc thưởng 30.000đ"*) mà gắn nhãn mềm, và `adherence_view` = `{}` ⇒ **một GET là đủ xoá một lời khuyên kinh tế khỏi bảng đo** | **CAO** |
| **F2** | `load_env` không cắt chú thích inline ⇒ copy `.env.example` → `.env` cho **giá trị RÁC**; chuỗi chú thích **truthy** nên **vượt qua** guard `if not api_key` ⇒ gọi GraphHopper thật với khoá rác | **CAO** |
| **F3** | Vòng decision chỉ kiểm topic đã giải ⇒ `decided[nudge]` + `followed[rest_nudge]` cùng `decision_id` cho `decision_adherence = 1.0` ⇒ `followed` **mềm** vào **tử số** topic được đo | TRUNG |
| **F4** | Nhãn `source` nói **sai xuất xứ** khi so chuỗi có scheme (`OSRM_BASE_URL=https://routing.openstreetmap.de/...` ⇒ nhãn `project_osrm_real`) | TRUNG |

## 7. Adversarial self-review / flaws found

**Tự bắt được trong cycle:**

1. 🔴 **Tôi lồng `STOP_conditions` vào trong block mới ⇒ JSON hỏng.** Bắt được vì parse lại thay vì
   tin edit thành công. Nếu không parse thì prereg — file *khoá* của một phép đo — sẽ nằm trên repo ở
   dạng không đọc được, và lỗi chỉ lộ ra lúc chạy Cycle B.
2. 🔴 **Nhãn `source` nói sai nguồn** khi mirror thứ hai trả lời (§3). Tôi vào sửa tên miền và **suýt
   để nguyên nhãn** — đúng họ lỗi Khánh vừa dọn ở tầng 3 của cùng file, trong cùng ngày.
3. **Contract `advice_action.json` thiếu hẳn `topic`** dù API nhận từ ĐA-04 ⇒ contract drift có sẵn,
   phát hiện khi đi thêm ranh giới. Đã vá lên v1.1.
4. **Lọc một vòng là chưa đủ.** Bản đầu tôi chỉ lọc vòng decision. Mũi tiêm 2 của sever-restore cho
   thấy event `followed` **không kèm `decided`** vẫn lọt qua vòng event ⇒ topic mềm vẫn có mặt trong
   view. Đúng họ `L4-01` (hai tên cho *"advisor đã nói"*, sửa một nửa rồi tưởng xong).
5. **Bẫy escaping của shell** làm regex sever script nổ (`\o` bad escape) và tôi **suýt đọc thành
   "cổng không bắn"**. Dời sang file script rồi mới có kết quả đúng. Cùng họ bẫy đã ghi ở §5 (so hash
   bằng `awk` trên CRLF).

**Đã double-check theo `CLAUDE.md` §4b:**

- **Cờ config có thực sự được dùng:** đây là chủ đề của cả nửa (a) — `OSRM_BASE_URL` nay có người đọc,
  có cổng canh.
- **Disabled factor về baseline:** topic **được đo** không đổi hành vi gì (đối chứng ngược xanh).
- 🔴 **UI đọc canonical source hay tự recompute — TÔI ĐÃ LÀM SAI, RỒI SỬA TRONG CÙNG CYCLE.** Bản đầu
  `cards.js` **chép** danh sách `SOFT_TOPICS` sang JS. Tôi ban đầu ghi nó là "nợ chấp nhận được vì
  không có build step chia sẻ hằng giữa Python và JS thuần" — **lý lẽ đó không đứng được**: đây đúng
  là nguồn sự thật thứ hai cho một **ranh giới đạo đức**, và `D-M3-17` (cycle ngay trước) đã trả giá
  cho chính mẫu đó — UI tự tính tầm pin bằng công thức riêng, lệch engine **1,76×**, và **1.000 test
  không thấy vì không test nào so hai bên**. Cụ thể hậu quả nếu để nguyên: thêm topic mềm mà quên sửa
  JS ⇒ thẻ đó **vẫn vẽ nút "Làm theo"**.
  **Đã sửa:** `GET /advice` nay trả **`is_soft_advice`** (+ vọng lại `topic`); `cards.js` **bỏ hẳn**
  danh sách và chỉ đọc cờ của server; registry `advice_topics.py` là nguồn DUY NHẤT. Kèm 6 test mới
  trong `test_soft_advice_no_trace.py`, gồm một cổng **chặn tái phát** (`cards.js` chép lại danh sách
  ⇒ ĐỎ) và một cổng **so hai bên** (cờ của endpoint phải khớp registry, không phải một danh sách thứ
  hai ở tầng router). Contract `ui/contracts/advice.json` += 2 field.
  **Bài học tôi tự rút:** *"không có cơ chế chia sẻ nên chấp nhận trùng lặp"* là đúng cái lý lẽ dẫn
  tới `D-M3-17`. Cách ra khỏi nó không phải build step — mà là **để một bên TRẢ LỜI thay vì cả hai
  cùng suy**.
- **Future leak / CRN / random stream:** không chạm. Thay đổi thuần ở đường ĐO và đường mạng.
- **Nhãn MOCK/PROXY:** không mất (`is_mock` nguyên; `route_is_real_road` nguyên).
- **Seed/scenario nào làm kết luận đảo chiều:** không có kết luận số nào trong cycle này.

**Flaw đã map vào TODO/DEFERRED:** `D-M3-19` (E11 mất trụ V1) · `SOFT-ADVICE-02` (Flutter) ·
`D-ENV-02` (khoá Google chết).

### 7b. Bốn lỗi do SOI ĐỘC LẬP bắt — đã sửa, kèm bài học

**F1 — cờ đạo đức dán lên thẻ nó không mô tả (CAO).** Tái lập được: `GET /advice?topic=weather` trả
`is_soft_advice=True` **cùng với** một thẻ `bonus_gap` *"Còn với được mốc thưởng 30.000đ hôm nay"*, và
`adherence_view` = `{}`. Nguyên nhân: `topic` là **query param do client chọn** còn
`advisor.advice()` **không nhận `topic`** ⇒ *"một nguồn sự thật"* chỉ áp cho **phân loại topic**, chưa
buộc vào **nội dung thẻ**. Người phản biện còn đo thêm một hệ quả tôi chưa thấy: **thứ tự request**
quyết định phép đo (hai GET cùng `now_min`, đổi thứ tự `weather`/`nudge` cho hai kết quả khác nhau).
**Sửa:** `topic` phải nằm trong registry (fail-closed ở **runtime**, cả GET và POST) + topic mềm ⇒
**im lặng** `no_soft_producer` thay vì gắn nhãn mềm lên thẻ kinh tế. Trung thực với hiện trạng: đường
ray đã có, **nguồn** sinh khuyên mềm thì chưa.
*Bài học:* tôi kiểm *"nhãn khớp registry"* mà **không** kiểm *"nhãn khớp nội dung"* — hai câu khác
nhau, và tôi đã tự nhận là đã đóng D-M3-17 bằng câu thứ nhất.

**F2 — chú thích cảnh báo lại tạo ra một cách chết lặng lẽ MỚI (CAO).** `load_env` chỉ
`split("=",1)` + `strip()`, không cắt chú thích inline. Copy `.env.example` → `.env` (đúng lời dặn
dòng 1 của chính file đó) cho `GRAPHHOPPER_API_KEY = '# graphhopper.com Directions API…'` — **truthy**
⇒ **vượt qua** guard `if not api_key` ⇒ gọi thật với khoá rác. Người phản biện tìm biến thể **thường
gặp hơn**: người dùng gõ khoá ngay sau `=` và giữ chú thích ⇒ khoá gửi đi là `'abc123   # …'`.
**Sửa:** `_strip_inline_comment` (tôn trọng dấu nháy, không phá giá trị chứa `#` hợp lệ) + cổng
`tests/test_env_loader_inline_comment.py` dùng **chính `.env.example` thật** làm dữ liệu thử. Cổng đó
**đỏ ngay lần đầu** và lộ thêm: **ba khoá `WEATHER`/`JINA`/`STADIA` đã mang lỗi này TRƯỚC cycle** —
bug có sẵn, chỉ chưa ai copy file mẫu nên chưa nổ.
*Bài học:* đoạn chú thích tôi thêm để **cảnh báo** *"thiếu biến này thì tier 2 chết lặng lẽ"* chính là
thứ tạo ra một cách chết lặng lẽ khác. Sửa tài liệu cũng là sửa hành vi khi tài liệu là dữ liệu.

**F3 — tầng thứ hai không chặn được hướng nó tự nhận sẽ chặn (TRUNG).** `decision_state` giải
`row["topic"]` = topic của event **đầu**, còn `row["state"]` = kết cục của event **cuối**. Nên
`decided[nudge]` + `followed[rest_nudge]` cùng `decision_id` cho `decision_adherence = 1.0`. Vòng
event đã kiểm hai hướng, **vòng decision thì chưa** ⇒ câu *"adherence_view là tầng thứ hai độc lập"*
trong docstring test của chính tôi chưa đúng ở hướng đó. **Sửa:** `_soft_dids` quét **cả event**;
đánh đổi (loại cả quyết định trộn topic ⇒ có thể mất một `decided` hợp lệ) **khai tường minh** trong
code + 2 test. Không reachable hôm nay (UI 422, sim chỉ có 5 kênh đều được đo) ⇒ **chưa có số sai**.

**F4 — nhãn `source` nói sai xuất xứ (TRUNG).** Phép so `OSRM_DE_BASE_URL in osrm_url` là so **chuỗi
có scheme**: đặt `OSRM_BASE_URL=https://routing.openstreetmap.de/routed-car` (https, mirror A viết
cứng http) ⇒ dữ liệu đến **từ openstreetmap.de** mà nhãn nói `project_osrm_real`; self-host
`localhost:5000` cũng bị khẳng định là project-OSRM. **Sửa:** `_osrm_source()` so theo **host** (không
phân biệt hoa/thường) và trả `osrm_custom_real` cho host lạ — vẫn khai *"OSRM thật"* nhưng **không
khẳng định của ai**.
*Bài học:* tôi vào file này để sửa đúng lỗi *"nhãn nói một đằng, dữ liệu một nẻo"* và **tạo lại chính
nó** ở dạng nhẹ hơn, trong cùng một hàm.

### 7c. Bốn cổng của tôi là TRANG TRÍ — soi độc lập bắt, đã làm lại

Đây là phần đáng ghi nhất, vì tôi đã tuyên bố ở §5 rằng các cổng *"tự chứng minh bắn được"*:

| Cổng | Bệnh | Đã làm gì |
| --- | --- | --- |
| `test_nhan_source_phan_biet_duoc_HAI_mirror` | chỉ **grep văn bản** file nguồn ⇒ *"thoả mãn được bằng một COMMENT"* | viết lại: gọi thật `try_osrm` với `urlopen` giả, kiểm nhãn ứng với mirror **thực sự trả lời** — và **chính nó phát hiện F4** |
| `test_khong_goi_HAI_LAN_cung_mot_server` | **RỖNG** — hai mirror không bao giờ trùng chuỗi ở ca mặc định ⇒ xanh cả khi xoá `dict.fromkeys` | kiểm đúng ca gây trùng (env = mirror A) + đối chứng ca mặc định phải có 2 |
| `test_cards_js_doc_CO_cua_server` | xanh kể cả khi `cards.js` **không còn** chỗ nào đọc `a.is_soft_advice`, vì đoạn **chú thích** giải thích cờ đó đã chứa chuỗi ấy — đúng bẫy #2 | bỏ comment trước khi quét; đòi có **isSoft** truyền vào đường render; và quét mọi cách chép danh sách, không chỉ `new Set([…])` |
| 3 file test mới | **ghi vào `data/ui-telemetry` THẬT** ⇒ trên store bẩn, nhịp nói có thể NÉN mọi GET ⇒ assert đi qua **nhánh im lặng** và không chứng minh gì | fixture `autouse` cô lập `TELEMETRY_DIR`, cùng khuôn `_patch` của test cũ |

**Và fail-closed vừa bắt việc thật ngay khi bật:** 3 test cũ đỏ vì dùng **topic bịa** (`topic-0…`,
`rest`) để lấy namespace phân biệt. Đó không phải cớ để nới cổng — tôi đổi chúng sang **topic THẬT**
(`brief`/`nudge`/`recap`/`positioning`/`accept_lift`/`shift_extend`), tức các test đó nay chứng minh
việc đếm ngân sách đúng trên **từ vựng topic thật** thay vì ba chuỗi không bao giờ tồn tại. **Cố ý
KHÔNG khai `rest`** vào registry: nhắc nghỉ ở sản phẩm phải dùng đúng một tên (`rest_nudge`), và để
`rest` ở trạng thái chưa phân loại thì ai dùng nó sẽ nhận 422 và **buộc phải quyết định**.

### 7c-bis. Vòng soi SỐ LIỆU (chạy lại sau khi tác tử đầu lỗi) — bắt thêm 3 lỗi, 2 đã sửa

**(a) Ba con số test trong §2 SAI (11/11/7 · thật 15/25/8) và bảng thiếu hẳn file thứ tư.** Nguyên
nhân: tôi ghi lúc mới tạo file rồi **không đếm lại** khi thêm test theo vòng soi. Đã sửa bằng
`pytest --collect-only`. Cùng họ `+6.016đ`: một con số đúng lúc viết, sai lúc đọc, không ai đếm lại.
`TODO.md` ghi "22 tests" cũng sai (thật **59** trên 4 file) — đã sửa.

**(b) `reason_code` của contract thiếu CẢ 5 mã router thật phát ra** — xem §7c-ter. Đây là finding
đắt nhất của toàn vòng soi.

**(c) IP trong docstring không tái lập được** — đã tự đính chính trước khi vòng soi trả kết quả
(3 lần đo cho 3 giá trị khác nhau vì đó là tên miền đỗ, IP xoay).

⚠ **Người phản biện của chiều số liệu LỖI HAI LẦN** (`ENOTFOUND`) ⇒ 7 finding của chiều này **chưa
qua phản biện đối kháng**. Tôi tự kiểm 4 claim đếm được (đúng cả 4) nhưng **không** có vòng phản biện
độc lập cho chúng — với bẫy #7 (~1/4 finding của soi độc lập sai hoặc phóng đại), đó là **vùng chưa
phủ phải khai**, không phải chi tiết bỏ qua được.

### 7c-ter. Cổng mới TỰ BẮT hai lỗi contract, một cái có sẵn nhiều tháng

Tôi viết `test_MOI_nhanh_cua_GET_advice_deu_KHOP_contract` — validate **mọi nhánh** của `GET /advice`
bằng chính schema trong repo. Nó **đỏ ngay, hai lần liền**:

1. **Thiếu `scenario_id`/`seed`/`data_mode`.** `git show HEAD:` chứng minh vi phạm **có từ trước
   cycle** (nhánh im lặng ở HEAD cũng thiếu) — tôi **lan truyền** nó vào nhánh khuyên mềm mới, không
   tạo ra. Sửa bằng `advisor.provenance()` dùng **chung** với adapter, không chép ba chuỗi sang
   router (chép là dựng nguồn sự thật thứ hai — họ `D-M3-17`, cycle này đã trả giá hai lần).
2. 🔴 **`reason_code` có enum, và enum thiếu CẢ 5 mã router phát ra.** Bốn mã nhịp nói của ĐA-04
   (`dismissed_for_window`/`shift_budget_exhausted`/`topic_cooldown`/`unsafe_while_moving`) **chưa
   từng được khai** kể từ UPDATE-099 — tức **mọi response im lặng của đường sản phẩm đã vi phạm
   contract của chính nó, im lặng, nhiều tháng**; enum chỉ chứa 5 mã của *adapter*. Cộng
   `no_soft_producer` mà chính cycle này thêm. ⇒ Cycle này **sửa đúng file `advice.json`** mà vẫn
   ship một `reason_code` vi phạm chính schema đó — đúng họ lỗi "docs-vs-code" nó tuyên bố đang sửa.

**Vì sao không test nào bắt:** `test_advice_matches_contract_all_hours` chỉ quét 3 giờ trên store
sạch (đều ra nhánh PRESENT), còn `test_advice_car_fleet_is_silent_not_wrong` rơi vào nhánh im lặng
của **ADVISOR** — nhánh đó đi qua `advisor.advice()` nên CÓ đủ 3 field ⇒ nó xanh và **không phủ hai
nhánh early-return của router**. Cổng cũ đúng nhưng đứng sai chỗ.

### 7c-quater. Store dev đã bị bản nháp của tôi làm bẩn

Đo được trong `data/ui-telemetry/advice_lifecycle.db` (**gitignored**, mock dev):

| Bản ghi | Số lượng | Vấn đề |
| --- | --- | --- |
| `('rest_nudge', 'followed')` | 1 | **vi phạm chính ranh giới cycle này dựng** |
| topic `khong_khai_bao` / `topic_bay_dat_ra` | 3 | topic chưa phân loại — code hiện tại sẽ **422**, tức store chứa bản ghi mà code không còn sinh được |

**Không sinh ra số sai** — vì ranh giới enforce ở đường **ĐỌC** (`adherence_view` lọc topic mềm), nên
bản ghi đó đã bị vô hiệu tại chỗ đọc. Fixture nay cô lập đúng (kiểm bằng md5: chạy test không đổi
một byte nào), nên **không tái phát**.

🔴 **ĐÍNH CHÍNH của chính tôi — tôi đã nói SAI một lần ở đây.** Bản đầu mục này viết *"đường ĐỌC đã
vô hiệu hoá chúng"*. **Đúng với topic MỀM, SAI với topic CHƯA KHAI.** Đo lại trên DB bẩn: 99 event
(44 được đo · **52 mềm** · **3 chưa khai**); `adherence_view` loại sạch 52 event mềm, nhưng **1 khoá
`khong_khai_bao` VẪN lọt vào view** — vì `is_soft("unknown")` trả `False` ⇒ topic lạ được xếp vào
nhóm **ĐƯỢC ĐO**.

⇒ Đường đọc **fail-OPEN với topic chưa khai**, trong khi tôi đã khai nó là fail-closed. Hôm nay vô
hại (khoá đó chỉ có `suppressed: 1`, adherence `None`, không sinh tỷ lệ nào), **nhưng** một topic lạ
có `decided`+`followed` thì **sẽ** sinh ra một tỷ lệ. Boundary 422 chặn topic lạ MỚI, không chặn được
bản ghi CŨ, đường sim, và đường pipeline (`Nợ 1`). → **`Nợ 9`**, gộp vào cycle nợ.

**Tôi tự bắt được điều này đúng lúc đi kiểm để giải thích cho Cường quyết** — tức nếu chỉ đọc lại
ghi chép của mình thì tôi đã trình bày một bảo đảm không tồn tại.

**QUYẾT ĐỊNH CƯỜNG 2026-08-03: dựng lại DB.** Đã xoá `advice_lifecycle.db` + `advice_actions.jsonl`
+ `a.jsonl`, sao lưu ra scratchpad trước (bảo hiểm, không phải để giữ làm ca thử). Kiểm sau khi xoá:
`GET /actions` trên DB VẮNG trả `200 {"actions": []}` (không nổ), POST tạo lại store, GET đọc lại ra
đúng 1 bản ghi **mang `topic` + `is_soft_advice`** — tức Nợ 2 chạy thật trên đường sản phẩm.

**Vì sao xoá KHÔNG phá append-only:** append-only nói *không được sửa/xoá TỪNG bản ghi* (để projection
replay ra đúng kết quả). Vứt cả một store **dữ liệu rác của môi trường dev** rồi dựng lại là chuyện
khác — đây là mock gitignored, không phải telemetry thật. Ranh giới đó phải nói rõ, vì nếu lẫn thì
lần sau ai đó sẽ xoá một event vì nó làm số xấu.

⚠ Một dấu vết lộ ra khi dọn: file **`a.jsonl` nằm trong thư mục telemetry THẬT** — mà `a.jsonl` đúng
là tên fixture `_patch` dùng dưới `tmp_path`. Tức đã từng có test (phiên nào đó trước) chạy **không
qua fixture**.

🔴 **Nhưng tôi đã suýt viết một kết luận SAI từ dấu vết này, và tự bắt được bằng bisect — ghi lại vì
nó là bài học lặp lại của chính cycle:**

Sau khi xoá store, tôi chạy `pytest ui/backend/tests`, thấy `advice_lifecycle.db` +
`advice_actions.jsonl` **xuất hiện lại**, và kết luận *"test vẫn rò ra store thật"*. Sai. Hai file đó
do **chính lệnh probe của tôi** tạo ra ở bước ngay trước (tôi POST thật để kiểm store dựng lại được).
Tôi **không kiểm file có sẵn từ trước hay không** — thấy file sau khi chạy test rồi quy cho test.

Bisect bác nó dứt điểm: chạy **từng file** → 0 rò; chạy **cả bộ** trên thư mục sạch → **0 rò**. Suite
hiện tại **không** rò ra store thật.

**Bài học:** đây đúng là mẫu *"thấy X sau khi làm Y nên Y gây ra X"* — cùng họ với bẫy #7 (đúng cơ
chế, sai quy kết). Cái cứu tình huống là **bisect**, một lệnh; cái suýt làm hỏng là **viết kết luận
từ một lần quan sát**. Trong cùng cycle này tôi đã mắc nó ba lần theo ba cách khác nhau: khai quá
bằng chứng sever, đếm số bằng ký ức, và lần này là quy kết nhân quả sai.

⇒ `Nợ 6` **giữ nguyên phạm vi cũ** (test chỉ assert HTTP 200, không assert event vào store) — **không**
mở rộng thành "rà rò rỉ toàn bộ test cũ", vì rò rỉ đó không tái lập được.

### 7d. Còn nợ từ vòng soi — CHƯA sửa, ghi rõ thay vì im

| Nợ | Mức | Vì sao chưa sửa |
| --- | --- | --- |
| `episode_store` (origin=pipeline) **không bao giờ ghi `topic`** ⇒ mọi quyết định pipeline nằm trong nhóm được đo theo mặc định | TRUNG | Đường pipeline chưa có kênh mềm nào; sửa cần quyết định taxonomy cho pipeline → gộp `SOFT-ADVICE-02` |
| `GET /advice/actions` **không trả `topic`** ⇒ khối *"Nhật ký làm-theo"* vừa hứa phân biệt khuyên mềm thì không có dữ liệu để phân biệt | TRUNG | Chạm contract đọc + UI; tách khỏi cycle này |
| Cổng fail-closed chỉ quét **3 file `.py`** bằng regex; idiom `channel=<biến>` đang dùng ở 2/7 chỗ nên scanner không thấy | TRUNG | Cùng vùng mù với 3 cổng tĩnh UPDATE-118; cần AST thay regex |
| `card_kind` pattern `^(brief\|nudge\|recap)$` — thẻ thời tiết thật sẽ là `nudge`, dùng được, nhưng taxonomy hai trục (`card_kind` × `topic`) chưa được khai ở đâu | THẤP | Thuộc `ĐA-06 AdviceEnvelopeV2` |
| Xoá riêng `"traffic"` khỏi `SOFT_TOPICS` là **im lặng hoàn toàn** — nó thành `unknown` rồi bị 422 ở boundary, nhưng không cổng nào canh việc *thu hẹp* registry. Vòng soi đo thêm: **mọi** cổng đều `parametrize`/loop trên **chính `SOFT_TOPICS`** ⇒ chuyển `traffic` sang `MEASURED_TOPICS` làm **5 test case biến mất ÂM THẦM**, suite vẫn xanh | TRUNG (nâng từ THẤP) | Cần một bảng kỳ vọng **viết cứng** (không suy từ registry) — tự tham chiếu là lý do các cổng này không thấy việc thu hẹp |
| Hai cổng `test_cards_js_*` đo **TỪ VỰNG** chứ không đo **HÀNH VI**: vòng soi tiêm lỗi bỏ `isSoft` khỏi phép tính `mode` ⇒ thẻ mềm hiện lại nút "Làm theo" mà cổng **vẫn xanh** | TRUNG | Repo không có test runner JS. Fix thật cần chạy `cards.js` (jsdom/node) — một quyết định hạ tầng, không phải một dòng |
| `test_khuyen_mem_VAN_nhan_dismissed` chỉ assert **HTTP 200**, không assert event ĐÃ VÀO store ⇒ ai đó "đọc ranh giới là không lưu trace khuyên mềm" rồi ném cả `dismissed` thì cổng vẫn xanh 51/51 | TRUNG | Sửa được rẻ (đọc lại store trong test); chưa làm trong cycle này để không thêm thay đổi sau lượt suite cuối |
| **Cú drop của quyết định trộn topic là IM LẶNG**: `sim_metrics.adherence_flags:604` chỉ kiểm `event_decided == 0 and decided > 0` — nó **không thể thấy một khoá VẮNG**. Nếu tương lai có producer trộn topic thì mẫu số tụt mà không cảnh báo | TRUNG | Phát hiện bởi người phản biện khi **hạ** finding F2 xuống THẤP — cơ chế bị bác, nhưng tàn dư này là thật |
| ~~Store dev chứa event topic mềm + topic chưa khai~~ | ✅ **XONG** | Cường chốt **dựng lại DB** (2026-08-03); đã xoá + kiểm store tự sinh lại sạch |
| 🔴 **`Nợ 9` MỚI — `adherence_view` fail-OPEN với topic CHƯA KHAI**: `is_soft("unknown")` = `False` ⇒ topic lạ vào thẳng nhóm ĐƯỢC ĐO. Boundary 422 chỉ chặn topic lạ MỚI qua đường UI; **không** chặn bản ghi cũ, đường sim, đường pipeline | **TRUNG** | Tự bắt được khi đi kiểm để Cường quyết `Nợ 8` — tức ghi chép cũ của tôi mô tả một bảo đảm **không tồn tại**. Fix cùng họ `Nợ 1`: quyết định fail-closed ở đường ĐỌC (loại `unknown` khỏi mẫu số) và **kêu to** thay vì lặng lẽ bỏ |

## 8. Visual status

**`NOT_APPLICABLE`** — và lý do đáng ghi rõ vì nó dễ bị đọc thành lảng tránh gate:

- (a) khoá ngoài: thay đổi ở đường mạng + comment; đã đo bằng **gọi thật 3 tầng** (§3), mạnh hơn ảnh.
- (b) ranh giới khuyên mềm: `cards.js` có chế độ render mới, **nhưng không thẻ nào dùng nó hôm nay** —
  sản phẩm chỉ có `brief`/`nudge`/`recap`, không có thẻ nghỉ hay thẻ thời tiết. **Không có gì để
  xem.** Chụp một ảnh brief/nudge không đổi rồi gọi là "đã review" thì tệ hơn ghi `NOT_APPLICABLE`.
- Khi Khánh thêm thẻ thời tiết thật thì **lúc đó** mới có visual gate, và nó thuộc `SOFT-ADVICE-02`.

## 9. Follow-up

| Việc | Ai | Ghi chú |
| --- | --- | --- |
| **Cycle B: chạy `D-M3-04`** (`run_pair_multiday`, n=100, days=3) rồi áp `luat_quyet_dinh` | Cường (agent) | Cần plan riêng (`CLAUDE.md` §4b: đổi hành vi sim + thêm đường đo). ~1,5h người + ~4,2h máy |
| **Xác nhận tôi dịch đúng ý Cường** → `V-26` | Cường | Sửa tiêu chí **TRƯỚC** Cycle B; sửa sau khi thấy số là vi phạm prereg |
| Thẻ thời tiết dùng chế độ `soft` + Flutter theo QĐ-1 | **Khánh** | `SOFT-ADVICE-02` |
| Quyết `GOOGLE_MAPS_API_KEY`: xin khoá thật hay gỡ biến | Cường | `D-ENV-02` |
| `V-20` (PHAN-QUYET đảo C2 / E11) | Cường | Văn bản này **không** đóng nó, nhưng nếu `D-M3-04` REVERT thì lý do tồn tại của E11 yếu đi rõ (`D-M3-19`) |

---

⏸ **PENDING-REVIEW: 24 mục chờ Cường** — V-01…V-14 · V-16 · V-17 · V-18 · V-20 · V-21 · V-22 ·
V-23 (2 PDF) · V-24 (routing 3 tầng của Khánh) · V-25 (số tầm pin) · **V-26 (cycle này)**.
