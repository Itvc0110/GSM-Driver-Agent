"""Tầng 5 phải đo được trên NHÓM BỊ CHẠM, không chỉ trên tổng cohort — vòng soi D-M3-04 bắt.

Vấn đề (phụ thuộc cấu hình, đã đo): với ladder `all` + coverage `all`, can thiệp chạm **100%**
tài xế nên cổng trên tổng cohort đủ nhạy (`rest_min_total` +15% ≫ tolerance 2%). Nhưng với
kênh THƯA — đúng cấu hình `D-M3-04` (`rest_window` nói ~11 lần/ngày cho 90 tài xế ⇒ chạm
~10%) — hiệu ứng bị pha loãng ~10× ⇒ nằm dưới nhiễu seed ⇒ **cổng tầng 5 canh NHIỄU**.

Nguy hiểm cụ thể: khi đó verdict TREO/OK trở nên tuỳ seed, và người sửa sẽ nới
`REST_TOTAL_DROP_TOL`/`SPAN_P90_RISE_TOL` — tức phá tầng 5 từ bên trong (mẫu `D-R20`).
"""
from __future__ import annotations

from gsm_sim.sim_metrics import health_guardrail, touched_actors


class _Seg:
    """Result tối giản: 2 actor, chỉ 1 người bị chạm."""

    class _A:
        def __init__(self, aid, rest):
            self.actor_id, self.rest_min = aid, rest

    def __init__(self, rest1, rest2, touched_aid):
        self.actors = [self._A(1, rest1), self._A(2, rest2)]
        self.segments = []
        self.events = [type("E", (), {"kind": "advice_rest_window", "actor_id": touched_aid,
                                      "detail": {"channel": "rest_window"}, "cell": "",
                                      "t_min": 400.0})()]


def test_touched_actors_doc_tu_event_advice():
    r = _Seg(100.0, 100.0, touched_aid=1)
    assert touched_actors(r) == {1}
    assert touched_actors(r, channel="rest_window") == {1}
    assert touched_actors(r, channel="positioning") == set()


def test_tang5_tinh_duoc_tren_nhom_bi_cham():
    """Actor 1 (bị chạm) nghỉ 60′, actor 2 (không chạm) nghỉ 100′.

    Tổng cohort = 160′ — pha loãng. Trên nhóm bị chạm = 60′, thấy đúng thứ cần thấy."""
    r = _Seg(60.0, 100.0, touched_aid=1)
    tong = health_guardrail(r)
    assert tong["rest_min_total"] == 160.0
    cham = health_guardrail(r, actor_ids={1})
    assert cham["rest_min_total"] == 60.0, cham


def test_pha_loang_dinh_luong_duoc():
    """Hiệu ứng −40′ trên MỘT người: trên tổng 2 người là −20%, trên nhóm chạm là −40%.
    Với cohort 90 người và 10 người bị chạm, cùng hiệu ứng chỉ còn −1/9 độ lớn — dưới
    tolerance 2% của cổng ⇒ đó là cơ chế 'cổng canh nhiễu'."""
    truoc = health_guardrail(_Seg(100.0, 100.0, 1))
    sau = health_guardrail(_Seg(60.0, 100.0, 1))
    pha_loang = (truoc["rest_min_total"] - sau["rest_min_total"]) / truoc["rest_min_total"]
    that = (100.0 - 60.0) / 100.0
    assert abs(pha_loang - 0.20) < 1e-9 and abs(that - 0.40) < 1e-9
    assert pha_loang < that, "pha loãng phải làm hiệu ứng NHỎ đi"
