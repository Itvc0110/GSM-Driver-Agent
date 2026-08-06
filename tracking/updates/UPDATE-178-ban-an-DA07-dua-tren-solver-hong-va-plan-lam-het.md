# UPDATE-178 — Bản án ĐA-07 **tuyên bởi một solver mù thưởng**; lan can `soc_low` **mồ côi**; và plan xếp lại theo **bán kính ảnh hưởng thật**

- **Ngày:** 2026-08-07
- **Loại:** research tìm root cause (tự kiểm, 0 dòng code đổi) + plan thi công
- **Artifact:** `research/audit/2026-08-07-root-cause-classes/00-TU-KIEM-cua-toi.md` ·
  `tracking/PLAN-2026-08-07-todo-cycle-lam-het.md`

## 1. ⭐ Bản án giết `shift_plan` dựa trên bằng chứng đã hỏng

**Đo bằng git, không suy luận:**

| việc | commit | ngày |
| --- | --- | --- |
| ĐA-07 tắt `shift_plan` trong config | `5a44cbb` | **2026-07-28** |
| E5 đo lại (`D-ĐA07-recheck`) ⇒ củng cố ĐA-07 | — | 2026-07-29 |
| sửa `points_band_size` **15 → 5** (`ADV-01`) | `bec2671` | **2026-08-06** |

Ở band 15: `shift_dp.py:207` là `pb + add_pts // PBS`; giờ thường `pph=5`, `exp_trips≈1–2,2` ⇒
`add_pts ≈ 5–11` ⇒ `add_pts // 15 = **0**` ⇒ **points_band đóng băng suốt DP** ⇒ mốc thưởng ngày
(60/100/160/200) **không bao giờ vào giá trị Bellman**. ⇒ **Cả hai vế** bằng chứng của ĐA-07 — *"không
giá trị"* (payout ns) **và** *"còn có hại"* (served −0,33đp SIG, đơn chết +4,1 SIG) — sinh ra từ một DP
**không nhìn thấy thứ nó tồn tại để tối ưu**.

**Khẳng định hẹp (KHÔNG nói S2 có giá trị):** *chưa ai đo `shift_plan` bằng solver đã sửa*, và **chưa ai
ghi nghĩa vụ đo lại**. `D-E4-01` có ghi ADV-01 trơ nhưng quy nguyên nhân cho **world zero-cost**, không
quy cho lỗi band — hai cách giải thích **cạnh tranh và tách được** (band chạm phía doanh thu, zero-cost
chạm phía chi phí).

## 2. Lan can `soc_low` **bất khả đạt**, và cổng canh nó **mù đúng ca này**

- **Cấu trúc:** `world.py:1037` chỉ vào nhánh khi `action == REST`; `behavior.py:151` đã trả `GO_SWAP`
  với **cùng ngưỡng** `swap_soc_threshold_pct` mà `world.py:1040` truyền xuống; `advice_bridge.py:890`
  kiểm lại đúng ngưỡng đó ⇒ **tập rỗng**.
- **Đo:** `veto_soc_low_n = 0,0` ở **cả hai arm, mọi nấc**, 30 seed (`2026-08-06-e1b/ladder-truoc.json`);
  `veto_fatigued_n = 55,0 = veto_fired_n` ⇒ cổng *"3 lan can"* thực tế là **1**.
- **Nguồn:** `D-M3-04-FIX` xoá hai nhánh `GO_SWAP/GO_CHARGE` (đúng — code chết) và **hệ quả chưa ai ghi**
  là lan can đi kèm thành mồ côi.
- **Vì sao cổng không bắt:** `sim_metrics.py:537` đòi `va >= RAIL_ALIVE_MIN_N and vb == 0` ⇒ bắt *"sống
  ở A, chết ở B"*, **mù** với rail **chưa từng sống**.
- **Mức độ (nói đúng, không thổi):** tính an toàn *"pin thấp thì không hoãn nghỉ"* **vẫn đúng** vì chặn ở
  thượng nguồn. Sai là **báo cáo**, không phải an toàn.
- **Khuôn sửa có sẵn:** `defer_cap` cũng trơ nhưng **có chủ ý**, có test khai-trơ + điều kiện mở lại
  (`tests/test_rest_rails_guardrail.py:58-62`). Làm y hệt cho `soc_low` + thêm cổng bắt rail chết ở **cả
  hai** arm.

## 3. Phát hiện làm **đảo thứ tự kế hoạch**: 6/6 kênh advisor đang TẮT

`configs/pilot_dongda.yaml:330-343` — `shift_plan`/`accept_lift`/`shift_extend`/`rest_window`/
`swap_early`/`station_choice` = `false`; kênh sống duy nhất **positioning**; và `B6-PARITY`: sản phẩm
chạy **1/9 solver**. ⇒ Phần lớn nợ hai ngày qua (`S2-*`, `R-*`, `D-E4-*`) có **bán kính ảnh hưởng hôm
nay = 0**. Kế hoạch xếp lại theo: **sản phẩm → kênh sống → độ tin phép đo → kênh ngủ**.

