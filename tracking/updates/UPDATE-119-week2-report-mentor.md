# UPDATE-119 — Week 2 Report gửi mentor: HAI bản PDF (brief 6 trang + kỹ thuật 30 trang)

Ngày: 2026-08-01 · Trạng thái: `WAITING-VERDICT` (chờ Cường xem PDF) · Hướng: **docs/deliverable**

## Yêu cầu

Cường yêu cầu một bản **Week 2 Report — Driver Advisor Team** (Trần Quốc Khánh · Lưu Thiện Việt
Cường) gửi **mentor để đánh giá**, tập trung: hướng sản phẩm · định hướng từng feature · **toán ứng
dụng học thuật** · thiết kế sim (actor/state/action/cách chọn tối ưu) · luồng dữ liệu qua field
schema · guardrails · architecture choice · agent đặt ở đâu · UI/UX kèm ảnh · CI/CD · fairness ·
**bảng kết quả đo được nhiều vòng** · bài học → mục tiêu tuần 3. Sản phẩm: **một folder** để team
gửi teammate audit, và (đổi kế hoạch giữa phiên) **in luôn PDF cuối**.

Bốn điểm chốt qua AskUserQuestion: tuần 2 = **23/07–01/08** · **tiếng Việt** (thuật ngữ kỹ thuật
giữ EN) · tự chụp UI, fallback render từ code · Markdown nguồn → sau đó Cường đổi thành **in PDF**.

## Files

**TẠO** `docs/reports/week2/`:

| File | Nội dung |
| --- | --- |
| `Week2-Bao-cao-Brief.pdf` | **BẢN BRIEF — 6 trang** cho mentor/stakeholder đọc một lượt |
| `Week2-Bao-cao-Brief.md` | Nguồn bản brief — viết lại bằng ngôn ngữ thường ngày, 0 jargon |
| `Week2-Bao-cao-ky-thuat-chi-tiet.pdf` | **BẢN CHI TIẾT — 30 trang** |
| `Week2-Report-Driver-Advisor-Team.md` | Nguồn bản chi tiết (17 mục) |
| `report.html` · `brief.html` | Dẫn xuất (CSS in ấn A4 + MathML) |
| `build_pdf.py` · `build_pdf_brief.py` | md → HTML → PDF bằng playwright/chromium |
| `make_figures.py` | **7 biểu đồ** (4 bản kỹ thuật + 3 bản brief nhãn tiếng Việt), **đọc số từ artifact JSON**, fail-loud nếu thiếu khoá |
| `AUDIT-CHECKLIST-cho-Khanh.md` | ⭐ tài liệu để Khánh soi lại (5 phần, có ô ký tắt) |
| `NGUON-SO-LIEU.md` | Mọi số → file:line hoặc artifact |
| `HUONG-DAN-DUNG-PDF.md` | Cách sửa nội dung rồi in lại + 3 bước tự kiểm |
| `assets/` (21 ảnh) | 4 của Khánh · 7 Track UI · 3 dashboard · 7 biểu đồ (screenshot đã crop) |

**TẠO** `specs/simulation/e11-plan-nghi-co-gia-tri.md` — plan cũ (E11 nghỉ-có-giá-trị) được lưu
lại theo yêu cầu Cường *"lưu plan cũ lại rồi viết đè sau"*; `PENDING-REVIEW` V-20 nay trỏ tới nó.

**XOÁ** `gsmimage-20260801T034156Z-1-001.zip` khỏi workspace (Cường yêu cầu, sau khi 4 ảnh đã vào
`assets/`).

## Đối chiếu toàn dự án trước khi viết (Cường yêu cầu dùng subagent)

Workflow 12 mảng × (thu thập + phản biện) = **24 agent, 0 lỗi, 3,6M token, 29 phút**:
**494 finding · 525 số có nguồn · 279 khoảng trống · 309 cảnh báo**. Agent phản biện được giao
nhiệm vụ *tìm chỗ sai* (số không nguồn · claim quá mạnh · số đã bị UPDATE sau đính chính), không
phải xác nhận.

## 🔴 Verify doc của Khánh — Cường nhắc *"có thể không hoàn toàn chính xác"*

**Một lỗi nghiêm trọng:** doc Khánh trích `+6.016đ`. `UPDATE-113:109` ghi nguyên văn *"CI [2.854,
5.033] **không chứa +6.016** ⇒ **không tái lập được trần điểm cũ**"*. Artifact
`41-e10-diff.json` còn **tự ghi** `"ref_update087": 6016` để đánh dấu là số cũ. Số hiện hành:
**+3.939đ** (oracle) / **+3.126đ** (real).

**Hai chỗ thiếu ngữ cảnh:** `−17.310đ` là của cấu hình `shift_plan` **đã bị ĐA-07 TẮT vì có hại**;
`ui/README.md` mô tả cấu trúc `UIUXgsm/` không còn đúng + *"100% Green Coverage"* là marketing +
danh sách 5 tab khác code Flutter thật.

