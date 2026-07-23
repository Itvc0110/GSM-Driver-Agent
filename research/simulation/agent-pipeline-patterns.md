# Research — Agent pipeline patterns cho C6 (Composer/Verifier/ContextPack/Router/Memory)

Ngày: 2026-07-23 · Nguồn: research đợt 7 (4 nhánh web + synthesize, nguồn arxiv/docs 2024-2026) · Phục vụ: C6 agent pipeline (Track CORE), bổ sung `llm-advisor-architecture.md`

# BÁO CÁO CHỐT — Research tổng hợp cho C6 (Router + Composer + Verifier + Context Pack + Memory)

Nguồn: 4 nhánh research (grounded composition, verifier architecture, context pack engineering, router/memory). Mapping vào pipeline `specs/core-data-schema-and-advisor-architecture.md` §3–§5. Mọi khuyến nghị kèm confidence; cái gì chưa có bằng chứng trên chính deepseek-v4-flash đều đẩy xuống mục EXP.

---

## 1. TL;DR — Khuyến nghị chốt per-component

### Composer (LLM #1)
- **CHỐT: placeholder-first, không free-gen số.** LLM viết message tiếng Việt nhưng mọi số tài chính là token `{{n1}}`/`[N-id]` tham chiếu `numbers[]` của SolverReport; CODE render số format VN (`45.000đ`) sau khi nhận response. Faithfulness=1.0 trở thành **bất biến cấu trúc** thay vì xác suất + retry. [HIGH — LLM copy số verbatim không có bảo đảm kể cả N nhỏ, arxiv 2601.03640; template-based ít hallucinate hơn free-gen là kết quả nhất quán của văn liệu data-to-text]
- **CHỐT: 1 unified prompt skeleton** (persona + hard rules + output contract + 2–3 few-shot tiếng Việt) + per-feature instruction block do CODE inject theo solver fired. Routing bằng code, không in-prompt routing, không tách nhiều call. Skeleton static byte-identical đứng đầu để ăn DeepSeek prefix-cache (hit rẻ ~10x). [MED cho unified-vs-per-feature — chưa quyết định được từ văn liệu, giữ EXP-002; HIGH cho prefix-cache — docs chính thức DeepSeek]
- **CHỐT tiếng Việt:** temperature 0–0.3; instruction tiếng Anh được, few-shot **bắt buộc** tiếng Việt hoàn chỉnh đúng register tài xế (xưng "anh/chị"); code format toàn bộ số theo locale VN — không bao giờ để LLM format số. [MED — practice chuẩn ngành, chưa có benchmark tiếng Việt riêng]

### Verifier
- **CHỐT: 3 tầng plain code + Pydantic/instructor, KHÔNG thêm framework** (guardrails-ai/NeMo bị loại: validator hub English-centric degrade trên tiếng Việt — arxiv 2410.22153 [HIGH]; Colang quá nặng cho team 2 người).
  1. **Tầng 1 — CODE deterministic, có quyền veto:** numeric regex trên text sau-render + Pydantic schema `advice_spec` + blocklist tiếng Việt tự viết cho 3 category cấm (hứa thu nhập / khuyên đơn cụ thể / thiếu disclaimer) + 2 check rẻ: reject ký tự CJK (language-mixing model gốc Trung) + check diacritics tiếng Việt hợp lệ. Mỗi rule = 1 hàm thuần có ID + test. [HIGH]
  2. **Tầng 2 — LLM-judge advisory, config flag tắt được:** separate prompt/context (self-critique cùng context KHÔNG đáng tin — ICLR 2024 arxiv 2310.01798 [HIGH]); judge chỉ hạ confidence/trigger repair, **không có quyền override code check** (judge nhỏ miss rate đáng kể [MED]).
  3. **Repair — đúng 1 vòng, targeted:** implement check thành Pydantic validator raise ValueError với message cụ thể → dùng cơ chế reask của instructor, `max_retries=1`. Gain lớn nhất ở vòng đầu (Self-Refine [HIGH]). Budget cứng ≤2 LLM call/advice — khớp loop bound "repair ≤1" đã đóng băng trong spec.
