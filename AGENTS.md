# Instructions for AI Coding Agents

## Mission

Xây dựng Driver Income OS như một hệ thống hỗ trợ quyết định an toàn, có thể kiểm chứng và thay thế được mock data bằng dữ liệu thật. Không tối ưu demo bằng cách làm suy yếu ranh giới với dispatch, safety hoặc platform guardrails.

## Source of truth

Khi có xung đột, ưu tiên theo thứ tự: policy/compliance đã phê duyệt → contract version hiện hành → PHASE đang active → SPEC/PRD → MEMORY → code comments. Nếu xung đột chưa giải được, ghi `BLOCKER-*`; không âm thầm chọn một hành vi có tác động sản phẩm.

## Quy trình bắt buộc

1. Đọc `README.md`, tài liệu liên quan và `templates/MEMORY.md`; sau đó mới khảo sát code hiện hữu.
2. Trước khi code, tạo/cập nhật `PHASE-###-<slug>.md` từ template, nêu assumption, scope, contract, acceptance criteria và test plan.
3. Nếu sửa lỗi, tạo `FIX-###-<slug>.md`; phải có reproduction, root cause, regression test và phạm vi ảnh hưởng.
4. Thực hiện lát cắt nhỏ nhất end-to-end. Không tạo microservice chỉ để tách folder.
5. Sau thay đổi, chạy test phù hợp, cập nhật docs và MEMORY; ghi rõ việc chưa kiểm chứng.
6. Không xóa/chỉnh thay đổi không liên quan của người khác. Không đổi schema dùng chung nếu chưa bump version và có compatibility test.

## Ranh giới kiến trúc không được phá

- LLM không được tính tiền, giải bài toán tối ưu, tự tạo số liệu, bypass policy gate hoặc trực tiếp ghi state vận hành.
- Mọi số hiển thị cho tài xế phải đến từ `RecommendationEnvelope`/tool output có version và trace.
- Optimizer không quyết định nhận/từ chối/hủy cuốc; không thay thế dispatch.
- Phase 0–1 không phát recommendation reposition theo hotspot cụ thể. Phase 2 chỉ cho phép khi fleet capacity và network guardrails hoạt động.
- Safety/legal/platform constraints là hard constraints hoặc veto ở policy gate; không biến thành penalty có thể “mua” bằng doanh thu.
- Nếu forecast stale, solver infeasible/timeout hoặc policy không khả dụng, trả fallback an toàn; không bịa phương án.

## Quy tắc dữ liệu

- Dùng adapter theo interface; domain không import trực tiếp SDK nguồn dữ liệu.
- Mỗi event có `event_time`, `ingested_at`, `source`, `schema_version`, `data_mode`, `is_mock`, quality/freshness.
- Không trộn synthetic và live trong cùng một evaluation run.
- Mock generator phải deterministic theo seed, có scenario ID và cover normal/adverse/edge cases.
- PII tối thiểu hóa; dùng zone/geofence thay cho địa chỉ nhà; không log tọa độ thô hoặc nội dung chat chứa PII.

## Quy tắc optimizer và recommendation

- Tách forecast, candidate generation, optimization, policy và explanation để có thể test độc lập.
- Lưu solver status, time limit, objective components, constraints binding và model versions.
- Tạo baseline `do_nothing/current_plan`; mọi lợi ích là delta so với baseline với khoảng bất định.
- Tối đa ba phương án không bị dominated; một phương án recommended chỉ khi vượt minimum-value và confidence gate.
- Recommendation phải có expiry, confidence/calibration band, trade-off, data freshness và lý do policy.
- Hành vi người dùng là tự nguyện; accept/ignore không được coi là “vâng lời” hoặc dùng để trừng phạt.

## Tách việc cho hai developer

- Dev A sở hữu `domain`, `data`, `forecasting`, `optimization`, `simulator`, offline evaluation.
- Dev B sở hữu `api`, `recommendation`, `policy`, `explanation`, integration/UI contract, observability.
- Hai bên chỉ tích hợp qua JSON Schema/OpenAPI, fixtures và contract tests. Không import module nội bộ chéo qua boundary đã nêu.

## Quality gates tối thiểu

- Format/lint/type check; unit + property + contract tests.
- Schema backward compatibility; synthetic/live isolation test.
- Solver feasibility, hard-constraint invariant, deterministic seed và timeout fallback.
- Golden recommendation tests; prompt/tool injection tests cho explanation layer.
- Offline scenario evaluation; platform/safety/fairness non-regression.
- Migration, feature flag, canary/shadow plan và rollback đã kiểm chứng trước live.

## Cách giao tiếp

Nêu outcome trước. Phân biệt rõ `FACT`, `ASSUMPTION`, `HYPOTHESIS`, `DECISION`, `BLOCKER`. Không gọi prototype là production-ready và không dùng kết quả synthetic để tuyên bố uplift thật.
