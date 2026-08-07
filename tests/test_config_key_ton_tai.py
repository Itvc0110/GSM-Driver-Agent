"""🔴 CỔNG KHOÁ CONFIG — **chiều NGƯỢC** của `test_config_flags_wired.py`.

`test_config_flags_wired` hỏi: *"mọi cờ trong yaml có người đọc không?"*
File này hỏi câu còn lại: **"mọi khoá mà code đọc có TỒN TẠI trong yaml không?"**

## Vì sao phải có cả hai chiều — cổng cũ bị chính con bug nó đi bắt qua mặt

`Config.get(dotted, default)` trả **default IM LẶNG** khi path vắng. Code viết
`cfg.get("orders.trip_km_median", 3.5)` trong khi yaml có `demand.trip_km_median` ⇒ giá trị
config **không bao giờ tới nơi**, và không ai biết vì `3.5` tình cờ trùng.

Cổng cũ khớp theo **TÊN LÁ** (`test_config_flags_wired.py:80`): nó tìm token `trip_km_median`
trong toàn bộ source. Chuỗi `"orders.trip_km_median"` **chứa đúng token đó** ⇒ cổng kết luận
`demand.trip_km_median` *"đã có người đọc"*. **Chính dòng hỏng đã bảo lãnh cho khoá đúng.**
Vì vậy `test_config_flags_wired` cũng được sửa sang khớp **ĐƯỜNG DẪN ĐẦY ĐỦ** trong cùng cycle.

## Cái giá cụ thể

Ai sweep `demand.trip_km_median` để đo độ nhạy sẽ thấy **Δ = 0** và kết luận *"quãng đường
không ảnh hưởng"* — một kết luận SAI **trông như được dữ liệu hậu thuẫn**. Đây đúng loại tệ
nhất, và cùng họ với `D-M3-15` (cờ mồ côi) chỉ theo chiều ngược lại.

Hồ sơ: `research/audit/2026-08-07-root-cause-classes/` — cơ chế này bị **BA lớp** cùng nhận
(L1(a) = L3(a) = L6b) và sinh **ba đề xuất cổng trùng nhau** ⇒ viết **MỘT LẦN**, ở đây.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Receiver được coi là "config-like". Hẹp có chủ ý: `dict.get("a.b")` với khoá có dấu chấm là
# chuyện hiếm, nhưng mở rộng bừa sẽ đẻ dương tính giả và cổng sẽ bị tắt.
CFG_RECV = frozenset({"cfg", "config", "_cfg", "conf"})

QUET = ("src/**/*.py", "scripts/*.py", "ui/backend/app/**/*.py",
        "tests/*.py", "ui/backend/tests/*.py")

# Khoá code đọc mà CỐ Ý không có trong yaml — mỗi dòng phải có lý do.
# Đây là nơi DUY NHẤT được phép "đọc một khoá không tồn tại".
KHOA_NGOAI_CONFIG: dict[str, str] = {}


def _cfg() -> dict:
    return yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))


def _ton_tai(cfg: dict, dotted: str) -> bool:
    node = cfg
    for phan in dotted.split("."):
        if not isinstance(node, dict) or phan not in node:
            return False
        node = node[phan]
    return True


def _receiver(node: ast.Call) -> str:
    v = node.func.value
    if isinstance(v, ast.Name):
        return v.id
    if isinstance(v, ast.Attribute):
        return v.attr                       # `self.cfg.get(...)` → "cfg"
    if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute):
        return v.func.attr
    return ""


def _cac_lan_goi(goc: pathlib.Path = ROOT):
    """Sinh (file, lineno, dotted, default_src) cho mọi `<cfg-like>.get("a.b"[, default])`."""
    for pat in QUET:
        for f in sorted(goc.glob(pat)):
            try:
                cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for n in ast.walk(cay):
                if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "get" and n.args):
                    continue
                a0 = n.args[0]
                if not (isinstance(a0, ast.Constant) and isinstance(a0.value, str)):
                    continue
                if "." not in a0.value or _receiver(n) not in CFG_RECV:
                    continue
                mac_dinh = ast.unparse(n.args[1]) if len(n.args) > 1 else "<<KeyError>>"
                yield f, n.lineno, a0.value, mac_dinh


def test_A_moi_khoa_code_doc_deu_ton_tai_trong_config():
    """Chiều NGƯỢC: code → config. Đỏ khi code đọc một khoá yaml không có."""
    cfg = _cfg()
    ma = []
    for f, dong, dotted, mac_dinh in _cac_lan_goi():
        if dotted in KHOA_NGOAI_CONFIG or _ton_tai(cfg, dotted):
            continue
        ma.append(f"{f.relative_to(ROOT).as_posix()}:{dong}  "
                  f"cfg.get('{dotted}') → rơi về default {mac_dinh}")
    assert not ma, (
        "KHOÁ MA — code đọc một đường dẫn KHÔNG có trong pilot_dongda.yaml nên `Config.get` trả "
        "default IM LẶNG; sweep khoá thật sẽ ra Δ=0 và cho kết luận SAI:\n  " + "\n  ".join(ma)
        + "\nSửa đúng khoá, HOẶC thêm vào KHOA_NGOAI_CONFIG kèm lý do.")


# Đọc config bằng BIẾN — cổng tĩnh KHÔNG truy được đường dẫn ở những chỗ này, nên khoá ma nấp
# ở đây sẽ không bị `test_A` bắt. `UPDATE-117:97` tự nhận điểm mù này.
#
# ⚠ Bản đầu của cổng này ghim **0** call site (theo đề xuất của bản đồ audit). Chạy thử ra **5**,
# và cả 5 đều CHÍNH ĐÁNG (duyệt vòng lặp khoá, hoặc helper nhận `key` làm tham số). Ghim 0 sẽ
# biến cổng thành thứ luôn đỏ ⇒ người sau tắt nó ⇒ mất luôn phần có ích. Nên đổi sang **ghim
# DANH MỤC**: chỗ mù được phép tồn tại nhưng không được **âm thầm lớn lên**.
DOC_BANG_BIEN: dict[str, str] = {
    "src/gsm_sim/advice_bridge.py": "duyệt vòng lặp khoá `meta.*` bằng f-string — tiền tố cố định",
    "src/gsm_sim/dashboard_defaults.py": "helper nhận `key` làm tham số; đường dẫn do caller quyết",
    "src/gsm_sim/runner.py": "duyệt `world.{fname_key}` bằng f-string — tiền tố cố định",
    "tests/test_dashboard_defaults.py": "test của chính helper trên",
    "tests/test_policy_locked_keys.py": "duyệt danh sách khoá bị POLICY_LOCK",
    "tests/test_config_key_ton_tai.py":
        "chính file này — `test_sua_xong_thi_config_THUC_SU_CO_RANG` parametrize khoá. "
        "Ghi lại vì cổng đã bắt đúng nó ngay lần chạy kế: đó là bằng chứng cổng có răng.",
}


def test_B_diem_mu_doc_config_bang_BIEN_khong_duoc_lon_len():
    """Ghim DANH MỤC file có `cfg.get(<biến>)` (không ghim 0 — xem lý do ở `DOC_BANG_BIEN`)."""
    theo_file: dict[str, list[str]] = {}
    for pat in QUET:
        for f in sorted(ROOT.glob(pat)):
            try:
                cay = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for n in ast.walk(cay):
                if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "get" and n.args):
                    continue
                if _receiver(n) in CFG_RECV and not isinstance(n.args[0], ast.Constant):
                    theo_file.setdefault(f.relative_to(ROOT).as_posix(), []).append(
                        f":{n.lineno} cfg.get({ast.unparse(n.args[0])})")
    moi = {k: v for k, v in theo_file.items() if k not in DOC_BANG_BIEN}
    assert not moi, (
        "CHỖ MÙ MỚI — đọc config bằng BIẾN ở file chưa khai; `test_A` không bắt được khoá ma ở "
        f"đây:\n  {moi}\nNếu chính đáng, thêm vào DOC_BANG_BIEN kèm lý do.")
    het = [k for k in DOC_BANG_BIEN if k not in theo_file]
    assert not het, (
        f"khai 'đọc bằng biến' nhưng file không còn call site nào: {het} — xoá khỏi DOC_BANG_BIEN "
        "để danh mục không phình bằng những dòng đã chết")


def test_scanner_nay_THUC_SU_bat_duoc(tmp_path):
    """Đối chứng DƯƠNG TÍNH — bắt buộc.

    Một cổng không tự chứng minh đỏ được thì chính nó là *"cơ chế sống trên giấy"* mà cycle này
    đi bịt (tiền lệ: `test_future_leak_gate.py`, `test_range_matches_engine.py`). Dựng một file
    có khoá ma trong cây tạm rồi đòi scanner tìm ra."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "gia_lap.py").write_text(
        'def f(cfg):\n    return cfg.get("khong_he_ton_tai.khoa_ma", 1.0)\n', encoding="utf-8")
    thay = [d for _f, _l, d, _m in _cac_lan_goi(tmp_path)]
    assert "khong_he_ton_tai.khoa_ma" in thay, (
        "scanner KHÔNG bắt được khoá ma dựng sẵn ⇒ mọi kết quả xanh của nó là vô nghĩa")
    assert not _ton_tai(_cfg(), "khong_he_ton_tai.khoa_ma")


