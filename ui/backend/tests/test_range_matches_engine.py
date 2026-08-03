"""D-M3-17 — CỔNG: số tầm pin UI hiển thị phải suy từ CÙNG hệ số mà engine dùng.

Vì sao cần cổng này, và vì sao 1.000 test cũ không bắt được: **không có test nào so UI với
engine**. Mỗi bên đúng theo tiêu chuẩn của riêng mình, nên cả hai đều xanh trong khi lệch nhau
gần 2×.

Đo được 2026-08-01 (smoke end-to-end):

| Nguồn | Công thức | Tầm ở SOC 100% |
| --- | --- | --- |
| engine `behavior.soc_range_km` — đội **đổi pin** | `soc / 1.6` | **62,5 km** |
| engine `behavior.soc_range_km` — đội **sạc** | `soc / 0.85` | **117,6 km** |
| `adapters/mockdata.py` (UI đang dùng) | `soc * 1.1` | **110 km** cho MỌI tài xế |
| `simulator.py` (endpoint legacy) | `soc * 3.2` | **320 km** |

⇒ tài xế đội đổi pin thấy tầm bị **thổi ~1,76×**; endpoint legacy thổi **5,1×** (320 km với xe
máy điện là vô lý — dải tham chiếu Feliz S là 100–130 km).

**Một phát hiện làm đổi cách sửa:** cả bảng mock lẫn 13 bảng GSM **không có** thông tin đội pin.
`driver_type` chỉ nói loại xe (`bike-electric`, `car`, `car-premium`, `bike-electric-rto`); engine
phân đội pin theo *archetype* (P1 sạc · P2/P4/P6/P7 đổi pin · P3/P5 chia 50/50). Nên đây là
**thiếu field**, không phải chọn sai hệ số — và ta không được lấy đó làm cớ để bịa một hệ số.

Cách xử lý đã chọn: khi **không biết** đội pin thì dùng hệ số **THẬN TRỌNG** (tầm NGẮN hơn) và
khai rõ dải. Lý do: với tài xế, báo tầm ngắn hơn thực tế chỉ gây bất tiện, còn báo dài hơn thực tế
thì có thể làm họ hết pin giữa đường.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT / "ui/backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "ui/backend"))

from app.adapters import mockdata  # noqa: E402


def _engine_consume() -> tuple[float, float]:
    """Hệ số tiêu hao (%/km) của engine — đọc từ CÙNG file cấu hình, không nhập tay."""
    from gsm_sim.runner import Config
    veh = Config.load(str(ROOT / "configs/pilot_dongda.yaml")).get("vehicle")
    return float(veh["swap_consume_pct_per_km"]), float(veh["charge_consume_pct_per_km"])


def _first_driver_and_date() -> tuple[str, str]:
    """Tài xế XE MÁY đầu tiên — engine chỉ mô hình xe máy nên phép so chỉ có nghĩa với đội này.

    Bẫy đã sập: bản đầu lấy `drivers[0]` và trúng `ce-0` (**xe hơi**) ⇒ test đỏ oan. Chính lần đỏ
    đó làm lộ ra `D-M3-18`: catalog có 40/150 tài xế xe hơi mà repo không có tham số tiêu hao cho
    xe hơi."""
    cat = mockdata.catalog()
    dv = mockdata.default_view()
    bike = [d["driver_id"] for d in cat["drivers"] if d["fleet"].startswith("bike")]
    assert bike, "catalog không có tài xế xe máy nào"
    return bike[0], dv["date"]


def _first_car_and_date() -> tuple[str, str] | tuple[None, None]:
    cat = mockdata.catalog()
    dv = mockdata.default_view()
    car = [d["driver_id"] for d in cat["drivers"] if d["fleet"].startswith("car")]
    return (car[0], dv["date"]) if car else (None, None)


def test_tam_pin_UI_suy_tu_he_so_cua_engine():
    """Tầm UI phải bằng `soc / hệ_số` của một trong hai đội — KHÔNG phải một hệ số riêng."""
    swap, charge = _engine_consume()
    drv, date = _first_driver_and_date()
    st = mockdata.driver_state(drv, date)
    soc, ui_range = st["soc_percent"], st["vehicle_range_km"]

    hop_le = {round(soc / swap, 1), round(soc / charge, 1)}
    assert ui_range in hop_le, (
        f"UI báo {ui_range} km ở SOC {soc}%, nhưng engine cho {sorted(hop_le)} km. "
        f"UI đang dùng công thức riêng ⇒ hai nguồn sự thật cho một đại lượng (D-M3-17)")


def test_khong_biet_doi_pin_thi_phai_THAN_TRONG():
    """Không biết đội pin ⇒ chọn tầm NGẮN hơn. Báo dài hơn thực tế có thể làm tài xế hết pin
    giữa đường; báo ngắn hơn chỉ gây bất tiện."""
    swap, charge = _engine_consume()
    drv, date = _first_driver_and_date()
    st = mockdata.driver_state(drv, date)
    soc = st["soc_percent"]
    ngan = round(soc / max(swap, charge), 1)      # hệ số tiêu hao LỚN ⇒ tầm NGẮN
    assert st["vehicle_range_km"] == ngan, (
        f"phải dùng tầm thận trọng {ngan} km, đang báo {st['vehicle_range_km']} km")


def test_phai_khai_ro_CO_SO_va_DAI_cua_con_so():
    """Một con số thận trọng mà không nói là thận trọng thì người đọc tưởng đó là số chính xác."""
    drv, date = _first_driver_and_date()
    st = mockdata.driver_state(drv, date)
    assert st.get("vehicle_range_km_basis"), "thiếu `vehicle_range_km_basis` — cơ sở của con số"
    assert "thận trọng" in st["vehicle_range_km_basis"].lower() \
        or "than trong" in st["vehicle_range_km_basis"].lower(), st["vehicle_range_km_basis"]
    lo, hi = st.get("vehicle_range_km_low"), st.get("vehicle_range_km_high")
    assert lo and hi and lo < hi, f"thiếu hoặc sai dải tầm pin: {lo}–{hi}"
    assert st["vehicle_range_km"] == lo, "số hiển thị phải là đầu THẤP của dải (thận trọng)"


def _hard_coded_range_factors(path: pathlib.Path) -> list[str]:
    """Tìm `soc * <hằng>` trong CODE THẬT — comment và docstring miễn nhiễm.

    Miễn nhiễm là bắt buộc, không phải tiện lợi: chính comment giải thích *"trước đây file này
    dùng `soc * 3.2`"* đã làm bản grep-thô của test này đỏ oan. Một cổng bắt cả lời giải thích
    về lỗi cũ sẽ dạy người sau xoá lời giải thích — đúng thứ ta muốn giữ.
    """
    import ast
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    def _is_soc(n) -> bool:
        return isinstance(n, ast.Name) and "soc" in n.id.lower()

    def _is_num(n) -> bool:
        return (isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool))

    hits = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div))):
            continue
        # CHỈ xét hai toán hạng TRỰC TIẾP. Quét cả cây con sẽ bắt oan `soc * _range_band()[0]`
        # (hằng `0` chỉ là chỉ số mảng) — tức bắt đúng đoạn code ĐÃ SỬA ĐÚNG.
        if (_is_soc(node.left) and _is_num(node.right)) or \
           (_is_num(node.left) and _is_soc(node.right)):
            hits.append(f"{path.name}:{node.lineno} → {ast.unparse(node)}")
    return hits


def test_khong_hard_code_he_so_tam_pin_trong_ui():
    """Chặn tái phát: hệ số tiêu hao phải đọc từ config, không viết cứng trong UI.

    Hai hệ số cũ (`soc * 1.1` và `soc * 3.2`) là chính thứ đã gây `D-M3-17`."""
    xau = []
    for f in (ROOT / "ui/backend/app").rglob("*.py"):
        xau += [f"{f.relative_to(ROOT).parent.as_posix()}/{h}"
                for h in _hard_coded_range_factors(f)]
    assert not xau, (
        "hệ số tầm pin bị viết cứng trong UI — phải suy từ `vehicle.*_consume_pct_per_km`: "
        + "; ".join(xau))


def test_scanner_nay_THUC_SU_bat_duoc(tmp_path):
    """Test sever-restore: cổng nào không tự chứng minh bắn được thì là cổng trang trí."""
    f = tmp_path / "gia_dinh_loi.py"
    f.write_text("def r(soc):\n    return round(soc * 3.2, 1)\n", encoding="utf-8")
    assert _hard_coded_range_factors(f), "scanner KHÔNG bắt được `soc * 3.2` ⇒ cổng vô nghĩa"

    g = tmp_path / "chi_comment.py"
    g.write_text('"""Trước đây dùng soc * 3.2 — đã bỏ."""\n# soc * 1.1 cũng vậy\n'
                 "def r(soc, k):\n    return soc * k\n", encoding="utf-8")
    assert not _hard_coded_range_factors(g), "comment/docstring phải MIỄN NHIỄM"


def test_nhan_nguon_van_con():
    """Đối chứng: sửa công thức không được làm mất nhãn MOCK (Q-06)."""
    drv, date = _first_driver_and_date()
    st = mockdata.driver_state(drv, date)
    assert st["vehicle_range_km_source"] == "MOCK"
    assert st["soc_source"] == "MOCK"


@pytest.mark.parametrize("soc", [30, 55, 95])
def test_cong_thuc_dung_tren_nhieu_muc_soc(soc):
    """Kiểm quan hệ tuyến tính đúng ở nhiều mức SOC, không chỉ ở một điểm."""
    swap, charge = _engine_consume()
    assert round(soc / max(swap, charge), 1) < round(soc / min(swap, charge), 1)
    # tầm thận trọng ở SOC 100% phải nằm trong dải tham chiếu xe máy điện (55–130 km)
    assert 40 <= round(100 / max(swap, charge), 1) <= 130


# ---------- D-M3-18: tài xế XE HƠI — hệ số xe máy KHÔNG áp dụng được ----------

def test_xe_hoi_phai_khai_KHONG_CO_CO_SO():
    """Engine và config chỉ mô hình xe máy điện (hai loại pin). Catalog lại có **40/150** tài xế
    xe hơi. Lặng lẽ đưa con số tính bằng hệ số xe máy cho họ là sai loại xe — tệ hơn cả lỗi
    1,76× ban đầu. Nên phải có cờ `applicable=False` + cơ sở nói rõ."""
    drv, date = _first_car_and_date()
    if drv is None:
        pytest.skip("catalog không có tài xế xe hơi")
    st = mockdata.driver_state(drv, date)
    assert st["vehicle_range_km_applicable"] is False, (
        f"{drv} là xe hơi nhưng cờ applicable vẫn True ⇒ UI sẽ hiện số sai loại xe")
    assert "KHÔNG CÓ CƠ SỞ" in st["vehicle_range_km_basis"], st["vehicle_range_km_basis"]


def test_xe_may_thi_applicable_True():
    """Đối chứng: cờ không được False tất cả cho tiện."""
    drv, date = _first_driver_and_date()
    assert mockdata.driver_state(drv, date)["vehicle_range_km_applicable"] is True


def test_van_tra_SO_chu_khong_tra_null():
    """Ràng buộc tương thích: `driver_state.dart:56` ép `(json[...] as num)` ⇒ null làm app
    Flutter của Khánh CRASH; `models.py:57` khai `float` nên pydantic cũng reject null. Vì vậy ta
    thêm CỜ chứ không đổi kiểu — thay đổi cộng thêm, không phá consumer nào."""
    for drv, date in (_first_driver_and_date(), _first_car_and_date()):
        if drv is None:
            continue
        v = mockdata.driver_state(drv, date)["vehicle_range_km"]
        assert isinstance(v, (int, float)) and v > 0, f"{drv}: {v!r}"
