# RESEARCH — Kế hoạch & trạng thái nghiên cứu thực tế

Cập nhật: 2026-07-20 · Trạng thái: **HOÀN TẤT ĐỢT 1 + ĐỢT 2** (T-001, T-012). Findings hiện nằm trong `research/`, chia theo loại; gap cần người thật đọc group Facebook là T-013.

## 1. Mục tiêu nghiên cứu

1. **Features thực tế ảnh hưởng thu nhập**: cước/doanh số, thưởng, phần chia nền tảng, chi phí tự chịu (sạc, thuê xe, khấu hao), ngưỡng policy.
2. **Các cách tài xế có thể tăng thu nhập**: chương trình thưởng theo chuyến/điểm/khung giờ, sắp xếp thời gian chạy–nghỉ–sạc, duy trì điều kiện profile.
3. **Root cause của pain point**: không nắm policy đúng track/version, sạc sai thời điểm, chạy giờ thấp điểm, thiếu điều kiện thưởng, nhầm gross/payout/net.
4. **Số liệu để mock**: hình dạng demand theo giờ/ngày/khu vực và dải thu nhập tự khai để sanity-check — luôn phân biệt FACT / PROXY / MOCK.

## 2. Nguồn đã tra cứu

- Nguồn official: `greensm.com`/`xanhsm.com`, policy/news tuyển dụng, bộ quy tắc ứng xử, Q&A/chương trình thưởng.
- Press: VnExpress, Tuổi Trẻ, CafeF/CafeBiz, VietnamNet, VOV, báo chuyên ngành.
- Community: VOZ, diễn đàn VinFast, YouTube/tài xế tự khai; tối đa medium confidence và không là authority policy/số tài chính.
- Market/research proxy: Mordor, Rakuten Insight, Q&Me; Didi/NYC/Chicago/Haikou chỉ dùng cho hình dạng/hệ số, không làm fact GSM.
- Facebook groups: mới định danh tên/URL do login wall; cần Cường/Khánh join tay nếu tiếp tục T-013.

## 3. Câu hỏi đã trả lời một phần

- Đã lập timeline policy/chia sẻ doanh số và bảng thưởng có version/effective date; vẫn thiếu tỷ lệ chi tiết từng khung giờ cho policy hiện hành.
- Đã xác nhận policy khác nhau theo track/cohort/market; không được trộn Platform, RTO và employee.
- Đã xác định các pain point lặp lại: sạc/đổi pin, giờ chạy dài, áp lực điều kiện nhận/hoàn thành, policy đổi nhanh.
- Đã xây demand proxy v1 cho Bike Hà Nội tại `specs/mock-order-distribution.md`; chưa có dữ liệu GSM theo giờ/khu vực để hiệu chỉnh mức tuyệt đối.
- Quy trình khiếu nại/giải trình đã defer sang D-007 (dự án khác).

## 4. Đầu ra & nơi lưu

- `research/00_SUMMARY.md` — tổng hợp đọc trước.
- `research/policy/` — chính sách, thưởng/phạt, version/effective date.
- `research/economics/` — cấu trúc Gross / Driver payout / Estimated net và chi phí theo track.
- `research/community/` — pain points, kinh nghiệm, findings tự khai, danh sách group.
- `research/market/` — market/demand distribution research + proxy.
- `specs/` — đặc tả kỹ thuật để code; không trộn với raw findings.

Kết quả đang được dùng để: xác nhận pain point/root cause, thiết kế **5 persona mock**, tham số hóa mock demand proxy, và chuẩn bị policy KB F0. Mọi số chưa xác nhận đánh dấu `TBD`/`MOCK`; không đưa vào sản phẩm như fact.