**Nhưng phần lớn Khánh trích ĐÚNG** (đã ghi vào checklist để không sửa oan): H3 res 9 ~85 ô ·
1.200 đơn/ngày · 9 solver · 50→90 actor · dispatch 0,761→0,764 / 233→228 / 1,04→0,98 km / 2,9→2,7s
· OSRM là thật · ranh giới sản phẩm.

**Hai câu hỏi cho Khánh** (đã ghi trong checklist): text chat trong ảnh là từ solver S1 thật hay
mockup Stitch? · Flutter gửi `scenario_id`/`seed` mà backend bỏ qua — chủ ý hay drift?

## Ba điều tôi tự sửa sau khi ĐO (không phải suy luận)

1. **Tôi đã nghi sai "chưa có API ngoài nào".** Agent tìm ra: có **đúng một** lời gọi runtime —
   `POST /api/v1/routing/calculate` gọi OSRM public qua `urllib.request.urlopen`. Nên ảnh "CUỐC
   OSRM REAL" của Khánh là thật.
2. **Đọc journal workflow sai field** (`value` thay vì `result`) rồi tưởng 11 agent trả null.
   Chúng trả kết quả đầy đủ. Cùng họ bẫy #10 (đừng kết luận từ một giá trị rỗng).
3. **`λ̂` render lệch dấu mũ** — kiểm bằng cách chụp 5 biến thể rồi xem thật: MathML (HTML) và
   mathtext `r"$\hat\lambda$"` (matplotlib) mới đúng. Đã đưa cả hai vào code + hướng dẫn.

## Phát hiện mới trong lúc chụp ảnh

🔴 **UI Khu Mô phỏng đang demo cấu hình ĐÃ BỊ BÁC BỎ.** Bấm "Chạy cặp A/B" cho
`Δ payout = −10.819đ` (ÂM), vì dòng chú thích ngay trên ảnh ghi *"Kênh: all (accept_lift +
shift_extend + rest_window + shift_plan)"* — tổ hợp mà ĐA-07 đã tắt. Nếu mentor mở UI sẽ thấy Δ âm
trong khi report báo Δ dương. **Tôi đưa ảnh này vào report kèm giải thích thay vì che**, và xếp
việc đổi default UI vào mục tiêu tuần 3.

Kèm hai xác nhận độc lập cho cảnh báo của agent: `dashboard.py` tạo **7 tab** (docstring nói 4 —
stale); Track UI web có bottom-nav **khác** app Flutter.

## Kiểm chứng

- **4 biểu đồ**: đọc số từ `41-e10-diff.json` + `44-e10blow-summary.json`, fail-loud nếu thiếu
  khoá. **Đã xem thật từng hình** và sửa 3 lỗi: nhãn đè tiêu đề · chú thích +6.016 không hiện ·
  `λ̂` mất dấu.
- **Ảnh UI**: chụp thật qua backend `:8077` + Streamlit `:8078`. Hai tab (`Chuyến của tôi`,
  `Xe & Pin`) và chat fab **timeout** ⇒ **bỏ, không bịa** (ảnh chat đã có từ Khánh).
- **PDF tự kiểm 3 bước** (làm cho cả hai bản): `pypdf` → brief **6 trang**, chi tiết **30 trang**; dấu tiếng Việt + công thức OK;
  `809`/`865` = **0 lần**; `6.016` xuất hiện 3 lần và **cả 3 đều có ngữ cảnh đính chính** (kiểm
  từng đoạn 190 ký tự quanh mỗi lần); `pymupdf` render 3 trang ra PNG để **xem layout thật**.
- **Không chạy suite** vì cycle này không đổi code sản phẩm (chỉ thêm `docs/` + `specs/` + 2 script
  trong `docs/`).

## Adversarial self-review / flaws found

- **Tôi ghi đè plan file TRƯỚC khi đọc tin nhắn "lưu plan cũ lại"** của Cường. Nội dung không mất
  (còn trong context, đã bảo toàn nguyên văn rồi ghi ra `specs/`), nhưng đúng ra phải hỏi trước khi
  overwrite một file người khác có thể còn cần. Bài học: plan file là **tài sản của người dùng**,
  không phải scratch của tôi.
- **Report có 2 số tôi KHÔNG verify được về artifact gốc**: `−19.654đ`/`+27.416đ`/`+3.610đ`/
  `+5.350đ` (bảng sign-flip) và chuỗi suite `850→1.000` chỉ trích được về **UPDATE**, không về
  artifact JSON. Đã khai rõ trong `NGUON-SO-LIEU.md` §6 và §9 rằng nguồn là UPDATE. Nếu mentor đòi
  artifact thì phải đo lại.
- **`Q-14` làm yếu mọi con số A/B trong report** (UI chỉ chạy 1/9 solver ⇒ A/B đo sản phẩm khác
  sản phẩm ship). Tôi đã nêu ở §13.2 nhưng **không** nêu ở đầu §11 — người đọc nhanh có thể bỏ
  qua. Cân nhắc thêm một dòng ở §11 nếu Cường thấy cần.
