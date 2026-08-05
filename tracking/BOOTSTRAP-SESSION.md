# BOOTSTRAP SESSION — prompt để nạp một AI coding agent mới vào dự án này

Cập nhật: **2026-08-01** · local HEAD = **`1d98de6`** (đã đẩy origin/main; Cường đã cho phép đẩy)

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
  mệt**, huỷ vĩnh viễn (`specs/advisor-objective-model-v2.md` §1.2b). ⚠ **Bổ sung 2026-08-03 —
  TẦNG THỨ BA**: cũng **không đo mức NGHE LỜI** của khuyên sức khoẻ. §1.2b bịt tỷ giá ở tầng
  objective và tầng world nhưng không nói gì về việc *sản phẩm đếm mức nghe lời*, nên tỷ giá mọc
  lại được ở UI — im lặng. Nay có cổng: `SOFT_TOPICS` (thời tiết · `rest_nudge` · giao thông) vắng
  khoá khỏi `adherence_view`, `followed` bị 422. Xem §1.2c +
  `tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`.
  🔴 **Bổ sung 2026-08-04 — ranh giới này có HAI CHIỀU, không chỉ một** (`D-QD4-03`, UPDATE-138).
  Suốt thời gian dài chỉ chiều *"khuyên NGHỈ"* được canh. Chiều ngược — *"khuyên CHẠY THÊM"* — có
  **0 lan can sức khoẻ** trong khi kênh nghỉ có ba, dù `policy_locks.py:40-42` **tự xếp hai cần
  gạt CÙNG HỌ** (*"kéo dài thời gian làm việc vì tiền"*). Câu §1.2c đổi dấu vẫn đúng: cải thiện
  `shift_extend_adherence` = nhiều tài xế hơn đồng ý làm dài giờ hơn. Nay `check_shift_extend` có
  `soc_low`/`fatigued`/`would_exceed_fatigue` + event `advice_extend_veto` vào guardrail tầng 5.
  **Bài học chung: khi kiểm một ranh giới, hỏi luôn "chiều ngược lại của nó được canh chưa?"**
- Mock data **phải gắn nhãn mock**. Mọi số trong repo là MOCK; **GSM sẽ không cấp thêm dữ liệu**.

---

## §2. STATE hiện tại (2026-07-30)

