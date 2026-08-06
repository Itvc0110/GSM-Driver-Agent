"""Mã hoá THỜI GIAN của lời khuyên — bucket phải đúng ngày và không vượt đời thế giới (b0-A).

## Vì sao có file này

Cường hỏi *"kiểm tra xem có lỗi time mismatch ở bất cứ đâu không"* (2026-07-28). Truy nguyên tìm
ra **một chuỗi bốn mắt**:

1. `advice_bridge.build_shift_plan_input` hard-code ngày `2026-07-01` và wrap giờ `(s // 60) % 24`;
2. `check_shift_extend` cộng `shift_end_min` tới **+60′**, trong khi `archetypes.py` đã cap
   `shift_end = min(1440, …)` ⇒ ca tối-đêm chạm trần rồi bị đẩy lên tối đa **1500**;
3. `build_shift_plan_input` nhận `horizon_min = shift_end_min` ⇒ sinh `s = 1440` ⇒ nhãn bucket
   `2026-07-01T00:00` — **sớm hơn `t_now`, cùng ngày**;
4. `shift_dp._forecast_arrays` làm `sorted(grouped)` — **sort chuỗi ISO theo từ điển**.

## Hai kết luận KHÁC NHAU, phải phân biệt (đo, không đoán)

- **Đảo thứ tự bucket**: tái lập được bằng forecast tổng hợp có cầu ở giờ 0 (`_forecast_arrays`
  trả `00:00` ở **vị trí 0**), nhưng **KHÔNG với tới trong chạy thật** — `demand_field` chỉ phủ
  05:00–24:00 nên giờ 0 trả `{}` ⇒ không sinh dòng nào cho bucket đó.
  ⇒ **Đính chính**: nghi ngờ ban đầu của tôi rằng số của UPDATE-047 (nhánh `all`, có
  `shift_extend`) đã nhiễm là **SAI**. Đo 1 seed × 1197 lần hỏi solver: **0 lần đảo**.
- **Bucket MA thì CÓ thật**: `buckets_remaining` đếm cả bucket sau 24:00 trong khi thế giới dừng
  ở `time.end_min`. Đo seed 1000: **48 lần** `horizon > 1440`, và ở mỗi lần `B` lớn hơn số bucket
  có dữ liệu đúng 1. `_required_rest` tính theo `B` ⇒ bucket ma có thể thổi phồng nghỉ bắt buộc.

Giữ cả hai lan can: cái thứ nhất chặn một lỗi **tiềm ẩn** (chỉ cần ai đó cho cầu ban đêm vào
config là nó sống dậy), cái thứ hai chặn lỗi **đang xảy ra**.
"""

from __future__ import annotations

import copy

import pytest

from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.config import Config
from gsm_sim.entities import Actor, FleetType
from gsm_sim.policy import PolicyBundle

WORLD_END_MIN = 1440.0        # `time.end_min` của pilot config — 24:00


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


def _bridge(cfg, end_min: float | None = None):
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    # `advice.enabled` mặc định FALSE trong pilot config ⇒ `covers()` trả False ⇒ mọi kênh trả
    # 0/None ngay dòng đầu. Không bật thì test "xanh" mà chưa gọi tới logic nào.
    c.data.setdefault("advice", {}).update({"enabled": True, "coverage": "all"})
    if end_min is not None:
        c.data.setdefault("time", {})["end_min"] = end_min
    return AdviceActionBridge(c, PolicyBundle.from_config(c), seed=1000)


@pytest.fixture
def bridge(cfg):
    """Thế giới pilot: dừng đúng 24:00."""
    return _bridge(cfg)


@pytest.fixture
def bridge_qua_nua_dem(cfg):
    """Thế giới kéo tới 26:00 — nửa đêm là HỢP LỆ, nên bucket `00:00` thật sự được sinh ra.

    Cần fixture riêng vì bản sửa clamp `horizon` khiến pilot config **không bao giờ** sinh bucket
    nửa đêm nữa; test chạy trên pilot sẽ xanh vì không có gì để sai, chứ không phải vì mã hoá
    đúng (đã kiểm bằng mutation: hai test thứ tự KHÔNG đỏ dưới M1 khi còn dùng pilot).
    """
    return _bridge(cfg, end_min=1560.0)


