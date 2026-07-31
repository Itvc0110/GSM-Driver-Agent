"""🔴 D-M3-13 — tầng 5 trong đường A/B có HÀM GỘP nhưng KHÔNG có NGUỒN DỮ LIỆU.

Đo được 2026-08-01 (seed 5011, `pilot_dongda`, arm A thật), không phải suy luận:

| Đo | Kết quả |
| --- | --- |
| `_system_metrics` (nguồn duy nhất của `system_a`/`system_b`) có khoá sức khoẻ? | **KHÔNG** — `rest_min_total`, `veto_fired_n`, `work_span_p90`, `drive_min_p90` đều vắng |
| `sim_metrics.health_guardrail(ra)` có dữ liệu thật? | **CÓ** — `rest_min_total=3689.0`, `veto_fired_n=175` |
| `aggregate_health_guardrail([pair thật])` | `verdict='TREO — sức khoẻ suy giảm'`, flags = *"tầng 5 THIẾU DỮ LIỆU"* |

⇒ Mọi `run_ladder` báo TREO **vì thiếu dữ liệu**, không vì sức khoẻ suy giảm. Fail-closed nên
an toàn về HƯỚNG, nhưng **vô dụng về chẩn đoán** — và tệ hơn: một verdict TREO luôn-bật sẽ bị
đọc thành nhiễu rồi bỏ qua, đúng con đường mà `D-R20` mô tả.

Đây là **lần thứ ba trong hai ngày** cùng một mẫu (`D-R12` · UPDATE-114 lỗ (a) · lỗ này):
cơ chế được mô tả trong docstring + có hàm, nhưng **không ai nối nguồn vào**. UPDATE-111 do
chính tôi viết nói tầng 5 đã *"promote vào parallel"* — thực tế chỉ promote hàm GỘP.

Thiết kế của fix, và vì sao tập actor lấy từ arm B: tầng 5 phải chấm trên **nhóm BỊ CHẠM**
(UPDATE-114 lỗ (b) — chấm trên tổng cohort pha loãng ~10× ở kênh thưa). Arm A không có event
advice nên `touched_actors(ra)` luôn rỗng; tập đúng là **`touched_actors(rb)` áp cho CẢ HAI
arm** — nhờ CRN, cùng `actor_id` tồn tại ở hai bên, nên so sánh mới là so cùng một nhóm người.
"""
from __future__ import annotations

import pytest

import copy

from gsm_sim.parallel import (_cfg_with, _system_metrics, aggregate_health_guardrail,
                              PairResult)
from gsm_sim.runner import Config, run_once

HEALTH_KEYS = ("rest_min_total", "veto_calls_n", "veto_fired_n",
               "work_span_p50", "work_span_p90", "work_span_max",
               "drive_min_p50", "drive_min_p90", "drive_min_max")


@pytest.fixture(scope="module")
def base():
    """MỘT run thật, dùng lại cho mọi ca. Fake mỏng không đi qua được `_system_metrics` — nó
    gọi `summarize`/`system_guardrail`/`_cohort_metrics` nên cần `grid`/`orders`/`seed` thật;
    mỗi lần vá thêm một field là một lần test đỏ SAI lý do (đã trả giá 3 lượt)."""
    cfg = Config.load("configs/pilot_dongda.yaml")
    return run_once(_cfg_with(cfg, enabled=False, actor_id=None, channels=None), 5011)


def _shaped(base, rest1: float, rest2: float, touched_aid: int = 1):
    """Cắt về 2 actor với `rest_min` kiểm soát được, giữ nguyên grid/orders thật; events thay
    bằng đúng MỘT event advice để `touched_actors` xác định được nhóm bị chạm."""
    r = copy.copy(base)
    a1, a2 = copy.copy(base.actors[0]), copy.copy(base.actors[1])
    a1.actor_id, a2.actor_id = 1, 2
    a1.rest_min, a2.rest_min = rest1, rest2
    r.actors = [a1, a2]
    r.events = [e for e in base.events if False] + [type("E", (), {
        "kind": "advice_rest_window", "actor_id": touched_aid, "t_min": 400.0,
        "cell": "", "detail": {"channel": "rest_window"}})()]
    return r


def _sm(base, rest1, rest2, **kw):
    return _system_metrics(_shaped(base, rest1, rest2), 1, **kw)


def _pair(base, ra_rest, rb_rest, health_actor_ids=None):
    kw = {"health_actor_ids": health_actor_ids}
    return PairResult(
        seed=1, actor_id=1, a={}, b={}, adherence_a={}, adherence_b={},
        system_a=_system_metrics(_shaped(base, *ra_rest), 1, **kw),
        system_b=_system_metrics(_shaped(base, *rb_rest), 1, **kw))


def test_system_metrics_PHAI_mang_khoa_suc_khoe(base):
    """Nếu thiếu, `aggregate_health_guardrail` không có gì để chấm và cổng thành trang trí."""
    sm = _sm(base, 100.0, 100.0)
    thieu = [k for k in HEALTH_KEYS if k not in sm]
    assert not thieu, f"thiếu khoá sức khoẻ ⇒ tầng 5 mù: {thieu}"