```
local HEAD  = cây làm việc UPDATE-140..142 CHƯA commit (Cycle B REVERT + Q-16/FIX-PRE + D-M3-04-FIX)
suite       = 1283 passed / 4 skipped / **5 FAILED** + **1 file KHÔNG THU ĐƯỢC**
              (đo 2026-08-05 SAU UPDATE-142)
              uv run pytest -q                  -> 1091 / 5 fail / 4 skip  (22-56′ tuỳ tải máy
                 ⚠ đã dài hơn hẳn vì test multiday — đừng tưởng treo)
              uv run pytest -q ui/backend/tests -> ⛔ **Interrupted: collection error**
                 phải thêm `--ignore=ui/backend/tests/test_demo_advice_ack.py` -> 192 passed
              ⚠ 2026-08-05: K-03 từng phình 4→5 mục vì `fingerprint_actors` (UPDATE-140 chuyển nó
                 từ scripts/ vào src/ ⇒ lọt tầm quét money-manifest) — ĐÃ phân loại (MONEY, có
                 chú thích trong manifest) ⇒ K-03 về đúng 4 mục CỦA KHÁNH. Bài học: chuyển hàm
                 vào src/ là ĐỔI TẦM QUÉT của cổng, phải chạy test_health_boundary sau đó
              🔴 CẢ 5 FAIL + lỗi collection đều ĐỎ SẴN trên origin/main — đã chứng minh bằng
                `git worktree add <tmp> origin/main` rồi chạy ở đó (KHÔNG có việc của tôi):
                  K-01 (3): cadence QUEUE≠PRESENT · 2× checkpoint_trace thiếu `__init__.py`
                  K-02 (1): test_demo_advice_ack.py — `from ui.backend.tests...` mà `ui` không
                            phải package ⇒ **lỗi COLLECTION, chặn CẢ suite ui/backend**.
                            `python -m pytest` XANH / `pytest` console script ĐỎ (CWD vào sys.path)
                  K-03 (2): test_money_manifest_is_complete — 4 hàm mới chạm token tiền chưa phân
                            loại (`demo_trace._driver_snapshot/_trip/build_demo_trace`,
                            `world.World.log`) · test_demo_trace_neutrality
                ⚠ K-03 là **cổng ranh giới sức khoẻ**. Nó đang làm đúng việc, nhưng đỏ thường trực
                  ⇒ mất tác dụng bắt vi phạm TIẾP THEO. Không tự phân loại giúp — phân loại sai
                  còn tệ hơn để đỏ. Chi tiết + 3 lựa chọn: `tracking/HANDOFF-KHANH-2026-08-04.md`
              🔴 3 F là ĐỎ SẴN sau PR #4 (`K-01`), KHÔNG do cycle nào của tôi — đã chứng minh bằng
                `git stash push -u` rồi chạy đúng 3 test đó trên cây sạch ⇒ vẫn 3 failed:
                  tests/test_cadence_policy.py::test_safety_topic_presents_even_while_driving
                  tests/test_checkpoint_trace.py::test_shadow_comparator_ignores_only_diagnostic_metadata
                  tests/test_checkpoint_trace.py::test_run_once_wires_shadow_trace_without_changing_semantic_outcomes
                Cái đầu là **bất đồng CHÍNH SÁCH** (code cố ý QUEUE mọi thẻ chữ khi đang lái, kể cả
                safety; test đòi PRESENT) — thuộc claim Khánh, KHÔNG tự sửa. Hai cái sau: `scripts/`
                thiếu `__init__.py`
              ⚠ ĐỪNG TIN hai số này nếu vừa có ai thêm test — ĐO LẠI. Trong UPDATE-135 con số UI
                stale BA LẦN (101→108→111→115) vì viết bằng tay rồi không đếm lại
              ⚠ chỉ khởi động suite khi ĐÃ NGỪNG sửa file nó thu — pytest import lúc collection,
                sửa sau đó ⇒ kết quả đo CODE CŨ. 2026-08-04 tôi lại sập bẫy này (sửa
                `ui/contracts/advice_v2.json` giữa chừng, mà một test trong `tests/` đọc nó lúc
                runtime) ⇒ phải HUỶ và chạy lại từ đầu, mất ~25′ máy. Lần thứ HAI
UPDATE       = 125 file (ĐẾM 2026-08-04), mới nhất UPDATE-137 (104 UIUX + 105 codex + 120 routing = remote/Khánh)
              ⚠ 125 ≠ 130 vì dãy số THIẾU vài số (013–018) và có số TRÙNG (121, 125 dùng hai lần
                do song song với remote). Đừng suy số file từ số cao nhất — đếm bằng lệnh:
                `(Get-ChildItem tracking\updates -Filter "UPDATE-*.md" | Measure-Object).Count`
                Dòng này đã sai HAI lần vì đếm bằng ký ức (2026-08-03 ghi 115; 2026-08-04 ghi 118)
PENDING      = 26 mục V- đang chờ Cường (V-15/V-19 đã ĐÓNG; V-27 mới 2026-08-04):
              V-01..V-14 (visual/data SIM + Track UI) · V-16 (fare parity gate)
              V-17 (kênh VỊ TRÍ b3/b4) · V-18 (nhịp nói advisor + card im lặng)
              V-20 (PHAN-QUYET đảo C2 — Cường đã hạ xuống THỬ NGHIỆM, chờ chốt văn bản)
              V-21 (L4-03 khe advisor nói MIỄN PHÍ — 3 lựa chọn, (a)/(b) đổi CHÍNH SÁCH)
              V-22 (xoá 300 dòng `trajectory.py` hay giữ? — module chết, bảng màu xung đột)
              V-23 (hai bản PDF Week 2 Report — brief 6 trang + kỹ thuật 30 trang)
              V-24 (routing 3 tầng của KHÁNH — OSRM→GraphHopper→đường thẳng trung thực)
              V-25 (số tầm pin trên UI ĐỔI: 77 → 43,8 km; xe hơi hiện "chưa có cơ sở")
              V-26 (ranh giới KHUYÊN MỀM KHÔNG ĐO — phần (b) luật quyết định D-M3-04 đã ĐÓNG
                    2026-08-03; CÒN LẠI chỉ (a): Cường đọc văn bản QUYET-DINH rồi xác nhận)
              V-27 (QĐ-4 — hai quyết định, KHÔNG phải xem màn hình:
                    (a) `rest` của v2 xếp MỀM hay KINH TẾ? nó gộp `rest_window` (HOÃN nghỉ,
                        được đo) với `rest_nudge` (mềm); tôi chọn MỀM vì fail-closed nhưng
                        KHÔNG chắc → `D-QD4-01`
                    (b) defer bước 3 `CheckpointStore` vào đường đo chung → `D-QD4-02`)
              ⚠ V-16/V-17 dễ bị đọc thiếu — agent đã nhiều lần chỉ đọc V-01..V-14 + V-18
              ⚠ K-01 là mục cho KHÁNH, không phải Cường — đừng gộp vào 26
```

