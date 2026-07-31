"""D-M3-05 — guardrail TẦNG 5: lan can sức khoẻ còn nguyên không (spec §1.2b bảng enforce).

Vì sao tồn tại: phản biện chéo từng đo được rằng XOÁ lan can `fatigued` làm veto 54/90 → 0/90,
test vẫn xanh, net TĂNG, và guardrail 4 tầng câm. Tầng 5 tố giác đúng đòn đó.

Tiền đề đã ĐO (đảo tiền đề của đề bài): `veto_fired_n` KHÔNG trơ — lan can bắn hàng trăm
lần/run (số 0/873 của D-M3-04 là số lần kênh NÓI, không phải số lần lan can CHẶN).
`defer_cap` thì trơ thật (defer=0 ⇒ không bao giờ chạm trần) — khai ở test T3.
"""
from __future__ import annotations

import copy

import pytest

from gsm_sim.config import Config
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with
from gsm_sim.runner import run_once
from gsm_sim.sim_metrics import (DRIVE_BREAK_MIN, REST_RAILS, continuous_work,
                                 health_guardrail, health_guardrail_flags,
                                 rest_rails_audit, system_guardrail)


@pytest.fixture(scope="module")
def run_a():
    cfg = _cfg_with(Config.load("configs/pilot_dongda.yaml"),
                    enabled=False, actor_id=None, channels=None)
    return run_once(cfg, 5100)


@pytest.fixture(scope="module")
def run_b():
    cfg = _cfg_with(Config.load("configs/pilot_dongda.yaml"),
                    enabled=True, actor_id=None,
                    channels=CHANNEL_LADDER["all"], coverage="all")
    return run_once(cfg, 5100)


# --- T1/T2: lan can sống và ĐẾM ĐƯỢC ------------------------------------------

def test_t1_veto_counter_khong_am_tham_bang_0(run_b):
    """Đỏ nếu nhánh `else:` log advice_rest_veto bị bỏ (mọi khoá = 0) — cơ chế 'sống
    trên giấy' đúng mẫu D-R12."""
    audit = rest_rails_audit(run_b)
    assert audit["veto_calls_n"] > 0, "khong co event advice_rest_veto nao — nhánh log chết"
    assert audit["veto_fired_n"] > 0, "lan can không bắn lần nào — bất thường ở arm all"


def test_t2_veto_calls_di_kem_bat_buoc(run_a, run_b):
    """Mẫu số đổi theo arm (advice giữ tài xế online lâu hơn) — đọc fired mà không đọc
    calls là đọc sai. Ghim CẢ HAI khoá tồn tại ở CẢ HAI arm."""
    for r in (run_a, run_b):
        audit = rest_rails_audit(r)
        assert set(audit) >= {"veto_calls_n", "veto_fired_n",
                              *(f"veto_{x}_n" for x in REST_RAILS)}


def test_t3_defer_cap_TRO_o_config_hien_hanh(run_b):
    """`defer_cap` chỉ bắn sau khi ĐÃ defer, mà kênh nói 0 lần (D-M3-04) ⇒ trơ.
    ĐỎ = TIN TỐT: D-M3-04 được sửa, kênh nói được, defer thật xảy ra — lúc đó gỡ khai-trơ
    và căn lại cổng, KHÔNG được sửa test cho xanh."""
    assert rest_rails_audit(run_b)["veto_defer_cap_n"] == 0


# --- T4/T5: tầng 5 tố giác đúng đòn -------------------------------------------

def test_t4_tang5_to_giac_khi_lan_can_sup_ve_0(run_a):
    """Kịch bản xoá-lan-can (mô phỏng bằng dict): veto sống ở A, chết ở B ⇒ PHẢI có flag.
    Đây chính là ca 'guardrail 4 tầng câm' — tầng 5 sinh ra để bắn ở đây."""
    a = health_guardrail(run_a)
    b = dict(a)
    for r in REST_RAILS:
        b[f"veto_{r}_n"] = 0
    flags = health_guardrail_flags(a, b)
    assert any("SỤP VỀ 0" in f for f in flags), flags


def test_t5_cong_mot_chieu_khong_khen_veto_cao(run_a):
    """Chống Goodhart: veto CAO HƠN / nghỉ NHIỀU HƠN không tạo flag (không có chiều khen).
    Nếu ai thêm chiều thưởng, tối ưu cho nó = ép tài xế chạm mệt nhiều hơn để 'qua cổng'."""
    a = health_guardrail(run_a)
    b = dict(a)
    b["veto_fatigued_n"] = a["veto_fatigued_n"] * 3 + 100
    b["rest_min_total"] = a["rest_min_total"] * 1.5
    assert health_guardrail_flags(a, b) == []