- **Veto → template fallback, fail-closed:** sau 1 repair vẫn fail Tầng 1 → REFRAIN, trả template deterministic + log đầy đủ. Veto ngay không repair khi parse fail hẳn hoặc zero số trace được. User luôn nhận advice. [MED–HIGH]

### Context Pack
- **CHỐT format: hybrid Markdown-KV + XML-tag.** Mỗi SolverReport bọc tag riêng (`<solver_report name="..." id="S1">`), numbers[] mỗi số một dòng canonical: `- [N3] muc_tieu_ngay: 450.000 VND (nguồn: solver=earnings_gap, field=daily_target)`. KHÔNG dump nested JSON thô. [MED — Markdown-KV thắng benchmark extraction nhưng chỉ test trên GPT-4.1-nano; format là model-specific, chênh tới 40% → phải A/B trên v4-flash, xem EXP]
- **CHỐT: 1 renderer duy nhất** sinh chuỗi canonical cho CẢ prompt lẫn Verifier regex — prompt và check không bao giờ lệch nhau. Instruction bắt copy verbatim + kèm [N-id] (copy-degree tương quan nghịch hallucination [MED]).
- **CHỐT ordering:** system static đầu tuyệt đối → data blocks → instruction + task ở CUỐI (+~30% theo docs Anthropic [HIGH cho nguyên lý]); thứ tự section deterministic cố định (premise order matters [MED]).
- **CHỐT budget:** tổng pack ≤ ~4K tokens (system 1–1.5K; mỗi solver section 200–500). Không lợi dụng 1M context — model 13B-activated. [MED — practice, không có degradation curve chính thức cho v4-flash]

### Router
- **CHỐT: direct mapping, zero ML.** Feature đã biết từ UI trigger → structured field → solver set. Free-text: layer keyword/rule tiếng Việt per-feature (dict + regex viết tay, fixture test); không match → out-of-taxonomy fallback template (R5), không đoán. [MED–HIGH — nguồn ngành thống nhất <15 intents không cần classifier]
- **CHƯA thêm** embedding layer (semantic-router/aurelio-labs, threshold ~0.7) — chỉ mở khi đo được free-text share tăng và keyword precision tụt. LLM router chỉ khi có query compositional thật. Router log route + confidence. [HIGH cho quyết định defer]

### Memory
- **CHỐT: exact-key cache, TUYỆT ĐỐI KHÔNG semantic cache** cho advice (false-positive risk mâu thuẫn trực tiếp faithfulness=1.0; financial advice là anti-pattern của semantic cache [MED–HIGH]). Key = `hash(driver_id + state_digest + policy_version + solver_version + prompt_version + model_id)`; invalidation = versioned keys + TTL 6–24h + purge endpoint. [HIGH cho versioned-key pattern]
- **CHỐT: episode store v1 = 1 bảng SQLite append-only** (episode_id, driver_id, ts, state_digest, solver_reports ref, advice_spec, composed_advice, confidence, route_taken, shown/accepted/outcome nullable) — đồng thời là DecisionRecord/audit trail đã có trong spec §3. [HIGH]
- **CHỐT: trust/adherence v1 = simple counters + EMA** per (driver, advice_type). **KHÔNG contextual bandit v1** (option ít, feedback thưa; bandit tự chọn advice đụng ranh giới "agent không tự thực thi" CLAUDE.md §5 — cần plan riêng nếu mở). Nhưng schema log **bandit-compatible ngay** (context, action, propensity=1.0, reward) để v2 chỉ đọc lại log. [MED]

---

## 2. Bảng findings chính có nguồn

