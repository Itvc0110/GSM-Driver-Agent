# UPDATE-077 — ĐA-01: gỡ rò tương lai ở tỷ lệ nhận/hoàn thành + một estimator dùng chung

- **Ngày:** 2026-07-27
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** fix (correctness — **advisor đang được chấm điểm bằng thông tin nó không thể có**)
- **TODO / User story liên quan:** **T-042 việc 3a**; ĐA-01 (APPROVED-DESIGN 2026-07-27);
  hồ sơ `08-parity-sim-vs-ui.md` §2

## Tóm tắt

`build_gi` lấy `acceptance_rate`/`completion_rate` từ `driver_statistic_daily` của **chính ngày
đó** — aggregate CẢ NGÀY. Ở **9h sáng**, S1 đã biết tỷ lệ **cuối ngày**. Đây là **rò tương lai**,
không phải "granularity thô" như comment cũ ghi. Kèm theo là fallback **`or 1.0`** — thiếu dữ liệu
thì coi như "hoàn hảo", nên gate thưởng đi qua nhầm đúng ở nhóm chưa có gì để tin.

Thay bằng estimator shrinkage ĐA-01, chỉ dùng **ngày TRƯỚC**. **16/60 tài xế (27%) đổi phía ngưỡng
0,85** ⇒ kết luận gate thưởng đổi cho hơn một phần tư đội.

## Chi tiết cập nhật

### 1. Vì sao đây là lỗi nặng chứ không phải chi tiết kỹ thuật

Con số cũ **không tồn tại tại thời điểm ra quyết định**. Hệ thống thật, chạy lúc 9h sáng, **không
có cách nào** biết tỷ lệ cuối ngày. Nghĩa là:

- mọi kết luận "đạt/không đạt ngưỡng" của advisor trong các demo trước đây được ra **với một oracle**;
- và vì thế **mọi đánh giá chất lượng advisor trên đường UI đều là cận trên lạc quan** — cùng loại
  cảnh báo mà hồ sơ 07 §5.1 đã phải viết cho các số A/B đơn-tài-xế.

Ca cụ thể (`d-37`, 2026-09-28): tỷ lệ **cùng ngày = 1,000** (hôm đó nhận hết). Bản cũ thấy 1,000 ⇒
kết luận thoải mái. Lịch sử 7 ngày = **0,745** ⇒ bản mới cảnh báo `acceptance_below_threshold`.
Ở 9h sáng, **0,745 là ước lượng hợp pháp duy nhất**; 1,000 là thông tin từ tương lai.

### 2. Một estimator cho cả hệ (`src/gsm_core/rates.py`)

```
p̂ = (k + m·p0) / (n + m)
```

Hậu nghiệm trung bình Beta-Binomial; `m` = số quan sát giả (đơn vị "số lần được chào").

Trước đó **một khái niệm có BA cách tính**: `entities.acceptance_rate` (0/0 → **1.0**) ·
`journey.py` (0/0 → **None**) · UI (aggregate ngày, thiếu → **1.0**). Đúng thứ đã đẻ ra
UPDATE-075/076. `rates.shrunk_rate` là nguồn duy nhất từ nay.

**Không có mặc định cho `p0`/`m`** — caller phải truyền, vì `p0` phải là số **đo được**, không bịa.
Đầu vào hỏng (`k > n`, số âm, `p0` ngoài [0,1]) thì **nổ**, không lặng lẽ trả số trông hợp lý.

### 3. Tham số đã chọn và lý do

| Tham số | Giá trị | Lý do | Nhãn |
|---|---|---|---|
| `m` (quan sát giả) | **20** | ≈ hơn một ngày được chào; **n trung vị của cửa sổ 7 ngày = 81** nên shrinkage nhẹ, người có lịch sử vẫn được chấm theo chính họ | **ASSUMPTION** — nhưng **đã quét độ nhạy**, xem §5 |
| cửa sổ | **7 ngày trước** | **đồng bộ `_hist_rate`** cùng file — không tạo quy ước thứ hai | thiết kế |
| `p0` acceptance | **0,8971** (pooled, ngày < `date`) | đo từ `driver_statistic_daily`, cắt `< date` để không đổi leak cá nhân lấy leak tập thể | **OBSERVED-DATA** |
| `p0` khi chưa có ngày nào | ngưỡng policy | bảo thủ, và **không phải 1.0** | thiết kế |