🔴 **BẮT BUỘC: luôn chạy CẢ HAI lệnh khi nói "suite xanh".** `pyproject.toml` có
`testpaths = ["tests"]` nên `pytest -q` từ root **BỎ 115 test ở `ui/backend/tests/`** — tức bỏ đúng
test của **đường sản phẩm** (`D-M3-09`).

### Cấu hình đang chạy (đọc kỹ, dễ hiểu sai)

| Cờ | Giá trị | Nghĩa |
| --- | --- | --- |
| `advice.enabled` | **false** | Ở config mặc định **advisor im hoàn toàn**. A/B bật cờ này qua `_cfg_with` để đo |
| 4/5 kênh (`shift_plan`, `accept_lift`, `shift_extend`, `rest_window`) | **false** | Tắt theo ĐA-07 — *"không hiệu quả thì TẮT để advisor IM LẶNG"* |
| `positioning_overrides` | **`wait_only`** | Kênh **duy nhất** được duyệt bật. Chỉ ghi đè khi bản năng là ĐỨNG CHỜ |
| `advice.cadence.enabled` | **false** | Nhịp thuộc SẢN PHẨM (xem §1) |

### Vừa xong (3 cycle cuối)

- **UPDATE-142 `D-M3-04-FIX`** — hoãn nghỉ nay là **CAM KẾT** (ghi "nghỉ ở giờ X", ép ở decision
  point kế trong giờ X, bận trọn giờ thì trả quyền nghỉ ngay) và **nhánh rơi không được là WAIT**
  (không có việc có ích ⇒ không hoãn, cho nghỉ luôn). A/B chẩn đoán 30 seed **đạt cả ba
  acceptance**: `rest_min` Δ **−244 → +10,9 ns** · `idle_min` **+209,5 → −66,8 ns** ·
  `work_span_p90` **+42,3 → −2,9 ns** ⇒ kênh thôi ăn vào nghỉ. Sổ cam kết: made 2,0/ngày ·
  kept 2,0 — lời hứa được giữ. `D-M3-06` gỡ cùng cycle. Sever 7/7 · fingerprint OFF 15/15 ·
  16 test đỏ-trước. ⚠ Kênh **vẫn TẮT + MỀM** (Q-16a) — bật lại như lời khuyên kinh tế cần
  **prereg MỚI**. Visual `BLOCKED` → `V-30` (dashboard chưa replay multiday).
- **UPDATE-141 Q-16 + FIX-PRE** — Cường chốt giữ TẮT + duyệt hướng FIX; phép kiểm phân biệt cắt
  riêng `world.py:970` cho **B″ ≡ A bit-identical 30/30 seed** ⇒ dòng đó là TOÀN BỘ cơ chế,
  bridge không nhiễm RNG world. Ba ô đọc kết quả khai TRƯỚC khi chạy.
