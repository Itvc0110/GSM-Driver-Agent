"""Phân loại CHỦ ĐỀ lời khuyên: cái nào được ĐO mức nghe lời, cái nào KHÔNG.

Quyết định của Cường 2026-08-03 (`tracking/QUYET-DINH-2026-08-03-khuyen-mem-khong-do.md`):

> *"trong UI cũng không nên có trace đồng ý làm theo hay không làm theo khi gợi ý — tương tự
> đối với thời tiết"*

## Vì sao đây là ranh giới, không phải chi tiết UI

Đo *mức nghe lời* của một lời khuyên sức khoẻ **chính là** biến sức khoẻ thành chỉ tiêu để tối
ưu. Một khi `rest_adherence` tồn tại như một con số, nó sẽ được nhìn như thứ cần cải thiện — và
"cải thiện tỷ lệ tài xế chịu nghỉ" là tối ưu hoá trên sức khoẻ, đúng thứ
`specs/advisor-objective-model-v2.md` §1.2b cấm. Nút "Làm theo" trên thẻ nghỉ không phải một
widget; nó là một **tỷ giá sức-khoẻ↔KPI** được cài vào sản phẩm.

Nên khuyên mềm **không có mẫu số** — và điều đó là **THIẾT KẾ**, không phải thiếu dữ liệu. Phân
biệt này quan trọng: `decision_adherence = None` vì mẫu số 0 là *dấu hiệu có thể có bug*; còn
topic mềm **vắng mặt hoàn toàn** khỏi `adherence_view` là *ranh giới đang được thi hành*.

## Hai vai của `dismissed` — lẫn hai vai này là làm sai

| Vai | Nghĩa | Khuyên mềm |
| --- | --- | --- |
| **Nhịp nói** (ĐA-04) | *"đừng nhắc nữa trong pha này"* — để không làm phiền tài xế | ✅ **GIỮ** |
| **Thước adherence** | *"tài xế KHÔNG đồng ý với lời khuyên"* | 🚫 **CẤM** |

Cùng một cú bấm, hai nghĩa. Cường chốt: *"Giữ nút ẩn, bỏ nút Làm theo"* ⇒ tài xế vẫn tắt được
thẻ (vai 1 sống), nhưng hệ thống không bao giờ suy ra sự đồng thuận từ đó (vai 2 chết).

## Fail-closed

`classify()` trả `"unknown"` cho topic chưa khai, và cổng `tests/test_advice_topic_registry.py`
làm nó ĐỎ. Lý do phải fail-closed thay vì mặc định "được đo": mặc định im lặng làm điều sai là
mẫu lỗi repo đã trả giá 4 lần (`D-R12` · UPDATE-114 lỗ (a) · `D-M3-13` · `D-M3-15`). Thẻ mềm đầu
tiên ai thêm vào mà quên khai sẽ **tự động** rơi vào bảng đo — im lặng và đúng hướng có hại.
"""
from __future__ import annotations

from typing import Literal

