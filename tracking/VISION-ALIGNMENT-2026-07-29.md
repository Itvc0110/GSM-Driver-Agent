# VISION-ALIGNMENT — đối chiếu tầm nhìn Cường ↔ kiến trúc hiện tại (2026-07-29)

> Tầm nhìn do Cường nêu nguyên văn (goal phiên 2026-07-28, nhắc lại 2026-07-29). File này
> là **bản đối chiếu có bằng chứng**: từng vế → cái đã có (kèm đường dẫn) → gap → route.
> Đây là tài liệu NEO cho mọi plan mới: plan nào không trỏ được về một vế ở đây thì phải
> tự hỏi vì sao tồn tại. Cập nhật khi trạng thái đổi; không viết lại lời của Cường.

## A. Vế PRODUCTION (phần mềm cuối chạy thật)

| # | Vế tầm nhìn (tóm tắt trung thực) | Đã có | Gap + route |
|---|---|---|---|
| A1 | **Data thật, state tài xế cập nhật liên tục vào database**; policy plain text; state chưa rõ dtype (vd pin) từ hệ sinh thái Vingroup/GSM; output API ngoài phải **normalize về đúng dạng** | Lifecycle store (ĐA-05, UPDATE-091) là bước đầu của mạch "state → database": append-only, validate + **parse thật tại boundary** (`event_log.append`: lịch thật, offset bắt buộc, numpy normalize — chính là tiền lệ normalize-hoặc-fail-loud cho dtype lạ). Registry đa phiên bản (UPDATE-090) cho phép data cũ/mới sống chung. Policy plain text: corpus T-004 + `PolicyKB`; số policy đi qua `policy_bundle` versioned có `effective_from/to` | Lớp ingest/datasource **chưa tồn tại** (`src/gsm_core/datasource/` = 0 file) — plan sẵn ở `specs/real-data/04-datapull-tool-plan.md`, defer CHỦ Ý (D-GCP-01: publish chạy mock, quyết định Cường 24/07). Finding sống sót UPDATE-092: `format_checker` (15 schema `format:` vô hiệu) — fix qua plan mode. "Chưa kiểm chứng output nếu lấy thật từ API key" = gap Cường tự nêu và chấp nhận |
| A2 | **Không ảnh hưởng hệ thống có sẵn** (dispatching…) | Ranh giới cứng `CLAUDE.md §5`: không can thiệp matching/dispatch/pricing/routing, không khuyên nhận/từ chối đơn cụ thể; advisor chỉ khuyên vị trí/thời gian/nghỉ. Dispatcher trong sim là **mô phỏng để đo**, không phải thiết kế can thiệp | Giữ nguyên làm bất biến; mọi kênh advice mới phải qua kiểm ranh giới này (đã thành mục trong adversarial self-review §4b) |
| A3 | Tài xế thật **part-time, random hơn** sim | PoA đo với adherence thực 0,30–0,75 (UPDATE-088) — tức "không nghe lời" đã trong mô hình đánh giá; behavior sim có impatience/fatigue/patience 2 tầng | Persistence hành vi đa ngày (ngày nghỉ/thói quen) = D-SIM-16 DEFERRED; nhân quả từng lượt advice + counterfactual ngắn = REVIEW-092-1/2 (UPDATE-092, nhận xét #1/#2 của Cường **vẫn đúng nguyên vẹn** — phần ước lượng chưa có dòng code nào) |
| A4 | **Mất mát lớn nếu làm ẩu** (ai cũng ra điểm đông / sạc cùng lúc) | 3 tầng chống herding có code thật (UPDATE-092 §1.1 verify độc lập): capacity_left lọc ô, `pending_targets` tính cung-đang-tới ngay, Hungarian bỏ advice khi dư. Bằng chứng định lượng: heatmap ngây thơ γ=0 **không hội tụ và tệ vĩnh viễn** (UPDATE-088) — đúng kiểu "nghe hợp lý mà tự phá" của vế này; bẫy free-rider 25–50% đã ghi | Mọi kênh mới PHẢI đo ở `coverage: all` + chỉ tiêu kép ĐA-08 (1a+1b) trước khi bật — đã thành quy trình |
| A5 | **Hàm tối ưu đủ biến, cập nhật giá trị theo policy — HOẶC agent chọn hàm/giá trị biến theo policy** | Đường đi đã duyệt `tracking/PLAN-cycle-wx-2026-07-29.md` Phần B: B1 `net_mean_all` ✅ (`8fc02ba` — thước thấy chi phí TRƯỚC khi solver có chi phí) → B2 C1 hệ số 0 → B3 `resolve_cost_params(policy, track, as_of)` 3 trạng thái ACTIVE/OFF_BY_POLICY/UNKNOWN + `terms_active[]` trong SolverReport. Ý A1-agent-router của Cường: ghi ở `OPEN-THREADS` §A1 — agent chọn **bài toán/biến sống**, KHÔNG chọn giá trị tiền (ranh giới §5 nguyên vẹn) | B2/B3 chưa code (cần đo 30–100 seed); agent-as-router là cycle SAU B3 (cần `CostParams` + `net_mean_all` tồn tại để chấm điểm); mốc policy thật: pin miễn phí tới 31/03/2029 (official) đã vào docs, chưa vào `policy_bundle.costs` |

## B. Vế SIM (thế giới đánh giá)

| # | Vế | Đã có | Gap |
|---|---|---|---|
| B1 | Hồ sơ hạn chế, khu vực hạn chế, **full-time, kiếm max** | 7 archetype (PERSONAS đã tách: 5 persona product / 7 archetype sim), 90 actor, 1 quận Đống Đa res 9 — đúng chủ ý "đủ sát để đo" | Quy mô thành phố (res 8/N=500) DEFER có chủ ý (D-SIM-01/D-010) |
| B2 | **Thời gian rời rạc, sát thực tế** | tick 2′, bucket 30/60′; 3 time bug đã vá + mutation-proof (UPDATE-083) | — |
| B3 | **KHÔNG agent trong luồng sim; output solver = action; behavior random cho thế giới kia — engineer kỹ** | `advice_bridge`: solver output → `mapped_action` trực tiếp, KHÔNG LLM; arm A = behavior thuần; CRN paired để bật advice không dịch RNG (test canh); sim chốt không gọi LLM live | Arm C placebo **chưa có** (nợ duy nhất của bộ 3 arm — specs đã ghi rõ) |
| B4 | Structured data **y hệt thật**; state ở RAM chấp nhận được | 13 bảng l1r mirror schema GSM thật; `Event.run_id` + export → lifecycle store là cầu RAM→DB đúng chốt "sim để RAM chỉ thêm run_id" | Gap API thật = A1 |
| B5 | Sim **visualize đẹp, dễ hiểu, observation cho từng feature** | Dashboard Streamlit + khu Mô phỏng web (Replay/Hành trình/A/B/Độ nhạy); V-01..V-17 chờ verdict Cường | W6: khu Mô phỏng đọc projection lifecycle (visual gate, cycle riêng); B6-PARITY (UPDATE-092): UI ship 1 solver ≠ hệ được đo 5 kênh/9 solver — **chờ Cường xếp ưu tiên** |

## C. Ba việc kế tiếp bám tầm nhìn (thứ tự đề xuất)

1. **B2→B3 của PLAN-cycle-wx** (vế A5 — "hàm tối ưu cập nhật theo policy" có bằng chứng đo được: kịch bản as_of>2029-03-31 phải đổi lời khuyên).
2. **B6-PARITY** (vế B5 + A2 — thứ được đo phải là thứ được ship) — cần verdict ưu tiên của Cường.
3. **format_checker** (vế A1 — boundary validate thật) — plan mode, nhỏ.
