"""🔴 D-M3-12 — CỔNG THƯỜNG TRỰC: không L3 view nào được đọc record CHƯA TỒN TẠI.

UPDATE-115 tìm ra 6 rò rỉ thông tin tương lai bằng một **script dùng một lần**. Script đó đã
làm xong việc của nó rồi biến mất — nên deriver thêm sau lặp lại y nguyên được. File này biến
phép thử đó thành cổng.

**Quy tắc kiểm**: gọi mỗi deriver hai lần — trên bảng đầy đủ, và trên bảng đã xoá mọi record mà
**timestamp SỚM NHẤT của nó** vẫn còn sau `t_now` (tức record chưa tồn tại vào lúc hỏi). Hai kết
quả phải **hệt nhau**; khác nhau ⇒ view đang đọc thứ chưa xảy ra.

Vì sao lấy timestamp **sớm nhất** chứ không phải một khoá cố định — đây là bài học trả giá bằng
một false positive trong UPDATE-115: script cũ cắt theo `complete_time` (khoá đầu danh sách), nên
một cuốc *đặt* 07:50 và *xong* 08:10 bị nó loại, trong khi `demand_by_hour` **đúng** khi giữ cuốc
đó (tại 08:00 ta đã biết có yêu cầu lúc 07:50). Cắt theo min-timestamp không phụ thuộc việc
deriver dùng khoá nào ⇒ không tạo báo động giả kiểu đó.

**Giới hạn đã khai** (cổng này KHÔNG bắt được, đừng đọc nó như bảo đảm toàn phần): một record đã
tồn tại nhưng có **field** trỏ tương lai (vd `complete_time` của cuốc đang chạy) vẫn qua được
cổng. Chống ca đó cần luật per-field, không phải per-record. `tests/test_future_leak_l1r.py` canh
các ca cụ thể đã biết; cổng này canh **họ**.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from gsm_core.features import from_l1r as F
from gsm_core.mockgen.realdata import generate_realdata
from gsm_core.policy import PolicyBundle

D = "2026-07-03"
T_NOW = f"{D}T08:00:00+07:00"          # sáng sớm: đa số dữ liệu trong ngày còn ở TƯƠNG LAI
DRIVER = "d-62"                        # driver-day đã phơi ra D-M3-11

POLICY_REC = {   # cùng bundle với tests/test_features_from_l1r.py
    "schema_version": "1.0.0", "bundle_id": "b1", "version": "sim-policy-v0",
    "effective_from": "2026-07-01T00:00:00+07:00", "track": "platform", "service": "bike",
    "fare": {"base_vnd": 13000, "base_km": 2.0, "per_km_vnd": 4300}, "driver_share": 0.75,
    "points": {"peak": 10, "normal": 5, "peak_hours": [6, 7, 16, 17],
               "window_hours": list(range(6, 22))},
    "day_bonus_tiers": [[60, 30000], [100, 60000], [160, 115000], [200, 170000]],
    "thresholds": {"bonus_min_acceptance": 0.85, "bonus_min_completion": 0.85,
                   "forced_accept_below": 0.5},
    "source_url": None, "source": "MOCK",
}

# Mọi field thời gian xuất hiện trong 13 bảng. Cắt theo cái SỚM NHẤT của mỗi record.
TS_FIELDS = ("request_time", "complete_time", "entered_current_hex_at", "created_at",
             "last_seen_at", "updated_at", "reached_target_at", "detected_at",
             "penalization_time", "resolved_at")


@pytest.fixture(scope="module")
def tables():
    with TemporaryDirectory() as td:
        return generate_realdata(days=6, seed_base=900, out_dir=Path(td))["tables"]


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


def _truncated(tables: dict, t_now: str) -> dict:
    """Xoá record chưa TỒN TẠI tại `t_now` = mọi timestamp của nó đều sau `t_now`.

    Record chỉ có `local_date`/`order_date` (độ phân giải NGÀY) thì giữ — cổng này không phán
    về chúng, vì cắt theo ngày là quyết định ngữ nghĩa của từng deriver."""
    out = {}
    for entity, rows in tables.items():
        keep = []
        for r in rows:
            stamps = [str(r[f]) for f in TS_FIELDS if r.get(f)]
            if not stamps or min(stamps) <= t_now:
                keep.append(r)
        out[entity] = keep
    return out


def _cases(policy):
    return {
        "bonus_gap": lambda t: F.derive_bonus_gap_input_l1r(DRIVER, T_NOW, t, policy),
        "weekly_khoan": lambda t: F.derive_weekly_khoan_input_l1r(DRIVER, T_NOW, t, policy),
        "shift_plan": lambda t: F.derive_shift_plan_input_l1r(DRIVER, T_NOW, t, policy),
        "mission_select": lambda t: F.derive_mission_select_input_l1r(DRIVER, T_NOW, t, 4.0),
        "idle_reduction": lambda t: F.derive_idle_reduction_input_l1r(
            DRIVER, T_NOW, t, session_date=D),
        "penalty_explain": lambda t: F.derive_penalty_explain_input_l1r(DRIVER, T_NOW, t),
        "anomaly_alert": lambda t: F.derive_anomaly_alert_input_l1r(DRIVER, T_NOW, t),
    }


def test_khong_view_nao_doc_record_CHUA_TON_TAI(tables, policy):
    cut = _truncated(tables, T_NOW)
    ro_ri = {}
    for name, fn in _cases(policy).items():
        day_du, da_cat = fn(tables), fn(cut)
        if day_du != da_cat:
            khac = sorted(k for k in set(day_du) | set(da_cat)
                          if day_du.get(k) != da_cat.get(k))
            ro_ri[name] = khac
    assert not ro_ri, (
        "L3 view đổi giá trị khi xoá record CHƯA TỒN TẠI tại t_now ⇒ nó đang đọc tương lai "
        f"(họ lỗi D-M3-11, đã trả giá 7 bug): {ro_ri}")


def test_cong_nay_THUC_SU_bat_duoc_ro_ri(tables, policy):
    """Test sever-restore: cổng nào không tự chứng minh mình bắn được thì là cổng trang trí.

    Tái tạo đúng bug gốc `D-M3-11` — một deriver chỉ lọc theo NGÀY, không so `t_now` — rồi đòi
    phép thử phải phát hiện. Nếu ca này KHÔNG bắn, `test_khong_view_nao_doc_record_CHUA_TON_TAI`
    ở trên chỉ đang xanh vì nó không đo gì."""
    def deriver_bi_loi(t: dict) -> dict:
        segs = [r for r in t["public_driver_hex_tracking"]
                if r["driver_id"] == DRIVER
                and str(r.get("last_seen_at") or "")[:10] == D
                and r.get("tracking_status") == "idle"]           # ⚠ KHÔNG so t_now
        return {"total": sum(int(r.get("stay_duration_seconds") or 0) for r in segs)}

    day_du = deriver_bi_loi(tables)
    da_cat = deriver_bi_loi(_truncated(tables, T_NOW))
    assert day_du != da_cat, (
        "phép cắt KHÔNG tách được tương lai khỏi quá khứ trên chính driver-day của D-M3-11 ⇒ "
        "cổng ở trên vô nghĩa. Kiểm TS_FIELDS và T_NOW trước khi tin bất kỳ verdict xanh nào.")
    assert day_du["total"] > da_cat["total"], (day_du, da_cat)


def test_phep_cat_khong_xoa_sach_du_lieu(tables):
    """Đối chứng ngược: nếu `_truncated` xoá gần hết bảng thì test đầu xanh một cách rỗng
    (view rỗng == view rỗng). Đòi phần GIỮ LẠI phải đáng kể."""
    cut = _truncated(tables, T_NOW)
    for entity in ("trips", "public_driver_hex_tracking"):
        truoc, sau = len(tables[entity]), len(cut[entity])
        assert sau > 0, f"{entity}: cắt xong RỖNG ⇒ mọi so sánh sau đó vô nghĩa"
        assert sau < truoc, f"{entity}: cắt xong KHÔNG giảm ⇒ T_NOW quá muộn, cổng không đo gì"
