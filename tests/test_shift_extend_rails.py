"""🔴 CỔNG `D-QD4-03` / `V-28` — lan can SỨC KHOẺ cho kênh KÉO CA (`shift_extend`).

Cường chốt 2026-08-04, phương án **(b)**: *giữ đo, thêm lan can* (không chuyển kênh sang
`SOFT_TOPICS`).

## Vì sao cần cổng này

Trước cycle này, `check_shift_extend` có **0 lan can sức khoẻ**, trong khi `should_defer_rest` —
kênh mà chính `src/gsm_core/policy_locks.py:40-42` xếp **CÙNG HỌ** (comment nguyên văn: *"trần hoãn
KẾT CA (cùng họ: **kéo dài thời gian làm việc vì tiền**)"*) — có **ba**.

Nó *có* đọc `actor.online_min`, nhưng làm **mẫu số năng suất** (`rate = points / online_h`), không
phải cổng mệt ⇒ **tài xế mệt mà năng suất cao vẫn được khuyên kéo ca**.

Lập luận §1.2c áp nguyên văn, chỉ đổi dấu: *"một khi `rest_adherence` tồn tại như một con số, nó sẽ
được nhìn như thứ cần cải thiện"* → với `shift_extend_adherence`, "cải thiện" nghĩa là **nhiều tài
xế hơn đồng ý làm dài giờ hơn**. Và repo đang tự mâu thuẫn: guardrail tầng 5
(`sim_metrics.SPAN_P90_RISE_TOL`) **tố giác** khi `work_span_p90` tăng >10%, còn `adherence_view`
**tính là thành tích** cái tỷ lệ làm nó tăng.

## Cổng canh HAI thứ, không phải một

1. **nhánh chặn** — ba lan can có bắn không;
2. **đường quan sát** — cú chặn có để lại `advice_extend_veto` + có được `extend_rails_audit` đếm
   không.

Thiếu (2) thì lan can là **trang trí**: nó chặn đúng nhưng không ai thấy, guardrail tầng 5 không
đọc được. Đó đúng `N5` (*cú loại im lặng*) và `D-M3-08` (*cơ chế chỉ sống trên giấy*) — hai họ lỗi
repo đã trả giá.
"""
from __future__ import annotations

import copy

import pytest

from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_sim.config import Config
from gsm_sim.entities import Actor, FleetType
from gsm_sim.policy import PolicyBundle
from gsm_sim.sim_metrics import EXTEND_RAILS, extend_rails_audit

SOC_THRESHOLD = 20.0
FATIGUE = 480.0


def _actor(**kw) -> Actor:
    """Tài xế ĐỨNG NGOÀI mọi lan can theo mặc định — mỗi test chỉ đẩy MỘT biến qua ngưỡng.

    Nếu fixture mặc định đã dính một lan can thì test nào cũng "xanh" và ta không phân biệt được
    lan can nào đang bắn (bài học `T-046`: fixture sai làm test xanh mà chưa chạm code path)."""
    a = Actor(actor_id=1, archetype="P7", fleet=FleetType.SWAP, home_cell="x",
              shift_start_min=600.0, shift_end_min=1300.0, demand_prior_sigma=0.2,
              accept_base=0.8, fatigue_threshold_min=FATIGUE, meal_hour=12)
    a.cell = "x"
    a.soc_pct = 100.0
    a.points, a.online_min = 95, 300.0     # sát mốc ⇒ need_min ~16′, tổng 316 < 480
    for k, v in kw.items():
        setattr(a, k, v)
    return a


@pytest.fixture(scope="module")
def cfg():
    return Config.load("configs/pilot_dongda.yaml")


@pytest.fixture
def bridge(cfg):
    # `advice.enabled` mặc định FALSE ở pilot config ⇒ `covers()` trả False ⇒ mọi kênh trả 0 ngay
    # dòng đầu. Không bật thì test "xanh" mà chưa gọi tới logic nào (bài học T-046).
    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    c.data.setdefault("advice", {}).update({"enabled": True, "coverage": "all"})
    b = AdviceActionBridge(c, PolicyBundle.from_config(c), seed=1000)
    b.ch_shift_extend = True
    return b


