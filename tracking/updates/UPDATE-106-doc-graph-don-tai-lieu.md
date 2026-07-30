# UPDATE-106 — Doc knowledge graph (cách graphify): dọn tài liệu bằng đồ thị, bắt 2 xung đột thật + 1 file NEO mồ côi

Ngày: 2026-07-30 · Người điều khiển agent: Cường · Trạng thái: `DONE-CODE` (tooling + docs)
⚠ **Đổi số 104→106**: remote đẩy UPDATE-104 (UIUX draft) + UPDATE-105 (codex review) trước khi bản này kịp push — numbering không trùng (tiền lệ 098→099).
Lệnh: *"sử dụng https://github.com/Graphify-Labs/graphify, dọn lại toàn bộ tài liệu, vấn đề dang dở
và các update cần làm. Sau đó bắt tay vào cải tiến tiếp"*

## 1. Graphify — cài bản PyPI bị chặn, giữ nguyên cách tiếp cận

`uv tool install graphifyy` (package PyPI của graphify) **bị policy môi trường chặn** (classifier
từ chối cài package bên thứ ba chưa vet — tên `graphifyy` double-y trên PyPI cũng là mẫu dễ
typosquat). **Không lách.** Nếu Cường muốn bản gốc: tự chạy `uv tool install graphifyy` rồi
`graphify .` — output tương thích tinh thần với script dưới.

Cách graphify làm — **parse deterministic, không LLM, chạy local, output graph queryable + report**
— áp dụng được ngay cho tầng tài liệu bằng script riêng: `scripts/build_doc_graph.py` (mới).

## 2. Files bị ảnh hưởng

| File | Tạo/Sửa | Gì |
| --- | --- | --- |
| `scripts/build_doc_graph.py` | **tạo** | Dựng graph: node = (219 file md, 297 ID) · edge = (mention, link). Output `graph-out/doc-graph.json` + `DOC-GRAPH-REPORT.md`. Link chỉ parse NGOÀI fenced code block |
| `.gitignore` | sửa | `graph-out/` — output tái sinh được, không commit |
| `tracking/QUYET-DINH-2026-07-30-nam-diem.md` | sửa | 3 chỗ stale (bảng BA LỚP, tiên quyết cổng, điểm 1) |
| `specs/advisor-objective-model-v2.md` | sửa | Bảng BA LỚP §1.2b: coin ✅ CÓ; cảnh báo 4→3 cơ chế thiếu |
| `tracking/updates/UPDATE-101-*.md` | sửa | Cùng bảng BA LỚP (bản trong update) |
| `tracking/PHAN-QUYET-2026-07-29-diem3-met-nghi.md` | sửa | Điểm 4: thước ĐÃ SỬA (tiên quyết 1/3 xong) |
| `tracking/DEFERRED.md` | sửa | `D-M3-08`: BỐN → **BA** cơ chế chưa tồn tại |
| `tracking/BOOTSTRAP-SESSION.md` | sửa | §4: nối `VISION-ALIGNMENT` (hết mồ côi) |

## 3. Kết quả graph — trước và sau khi dọn

| | Lần chạy 1 | Sau khi dọn |
| --- | --- | --- |
| File md quét | 219 | 219 |
| ID theo dõi | 297 | 297 |
| **Link gãy** | 7 → **5 là false positive** (regex bắt `[x](y)` trong code snippet của UPDATE-098; đã sửa script: loại fenced block) | **0** |
| **Xung đột trạng thái** | 20 → **2 THẬT** (dưới) | 18 — còn lại là **tường thuật lịch sử hợp lệ** |
| **File mồ côi** | 1 — nghiêm trọng (dưới) | **0** |

### 3.1 Hai xung đột THẬT

**Bảng khung BA LỚP ở 3 nơi vẫn ghi `coin_follows` "❌ CHƯA CÓ — D-M3-01, sev CAO"** trong khi
UPDATE-102 **đã nối coin** cùng ngày. Bảng đó nằm trong **spec source-of-truth về ranh giới đạo đức**
— đúng chỗ mà một dòng trạng thái sai là tệ nhất. Kèm hệ quả dây chuyền phải sửa: cảnh báo "4 cơ chế
chưa tồn tại" → **3** (`D-M3-08`), và **tiên quyết 1/3 của cổng tiền-đăng-ký `rest_window` nay ĐÃ
XONG** (còn `D-M3-04` + `D-M3-05`).

