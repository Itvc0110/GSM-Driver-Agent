> ⚠️ **DEFERRED — 2026-07-20.** Tài liệu thuộc cách tiếp cận cũ (full multi-variable constrained optimization). Scope hiện hành: `CLAUDE.md` + `planning/SCOPE.md`. Chỉ dùng tham khảo (xem `tracking/DEFERRED.md`, mục D-001).

# 01 — Product Requirements Document

## 1. Product summary

Driver Income OS hỗ trợ tài xế lập và cập nhật kế hoạch ca nhằm cải thiện thu nhập ròng, giảm thời gian rỗng/chờ/sạc sai thời điểm và kết thúc ca đúng constraint. Sản phẩm chủ động qua dashboard/timeline/cards; lớp hội thoại giải thích và chạy what-if, không thay optimizer.

## 2. Goals

- Cải thiện causal net earnings/hour của nhóm eligible mà không làm xấu total net earnings theo cách không mong muốn.
- Giảm empty km, wait/opportunity loss và bonus pursuit không có lợi.
- Tăng khả năng kết thúc đúng giờ/zone và tuân thủ break/safety.
- Bảo vệ platform service, fleet balance, fairness và driver autonomy.
- Tạo đường thay data mock bằng official adapters mà không đổi domain contract.

## 3. Non-goals MVP

- Dispatch, dynamic pricing, order matching hoặc order acceptance advice.
- Autonomous agent hành động thay tài xế.
- Real-time exact hotspot/reposition recommendation.
- Guaranteed earnings, formal medical/legal advice hoặc driver scoring để kỷ luật.
- Production ML model huấn luyện bằng synthetic data.

## 4. Personas/JTBD

| Persona | Job to be done | Primary objective | Important constraints |
| --- | --- | --- | --- |
| Full-time | Lập ca đủ mục tiêu và thưởng có lợi | total net + stability | break, battery, weekly schedule |
| Part-time | Chọn cửa sổ ngắn hiệu quả | net/hour | hard end time |
| New driver | Tránh quyết định sai rõ ràng | understandable safe plan | low trust/limited history |
| Experienced | So sánh plan cá nhân với baseline | incremental value | high control, familiar zones |
| Family deadline | Kiếm tốt nhưng về đúng giờ | utility under deadline | end time/end zone |
| Stability-first | Tránh downside lớn | lower variance/CVaR | risk preference |

## 5. User journeys

### A. Before shift

Tài xế xác nhận availability, target, end time/zone, risk mode và pin. Hệ thống trả ba plan `Stable/Balanced/Stretch` với range, total time, charging/break, goal probability và risk. Tài xế chọn hoặc sửa constraint.

### B. During shift

State cập nhật sau event quan trọng. Hệ thống chỉ gửi card khi estimated value vượt threshold, còn hiệu lực và không gây notification fatigue. Card có một action chính, hai lựa chọn thay thế/giữ nguyên và explanation.

### C. Charging/break

Khi SOC/time policy hoặc opportunity-cost thay đổi, hệ thống so sánh charge now/later, mức sạc và kết hợp nghỉ. Nếu data trạm stale, chỉ đưa generic safe action, không khẳng định wait time.

### D. Bonus navigator

Hiển thị progress/eligibility và incremental net của tier kế tiếp. Cho phép khuyên “dừng theo tier” nếu extra time/cost/downside lớn hơn expected bonus.

### E. Homeward

Tài xế đặt deadline và end zone làm mờ. Hệ thống ước lượng lúc kích hoạt mode và kế hoạch sạc/nghỉ tương thích. Phase 1 không chọn cuốc hướng về nhà.

### F. Post-shift

Phân rã revenue/bonus/cost/time; so sánh planned vs actual và comparable self-days; chỉ ra tối đa ba drivers of outcome và một change cho ca tới.

## 6. Functional requirements

