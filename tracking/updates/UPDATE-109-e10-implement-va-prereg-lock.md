# UPDATE-109 — E10 thi công (Bước 1–5) + KHOÁ tiền-đăng-ký trước khi đo

Ngày: 2026-07-31 · Người thực hiện: agent (dưới claim Cường, plan duyệt qua AskUserQuestion
2026-07-31: B_hist ✓ · sửa-thước-nếu-z>4 ✓ · ngân sách 5–5,5h ✓) · Trạng thái: `DOING`
(cycle E10 chưa xong — đây là commit CHECKPOINT bắt buộc: spec §6.1 đòi commit
`e10-prereg-locked.json` TRƯỚC run đo đầu tiên; UPDATE kết quả đo là UPDATE kế tiếp)

## Files bị ảnh hưởng

- **TẠO** `src/gsm_sim/demand_estimator.py` — `RealizedDemandEstimator` (λ̂ chỉ từ event
  `pickup`, cửa sổ cuốn k bucket, cold ⇒ `{}` im lặng, narrow reader, 0 RNG).
- **SỬA** `src/gsm_sim/market_state.py` — `market_demand_source: oracle|realized` (fail-loud
  3 ValueError), `_demand(hour, idx)` rẽ nhánh estimator TRƯỚC (2 nhánh cũ nguyên văn),
  `view()` log `demand_est`/`demand_est_cold` một lần/bucket CHỈ khi realized;
  `count_idle_wait` + `wait_fired_cells` (E10b, cạnh `count_supply`).
- **SỬA** `src/gsm_sim/world.py` — nhánh `wait` trong `_standby_planner` (fired set + cổng cá
  nhân streak ≥ T + **zone-veto** `ranked_eff` + assert runtime không-gán-vào-ô-fired + log
  `fired_cells` chỉ ở wait-mode); process `_wait_stats_probe` (log-only, cờ `probe.wait_stats`).
- **SỬA** `src/gsm_sim/advice_bridge.py` — 3 khoá `positioning_trigger`/`positioning_wait.*`
  (validate fail-loud); đính chính docstring stale `standby_follow_draw` ("cùng dòng RNG" →
  keyed sha256).
- **SỬA** `configs/pilot_dongda.yaml` — khoá E10 default neutral (`market_demand_source:
  oracle`, `realized_demand`, `positioning_trigger: capacity`, `positioning_wait`, `probe`).
- **TẠO** `scripts/measure_e10.py` — 9 lệnh: preflight/probe/tune/histprior/prereg/worldA/
  arm/sens/diff (bias thêm sau khi có arm chạy); wrapper verdict đi qua `aggregate_adherence`
  THẬT (không recompute); guardrail truy cập cứng `g[k]`; prereg lazy-load.
- **TẠO** `specs/simulation/e10-prereg-locked.json` — **FILE KHOÁ**: sau commit này CẤM đổi
  k/T/n_min/min_pickups sau khi nhìn Δ, cấm nới z, cấm dời T headline.
- **TẠO** `tests/test_demand_estimator.py` (12) · `tests/test_e10_wiring.py` (13) ·
  `tests/test_e10b_wait_trigger.py` (10) — 35 test mới, tất cả xanh.
- **TẠO** artifact `research/audit/2026-07-27-current-state/41-e10-{preflight,probe,tune-kstar,
  hist-prior}*.json`; cache `41-e10-tuning-cache.json` vào `.gitignore` (1,3MB, tái tạo được).

## Kết quả các bước (số ĐO, không phải ước)

1. **Tiền-flight §5.5 (STOP-0b)**: z gộp positioning trên B_oracle 30 seed = **−2,39**
   (n=2.277, đo 0,466 vs null 0,490) ⇒ |z| ≤ 4, **cổng KHÔNG bắn — THƯỚC GIỮ NGUYÊN**.
   🔴 **Dự đoán đăng ký trước SAI theo hướng bảo thủ**: spec đăng ký "SẼ bắn, z ước ~13" từ
   số 1-seed (gap 7đp); gap gộp thật chỉ −2,4đp. Đúng bẫy "cơ chế đúng độ lớn sai" — lần này
   bẫy được chính spec đặt ra bắt (buộc tự đo trước khi trích). Nhánh sửa-thước Cường duyệt
   KHÔNG kích hoạt (điều kiện z>4 không xảy ra).
2. **Estimator + wiring**: fingerprint per-actor **10/10 IDENTICAL** trước/sau merge (5 seed ×
   2 config: default-off và B_oracle) + 6/6 sau khi thêm khoá yaml + 6/6 sau E10b ⇒ STOP-0a đứng.
