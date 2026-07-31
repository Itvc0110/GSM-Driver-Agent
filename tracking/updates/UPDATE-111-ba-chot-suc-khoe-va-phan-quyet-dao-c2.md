# UPDATE-111 — BA CHỐT SỨC KHOẺ có thật (D-M3-08/05 đóng) + PHÁN QUYẾT đảo C2 tầng world

Ngày: 2026-07-31 · Trạng thái: `DONE-CODE` (3 cơ chế) + `WAITING-VERDICT` (phán quyết C2 —
verdict cuối của Cường) · Commit: `fe63f61` (cơ chế 1) · `f4e7e40` (cơ chế 2) · `b40a38b`
(cơ chế 3) · docs commit này.

## Bối cảnh — hai việc trong một cycle

1. **Ba cơ chế enforce của khung BA LỚP** mà spec §1.2b khai "phải viết" nhưng grep toàn repo
   = 0 kết quả (D-M3-08 sev CAO — "chốt chặn sức khoẻ ghi là tồn tại nhưng không tồn tại" là
   loại sai tệ nhất của tài liệu ranh giới đạo đức).
2. **Chỉ đạo Cường** (*"thiết kế nghỉ phải đi kèm thiết kế mệt → giảm hiệu suất → khuyên nghỉ
   phải đem lại giá trị; triển khai thật AI chỉ GỢI Ý khi thấy làm quá sức"* — kèm ghi chú:
   thắc mắc + hướng hiểu, mời debate) ⇒ Cường giao agent **kiểm lại độ chính xác C2 và tự ra
   phán quyết**. Kết quả: `tracking/PHAN-QUYET-2026-07-31-dao-c2-tang-world.md`.

## Files bị ảnh hưởng

- **TẠO** `src/gsm_core/policy_locks.py` · `tests/test_policy_locked_keys.py` (8 test)
- **SỬA** `src/gsm_sim/advice_bridge.py` (chokepoint `assert_policy_locks` trong `__init__`)
- **TẠO** `tests/_health_boundary_scan.py` (scanner AST 2 lớp) · `tests/_health_boundary_manifest.py`
  (108 scope pin cứng) · `tests/test_health_boundary.py` (12 test)
- **SỬA** `src/gsm_sim/world.py` (hằng `REST_MIN/MAX_MINUTES` thay literal — bit-identical;
  nhánh `else:` log `advice_rest_veto` mọi kết cục không-defer — log-only) ·
  `src/gsm_sim/sim_metrics.py` (khối tầng 5: `rest_rails_audit`/`continuous_work`/
  `health_guardrail`/`health_guardrail_flags`; `system_guardrail` thành NĂM tầng) ·
  `src/gsm_sim/parallel.py` (`aggregate_health_guardrail` nối `run_ladder`)
- **TẠO** `tests/test_rest_rails_guardrail.py` (12 test) · **SỬA** `tests/test_fairness_metrics.py`
  (bundle 4 → 5 tầng)
- **TẠO** `tracking/PHAN-QUYET-2026-07-31-dao-c2-tang-world.md`
- **SỬA** `specs/advisor-objective-model-v2.md` §1.2b (3 hàng ❌→✅ SAU khi test xanh + trỏ
  phán quyết mới) · `configs/pilot_dongda.yaml` + `src/gsm_core/solvers/idle_reduction.py`
  (nhãn POLICY_LOCKED, comment-only) · `tracking/DEFERRED.md` (D-M3-05/08 → DONE-CODE) ·
  graph/BOOTSTRAP.

## Ba cơ chế — mỗi cái một dòng bằng chứng

| Cơ chế | Bằng chứng sống | Bằng chứng đỏ |
| --- | --- | --- |
| 1. `POLICY_LOCKED_KEYS` (khoá `rest_defer_max_min`=120, `shift_extend_max_min`=60, 3 hằng idle_reduction — gate OR) | sweep ⇒ `PolicyLockViolation` ngay khi dựng world, kể cả đường multiday (dựng World trực tiếp — lý do chokepoint là bridge, KHÔNG run_once) | sever chokepoint ⇒ 3/8 test đỏ đúng chỗ; monkeypatch hằng ⇒ nổ run kế |
| 2. Scanner AST `no_fatigue_in_payout_path` (2 lớp: token cấm trong 108 money-scope + toàn vẹn manifest) | repo hôm nay: 0 vi phạm, 0 unclassified, 0 dead entry; comment ĐÚNG `shift_dp.py:36,40` không bị oan (AST); lan can đọc fatigue hợp lệ | 4 mũi tiêm mutation IN-MEMORY vào file thật (arithmetic/dictkey/attribute/signature) đều bắn; hàm-mới-chạm-tiền bị lớp 2 bắt |
| 3. Guardrail TẦNG 5 (`rest_min_total` · `veto_*_n` per-rail + `veto_calls_n` · quá-sức CẢ HAI định nghĩa `work_span`/`drive_min` — Cường chốt qua AskUserQuestion) | veto KHÔNG trơ (hàng trăm lần/run); cổng MỘT CHIỀU trên p90, không chiều khen (chống Goodhart); nối `run_ladder` (T10 canh "sống trên giấy") | sever nhánh log ⇒ T1 đỏ; kịch bản xoá-lan-can ⇒ flag "SỤP VỀ 0" (T4 — đúng ca guardrail 4 tầng từng câm) |