# Chủ đề ĐƯỢC đo mức nghe lời. Đây là lời khuyên KINH TẾ: tài xế theo hay không theo là thông
# tin hợp lệ để đánh giá advisor, và không có tỷ giá sức khoẻ nào bị tạo ra.
MEASURED_TOPICS: frozenset[str] = frozenset({
    # --- sản phẩm (`ui/backend/app/routers/advice.py` CLIENT_TOPICS) ---
    "brief",            # thẻ trước ca (F1)
    "nudge",            # thẻ trong ca (F2)
    "recap",            # thẻ tổng kết ca (F3)
    "bonus",            # mặc định LỊCH SỬ của `AdviceAction.topic`; còn trong test/dữ liệu cũ
    # --- từ vựng của PIPELINE (`advice_spec.action_type`, `templates._advice_spec`) ---
    # `online` = *"cứ chạy tiếp"* — mặc định của `_advice_spec(action=None)`. Lời khuyên KINH TẾ,
    # đo mức nghe lời là hợp lệ. Khai ở đây từ UPDATE-136 (`N1`): trước đó `episode_store` không
    # ghi `topic` nên mọi quyết định pipeline có `topic=None` và **mặc định** vào bảng đo.
    # ⚠ `rest_window`/`shift_plan` mà pipeline cũng dùng đã có ở dưới — KHÔNG khai lại.
    "online",
    # --- kênh của sim (`world.py` channel=…, `parallel.CHANNEL_LADDER`) ---
    "positioning",      # pseudo-channel: kênh VỊ TRÍ (`wait_only`) — kênh duy nhất đang bật
    "shift_plan",       # TẮT theo ĐA-07 (đo ra có hại) nhưng vẫn là kênh ĐƯỢC ĐO khi bật
    "accept_lift",
    "shift_extend",
    # `rest_window` = HOÃN nghỉ (đổi THỜI ĐIỂM, không đổi lượng) = `C2′`. Nó nằm ở đây một cách
    # CÓ ĐIỀU KIỆN: Cường 2026-08-03 chọn *"thử D-M3-04 trước, nếu có ý nghĩa thì giữ, không thì
    # revert và khuyên mềm"*. Luật quyết định đã đăng ký TRƯỚC khi đo trong
    # `specs/simulation/d-m3-04-multiday-prereg-locked.json` → `luat_quyet_dinh`.
    # ⚠ Nếu D-M3-04 cho Δ ≤ 0 hoặc ns (là nhánh prereg DỰ ĐOÁN TRƯỚC, vì world β=0) thì chuyển
    # khoá này sang SOFT_TOPICS. ĐỪNG chuyển trước khi có số — và đừng giữ nó ở đây sau khi có
    # số âm chỉ vì "đã viết ở đây rồi".
    "rest_window",
    # --- từ vựng của ADVICE CHECKPOINT v2 (`ui/contracts/advice_v2.json`, `checkpoint.py`) ---
    # QĐ-4 (Cường chốt 2026-08-04): HỢP NHẤT. Trước đó v2 có từ vựng RIÊNG, giao với registry = RỖNG
    # ⇒ ranh giới `classify()` **không chạm được một event nào của v2**, và một checkpoint `rest`
    # nhận được `response: accepted` — tức TRACE ĐỒNG Ý cho lời khuyên NGHỈ đang được ghi.
    #
    # ⚠ Hợp nhất ở đây là hợp nhất **THẨM QUYỀN**, không phải đổi tên: `advice_v2.json` và dữ liệu
    # đã lưu giữ nguyên chuỗi cũ. Đổi tên sẽ phá contract của Khánh và mọi bản ghi lịch sử — đắt hơn
    # nhiều so với cái nó giải quyết. Cái phải là MỘT là **nơi quyết định topic nào được đo**.
    "bonus_eligibility",     # S1 — mốc thưởng. Kinh tế (`bonus_feasibility.py`: 0 hit
                             # rest/fatigue/soc/safety).
    # `energy` = SWAP. Xếp ĐƯỢC ĐO vẫn đứng, nhưng KHÔNG phải vì lý do tôi viết ban đầu
    # ("pin là điều kiện chạy, không phải sức khoẻ người") — `soc_low` được chính repo gọi là
    # **lan can sức khoẻ** ở §1.2b và ở `sim_metrics.REST_RAILS`. Lý do ĐÚNG: pin có **kênh tác hại
    # được mô hình hoá** (`world.py` log `battery_stranded`, `metrics.py` đếm nó), còn mệt thì
    # KHÔNG có kênh nào (`D-SIM-16`). Đo mức nghe lời của lời khuyên đổi pin không tạo ra tỷ giá
    # sức-khoẻ↔tiền vì hậu quả của nó đã nằm trong hàm mục tiêu một cách hợp lệ.
    "energy",
    # 🔴 `shift_boundary` gộp **END + EXTEND** — `checkpoint.py:138-141` trả cùng chuỗi này cho cả
    # hai. Comment cũ của tôi ghi "END ca. Kinh tế." và ghi EXTEND ở dòng `shift_timing` bên dưới:
    # **cả hai đều SAI**, và nửa EXTEND rơi qua khe giữa hai dòng comment ⇒ nó chưa từng được xét
    # khi tôi phân loại. Soi độc lập 2026-08-04 bắt được.
    # ⚠ EXTEND ("chạy thêm để với mốc thưởng") là **câu hỏi mở**, không phải kinh tế thuần — xem
    # `D-QD4-03`. Nó ở đây vì giữ NGUYÊN TRẠNG chờ Cường quyết (`V-28`), không phải vì đã xét.
    "shift_boundary",
    # `shift_timing` KHÔNG phải "EXTEND/đổi giờ" — nó là **nhánh mặc định cuối** của
    # `_topic_for_action`, hứng ONLINE · NO_ACTION · PROTECT_ELIGIBILITY(non-S1) ·
    # REPOSITION_SIM_ONLY(non-S4). Đo được: `S2 EXTEND -> shift_boundary`, không lần nào ra đây.
    "shift_timing",
    "positioning_sim_only",  # S4 vị trí — chỉ sim (`ProductSolverOrchestrator` không gọi S4).
    # ⚠ `policy_info` KHÔNG có producer nào: grep toàn repo cho đúng 2 hit — dòng khai này và bảng
    # ghim trong test. Nó tới từ enum contract chứ không từ code sinh ra thẻ. Giữ để enum v2 và
    # registry không lệch, nhưng đừng đọc nó như bằng chứng rằng kênh này tồn tại.
    "policy_info",
})