# ---------------------------------------------------------------- lan can BẮN

def test_soc_thap_KHONG_khuyen_keo_ca(bridge):
    """Khuyên chạy thêm 40′ khi pin sắp cạn là khuyên một việc **có thể không làm được**, và đẩy
    rủi ro `battery_stranded` — đúng thứ lan can 1 của `should_defer_rest` sinh ra để chặn."""
    added, why = bridge.check_shift_extend(_actor(soc_pct=15.0), 900.0, SOC_THRESHOLD)
    assert (added, why) == (0.0, "soc_low")


def test_da_MET_thi_KHONG_khuyen_keo_ca(bridge):
    """`online_min > fatigue_threshold_min` — tài xế ĐÃ quá ngưỡng."""
    added, why = bridge.check_shift_extend(_actor(online_min=500.0), 900.0, SOC_THRESHOLD)
    assert (added, why) == (0.0, "fatigued")


def test_loi_khuyen_DAY_QUA_nguong_thi_KHONG_khuyen(bridge):
    """🔴 Lan can mà **chỉ có bản 'đã mệt' sẽ để lọt** — và là ca đáng chặn nhất.

    ⚠ SỬA CÓ CHỦ Ý 2026-08-06 (E1b ADV-02/03, UPDATE-153): kịch bản cũ (ca còn 400′) nay hợp lệ
    là `reachable_in_shift` — mốc đạt được KHÔNG cần kéo ca thì không có gì để khuyên. Dựng lại:
    ca chỉ còn 10′ (900→910), tài xế 470′ < ngưỡng 480 nên `fatigued` không bắn; cần ~24,7′ ⇒
    phần kéo ~14,7×1,15 ≈ 16,9′; DỰ PHÓNG CUỐI CA MỞ RỘNG = 470+10+16,9 ≈ 497 > 480 ⇒ **chính
    lời khuyên này** đẩy họ qua ngưỡng — đo ở dự phóng, không phải tại-lúc-khuyên.

    Vì sao kênh kéo ca cần lan can này mà kênh nghỉ thì không: hoãn nghỉ chỉ **ĐỔI THỜI ĐIỂM**
    nghỉ; kéo ca **THÊM GIỜ LÀM**. Cái hại nằm ở phần thêm vào, không chỉ ở trạng thái sẵn có."""
    added, why = bridge.check_shift_extend(
        _actor(online_min=470.0, shift_end_min=910.0), 900.0, SOC_THRESHOLD)
    assert (added, why) == (0.0, "would_exceed_fatigue")


# ---------------------------------------------------------------- ĐỐI CHỨNG: không chặn oan

def test_DOI_CHUNG_tai_xe_khoe_van_duoc_khuyen(bridge):
    """Bắt buộc — không có bước này thì một `return 0.0, "fatigued"` vô điều kiện cũng làm ba test
    trên XANH. Cổng phải phân biệt *"ranh giới chạy đúng"* với *"kênh chết"*."""
    # E1b ADV-02 (sửa CÓ CHỦ Ý 2026-08-06): actor mặc định có ca còn 400′ ⇒ mốc trong tầm ca
    # ⇒ `reachable_in_shift` là ĐÚNG. Muốn thấy kênh khuyên thì ca phải sắp kết: còn 5′,
    # cần ~15,8′ ⇒ phần kéo ~12,4′; dự phóng 300+5+12,4 = 317 ≪ 480 ⇒ phải được khuyên.
    got = [bridge.check_shift_extend(_actor(shift_end_min=905.0 + i), 900.0 + i, SOC_THRESHOLD)
           for i in range(0, 200, 31)]         # nhiều bucket ⇒ vượt cadence/coin
    assert any(added > 0.0 for added, _ in got), (
        f"kênh không còn khuyên được lần nào cho tài xế KHOẺ ⇒ lan can đang chặn oan: {got}")


