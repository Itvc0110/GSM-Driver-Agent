# UPDATE-113 — SỬA THƯỚC adherence kênh vị trí; và một lỗi phương pháp của chính tôi

Ngày: 2026-07-31 · Trạng thái: `DONE-CODE` (đo lại E10 XONG, 4/4 arm cổng OK) · Cường duyệt nhánh này
sáng 2026-07-31 (AskUserQuestion: *"Cho sửa thước"*), điều kiện kích hoạt nay ĐÃ xảy ra.

## Vì sao kích hoạt: cổng z TREO arm oracle

Sau khi thống nhất lưới quyết định (UPDATE-112/V-21), đo lại E10:

| Phép đo | Lệch so null | z | Cổng |
| --- | --- | --- | --- |
| preflight n=30 (lưới cũ) | −2,41đp | −2,39 | OK |
| arm oracle n=100 (lưới cũ) | −1,64đp | −3,00 | OK |
| **arm oracle n=100 (lưới mới)** | −2,36đp | **−4,41** | 🔴 **TREO** |

**Thống nhất lưới KHÔNG gây ra việc này** — hai lệch −1,64 và −2,36đp chỉ cách nhau **1,3 SE**
(SE = 0,57đp ở n=7.635 quyết định), không phân biệt được. Dự đoán z từ preflight nếu **chỉ cỡ
mẫu tăng** là −4,39; đo được **−4,41**. Khớp gần như hoàn hảo ⇒ nguyên nhân là **bias
coin-vs-execution ~2,4đp có sẵn**, cộng với cỡ mẫu đủ lớn để cổng thấy.

## 🔴 Lỗi phương pháp của chính tôi (UPDATE-109)

UPDATE-109 chạy cổng tiền-flight ở **n=30** rồi kết luận *"z=−2,39 ⇒ thước GIỮ NGUYÊN"* cho
phép đo thật ở **n=100**. Cùng một bias 2,4đp cho z=2,29 ở n=30 (không bắn) nhưng z=4,20 ở
n=100 (bắn). **Dùng phép kiểm ở cỡ mẫu NHỎ HƠN cỡ mẫu thật để tuyên bố thước lành.**

Hệ quả với những gì đã báo: tôi từng nói *"dự đoán z~13 của spec SAI theo hướng bảo thủ"* —
**câu đó sai**. Dự đoán "SẼ bắn" của spec §5.5 là **ĐÚNG**; công cụ tôi dùng để bác nó không
đủ mạnh. Đây là họ lỗi "cơ chế đúng, độ lớn sai" ở dạng mới: **cơ chế đúng, POWER sai**.

Bài học đã áp ngay trong cycle này: sau khi sửa thước, tôi **tính power TRƯỚC** — từ z=−0,84
ở n=30, dự phóng n=100 ≈ −1,5 (an toàn); đo được **−0,38**.

## Thước mới — tách hai câu hỏi

`standby_followed` = coin-true **∧ thi hành được**. Các ca coin-true-không-thi-hành là code
path THẬT (pop im lặng khi actor đã đứng đúng ô; bận tới hết ca; bản năng ≠ WAIT ở
`wait_only`). Đếm chúng thành "không theo" là trộn hai câu hỏi vào một con số.

| | Đo cái gì | Nguồn |
| --- | --- | --- |
| `followed` (tử số adherence) | tài xế có **NGHE** không | `coin_follow_ids` — kết cục coin tại đúng lúc gán |
| `execution_rate` (chỉ tiêu RIÊNG) | nghe rồi có **LÀM ĐƯỢC** không | `standby_followed` / coin-true |

- `world.py`: planner ghi `coin_follow_ids` vào detail `standby_alloc` (event SẴN CÓ, không
  thêm kind mới).
- `projections.py`: `standby_followed` **gỡ khỏi** `_TERMINAL_ONLY` (thôi map thành
  `followed`); `_offer_events` sinh `followed` cho coin-true ids (cùng `decision_id`,
  `reason_code="coin"`). Hằng `EXECUTION_KINDS` khai tường minh.
- `sim_metrics.adherence_audit`: thêm `execution` (`coin_true_n`/`executed_n`/`execution_rate`).

