"""`D-ADV-04` — mẫu số của `historical_points_per_hour` phải là giờ online **TRONG BUCKET**.

## Bug đang sửa (đã reproduce, `research/audit/.../repro-s1-denominator.py`)

Producer chia **điểm-của-bucket** cho **giờ online TOÀN NGÀY**, còn solver
(`bonus_feasibility._hour_rate` → `_walk`) tiêu thụ con số đó như **điểm/giờ TRONG bucket** (nó nhân
`rate × span` cho **từng giờ** thuộc bucket). Vì `giờ_ngày ≥ giờ_bucket`, rate **luôn** bị ước NON.

**Ai đúng:** ngữ nghĩa của solver bị ghim bởi `tests/test_bonus_feasibility.py:112-119`
(`hist offpeak=15 ⇒ hours = gap/15`) ⇒ **solver ĐÚNG, producer SAI**. Các test dưới đây ghim ngữ nghĩa
đó ở **cả hai phía** để không bao giờ còn hai quy ước.

Vì sao nghiêm trọng: `S1` là solver **duy nhất** đường sản phẩm chạy (`B6-PARITY`) ⇒ hệ nói với tài xế
*"không với tới mốc"* về một mốc **với tới được** — bi quan có hệ thống, đúng lúc lời khuyên đáng giá nhất.
"""

import pytest

from gsm_core.policy import PolicyBundle
from gsm_core.features.bonus_gap import derive_bonus_gap_input
from gsm_core.solvers.bonus_feasibility import solve

from tests._bucket_rate_fixture import (build_l1, build_l1r, GAP_POINTS, HOURS_NEEDED_DUNG,
                                        RATE_DUNG, SHIFT_WINDOW, T_NOW)
from tests.test_bonus_feasibility import POLICY_REC


@pytest.fixture(scope="module")
def policy():
    return PolicyBundle.from_record(POLICY_REC)


# ---------- Đường L1 (CÓ mốc thời gian ⇒ tính CHÍNH XÁC được) ----------

def test_l1_rate_la_diem_tren_gio_TRONG_bucket(policy):
    """60đ peak trong 2 giờ peak ⇒ 30đ/h; 60đ offpeak trong 8 giờ offpeak ⇒ 7,5đ/h.

    Hiện tại trả `{peak: 6.0, offpeak: 6.0}` vì chia cho 10h TOÀN NGÀY.
    """
    gi = derive_bonus_gap_input("d-1", T_NOW, build_l1(), policy,
                                shift_window=SHIFT_WINDOW, history=[])
    assert gi["historical_points_per_hour"] == pytest.approx(RATE_DUNG)


def test_l1_end_to_end_moc_thuong_voi_toi_duoc(policy):
    """Đi qua ĐÚNG đường production `derive_bonus_gap_input → solve`.

    Đây là test quan trọng nhất: nó chứng minh hệ quả với TÀI XẾ, không chỉ một con số nội bộ.
    Trước fix: `feasible=False`, reason *"chỉ kiếm thêm được ~42đ < 50đ còn thiếu"*.
    """
    gi = derive_bonus_gap_input("d-1", T_NOW, build_l1(), policy,
                                shift_window=SHIFT_WINDOW, history=[])
    r = solve(gi, policy)
    sol = r["solution"]
    assert sol["gap_points"] == GAP_POINTS
    assert sol["feasible"] is True, (
        f"advisor vẫn nói KHÔNG với tới một mốc với tới được: {r['infeasible_reason']}")
    assert sol["hours_needed"] == pytest.approx(HOURS_NEEDED_DUNG, abs=0.05)


def test_ngay_online_ma_trang_diem_dong_0_vao_mau(policy):
    """ADV-05: `0.0` điểm/giờ là **DỮ LIỆU HỢP LỆ**, không phải thiếu dữ liệu.

    Tài xế online phủ giờ peak (16,17) nhưng KHÔNG có cuốc peak nào ⇒ mẫu peak phải là `0.0`.
    Hiện tại khoá `peak` **biến mất** khỏi hist ⇒ solver rơi về fallback lý thuyết **DƯƠNG**
    (`bonus_feasibility.py:53`) ⇒ "còn kịp" lạc quan đúng ở khung tài xế biết rõ là chết.
    """
    l1 = build_l1(hist_peak_hours=[])          # online 08–18 (phủ 16,17) nhưng 0 cuốc peak
    gi = derive_bonus_gap_input("d-1", T_NOW, l1, policy,
                                shift_window=SHIFT_WINDOW, history=[])
    hist = gi["historical_points_per_hour"]
    assert "peak" in hist, "bucket online-mà-trắng-điểm bị LOẠI khỏi mẫu (survivorship)"
    assert hist["peak"] == 0.0