3. **Probe §4.7** (30 seed tuning, World A): W median per-cell (ô ≥2 idle) p50=**14′** —
   khớp neo hoà-vốn 14–18′ của spec; firing T=30/n=2 = **0,057 ô/bucket** (~1 lần/ngày —
   SỐNG nhưng RẤT THƯA); **T=45/60 firing = 0 tuyệt đối** (chết cấu trúc — đúng đăng ký);
   precision fired-vs-underfed(λ) = **1,00**, recall = **0,03** (trigger hiếm-nhưng-chuẩn);
   idle_share_ge2 = 0,775 ⇒ **fallback khối KHÔNG kích hoạt**; persistence proxy 0,024
   (người trong ô fired hầu hết rời đi trong bucket — nhất quán L4 execution-gate).
4. **Tune §6.2**: MAE one-step-ahead realized-only: k={1: 59,7 · 2: 56,4 · 3: 55,4 ·
   4: 54,8 · 6: **54,1**} ⇒ **k\* = 6**. ⚠ k\* nằm ở BIÊN lưới, MAE giảm đơn điệu theo k —
   hệ quả dự kiến của thế giới rank-tĩnh (L1): cửa sổ càng dài càng ít nhiễu vì không có gì
   để quên. Ghi nhận, không mở rộng lưới (prereg khoá).
5. **Hist prior**: 1.614 ô-giờ từ 30 run tuning (5100–5129) — cấm dùng cho seed đo (future
   leak xuyên thế giới); pickup/giờ thấp nhất = **14** ⇒ dự đoán "min_pickups trơ" (§6.5#1)
   nhiều khả năng đúng, sweep sẽ kiểm.

## Kiểm chứng

- 35 test mới xanh; **đỏ chứng minh**: T1 (ngắt truyền `by_channel_archetype` ⇒ 2 fail),
  9/9 test wiring đỏ trước khi có code, estimator 2 vế đỏ mutation đơn, biên bucket =
  defense-in-depth 2 lớp (sever CẢ HAI ⇒ 2 fail; sever một lớp được lớp kia đỡ — ghi trong
  docstring test), T14 stagger-về-own-cell ĐỎ trên thế giới chưa-veto (test riêng chứng minh
  Hungarian gán về chỗ đứng khi own-cell còn slot).
- 2 guard cold (`max(0,…)`, `idx ≤ first_op`) **không chứng minh đỏ được** — bất biến giữ theo
  CẤU TRÚC (range rỗng ⇒ acc rỗng), spec §3.2 lo bug không thể biểu hiện ở implementation dạng
  con-trỏ-theo-bucket. Ghi trong docstring test.
- Regression subset sim (11 file test cũ) + full suite: chạy tại thời điểm commit — kết quả
  ghi ở UPDATE kế tiếp nếu khác 0 fail.
- Seeds đã dùng: 5100–5129 (tuning/probe/preflight). Seeds đo 5000–5099 **CHƯA chạm**.

## Nhãn evidence

Toàn bộ MOCK (`pilot_dongda.yaml`). Số probe/tune/preflight = `[ĐO]` (artifact 41-e10-*).
`ruler_fix_applied = false` (thước giữ nguyên — z đo được dưới ngưỡng).

## Visual review

`NOT_APPLICABLE` cho checkpoint này — default bit-identical đã chứng minh bằng fingerprint
(không có output nào đổi để xem); visual gate THẬT (bản đồ herding B_real vs B_oracle) nằm ở
Bước 7 sau khi đo, trước commit kết quả.

## Adversarial self-review / flaws found

- **Dự đoán preflight sai hướng bảo thủ** (trên) — đã đăng ký trước nên không tô lại chuyện.
- **k\* ở biên lưới** — nếu ai trích "k=6 tối ưu" mà không kèm caveat L1 là trích sai; đã ghi.
- **Firing 0,057/bucket**: B_wait sẽ can thiệp ~1 lần/ngày ⇒ Δ(B_wait − B_real) gần như chắc
  chắn nhỏ/không phát hiện được ở n=100 — ĐÃ dự kiến ở §6.5#3, không phải lý do chỉnh T sau
  khi nhìn Δ (prereg cấm).
- Volume `n_assigned_into_fired_cells` có cả assert runtime lẫn cột artifact — hai lớp.
- Chưa có lệnh `bias` (B1–B5) — thêm sau khi arm chạy xong, trước UPDATE kết quả.

## Follow-up

- Bước 6 (đo ~5,5h máy theo batch) chạy ngay sau commit này; UPDATE kết quả + visual gate +
  full suite là bước nghiệm thu.
- ⏳ **PENDING-REVIEW còn 17 mục chờ Cường**: V-01..V-14, V-16, V-17 (kênh VỊ TRÍ), V-18.
