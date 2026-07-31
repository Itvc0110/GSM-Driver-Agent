# UPDATE-108 — Spec E10 "advisor cũng nhiễu" tổng hợp từ 3 thiết kế + 6 phản biện; CHỜ DUYỆT plan mode

Ngày: 2026-07-31 · Người thực hiện: agent (dưới claim Cường) · Trạng thái: `WAITING-VERDICT`

## Files bị ảnh hưởng

- **TẠO** `specs/simulation/e10-advisor-noisy.md` (847 dòng) — spec thi công E10, sinh bởi workflow
  10 agent (3 thiết kế độc lập → 6 phản biện đối kháng lăng kính rò-rỉ-oracle → tổng hợp), sau đó
  **agent chính tự kiểm lại các claim code chịu-lực** (xem Kiểm chứng).
- **SỬA** `tracking/DEFERRED.md` — thêm 4 mục `D-E10-01..04` (bẫy/DEFER spec chỉ ra).
- **SỬA** `tracking/PLAN-2026-07-30-hang-doi-cong-viec.md` — mục 3: trỏ spec, ghi 2 đính chính
  (nguồn E10b là `idle_streak_min` không phải `idle_by_hour`; đề xuất 4+1 arm thay 3).
- **SỬA** `tracking/PROJECT-GRAPH.md`, `tracking/BOOTSTRAP-SESSION.md` — node/route UPDATE-108.

## Chi tiết cập nhật

Câu hỏi trung tâm: **"+6.016đ còn lại bao nhiêu khi advisor mất λ?"** (con số chủ lực đang ở cột
LUNG LAY của `data-contract-counterfactual.md` §4 vì advisor nhận đúng λ generator —
`demand.py:76`).

Quyết định tổng hợp chính của spec (chi tiết + lý do trong spec):

- **E10a**: λ̂ chỉ từ event `pickup`, cửa sổ cuốn k bucket; **cold = advisor IM LẶNG có log, CẤM
  fallback oracle**; chống nhiễm oracle 3 tầng đều có test đỏ-được (narrow reader whitelist /
  poison đúng ref producer / λ chỉ làm thước chấm hậu-kiểm trong script).
- **k\*** chọn bằng MAE dự báo one-step-ahead **realized-only** (0 oracle trong hyperparameter),
  shadow trên World A tuning seeds; bỏ hẳn `smooth_alpha`.
- **E10b**: nguồn `idle_streak_min` (đính chính PLAN §3b); T=30′ headline (neo sửa lại 14–18′ vì
  bản gốc nhầm CYCLE/WAIT; 45/60 loại cấu trúc do impatience 20′×2 cụt streak ~40–44′); n_min=2;
  cổng cá nhân streak ≥ T; **zone-veto** đóng cả tự-gán-qua-Hungarian-stagger
  (`capacity_alloc.py:50` — cost lệch target = `pen+10`, KHÔNG phải LARGE) lẫn nguồn-đích chồng
  batch.
- **Phép đo**: 4 arm chính (A, B_oracle, **B_hist** mới, B_real) + B_wait + B_wait_oracle chẩn
  đoán n=30; B_hist tách "mất λ" khỏi "mất trí nhớ qua đêm" (lỗ GIẾT-CHẾT của phản biện), dùng hook
  `market_demand_override` sẵn có, prior từ 30 run World A tuning — CẤM cùng seed (future leak
  xuyên thế giới). Seeds đo 5000–5099 / tuning 5100–5129, coverage="all" pin cứng.
- **Tiền-flight bắt buộc** (§5.5): cổng z gộp chưa từng chạy trên positioning; dự đoán đăng ký
  trước là TREO cả oracle vì gap coin-vs-execution (86 gán/42 coin/36 followed theo comment 1-seed
  `world.py:335-338`) ⇒ nhánh sửa THƯỚC (followed = coin-outcome tại gán; execution_rate tách
  riêng), không nới ngưỡng.
- **Tiền-đăng-ký** `e10-prereg-locked.json` commit trước run đo; 4 lớp kết luận
  GIỮ/CÒN-MỘT-PHẦN/SỤP/ÂM; STOP-0a/0b/1/2/3; bảng kỳ vọng trung thực §6.5 ghi trước khi đo.
- **10 giới hạn không vá được** khai tường minh §9 (L1 thế giới rank-tĩnh → KQ-GIỮ phát biểu yếu /
  KQ-SỤP phát biểu mạnh; L2 λ̂ ngửi oracle qua bản năng tài xế; L3 feed pickup toàn đội chưa VỮNG;
  L4 E10b đo trigger×execution-gate; …).

