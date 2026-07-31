"""Ba lỗ của đường ống A/B do vòng thiết kế D-M3-04 bắt được (2026-07-31) — đều là lỗi
HIỆN HÀNH, ảnh hưởng MỌI phép đo, không riêng D-M3-04.

- (a) `PairResult.adherence_a` tồn tại kèm comment *"giữ cho arm đối chứng (bài học DET-01:
  arm đối chứng cũng phải được ĐO, không giả định sạch)"* — nhưng **không cổng nào đọc nó**.
  Đúng họ lỗi `D-R12` (cơ chế tự quảng cáo ở comment + field, không có đường chạy).
- (c) `aggregate_adherence` chỉ cộng 4 khoá ⇒ `dismissed`/`suppressed`/`execution` **không
  bao giờ tới artifact**. Vi phạm bằng BỎ SÓT, không phải bằng tính sai.
- (e) Tầng 5 (đếm/phút, cổng MỘT CHIỀU) bị `compare()` đưa vào bảng significance HAI CHIỀU
  và `run_parallel.py` in như *"ĐỘNG TỚI HỆ THỐNG"* ⇒ veto tăng (tài xế chạm mệt nhiều hơn)
  bị đọc thành "advice làm hệ thống tốt lên". Chính hướng Goodhart mà tầng 5 sinh ra để chặn.
"""
from __future__ import annotations

from gsm_sim.parallel import PairResult, aggregate_adherence


def _pr(seed, a_by_channel, b_by_channel):
    return PairResult(
        seed=seed, actor_id=-1, a={}, b={}, system_a={}, system_b={},
        adherence_a={"by_channel": a_by_channel, "by_channel_archetype": {}, "flags": []},
        adherence_b={"by_channel": b_by_channel, "by_channel_archetype": {}, "flags": []})


def test_a_arm_doi_chung_ban_ban_khi_khong_sach():
    """DET-01: arm A (advice OFF) mà có adherence ⇒ arm đối chứng KHÔNG SẠCH ⇒ mọi Δ là rác.
    Trước fix: `aggregate_adherence` chỉ đọc `adherence_b` nên ca này lọt im lặng."""
    bad = _pr(1, a_by_channel={"positioning": {"decided": 7, "followed": 3,
                                               "event_decided": 7, "event_followed": 3}},
              b_by_channel={"positioning": {"decided": 50, "followed": 25,
                                            "event_decided": 50, "event_followed": 25}})
    out = aggregate_adherence([bad], nominal={"P4": 0.5})
    assert out["verdict"].startswith("TREO"), out
    assert any("đối chứng" in f or "arm A" in f for f in out["flags_per_seed"]), out


def test_a_arm_doi_chung_sach_thi_khong_ban_oan():
    ok = _pr(1, a_by_channel={},
             b_by_channel={"positioning": {"decided": 50, "followed": 25,
                                           "event_decided": 50, "event_followed": 25}})
    out = aggregate_adherence([ok], nominal={"P4": 0.5})
    assert out["verdict"] == "OK", out


def test_c_dismissed_va_suppressed_toi_duoc_artifact():
    """`dismissed`/`suppressed` là hai kết cục THẬT của một quyết định (ĐA-04) — bỏ sót chúng
    làm mất đường phân biệt "tài xế từ chối" với "advisor bị nhịp chặn"."""
    pr = _pr(1, a_by_channel={},
             b_by_channel={"rest_window": {"decided": 10, "followed": 4, "dismissed": 3,
                                           "suppressed": 2, "event_decided": 10,
                                           "event_followed": 4}})
    out = aggregate_adherence([pr], nominal={"P4": 0.5})
    row = out["by_channel"]["rest_window"]
    assert row["dismissed"] == 3, row
    assert row["suppressed"] == 2, row


def test_e_tang_5_khong_vao_bang_significance_hai_chieu():
    """Tầng 5 là cổng MỘT CHIỀU (`health_guardrail_flags`). Đưa nó vào bảng hai chiều của
    `compare()['system']` khiến "veto tăng" đọc thành "hệ thống tốt lên" — đúng hướng
    Goodhart mà tầng 5 sinh ra để chặn."""
    from gsm_sim.parallel import HEALTH_KEYS_ONE_WAY
    assert "veto_fired_n" in HEALTH_KEYS_ONE_WAY
    assert "rest_min_total" in HEALTH_KEYS_ONE_WAY
    assert "work_span_p90" in HEALTH_KEYS_ONE_WAY