def test_t5b_to_giac_khi_an_vao_nghi_va_keo_dai_chuoi(run_a):
    a = health_guardrail(run_a)
    b = dict(a)
    b["rest_min_total"] = a["rest_min_total"] * 0.9          # −10% > tol 2%
    b["work_span_p90"] = a["work_span_p90"] * 1.2            # +20% > tol 10%
    flags = health_guardrail_flags(a, b)
    assert any("rest_min_total" in f for f in flags)
    assert any("work_span_p90" in f for f in flags)


# --- T6/T7: continuous_work — CẢ HAI định nghĩa (Cường chốt 2026-07-31) --------

def test_t6_hai_dinh_nghia_tach_bach(run_a):
    """work_span (nghỉ→nghỉ, gồm chờ khách) ≥ drive_min (phút lái thật) — hai cột riêng,
    tên nói rõ. Baseline seed 5100: span_max ~697′, drive_max ~484′ (62/90 vs 25/90 vượt
    240′ — chọn MỘT định nghĩa là mù nửa bức tranh)."""
    cw = continuous_work(run_a)
    assert cw["work_span_max"] >= cw["drive_min_max"]
    assert cw["work_span_p90"] >= cw["drive_min_p90"]
    assert cw["drive_min_max"] > 0


def test_t6b_gop_dung_tren_du_lieu_tong_hop():
    """Số tay: lái 100′ · nghỉ 30′ (reset) · lái 50′ + chờ 40′ + lái 60′ (không reset vì
    idle không phải nghỉ) ⇒ span nửa sau = 150′, drive nửa sau = 110′."""
    class _R:
        segments = [
            {"actor_id": 1, "t0": 0.0, "t1": 100.0, "kind": "on_trip"},
            {"actor_id": 1, "t0": 100.0, "t1": 130.0, "kind": "rest"},      # 30' >= break
            {"actor_id": 1, "t0": 130.0, "t1": 180.0, "kind": "enroute"},   # 50'
            # 40' idle gap — KHÔNG reset, KHÔNG cộng drive
            {"actor_id": 1, "t0": 220.0, "t1": 280.0, "kind": "relocate"},  # 60'
        ]
        actors = []
    cw = continuous_work(_R(), break_min=20.0)
    assert cw["work_span_max"] == 150.0       # 130 → 280
    assert cw["drive_min_max"] == 110.0       # 50 + 60


def test_t7_break_min_dan_xuat_tu_phan_phoi_nghi_cua_world():
    """DRIVE_BREAK_MIN phải ≤ độ dài nghỉ NGẮN NHẤT của world (uniform[REST_MIN, REST_MAX])
    — mọi lần nghỉ thật đều reset chuỗi. Đổi phân phối nghỉ ở world mà không căn lại ⇒ đỏ,
    buộc dẫn xuất lại thay vì để chỉ tiêu đổi nghĩa im lặng."""
    from gsm_sim.world import REST_MIN_MINUTES
    assert DRIVE_BREAK_MIN <= REST_MIN_MINUTES


# --- T8/T9: event veto không rò rỉ + behavior-neutral ---------------------------

def test_t8_event_veto_khong_lot_lifecycle_va_adherence(run_b):
    """`advice_rest_veto` mang channel='rest_window' — RẤT dễ bị ai đó map vào lifecycle
    ⇒ mẫu số adherence phình hàng trăm lần advisor CHƯA HỀ NÓI ⇒ decision_adherence sập.
    Ghim: không decision_id, không vào lifecycle, không đổi by_channel."""
    from gsm_core.lifecycle import projections as p
    assert all("decision_id" not in e.detail for e in run_b.events
               if e.kind == "advice_rest_veto")
    lc = p.sim_events_to_lifecycle(run_b.events)
    assert not [e for e in lc if e.get("kind") == "advice_rest_veto"]


def test_t9_log_veto_la_behavior_neutral(run_a):
    """Fingerprint per-actor của run mới phải KHỚP baseline TRƯỚC cơ chế 3 (đã lưu từ cycle
    E10 — cùng seed 5100, cùng config off). Nhánh else chỉ log: 0 RNG, 0 đổi state."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        "probe_m", Path(__file__).resolve().parents[1] / "scripts" / "probe_adherence_truth.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # exact-repeat: chạy lại cùng seed phải ra cùng fingerprint (deterministic guard);
    # so với baseline lịch sử làm ở cấp cycle (UPDATE) vì test không giữ hash cũ.
    cfg = _cfg_with(Config.load("configs/pilot_dongda.yaml"),
                    enabled=False, actor_id=None, channels=None)
    assert m.fingerprint_actors(run_a) == m.fingerprint_actors(run_once(cfg, 5100))


# --- T10: tầng 5 có mặt trong system_guardrail (không "sống trên giấy") ---------

def test_t10_system_guardrail_mang_tang_5(run_a):
    g = system_guardrail(run_a)
    for k in ("rest_min_total", "veto_fired_n", "veto_calls_n",
              "work_span_p90", "drive_min_p90", "work_span_max", "drive_min_max"):
        assert k in g, f"guardrail thiếu khoá tầng 5: {k}"