## Kèm theo: L3-04 — `event_adherence` là estimator LỆCH (gắn nhãn, không "sửa")

Đo được seed 5100 ladder=all: `accept_lift` decision **0,714** (n=63) vs event **0,524**
(n=147) ⇒ **lệch −19,0đp**, tỷ lệ hỏi lại **2,33×**; ba kênh không-hỏi-lại lệch đúng **0,0đp**
(1,00×). Cơ chế: tần suất hỏi lại **phụ thuộc chính kết cục** — người KHÔNG theo bị hỏi lại
mỗi tick, người ĐÃ theo thì thôi ⇒ mẫu số event phình bởi người không theo.

Không "sửa" được vì nó đo thứ khác ⇒ **gắn nhãn**: `adherence_audit` nay trả
`event_repeat_ratio` + `event_adherence_is_lower_bound`. Với kênh hỏi lại,
`event_adherence` là **chặn DƯỚI**; **CẤM so giữa các kênh**.

## Kết quả cổng sau khi sửa

| | z (30 seed) | z (n=100) |
| --- | --- | --- |
| Thước cũ | −2,39 | **−4,40 TREO** |
| **Thước mới** | **−0,84** | **oracle −0,38 · hist +0,82 — OK** |

## Files

- **SỬA** `src/gsm_sim/world.py` · `src/gsm_core/lifecycle/projections.py` ·
  `src/gsm_sim/sim_metrics.py`
- **TẠO** `tests/test_adherence_ruler_fix.py` (4 test)
- **SỬA** `tests/test_lifecycle_review_fixes.py` (2 test pin hành vi cũ → pin hành vi mới,
  ghi chú tại chỗ) · SOI + DEFERRED (`D-R22` mở rộng).

## Kiểm chứng

- 4 test thước mới xanh; **khôi phục thước cũ ⇒ 3/4 ĐỎ** (test có răng thật).
- Nhóm lifecycle **22/22** · cổng adherence + thước **24/24** · full suite CẢ HAI lệnh
  **889 + 5 skipped + 65 UI = 959 / 0 fail**.
- Cổng thống kê thật: preflight n=30 z=−0,84 · arm oracle n=100 z=−0,38 · arm hist z=+0,82,
  tất cả verdict **OK**.
- Cổng thật CẢ 4 ARM verdict **OK**: oracle −0,38 · hist +0,82 · real −0,95 · wait −0,16
  (thước cũ: oracle **−4,40 TREO**).

## 🔴 SỐ E10 ĐỔI — và LỚP KẾT LUẬN cũng đổi

| Arm | Δ vs A (CI95) | Δ vs oracle (CI95) | Lớp §6.3 — THƯỚC MỚI | (thước cũ) |
| --- | --- | --- | --- | --- |
| `B_oracle` | **+3,939đ** [2,854, 5,033] | — | trần | (+5.529) |
| `B_hist` | **+3,401đ** [2,423, 4,337] | −538 [−1.522, +464] | 🟢 **KQ-GIỮ** (MDE_dd=1.012) | CÒN-MỘT-PHẦN 57% |
| `B_real` | **+3,126đ** [2,080, 4,167] | −813 [−2.046, +420] | 🟢 **KQ-GIỮ** (MDE_dd=1.212) | CÒN-MỘT-PHẦN 65% |
| `B_wait` | +174đ [-603, 916] | −3.765 [−5.033, −2.536] | 🔴 **KQ-SỤP** (không đổi) | KQ-SỤP |

**Đổi lớp từ CÒN-MỘT-PHẦN → KQ-GIỮ**: với thước đúng, `CI(Δ_X − Δ_oracle)` **chứa 0** ở cả
hist và real ⇒ *"mất λ không gây suy giảm PHÁT HIỆN ĐƯỢC"*. Nhưng theo đúng §6.3, KQ-GIỮ là
phát biểu **YẾU** và phải kèm nguyên văn:

