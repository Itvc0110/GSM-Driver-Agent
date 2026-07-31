"""D-M3-08 cơ chế 2 — `test_no_fatigue_in_payout_path`: fatigue KHÔNG có mặt trên đường tới tiền.

Spec: advisor-objective-model-v2 §1.2b ("MỆT là LATENT") + data-contract-counterfactual §7.4
(pseudocode — spec tự khai CHƯA TỒN TẠI trước cycle này).

Mọi mũi tiêm mutation chạy TRONG BỘ NHỚ (`source_override`) trên nội dung file THẬT —
không ghi đĩa. Mỗi mũi tiêm neo vào một chuỗi mã thật; neo mất (refactor) thì test tự ĐỎ
với message rõ, không im lặng thành vô dụng (chống anchor mục).
"""
from __future__ import annotations

from pathlib import Path

from _health_boundary_manifest import MANIFEST
from _health_boundary_scan import ROOT, discover, integrity, scan_tree


def _src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _inject(rel: str, anchor: str, replacement: str) -> dict[str, str]:
    src = _src(rel)
    assert anchor in src, (f"NEO MẤT: {anchor!r} không còn trong {rel} — refactor đã đổi "
                           f"dòng neo; cập nhật mũi tiêm, đừng xoá test")
    return {rel: src.replace(anchor, replacement, 1)}


# ---------- cổng chính + toàn vẹn ----------

def test_no_fatigue_in_payout_path():
    """Tên do spec §7.4 đặt. Đỏ trước cycle: module scanner không tồn tại (grep = 0)."""
    assert scan_tree() == []


def test_money_manifest_is_complete():
    """Hàm MỚI chạm token tiền mà chưa phân loại ⇒ đỏ — chặn đường lách 'viết hàm mới'."""
    unclassified, _ = integrity()
    assert unclassified == [], f"scope chạm tiền chưa phân loại: {unclassified}"


def test_money_manifest_has_no_dead_entries():
    """Manifest mục (scope bị xoá/đổi tên còn entry) ⇒ đỏ — chống 'sống trên giấy'."""
    _, dead = integrity()
    assert dead == [], f"entry chết trong manifest: {dead}"


def test_world_physiology_class_empty_today():
    """Phase B (E11) mới được khai WORLD_PHYSIOLOGY — hôm nay phải RỖNG (chưa có PHAN-QUYET
    thi hành). Đỏ = ai đó mở cơ chế mệt trong world mà không đi qua cổng phán quyết."""
    assert not [k for k, v in MANIFEST.items() if v == "WORLD_PHYSIOLOGY"]


# ---------- 4 mũi tiêm: scanner phải BẮN trên từng đường tấn công ----------

def test_scanner_catches_arithmetic_injection_in_real_solver():
    """Tiêm hệ số mệt vào công thức tiền của shift_dp ⇒ phải ra đúng 1 vi phạm."""
    over = _inject("src/gsm_core/solvers/shift_dp.py",
                   "exp_trips * (ppo - cost_per_trip)",
                   "exp_trips * (ppo - cost_per_trip) * (1.0 - fatigue_factor)")
    viols = scan_tree(over)
    assert viols and all("shift_dp.py" in v for v in viols), viols


def test_scanner_catches_dictkey_injection():
    """Tiêm khoá dict 'fatigue_cost_vnd' (string constant) vào scope tiền ⇒ bắn."""
    over = _inject("src/gsm_core/solvers/shift_dp.py",
                   "exp_trips * (ppo - cost_per_trip)",
                   'exp_trips * (ppo - cost_per_trip) - x.get("fatigue_cost_vnd", 0)')
    assert any("fatigue_cost_vnd" in v for v in scan_tree(over))


def test_scanner_catches_attribute_injection_in_real_world():
    """Tiêm actor.fatigue_threshold_min vào dòng cộng payout của world ⇒ bắn."""
    over = _inject("src/gsm_sim/world.py",
                   "actor.payout_vnd += self.policy.driver_payout_from_gross(order.gross_vnd)",
                   "actor.payout_vnd += int(self.policy.driver_payout_from_gross(order.gross_vnd)"
                   " * (1 - actor.fatigue_threshold_min / 1e5))")
    viols = scan_tree(over)
    assert viols and all("world.py" in v for v in viols), viols


def test_scanner_catches_signature_injection_in_real_pricing():
    """Tiêm tham số `fatigue` vào chữ ký hàm tính cước ⇒ bắn (arg thuộc scope của hàm)."""
    over = _inject("src/gsm_sim/policy.py",
                   "def gross_fare(self, dist_km: float",
                   "def gross_fare(self, dist_km: float, fatigue: float = 0.0")
    assert any("gross_fare" in v for v in scan_tree(over))


def test_scanner_catches_new_function_via_completeness():
    """Đường lách 'viết HÀM MỚI' — hàm mới sạch token cấm vẫn bị lớp 2 bắt vì chưa phân loại."""
    over = _inject("src/gsm_sim/behavior.py",
                   "def choose_idle_action",
                   "def energy_discount_vnd(actor, gross_vnd):\n"
                   "    return gross_vnd * 0.9\n\n\n"
                   "def choose_idle_action")
    unclassified, _ = integrity(over)
    assert ("src/gsm_sim/behavior.py", "energy_discount_vnd") in unclassified


# ---------- miễn nhiễm đúng chỗ ----------

def test_scanner_ignores_comments_and_docstrings():
    """`shift_dp.py:36,40` chứa chữ fatigue trong COMMENT ĐÚNG ĐẮN — AST không thấy ⇒ 0 vi
    phạm (regex trên text thô sẽ bắn oan rồi ai đó 'sửa' comment đúng — bẫy đã lường)."""
    src = _src("src/gsm_core/solvers/shift_dp.py")
    assert "fatigue" in src                    # chữ đó CÓ trong file (ở comment)
    assert not [v for v in scan_tree() if "shift_dp" in v]
    # docstring tiêm thêm cũng không bắn
    over = _inject("src/gsm_sim/policy.py", '"""', '"""KHÔNG phụ thuộc fatigue của tài xế.\n', )
    assert not [v for v in scan_tree(over) if "policy.py" in v]


def test_veto_scope_may_read_fatigue():
    """Lan can `should_defer_rest` ĐỌC fatigue_threshold_min hợp lệ (VETO, không tính tiền)
    — không nằm trong tập scope tiền nên không bị quét. Ghim để reviewer thấy ranh giới."""
    assert ("src/gsm_sim/advice_bridge.py", "AdviceActionBridge.should_defer_rest") \
        not in discover()


def test_manifest_covers_ui_backend_money_path():
    """Đường tiền SẢN PHẨM (ui/backend) cũng trong tầm quét — không chỉ sim."""
    ui = [k for k in MANIFEST if k[0].startswith("ui/backend/")]
    assert len(ui) >= 5, f"ui/backend chỉ có {len(ui)} scope tiền trong manifest — tầm quét teo?"