### 4. Tác động đo được (ngày cuối snapshot, 60 tài xế bike)

| | tỷ lệ cùng ngày (CŨ) | as-of shrunk (MỚI) |
|---|---|---|
| median | 0,8889 | **0,9042** |
| min | 0,5882 | **0,7420** |
| số dưới ngưỡng 0,85 | 21 | **9** |

`|Δ|` median **0,0713**, max **0,2555**. **16/60 (27%) đổi phía ngưỡng.**

Đọc đúng: số cũ **vừa rò vừa nhiễu** — một ngày ít đơn (5 offers) lật kết luận. Số mới dùng ~7
ngày nên ổn định hơn. Hướng "ít cảnh báo hơn" **không phải là làm nhẹ đi**: nó phản ánh việc bỏ
nhiễu một-ngày, và đồng thời **thêm cảnh báo** cho những người mà ngày hôm đó tình cờ đẹp (`d-37`).

### 5. Quét độ nhạy `m` (T-042 việc 3c — làm luôn vì đây là mắt xích yếu nhất)

90 tài xế × 3 ngày rải đều (ngày 31 / 61 / cuối) = **270 quan sát**. `n` trung vị = **81**.

| `m` | dưới ngưỡng | p10–p90 | **đổi kết luận so với `m=20`** |
|---|---|---|---|
| 5 | 64/270 (23,7%) | 0,785–0,946 | **6 (2,2%)** |
| 10 | 61/270 (22,6%) | 0,791–0,943 | **3 (1,1%)** |
| **20** | 58/270 (21,5%) | 0,802–0,939 | — |
| 50 | 47/270 (17,4%) | 0,827–0,930 | **11 (4,1%)** |
| 200 | 4/270 (1,5%) | 0,865–0,913 | **54 (20,0%)** |

**Kết luận: `m` trong dải hợp lý [5, 50] KHÔNG lật kết luận** (1,1–4,1%). Vì `m ≪ n` (20 so với
81) nên dữ liệu thật vẫn áp đảo prior. Chỉ khi `m = 200` — **lớn hơn cả `n`** — estimator mới sập:
chỉ còn 1,5% dưới ngưỡng, tức **mất khả năng phân biệt**, đúng như lo ngại đã nêu.

⇒ Ràng buộc phải giữ: **`m` luôn nhỏ hơn nhiều so với `n` điển hình của cửa sổ**. Nếu sau này rút
cửa sổ xuống 1–2 ngày thì `m=20` sẽ thành quá mạnh — phải quét lại.

## Files bị ảnh hưởng

| File | Hành động | Ghi chú |
| --- | --- | --- |
| `src/gsm_core/rates.py` | **tạo** | `shrunk_rate` — estimator dùng chung |
| `tests/test_rate_estimator.py` | **tạo** | 7 test tính chất toán học (0/0→prior, co về prior, hội tụ, đơn điệu, biên, nổ khi k>n) |
| `ui/backend/app/adapters/advisor.py` | sửa | `_pooled_prior` + `_rate_asof`; `build_gi` hết đọc `_stat_row` của ngày hiện tại |
| `ui/backend/tests/test_contracts.py` | sửa | +2 test: tái tính độc lập + chặn leak; cấm fallback 1.0 |

## Docs đã cập nhật kèm theo

TODO (T-042 việc 3a → DONE) ✅ · PENDING-REVIEW (V-14) ✅. SCOPE/USER_STORIES/DEFERRED: không đổi.

## Assumptions và evidence