@pytest.mark.parametrize("dotted,khoa_ma,gia_tri_moi", [
    ("demand.trip_km_median", "orders.trip_km_median", 9.0),
    ("behavior.cancel_after_accept_rate", "orders.cancel_after_accept_rate", 0.40),
    ("dispatcher.offer_cooldown_min", "dispatcher.offer_cooldown_minutes", 45.0),
])
def test_sua_xong_thi_config_THUC_SU_CO_RANG(dotted, khoa_ma, gia_tri_moi):
    """Vế còn lại của cycle: khoá đúng phải **truyền được giá trị**, khoá ma thì không.

    `test_A` chứng minh đường dẫn tồn tại; test này chứng minh **hệ quả**: sweep khoá thật giờ
    đổi được số, còn nếu ai lỡ viết lại một namespace sai thì giá trị **im lặng rơi về default**
    — đúng cơ chế đã giấu ba lỗi này suốt nhiều tháng.

    Đây là phép thử ĐO, không phải lập luận: cùng một `Config`, hai đường đọc, hai kết quả."""
    from gsm_sim.config import Config

    goc = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    node = goc
    *cha, la = dotted.split(".")
    for p in cha:
        node = node[p]
    cu = node[la]
    node[la] = gia_tri_moi

    cfg = Config(goc, ROOT)
    assert cfg.get(dotted, cu) == gia_tri_moi, "khoá ĐÚNG không truyền được giá trị"
    assert cfg.get(khoa_ma, cu) == cu, (
        f"`{khoa_ma}` lẽ ra phải rơi về default — nếu nó cũng trả {gia_tri_moi} thì ai đó đã "
        f"thêm block trùng vào yaml và dựng lại HAI nguồn sự thật")


@pytest.mark.parametrize("dotted,co", [
    ("demand.trip_km_median", True),
    ("behavior.cancel_after_accept_rate", True),
    ("dispatcher.offer_cooldown_min", True),
    ("orders.trip_km_median", False),                 # namespace SAI — bug gốc của cycle này
    ("orders.cancel_after_accept_rate", False),
])
def test_ghim_ba_khoa_da_sua_va_hai_namespace_SAI(dotted, co):
    """Ghim cả hai vế: khoá ĐÚNG phải tồn tại, namespace SAI phải KHÔNG tồn tại.

    Vế thứ hai quan trọng ngang vế đầu: nếu ai đó "sửa" bằng cách **thêm** block `orders:` vào
    yaml cho khớp code, cổng test_A sẽ xanh trở lại trong khi hai nguồn sự thật vẫn còn nguyên."""
    assert _ton_tai(_cfg(), dotted) is co