> **L1** — thế giới sim có thứ hạng ô ĐỨNG YÊN cả ngày (`λ = ngày × giờ × ô`), tức bài toán
> khó nhất ngoài đời (pattern sáng/tối đổi rank) KHÔNG tồn tại ở đây. **L2** — λ̂ ngửi được
> oracle qua bản năng tài xế (Spearman pickup-vs-λ = 0,41). Hai điều này kéo kết quả LÊN.
> ⇒ Ngoài đời phần giữ lại **thấp hơn**; KQ-GIỮ ở đây KHÔNG chứng minh "advisor không cần λ".

Và **MDE_dd ≈ 1.000–1.200đ**: ta chỉ loại trừ được suy giảm LỚN HƠN mức đó — không phải
"suy giảm bằng 0". Δ vs oracle vẫn ÂM ở cả hai (−538 và −813), chỉ là chưa vượt nhiễu.

- **STOP-1 không bắn** (CI Δ_oracle > 0). Nhưng CI [2.854, 5.033] **không chứa +6.016** của
  UPDATE-087 ⇒ **không tái lập được trần điểm cũ**; xem `D-E10-06` về khả năng lưới/coin.
- **G-GUARD 0/9 tầng xấu** ở mọi arm · **G-HERD**: HHI real 0,01235 vs oracle 0,01214 —
  vẫn không có dấu hiệu dồn cục.

## Nhãn evidence

Mọi số MOCK. **Số Δ của E10 trong UPDATE-110 đo bằng THƯỚC CŨ** — chưa bị chứng minh sai,
và cổng đã TREO arm oracle ở lưới mới ⇒ **UPDATE-110 SUPERSEDED: dùng số của UPDATE này**.
Con số công bố mới: mất λ ⇒ **KQ-GIỮ** (không suy giảm phát hiện được, MDE_dd ≈1.000–1.200đ),
Δ tuyệt đối +3.126…+3.401đ/người/ngày trên trần +3.939đ — kèm caveat L1+L2 bắt buộc.

## Visual review

`NOT_APPLICABLE` — đổi cách ĐẾM, không đổi dynamics (fingerprint không đổi vì `coin_follow_ids`
là detail của event sẵn có; coin vẫn rút đúng một lần tại đúng chỗ cũ).

## Adversarial self-review / flaws found

- Thước mới làm `followed` **không còn quan sát được từ hành vi** — nó là kết cục coin do
  chính bridge sinh. Rủi ro: nếu coin sai thì adherence "đúng" một cách tự quy chiếu. Đối
  trọng: coin là keyed sha256 độc lập với event log, và `probe_adherence_truth.py` vẫn so
  được hai đường. Nhưng phải nói rõ: **cổng z nay đo tính TOÀN VẸN của đường ghi, không đo
  hành vi tài xế**.
- `execution_rate` mới, chưa có baseline lịch sử ⇒ chưa biết ngưỡng nào là bất thường. Chỉ
  báo số, chưa gắn cổng — đúng nguyên tắc không đặt ngưỡng khi chưa có phân phối.
- Hai test hồi quy bị sửa kỳ vọng — cả hai đang pin hành vi cũ (một cái pin số lần thi hành
  làm tử số; một cái pin `bucket_min=15` chạy được). Ghi chú lý do tại chỗ sửa.
- L3-04: nhãn `is_lower_bound` chỉ bật khi `event_decided > decided`. Kênh hỏi lại mà tình
  cờ 1,00× ở một seed sẽ không bật nhãn — nhãn theo run, không theo bản chất kênh. Ghi nhận.

## Follow-up

- ✅ Đã đo đủ 4 arm + `diff`; lớp kết luận ĐỔI (CÒN-MỘT-PHẦN → KQ-GIỮ) và đã báo đúng như đổi.
- `D-E10-06`: Δ_oracle dịch −1.590đ khi đổi lưới (p=0,012, 62/38 seed) — chưa giải thích được,
  có phép đo phân biệt cụ thể (đổi salt coin, giữ lưới cũ, ~17′ máy).
- `waitoracle` chưa đo lại với thước mới (n=30, chỉ đọc CHIỀU) — không đổi kết luận nào.
- ⏳ **PENDING-REVIEW 20 mục chờ Cường**: V-01..V-14, V-16, V-17, V-18, V-20, V-21.