| Claim | Nhãn | Nguồn | Confidence | Tác động nếu sai |
| --- | --- | --- | --- | --- |
| `k/n` khớp `acceptance_rate` trong data | **OBSERVED-DATA** | lệch ≤ 5e-5 (làm tròn 4 chữ số), 12.805 dòng | cao | nếu lệch thật thì estimator sai gốc |
| `p0 = 0,8971` | **OBSERVED-DATA** | 176.082 / 196.306 | cao | prior lệch ⇒ ước lượng lệch ở tài xế ít lịch sử |
| `m = 20` | **ASSUMPTION đã quét độ nhạy** | §5: kết luận đổi 1,1–4,1% khi `m ∈ [5,50]`; `m ≪ n` (20 vs 81) | **trung bình–cao** (kết luận robust, *mức* vẫn chưa hiệu chỉnh) | chỉ sập khi `m ≳ n` (đã đo tại `m=200`: 20% đổi kết luận) |
| Cửa sổ 7 ngày | thiết kế | đồng bộ `_hist_rate` | trung bình | hành vi trôi nhanh hơn 7 ngày ⇒ ước lượng chậm |

## Kiểm chứng

| Command / run | Kết quả | Chưa kiểm chứng |
| --- | --- | --- |
| `pytest tests/test_rate_estimator.py` | **đỏ (module chưa có) → 7 passed** | — |
| `pytest tests` (ui/backend) | **33 passed** (31 → +2) | — |
| `pytest tests` (root, full) | **555 passed, 4 skipped** (14:55) | — |
| Quét độ nhạy `m` ∈ {5,10,20,50,200} | 270 quan sát (90 tài xế × 3 ngày) | chỉ đội bike, chỉ 3 ngày |
| Đo tác động 60 tài xế bike, ngày cuối | 16/60 đổi phía ngưỡng | chỉ 1 ngày, chỉ đội bike |

**Full suite:** **555 passed / 4 skipped** (548 của UPDATE-076 → +7 test estimator).

**Baseline 30 seed có bị ảnh hưởng không?** **KHÔNG** — thay đổi nằm hoàn toàn ở
`ui/backend/app/adapters/advisor.py`; `gsm_sim` **chưa** import `rates.py`. Sim vẫn dùng
`actor.acceptance_rate` (as-of đúng, không leak). Đây là lý do việc 3 được tách 3a/3b.

## Visual verification

- **Status:** `BLOCKED` → chờ Cường xem (**có kịch bản thật, khác V-13**)
- **Launch:** `uv run uvicorn app.main:app --app-dir ui/backend --port 8010` → `http://localhost:8010/app/`
- **Kịch bản CỤ THỂ (đã tìm được driver thật, không phải fixture):**
  - **`d-37` @ `2026-09-28`, 09:00** — tỷ lệ *cùng ngày* 1,000 nhưng lịch sử 7 ngày 0,745 ⇒
    **bản mới cảnh báo** `acceptance_below_threshold`, bản cũ thì không. Đây là ca cho thấy rõ
    nhất "advisor thôi dùng oracle".
  - Đối chứng ngược: **`d-2`** (cùng ngày 0,636 → lịch sử 0,881) — bản cũ cảnh báo, bản mới thôi.
    Xem để chắc rằng thay đổi không chỉ một chiều.
- **Người review + verdict:** chưa có.

## Adversarial self-review / flaws found

1. **Thay leak này bằng leak khác?** Đã chặn: `p0` cũng chỉ tính trên `local_date < date`. Nếu
   pool cả ngày hiện tại thì vừa gỡ leak cá nhân xong lại rước leak tập thể.
2. **Test có bắt được leak thật không?** Test tái tính **độc lập** từ dữ liệu thô rồi so, **và**
   ràng buộc kết quả ≠ tỷ lệ cùng ngày, **và** ràng buộc không phụ thuộc `now_min`. Ba mặt — một
   mình "≠ cùng ngày" thì một implement sai vẫn có thể qua.
3. **Đánh đổi thật, phải nói rõ:** ta mất khả năng thấy **hành vi TRONG ngày hôm nay**. Nhưng đó
   là khả năng **hệ thống thật chưa bao giờ có** — 13 bảng không có accept/decline mức sự kiện
   (hồ sơ 08 §5.3). Không phải mất mát, là **thôi giả vờ có**.