## Phán quyết C2 (tóm tắt — văn bản đầy đủ là nguồn sự thật)

**Đảo trụ (a) ở TẦNG WORLD** — lỗ trong lập luận cũ: *"không mô hình = mô hình với β=0, và
β=0 là lựa chọn hiệu chuẩn THIÊN VỊ CHỐNG NGHỈ"* (làm gợi-ý-nghỉ vĩnh viễn trông như chi phí,
làm hoãn-nghỉ trông miễn phí). **Giữ nguyên**: trụ (b) — chỉ đường cong Δ(β), cấm claim điểm,
cấm chọn β theo Δ; advisor MÙ latent (scanner enforce, class `WORLD_PHYSIOLOGY` rỗng chờ E11);
sức khoẻ không quy tiền. Sáu điều kiện ràng; Phase A này là điều kiện #1 — ĐÃ XONG.
⚠ Phát hiện kỹ thuật: `online_min` gộp cả nghỉ (đơn điệu) — E11 phải dựng liều-có-hồi-phục
riêng, nếu không sẽ đo ra "số 0 giả".

## Kiểm chứng

- 32 test mới (8+12+12) xanh; bằng chứng đỏ như bảng trên (mutation thật, sever-restore).
- Fingerprint per-actor: **10/10 IDENTICAL** (5 seed × 2 config) so baseline TRƯỚC cycle —
  cơ chế 3 chạm world nhưng log-only, 0 RNG, 0 state.
- Regression: 48 test bridge + 20 test guardrail/fairness xanh. Full suite CẢ HAI lệnh: đang
  chạy tại thời điểm viết — kết quả chốt ghi vào commit docs (nếu ≠ 0 fail sẽ sửa trước khi
  gọi DONE-CODE).
- ✅ **Sabotage end-to-end ĐÃ chạy** (`scripts/probe_rest_rails.py`, 5 seed × 3 thế giới,
  artifact `42-rest-rails-sabotage-probe.json`): vô hiệu lan can `fatigued` thật (nâng ngưỡng
  ∞ chỉ trong lời gọi bridge) ⇒ arm B bình thường **0 flag** (không báo oan, veto 72/run);
  arm sabotage ⇒ flag đúng **"lan can `fatigued` SỤP VỀ 0 (A=51, B=0)"** — VERDICT: TẦNG 5
  TỐ GIÁC ĐÚNG. Kịch bản "guardrail 4 tầng câm" nay có còi.
- **Chưa kiểm chứng**: phán quyết C2 chờ verdict Cường.

## Nhãn evidence

Baseline quá-sức (World A seed 5100): work_span p50=295′/p90=431′/max=697′ — **62/90** tài xế
vượt 240′; drive_min p50=189′/max=484′ — **25/90** vượt. `[ĐO]`. Mốc 240′ = Điều 64 ô tô KDVT,
pilot là bike ⇒ ASSUMPTION tham chiếu. Toàn bộ MOCK.

## Visual review

`NOT_APPLICABLE` — không đổi output sim/UI (fingerprint 10/10 IDENTICAL là bằng chứng máy).

## Adversarial self-review / flaws found

- Vòng soi thiết kế bằng agent CHẾT vì quota (3/3 agent soi + 21 agent hai vòng khác) — tôi
  tự soi bằng tay: 2 lỗ nghi (test override khoá; bridge không dựng khi advice off) kiểm là
  KHÔNG tồn tại. **Vòng soi máy sẽ chạy bù sau 15:50** (đã hẹn resume) — nếu nó bắt thêm
  flaw, sửa ở commit kế.
- Chèn hằng `REST_MIN_MINUTES` ban đầu kẹt giữa `@dataclass` và `class Event` (SyntaxError)
  — bắt ngay bởi py_compile, sửa; bài học: anchor replace phải nhìn decorator.
- `defer_cap` trơ + 2 chỉ tiêu tầng 5 mù với đòn xoá-lan-can khi kênh nói 0 lần — KHAI tường
  minh trong spec (không im), `veto_fired_n` là chỉ tiêu chịu tải duy nhất hôm nay.
- Scanner token hẹp (`fatigue`) có chủ ý — nhưng nghĩa là biến tên khác (`tiredness`?) lách
  được LỚP 1; lớp 2 (hàm mới chạm tiền phải phân loại) là lưới đỡ. Ghi nhận giới hạn.

## Follow-up

- E11 (world-có-mệt + `rest_nudge`): CHỜ verdict Cường trên PHAN-QUYET; spec + prereg qua
  plan mode riêng.
- D-M3-05a: `defer_cap` trơ — mở lại khi D-M3-04 (multiday) xong.
- Resume 2 workflow sau 15:50: soi kết luận E10 + phản biện 13 finding sản phẩm.
- ⏳ **PENDING-REVIEW 17 mục chờ Cường**: V-01..V-14, V-16, V-17, V-18 — cộng: verdict visual
  gate E10 (artifact d8c58414) + verdict PHAN-QUYET đảo C2 + lệnh đẩy (ahead 6 sau cycle này).