- **UPDATE-140 Cycle B `D-M3-04`** — phép đo multiday 100 seed chạy xong ⇒ **REVERT thi hành**
  (`rest_window` MEASURED → SOFT): Δ **−429,3đ ns** [−1 142; +290] **và** STOP-C bắn
  (`rest_min_total` −6,6%) — hai đường REVERT độc lập của `luat_quyet_dinh` khoá TRƯỚC khi đo; Δ nằm
  TRONG kỳ vọng đã khoá ⇒ **phép đo thành công, không phải kênh thất bại**. 🔴 Ba bài học phải nhớ:
  (1) **ba lần một phiên** kết luận từ n nhỏ rồi bị bác (n=5 "hàng đợi trạm" · n=3 "nghỉ→sạc" ·
  "85% lượt kéo ca") — CI ở n<30 không được vào câu kết luận; (2) **đọc nhánh `if` TRƯỚC khi khai
  thác số tổng hợp** — cơ chế thật là MỘT dòng `world.py:970` (`action := WAIT`): hoãn nghỉ = đứng
  chờ, 86% nghỉ mất đi thành chờ rỗng, đơn **ns** ⇒ kênh đốt sức khoẻ không đổi lấy gì; (3) REVERT
  **không sửa cái hại** — kênh vẫn hại sức khoẻ, giữ TẮT (`D-M3-04-FIX` sev CAO, chặn bởi
  `D-M3-04-FIX-PRE`). `D-QD4-01` tự tiêu. `Q-16` chờ Cường. Sever 12/12.
