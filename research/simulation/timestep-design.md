# Research — Thiết kế timestep phân tầng cho simulator (đợt 4)

Ngày: 2026-07-21 · Nguồn: T-022 · Phục vụ: `specs/simulation-pilot-world.md` + `specs/simulation-twin-world.md`
Trả lời yêu cầu #3 của Cường (2026-07-21 đợt 2): "nghiên cứu cách phân chia timestep đủ lớn".

## Kết luận: HYBRID — discrete-event làm lõi, tick chỉ cho dispatch + metrics

- **Pure DES thắng khi event thưa**: A/B Street bỏ fixed timestep 0.1s chuyển sang DES vì lãng phí tick; với 50 actors và khoảng lặng dài (chờ đơn, on-trip 8–15ph), timestep 1s lãng phí ~99% tick ([A/B Street](https://a-b-street.github.io/docs/tech/trafficsim/discrete_event/index.html)).
- **Dispatch/matching bản chất là time-triggered** (batched) → cần tick định kỳ riêng. FleetPy: sim `time_step` 1s nhưng fleet control 10–60s riêng ([FleetPy params](https://github.com/TUM-VT/FleetPy/blob/main/Input_Parameters.md), [arXiv:2308.05535](https://arxiv.org/pdf/2308.05535)).
- **SimPy hỗ trợ cả hai tự nhiên** (process generator + `while True: yield env.timeout(TICK)`); simulator EV ride-hailing trên SimPy chạy multi-day hàng nghìn trip trong vài phút ([arXiv:2411.19471](https://arxiv.org/abs/2411.19471)).
- **Pin/vị trí tính lazily tại biên event**, không update mỗi giây; vị trí nội suy khi render.

## Mốc thời gian tham chiếu từ industry/papers

| Nguồn | Đại lượng | Giá trị |
| --- | --- | --- |
| Ride-sourcing production ([arXiv:1902.06228](https://arxiv.org/pdf/1902.06228)) | Match window | **1–2s** |
| DiDi RL dispatching | Window "a few seconds"; sim replay 2s cycles | (2s chưa fetch được full text — đánh dấu) |
| Uber | Batch vài giây; offer window tài xế ~15s | |
| FleetPy | sim 1s / fleet control 10–60s / horizon 900s | |
| [arXiv:2503.13200](https://arxiv.org/html/2503.13200) | Sim second-by-second; khách hủy sau 5ph | |
| Demand granularity ([arXiv:2203.10301](https://arxiv.org/abs/2203.10301), 36 cấu hình Chengdu) | Bucket tối ưu | hexagon 800m + **30 phút**; ngành dùng 10–30ph |
| Battery swap 2-wheeler DES ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S095965262300313X)) | Service time | ~1 phút, M/M/C |

## Kiến trúc thời gian phân tầng ĐỀ XUẤT cho pilot (50 actors, 1 quận)

| Tầng | Cơ chế | Giá trị | Lý do |
| --- | --- | --- | --- |
| **T0 Trip/swap lifecycle** | Pure DES (SimPy process/actor; pin lazily tại biên event) | độ phân giải giây, duration làm tròn giây nguyên | DES rẻ + chính xác thứ tự tuyệt đối |
| **T1 Dispatch tick** | `yield env.timeout(5)` gom đơn + tài xế rảnh, giải assignment | **5s** (dải 2–10s) | Production 1–2s là cho pool nghìn đơn; 50 actors pool nhỏ, 5s << pickup 120–360s; quantization TB 2.5s ≈ 1–2% pickup |
| **T2 Demand/metrics bucket** | flush counters | **15 phút**/hex (metrics hệ thống có thể 5ph) | 30ph tối ưu prediction nhưng thô cho ca 4–8h; 5ph quá nhiễu với 50 actors; 15ph = 16–32 điểm/ca |
| **T3 Advisor anchor** | hybrid anchor + event-trigger | **30 phút** định kỳ + trigger (sau swap, idle >10ph, đầu/cuối ca) | advisor đọc số từ T2; quyết định tài xế có thời gian đặc trưng 30ph–giờ; khớp `advice-timing-state-memory.md` |
| **T4 Viz frame** | KHÔNG mô phỏng theo frame — log event + nội suy lúc render | frame 1s sim-time, tua nhanh tùy ý | event log là source of truth; tránh phình log |

Chỉ **T1 là tick thật**; T2 flush rẻ; T3/T4 derive từ log → engine gần như pure DES, rất nhanh với 50 actors.

## Sensitivity protocol — kiểm tra "đủ mịn" (timestep-halving convergence)

1. Metrics nhạy thời gian: p50/p90 wait khách; % đơn expire; p90 queue trạm swap; payout/ca; utilization.
2. Chạy cặp cùng seed: T1 = 5s vs 2s (+1 run 15s xem hướng lệch); T2 = 15ph vs 5ph.
3. So **paired difference per-seed** (N=20 seeds — tận dụng hạ tầng CRN sẵn có).
4. Chấp nhận khi |mean Δ| < 2% giá trị metric HOẶC < ½ SD giữa các seed (sai lệch do tick chìm dưới nhiễu). Không đạt → hạ 2s, lặp với 1s.
5. Soi artifact: histogram wait có "răng cưa" tại bội số tick; thứ tự vào queue swap có đổi; số đơn expire sát biên timeout có nhảy bậc.
6. Làm 1 lần khi chốt engine; lặp khi đổi tham số lớn.

## Determinism & CRN pairing cho twin-world (3 arm) — PHẦN DỄ SAI NHẤT

1. **SimPy tie-breaking deterministic trong 1 run** (heap tuple `(time, priority, eid, event)` — đã xác minh source [simpy/core.py](https://gitlab.com/team-simpy/simpy/-/raw/master/src/simpy/core.py)) nhưng `eid` KHÁC giữa các arm ngay khi quyết định khác → không dùng eid để pairing. Cần:
   - **Priority tường minh theo loại event** cùng timestamp: `trip/swap hoàn thành (giải phóng supply) < đơn mới nổ < dispatch tick < metrics flush`; đơn nổ đúng biên tick → VÀO batch đó (quy ước chốt).
   - **Sort mọi iteration bằng key ổn định** (actor_id, order_id); cấm duyệt set/dict theo insertion order.
2. **CRN đúng cách**: tách RNG stream theo mục đích `(entity_id, purpose)` bằng `numpy SeedSequence(root).spawn()`; 1 RNG toàn cục sẽ lệch pha toàn stream chỉ vì 1 lần gọi thêm ([Glasserman & Yao guidelines](https://business.columbia.edu/sites/default/files-efs/pubfiles/4261/glasserman_yao_guidelines.pdf), [KSL Ch.9](https://rossetti.github.io/KSLBook/ch9VRTs.html)).
3. **Mạnh nhất — pre-generate exogenous trace**: sinh trước toàn bộ demand (timestamp, hex đón/trả, base duration, hệ số traffic) thành trace; cả 3 arm replay cùng trace, chỉ khác quyết định nội sinh. CRN hoàn hảo by construction (DiDi cũng replay-based). Chỉ biến phụ thuộc trạng thái nội sinh mới cần stream per-entity.
4. **Test bắt buộc**: (i) mỗi arm chạy 2 lần cùng seed → log identical từng byte; (ii) diff trace ngoại sinh giữa các arm → identical; (iii) chạy máy/Python version khác nếu được (bắt hash-ordering bug).

## Ghi chú trung thực

Giá trị 5s/15ph/30ph là tổng hợp đề xuất cho quy mô 50 actors (không phải số nguyên văn từ 1 paper) — sensitivity protocol ở trên là cách kiểm chứng chúng. "2-second dispatching cycles" của DiDi chỉ thấy trong search snippet, chưa fetch được full text; match window 1–2s đã xác nhận độc lập qua arXiv 1902.06228.