- `FR-001` Tạo/cập nhật typed driver constraints; explicit constraints cần user confirmation.
- `FR-002` Snapshot state với provenance/freshness/data mode.
- `FR-003` Tạo baseline và candidate plans theo action taxonomy.
- `FR-004` Tối ưu/xếp hạng tối đa ba feasible options; trả solver status.
- `FR-005` Policy gate veto safety/legal/platform violations và ghi reason code.
- `FR-006` Recommendation envelope có range, baseline, expiry, confidence, trade-off, trace/version.
- `FR-007` Accept/ignore/adjust; ignore reason là optional, không punitive.
- `FR-008` What-if chạy lại với constraint mới; không sửa silent state.
- `FR-009` Explanation chỉ dùng structured output/policy source; schema validation bắt buộc.
- `FR-010` Synthetic scenarios deterministic; demo hiển thị nhãn mock.
- `FR-011` Post-shift decomposition có reconciliation với earning ledger.
- `FR-012` Feature flags theo market/service/driver cohort/data mode.
- `FR-013` Audit log cho recommendation/policy/model/data versions, không log PII thô.
- `FR-014` Consent/preferences: view/update/delete; home zone có thể tắt.
- `FR-015` Phase 2 capacity token ngăn oversubscription và hết hạn tự động.

## 7. UX requirements

- Outcome/action trước, lý do sau; không quá ba options.
- Không dùng màu/wording khiến uncertainty trông như guarantee.
- Voice/notification không yêu cầu thao tác khi xe đang di chuyển; deep interaction chỉ khi dừng an toàn.
- Luôn có “Giữ kế hoạch hiện tại”, “Tại sao?”, “Điều chỉnh mục tiêu” và opt-out.
- Hiển thị `Dữ liệu mô phỏng` trong synthetic mode.
- Recommendation có expiry countdown; stale card tự đóng.
- Không so sánh trực tiếp với tài xế khác; benchmark với chính tài xế hoặc cohort đã normalize.

## 8. Non-functional requirements

- `NFR-001` API contract versioned và backward-compatible trong một phase.
- `NFR-002` Phase 1 p95 recommendation compute target là hypothesis phải benchmark; timeout trả fallback, không block app.
- `NFR-003` Reproducible theo input snapshot/model/policy/seed.
- `NFR-004` Availability của explanation không ảnh hưởng availability của recommendation core.
- `NFR-005` Least privilege, encryption, retention, deletion và privacy impact review.
- `NFR-006` Observability end-to-end bằng trace ID.
- `NFR-007` Không có single-point live data failure tạo unsafe advice.
- `NFR-008` Internationalization/timezone/currency/market policy tách config.

## 9. MVP acceptance criteria

1. Với 10 scenario bắt buộc, hệ thống tạo `RecommendationEnvelope` hợp lệ hoặc `NO_RECOMMENDATION` có reason; không crash/hallucinate.
2. Không action nào ngoài enum; không order-level advice xuất hiện trong API hoặc explanation.
3. Mọi hard constraint có invariant test; stale/unknown policy gây veto/fallback.
4. Cùng snapshot, versions và seed cho cùng kết quả (trừ solver metadata không quyết định).
5. Recommendation luôn có baseline, expiry, uncertainty, `data_mode`, trace và version.
6. Synthetic/live isolation và mock labeling được test end-to-end.
7. LLM/explanation không thay numeric fields và không hoạt động nếu tool payload không validate.
8. Post-shift totals reconcile với ledger fixture trong tolerance đã định nghĩa.
9. Feature flag có thể tắt từng action type/cohort và rollback không cần deploy code.
10. Offline report có driver metrics, platform/safety/fairness guardrails; không dùng synthetic result để claim business uplift.

## 10. Release gates

- Prototype: contract + synthetic vertical slice.
- Internal demo: scenario coverage + UX mock + trace/explanation.
- Shadow: official adapter, privacy/security/policy review, data quality SLO.
- Pilot: causal design, operational owner, support/incident/rollback.
- Scale: non-inferiority guardrails, calibration, capacity/fairness, cost/SLO.
