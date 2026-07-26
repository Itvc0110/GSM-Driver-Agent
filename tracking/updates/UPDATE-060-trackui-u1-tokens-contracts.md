# UPDATE-060 — Track UI U1: design tokens + palette LIGHT validated + contracts + SCREEN-PARITY

Ngày: 2026-07-26 · Track: **UI** · Phase U1/U4 · Sau U0 (`b6fec1c`).

## 1. Files bị ảnh hưởng

- **TẠO `ui/design-tokens.json`** — MỘT nguồn style cho cả web (CSS vars) lẫn Flutter (ThemeData):
  brand Khánh (cyan `#00AFB9`, ink `#1C1C1E`, nền `#E8F1FA`, Be Vietnam Pro, bo góc pill/16/24) +
  khối dataviz (categorical light/dark, sequential cyan, diverging, status) + nhãn mock bắt buộc.
- **SỬA `ui/contracts/driver_state.json`** → v1.1 **additive** (Flutter v0 của Khánh vẫn parse):
  thêm `money` (gross/payout/breakdown 4 nguồn/est_net nullable + definition_version), `tenure_days`,
  `rating` (từ counter sim), `missions[]`.
- **TẠO 4 contract mới**: `advice.json` (items + confidence + reason_code + numbers[].source
  THẬT/PROXY/ASSUMPTION/MOCK/SOLVER + trạng thái **silent có cấu trúc**), `journey.json` (segments/
  offers/income_curve/metrics bảo toàn 4 nguồn), `replay.json` (legs toạ độ + thời gian, client nội
  suy), `ab_result.json` (Δ paired + guardrail + **warning_text bắt buộc**).
- **TẠO `ui/docs/SCREEN-PARITY.md`** — bảng màn × contract × endpoint × trạng thái web/Flutter,
  trả lời câu hỏi của Cường về cách Khánh làm mobile song song không đè nhau.

## 2. Palette LIGHT — TÍNH, không ước bằng mắt (skill dataviz)

Nguyên tắc quyết định: **màu theo entity vĩnh viễn** — 5 hoạt động giữ ĐÚNG hue như bản dark P4
(aqua/blue/yellow/violet/magenta), chỉ đổi step cho nền sáng; còn **cyan brand `#00AFB9` là accent
UI chrome, KHÔNG làm series** (thử làm series thì FAIL: chroma 0.099 dưới sàn + ΔE 13.1 với blue —
vòng thử 1, giữ lại làm bằng chứng).

Kết quả `validate_palette.js` trên surface `#ffffff` (vòng thử 2 — **bộ chốt**):
- **Adjacent: PASS 5/5** — worst pair blue↔aqua ΔE 23.1 (protan) / 24.0 (normal).
- **All-pairs: PASS** kèm 2 ràng buộc ghi thẳng vào tokens.provenance:
  (a) aqua↔magenta ΔE 6.1 deutan (band 6–8) → **bắt buộc secondary encoding** (2px gap + direct
  label — Gantt/stack đã có theo mark spec); (b) aqua 2.82 / yellow 2.17 / magenta 2.69 **dưới 3:1**
  → relief rule: chart dùng các màu này phải có direct label hoặc table view.
- Sequential cyan 8 step nhạt→đậm (monotonic theo cách dựng); diverging đỏ↔cyan midpoint XÁM.
- Bộ dark validated UPDATE-057 giữ nguyên trong tokens cho dark-map mode.

## 3. Kiểm chứng

- Validator chạy thật 3 lần (candidate fail + chốt adjacent + chốt all-pairs) — log trong hội thoại,
  kết quả tóm tắt vào tokens.provenance.
- JSON hợp lệ: cả 6 file (tokens + 5 contracts) parse được (`json.load` khi commit U2 sẽ có test
  schema tự động — U1 chưa có runner, ghi rõ).
- Visual status: **NOT_APPLICABLE** (chưa có UI render — token/contract/docs; render đầu tiên ở U2).

## 4. Adversarial self-review / flaws found

- **Contract v1.1 chưa được code nào validate** — schema có thể lệch với adapter thật khi viết U2;
  chấp nhận theo trình tự contract-first, test schema là việc ĐẦU TIÊN của U2.
- `journey.income_curve` chọn dạng `[[min, vnd], ...]` (mảng thay vì object) để nhẹ payload replay —
  đánh đổi: kém tự mô tả; đã ghi description trong schema.
- Sequential cyan tự dựng quanh brand thay vì lấy ramp tham chiếu của skill — lý do: "neo quanh
  brand" là chỉ thị; rủi ro: chưa qua validator sequential-specific (skill chỉ yêu cầu monotonicity
  — thỏa theo cách dựng, kiểm mắt ở U3 khi render heatmap).
- Flutter parse v1.1: dựa trên đọc code `driver_state.dart` (fromJson bỏ qua field lạ — Dart map
  access) — CHƯA chạy Flutter thật để xác nhận; ghi vào parity table cho Khánh kiểm khi build.

## 5. Follow-up

U2: hợp nhất env Python (`pyproject.toml` extra `ui`) + test schema + tách demo → `ui/web/` + adapters
data thật + advice endpoint. U3: khu Mô phỏng. U4: verify + **V-10**.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 (sim/dashboard cũ) · **V-09** (dashboard SIM-XANH —
Replay/Hành trình d-41/A-B heatmap) · Q-03 (corpus Khánh thiếu policy 23/02/2026). V-10 sẽ mở ở U4.
