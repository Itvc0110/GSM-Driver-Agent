> ⚠️ **DEFERRED — 2026-07-20.** Tài liệu thuộc cách tiếp cận cũ (full multi-variable constrained optimization). Scope hiện hành: `CLAUDE.md` + `planning/SCOPE.md`. Chỉ dùng tham khảo (xem `tracking/DEFERRED.md`, mục D-001). Danh sách nguồn ở đây là input tốt cho `planning/RESEARCH.md`.

# 09 — Research References and Design Evidence

Ngày truy cập: `2026-07-16`. Nguồn chính thức/primary được ưu tiên; kết quả học thuật là evidence định hướng, không phải cam kết sẽ tái lập trên GSM.

## 1. Green SM/GSM context

- [Green SM Driver — Google Play](https://play.google.com/store/apps/details?id=net.gsm.driver.app): app dành cho đối tác tài xế, hỗ trợ passenger transport và parcel delivery cho xe máy; trang công khai nói tài xế có thể chọn thời gian/khu vực. Ảnh hưởng: cần capability/service config và không giả định chỉ có taxi car.
- [Green SM — Google Play](https://play.google.com/store/apps/details?id=com.gsm.customer): hệ sinh thái công khai gồm Car, Bike, Express và Food tại Việt Nam, 100% electric positioning. Ảnh hưởng: data/service/energy model phải extensible.
- [Green SM Car](https://www.greensm.com/vn-vi/greensm-car) và [Tuyển dụng tài xế ô tô](https://www.greensm.com/vn-vi/driver-car): trang công khai liệt kê nhiều phân khúc Car/Mini/Premium/Limo và mô tả quyền lợi/compensation car gồm thành phần lương, thưởng/hoa hồng theo chính sách. Ảnh hưởng: không dùng một economics model chung cho mọi tài xế; policy effective-dated.

## 2. Driver earnings, rebalancing and fleet externality

- Chen et al., [i-Rebalance: Personalized Vehicle Repositioning for Supply Demand Balance](https://arxiv.org/abs/2401.04429): preference/adherence khác nhau giữa tài xế; personalized recommendation và field study. Ảnh hưởng: explicit/learned preference + voluntary response, không assume compliance.
- Chaudhari et al., [Learn to Earn: Enabling Coordination within a Ride Hailing Fleet](https://arxiv.org/abs/2006.10904): objective driver/passenger/platform có thể lệch; coordination và explainability quan trọng. Ảnh hưởng: hierarchical objectives và fleet-level guardrails.
- Brar et al., [Vehicle Rebalancing Under Adherence Uncertainty](https://arxiv.org/abs/2412.16632): recommendation không deterministically tạo supply; trust/adherence đổi theo outcome, fleet recommendations cần tính over/under-supply. Ảnh hưởng: capacity, probabilistic adherence, closed-loop feedback.
- Xu et al., [When Recommender Systems Meet Fleet Management](https://doi.org/10.1145/3366423.3380287): driver repositioning là kết hợp recommendation và fleet management, không chỉ ranking độc lập. Ảnh hưởng: Phase 2 centralized allocation.
- Hsieh et al., [A Decision Framework to Recommend Cruising Locations](https://doi.org/10.1145/3490687): traffic-network và spatiotemporal prediction cần được xem cùng nhau. Ảnh hưởng: travel-time distribution/reachability trong value, không dùng heatmap đơn thuần.
- [Putting Data in the Driver's Seat: Optimizing Earnings for On-Demand Ride-Hailing](https://doi.org/10.1145/3159652.3159721): formalizes driver strategies/dynamic programming for expected earnings. Ảnh hưởng: sequential planning baseline.

## 3. Optimization/tooling

- [Google OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver): CP-SAT cho integer constraints và trả status `OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN`. Ảnh hưởng: integer money/time/energy, status/gap/timeout trace; không gọi FEASIBLE là OPTIMAL.
- [Google OR-Tools Routing](https://developers.google.com/optimization/routing): routing/time-window/capacity primitives. Ảnh hưởng: candidate/tool option, nhưng Phase 1 không route order.
- [FastAPI](https://fastapi.tiangolo.com/) và [PostGIS](https://postgis.net/): typed Python API và spatial storage/query. Ảnh hưởng: default stack cho small team, không phải requirement nếu repo hiện hữu có standard khác.
- [MLflow Tracking](https://mlflow.org/docs/latest/ml/tracking/): experiment/model metadata lineage. Ảnh hưởng: model/eval version tracking hoặc compatible internal abstraction.

## 4. Current legal/privacy context to hand to counsel

- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=), hiệu lực 2026-01-01, và [hướng dẫn công khai về dữ liệu vị trí](https://xaydungchinhsach.chinhphu.vn/quy-dinh-bao-ve-du-lieu-ca-nhan-doi-voi-du-lieu-vi-tri-ca-nhan-du-lieu-sinh-trac-hoc-119250730155653784.htm). Ảnh hưởng: location/home/history cần purpose, minimization, security, subject-rights và counsel mapping.
- [Tóm tắt sửa đổi thời gian lái xe theo Luật 118/2025/QH15](https://xaydungchinhsach.chinhphu.vn/noi-dung-co-ban-cua-luat-118-2025-qh15-sua-doi-bo-sung-mot-so-dieu-cua-10-luat-co-lien-quan-den-an-ninh-trat-tu-119260123142251615.htm): quy định đã thay đổi theo thời gian. Ảnh hưởng: không hard-code số giờ từ tài liệu cũ; dùng approved policy service với effective date.

Đây không phải tư vấn pháp lý. Legal/Safety/Privacy owner phải xác nhận rule áp dụng cho từng engagement model, loại xe, dịch vụ và thị trường trước live.

## 5. Input attachment incorporated

Phản hồi “sol 5.6” đính kèm đã cung cấp pain-point map, Driver Income OS framing, shift/opportunity/bonus/charging/break/homeward/coach concepts, fleet-herding risk và research hypotheses. Pack này giữ các insight đó nhưng bổ sung: dispatch boundary, action taxonomy theo phase, formal objective/constraints, agent boundary, mock provenance, contract/API, experiment interference, ROI model, two-developer scaffold, CI/CD và PHASE/FIX/MEMORY governance.
