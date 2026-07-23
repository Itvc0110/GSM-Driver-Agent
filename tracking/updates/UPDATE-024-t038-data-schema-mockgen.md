# UPDATE-024 — T-038 C0+C1: data schema registry + mock generator (4 vòng verify)

- **Ngày:** 2026-07-23
- **Người thực hiện:** AI agent (dưới claim **Cường**, Track CORE)
- **Loại:** feature / data / test
- **TODO / User story liên quan:** T-038 (C0+C1), spec `core-data-schema-and-advisor-architecture.md`; nền cho solver C2–C5

## Tóm tắt

Đóng băng data schema L0–L3 + advisor I/O thành **23 JSON Schema** (registry validate qua `gsm_core.schema_registry`), rồi gen **mock dataset 30 ngày × 50 driver** từ sim T-030 (đã qua M0 integrity) đúng schema, verify **4 vòng** theo spec §8.1. Đây là nền dữ liệu cho toàn bộ Track CORE — mọi solver/agent sau đọc data qua registry này. Data thật GSM sẽ thay dần từng entity (cùng schema, đổi `source`).

## Chi tiết cập nhật

### C0 — Schema registry (`schemas/`, 23 entity)
L0 reference (5) · L1 event log observable-only (6) · L2 measured (4) · **L2i inferred tách riêng** (1) · L3 feature views (4) · advisor I/O (3). Mỗi schema: `schema_version` semver, `source` label bắt buộc (MOCK/REAL/ESTIMATED/COARSE/INFERRED), `x-sensitivity` PII, `x-availability: TBC-với-GSM`. `payout_ledger` tách gross/payout tại nguồn. `SchemaRegistry.validate/validate_many` là gate chung.

### C1 — Mock generator (`gsm_core.mockgen`)
- `adapter_sim.py`: sim events/orders/segments → L0/L1. **Chỉ observable** (latent meals/belief/patience KHÔNG ra). Ledger **tái tính** trip_payout = gross × driver_share (không copy số sim mù). GPS nội suy tuyến tính dọc segment (~30s/ping).
- `generate.py`: CLI 30 ngày (seed = seed_base+day) → parquet per entity + `manifest.json` (nhãn MOCK, seeds, generated_at, schema versions) + verify vòng 1/3.
- `verify_stats.py`: vòng 2, 30 seeds vs benchmark.
- Output `data/mock/v1/`: policy_bundle 1, driver_profile 50, station_registry 11, **app_event 47,716, trip_record 22,075, swap_transaction 1,738, payout_ledger 23,194, gps_ping 1,004,273**. Parquet gitignored (tái gen từ seed); manifest + reports commit.

### 4 vòng verify (report `research/experiments/mockgen/`)
1. **Schema+FK**: 100% record pass registry, 0 orphan FK → PASS.
2. **Statistical (30 seeds)**: trips FT median 16 (dải 15–30) PASS; dist median 3.21 PASS; served-peak-share 0.28 PASS; payout FT 256k **GAP có nhãn T-021** (không che). Metric-definition correction: peak_share đo trên SERVED (đỉnh bão hòa) — có document, không phải nới để che.
3. **Consistency**: ledger tái tính khớp 100%; event ordering per driver OK; GPS↔trip endpoint ≤50m PASS.
4. **Adversarial (inline polars — subagent bị spend-limit)**: 0 payout>gross, 0 thu nhập âm, fare lệch ≤3 VND (rounding artifact), 0 trip dur≤0, speed max 23km/h, 0 GPS teleport, 0 event giờ 0-4h, 0 driver no-event, accept-rate 0.966. **KHÔNG generator bug.**

## Files bị ảnh hưởng

| File | Hành động |
|---|---|
| `schemas/**` (23 schema + README + CHANGELOG) | tạo |
| `src/gsm_core/{__init__,schema_registry}.py` | tạo |
| `src/gsm_core/mockgen/{__init__,adapter_sim,generate,verify_stats}.py` | tạo |
| `tests/test_schemas.py` (11), `tests/test_mockgen.py` (8) | tạo |
| `research/experiments/mockgen/ROUND-{1,2,3,4}-*.md` | tạo |
| `pyproject.toml` | +jsonschema, +gsm_core package |
| `.gitignore` | +data/mock parquet |
| `data/mock/v1/manifest.json` | tạo (parquet gitignored) |

