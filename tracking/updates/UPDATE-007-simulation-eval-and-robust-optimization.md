# UPDATE-007 — Mở rộng bài toán: giả lập twin-world, adherence, robust optimization, timing/memory

- **Ngày:** 2026-07-21
- **Người thực hiện:** AI agent (Claude Code), theo 6 yêu cầu mới của Cường (session 2026-07-21)
- **Loại:** research / spec / scope-extension
- **TODO / User story liên quan:** T-016 (DONE), T-017…T-021 (mới), SCOPE §5b (mới), D-004 (nới cho sim)

## Tóm tắt

Cường nêu 6 khoảng trống: (1) chưa đo được hiệu quả gợi ý trong giả lập khu vực thật nhiều tài xế + dispatcher có sẵn; (2) chưa có thiết kế đo tài xế có tuân theo lời khuyên không (kể cả tự làm đúng nhờ kinh nghiệm); (3) tối ưu hóa phải robust khi biến chưa chốt (biến bền vững → optimization, còn lại → reasoning) + kiểm tra luồng tuân thủ; (4) khung thời gian gợi ý/cập nhật state + biến nào persistent vs session; (5) thiếu supply field/trạm sạc → rủi ro herding "cả làng cùng đi sạc"; (6) thiết kế giả lập quan trọng ngang bài toán tối ưu, cần nhiều actor đa dạng hơn, chạy trên H3. Session này: research đợt 3 (3 agent web) + 2 spec thiết kế mới + đồng bộ SCOPE/TODO/DEFERRED.

## Chi tiết cập nhật

### Research đợt 3 (`research/simulation/` — folder mới)

1. **tooling.md**: chốt stack đề xuất — SimPy + h3-py v4 (res 8) + parquet/DuckDB (có H3 extension) + Streamlit/Plotly dashboard + kepler.gl replay (time playback, export HTML) + tracking bằng manifest/parquet (MLflow local là phương án phụ). Không simulator có sẵn nào dùng ngay; tham khảo kiến trúc tomslee/ridehail + FleetPy. pydeck không cần API key (Carto default); kepler.gl né Mapbox token bằng CARTO/OSM basemap.
2. **evaluation-methodology.md**: twin-world cùng seed = chuẩn **Common Random Numbers / paired-seed** (giảm >10× số run); RNG tách stream; paired t-test/bootstrap trên hiệu số theo seed (20–30 seeds, sequential tối đa 100); vì sao driver-level A/B sai trong ride-hailing (interference) và twin-world né được; taxonomy adherence 5 nhãn (Explicit/Coincident/Partial/None/Contrary) map vào principal strata, **twin-diff attribution** tách "làm theo lời khuyên" khỏi "đằng nào cũng làm"; metrics bổ sung (income SD, tổng payout hệ, envy, advised-vs-non khi adoption <100%); anti-herding có văn liệu (capacity-aware allocation/min-cost flow, tokens, staggering, power-of-two-choices).
3. **world-parameters.md**: **144 trạm đổi pin VinFast thật từ OSM** (tag battery_swap=yes, capacity=6) + tham số trạm (6 khe, đổi ~90s, sạc lại 1,5–2h/viên); tốc độ bike theo giờ (17/25/30 km/h), cuốc lognormal ~3,5 km, pin swap ~55–70 km/pack; dispatcher baseline batched-Hungarian trong grid_disk k=2 (pseudocode); quy mô đề xuất N=500 drivers, 8–12k đơn/ngày, ~407 cells res 8, 24h/run.

### Spec mới (`specs/`)

4. **simulation-twin-world.md**: kiến trúc 2 arm cùng seed (shared demand/dispatcher/policy; chỉ khác advice); metrics 3 tầng driver/system/fairness; 5 persona → archetype templates sample N=300–500 actors có jitter + behavior model bản năng (sinh coincident compliance); advisor-sim với **capacity ledger + staggering + marginal value** chống herding (trả lời #5); adherence đo bằng twin-diff (trả lời #2); viz 3 lớp (kepler replay + Streamlit dashboard + tracking); 7 kịch bản đánh giá (gồm stress herding, adoption từng phần); bảng .env sẽ xin Cường (MAPBOX_TOKEN optional, LLM key chưa cần).
5. **advice-timing-state-memory.md**: (trả lời #3, #4) — trigger **HYBRID** (event-driven theo cuốc/SOC + fixed anchors đầu ca/khung thưởng/giữa trưa + threshold-crossing) với cooldown 20ph/chủ đề + budget ≤6 advice/ca; rolling window bucket 30ph chỉ trình bày hành động kế tiếp; **phân lớp biến A/B/C** (A bền vững → bài toán tối ưu đa biến ràng buộc; B bán bền vững → feature flag `available_this_session`; C bất định → reasoning có guardrail) + quy trình thăng/giáng cấp biến không phá cấu trúc bài toán; tách **persistent memory** (hồ sơ hành vi, pattern sạc, lịch sử adherence/trust, rolling 4–8 tuần, cell làm mờ) vs **session state** (SOC, lũy kế, advice đang hiệu lực, cờ lớp B) + luồng feed/inject bằng immutable snapshot.
6. **Kiểm tra tuân thủ #3**: flow v2 + SCOPE đã đúng *nguyên tắc* (số từ rule, reasoning có guardrail) nhưng THIẾU phân lớp biến tường minh, feature-flag, trigger/cooldown, persistent-vs-session — 4 phần này là đóng góp mới, đã ghi rõ trong spec §2.

### Đồng bộ docs

- `planning/SCOPE.md`: thêm §5b (6 yêu cầu → nơi phản ánh).
- `tracking/DEFERRED.md`: D-004 nới **cho phạm vi sim** (fleet-awareness/anti-herding trong simulator OK; product vẫn không reposition).
- `tracking/TODO.md`: T-016 DONE; thêm T-017…T-021 (review spec → build sim core → advisor-sim → evaluator/dashboard → calibration).
- `research/README.md`, `CLAUDE.md`: bản đồ repo thêm `research/simulation/` + specs mới.

## Files bị ảnh hưởng

| File | Hành động |
| --- | --- |
| research/simulation/tooling.md · evaluation-methodology.md · world-parameters.md | tạo |
| specs/simulation-twin-world.md · specs/advice-timing-state-memory.md | tạo |
| planning/SCOPE.md (§5b) · tracking/DEFERRED.md (D-004) · tracking/TODO.md (T-016…T-021) · research/README.md · CLAUDE.md | sửa |
| tracking/updates/UPDATE-007-...md | tạo |

## Kiểm chứng

- Nguồn research: 3 agent web độc lập, URL kiểm chứng từng claim; OSM query chạy thật (144 node). CHƯA kiểm chứng: 2 paper CRN mới đọc abstract; hiệu năng pydeck-trong-Streamlit; số trạm thực tế ngoài OSM (undercount đã ghi).
- Spec là thiết kế, chưa có code chạy. Các quyết định thiết kế chờ Cường/Khánh review (T-017).
- Đầu session: xác nhận Cường đã tự commit/merge checkpoint (baa9e62) — làm việc trên main sạch.

## Follow-up / defer phát sinh

- **T-017 (cần Cường)**: review hybrid trigger + cooldown defaults; ranh giới lớp A/B/C; archetype mix; adoption scenarios; arm C placebo có cần không.
- **.env khi build**: `MAPBOX_TOKEN` (optional), `MLFLOW_TRACKING_URI` (optional); LLM key chưa cần (advisor-sim v1 rule-based).
- T-009 (UI clone) vẫn chờ theo thứ tự Cường điều phối.