def test_khong_bang_chung_thi_khong_co_khoa(policy):
    """Phân biệt **"không biết"** với **`0.0`** — hai thứ khác nhau, solver xử khác nhau.

    Ca online 08:00–15:00 KHÔNG phủ giờ peak nào (peak = 6,7,16,17) ⇒ **không có bằng chứng hiện
    diện** ⇒ hist KHÔNG được có khoá `peak` (khác hẳn ca trên, nơi có phủ mà 0 điểm ⇒ 0.0).
    """
    l1 = build_l1(hist_peak_hours=[], online_end_h=15)
    gi = derive_bonus_gap_input("d-1", T_NOW, l1, policy,
                                shift_window=SHIFT_WINDOW, history=[])
    assert "peak" not in gi["historical_points_per_hour"]


# ---------- Ghim quy ước MỘT CHIỀU giữa producer và solver ----------

def test_quy_uoc_MOT_chieu_producer_va_solver(policy):
    """Cổng chống tái diễn "hai quy ước cho một sự thật".

    Dựng cửa sổ **thuần một bucket** (hỏi 18:00 ⇒ giờ 18,19,20,21 đều offpeak) rồi đòi
    `hours_needed == gap / hist["offpeak"]`. Ai đổi mẫu số ở **một** bên — producer HOẶC solver —
    thì test này đỏ ngay, không cần ai nhớ ra là có hai chỗ phải sửa cùng nhau.

    `today_trips=29` ⇒ `points_now = 145` ⇒ gap 15đ. Cần vậy vì cửa sổ thuần offpeak chỉ có 4 giờ
    × 7,5đ = 30đ; gap 50 sẽ làm test đỏ vì **HẾT GIỜ**, không phải vì lệch quy ước.
    """
    t_now = T_NOW.replace("T15:", "T18:")
    gi = derive_bonus_gap_input("d-1", t_now, build_l1(today_trips=29), policy,
                                shift_window=[480, 1260], history=[])
    hist = gi["historical_points_per_hour"]
    assert "offpeak" in hist and hist["offpeak"] > 0
    sol = solve(gi, policy)["solution"]
    assert sol["hours_needed"] == pytest.approx(sol["gap_points"] / hist["offpeak"], abs=0.01)


# ---------- Đường L1R (KHÔNG có mốc thời gian ⇒ XẤP XỈ, phải cùng QUY ƯỚC) ----------

def test_l1r_rate_cung_QUY_UOC_voi_l1(policy):
    """Bảng thật chỉ có TỔNG `online_time` ⇒ giờ-trong-bucket phải XẤP XỈ từ span hoạt động.

    Không đòi khớp chính xác `{30, 7.5}` như đường L1: xấp xỉ có sai số (span quan sát được ngắn hơn
    ca thật vì cuốc cuối bắt đầu trước 18:00). Đòi hai thứ:
    1. **cùng bậc với quy ước ĐÚNG**, không phải quy ước cũ (peak phải ≫ 6.0),
    2. có **nhãn** nói rõ đây là xấp xỉ — không được trình bày như số đo.
    """
    from gsm_core.features.from_l1r import derive_bonus_gap_input_l1r
    l1r_tables = build_l1r()
    l1r = {"trips": l1r_tables["trips"], "driver_online_hours_sap_id": l1r_tables["online"]}
    gi = derive_bonus_gap_input_l1r("d-1", T_NOW, l1r, policy)
    hist = gi["historical_points_per_hour"]
    assert "peak" in hist, f"đường L1R mất bucket peak: {hist}"
    assert hist["peak"] > 2 * 6.0, (
        f"peak vẫn ở bậc của quy ước CŨ (6.0 = 60đ/10h toàn ngày): {hist}")
    assert 20.0 <= hist["peak"] <= 50.0, f"xấp xỉ lệch quá xa mức đúng 30.0: {hist}"
    assert gi["historical_rate_method"] == "estimated_span_scaled"


# ---------- Bất biến của helper xấp xỉ (đường KHÔNG có mốc thời gian) ----------

@pytest.mark.parametrize("span,online_h", [
    ((8 * 60, 18 * 60), 10.0),     # span = online: phân bổ trọn
    ((8 * 60, 18 * 60), 3.0),      # online ÍT hơn span (phần lớn span là offline)
    ((16 * 60, 17 * 60), 1.0),     # span thuần peak
    ((5 * 60, 23 * 60), 10.0),     # span tràn NGOÀI khung điểm hai đầu
])
def test_bat_bien_tong_gio_bucket_khong_vuot_online_do_duoc(policy, span, online_h):
    """**Không bao giờ bịa thêm giờ online.** Xấp xỉ chỉ được PHÂN BỔ con số đo được.

    Đây là lan can chống lớp lỗi tệ nhất của một estimator: tạo ra dữ liệu không tồn tại. Giờ nằm
    ngoài khung tính điểm cũng bị loại khỏi mẫu số (solver không bao giờ áp rate bucket cho giờ đó).
    """
    from gsm_core.rates import bucket_online_hours_estimated
    by_bucket, method = bucket_online_hours_estimated(policy, online_h, span)
    assert sum(by_bucket.values()) <= online_h + 1e-9, (
        f"bịa thêm giờ online: {by_bucket} > {online_h} (method={method})")
    assert all(v >= 0 for v in by_bucket.values())
