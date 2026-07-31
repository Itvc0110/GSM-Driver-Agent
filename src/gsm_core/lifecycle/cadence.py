"""AdviceCadencePolicy — MỘT LUẬT quyết định NHỊP nói của advisor (ĐA-04).

Design Cường duyệt 2026-07-27 (audit `04-*` §5): một component **deterministic, KHÔNG
nằm trong UI**, dùng chung sim và app — vì trước đó tồn tại ba semantics khác nhau (sim
theo tick, app theo giờ đồng hồ cứng, spec theo pha ca) nên A/B không đo đúng thứ sản
phẩm sẽ ship.

    evaluate(topic, now, phase, memory, safety) → PRESENT | QUEUE | SUPPRESS
                                                  + typed reason + next_eligible_min

Baseline đã duyệt (số ở `CadenceConfig`): ≥20′/topic · ≤6 proactive/ca · priority
safety > policy/bonus > demand · anchor theo **PHA CA** (bỏ wall-clock 09:00/14:00/21:30)
· while-driving → QUEUE theo safety class · **MỘT adherence draw cho (decision_id,
material_revision)**, không re-roll mỗi tick.

## Vì sao keyed coin quan trọng hơn vẻ ngoài của nó

Bản cũ rút coin tuần tự trên RNG stream MỖI TICK 2′ tới khi "thành công" ⇒ adherence
danh nghĩa 0,30 có hiệu dụng ≈ 1,0 (D-A3-01 washout; đo được decision 76,9% vs event
53,6% ở kênh accept_lift). Mọi kết luận A/B đều kế thừa sai số đó. `adherence_coin` là
hàm băm THUẦN của (seed, decision_id, material_revision): cùng quyết định ⇒ cùng coin,
hỏi lại 15 lần vẫn một câu trả lời; nội dung khuyên đổi thật thì mới có coin mới.

## Ranh giới SIM ↔ SẢN PHẨM (chỉ thị Cường 2026-07-29)

*"Việc đo hiệu quả của phần mềm trong sim không nên bị ảnh hưởng bởi việc tắt gợi ý khi
xế bấm nút bỏ qua — sim là để đo hiệu quả của một xã hội driver TUÂN THEO lời khuyên so
với một xã hội driver khi CHƯA CÓ hệ thống và làm việc với quy tắc random."*

⇒ `dismissed_for_window` là cơ chế của **sản phẩm thật (UI)**: tài xế bấm "Bỏ qua" thì
advisor im trong pha đó. **Sim KHÔNG dùng nhánh này** — sim không có nút bấm; việc "nghe
hay không nghe" đã được mô hình hoá bằng `adherence_coin` theo archetype. Hai test khoá
ranh giới này (`test_sim_never_suppresses_by_dismiss`,
`test_sim_cadence_memory_has_no_dismiss_state`).

Cooldown/ngân sách thì NGƯỢC LẠI — áp cho cả hai: sản phẩm thật sẽ có chúng, nên A/B
phải đo đúng thứ sẽ ship (đây chính là lý do ĐA-04 tồn tại).

Module này KHÔNG import gì của sim/UI — mọi caller tự dựng `CadenceMemory` từ nguồn của
mình (sim: RAM incremental; UI: `AdviceEventLog`), rồi gọi cùng `evaluate`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

PRESENT = "PRESENT"
QUEUE = "QUEUE"
SUPPRESS = "SUPPRESS"

# Chủ đề thuộc lớp AN TOÀN — priority cao nhất (design: safety > policy/bonus > demand):
# không bị chặn bởi budget/cooldown và KHÔNG hoãn khi đang chạy.
SAFETY_TOPICS = frozenset({"safety"})

# Độ rộng bucket định danh MỘT QUYẾT ĐỊNH (phút). Đây là NGUỒN SỰ THẬT DUY NHẤT —
# `world._decision_id` và coin tuân thủ PHẢI dùng cùng con số, nếu không một decision_id
# sẽ trải trên hai coin và washout sống lại im lặng (đã bị test bắt đúng 1 lần: coin
# dùng 20′ của cooldown trong khi decision_id dùng 30′ ⇒ 3 quyết định re-roll).
DECISION_BUCKET_MIN = 30.0


def decision_bucket(now_min: float, bucket_min: float | None = None) -> int:
    """Chỉ số bucket của quyết định tại `now_min` (mặc định 30′)."""
    return int(float(now_min) // float(bucket_min or DECISION_BUCKET_MIN))


@dataclass(frozen=True)
class CadenceConfig:
    """Số BASELINE đã duyệt. Design ghi rõ: *"coi 20 phút/6 advice là baseline đầu tiên;
    mọi tuning sau dựa trên telemetry/micro-randomized evaluation, không bằng cảm giác"*
    ⇒ ĐỪNG chỉnh mấy số này bằng trực giác; cadence chặt hơn phải là experiment ARM."""
    min_gap_min_per_topic: float = 20.0
    max_proactive_per_shift: int = 6
    # Độ rộng bucket định danh quyết định mà kênh này dùng (mặc định = hằng chung).
    # Kênh có nhịp ra quyết định khác (positioning: planner tick 60′) truyền giá trị của nó.
    decision_bucket_min: float = DECISION_BUCKET_MIN
    # Ranh giới pha ca theo TỈ LỆ thời lượng (hằng cấu trúc, không phải số kinh tế):
    # ca nào cũng có đầu/giữa/cuối, ca 6h và ca 12h được đối xử tương xứng.
    phase_early_frac: float = 0.25
    phase_late_frac: float = 0.75

    @property
    def effective_gap_min(self) -> float:
        """Cooldown THỰC THI = max(cooldown cấu hình, độ rộng bucket quyết định).

        L4-03 (phản biện 2026-07-31, reproduce được ở đường sản phẩm): cooldown 20′ NGẮN HƠN
        bucket quyết định 30′ ⇒ ở phút 21–29 cadence cho phép nói lại **về cùng một quyết
        định** — card tới tay tài xế thật, nhưng `event_id` trùng khoá bucket nên store
        dedupe: không event, không tiêu ngân sách 6 thẻ/ca. Tức trần ngân sách mất hiệu lực
        ở 33% thời gian, và mẫu số event hụt (họ lỗi `F-1`).

        Sửa bằng LUẬT DẪN XUẤT, không bằng hằng số mới (Cường 2026-07-31: *"mọi thứ phải
        được thống nhất"*): nói lại **trong cùng một bucket quyết định** là lặp lại chính
        mình, không phải lời khuyên mới. `gap ≥ bucket_width` ⇒ hai lần nói luôn rơi vào hai
        bucket khác nhau (chứng minh: `floor(t/b)` và `floor((t+b)/b)` luôn lệch 1) ⇒ bất
        biến **"một quyết định = tối đa một lần nói"** thành sự thật, không còn là lời hứa.

        `min_gap_min_per_topic = 20′` giữ nguyên là baseline Cường duyệt (`D-ĐA04-02`) —
        nó là SÀN, không phải giá trị cuối; trần do nhịp sinh quyết định của kênh áp đặt.
        Repo đã sập đúng họ lỗi này một lần ở phía coin (xem comment `DECISION_BUCKET_MIN`);
        đây là nửa còn lại.
        """
        return max(float(self.min_gap_min_per_topic), float(self.decision_bucket_min))


@dataclass
class CadenceMemory:
    """Tóm tắt lịch sử cần cho quyết định nhịp — caller tự dựng từ nguồn của mình.

    - `last_decided_min`: topic → phút lần CUỐI đã nói (cooldown).
    - `dismissed_in_phase`: topic → PHA mà tài xế bấm "Bỏ qua". Cường chốt 2026-07-29:
      cửa sổ im = **hết pha hiện tại** (không hằng số phút vô căn cứ; không im hết ca vì
      sẽ chặn cả cảnh báo an toàn/mất thưởng về sau).
    - `proactive_count`: số advice chủ động đã nói trong ca (ngân sách ≤6).
    """
    last_decided_min: dict[str, float] = field(default_factory=dict)
    dismissed_in_phase: dict[str, str] = field(default_factory=dict)
    proactive_count: int = 0


@dataclass(frozen=True)
class CadenceVerdict:
    verdict: str                      # PRESENT | QUEUE | SUPPRESS
    reason: str | None = None         # typed reason code (khớp schema lifecycle)
    next_eligible_min: float | None = None


def shift_phase(elapsed_min: float, shift_len_min: float,
                cfg: CadenceConfig | None = None) -> str:
    """Pha ca từ thời lượng ĐÃ TRÔI — thay wall-clock cứng của app (`KIND_HOURS`).

    Ca 10h: early < 150′ ≤ mid < 450′ ≤ late. Ca rỗng/không rõ ⇒ "early" (không chia 0,
    không đoán bừa)."""
    c = cfg or CadenceConfig()
    if shift_len_min <= 0:
        return "early"
    frac = max(0.0, float(elapsed_min)) / float(shift_len_min)
    if frac < c.phase_early_frac:
        return "early"
    if frac < c.phase_late_frac:
        return "mid"
    return "late"


def evaluate(topic: str, now_min: float, phase: str, memory: CadenceMemory,
             cfg: CadenceConfig | None = None, is_driving: bool = False) -> CadenceVerdict:
    """Có nên nói về `topic` lúc này không? Thứ tự xét = thứ tự ưu tiên đã duyệt.

    An toàn đi trước mọi thứ (không bị budget/cooldown/driving chặn). Sau đó: đang chạy
    xe ⇒ QUEUE (hoãn, KHÔNG mất — khác SUPPRESS); đã bấm Bỏ qua trong pha này ⇒ im;
    hết ngân sách ca ⇒ im; chưa đủ 20′ kể từ lần nói cuối cùng về topic ⇒ im kèm
    `next_eligible_min` để caller biết khi nào hỏi lại.
    """
    c = cfg or CadenceConfig()
    if topic in SAFETY_TOPICS:
        return CadenceVerdict(PRESENT)
    if is_driving:
        return CadenceVerdict(QUEUE, "unsafe_while_moving")
    if memory.dismissed_in_phase.get(topic) == phase:
        return CadenceVerdict(SUPPRESS, "dismissed_for_window")
    if memory.proactive_count >= c.max_proactive_per_shift:
        return CadenceVerdict(SUPPRESS, "shift_budget_exhausted")
    last = memory.last_decided_min.get(topic)
    if last is not None:
        eligible = float(last) + c.effective_gap_min
        if now_min < eligible:
            return CadenceVerdict(SUPPRESS, "topic_cooldown", eligible)
    return CadenceVerdict(PRESENT)


def adherence_coin(seed: int, decision_id: str, material_revision: str) -> float:
    """Coin tuân thủ trong [0,1) — hàm THUẦN của (seed, decision_id, material_revision).

    Thay cho `rng.random()` tuần tự: hỏi lại cùng một quyết định phải ra cùng câu trả
    lời (diệt washout D-A3-01/D-SIM-14). Dùng sha256 để phân bố đều và không phụ thuộc
    `PYTHONHASHSEED` (bài học digest run_id: `str()`/`hash()` không deterministic giữa
    các process).
    """
    key = f"{seed}\x1f{decision_id}\x1f{material_revision}".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big") / 2 ** 64
