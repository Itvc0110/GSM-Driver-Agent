# UPDATE-089 — BẬT kênh VỊ TRÍ làm mặc định (Cường duyệt) + chốt tiêu chí per-archetype (uỷ quyền)

- **Ngày:** 2026-07-28
- **Người thực hiện:** AI agent, dưới claim của **Cường**
- **Loại:** config default change (được duyệt tường minh) + spec amendment + test reconcile
- **Verdicts nền:** Cường 2026-07-28: *"1. Duyệt · 2. Tự quyết theo phương án tốt nhất cho 1 dự
  án tầm cỡ · 3. Hỏi lại sau"* — trên đề xuất UPDATE-087.

## 1. Cấu hình mặc định mới (pilot_dongda.yaml)

```yaml
advice:
  channels:
    shift_plan: false            # ⛔ TẮT theo điều khoản bản-cuối ĐA-07 — bằng chứng n=100:
                                 #    thêm shift_plan trên nền positioning: thu nhập ns,
                                 #    served −0,33đp SIG, đơn chết +4,1 SIG
  positioning_overrides: wait_only   # ✅ PASS 9/9 ĐA-08 (n=100 seed tươi, UPDATE-087)
```

`advice.enabled` vẫn `false` (thế giới A mặc định) — đây là mặc định CỦA ADVISOR khi được bật,
không phải bật advisor cho mọi run.

**`CHANNEL_LADDER` sở hữu pseudo-channel `positioning_overrides`** (đọc trong `_cfg_with`):
không có nó, bậc "none" sẽ âm thầm thừa kế positioning từ default mới và "none = không can
thiệp" thành nói dối. Thêm bậc `"positioning"` (= B3w) cho attribution.

## 2. Tiêu chí 1 ĐA-08 — bản chốt theo uỷ quyền (AMENDMENT trong spec §5)

**(1a)** `payout_mean_all` > 0, CI 95% loại 0, n≥30 **VÀ (1b) no-harm guard**: không archetype
nào có Δ âm-SIG (báo cáo đủ P1..P7). Lý do: đòi từng archetype dương-SIG là bất khả về power
(chặn giả tạo); chỉ mean_all là bỏ equity — efficiency + non-inferiority per subgroup là chuẩn
thử nghiệm nghiêm túc.

**Kiểm ngay trên artifact 25 (B3w, n=100)** — cấu hình vừa bật thoả cả hai:

| P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|
| +5,8k SIG | +4,4k SIG | +8,4k ns | −0,3k ns | +6,7k SIG | +5,9k SIG | **+16,4k SIG** |

0/7 bị hại · 5/7 dương SIG. Ai hưởng nhiều nhất: **P7 ca tối-đêm** (khung đơn chết dày nhất —
đúng nơi positioning có đòn bẩy).

## 3. Test reconcile theo mặc định mới

- `test_off_is_bit_identical_to_flag_absent` → viết lại thành
  `test_default_is_wait_only_and_off_still_kills_the_channel` (bất biến đổi theo quyết định
  sản phẩm — ghi lý do trong docstring; "tắt được về baseline" vẫn nguyên, baseline giờ cần cờ).
- Placebo test evaluator: "mọi kênh tắt" nay gồm cả positioning (qua pseudo-channel).
- 29 test target xanh; full suite đang chạy khi viết UPDATE (kết quả điền vào commit).

## Kiểm chứng

Per-archetype guard chạy trực tiếp trên artifact 25 (bootstrap 2000, in ở transcript) ·
target tests 29 passed · full suite: xem commit message.

## Visual verification

`BLOCKED` — V-17 nay xem bằng ĐÚNG mặc định mới (không cần override config).

## Adversarial self-review / flaws found

1. **Đổi mặc định làm MỌI đo đạc advice-enabled sau này bao gồm positioning** — ai muốn đo
   kênh khác thuần phải dùng ladder (có pseudo-channel). Đã ghi vào comment CHANNEL_LADDER.
2. **P3 CI rất rộng** (−1,5k..+17,6k — chỉ ~2 tài xế P3/run) — no-harm guard với subgroup
   siêu nhỏ gần như không thể fail; guard thực chất bảo vệ các archetype đông. Ghi nhận giới
   hạn, không giả vờ guard mạnh hơn thực tế.
3. Bẫy free-rider 25–50% (UPDATE-088 §3) áp dụng cho giai đoạn adoption thật — mặc định sim
   `coverage: all` không mô phỏng nó; khi demo adoption phải nhớ.
4. UI advisor (`ui/backend`) đọc solver trực tiếp — kênh standby CHƯA có card UI tương ứng
   (advice vị trí chưa hiển thị cho tài xế trong app demo). Ghi nợ: cần card `standby_zone`
   + 5 safety flags ở tầng UI — việc mới, chưa claim.

## ⏳ Nhắc PENDING-REVIEW

V-01..V-17 (visual — "hỏi lại sau" theo verdict #3) · Q-03/Q-04/Q-07 · B-02 · nợ UI card
standby (mục 4 trên).
