"""Producer trong sim: đếm CUNG HIỆN TẠI và CUNG ĐANG TỚI từ `World` (T-045a b2).

## Vì sao `supply_incoming` là phần khó, và là phần đáng giá

Hồ sơ `19-*` §4: điều khiến view này khác một bản đồ nhiệt thường là nó trừ cả **tài xế đang trên
đường tới** — kể cả người **vừa nhận lời khuyên mà chưa kịp đi**. Không có nó thì 90 tài xế hỏi
cùng một lúc sẽ nhận **cùng một câu trả lời** (*fallacy of composition*, đo được ở hồ sơ `07`).

## Vấn đề kỹ thuật phải xử lý trước

`ActorState.ENROUTE` đang dùng cho **ba** việc khác nhau — đón khách (`world.py` dispatch),
deadhead về lõi, và relocate tìm khách — mà **không ai ghi lại ĐÍCH ĐẾN**; `actor.cell` chỉ đổi
khi tới nơi (`_set_pos`). Vì vậy phải thêm `Actor.enroute_cell`.

Đây đúng mẫu lỗi **T-046** *"sửa một tầng, tầng khác không biết"*: thêm trường ở producer mà quên
gán ở một trong các đường di chuyển thì cung đang-tới bị đếm thiếu **âm thầm**. Test cuối file
canh đúng chỗ đó.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from gsm_sim.config import Config
from gsm_sim.entities import Actor, ActorState, FleetType
from gsm_sim.market_state import MarketStateProducer, count_supply

ROOT = Path(__file__).resolve().parents[1]


def _a(actor_id: int, cell: str, state: ActorState, enroute: str | None = None) -> Actor:
    a = Actor(actor_id=actor_id, archetype="P1", fleet=FleetType.SWAP, home_cell=cell,
              shift_start_min=300.0, shift_end_min=1400.0, demand_prior_sigma=0.2,
              accept_base=0.9, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell, a.state, a.enroute_cell = cell, state, enroute
    return a


# ---------- đếm cung ----------

def test_relocating_actor_is_incoming_not_supply_now():
    """Người đang ĐI tới X: là cung của X (sắp tới), **không** là cung của ô đang đứng.

    Đếm họ vào ô hiện tại là nói dối hai lần: ô đó sắp mất người, ô kia sắp thừa người."""
    now, inc = count_supply([_a(1, "A", ActorState.ENROUTE, enroute="X")])
    assert now == {}, f"người đang di chuyển bị tính là cung tại chỗ: {now}"
    assert inc == {"X": 1}


def test_pending_advice_counts_as_incoming_before_the_driver_moves():
    """Lời khuyên VỪA PHÁT, tài xế chưa nhúc nhích ⇒ vẫn phải trừ trần của ô đó.

    Đây là điểm mấu chốt chống dồn cục: nếu chỉ đếm người đã lên đường thì trong cùng một bucket,
    mọi tài xế hỏi sau đều thấy ô X còn trống và đều được khuyên tới X."""
    actors = [_a(1, "A", ActorState.IDLE)]
    now, inc = count_supply(actors, pending_targets={1: "X"})
    assert now == {"A": 1}, "người đang chờ vẫn là cung tại chỗ cho tới khi thực sự đi"
    assert inc == {"X": 1}, "advice đã phát mà không trừ trần ⇒ 90 người nhận cùng một câu trả lời"


def test_actor_counted_once_when_advice_and_movement_agree():
    """Đã được khuyên đi X **và** đang trên đường tới X ⇒ đếm **một**, không phải hai.

    Đếm đôi làm ô X trông đầy hơn thực tế ⇒ advisor thôi khuyên tới đó quá sớm."""
    actors = [_a(1, "A", ActorState.ENROUTE, enroute="X")]
    _, inc = count_supply(actors, pending_targets={1: "X"})
    assert inc == {"X": 1}, f"đếm đôi cùng một người: {inc}"


def test_movement_wins_over_stale_advice():
    """Đang đi tới Y nhưng sổ advice còn ghi X (lệnh cũ chưa dọn) ⇒ tin **chuyển động thật**.

    Vị trí thực tế là sự thật; sổ ghi chỉ là ý định."""
    actors = [_a(1, "A", ActorState.ENROUTE, enroute="Y")]
    _, inc = count_supply(actors, pending_targets={1: "X"})
    assert inc == {"Y": 1}, f"tin lệnh cũ hơn chuyển động thật: {inc}"


def test_offline_and_busy_actors_are_not_available_supply():
    """Chỉ `IDLE` mới là cung SẴN SÀNG.

    Người đang chở khách/nghỉ/đổi pin/offline không nhận được đơn ngay, tính họ vào là **thổi
    phồng cung** ⇒ advisor tưởng ô đã đủ người và bỏ qua ô thực ra đang thiếu.
    (Giới hạn có nhãn: người đang nghỉ/đổi pin sẽ quay lại, v1 chưa mô hình hoá điều đó.)
    """
    actors = [_a(1, "A", ActorState.OFFLINE), _a(2, "A", ActorState.ON_TRIP),
              _a(3, "A", ActorState.REST), _a(4, "A", ActorState.CHARGING),
              _a(5, "A", ActorState.IDLE)]
    now, inc = count_supply(actors)
    assert now == {"A": 1}, f"đếm cả người đang bận: {now}"
    assert inc == {}


def test_conservation_per_category():
    """Bảo toàn tính theo TỪNG LOẠI, không phải tổng.

    (Bản đầu của test này đòi `Σnow + Σinc ≤ n_actors` và **mâu thuẫn** với
    `test_pending_advice_counts_as_incoming_before_the_driver_moves` — test kia đòi người vừa
    được khuyên phải vừa là cung tại chỗ của ô đang đứng, vừa trừ trần của ô đích.

    Test kia mới đúng, vì hai con số nói về hai LÁT THỜI GIAN khác nhau: *"ai nhận đơn được ngay
    bây giờ"* và *"ô đó sắp có bao nhiêu người"*. Hệ quả là ô đang đứng trông đầy hơn thực tế một
    chút — lệch về phía **thận trọng**, đúng hướng ta muốn khi đang chống dồn cục.)
    """
    actors = [_a(1, "A", ActorState.IDLE), _a(2, "B", ActorState.IDLE),
              _a(3, "A", ActorState.ENROUTE, enroute="B")]
    now, inc = count_supply(actors, pending_targets={1: "B"})
    assert sum(now.values()) <= len(actors)
    assert sum(inc.values()) <= len(actors)
    assert now == {"A": 1, "B": 1}
    assert inc == {"B": 2}, "người vừa được khuyên + người đang đi, cả hai đều trừ trần của B"


# ---------- view + cache ----------

@pytest.fixture(scope="module")
def cfg():
    c = Config.load("configs/pilot_dongda.yaml")
    return Config(copy.deepcopy(c.data), c.root_dir)


class _FakeWorld:
    """Chỉ đủ mặt để dựng view — không cần cả SimPy."""

    def __init__(self, cfg, actors, demand_field):
        self.cfg, self.actors, self.demand_field = cfg, actors, demand_field


def test_view_matches_core_schema(cfg):
    w = _FakeWorld(cfg, [_a(1, "A", ActorState.IDLE)], {9: {"A": 12.0, "B": 6.0}})
    v = MarketStateProducer(w, bucket_min=60).view(9 * 60)
    assert v["schema_version"]
    assert v["positioning_allowed"] is True
    assert v["availability"]["supply"] == "available"
    assert v["cells"]["A"]["supply_now"] == 1
    assert v["source"] == "MOCK", "cung/cầu trong sim là MOCK — nhãn phải đi cùng dữ liệu"


def test_view_is_cached_within_a_bucket_but_refreshes_next_bucket(cfg):
    """Cache theo bucket: 90 actor × poll 2′ × 20h mà tính lại mỗi lần thì runtime nổ.

    Nhưng cache **không được** sống quá bucket — nếu không advisor sẽ ra quyết định bằng ảnh cung
    của một giờ trước, đúng loại lỗi 'số cũ trông như số mới'."""
    actors = [_a(1, "A", ActorState.IDLE)]
    w = _FakeWorld(cfg, actors, {9: {"A": 12.0}, 10: {"A": 12.0}})
    p = MarketStateProducer(w, bucket_min=60)
    v1 = p.view(9 * 60)
    actors.append(_a(2, "A", ActorState.IDLE))          # cung đổi GIỮA bucket
    assert p.view(9 * 60 + 30)["cells"]["A"]["supply_now"] == 1, "cache không có tác dụng"
    assert p.view(9 * 60 + 30) is v1
    assert p.view(10 * 60)["cells"]["A"]["supply_now"] == 2, "cache sống quá bucket ⇒ số cũ"


def test_absent_supply_disables_positioning(cfg):
    """`supply_by_cell = None` (không có nguồn cung) ⇒ view phải NÓI RA, không đoán."""
    w = _FakeWorld(cfg, [], {9: {"A": 12.0}})
    v = MarketStateProducer(w, bucket_min=60, supply_available=False).view(9 * 60)
    assert v["positioning_allowed"] is False
    assert v["availability"]["supply"] == "absent"
    assert v["ranked_cells"] == []


# ---------- bất biến PHỦ ĐƯỜNG (T-046) ----------

def test_arrival_clears_the_target_in_a_real_run(cfg):
    """Tới nơi phải XOÁ `enroute_cell`. Đặt mà quên xoá còn tệ hơn không đặt.

    Nếu cờ dính lại, actor đứng yên vẫn bị đếm là *"đang tới"* suốt phần còn lại của ngày ⇒
    `supply_now` thiếu người và `supply_incoming` thừa người **cùng lúc**, ở mọi bucket sau đó.
    Không có test nào khác trong file này bắt được điều đó vì chúng đều dựng actor bằng tay.
    """
    from gsm_sim.runner import run_once
    r = run_once(Config(copy.deepcopy(cfg.data), cfg.root_dir), 1000)
    dinh = [a.actor_id for a in r.actors
            if a.state in (ActorState.IDLE, ActorState.OFFLINE) and a.enroute_cell]
    assert not dinh, (
        f"{len(dinh)} actor kết thúc ngày ở trạng thái đứng yên mà `enroute_cell` vẫn còn "
        f"(vd {dinh[:5]}) — cờ không được dọn khi tới nơi")


def test_every_enroute_transition_sets_a_target():
    """Mọi chỗ gán `ActorState.ENROUTE` phải hoặc đặt `enroute_cell`, hoặc nằm trong danh sách
    MIỄN TRỪ CÓ NHÃN ngay dưới đây.

    Vì sao quét source thay vì chạy sim: thêm một đường di chuyển mới mà quên gán `enroute_cell`
    **không làm test nào đỏ** — cung đang-tới chỉ đơn giản đếm thiếu, âm thầm. Đây chính là mẫu
    lỗi T-046 đã xuất hiện 5 lần trong một phiên. Test này bắt tại chỗ sửa, không phải ở hạ nguồn.

    Miễn trừ hiện tại (v1, có lý do):
      * **đón khách** — đích là điểm TRẢ khách, chân trời dài và bất định; coi tài xế đang chở
        khách là "cung sắp tới ô Y" sẽ thổi phồng cung ở khắp nơi.
    """
    src = (ROOT / "src" / "gsm_sim" / "world.py").read_text(encoding="utf-8")
    lines = src.splitlines()
    hits = [i for i, ln in enumerate(lines)
            if "state = ActorState.ENROUTE" in ln.replace("actor.", "")]
    assert hits, "không tìm thấy chỗ nào chuyển sang ENROUTE — test đã lỗi thời"
    for i in hits:
        window = "\n".join(lines[max(0, i - 6):i + 7])
        ok = ("enroute_cell" in window) or ("ENROUTE_EXEMPT" in window)
        assert ok, (
            f"world.py:{i + 1} chuyển sang ENROUTE nhưng không đặt `enroute_cell` và cũng không "
            f"gắn nhãn miễn trừ `ENROUTE_EXEMPT`. Cung ĐANG TỚI sẽ đếm thiếu mà không ai biết.\n"
            f"---\n{window}\n---")