def test_DOI_CHUNG_ranh_gioi_nguong_dung_chieu(bridge):
    """`>` chứ không `>=`: đúng bằng ngưỡng thì CHƯA quá ngưỡng — khớp `should_defer_rest:763`.

    Ghim chiều so sánh vì đây là chỗ một ký tự đổi nghĩa cả lan can, và không test nào khác thấy."""
    added, why = bridge.check_shift_extend(
        _actor(online_min=FATIGUE, points=0), 900.0, SOC_THRESHOLD)
    assert why != "fatigued", "đúng bằng ngưỡng bị xử là ĐÃ quá ngưỡng — sai chiều so sánh"


def test_DOI_CHUNG_lan_can_SUC_KHOE_uu_tien_hon_tran_kinh_te(bridge):
    """Khi một lời khuyên vừa vượt trần kinh tế VỪA đẩy qua ngưỡng mệt, lý do báo ra phải là lý do
    **SỨC KHOẺ**. Nếu không, bảng veto sẽ nói *"hết trần"* cho đúng những ca mà lan can sức khoẻ
    mới là thứ chặn — và người đọc kết luận sai rằng lan can chưa bao giờ cần tới."""
    # E1b ADV-02/03 (sửa CÓ CHỦ Ý 2026-08-06): thêm `shift_end_min=920` để cần kéo THẬT
    # (need ~304′ > còn 20′ ⇒ phần kéo ~284′ vượt trần 60′) VÀ dự phóng 475+20+326 ≈ 821 ≫ 480.
    a = _actor(online_min=475.0, points=61, shift_end_min=920.0)
    added, why = bridge.check_shift_extend(a, 900.0, SOC_THRESHOLD)
    assert (added, why) == (0.0, "would_exceed_fatigue"), (
        f"lan can sức khoẻ bị trần kinh tế che: {why}")


def test_kenh_TAT_tra_channel_off_chu_khong_phai_lan_can(bridge):
    """Kênh tắt KHÔNG được báo là lan can — nếu không, `xveto_fired_n` sẽ đếm mọi run mặc định
    (kênh tắt ở config sản phẩm) và tố giác một thứ chưa từng xảy ra."""
    bridge.ch_shift_extend = False
    added, why = bridge.check_shift_extend(_actor(online_min=500.0), 900.0, SOC_THRESHOLD)
    assert (added, why) == (0.0, "channel_off")
    assert why not in EXTEND_RAILS


# ---------------------------------------------------------------- đường QUAN SÁT

def test_EXTEND_RAILS_khong_chua_rang_buoc_KINH_TE():
    """`extend_cap`/`cap_unreachable` là trần KINH TẾ, không phải lan can sức khoẻ. Gộp vào sẽ thổi
    `xveto_fired_n` bằng những lần chặn chẳng liên quan gì tới sức khoẻ ⇒ guardrail tầng 5 đọc sai."""
    assert set(EXTEND_RAILS) == {"soc_low", "fatigued", "would_exceed_fatigue"}


def test_audit_DEM_dung_va_co_MAU_SO():
    """`xveto_calls_n` bắt buộc đi kèm: advice làm tài xế online lâu hơn ⇒ mẫu số veto đổi theo
    arm. Đọc count trần mà không đọc calls là đọc sai (cùng lý do `rest_rails_audit` nêu)."""
    class _E:
        def __init__(self, kind, reason):
            self.kind, self.detail = kind, {"reason": reason}

    class _R:
        events = [_E("advice_extend_veto", "fatigued"),
                  _E("advice_extend_veto", "fatigued"),
                  _E("advice_extend_veto", "would_exceed_fatigue"),
                  _E("advice_extend_veto", "extend_cap"),      # KHÔNG phải rail
                  _E("advice_rest_veto", "fatigued")]          # kênh KHÁC — không được lẫn

    out = extend_rails_audit(_R())
    assert out["xveto_fatigued_n"] == 2
    assert out["xveto_would_exceed_fatigue_n"] == 1
    assert out["xveto_soc_low_n"] == 0
    assert out["xveto_calls_n"] == 4, "mẫu số phải đếm CẢ lần chặn không-phải-rail"
    assert out["xveto_fired_n"] == 3, "chỉ rail mới vào `fired`"