- **Chưa kiểm PDF trên máy khác.** Font `Segoe UI` có sẵn trên Windows; nếu mentor mở trên macOS/
  Linux thì chromium đã **embed font** (đã xác nhận `FontFile` trong PDF) nên chữ không đổi — nhưng
  tôi chưa test thật trên hệ khác.
- **21 ảnh; bản chi tiết chèn 8, bản brief chèn 13.** Còn `ui-track-02-thu-nhap`, `ui-track-06/07-*`,
  `dashboard-02/03` chưa dùng. Không phải lỗi, nhưng nếu Cường muốn report dài hơn về UI thì đã có
  sẵn ảnh.
- Cycle này **không chạy suite** — hợp lệ vì không đổi code sản phẩm, nhưng nghĩa là con số
  "1.000 passed" trong report là số đo lúc UPDATE-118, không phải đo lại hôm nay sau khi thêm
  `docs/`. (Thêm file trong `docs/` không ảnh hưởng suite.)

## Visual review

**`REVIEWED-SELF` / chờ Cường.** Tôi đã xem trực tiếp: 4/4 biểu đồ, 3 ảnh UI đại diện, và 3 trang
PDF render ra PNG. Cường cần xem **bản PDF** để cho verdict — đây là deliverable gửi ra ngoài nhóm
nên không tự waive.

## PENDING-REVIEW (nhắc lại theo yêu cầu Cường)

**20 mục đang chờ Cường check**: V-01…V-14, V-16, V-17, V-18, V-20 (nay trỏ tới plan E11 đã lưu),
V-21, V-22. Hoãn ≠ waive.

➕ `V-23` nay là **hai bản PDF** (brief + kỹ thuật chi tiết), chờ Cường xem trước khi gửi mentor.

➕ Thêm mục mới: **V-23 — bản PDF Week 2 Report** (`docs/reports/week2/`), chờ Cường xem trước khi
gửi mentor và trước khi commit.

## Vòng sửa theo phản hồi Cường (cùng ngày)

Cường yêu cầu bốn thay đổi sau khi xem bản đầu:

1. **Thêm bản BRIEF** cho stakeholder — 2-3 trang (sau nới thành *"4 trang cũng được do có nhiều
   hình"*, chốt ở **6 trang** khi Cường xác nhận *"6 ổn rồi"*). Viết **tự nhiên, không jargon**:
   mentor không quan tâm tên biến hay ký hiệu toán. Dùng **toàn bộ hình** đã dùng.
   ⇒ Sinh thêm **3 biểu đồ bản brief** với nhãn tiếng Việt (`fig-brief-*.png`) thay cho tên arm
   (`B_oracle`) và ký hiệu (`λ̂`, `KQ-GIỮ`). Kiểm lại: **0 jargon** còn trong text PDF brief.
2. **Đổi tên bản 24 trang** thành *"báo cáo kỹ thuật chi tiết"* + **bỏ icon đỏ** (4 chỗ).
3. **Rút gọn mục tiêu tuần 3** thành 4 hướng chung: UI/UX · thu thập thông tin hội nhóm tài xế để
   tìm pain point · cải thiện mô phỏng và thuật toán tối ưu hoá · nối kết quả tối ưu hoá + API
   ngoài qua agent để chuẩn hoá đầu ra.
4. **Bỏ hẳn "nối dữ liệu thật"** — Cường nhắc dự án **không** nối dữ liệu thật. Đây là chỗ tôi mô
   tả **sai định hướng**: bản đầu gọi việc chưa nối `from_l1r` là *"mắt đứt"* và xếp thành mục tiêu
   tuần 3. Sự thật là **lựa chọn phạm vi**: GSM cấp *cấu trúc* 13 bảng, dữ liệu vận hành thì nhóm
   không truy cập, nên nhóm dựng đường đọc đúng schema rồi chạy trên mock sinh cùng schema. Đã sửa
   §1 (M4), §6.4, §11.5 và bỏ mục *"Mong mentor góp ý"* ở cả hai bản.

**Kỹ thuật phát sinh:** bản brief đầu ra **9 trang** vì ảnh screenshot 3000px chiếm cả trang. Đã
**crop tự động** theo vùng nội dung thật (`ui-track-01-landing` từ 3000×2000 → 922×1842, chỉ còn
phần điện thoại) + giới hạn `max-height` theo loại ảnh ⇒ **6 trang**.

## Follow-up

- 🔴 **`D-M3-17`** vẫn là việc #0 của phiên sau (đã ghim ở `BOOTSTRAP-SESSION.md` §3 mục 0).
- Đổi cấu hình mặc định của Khu Mô phỏng về cấu hình duyệt (`positioning wait_only`) — phát hiện
  trong cycle này, đã vào mục tiêu tuần 3 §13.6.
- Chưa commit theo quy tắc: chờ Cường xem PDF.