# Chủ đề KHUYÊN MỀM — nói vì đúng cho tài xế, KHÔNG kèm claim tiền, KHÔNG đo mức nghe lời.
SOFT_TOPICS: frozenset[str] = frozenset({
    "weather",          # cảnh báo thời tiết (Khánh sở hữu implement — chưa có thẻ nào hôm nay)
    "rest_nudge",       # GỢI Ý nghỉ khi làm quá sức (khác `rest_window` = HOÃN nghỉ)
    "traffic",          # cảnh báo mật độ giao thông — cùng họ với thời tiết
    # --- QĐ-4: từ vựng v2 + cadence, phần thuộc lớp MỀM ---
    # `rest` — ĐÍNH CHÍNH 2026-08-04 (soi độc lập). Bản đầu tôi viết nó "nhập nhằng vì gộp
    # `rest_window` với `rest_nudge`, sinh bởi S7". **Sai ở cả producer lẫn bản chất:**
    #
    # · **S7 KHÔNG chạy ở sản phẩm.** `ProductSolverOrchestrator` chỉ gọi S1 (`bonus_feasibility`)
    #   và S2 (`shift_dp`); contract chốt bằng máy: `advice_v2.json` → `solver_set.enum=["S1","S2"]`.
    #   Ở sản phẩm, `rest` sinh từ **S2** qua nhánh `code == "REST"` (`checkpoint.py:134`).
    # · **Không producer nào sinh `rest_nudge`.** S7 (`solvers/idle_reduction.py`) là *"dời nghỉ/sạc
    #   vào khung nhu cầu thấp"* — HOÃN, và input của nó không có trường mệt/sức khoẻ nào nên nó
    #   **không thể** biết tài xế quá sức. S2's REST là **sàn nghỉ tối thiểu** (`rest_min_per_4h`)
    #   đặt vào bucket demand thấp. Cả hai đều là lời khuyên **THỜI ĐIỂM**.
    #
    # ⇒ `rest` không nhập nhằng vì gộp hai thứ — nó **đặt chỗ trước cho một thứ chưa tồn tại**.
    #
    # Vẫn giữ MỀM, và nay có lý do MẠNH HƠN lý do ban đầu: `_topic_for_action` route theo
    # `code == "REST"`, nên **bất kỳ** solver nào mai sau trả action `REST` — kể cả một producer
    # mệt-mỏi thật — đều rơi vào khoá này. Xếp MEASURED là mở một cửa **vĩnh viễn** cho lời khuyên
    # sức khoẻ chui vào bảng đo, đổi lấy mẫu số của một lát cắt S2 hôm nay. Hai sai không cùng hạng
    # (§1.2c). Giá đang trả + phương án tách theo NGUỒN: `D-QD4-01`.
    "rest",
    "safety_reserved",  # v2 — cảnh báo an toàn. Sức khoẻ/an toàn ⇒ không đo mức nghe lời.
    "safety",           # `cadence.SAFETY_TOPICS` — từ vựng THỨ TƯ, cùng khái niệm `safety_reserved`
})

ALL_TOPICS: frozenset[str] = MEASURED_TOPICS | SOFT_TOPICS

TopicClass = Literal["measured", "soft", "unknown"]

assert not (MEASURED_TOPICS & SOFT_TOPICS), (
    "một topic không thể vừa được đo vừa là khuyên mềm: "
    f"{sorted(MEASURED_TOPICS & SOFT_TOPICS)}")


def classify(topic: str | None) -> TopicClass:
    """`None` ⇒ `"measured"`: đường ghi cũ không đặt `topic`, và chúng là kênh kinh tế.

    Không dùng `None` làm chỗ trú cho khuyên mềm — khuyên mềm phải khai tên tường minh, nếu
    không thì ranh giới này không kiểm được bằng máy.
    """
    if topic is None:
        return "measured"
    if topic in SOFT_TOPICS:
        return "soft"
    if topic in MEASURED_TOPICS:
        return "measured"
    return "unknown"


def is_soft(topic: str | None) -> bool:
    """True ⇒ topic này KHÔNG được vào tử số/mẫu số adherence, và KHÔNG nhận `followed`."""
    return classify(topic) == "soft"
