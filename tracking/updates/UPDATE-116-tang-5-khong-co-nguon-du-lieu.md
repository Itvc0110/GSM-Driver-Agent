# UPDATE-116 — tầng 5 có hàm gộp nhưng KHÔNG có nguồn dữ liệu (`D-M3-13`)

Ngày: 2026-08-01 · Trạng thái: `DONE-CODE` · Hướng: **fix lỗi** (chỉ đạo Cường 2026-07-31)

## Bối cảnh — tôi đi nối một thứ và phát hiện nó chưa từng chạy

Acceptance `D-M3-04` (sửa hôm nay theo 5 lỗ UPDATE-114) có một dòng: *"nối
`health_guardrail(actor_ids=…)` vào `aggregate_health_guardrail` — cơ chế đã có nhưng đường chạy
thì chưa"*. Khi mở code ra nối, tôi thấy vấn đề lớn hơn hẳn.

## Đo được, không suy luận (seed 5011, `pilot_dongda`, arm A thật)

| Đo | Kết quả |
| --- | --- |
| `_system_metrics` — **nguồn duy nhất** của `system_a`/`system_b` — có khoá sức khoẻ? | 🔴 **KHÔNG.** `rest_min_total`, `veto_fired_n`, `work_span_p90`, `drive_min_p90`: cả 4 đều vắng |
| `sim_metrics.health_guardrail(ra)` có dữ liệu thật? | ✅ **CÓ.** `rest_min_total=3689.0`, `veto_fired_n=175` |
| `aggregate_health_guardrail([pair THẬT])` | 🔴 `verdict='TREO — sức khoẻ suy giảm'`, flags = *"tầng 5 THIẾU DỮ LIỆU"* |
| `grep health_guardrail src/ scripts/` (trừ `sim_metrics`) | chỉ `parallel.py` (hàm gộp) + `scripts/probe_rest_rails.py`. **Không dòng nào nạp nguồn** |

⇒ Tầng 5 trong đường A/B **chưa bao giờ đo được gì**. Nó fail-closed nên an toàn về **hướng**,
nhưng vô dụng về **chẩn đoán** — và tệ hơn: một verdict TREO **luôn bật** sẽ bị đọc thành nhiễu
rồi bỏ qua, đúng con đường `D-R20`. Dữ liệu thì **luôn có sẵn**; thiếu đúng một dòng merge.

**Đây là lần thứ BA trong hai ngày cùng một mẫu** — `D-R12` · UPDATE-114 lỗ (a) · lỗ này. Và
UPDATE-111 do **chính tôi** viết nói tầng 5 đã *"promote vào `parallel`"*: thực tế chỉ promote
hàm GỘP, không nối NGUỒN. Tôi đã tự mô tả một bảo đảm mình chưa nối xong.

## Fix

- `_system_metrics(result, exclude_actor, health_actor_ids=None)` merge
  `health_guardrail(result, actor_ids=health_actor_ids)`.
- `run_pair` và `run_ladder`: `touched = touched_actors(rb) or None`, áp cho **CẢ HAI** arm.
  Arm A không có event advice nên `touched_actors(ra)` luôn rỗng; tập đúng lấy từ arm B, và nhờ
  CRN thì cùng `actor_id` tồn tại hai bên ⇒ tầng 5 so **cùng một nhóm người**.
- `aggregate_health_guardrail` gộp thêm `n_actors_scope` — **khai mẫu số ra artifact**.

## Kết quả đo trên ĐƯỜNG THẬT (không phải fake của test)

`run_pair(seed=5011, positioning wait_only, coverage=all)`:

| Chỉ tiêu | Arm A | Arm B | Δ |
| --- | --- | --- | --- |
| `n_actors_scope` | 90 | 90 | cổng chấm trên **100% cohort** ⇒ nhạy |
| `rest_min_total` | 3.689,0 | 4.041,8 | **+352,8′** |
| `veto_fired_n` | 175 | 184 | +9 |
| `work_span_p90` | 388,3 | 370,5 | **−17,8′** |
| `drive_min_p90` | 314,6 | 301,2 | **−13,4′** |

verdict **OK**, flags rỗng. Đọc đúng cách: kênh vị trí `wait_only` làm tài xế **nghỉ nhiều hơn**
và **làm việc ít căng hơn**. Ba số này báo ở **cột sức khoẻ riêng**, không quy ra VND (ranh giới
3 của khung §1.2b).

## Files

- **SỬA** `src/gsm_sim/parallel.py` — `_system_metrics` (+tham số, +merge nguồn) · `run_pair` ·
  `run_ladder` · `aggregate_health_guardrail` (+`n_actors_scope`)
- **TẠO** `tests/test_health_source_wired.py` — **8 test**
- **SỬA** `src/gsm_sim/parallel.py` — thêm `SCOPE_KEYS` (mẫu số tách khỏi chỉ tiêu một chiều)

## Kiểm chứng

