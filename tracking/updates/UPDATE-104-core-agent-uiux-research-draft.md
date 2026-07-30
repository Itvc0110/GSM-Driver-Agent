# UPDATE-104 — Tài liệu nghiên cứu Core Agent và UI/UX presentation-only

- **Ngày:** 2026-07-30
- **Người thực hiện:** AI agent theo yêu cầu của Cường
- **Loại:** research / docs
- **TODO / User story liên quan:** ĐA-06 / T-044 (chỉ tham chiếu; không đổi trạng thái hay implement)

## Tóm tắt

Tạo một tài liệu **RESEARCH DRAFT** về Core Agent và UI/UX đồng nhất về semantics với simulator,
nhưng giữ ranh giới agent không được chạm simulator/dispatch/solver/state. Tài liệu trình bày bằng
chứng code tại `be588244`, các lựa chọn và trade-off; không chốt kiến trúc, không sửa code/contract/UI.

Trước cycle docs này, toàn bộ implementation nhầm ở working tree đã được khôi phục/xóa đúng phạm vi,
sau đó nhánh local được fast-forward từ `c493d89` tới `origin/main` `be588244`.

## Chi tiết cập nhật

- Ghi rõ `RecommendationSpec` chỉ là tên làm việc, không phải contract canonical hiện có.
- So sánh template-only, bounded “Vì sao?” enrich, full-card render và agent tự quyết.
- Nêu Core Agent chỉ có giá trị ở explanation/personalization có kiểm soát; không trực tiếp tạo uplift.
- Thiết kế research choices cho provider portability, structured output và read-only tool allowlist.
- Đề xuất UX hypotheses: progressive disclosure, queue khi lái, card budget, CTA intent, surface parity.
- Khóa conceptual boundary: agent không có cạnh tới `AdviceActionBridge` hay simulator state.
- Tách presentation experiment khỏi per-advice causal attribution và fleet interference/herding.
- Ghi các gate và câu hỏi cần duyệt trước khi có một plan implementation riêng.
- Reviewer read-only kiểm chéo C6/UI/SIM và phát hiện hai gap quan trọng: LLM hiện còn được phép sinh
  `advice_spec`; verifier chưa pin spec này về solver action. Repo cũng chưa có runtime Tool Gateway.

## Files bị ảnh hưởng

| File | Hành động (tạo/sửa/xóa) | Ghi chú |
|---|---|---|
| `research/ux/2026-07-30-core-agent-uiux-research-draft.md` | tạo | artifact nghiên cứu chính; nhãn NOT FINAL/NOT SPEC |
| `research/README.md` | sửa | đăng ký artifact trong index research |
| `tracking/updates/UPDATE-104-core-agent-uiux-research-draft.md` | tạo | ledger theo harness |
| `tracking/PROJECT-GRAPH.md` | sửa | đăng ký UPDATE-104 |

Không có file runtime, schema, test, UI hay simulator trong diff cuối.

## Docs đã cập nhật kèm theo

- `research/README.md`: có.
- `tracking/PROJECT-GRAPH.md`: có.
- `SCOPE`, `TODO`, `DEFERRED`, `USER_STORIES`, `PENDING-REVIEW`: không đổi vì tài liệu không phê duyệt
  feature, không thay task status và không mở implementation.

## Assumptions và evidence