Sắc thái giữ lại: `false` là **mặc định ship**, run nghiên cứu bật qua override ⇒ lỗi trong kênh ngủ
vẫn **làm hỏng phép đo** (chính là §1) ⇒ chúng là **nợ đo lường**, không phải nợ sản phẩm.

## 4. Đính chính hồ sơ `B3` — cách phát biểu cũ **quá rộng**

Sốt ruột có **4** hiệu ứng, không phải 1. Chỉ **nới vành 1→3** là no-op (vì `_neighbors` dùng đĩa
`grid_disk` — `behavior.py:238` — còn niềm tin chỉ phủ `grid_disk(cell, **2**)` — `world.py:1165` — nên
ô vành 3 đọc `0.0`). Ba hiệu ứng kia **sống**: `bar` 1,25→1,05 · `p_move` 0,5→0,9 · `give_up` bỏ hẳn
phép so (`behavior.py:224-227`). ⇒ **Fix chỉ nới vành sẽ vẫn no-op** — phải sửa **bán kính niềm tin**
cùng lúc.

## Kiểm chứng

- §1: `git log -L` trên `DEFAULT_PARAMS` + `git log -S 'shift_plan: false'` — **hai commit + hai ngày**.
- §2: 4 điểm code đọc trực tiếp + artifact 30 seed **có sẵn trong repo** (không chạy sim mới).
- §3: đọc config trực tiếp.
- §4: đọc `behavior.py` + `world.py`.
- **Suite: không chạy** — 0 dòng code đổi. **Visual: `NOT_APPLICABLE`** (research + docs).
- **Chưa kiểm chứng:** `R-1` (chưa đo phân phối giờ đích) · `D-ADV-06` (số 16,15 pp/giờ của tôi là
  **blended** hai đội, mà `soc_cost_per_bucket` không phân biệt đội ⇒ chưa trích được) · `A2` vẫn n=5 ·
  **HHI cung theo ô** chưa đo lần nào · `S2-2` phần dư `add_pts % 5` mới là **DERIVED**.

## Adversarial self-review / flaws found

1. **§1 là phát hiện THUẬN LỢI cho luận điểm của tôi** (rằng còn việc thật phải làm) ⇒ đúng loại phải
   soi kỹ nhất. Tôi đã hạ xuống mức hẹp nhất bằng chứng đỡ được: *"chưa ai đo lại"*, **không phải**
   *"S2 có giá trị"*. Rất có thể đo lại vẫn ns — và đó cũng là kết quả tốt (ĐA-07 được củng cố bằng
   bằng chứng sạch).
2. **Tôi suýt báo `defer_cap` chết như lỗi thứ hai.** Mở nguồn ra thì nó đã được **khai trơ có chủ ý**
   kèm điều kiện mở lại. Quy tắc *"mở nguồn gốc con số trước khi nói nó sai"* cứu lần thứ **tư**.
3. **Tôi suýt báo `build_shift_plan_input` không có caller** (⇒ S2 chưa từng chạy). Sai: grep bị cắt bởi
   `head_limit`; caller thật ở `advice_bridge.py:603`. ⇒ **`head_limit` của grep là một nguồn kết luận
   sai** — với câu hỏi *"có caller nào không"* phải grep **không giới hạn** hoặc dùng `files_with_matches`.
4. **Tôi đã viết một probe rồi xoá** (đo cắt cụt điểm S2) khi nhận ra kênh đang tắt ⇒ số đó không đổi
   được quyết định nào hôm nay. Ghi lại để thấy: **§3 đã thay đổi việc tôi làm ngay trong session**,
   không phải một nhận xét trang trí.
5. `B3` — hồ sơ cũ do **chính tôi/agent** viết và nó **quá rộng**. Bài học lặp lại: *cách phát biểu sai
   dẫn tới fix sai chỗ*.
6. **Chưa có phản biện độc lập** cho §1 và §2 — 12 agent đang chạy (6 lớp nguyên nhân + 1 refuter được
   lệnh cố BÁC). Nếu §2 bị bác thì cycle C4 rút khỏi plan.

## ⏳ Nhắc PENDING-REVIEW

**Mới — cần Cường quyết:** có **mở lại ĐA-07** để đo `shift_plan` bằng solver đã sửa không (§1)? Mở lại
một quyết định đã duyệt là việc của Cường; tôi chỉ trình rằng **bằng chứng cũ đã hỏng**.
**Đang chờ:** **Q-07** (3 lựa chọn, đã có số n=100) · **V-32** (blocking) · **V-31** · K-01(b) ACK ·
D-QD4-05 · ~27 mục V- · Q-03/04/09/10/13 · **amendment ĐA-08** — gom ở
`tracking/CAN-CUONG-DUYET-2026-08-06.md`. ⏸ Khánh: 2 test đỏ + Flutter.