- 8 test: **5 đỏ trước** (đỏ vì đúng lý do: thiếu 9 khoá sức khoẻ + `health_actor_ids` chưa tồn
  tại), xanh sau. Test thứ 6 (`n_actors_scope`) viết sau khi tôi tự bắt mình đọc sai — xem dưới.
- Đo trên **đường thật** (`run_pair`), không chỉ trên fixture: bảng số ở trên.
- Test tầng 5 hiện có không vỡ: `test_health_gate_touched` + `test_rest_rails_guardrail` +
  `test_control_arm_gate` + file mới = **25 xanh** (rồi 8/8 sau khi thêm 2 test `SCOPE_KEYS`).
- Full suite **CẢ HAI lệnh**: `uv run pytest -q` → **925 passed / 4 skipped / 0 failed**
  (19:47) · `uv run pytest -q ui/backend/tests` → **65 passed**. Tổng **990**. Khớp kiểm đếm:
  917 (sau UPDATE-115) + 8 test mới = 925. **0 đỏ.** Đáng chú ý: 13 khoá tầng 5 nay chảy vào
  `out["system"]` của `compare()` mà **không test nào vỡ** — tức không có test nào pin số lượng
  khoá system, nên việc thêm chỉ tiêu vào artifact không có cổng nào canh. Ghi nhận, không sửa
  trong cycle này (một cổng "đếm khoá" dễ thành cổng phiền hơn là cổng hữu ích).

## Adversarial self-review / flaws found

- 🔴 **Tôi suýt báo một lỗi KHÔNG tồn tại.** Sau khi nối, tôi đọc `a_mean['n_actors_scope']` ra
  `None` và kết luận *"touched_actors trả rỗng ⇒ vẫn chấm toàn cohort ⇒ lỗi họ (a) lần thứ TƯ"*.
  Sai: `_mean` chỉ gộp 12 khoá liệt kê, `n_actors_scope` không nằm trong đó nên `.get` trả
  `None`. Đo trực tiếp cho thấy `touched_actors(rb)` = **90/90 actor**, đúng như vòng soi đã đo.
  Đây là **cùng loại lỗi với lần tôi báo số sai cho Cường**, chỉ khác chiều: lần này là *thấy lỗi
  ở nơi không có*. Thứ cứu tình huống vẫn là **đo thay vì suy luận từ một giá trị `None`**.
- Nhưng phát hiện sai đó dẫn tới một fix thật: `n_actors_scope` **đáng phải có trong artifact**.
  verdict `OK` trên 90/90 và trên 9/90 đọc giống nhau mà nghĩa khác hẳn — ca sau là cổng canh
  nhiễu. Thiếu mẫu số thì người đọc không có cách nào phân biệt.
- **Fake mỏng làm test đỏ SAI lý do 3 lượt liên tiếp** (`seed`, `grid`, `AttributeError` ở
  `summarize`). `_system_metrics` đi qua `summarize`/`system_guardrail`/`_cohort_metrics` nên phải
  dựng từ **một run thật rồi cắt về 2 actor**. Ghi lại vì mỗi lượt vá fake là một lượt tôi tưởng
  mình đang đọc tín hiệu của cổng.
- ✅ **ĐÃ ĐÓNG, không để thành nợ** (hai mục bản nháp này định defer, kiểm ra rẻ nên làm luôn):
  - `n_actors_scope` **đúng là** không nằm trong `HEALTH_KEYS_ONE_WAY` ⇒ sẽ bị gắn `significant`
    như một chỉ tiêu hai chiều. Vô hại về số (Δ luôn 0 vì hai arm cùng tập actor) nhưng **sai
    ngữ nghĩa**: một MẪU SỐ hiện ra như *"kết quả không đáng kể"* — đúng loại nhầm lẫn của lỗ
    (e), khác nguyên nhân. Sửa bằng tập **riêng** `SCOPE_KEYS` (không nhập vào
    `HEALTH_KEYS_ONE_WAY`, vì hai tập chặn `significant` vì **hai lý do khác nhau**) + nhãn
    `role = "MẪU SỐ …"`. 2 test, gồm một đối chứng canh cổng một chiều không bị hỏng theo.
  - `grep -rl health_guardrail research/audit/` = **0 file**. Không artifact nào từng mang tầng
    5 ⇒ **không có verdict TREO vô nghĩa nào đã lưu**, không cần dán nhãn hồi tố. Đây cũng là
    bằng chứng độc lập thứ hai cho kết luận chính: tầng 5 chưa bao giờ tới artifact.

## Visual review

`NOT_APPLICABLE` — không đổi dashboard/replay. Đổi **nội dung artifact A/B** (thêm 13 khoá tầng 5
+ mẫu số), nhưng đây là dữ liệu chẩn đoán trong JSON, chưa có panel nào render nó.

## PENDING-REVIEW (nhắc lại theo yêu cầu Cường)

**19 mục đang chờ Cường check**: V-01…V-14, V-16, V-17, V-18 (kèm card im lặng), V-20, V-21.
Hoãn ≠ waive. Chi tiết: `tracking/PENDING-REVIEW.md`.