# `D-QD4-03`: ngưỡng SOC truyền cho `check_shift_extend`. Đặt 0.0 CÓ CHỦ Ý — các test trong file
# này kiểm `b0-A`/`L1-04` (trần thế giới, token), KHÔNG kiểm lan can sức khoẻ. Ngưỡng 0 làm lan can
# `soc_low` không bao giờ bắn ⇒ chúng đo đúng thứ chúng sinh ra để đo. Lan can có test riêng ở
# `tests/test_shift_extend_rails.py`.
_SOC_THRESHOLD = 0.0


def _actor(shift_end: float) -> Actor:
    a = Actor(actor_id=1, archetype="P7", fleet=FleetType.SWAP, home_cell="x",
              shift_start_min=900.0, shift_end_min=shift_end, demand_prior_sigma=0.2,
              accept_base=0.8, fatigue_threshold_min=480.0, meal_hour=12)
    a.cell = "x"
    return a


def _hint_all_hours(_actor, hour):
    """Cầu ở MỌI giờ, kể cả ban đêm.

    `demand_field` hiện tại không có giờ 0 nên lỗi đảo thứ tự bị che. Test phải kiểm **mã hoá**,
    không phụ thuộc việc config hôm nay tình cờ không có cầu ban đêm — nếu không thì lỗi sẽ sống
    dậy im lặng ngày ai đó thêm ca đêm.
    """
    return {"cellA": 10.0 if hour in (21, 22, 23) else 1.0}


def _buckets(spi) -> list[str]:
    return list(dict.fromkeys(r["bucket"] for r in spi["demand_forecast"]))


# ---------- 1. Nhãn bucket phải mang NGÀY THẬT ----------

def test_iso_label_rolls_to_next_day_past_midnight():
    """Hàm mã hoá phải mang NGÀY THẬT. `% 24` giữ GIỜ nhưng vứt mất NGÀY, nên một thời điểm ở
    tương lai lại mang nhãn sớm hơn hiện tại."""
    from gsm_sim.advice_bridge import _iso
    assert _iso(1380) == "2026-07-01T23:00:00+07:00"
    assert _iso(1440) == "2026-07-02T00:00:00+07:00", "qua nửa đêm mà không sang ngày mới"
    assert _iso(1500) == "2026-07-02T01:00:00+07:00"
    assert _iso(1380) < _iso(1440) < _iso(1500), (
        "so CHUỖI phải cùng chiều với thời gian — `shift_dp._forecast_arrays` sort chuỗi ISO, "
        "nên đây chính là bất biến nó dựa vào")


def test_producer_bucket_labels_roll_over_in_a_world_that_spans_midnight(bridge_qua_nua_dem):
    """Thế giới kéo qua nửa đêm (`time.end_min > 1440`) ⇒ bucket phải sang ngày 02/07."""
    spi = bridge_qua_nua_dem.build_shift_plan_input(
        _actor(1560.0), 1320.0, _hint_all_hours, 1560.0)
    bs = _buckets(spi)
    midnight = [b for b in bs if b[11:16] == "00:00"]
    assert midnight, f"không có bucket nửa đêm để kiểm: {bs}"
    assert midnight[0].startswith("2026-07-02"), (
        f"bucket nửa đêm mang nhãn {midnight[0]} — vẫn ngày 01/07 ⇒ sớm hơn t_now "
        f"({spi['t_now']}), sẽ bị `sorted()` của shift_dp đẩy lên đầu")
    assert bs == sorted(bs), f"nhãn bucket không tăng dần: {bs}"