**Ba điểm spec KHÔNG tự quyết, chờ Cường trong plan mode** (ghi đầu spec): (1) thêm arm B_hist;
(2) mini-cycle sửa thước adherence positioning nếu tiền-flight bắn; (3) ngân sách máy ~5–5,5h
(cao hơn ước 3–4h của PLAN).

## Docs đã cập nhật kèm theo

DEFERRED (+4 mục) · PLAN mục 3 (trỏ spec + 2 đính chính) · PROJECT-GRAPH · BOOTSTRAP. SCOPE /
TODO / USER_STORIES: không đổi (E10 là thí nghiệm đo lường trong scope sim hiện hành).

## Kiểm chứng

- **Chưa kiểm chứng bằng chạy**: spec chưa implement, chưa đo — mọi con số độ lớn trong spec
  (0,6–1,2 pickup/ô/bucket; z≈13; 15–22 pickup/giờ thấp nhất) là ước tính tay/1-seed, spec tự đánh
  dấu PHẢI đo lại ở probe/preflight trước khi trích (bẫy "cơ chế đúng độ lớn sai" đã sập 3 lần).
- **Đã tự kiểm độc lập** (mở file, không tin số dòng của workflow) các claim code chịu-lực:
  `demand.py:76` oracle λ ✓ · `market_state.py:94-99` override THAY THẾ + docstring cross-run ✓ ·
  `capacity_alloc.py:50` stagger `pen+10.0` ✓ · `world.py:781-787` pop im lặng + cổng wait_only ✓ ·
  `world.py:353` coin rút một lần lúc gán ✓ · `behavior.py:168-197` + `pilot_dongda.yaml:202-204`
  impatience 20′×2 ✓ · `entities.py:53/125-132` `idle_streak_min` KHÔNG trong `_DAILY_RESET_*` ✓ ·
  `world.py:499/881/885` ba điểm ghi streak ✓ · `parallel.py:73-95` coverage default "single" ✓ ·
  `world.py:292-318` trigger hiện hành `cap_left==0` ✓. **0 claim sai bắt được.**
- Suite: không chạy lại (docs-only, không đổi code).

## Nhãn evidence

Spec = **THIẾT KẾ** (chưa có số đo nào); các file:line trong §0 = `[ĐO]` (đã mở file 2026-07-31);
ước độ lớn = `[ƯỚC TÍNH]` có nhãn trong spec. Seeds: chưa chạy seed nào cho E10.

## Visual review

`NOT_APPLICABLE` — docs-only (spec + tracking), không đổi output sim/UI. Visual gate của chính E10
nằm ở spec §8 bước 7 (dashboard bản đồ herding B_real vs B_oracle, trước commit cycle đo).

## Adversarial self-review / flaws found

- Rủi ro lớn nhất spec tự khai: **thi công chọn lọc** (spec dài, làm phần dễ rơi phần cổng) — đối
  trọng là 18 test T1–T18 đánh số + artifact phải mang đủ khoá, `diff` fail-loud khi thiếu.
- Spec đề xuất **vượt PLAN đã duyệt ở 2 điểm** (4+1 arm thay 3; ~5–5,5h máy thay 3–4h) — KHÔNG tự
  thi hành, đã đưa thành điểm chờ #1/#3.
- Phản biện của workflow có 2 finding bị BÁC (percentile threshold; prior cell_weight) — đã ghi lý
  do trong bảng §0b của spec; tôi đồng ý với cả hai phán quyết sau khi đọc code (percentile
  luôn-bắn ngược ĐA-07; cell_weight là chiều không gian noise-free của λ).
- Con số "z ước ≈ 13" ở §5.5 là ngoại suy từ MỘT seed — nếu preflight 30 seed cho |z| ≤ 4 thì nhánh
  sửa thước không kích hoạt, spec đã có nhánh 2 cho trường hợp này (không phải chỉ nhánh "bắn").
- UPDATE numbering: 108 là số local kế tiếp; remote từng chiếm 104/105 — nếu đụng khi merge, đổi số
  theo tiền lệ 098→099 (memory `gsm-git-integration-workflow`).

## Follow-up / defer phát sinh

- 4 mục DEFERRED mới: xem `tracking/DEFERRED.md` `D-E10-01..04`.
- Docstring stale `advice_bridge.py:589` ("cùng dòng RNG" — code thật là keyed): sửa khi chạm file
  trong cycle thi công (spec §2.2).
- ⏳ **PENDING-REVIEW còn 17 mục chờ Cường**: V-01..V-14, V-16 (fare parity), V-17 (kênh VỊ TRÍ),
  V-18 (nhịp nói) — nhắc theo lệ sau mỗi update.