| # | Finding | Nguồn | Conf | Hệ quả thiết kế |
|---|---|---|---|---|
| 1 | LLM copy số verbatim sụp từ ~63%→~7% khi N tăng; N nhỏ đa số perfect nhưng không bảo đảm | arxiv 2601.03640 | HIGH | Placeholder-first, code render số |
| 2 | Template/slot-filling ít hallucinate hơn free-gen; số là token dễ sai nhất | arxiv 1910.08684, 2401.01313 | HIGH | Giữ regex verifier làm lớp hai sau render |
| 3 | "Plan trước, sinh sau" (spec → prose) giảm hallucination + attribution tự nhiên | arxiv 2403.17104 (ACL 2024) | HIGH | `advice_spec` sinh trước, message sinh sau |
| 4 | Self-correction nội tại không đáng tin, có thể làm performance GIẢM; chỉ hiệu quả khi feedback từ tool ngoài | arxiv 2310.01798, 2305.11738 (ICLR 2024) | HIGH | Code check là verdict; judge tách context, advisory-only |
| 5 | Guardrail off-the-shelf degrade trên non-English (gồm tiếng Việt) | arxiv 2410.22153 | HIGH | Tự viết blocklist/rubric tiếng Việt, không dùng validator hub |
| 6 | Targeted repair (lỗi cụ thể) >> blind regenerate; gain tập trung vòng đầu | arxiv 2303.17651 (Self-Refine) | HIGH | 1 vòng reask qua instructor, error message có rule ID + span |
| 7 | Instructor reask = đúng pattern targeted-repair, miễn phí qua Pydantic validator | python.useinstructor.com/concepts/reask_validation | HIGH | Không code repair loop riêng |
| 8 | Format prompt chênh tới 40% giữa model, không có format tối ưu phổ quát | arxiv 2411.10541 (Microsoft) | HIGH | Bắt buộc A/B trên chính v4-flash |
| 9 | Markdown-KV thắng extraction (60.7% vs JSON 52.3%) nhưng chỉ test GPT-4.1-nano | improvingagents.com | MED | Markdown-KV là default, chờ A/B confirm |
| 10 | Data trước, instruction cuối (+~30%); lost-in-the-middle thật nhưng yếu với pack <4–8K | docs Anthropic; arxiv 2307.03172 (TACL 2024) | HIGH | Ordering + budget ≤4K |
| 11 | DeepSeek prefix-cache từ token 0, hit rẻ ~10x, cần prefix byte-identical | api-docs.deepseek.com/guides/kv_cache | HIGH | System static tuyệt đối; verify qua `prompt_cache_hit_tokens` trên proxy ai-box.vn |
| 12 | Model gốc Trung có language-mixing (chèn CJK) nonzero risk | arxiv 2507.15849 | MED | Check CJK + diacritics trong Tầng 1 |
| 13 | Locale số VN (45.000đ vs 45,000) là bẫy regex — pass nhầm đảo nghĩa | practice | HIGH | Code kiểm soát format, canonicalize trước khi so |
| 14 | <15 intents không cần classifier; embedding router chỉ đáng khi taxonomy free-text lớn | tianpan.co (intent routers) | MED | Direct mapping + keyword; defer semantic-router |
| 15 | Semantic cache: FP risk + hit rate thực 20–45%; financial advice không nên semantic-cache | buildmvpfast.com, dev.to | MED | Exact-key cache only |
| 16 | Bandit là overkill khi option ít + feedback thưa; "log first, learn later" là practice chuẩn | geteppo.com, applyingml.com | MED | Counters v1, log schema bandit-compatible |
| 17 | Không tồn tại benchmark công khai nào cho deepseek-v4-flash (format/extraction/tiếng Việt) | practice | HIGH | Mọi lựa chọn model-specific phải qua EXP; sanity-check SEA-HELM leaderboard |

---

## 3. Những gì VẪN PHẢI EXP (nối EXP-001..005 spec §5)

