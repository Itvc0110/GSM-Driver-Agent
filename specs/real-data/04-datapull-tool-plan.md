# P4 — Data-pull tool plan (BigQuery read-only + PII + DataSource abstraction)

Cập nhật: 2026-07-24 · Part 4/7 · Trạng thái: DESIGN
Bối cảnh: **CHƯA có BQ access** → cycle này = interface + PII policy + test-vs-mock; kéo live sau khi Cường cấp credentials. **Không kéo data thật ở cycle nào tới khi Cường chốt.**

## 1. Kiến trúc `DataSource` (swappable mock ⇄ real)

```python
# src/gsm_core/datasource/base.py
class DataSource(Protocol):
    def fetch(self, table: str, *, cols: list[str] | None, where: Filter,
              limit: int | None) -> list[dict]: ...   # trả record đúng shape l1r/*
    def tables(self) -> list[str]: ...
```
- **`MockSource(parquet_dir)`** — đọc `data/mock/realdata-v1/*.parquet` (P3). Dùng cho test/dev/sim. **Mặc định.**
- **`BigQuerySource(project, dataset, credentials)`** — đọc gsm-data-prod (khi có access). Cùng interface → pipeline/solver KHÔNG biết nguồn nào.
- Pipeline/L3-derive gọi `DataSource` → **1 dòng đổi mock↔real** (env `GSM_DATA_SOURCE=mock|bq`).

## 2. Read-only CỨNG (nhiều lớp)

1. **IAM**: service-account chỉ role `roles/bigquery.dataViewer` + `jobUser` (chạy query), KHÔNG dataEditor/admin. (Cấu hình phía GSM/GCP — Cường/GSM chốt.)
2. **Code guard**: `BigQuerySource` chỉ dùng `client.query(SELECT…)`; **chặn** mọi statement ≠ SELECT (regex + parametrized); KHÔNG `INSERT/UPDATE/DELETE/CREATE/MERGE`.
3. **Table allowlist**: chỉ 13 bảng trong catalog; bảng ngoài → raise.
4. **Column allowlist**: chỉ cột trong catalog (+ loại cột PII-drop ngay tại query nếu có thể) → giảm bề mặt PII.
5. **Cost guard**: `maximum_bytes_billed` + `LIMIT` mặc định + dry-run ước tính bytes trước khi chạy.

## 3. PII policy (đọc từ schema `x-pii-action`)

| Cột PII | Action | Ghi chú |
|---|---|---|
| full_name, phone_number, email, tel, driver_name, engname | **DROP** tại ingestion (không lưu) | không cần cho feature |
| sap_id, sap_profile_id, vehicle_vin_number, vehicle_license_plate | **DROP** (hoặc hash nếu cần join) | |
| customer_id | **DROP** | không dùng |
| driver_id | **HASH ổn định** → pseudonym (HMAC + salt bí mật) | giữ join được, không lộ định danh |
| sap_contract_type | **KEEP** (map track) — không phải PII trực tiếp | |
| lat/lon | đã hex-agg trong bảng thật → **KEEP hex**, không lấy toạ độ thô | |
- Module `datasource/pii.py`: `scrub(record, schema)` áp action theo `x-pii-action`. Chạy **trước khi** record rời tool (ingestion boundary). Test: mọi cột PII-drop vắng mặt ở output; driver_id output ≠ input (đã hash), ổn định qua 2 lần.
- **Salt** = env bí mật (không commit); pseudonym nhất quán trong 1 dataset version.

## 4. Provenance & governance mỗi pull
Ghi `pull_manifest`: {table, cols, filter, ts, row_count, bytes_billed, schema_version, source=REAL, pseudonym_salt_version}. Append-only log. Nhãn record `source="REAL"` (phân biệt MOCK).

## 5. Test (KHÔNG cần live)
- `MockSource` contract test: fetch trả đúng shape l1r, cols filter đúng, where/limit đúng.
- `BigQuerySource` unit test với **client mock** (không mạng): guard chặn non-SELECT, allowlist bảng/cột, PII scrub áp đúng, provenance ghi đủ.
- (Optional) BigQuery **emulator**/`bq` dry-run nếu Cường muốn kiểm SQL syntax — cần chốt (xem §7).

## 6. Techstack & ENV cần Cường chốt (KHÔNG tự quyết)
> Theo yêu cầu Cường "luôn hỏi khi cần chốt techstack/env":
1. **Client lib**: `google-cloud-bigquery` (chính thức) — thêm vào optional extra `bq`. **Chốt?**
2. **Auth**: service-account JSON key (`GOOGLE_APPLICATION_CREDENTIALS`) vs Workload Identity vs `bq` CLI ADC. **Chốt cơ chế + ai cấp?**
3. **ENV cần điền (khi có access)**: `GSM_GCP_PROJECT`, `GSM_BQ_DATASET`(3 dataset: KPI_REWARD/MISSION/BROADCASTING), `GOOGLE_APPLICATION_CREDENTIALS`, `GSM_PII_SALT` (bí mật, không commit — vào `.env`), `GSM_DATA_SOURCE=mock|bq`.
4. **Emulator test** có cần không (thêm dep) hay chỉ client-mock unit test.

→ Tôi sẽ HỎI trước khi thêm dep/điền `.env`. Hiện plan = interface + test-vs-mock, chưa đụng credentials.

## 7. Acceptance P4 (cycle impl)
`DataSource` + `MockSource` chạy + test; `BigQuerySource` skeleton + guard/PII/provenance + client-mock test; `.env.example` thêm biến (giá trị rỗng, có chú thích); README cách bật khi có access. Live pull = **treo tới khi Cường cấp credentials + chốt §6**.