def test_bucket_labels_are_chronological(bridge_qua_nua_dem):
    """Danh sách bucket phải TĂNG dần — và phải giữ đúng thứ tự sau khi `sorted()`.

    `shift_dp._forecast_arrays` gộp theo timestamp rồi `sorted(grouped)`. Nếu nhãn sai thì thứ tự
    DP dùng khác thứ tự thời gian thật, và `schedule[0]` (hành động TỨC THỜI mà bridge thi hành)
    được tính cho một bucket khác.
    """
    spi = bridge_qua_nua_dem.build_shift_plan_input(
        _actor(1560.0), 1320.0, _hint_all_hours, 1560.0)
    bs = _buckets(spi)
    assert bs == sorted(bs), f"nhãn bucket không tăng dần: {bs}"


def test_dp_uses_same_order_as_producer(bridge_qua_nua_dem):
    """Bất biến NỐI TẦNG: thứ tự producer sinh ra == thứ tự solver dùng.

    Kiểm ở ĐÚNG chỗ hai tầng gặp nhau, thay vì tin rằng chúng khớp (mẫu lỗi T-046). Đây là test
    duy nhất bắt được kịch bản đầy đủ: nhãn sai ⇒ `sorted()` đẩy bucket cuối lên vị trí 0 ⇒ DP
    lập kế hoạch cho sai khung giờ.
    """
    from gsm_core.solvers.shift_dp import _forecast_arrays
    br = bridge_qua_nua_dem
    spi = br.build_shift_plan_input(_actor(1560.0), 1320.0, _hint_all_hours, 1560.0)
    _, _, _, dp_buckets = _forecast_arrays(spi, {"bucket_min": br.bucket_min}, 1.0)
    real = [b for b in dp_buckets if b]
    produced = _buckets(spi)
    assert real, "không có bucket nào để kiểm — fixture hỏng"
    assert real == produced[:len(real)], (
        f"solver dùng thứ tự {real} ≠ thứ tự producer {produced}")


# ---------- 2. Không lập kế hoạch cho thời gian thế giới KHÔNG tồn tại ----------

def test_shift_extend_cannot_push_past_world_end(bridge, cfg):
    """`check_shift_extend` không được kéo ca vượt `time.end_min`.

    Thế giới dừng ở 24:00 (`world.py`: `while self.env.now < self.end_min`). Kéo ca tới 25:00 là
    lời khuyên **không thể thực hiện được**: nó không sinh thêm cuốc nào, nhưng vẫn tiêu ngân sách
    `shift_extended_min` và vẫn ghi event `advice_shift_extend` ⇒ đo A/B thấy "có can thiệp" trong
    khi thực tế không có gì xảy ra.
    """
    bridge.ch_shift_extend = True
    # Ca kết thúc 23:50 — CÒN chỗ để hoãn, nhưng mức hoãn tự nhiên (~18′) sẽ vượt 24:00.
    # Nếu đặt shift_end = 1440 sẵn thì hàm trả 0 ngay và test không kiểm được gì.
    a = _actor(1430.0)
    # `points` phải SÁT mốc thì mới vào nhánh hoãn. Mốc (60, 100, 160, 200) ⇒ 95 điểm cho gap 5
    # ⇒ need_min ≈ 16′ < trần 60′.
    # (Bản đầu của test này dùng points=60 ⇒ gap 40 ⇒ need_min 200′ > trần ⇒ hàm trả 0 ngay,
    #  test XANH mà chưa hề chạm code path — đúng mẫu "test có mà không bắt" ở T-046.)
    a.points, a.online_min = 95, 300.0
    # `D-QD4-03`: hàm nay nhận `soc_threshold` và trả `(phút, lý do)`. Fixture cố ý ĐỨNG NGOÀI ba
    # lan can (soc 100% > ngưỡng; dự phóng 300 + 10 + ~7 ≈ 317 < `fatigue_threshold` 480)
    # ⇒ test này vẫn kiểm ĐÚNG thứ nó sinh ra để kiểm (`b0-A`), không bị lan can chặn hộ.
    # E1b ADV-02 (sửa CÓ CHỦ Ý 2026-08-06): hỏi ở 1420 (ca còn 10′ < need ~16′) — bản cũ hỏi ở
    # 1200 khi ca còn 230′, nay hợp lệ là `reachable_in_shift` (mốc trong tầm ca, không kéo).
    # Coin là hash TẤT ĐỊNH theo (bucket, revision) — bucket mới có thể ra False vĩnh viễn;
    # coin không phải chủ thể của test này ⇒ ép True để cô lập đúng cơ chế b0-A.
    bridge.coin_follows = lambda *args, **kw: True
    for _ in range(20):
        bridge.check_shift_extend(a, 1420.0, _SOC_THRESHOLD)
    assert a.shift_extended_min > 0.0, (
        "test KHÔNG chạm được nhánh hoãn ca ⇒ nó không kiểm gì cả; sửa fixture, đừng để xanh giả")
    assert a.shift_end_min <= WORLD_END_MIN, (
        f"ca bị kéo tới {a.shift_end_min:.0f}′ > {WORLD_END_MIN:.0f}′ — thế giới đã dừng, "
        f"phần kéo thêm không bao giờ chạy")