| EXP | Trạng thái sau research | Việc còn lại |
|---|---|---|
| **EXP-001** (Verifier: LLM #2 vs rule-only) | **Thu hẹp đáng kể**: research chốt rule-code là verdict bắt buộc, LLM-judge chỉ advisory. EXP-001 giờ đo: judge advisory bật/tắt có bắt thêm bao nhiêu paraphrase violation so với chi phí +1 call | Chạy trên instrumentation C6; đo thêm false-positive rate Tầng 1 (target <~2.5%, hiện là ASSUMPTION) |
| **EXP-002** (1 prompt chung vs per-feature) | **Thu hẹp**: văn liệu nói single-task không nhất quán thắng multitask (MED) — research chốt unified skeleton + injected block làm default. EXP-002 giờ là confirm: quality per-F của unified-injected có tụt so với per-feature thuần không | Giữ nguyên metric (quality per F, token cost); thêm đo cache-hit ratio giữa 2 biến thể |
| **EXP-003** (demand forecast S2) | Ngoài phạm vi 4 nhánh research này | Không đổi |
| **EXP-004** (pack: full 4 reports vs relevant-only) | **Củng cố**: lost-in-the-middle + model 13B-activated ủng hộ relevant-only + budget ≤4K, nhưng chưa có số cho v4-flash | Giữ nguyên; chạy với format đã chốt ở EXP-006 |
| **EXP-005** (model fallback khi 403) | Không đổi; lưu ý format tối ưu là model-specific → khi gpt-4o-mini mở, phải re-run EXP-006 cho model đó | Không đổi |
| **EXP-006 (MỚI, đề xuất)** — Input format micro-benchmark trên chính deepseek-v4-flash: Markdown-KV+XML vs YAML vs JSON blob, 30–50 câu extraction + 20–30 case eval faithfulness | Bắt buộc vì zero benchmark công khai cho v4-flash; chặn trước khi khóa formatter | ~nửa ngày công; chạy TRƯỚC khi đóng băng pack format; kèm verify `prompt_cache_hit_tokens` qua ai-box.vn |
| **EXP-007 (MỚI, đề xuất)** — Precision/recall blocklist tiếng Việt Tầng 1 trên test set vi phạm tự build từ log | Không có benchmark công khai cho use case này; mọi số precision hiện là ASSUMPTION | Build dần từ JSONL verdict log của C6; regression suite |

Đề xuất: thêm EXP-006/007 vào bảng §5 của spec khi làm C6 (cần plan mode + duyệt, ngoài phạm vi báo cáo này).

---

## 4. Risks

1. **Extrapolation risk (cao nhất):** toàn bộ finding về format/extraction đến từ model KHÁC (GPT-4.1-nano, GPT-3.5/4) — v4-flash chưa có benchmark công khai nào. Mitigation: EXP-006 trước khi khóa; formatter tách khỏi pack-builder để đổi format không đụng structure. [HIGH confidence rằng risk này thật]
2. **Chất lượng tiếng Việt của v4-flash chưa được kiểm chứng** — tiếng Việt là low-resource; SEA-HELM chỉ là sanity-check gián tiếp. Nếu register tài xế không đạt, chi phí chuyển model kéo theo re-run EXP-006. [MED]
3. **Proxy ai-box.vn có thể phá prefix-cache** (inject header/prefix) → mất lợi ích 10x cost. Phải verify field usage thực tế ngay lần call đầu; nếu cache không hit, cost model của unified-prompt thay đổi. [MED]
4. **Placeholder-first có thể làm văn cứng** — LLM viết quanh `{{n1}}` đôi khi thiếu tự nhiên. Mitigation: few-shot chất lượng cao có placeholder mẫu; nếu quality tụt, fallback là free-gen số + canonicalize-both-sides (đã có sẵn regex lớp hai) — nhưng khi đó faithfulness quay lại là xác suất. [MED]
5. **Blocklist tiếng Việt recall thấp với paraphrase** ("chắc chắn kiếm được" viết lệch) — judge advisory bù nhưng judge tắt được theo config; khi judge off, recall vi phạm phi-số giảm mà không có cảnh báo. Mitigation: EXP-007 + log verdict JSONL từ ngày đầu. [MED]
6. **False-positive Tầng 1 chưa đo** — siết rule quá tay → veto oan → user nhận toàn template, mất giá trị LLM. Target <~2.5% là số mượn từ practice ngành, gắn nhãn ASSUMPTION. [MED]
7. **Scope-boundary risk (memory):** counters/EMA hiển thị cho tài xế phải đi qua đúng ranh giới "số-có-nguồn" CLAUDE.md §5; và mọi đường lên bandit v2 đụng "agent không tự thực thi" — phải plan mode riêng, không tự mở. [HIGH]

Files liên quan: `C:\Users\Cuong\OneDrive - Hanoi University of Science and Technology\Documents\GitHub\My\GSM-Driver-Agent\specs\core-data-schema-and-advisor-architecture.md` (§3 pipeline, §5 bảng EXP-001..005, §6 metrics).