def test_audit_KHONG_de_khoa_cua_rest_rails():
    """Hai bộ đếm sống cạnh nhau trong cùng `full_report`. Trùng khoá thì một bên bị ghi đè **im
    lặng** và guardrail đọc số của kênh kia."""
    from gsm_sim.sim_metrics import rest_rails_audit

    class _R:
        events = []

    assert not (set(rest_rails_audit(_R())) & set(extend_rails_audit(_R())))


def test_WORLD_thuc_su_log_veto_khi_lan_can_ban(cfg):
    """🔴 Test này sinh ra vì **sever-restore bắt tôi**: mũi *"bỏ log `advice_extend_veto` ở
    world"* cho **XANH — KHÔNG BẮT**.

    Mọi test khác trong file kiểm `check_shift_extend` (đơn vị) và `extend_rails_audit` (event
    tổng hợp). **Không cái nào kiểm khúc GIỮA**: world có thật sự ghi event khi lan can bắn không.
    Gỡ dòng `self.log(...)` ⇒ lan can chặn đúng nhưng **vô hình**, guardrail tầng 5 không thấy —
    và cổng vẫn xanh. Đó đúng định nghĩa cổng trang trí.

    Nên test này chạy `run_once` THẬT (chậm hơn, nhưng là chỗ duy nhất chứng minh được khúc giữa).
    """
    import copy

    from gsm_sim.runner import run_once

    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    adv = c.data.setdefault("advice", {})
    adv["enabled"], adv["coverage"] = True, "all"
    adv.setdefault("channels", {})["shift_extend"] = True

    r = run_once(c, 1000)
    veto = [e for e in r.events if e.kind == "advice_extend_veto"]
    assert veto, (
        "kênh BẬT mà KHÔNG có event `advice_extend_veto` nào ⇒ world không ghi lại cú chặn của "
        "lan can. Lan can vẫn chặn đúng, nhưng không ai đếm được — `D-M3-08`/`N5`.")
    assert {e.detail.get("reason") for e in veto} <= set(EXTEND_RAILS), (
        "world ghi veto với reason KHÔNG phải lan can (vd `cadence`/`channel_off`) ⇒ `xveto_*` "
        "thổi bằng những lần chặn chẳng liên quan sức khoẻ")
    audit = extend_rails_audit(r)
    assert audit["xveto_fired_n"] == len(veto), "audit và event log lệch nhau"


def test_WORLD_kenh_TAT_thi_KHONG_sinh_event_veto(cfg):
    """Tính chất AN TOÀN quan trọng nhất của cycle này: ở **config mặc định** (`shift_extend:
    false`) không được sinh thêm một event nào.

    Nếu sinh, event stream của mọi run mặc định đổi ⇒ **mọi số A/B đã đo mất tính so sánh được**
    — cùng họ `b0-A`. Đây là lý do nhánh `channel_off` KHÔNG nằm trong `EXTEND_RAILS`."""
    import copy

    from gsm_sim.runner import run_once

    c = Config(copy.deepcopy(cfg.data), cfg.root_dir)
    adv = c.data.setdefault("advice", {})
    adv["enabled"], adv["coverage"] = True, "all"
    adv.setdefault("channels", {})["shift_extend"] = False

    r = run_once(c, 1000)
    assert not [e for e in r.events if e.kind == "advice_extend_veto"], (
        "kênh TẮT mà vẫn ghi event veto ⇒ phá tính so-sánh-được của mọi số A/B đã đo")


def test_full_report_CO_NOI_extend_rails():
    """`D-M3-13` đã trả giá: tầng 5 có hàm gộp nhưng **không có nguồn dữ liệu** ⇒ TREO trên mọi
    pair mà không ai biết vì sao. Cổng này đòi hàm audit có caller thật trong `full_report`."""
    import ast
    import pathlib

    src = pathlib.Path(__file__).resolve().parents[1] / "src/gsm_sim/sim_metrics.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "health_guardrail"), None)
    if fn is None:
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and "rest_rails_audit" in ast.unparse(n))
    assert "extend_rails_audit" in ast.unparse(fn), (
        "`extend_rails_audit` không có caller trong hàm gộp tầng 5 ⇒ nó là hàm chết, và lan can "
        "sức khoẻ của kênh kéo ca vô hình với guardrail")