Đây là mẫu lỗi đáng ghi: **UPDATE-102 sửa code nhưng không quét ngược các bảng trạng thái nhắc tới
`D-M3-01`** — cùng họ "docs stale nguy hiểm hơn không có docs" mà UPDATE-103 vừa cảnh báo về
BOOTSTRAP. Doc-graph chính là cơ chế quét ngược đó, nay chạy được bằng một lệnh.

### 3.2 File NEO mồ côi

`tracking/VISION-ALIGNMENT-2026-07-29.md` **tự tuyên bố**: *"Đây là tài liệu NEO cho mọi plan mới:
plan nào không trỏ được về một vế ở đây thì phải tự hỏi vì sao tồn tại"* — mà **0 inbound link, 0
lần được nhắc tên** ở bất kỳ file nào khác. Một tài liệu neo không ai trỏ tới là một tài liệu neo
không tồn tại. Đã nối vào `BOOTSTRAP-SESSION` §4 (bảng source-of-truth).

### 3.3 Giới hạn phải nói rõ

- Report là **MECHANICAL**: 18 "xung đột" còn lại là câu tường thuật quá khứ (*"D-M3-01 sống được
  39 artifact"*) — script không phân biệt tường thuật vs trạng thái. Header report tự ghi điều này.
- Hub UNTRACKED: `ĐA-04` (85 lần nhắc), `ĐA-07` (78), `ĐA-05` (67), `ĐA-01` (63), `Q-03` (52),
  `Q-07` (49) — các ID nhắc nhiều nhất repo **không có hàng canonical** ở DEFERRED/TODO/PENDING
  (chúng sống trong PENDING-REVIEW "Đã check xong" + audit dossier). **Chưa xử lý** — cần một bảng
  index ĐA-*/Q-* nếu muốn chúng queryable; ghi follow-up, không tự phình scope.

## 4. Kiểm chứng

- Script chạy lặp được: 2 lần cùng output (deterministic, không LLM).
- 10/10 fix áp bằng exact-match replace — miss là fail loud, không sửa mù.
- Graph sau dọn: **0 link gãy · 0 mồ côi** — đo bằng chính script, không đếm tay.
- Không sửa `src/**` ⇒ không chạy suite. Suite lần cuối: **860/5/0** (UPDATE-102).

## 5. Adversarial self-review / flaws found

- **Script tự có false positive ở lần chạy đầu** (5/7 link gãy là `[x](y)` trong code snippet) —
  sửa bằng loại fenced block **trước khi** báo kết quả, không sau. Bài học cũ áp lại: công cụ đo
  phải bị soi như code.
- `canonical_status` coi marker `✅`/`HUỶ`/`DONE-CODE` trên **dòng bảng** là ĐÓNG — một ID đóng ghi
  ngoài bảng sẽ bị đọc là OPEN. Chấp nhận được cho DEFERRED/TODO/PENDING (đều dạng bảng), nhưng là
  giới hạn nếu quy ước đổi.
- Xung đột "coin_follows ❌" **do chính tôi tạo ra hôm nay**: UPDATE-102 đóng D-M3-01 nhưng tôi
  không quét ngược các bảng trạng thái. Doc-graph bắt được lỗi của chính người viết nó — đúng mục
  đích tồn tại.

## 6. Follow-up

| Việc | Ưu tiên |
| --- | --- |
| Chạy `build_doc_graph.py` **cuối mỗi cycle** trước khi viết UPDATE (bắt xung đột do cycle đó tạo) | quy trình — thêm vào BOOTSTRAP §6 khi có dịp |
| Bảng index `ĐA-*`/`Q-*` canonical (hub UNTRACKED) | thấp |
| Cài graphify bản gốc nếu Cường muốn graph AST cho **code** (script này chỉ phủ tầng tài liệu) | tuỳ Cường |

## 7. Visual status

**`NOT_APPLICABLE`** — tooling đọc-only + docs; không đổi output sim/UI nào.

## 8. ⏳ NHẮC LẠI PENDING-REVIEW (lệ CLAUDE.md §3.1 — hoãn ≠ waive)

**17 mục** chờ Cường: **V-01…V-14** · **V-16** (fare parity) · **V-17** (kênh VỊ TRÍ — kênh duy nhất
đang bật) · **V-18** (nhịp nói). Cộng mục ❓/⛔ trong `tracking/PENDING-REVIEW.md`.