def test_no_phantom_bucket_beyond_world_end(bridge):
    """`buckets_remaining` không được đếm bucket nằm ngoài đời sống của thế giới.

    Đo được trên seed 1000: **48 lần** `B` lớn hơn số bucket có dữ liệu đúng 1 đơn vị. `B` đi
    thẳng vào `_required_rest(B, params)` nên bucket ma có thể **thổi phồng số bucket nghỉ bắt
    buộc** — advisor ép nghỉ vì một khung giờ không tồn tại.
    """
    spi = bridge.build_shift_plan_input(_actor(1500.0), 1320.0, _hint_all_hours, 1500.0)
    b = bridge.bucket_min
    n_within = len([s for s in range(1320, int(WORLD_END_MIN), b)])
    assert spi["buckets_remaining"] == n_within, (
        f"B = {spi['buckets_remaining']} nhưng chỉ có {n_within} bucket nằm trong "
        f"[{1320}, {WORLD_END_MIN:.0f}) — phần dư là bucket MA")


def test_infeasible_extend_does_not_burn_claim(cfg):
    """`L1-04` — lời khuyên BẤT KHẢ THI không được tiêu token `_claim_effect`.

    Đo được (UPDATE-102 §2b): **38/135 = 28%** quyết định `shift_extend` đã tiêu token,
    tiêu suất ngân sách nhịp, rút coin — rồi bị clamp `b0-A` (kéo ca vượt `time.end_min`)
    và biến mất: không event tác động, không đường quay lại, vì token đã cháy nên mọi lần
    hỏi lại trong cùng bucket 30′ đều trả 0.0.

    Kịch bản tái dựng đúng theo acceptance (`PLAN-2026-07-30-hang-doi-cong-viec.md` §1):
    lần 1 hỏi khi thế giới hẹp (bất khả thi) ⇒ không có gì xảy ra; NỚI `world_end_min`
    rồi hỏi lại TRONG CÙNG bucket ⇒ phải áp được. Trước fix, lần 2 trả 0.0 — token đã
    cháy ở lần 1 dù chưa hề có tác động nào.

    ⚠ Ngữ nghĩa `R-01` GIỮ NGUYÊN: "MỘT quyết định = MỘT lần ÁP TÁC ĐỘNG". Token phải
    cháy khi tác động ĐƯỢC ÁP — không phải khi lời khuyên được nói. Lần 1 ở đây không áp
    được gì, nên chưa có "lần áp" nào để đếm.
    """
    b = _bridge(cfg)                     # world_end mặc định 1440
    b.ch_shift_extend = True
    a = _actor(1430.0)                   # ca kết thúc 23:50 — cách world_end đúng 10′
    a.points, a.online_min = 95, 300.0   # sát mốc ⇒ vào nhánh hoãn (bài học T-046 ở test trên)

    # E1b ADV-02 (sửa CÓ CHỦ Ý 2026-08-06): now dời 1200 → 1430 — ca phải còn ÍT hơn need
    # (~16′) thì mới cần kéo; ở 1200 (còn 240′) nay hợp lệ là `reachable_in_shift`.
    now = 1430.0
    b.coin_follows = lambda *args, **kw: True   # coin tất định theo bucket — không phải chủ thể
    # Muốn BẤT KHẢ THI hẳn phải hết chỗ: đặt shift_end = world_end (không còn phút nào để kéo).
    a.shift_end_min = WORLD_END_MIN      # 24:00 — không còn một phút nào để kéo
    got1 = 0.0
    for _ in range(20):                  # đủ lần để chắc chắn coin có lần True
        got1 += b.check_shift_extend(a, now, _SOC_THRESHOLD)[0]
    assert got1 == 0.0 and a.shift_extended_min == 0.0, (
        "fixture hỏng: lần 1 phải BẤT KHẢ THI hoàn toàn (add = 0)")

    # Thế giới "nới" ra (mô phỏng việc điều kiện đổi trong cùng bucket) — quyết định
    # CÙNG bucket 30′, CÙNG material_revision ⇒ cùng coin ⇒ nếu token chưa cháy thì áp được.
    b.world_end_min = WORLD_END_MIN + 120.0
    got2 = 0.0
    for _ in range(20):
        got2 += b.check_shift_extend(a, now + 2.0, _SOC_THRESHOLD)[0]  # vẫn bucket [1200,1230)
    assert got2 > 0.0, (
        "L1-04: quyết định bất khả thi ở lần 1 đã TIÊU token `_claim_effect` ⇒ lần 2 "
        "(cùng bucket, nay khả thi) không áp được nữa — 28% quyết định mất hẳn kiểu này")


