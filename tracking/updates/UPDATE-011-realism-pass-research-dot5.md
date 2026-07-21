# UPDATE-011 — Realism pass + calibration vòng 1 + research đợt 5 (advisor arch) + dashboard

- **Ngày:** 2026-07-21
- **Người thực hiện:** AI agent, dưới claim T-018/T-024/T-025 của Cường
- **Loại:** research / code (calibration) / infra
- **TODO liên quan:** T-024 DONE, T-025 DONE (research), T-028 DONE (dashboard), T-021 vòng 1, T-019 tiếp theo

## Tóm tắt

Theo 3 yêu cầu Cường: (0) sắp xếp lại TODO theo độ quan trọng + track song song; (1) research realism → đối chiếu + chỉnh mock; (2) research kiến trúc advisor LLM + observability; (3) dashboard xem/control sim. Đã: 2 research file + dashboard Streamlit + realism pass (sửa 1 bug accounting + 3 điểm behavior) + calibration vòng 1 với kết luận thiết kế quan trọng.

## Chi tiết

### Research đợt 5 (2 file `research/simulation/`)

- **realism-benchmarks.md** (T-024): đối chiếu 10 tham số sim với benchmark thực tế có nguồn. Phát hiện: patience 90s thổi phồng unserved; target 15-20% đúng cho hệ cung cố định không surge; sim thiếu lớp thưởng trong payout. **Kết luận calibration vòng 1** (sau khi áp): baseline B unserved ~34%/util ~38% là **mismatch không gian + swap herding** — feature làm dư địa cho advisor, KHÔNG ép về 15-20% (đó là target arm A).
- **llm-advisor-architecture.md** (T-025): CHỐT kiến trúc "spec-first, LLM-offline, deterministic replay" (KHÔNG gọi LLM realtime trong sim loop — phá CRN + chậm); DP tạo advice spec → adherence đọc spec → LLM chỉ render text/reasoning batch sau. Stack: openai SDK + instructor + fallback 4 tầng (SDK retry → instructor → gpt-4o-mini → template). Observability: **Langfuse chính** (Cloud Hobby 50k obs) / **Phoenix thay thế** (1 container local). Bảng metric per-layer (trigger/DP/LLM/guardrail số/adherence). Multi-map: same-map + domain randomization đủ cho robustness; map 2 chỉ khi external validity.

### Code — realism pass + calibration vòng 1

- **Bug fix (quan trọng)**: `online_min` accounting sai (reset `last` trong nhánh action → mất thời gian chờ/serve) → utilization giả 72%. Sửa: tách `occupied/empty/idle/rest/charge_min`; util = occupied/(online−rest−charge). Số thật: util FT 38%, online 9.7h.
- **Patience 2 tầng**: đổi `order_expire_s: 90` cứng → patience per-order lognormal median 3ph cap 10ph (exogenous, CRN-safe) trong Order.
- **Day-bonus**: cộng thưởng ngày (rule component) vào payout cuối ca — realism: thưởng chiếm 20-30% thu nhập.
- **Demand-hint**: bật "kinh nghiệm cá nhân" của actor (demand field từ trace × nhiễu σ_arch) cho relocate — nền coincident compliance (behavior §1).
- **Metrics mới**: utilization, pickup ETA p50/p90, swap wait p50/p90/max.
- Chẩn đoán bằng sweep (ring, demand/supply): xác nhận không phải thiếu tầm dispatcher/thiếu cung tổng mà là mismatch không gian + herding.

### Infra

- **Dashboard** `src/gsm_sim/dashboard.py` (T-028): Streamlit + pydeck H3 map + control levers; `uv run --extra viz streamlit run ...`; healthz 200.
- **.env** (Cường cung cấp) + `.env.example` + gitignore secrets. `scripts/smoke_llm_endpoint.py`: verify endpoint ai-box.vn.
- pyproject: extra `[viz]`.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| research/simulation/realism-benchmarks.md, llm-advisor-architecture.md | tạo |
| src/gsm_sim/{world,entities,metrics,cli,demand}.py | sửa (accounting, patience, day-bonus, demand-hint, metrics) |
| src/gsm_sim/dashboard.py | tạo |
| configs/pilot_dongda.yaml | sửa (patience, wait_cap) |
| scripts/smoke_llm_endpoint.py, .env.example | tạo |
| .gitignore (secrets), pyproject.toml ([viz]) | sửa |
| tracking/TODO.md (sắp xếp lại + T-024/025/028) | sửa |

## Kiểm chứng

- pytest **29/29** sau mọi thay đổi.
- Smoke test endpoint: deepseek-v4-flash chat + JSON mode + provider cache hit (512 tok) **OK**; **gpt-4o-mini 403** (token chưa có quyền — cần Cường xin quyền hoặc đổi fallback); JSON mode cần max_tokens lớn (thinking mode ăn reasoning tokens trước content).
- Dashboard boot headless healthz 200.
- CHƯA đạt: unserved chưa về 15-20% cho arm B — **cố ý** (là dư địa advisor, không phải gate của B). Tinh chỉnh nhỏ (swap rời trạm theo pin-availability, nghỉ trưa FT, σ demand-hint) để vòng sau.

## Follow-up

- **Cường cần quyết**: (a) xin quyền gpt-4o-mini trên token ai-box.vn HAY đổi fallback sang model khác aggregator hỗ trợ; (b) xác nhận kết luận "baseline B chưa tối ưu là feature".
- **T-019 tiếp theo**: viết `specs/advisor-system-detail.md` rồi build DP lớp A + LLM render + Langfuse — theo kiến trúc đã chốt.
- Bảo mật: API key đã lưu local (gitignore), Cường cân nhắc rotate sau dự án.
