# UPDATE-067 — UX-CARDS: advisor thành Proactive Cards + đo adherence + CI draft

Ngày: 2026-07-27 · Track: **UI/UX** (chỉ thị §12) · Plan duyệt riêng · Xen giữa AUDIT (A1/A2 xong).

## 1. Quyết định nền (DIRECTIVES §12, chốt với Cường qua AskUserQuestion)

Bỏ chat tự do (F0 → FAQ tối giản, cycle riêng); advisor = **PROACTIVE CARDS** 3 thời điểm
(brief F1 · nudge F2 · recap F3) + nút **Làm theo/Bỏ qua/Vì sao** đo adherence EXPLICIT.
Neo research: nudge patterns Uber (earnings-gap, target-nudge, Hub; kèm bài học đạo đức — KHÔNG
nudge ép-chạy khi solver bảo infeasible) + NHTSA distraction (không visual-manual khi lái →
nudge CHỈ khi không chở khách, áp cả vào demo).

## 2. Files

- `ui/contracts/advice_action.json` (TẠO v1.0): advice_id/driver/date/action(followed|dismissed|
  expanded)/card_kind/at_min + is_mock — ghi rõ đây là đường đo EXPLICIT, đường IMPLICIT ở sim/A-B.
- `ui/backend/app/routers/advice.py`: +POST `/action` (append `data/ui-telemetry/advice_actions.jsonl`
  — gitignored, nhãn mock) + GET `/actions`; pydantic chặn action ngoài enum (422).
- `ui/web/js/cards.js` (TẠO): module Cards — render/animation/log; **im lặng = KHÔNG card**;
  nudge bị chặn khi `isDriving`; "Vì sao" = numbers[]+source+caveat (thay vai trò giải thích của chat).
- `ui/web/js/app.js`: brief tự hiện khi mở app; nudge bắn sau khi TRẢ KHÁCH xong; hub sheet thay
  chat (demo 90s + 3 nút thẻ + lịch sử thẻ); countup payout pill; khối "Nhật ký làm-theo" ở Cài đặt.
- `ui/web/index.html` + `theme.css`: card-stack + styles/animation (slide-in, followed→phải,
  dismissed→trái); hub sheet mới; `api.js` +2 hàm.
- `.github/workflows/ci.yml` (TẠO — **DRAFT, chưa active** tới khi Cường push remote): job test
  (2 suite) + JS syntax gate + nightly calibration 30-seed. `.gitignore` +`data/ui-telemetry/`.
- `ui/docs/SCREEN-PARITY.md`: hàng Trợ Lý đổi thành cards + việc Flutter cần làm (Khánh).

## 3. Kiểm chứng (số từ output thật)

- UI backend suite: **23 passed** (+2: round-trip POST→GET khớp schema qua monkeypatch tmp_path;
  action ngoài enum → 422).
- `node --check` 3 file JS sạch; launch thật `:8010` — cards.js/theme 200, POST action live →
  GET đọc lại đúng bản ghi.
- Suite chính KHÔNG chạy lại: diff không đụng `src/` (kiểm git status) — 504-green từ c540f33 còn hiệu lực.
- Visual: nhập **V-10** (kịch bản bổ sung): mở app thấy **brief card tự hiện** → bấm 🤖 → "▶ Demo
  Một ngày của tài xế" (~90s: brief → cuốc demo → nudge sau trả khách → recap) → thử Làm theo/Bỏ
  qua/Vì sao → Cài đặt xem "Nhật ký làm-theo".

## 4. Adversarial self-review / flaws found

- **F-UX-A (TB)**: nudge dùng advice 14h cố định (demo) — thật phải theo now-thực của ca; đúng
  cho mock review, ghi để làm khi có realtime state.
- **F-UX-B (THẤP)**: "Làm theo" hiện chỉ LOG — không đổi hành vi gì tiếp (đúng ranh giới: tài xế
  tự quyết, hệ thống không tự thực thi); ghi rõ để không ai tưởng nút có side-effect.
- **F-UX-C (THẤP)**: countup pill là hiệu ứng — số cuối luôn là số thật; kiểm code path.
- Recap card dùng advice 21h30 — có thể là item `info` infeasible → hiển thị trung thực "khó
  khả thi" thay vì động viên rỗng (đúng bài học đạo đức đã ghi trong plan).
- CI draft chưa test được vì chưa có remote — ghi rõ DRAFT trong file + backlog N5.

## 5. Follow-up

Flutter cards (Khánh — parity); F0-FAQ tối giản (cycle riêng); spec 2-đường-đo adherence (BACKLOG
Q6); AUDIT tiếp tục theo wakeup 02:40 (verify 11 + S2 + A3 + A4).

---
**⏳ PENDING-REVIEW (nhắc lại):** V-01..V-08 · V-09 · **V-10 (Track UI + UX-CARDS — kịch bản §3)**
· Q-03 (corpus Khánh — vai trò mới: nguồn FAQ tối giản).