- **UPDATE-137 `QĐ-4`** — ranh giới KHUYÊN MỀM hoá ra hở ở **đường ghi thứ TƯ**: AdviceCheckpoint
  **v2** (đến từ PR #4 của Khánh) có **store riêng** và **từ vựng `topic` riêng giao với registry =
  RỖNG**, nên `classify()` không chạm được một event nào của nó — trong khi `rest` được sinh thật
  (`checkpoint.py:134`, S7) và nhận được `response: accepted`. Tức **trace đồng ý cho lời khuyên
  NGHỈ đang được ghi**. ⚠ Điều dễ hiểu sai: **chưa con số nào sai** (`adherence_view` không thấy
  store v2) — nhưng dữ liệu **tích luỹ**, nên dạng lỗi này **nguy hiểm hơn** một số sai: ngày ai đó
  tính adherence trên store này, tỷ lệ hiện ra ngay với lịch sử đầy đủ, không ai phải làm gì sai
  thêm. Cường chốt **(b) hợp nhất**; đã hợp nhất **THẨM QUYỀN chứ không đổi tên** (đổi tên phá
  contract Khánh + mọi bản ghi cũ). Sever 8/8. Bài học **khác** 5 lần trước của cùng họ lỗi: không
  phải một người quên nối, mà **hai người nối hai nửa khác nhau** ⇒ *"mỗi người kín phần mình"
  không cộng lại thành kín*.
- **UPDATE-136** — cycle nợ sau vòng soi độc lập: tuyên bố *"đã thi hành bằng máy"* của UPDATE-135
  chỉ đúng **một phần**. `adherence_view` **fail-OPEN với topic chưa khai** (`is_soft("unknown")` =
  `False` ⇒ topic lạ đi thẳng vào bảng đo) · đường **pipeline** không ghi `topic` · cú loại **im
  lặng** · scanner regex chỉ quét 3 file và **mù với `channel=<biến>`**. Nay: fail-closed +
  `adherence_drops()` + **TREO** khi có `unknown`/`mixed` + scanner AST khai được vùng mù + pin
  `SOFT_MONG_DOI` chống **THU HẸP** registry (mọi cổng khác tự tham chiếu `SOFT_TOPICS` nên mù với
  việc bỏ bớt — *"0 test chạy" trông y hệt "0 test hỏng"*).
- **UPDATE-135** — hai việc. **(a) Khoá ngoài: kiểm bằng GỌI THẬT cả 9 khoá/endpoint**, và cách đó
  tìm ra ba lỗi mà đọc code không thấy: `OSRM_BASE_URL` **không ai đọc** ở runtime (chỉ script ma
  trận offline đọc) dù `.env`/`.env.example` mô tả nó là tầng 1 · mirror OSRM thứ hai **sai tên
  miền** (`router.project.osrm.org` — TLS hostname mismatch ⇒ **chưa từng chạy được**) · và
  `GRAPHHOPPER_API_KEY` **thiếu hẳn** ở `.env` của Cường (gitignore nên bản Khánh sửa không sang
  được) ⇒ tầng 2 chết lặng. Đã sửa cả ba + `GOOGLE_MAPS_API_KEY` gắn nhãn CHẾT (`REQUEST_DENIED`,
  không code nào đọc). ⚠ Điều dễ hiểu sai: hai mirror OSRM **cùng một IP** ⇒ đổi mirror **không**
  chữa được rate limit. **(b) Ranh giới KHUYÊN MỀM KHÔNG ĐO** — tầng thứ ba của tỷ giá sức-khoẻ↔KPI
  (xem §1 ở trên). `V-26` chờ Cường. Bài học lặp lại lần thứ 5 của cùng một họ: **cấu hình/cơ chế
  được tài liệu quảng cáo mà không có đường chạy** — và lần này chỉ **gọi thật** mới thấy.
- **UPDATE-120 (Khánh)** — routing **3 tầng** OSRM → GraphHopper → ước lượng đường thẳng **trung
  thực**. Bỏ hẳn fallback từng vẽ một đường cong sin rồi gắn nhãn sai `"hanoi_street_graph_engine"`;
  thêm field `route_is_real_road` để UI phân biệt tuyến thật với ước lượng thay vì so chuỗi
  `source`. Cùng họ lỗi mà repo đã trả giá nhiều lần: **nhãn nói một đằng, dữ liệu một nẻo**.
- **UPDATE-121 `D-M3-17`** — tầm pin trên UI nay khớp engine (77 → **43,8 km** ở SOC 70%), và đây
  là **cổng UI↔engine đầu tiên** của repo. Bài học kiến trúc test: **cổng phải đặt ở ĐƯỜNG NỐI
  giữa hai thành phần**, không phải bên trong mỗi thành phần — 1.000 test cũ không thấy lệch 1,76×
  vì mỗi bên đúng theo tiêu chuẩn của riêng nó. Mở `D-M3-18` sev CAO: **40/150 tài xế là xe hơi**
  mà repo không có tham số tiêu hao cho xe hơi.
- **UPDATE-119** — **Week 2 Report gửi mentor** (`docs/reports/week2/`, PDF 24 trang,
  `WAITING-VERDICT` V-23). Trước khi viết: 24 subagent đối chiếu toàn dự án. Bắt được doc của
  Khánh trích `+6.016đ` — con số **không tái lập được** sau khi sửa thước (UPDATE-113). Và khi chụp
  ảnh thì phát hiện **UI đang demo cấu hình đã bị ĐA-07 bác bỏ** (Δ = −10.819đ trên UI).
- **UPDATE-118** — **BA cổng thường trực** nay canh ba bảo đảm mà `CLAUDE.md` §4b đòi nhưng
  trước đây không ai thi hành: cờ config phải có người đọc · không L3 view nào đọc record chưa
  tồn tại (7/7 deriver sạch, **có test sever-restore tự chứng minh cổng bắn được**) · chỉ MỘT
  bảng màu trạng thái. Nhận ra 14 bug của 115/116/117 đều thuộc **hai họ**, và nợ thật là
  **thiếu cổng**, không phải 14 bug rời.
- **UPDATE-117 `D-M3-15`** — **quét cơ chế mồ côi** thay vì chờ lỗ thứ tư. 5 cờ config không ai
  đọc (3 cờ **mô tả SAI hành vi**: phạm vi pin 60/110 vs thật 62,5/117,6 km; bucket metrics 15′
  vs thật 60′) + 14 hàm public không caller, gồm `trajectory.py` module CHẾT mang **bảng màu thứ
  hai xung đột** với dashboard. Nay có **cổng thường trực** `test_config_flags_wired.py`.
- **UPDATE-116 `D-M3-13`** — **tầng 5 chưa từng đo được gì**: có hàm gộp, có
  `health_guardrail`, nhưng `_system_metrics` không mang khoá sức khoẻ nào ⇒ `TREO — THIẾU DỮ
  LIỆU` trên mọi pair. Lần thứ BA cùng mẫu `D-R12` trong hai ngày, và cả ba lần UPDATE của chính
  tôi đã tuyên bố cơ chế hoạt động. Sau khi nối, đo đường thật: nghỉ **+352,8′**,
  `work_span_p90` **−17,8′**, verdict OK, scope **90/90**.
- **UPDATE-115 `D-M3-11`** — **6 rò rỉ thông tin tương lai** ở L3 view l1r. Vào từ MỘT test đỏ
  (idle 247,48′ > online 246′); hai giả thuyết rẻ (làm tròn · lệch hai bảng) bị **loại bằng đo**.
  Bài học tái dùng được: khi bắt được một lỗi *thuộc một họ*, **viết phép thử cho cả họ rồi quét**
  — 4/6 chỗ tìm ra bằng probe, không bằng đọc code (tôi đã đọc chính hàm đó mà vẫn không thấy).
- **UPDATE-114** — 5 lỗ đường ống A/B do vòng thiết kế `D-M3-04` bắt, trong đó **lỗ (b) là do
  chính tôi tạo ra hôm trước** (cổng tầng 5 trên TỔNG cohort ⇒ kênh thưa pha loãng ~10× ⇒ cổng
  canh nhiễu). Vòng soi cũng **bác 2 chỗ sai trong brief của tôi** bằng đo.


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
| **0** | ~~**`D-M3-17`**~~ | — | ✅ **XONG (UPDATE-121)** — UI đọc hệ số từ `configs/pilot_dongda.yaml`, hiển thị **dải + cơ sở**, chọn mức **THẬN TRỌNG** (77,0 → **43,8 km** ở SOC 70%). Kèm **cổng UI↔engine đầu tiên** của repo (12 test, có sever-restore). Mở `D-M3-18` sev CAO: **40/150 tài xế là XE HƠI** mà repo không có tham số tiêu hao cho xe hơi ⇒ cờ `applicable=false`, UI hiện *"— chưa có cơ sở"* | chờ `V-25` |
| 1 | ~~**`L1-04`**~~ | — | ✅ **XONG (UPDATE-107)** — n=100 BÁC giả thuyết "28% mất hẳn": Δ=0 tuyệt đối; đó là gap LOGGING đã đóng bởi `D-M3-01`. Fix giữ (đúng `R-01`). ⚠ Kèm flaw #6 SUITE bắt: event MA sau khi áp — đã sửa (`mark_outcome_logged`) |
| 2 | ~~**Cổng THỐNG KÊ**~~ | — | ✅ **XONG (UPDATE-107)** — z Poisson-binomial `\|z\| > 4` NỐI vào `run_ladder` thật; null đọc từ **nominal của run** (không hardcode); không treo oan arm tuân-thủ-tuyệt-đối |
| 3 | 🔴 **`E10` advisor-cũng-nhiễu** — **quan trọng nhất còn lại** | ~1–1,5 ngày | ✅ **XONG — nhưng ĐỌC SỐ CỦA UPDATE-113, KHÔNG phải 110.** ⚠ Thước adherence của UPDATE-110 SAI (trộn *tài xế đồng ý* với *hệ thống thực thi được*); sửa thước ⇒ **mọi số đo lại và giảm**: `B_oracle` **+3.939đ** [2.854, 5.033] · `hist` **+3.401đ** · `real` **+3.126đ** · `wait` +174đ **SỤP**. Lớp đổi **CÒN-MỘT-PHẦN → KQ-GIỮ** (CI của Δ vs oracle chứa 0). **+6.016đ của UPDATE-087 KHÔNG tái lập được** (CI mới không chứa nó) ⇒ `D-E10-06`. Phát biểu YẾU, bắt buộc kèm caveat L1+L2+`D-E10-07` |
| 4 | ~~**`D-M3-04`**~~ multiday A/B cho `rest_window` | — | ✅ **XONG (UPDATE-140, 2026-08-05) — verdict = REVERT, ĐÃ THI HÀNH.** 100 seed × 3 ngày × 2 arm; kênh nói 2 986 lần (hết inert). Trúng **HAI** đường REVERT độc lập của `luat_quyet_dinh` khoá trước: Δ **−429,3đ ns** [−1 142; +290] (TRONG kỳ vọng đã khoá [−1 500, +500] ⇒ phép đo **THÀNH CÔNG**) **và** **STOP-C BẮN** (`rest_min_total` −6,6%). `rest_window` nay là **khuyên MỀM** (`SOFT_TOPICS`); `D-QD4-01` **tự tiêu**. 🔴 Đọc thêm ở UPDATE-140: (a) kênh **VẪN hại sức khoẻ** sau REVERT ⇒ `D-M3-04-FIX` sev CAO (giữ TẮT; hoãn phải là CAM KẾT; nhánh rơi không được là `WAIT` — cơ chế nằm ở `world.py:970`, nghỉ −244′ → chờ rỗng +209,5′ = **86%**, đơn **ns**); (b) 🔴 **ba lần một phiên kết luận từ n nhỏ rồi bị bác** — CI ở n=3/n=5 KHÔNG được xuất hiện trong câu kết luận, và **đọc nhánh `if` TRƯỚC khi khai thác số tổng hợp**; (c) `Q-16` chờ Cường: giữ TẮT? duyệt hướng FIX? |
| 5 | Cycle **đường SẢN PHẨM** — 13 finding sev CAO | phần lớn đã xong | ✅ **6/6 finding NẶNG đã xử lý** (kiểm bằng code 2026-08-01): `L3-03` tie-break `observed_at` ✓ · `L4-01` `displayed` vào máy trạng thái ✓ · `L4-04` `CLIENT_TOPICS`+`DEFAULT_TOPIC="brief"` ✓ · `L4-07` card im lặng dùng cờ `actionable` ✓ · `L4-09` `shift_start_min` thành Query param ✓ · `L4-03` = **`V-21` chờ Cường** (3 lựa chọn, 2 trong đó đổi CHÍNH SÁCH). Còn: `cards.js` `KIND_HOURS` vẫn ánh xạ 3 mốc giờ — nhưng là **PLACEHOLDER có nhãn**, chờ `ĐA-06 AdviceEnvelopeV2` mang chủ đề thật |
| 6 | 🔴 **`D-M3-18`** — 40/150 tài xế là XE HƠI, repo chỉ có tham số tiêu hao XE MÁY | ~2–4 giờ | **TODO sev CAO** — backend+web đã gắn cờ, **app Flutter chưa đọc cờ** nên tài xế xe hơi trên app vẫn thấy số vô căn cứ (phần Khánh). Fix thật: thêm **field đội pin** vào view + tham số tiêu hao cho ô tô |
| 7 | **`E9`** chọn lọc TRONG kênh | ~1 ngày | chờ |

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
| `tracking/VISION-ALIGNMENT-2026-07-29.md` | **NEO của mọi plan mới** — đối chiếu từng vế tầm nhìn Cường ↔ cái đã có ↔ gap ↔ route. *Plan nào không trỏ được về một vế ở đây thì phải tự hỏi vì sao tồn tại.* ⚠ Doc-graph 2026-07-30 phát hiện file này MỒ CÔI (0 inbound link) dù tự tuyên bố là NEO — đã nối lại tại đây |

---

## §5. 🔴 MƯỜI HAI BẪY ĐÃ SẬP THẬT — đọc trước khi tin bất kỳ con số nào

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

**8. "Test đỏ lệch tí xíu ⇒ chắc là lệch ĐO."** `test_bug01_idle_never_exceeds_online_time` đỏ với
idle **247,48′** vs online **246,00′** — vượt **1,48′**. Phản xạ đầu tiên của tôi: lệch hai bảng, ghi
nợ, đi tiếp. Thực tế là **rò rỉ thông tin tương lai**: view hỏi lúc 23:00 nhận dwell bắt đầu **23:03
và 23:27**, và probe sau đó tìm thêm **5 chỗ nữa** ở 3 deriver (UPDATE-115). ⇒ **Vượt một bất biến
VẬT LÝ thì độ lớn không nói gì về mức nghiêm trọng** — 1,48′ và 1.054′ cùng nghĩa là "sai cơ chế".
Việc cứu tình huống chỉ là **dump dữ liệu ra xem**, một câu lệnh. Và: **4/6 chỗ tìm ra bằng probe,
không bằng đọc code** — tôi đã đọc chính hàm đó khi sửa chỗ đầu mà vẫn không thấy hai field kia.
⇒ **Bắt được một lỗi thuộc một họ thì viết phép thử cho CẢ HỌ rồi quét, đừng soi bằng mắt.**

**9. "Cơ chế TỰ QUẢNG CÁO trong docstring nhưng không ai nối nguồn" — sập 3 LẦN trong 2 ngày.**
`D-R12` · UPDATE-114 lỗ (a) (`adherence_a` có field + comment *"arm đối chứng cũng phải được ĐO"*
nhưng không cổng nào đọc) · UPDATE-116 `D-M3-13` (tầng 5 có hàm gộp + `health_guardrail` đầy đủ,
nhưng `_system_metrics` **không mang khoá sức khoẻ nào** ⇒ verdict `TREO — THIẾU DỮ LIỆU` trên
mọi pair, và `grep` cho thấy **0 artifact** từng mang tầng 5). Cả ba lần, **UPDATE của chính tôi
đã tuyên bố cơ chế hoạt động**. ⇒ **Trước khi tin một cổng, ĐO đầu ra của nó trên một pair
THẬT** — đừng đọc docstring, đừng tin UPDATE cũ, kể cả UPDATE của mình. Đối trọng duy nhất đã
chứng minh hiệu quả: **test sever-restore** (ngắt cơ chế ⇒ phải đỏ) và `grep` artifact đã lưu.

**10. Một giá trị `None` KHÔNG phải bằng chứng cơ chế mù.** Sau khi nối tầng 5, tôi đọc
`a_mean['n_actors_scope']` ra `None` và kết luận *"`touched_actors` trả rỗng ⇒ cổng vẫn chấm toàn
cohort"* — sắp ghi thành lỗi thứ tư. Thực tế: `_mean` chỉ gộp 12 khoá liệt kê nên khoá đó **vắng
khỏi dict**, còn `touched_actors(rb)` trả đúng **90/90**. ⇒ Với `.get()` trả `None`, phân biệt
*"giá trị là None"* với *"khoá không tồn tại"* trước khi kết luận. (Phát hiện sai vẫn dẫn tới một
fix thật: mẫu số **phải** hiện trong artifact — `OK` trên 90/90 và trên 9/90 nghĩa khác hẳn.)

**12. Cấu hình có thể CHẾT theo ba cách khác nhau, và `grep` chỉ thấy một.** Ngày 2026-08-03 Cường
hỏi *"có cần cập nhật `OSRM_BASE_URL` ở end của tôi không"*. Câu trả lời trung thực hoá ra là *"đổi
cũng không ảnh hưởng gì"* — vì **không code runtime nào đọc biến đó** (chỉ script ma trận offline
đọc), trong khi `.env` và `.env.example` mô tả nó là **tầng 1 của routing**. Và **gọi thật** còn lộ
thêm hai lỗi nữa mà đọc code không thấy:

| Cách chết | Phát hiện bằng | Lỗi thật |
| --- | --- | --- |
| Không ai đọc biến | `grep` tên biến trong `src`/`ui` | `OSRM_BASE_URL` |
| Giá trị **trông đúng** mà host chết | **gọi HTTP thật** | mirror 2 viết `router.project.osrm.org` (dấu **chấm**) — DNS phân giải được nên trông thật, nhưng TLS trả `Hostname mismatch` ⇒ **chưa từng chạy** |
| Biến **vắng** ⇒ nhánh return `None` lặng lẽ | gọi thật **từng tầng** | `.env` thiếu `GRAPHHOPPER_API_KEY` (gitignore ⇒ bản Khánh sửa không sang máy Cường) ⇒ tầng 2 không tồn tại, app tụt thẳng xuống tầng 3 |

⇒ **Suite không thể bắt loại này**: mọi test routing đều `monkeypatch` `urlopen`, nên tên miền không
bao giờ bị phân giải thật. Và `test_config_flags_wired` chỉ quét `configs/pilot_dongda.yaml`, **không
quét `.env`**. ⇒ **Với dịch vụ ngoài, hãy GỌI THẬT một lần rồi mới nói nó hoạt động** — và với biến
gitignore, **đừng cho rằng đồng đội sửa `.env` là bạn cũng có.**

**11. "Suite xanh + 5 cycle fix" KHÔNG có nghĩa luồng sản phẩm đã kín.** Sau 5 UPDATE liền và
suite 1.000/0 đỏ, một **smoke end-to-end 10 phút** (gọi thật 4 endpoint qua `TestClient`) tìm ra
`D-M3-17`: UI tự tính phạm vi pin `soc*1.1` cho MỌI tài xế trong khi engine cho 62,5 km (swap) và
117,6 km (charge) ⇒ tài xế swap thấy số **thổi 1,76×**; endpoint legacy còn dùng `soc*3.2` = **5,1×**.
Không test nào bắt được vì **không có test nào so UI với engine**. ⇒ **Chạy thật đường mà người
dùng đi, đừng chỉ chạy test.** Và lưu ý prefix API là `/api/v1/...` (tôi gọi `/api/...` trước và
nhận 404 — đừng kết luận "endpoint chết" từ một 404).

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