## Docs đã cập nhật kèm theo

TODO T-038 → VALIDATING. SCOPE/DEFERRED: không đổi. Spec core: không đổi (v1.1 đã chốt).

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
|---|---|---|---|---|
| 23 schema phủ đủ spec §1–3 | OBSERVED-CODE | test_all_entities_registered | Cao | thiếu entity → solver thiếu input |
| Ledger tái tính được từ policy | OBSERVED-CODE | round 3 + test_ledger_recomputable (100% khớp) | Cao | số tài chính không trace được |
| Data không phi thực tế | OBSERVED-CODE | round 4 (0 bug/8 chiều) | Cao | solver học pattern sai |
| payout/trips dưới benchmark | OBSERVED-CODE + PROXY | round 2 vs realism-benchmarks | Cao | — (gap đã biết T-021) |

## Kiểm chứng

### Seeds và scenarios

| Run | Seeds | Kết quả |
|---|---|---|
| `pytest -q` | fixture | **76/76 pass** (57 sim + 19 core) |
| Mock gen | 100–129 (30) | 4 vòng verify: PASS/PASS/PASS/PASS |
| Determinism | seed 101 ×2 | manifest identical (test_determinism) |

## Visual verification

- **Status:** `NOT_APPLICABLE` — data/schema layer, không đổi sim engine hay UI output; dashboard không phụ thuộc gsm_core. Report data là markdown số liệu, không phải visual.

## Adversarial self-review / flaws found

1. **Trông tốt nhưng sai?** Round 2 GAP có thể bị đọc là "data kém" — thực ra là calibration gap sim đã biết (T-021), generator trung thực phản ánh sim; KHÔNG tune để đẹp số.
2. **Latent leak:** test_no_latent_fields (schema + output) enforce — meals/belief/patience không ra L1.
3. **Ledger provenance:** tái tính từ policy, không copy số sim → số tài chính trace được (ràng buộc §5).
4. **Metric-definition risk:** peak_share sửa dải từ demand→served có document — không phải nới che flaw.
5. **Subagent adversarial bị spend-limit 2 lần** → thay bằng inline polars phủ 4 chiều với số thật; ghi nhận chạy lại subagent khi quota ổn (không blocker).
6. **Flaw còn mở:** fare rounding ≤3 VND (siết bằng dist_km nhiều số lẻ nếu solver cần — defer); L2/L2i/L3 derivation chưa gen (bước C2+).

## Expansion checkpoint (T-039)

1. **Schema**: cần thêm gì? → **net_input entity** (chi phí thuê/điện per track) khi có known costs — hiện `estimated_net_vnd` để null trong session_summary; **request-log entity** nếu GSM export unserved thật (thay ESTIMATED). Chưa thêm — chờ data thật/nhu cầu solver.
2. **Bài toán tối ưu mới?** Data GPS 1M ping mở khả năng: **idle-hotspot detection** (vùng tài xế đứng chờ lâu) — formalize được thành clustering, có thể thành solver F2 phụ. Đề xuất để Cường duyệt, chưa làm.
3. **Tính năng mới?** Từ payout_ledger + policy: **"policy delta impact"** (chính sách đổi ảnh hưởng payout ngày thế nào) — US-F0-03. Khả thi khi có policy_change_event thật. Ghi nhận.

(Không tự triển khai — đề xuất để Cường duyệt.)

## Follow-up / defer phát sinh

- **C2 (tiếp theo):** metric table per-layer (T-026 phase 1) + solver S1 BonusFeasibility + SolverReport envelope. L3 view `bonus_gap_input` derive từ data này.
- Chạy lại round-4 bằng subagent khi quota workflow ổn định.
- net_input + request-log entity: chờ data thật GSM.