| Claim / tham số | Nhãn | Nguồn / bằng chứng | Confidence | Tác động nếu sai |
|---|---|---|---:|---|
| C6 có template/composer/verifier fail-closed | `OBSERVED-CODE` | `src/gsm_core/advisor/pipeline.py:49-164` | cao | sai nền tái sử dụng |
| UI Web đang dùng S1 adapter riêng | `OBSERVED-CODE` | `ui/backend/app/adapters/advisor.py:1-6`, `318-338` | cao | sai nhận định canonical-path gap |
| LLM còn sinh được `advice_spec` | `OBSERVED-CODE` | `llm_client.py:24-30`, `86-101` | cao | boundary enrich-only có thể đã tồn tại |
| Verifier chưa pin action về solver | `OBSERVED-CODE` | `verifier.py:90-106`, `125-135` | cao | có thể đánh giá quá thấp guardrail |
| SIM bridge làm đổi action/state | `OBSERVED-CODE` | `advice_bridge.py`, `world.py:739-771` | cao | sai ranh giới agent/SIM |
| Tool Gateway runtime chưa có | `OBSERVED-CODE — ABSENT` | targeted negative search + `llm_client.py:86-100` | khá cao | có thể bỏ sót một path ngoài scope tìm kiếm |
| Bounded enrich cải thiện UX | `HYPOTHESIS` | PAIR/NHTSA/web.dev/Apple + code gaps | thấp–trung bình | phải quay về template-only hoặc pattern khác |
| Bốn provider có thể dùng common-minimum contract | `HYPOTHESIS` | official provider docs; chưa chạy API key thật | trung bình | cần contract/provider strategy khác |

## Kiểm chứng

- Xác minh `git ls-remote origin refs/heads/main` = `be588244edff09cca1359d948896ff94f6d57733`.
- `git fetch origin main` + `git merge --ff-only origin/main`: fast-forward thành công.
- Đọc lại `CLAUDE.md`, bootstrap, work queue, graph, assignments, pending review, correction chain và
  các source code C6/UI/SIM tại HEAD mới.
- Reviewer phụ chạy read-only và không sửa file.
- Không chạy unit/integration test vì docs-only và không đổi runtime.
- Chưa chạy provider API/model eval/usability test; mọi claim tương ứng giữ nhãn `HYPOTHESIS`/`UNVERIFIED`.

### Seeds và scenarios

| Command / run | Seed set | Scenario set | Kết quả / artifact | Chưa kiểm chứng |
|---|---|---|---|---|
| Không chạy SIM | N/A | N/A | docs-only | mọi income/causal/business outcome |

## Visual verification

- **Status:** `NOT_APPLICABLE`
- **Cách launch / artifact:** không launch UI; không thay visual/runtime.
- **Seed / scenario đã xem:** N/A.
- **Người review + verdict:** chưa có verdict nội dung nghiên cứu của Cường.
- **Lý do:** artifact Markdown research, không phải meaningful UI/simulator update.

## Adversarial self-review / flaws found

1. “Core Agent” và `RecommendationSpec` có thể bị đọc nhầm là module/contract đã có; tài liệu gắn nhãn
   working term và research draft ở đầu.
2. Structured output có thể tạo an toàn giả; tài liệu tách schema pass khỏi semantic/policy invariant.
3. Official docs chỉ chứng minh capability bề mặt, không chứng minh các model cho cùng behavior.
4. Không chạy live provider/API key; portability còn `UNVERIFIED`.
5. Không chạy UI/SIM; không có claim income, visual parity hay state invariant đã pass.
6. Tài liệu có hướng ưu tiên B/E1 nhưng không được diễn giải thành phê duyệt implementation.
7. Bằng chứng gắn snapshot `be588244`; phải re-audit nếu implementation diễn ra trên main mới.

## Expansion checkpoint (T-039 — bắt buộc sau mỗi phần hoàn thành)

1. **Schema:** có candidate fields cho presentation/explanation, nhưng chưa được phép tạo/sửa schema.
2. **Bài toán tối ưu:** không; Core Agent không mở solver mới và không đổi objective.
3. **Tính năng:** có research hypotheses cho “Vì sao?” enrich và reviewer trace; cần approval gate riêng.

## Follow-up / defer phát sinh

- Không tự thêm TODO/DEFERRED mới. Các dependency hiện hữu ĐA-06/T-044, D-C6-03, V-10/V-18 và
  adherence correction chain vẫn giữ nguyên.
- Bước tiếp theo chỉ là review tài liệu và chọn câu hỏi/gate nghiên cứu; không tự động implement.