def test_aggregate_KHONG_con_bao_THIEU_DU_LIEU_tren_pair_that(base):
    out = aggregate_health_guardrail([_pair(base, (100.0, 100.0), (100.0, 100.0))])
    assert not any("THIẾU DỮ LIỆU" in f for f in out["flags"]), out["flags"]
    assert out["verdict"] == "OK", out


def test_cong_BAN_khi_suc_khoe_that_su_suy_giam(base):
    """Đối chứng cần thiết: nối nguồn xong thì cổng phải còn NHẠY, không phải luôn OK.
    Arm B nghỉ ít hơn hẳn ⇒ phải TREO."""
    out = aggregate_health_guardrail([_pair(base, (200.0, 200.0), (100.0, 100.0))])
    assert out["verdict"].startswith("TREO"), out
    assert any("rest_min_total" in f for f in out["flags"]), out["flags"]


def test_cham_tren_NHOM_BI_CHAM_chu_khong_tong_cohort(base):
    """UPDATE-114 lỗ (b): với `health_actor_ids={1}` thì chỉ actor 1 vào mẫu số ⇒ hiệu ứng
    trên người bị chạm không bị người không-bị-chạm pha loãng."""
    tong = _sm(base, 60.0, 100.0)
    cham = _sm(base, 60.0, 100.0, health_actor_ids={1})
    assert tong["rest_min_total"] == 160.0, tong["rest_min_total"]
    assert cham["rest_min_total"] == 60.0, cham["rest_min_total"]


def test_pha_loang_lam_cong_BO_SOT_ca_that(base):
    """Định lượng vì sao điều trên quan trọng: cùng một hiệu ứng −40′ trên người bị chạm,
    chấm trên tổng 2 người ra −20%, chấm trên nhóm bị chạm ra −40%. Với cohort 90 người và
    ~10 người bị chạm, cùng hiệu ứng chỉ còn ~1/9 độ lớn — dưới tolerance của cổng."""
    truoc_tong = _sm(base, 100.0, 100.0)["rest_min_total"]
    sau_tong = _sm(base, 60.0, 100.0)["rest_min_total"]
    truoc_cham = _sm(base, 100.0, 100.0, health_actor_ids={1})["rest_min_total"]
    sau_cham = _sm(base, 60.0, 100.0, health_actor_ids={1})["rest_min_total"]
    assert (truoc_tong - sau_tong) / truoc_tong == pytest.approx(0.20)
    assert (truoc_cham - sau_cham) / truoc_cham == pytest.approx(0.40)


def test_artifact_PHAI_khai_mau_so_n_actors_scope(base):
    """Suýt làm tôi báo sai: đọc `a_mean['n_actors_scope']` ra `None` và tưởng tầng 5 đang chấm
    toàn cohort. Thực tế `touched_actors` trả đúng 90/90 (coverage `all` chạm 100%) — chỉ là
    `_mean` không gộp khoá đó nên nó vắng khỏi artifact.

    Vắng mẫu số là vấn đề thật: verdict `OK` trên 90/90 và trên 9/90 đọc giống nhau nhưng nghĩa
    khác hẳn — ca sau là cổng canh nhiễu (pha loãng ~10×)."""
    out = aggregate_health_guardrail([_pair(base, (100.0, 100.0), (100.0, 100.0),
                                            health_actor_ids={1})])
    assert out["a_mean"].get("n_actors_scope") == 1, out["a_mean"]
    assert out["b_mean"].get("n_actors_scope") == 1, out["b_mean"]


def test_mau_so_KHONG_duoc_gan_significant_hai_chieu(base):
    """`n_actors_scope` là MẪU SỐ. Gắn `significant` cho nó là vô nghĩa: Δ luôn 0 (hai arm dùng
    cùng tập actor) nên nó sẽ hiện ra như "một kết quả không đáng kể" — đúng loại nhầm lẫn mà
    lỗ (e) của UPDATE-114 đã trả giá, chỉ khác nguyên nhân."""
    from gsm_sim.parallel import compare, HEALTH_KEYS_ONE_WAY, SCOPE_KEYS
    pairs = [_pair(base, (100.0, 100.0), (100.0, 100.0), health_actor_ids={1}) for _ in range(3)]
    for i, pr in enumerate(pairs):
        pr.seed = i
        pr.a, pr.b = {"payout_vnd": 1.0}, {"payout_vnd": 1.0}
    out = compare(pairs)
    row = out["system"]["n_actors_scope"]
    assert "significant" not in row, row
    assert "MẪU SỐ" in row.get("role", ""), row
    assert "n_actors_scope" not in HEALTH_KEYS_ONE_WAY, "mẫu số KHÁC chỉ tiêu một chiều"
    assert "n_actors_scope" in SCOPE_KEYS


def test_chi_tieu_mot_chieu_van_bi_chan_significant(base):
    """Đối chứng: tách `SCOPE_KEYS` ra không được làm hỏng cổng một chiều của lỗ (e)."""
    from gsm_sim.parallel import compare
    pairs = [_pair(base, (100.0, 100.0), (100.0, 100.0), health_actor_ids={1}) for _ in range(3)]
    for i, pr in enumerate(pairs):
        pr.seed = i
        pr.a, pr.b = {"payout_vnd": 1.0}, {"payout_vnd": 1.0}
    row = compare(pairs)["system"]["rest_min_total"]
    assert "significant" not in row and "one_way_gate" in row, row
