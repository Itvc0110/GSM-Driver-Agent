# schemas/ — Data schema registry (T-038 C0)

Nguồn sự thật về contract dữ liệu core. Spec: `specs/core-data-schema-and-advisor-architecture.md`.
Validate qua `gsm_core.schema_registry.SchemaRegistry` — solver/agent/mockgen đều đi qua đây.

## Cấu trúc tầng

| Folder | Tầng | Tính chất |
|---|---|---|
| `l0/` | Reference (policy, profile, station, zone, service) | slowly-changing, versioned |
| `l1/` | Event log (app events, trips, GPS, swap, ledger, policy change) | **immutable, observable-only — CẤM latent** |
| `l2/` | State fields (supply/demand/station/driver-day) | derivation job có version |
| `l2i/` | Inferred views | **tầng RIÊNG — nhãn INFERRED + rule version bắt buộc** |
| `l3/` | Feature views cho solver | read-only |
| `advisor/` | I/O pipeline (request / solver report / composed advice) | đóng băng contract |

## Quy ước (spec §1.6)

- **Versioning:** `schema_version` semver per entity. Thêm field = optional + minor bump.
  Bỏ field = đánh `deprecated_since` trong description + giữ ≥1 chu kỳ, KHÔNG xóa thẳng.
  **CURRENT LIMITATION (2026-07-27):** `SchemaRegistry` hiện chỉ load một file/entity, trong khi
  schema khóa `schema_version.const` và `additionalProperties: false`. Vì vậy minor bump mới chỉ là
  quy ước tác giả, **chưa chứng minh backward compatibility runtime** cho record phiên bản cũ.
  Trước migration phải có registry đa phiên bản hoặc upcaster + compatibility test; xem
  `research/audit/2026-07-27-current-state/01-data-lineage-and-update-model.md#8-blocker-schema-versioning`.
- **`source` bắt buộc** mọi record: `MOCK | REAL | ESTIMATED | COARSE | INFERRED`
  (CLAUDE.md §5 — mock phải gắn nhãn; không trộn mock với data thật).
- **`x-sensitivity`**: field PII (driver_id, lat/lon thô) — cơ chế thu hẹp/anonymize sau.
- **`x-availability: TBC-với-GSM`**: field chưa chắc GSM export được — bảng fallback
  trong spec §1.6 (ESTIMATED/COARSE labels).
- **Latent cấm ở L1** (taxonomy reliability-upgrade §3.5): meals/fatigue/belief/patience
  là sim-only ground truth — test `test_latent_fields_absent_from_l1` enforce.
- **Data quality assumption:** L1 nhận data ĐÃ clean/normalize (dedup, UTC+7, hợp lệ)
  — pipeline ingest ngoài scope (spec §0).
- Sim và data thật GSM dùng CÙNG schema — chỉ đổi `source`.

## Sửa schema thế nào

1. Sửa file `.schema.json` + bump `schema_version` theo semver.
2. Ghi `CHANGELOG.md` (version, ngày, lý do, tương thích).
3. Chạy `uv run --extra dev pytest tests/test_schemas.py tests/test_mockgen.py`.
4. Biến mới phải điền được bảng traceability spec §1.7 (feature + pain hoặc lý-do-hạ-tầng) — điều kiện T-039.