4. **`m = 20` từng là mắt xích yếu nhất — đã quét độ nhạy ngay trong cycle này** (§5): kết luận
   chỉ đổi 1,1–4,1% khi `m ∈ [5,50]`, vì `m ≪ n` (20 so với 81). Điều tôi lo (kéo mọi người về
   prior, mất khả năng phân biệt) **có thật nhưng chỉ ở `m = 200`**, ngoài dải dùng. Vẫn chưa
   *hiệu chỉnh* `m` bằng dữ liệu thật — chỉ mới chứng minh **kết luận không nhạy** với nó.
4b. **Chính script quét đầu tiên của tôi có BUG** — gán `base` khi `m==20` nhưng vòng lặp chạy
   `5,10,20,...` nên `m=5/10` so với `base` rỗng và in ra "0 đổi kết luận". Con số 0 đó **trông
   như bằng chứng rất đẹp** cho `m` không quan trọng. Đã phát hiện và chạy lại đúng (tính `k,n`
   một lần, so sau). Số trong §5 là của lần chạy đã sửa.
5. **Ít cảnh báo hơn có phải là "làm nhẹ cho đẹp số" không?** Không — và tôi đã kiểm hai chiều:
   có 4+ ca **thêm** cảnh báo (`d-37`, `d-11`, `d-5`, `d-48`) chứ không chỉ bớt. Nếu chỉ một
   chiều thì mới đáng nghi.
6. **Chưa nối vào sim** (việc 3b) ⇒ tạm thời sim và UI **vẫn dùng hai estimator khác nhau** — tức
   yêu cầu "một luật" của Cường **chưa xong**, chỉ mới hết leak. Nói rõ, không tính là đã đạt.
7. **`lru_cache` trên `_pooled_prior`** khoá theo `(kind, date)` — an toàn vì dataset bất biến
   trong một tiến trình. Nếu sau này regen data lúc server đang chạy thì cache sẽ cũ; ghi nhận.

## Expansion checkpoint (T-039)

1. **Schema**: không cần đổi. Nhưng nếu GSM cấp được **accept/decline mức sự kiện** thì mở ra ước
   lượng trong-ngày thật (G-mới) — đáng đưa vào danh sách xin dữ liệu §4 spec objective v2.
2. **Bài toán tối ưu**: có `p̂` as-of rồi thì hỏi được câu chưa ai giải: *"tới giờ này, nhận thêm
   bao nhiêu cuốc nữa thì tỷ lệ luỹ kế vượt ngưỡng, và rẻ nhất là nhận loại nào"* — sim đã có
   `_acceptance_recoverable` trả có/không, chưa trả chi phí.
3. **Tính năng**: hiển thị "tỷ lệ ước lượng theo 7 ngày gần nhất" kèm khoảng tin cậy là card F1
   trung thực và rẻ.

## Follow-up / defer phát sinh

- **T-042 việc 3b** (kế tiếp): nối `shrunk_rate` vào **sim** để hết hai-estimator, diệt tận gốc
  0/0→1.0 (BUG-DSIM13-02) thay vì vá bằng `acc_est`. ⚠ **Sẽ làm lệch baseline 30 seed** ⇒ phải đo
  lại chỉ tiêu kép trong cùng cycle.
- ~~Quét độ nhạy `m`~~ **XONG trong cycle này** (§5): kết luận robust với `m ∈ [5,50]`.
- **Hiệu chỉnh `m` bằng dữ liệu** (ĐA-01 yêu cầu 30-seed recalibration) — chưa làm.

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-12 · **V-13** (card "thưởng sắp mất", không dựng được ca
thật) · **V-14 MỚI** (ĐA-01 — **có ca thật `d-37`/`d-2`**) · Q-03, Q-04 chưa duyệt ·
**ĐA-06 đã CHỐT 2026-07-27, không nhắc nữa** (ràng buộc thi công ở T-044) · B-02 ARCH-VERSION vẫn
mở và **chặn T-044** · **chưa commit gì cả phiên**.