def test_applied_decision_does_not_spawn_ghost_infeasible_event(cfg):
    """Regression cho event MA mà SUITE bắt sau `L1-04` (decided 101 vs event 104, seed 1000).

    Ca: quyết định ĐÃ ÁP làm `shift_end_min` chạm `world_end_min`; các lần hỏi lại trong
    CÙNG bucket rơi vào nhánh `add ≤ 0` ⇒ trước fix, sinh outcome `infeasible` cho một
    quyết định đã áp xong — event thừa cùng `decision_id` làm event-count ≠ decision-count.

    Lưu ý phương pháp: phép đo n=100 của L1-04 KHÔNG bắt được lỗi này vì mọi chỉ tiêu của
    nó là decision-level/hành vi; lỗi nằm ở EVENT LOG. Test này pin đúng tầng event.
    """
    b = _bridge(cfg)
    b.ch_shift_extend = True
    a = _actor(1430.0)                   # còn 10′ tới world_end
    a.points, a.online_min = 95, 300.0

    # E1b ADV-02 (sửa CÓ CHỦ Ý 2026-08-06): 1200 → 1425 — ca còn 5′ < need ~16′ ⇒ cần kéo thật;
    # phần kéo ~12′ bị trần thế giới cắt còn 10′ ⇒ vẫn áp được và chạm trần như kịch bản cần.
    now = 1425.0
    b.coin_follows = lambda *args, **kw: True   # coin tất định theo bucket — không phải chủ thể
    applied = 0.0
    for _ in range(20):                  # lần đầu coin=True sẽ áp ~10′ ⇒ shift_end chạm 1440
        applied += b.check_shift_extend(a, now, _SOC_THRESHOLD)[0]
    assert applied > 0.0, "fixture yếu: chưa áp được lần nào — test không kiểm gì"
    assert a.shift_end_min == WORLD_END_MIN, "fixture lệch: chưa chạm trần thế giới"

    # Hỏi lại trong CÙNG bucket sau khi đã áp + chạm trần: không được sinh outcome mới.
    for _ in range(10):
        b.check_shift_extend(a, now + 4.0, _SOC_THRESHOLD)
    ghosts = [o for o in b.drain_spoken_outcomes() if o[2] == "shift_extend"]
    assert ghosts == [], (
        f"{len(ghosts)} event MA cho quyết định ĐÃ ÁP — event-count sẽ lệch decision-count "
        f"(suite từng đo: 104 vs 101)")
