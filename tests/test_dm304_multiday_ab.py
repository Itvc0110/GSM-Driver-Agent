"""🔴 CỔNG cho đường đo `D-M3-04` (Cycle B) — `run_pair_multiday` + 4 cổng STOP.

Prereg: `specs/simulation/d-m3-04-multiday-prereg-locked.json` (khoá 2026-08-01; luật quyết định
khoá 2026-08-03; ba đính chính ghi TRƯỚC khi đo 2026-08-05).

## Cổng này canh cái gì

Phép đo này sẽ sinh ra một con số quyết định **GIỮ hay REVERT** một kênh chạm ranh giới sức khoẻ.
Nếu đường ống sai thì con số sai, và cái sai đó đi thẳng vào một quyết định sản phẩm. Nên mỗi ràng
buộc của prereg phải có một test **tự chứng minh bắn được**, không phải một comment.

Bốn ràng buộc dễ vi phạm nhất, mỗi cái có **đối chứng ngược**:
  1. BỎ ngày 0 — gộp vào là pha loãng chính thứ cần đo;
  2. MỘT `PairResult`/seed — sai thì `bootstrap_ci` resample theo NGÀY, mà các ngày KHÔNG độc lập;
  3. `channels` khai TƯỜNG MINH cả hai arm — `None` thừa kế im lặng từ config;
  4. DET-01 thu hẹp về kênh đang đo — quá rộng thì TREO 100% seed, quá lỏng thì mất cổng.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from gsm_sim.config import Config
from gsm_sim.parallel import (MIN_SEEDS_FOR_VARIANT_COMPARISON, _mean_dicts,
                              _merge_adherence, aggregate_adherence, run_pair_multiday)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_dm304.py"


@pytest.fixture(scope="module")
def cfg():
    return Config.load(str(ROOT / "configs/pilot_dongda.yaml"))


def _nap_script():
    """Nạp script theo ĐƯỜNG DẪN, không qua `import scripts.…`.

    `scripts/` **không phải package** (thiếu `__init__.py` — chính là `K-01`). Import kiểu package
    sẽ đỏ trên `uv run pytest` và xanh trên `python -m pytest`, đúng bẫy CWD-vào-`sys.path` mà repo
    đã trả giá. Nạp theo đường dẫn thì độc lập với chuyện đó."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_dm304_probe", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- nén ngày → một hàng/seed

def test_mean_dicts_TRUNG_BINH_chu_khong_TONG():
    """Prereg: *"trung bình driver_payout của ngày 1..2"*. Tổng thay vì trung bình sẽ thổi mọi Δ
    lên đúng `len(metric_days)` lần — và vì nó thổi **cả hai** arm nên hiệu số vẫn có dấu đúng,
    chỉ sai độ lớn. Đó là kiểu sai khó thấy nhất: biểu đồ vẫn đẹp, kết luận vẫn "đúng hướng"."""
    assert _mean_dicts([{"x": 10.0}, {"x": 20.0}])["x"] == 15.0


def test_mean_dicts_giu_gia_tri_KHONG_PHAI_SO():
    """Metric dict có cả khoá không phải số. Ép `mean` lên chúng sẽ nổ giữa một run 4 tiếng."""
    assert _mean_dicts([{"k": "abc", "n": 1}, {"k": "abc", "n": 3}]) == {"k": "abc", "n": 2}


def test_merge_adherence_CONG_chu_khong_trung_binh():
    """`decided`/`followed` là ĐẾM. Cổng thống kê `D-M3-10` (|z|>4) được thiết kế cho TỔNG — trung
    bình hoá làm mẫu số nhỏ đi `len(metric_days)` lần và cổng mất hết công suất, tức nó vẫn "chạy"
    nhưng không còn bắt được gì. Một cổng mất công suất im lặng còn tệ hơn không có cổng."""
    m = _merge_adherence([{"by_channel": {"rest_window": {"decided": 10, "followed": 4}}},
                          {"by_channel": {"rest_window": {"decided": 6, "followed": 3}}}])
    assert m["by_channel"]["rest_window"]["decided"] == 16
    assert m["by_channel"]["rest_window"]["followed"] == 7


# ---------------------------------------------------------------- ràng buộc metric_days

def test_metric_days_vuot_qua_days_thi_NO_SOM(cfg):
    """Nổ ở dòng đầu, không phải ở phút thứ 200 của một run 4 tiếng."""
    with pytest.raises(ValueError, match="vượt quá"):
        run_pair_multiday(cfg, 7000, days=2, channels_a={}, channels_b={}, metric_days=[1, 2])


def test_metric_days_rong_thi_NO(cfg):
    with pytest.raises(ValueError, match="rỗng"):
        run_pair_multiday(cfg, 7000, days=3, channels_a={}, channels_b={}, metric_days=[])


def test_SCRIPT_bo_ngay_0():
    """🔴 Ràng buộc prereg quan trọng nhất của phép đo này.

    Ngày 0 chưa có `DriverMemory` ⇒ `planned_rest_hour` vẫn `None` ⇒ kênh `rest_window` **INERT**
    (đo trước khi khoá prereg: decided **0**/12/11 theo ngày 0/1/2). Gộp ngày 0 vào là pha loãng
    chính thứ cần đo bằng một ngày mà can thiệp không tồn tại — Δ sẽ bị kéo về 0 và ta REVERT một
    kênh vì lý do sai."""
    src = (ROOT / "scripts/run_dm304.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    md = next(n for n in ast.walk(tree)
              if isinstance(n, ast.Assign) and any(
                  isinstance(t, ast.Name) and t.id == "METRIC_DAYS" for t in n.targets))
    assert ast.literal_eval(md.value) == [1, 2], "METRIC_DAYS phải là [1, 2] — ngày 0 bị BỎ"


# ---------------------------------------------------------------- channels tường minh

def test_SCRIPT_khai_channels_TUONG_MINH_ca_hai_arm():
    """`_cfg_with` chỉ ghi `positioning_overrides` khi `channels is not None` ⇒ truyền `None` cho
    arm A làm nó **thừa kế im lặng** `wait_only` từ `configs/pilot_dongda.yaml`. Kết quả tình cờ
    đúng, nhưng ngày ai đó đổi config thì nền của arm A đổi theo mà phép đo không biết."""
    m = _nap_script()
    for ten in ("CHANNELS_A", "CHANNELS_B"):
        assert getattr(m, ten).get("positioning_overrides") == "wait_only", (
            f"{ten} chưa khai nền `wait_only` TƯỜNG MINH — `_cfg_with` sẽ để nó thừa kế im lặng "
            f"từ configs/pilot_dongda.yaml")
    # Kiểm `CHANNEL_LADDER` KHÔNG ĐƯỢC DÙNG — bằng AST, không bằng tìm chuỗi: tên đó xuất hiện
    # trong chính COMMENT giải thích vì sao cấm dùng nó. Tìm chuỗi sẽ bắt oan lời cảnh báo.
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    dung = [n for n in ast.walk(tree)
            if isinstance(n, ast.Name) and n.id == "CHANNEL_LADDER"]
    nhap = [a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
            for a in n.names if a.name == "CHANNEL_LADDER"]
    assert not dung and not nhap, (
        "prereg CẤM `CHANNEL_LADDER['rest_window']` — nó bật kèm `shift_plan: True`, mà shift_plan "
        "đã bị ĐA-07/UPDATE-087 TẮT vì CÓ HẠI ⇒ đo hai can thiệp trộn nhau")


def test_SCRIPT_hai_arm_chi_khac_DUNG_MOT_kenh():
    """A/B chỉ được khác nhau ở can thiệp đang đo. Khác hai chỗ ⇒ Δ không quy được cho kênh nào."""
    m = _nap_script()
    khac = {k for k in set(m.CHANNELS_A) | set(m.CHANNELS_B)
            if m.CHANNELS_A.get(k) != m.CHANNELS_B.get(k)}
    assert khac == {"rest_window"}, f"hai arm khác nhau ở {khac}, phải chỉ khác `rest_window`"


# ---------------------------------------------------------------- DET-01 thu hẹp (STOP-B)

class _P:
    def __init__(self, seed, a=None, b=None):
        self.seed, self.adherence_a, self.adherence_b = seed, a or {}, b or {}


def test_DET01_thu_hep_KHONG_treo_vi_kenh_NEN():
    """🔴 Lý do phải thu hẹp: prereg định nghĩa `arm_A = positioning wait_only` — advice **BẬT** ⇒
    arm A LUÔN có quyết định `positioning`. Cổng cũ (bắt mọi kênh) sẽ TREO **100% số seed** và
    phép đo không bao giờ chạy được. Nền giống nhau ở hai arm nên nó triệt tiêu trong hiệu số."""
    p = _P(1, a={"by_channel": {"positioning": {"decided": 40, "followed": 20}}})
    out = aggregate_adherence([p], nominal={}, control_clean_channels=("rest_window",))
    assert out["verdict"] == "OK", out["flags_per_seed"]


def test_DET01_thu_hep_VAN_TREO_khi_arm_A_nhiem_kenh_dang_do():
    """Đối chứng bắt buộc — thu hẹp KHÔNG được biến thành tắt cổng."""
    p = _P(1, a={"by_channel": {"positioning": {"decided": 40},
                                "rest_window": {"decided": 3}}})
    out = aggregate_adherence([p], nominal={}, control_clean_channels=("rest_window",))
    assert out["verdict"].startswith("TREO")
    assert "rest_window" in str(out["flags_per_seed"])


def test_DET01_mac_dinh_GIU_NGUYEN_hanh_vi_cu():
    """Không truyền tham số ⇒ bắt MỌI kênh, y như trước. Mọi caller cũ (`run_ladder`) không đổi."""
    p = _P(1, a={"by_channel": {"positioning": {"decided": 40}}})
    assert aggregate_adherence([p], nominal={})["verdict"].startswith("TREO")


# ---------------------------------------------------------------- STOP-A cả hai arm

def test_STOP_A_soi_CA_HAI_arm():
    """Prereg STOP-A: *"TREO ở BẤT KỲ arm nào"*. Bản cũ chỉ gộp `adherence_b` ⇒ arm A không qua
    cổng thống kê. Vô hại với `run_pair` (arm A advice-off), nhưng `D-M3-04` có arm A BẬT
    positioning ⇒ arm đó cũng có thước adherence riêng, và thước hỏng ở A làm hỏng Δ y như ở B."""
    # arm A: 100 quyết định, 100 followed ⇒ adherence 1,0 vs danh nghĩa 0,5 ⇒ |z| lớn
    p = _P(1, a={"by_channel_archetype": {"rest_window|P4": {"decided": 100, "followed": 100}}})
    nom = {"P4": 0.5}
    assert aggregate_adherence([p], nominal=nom, gate_both_arms=False)["verdict"] == "OK"
    out = aggregate_adherence([p], nominal=nom, gate_both_arms=True)
    assert out["verdict"].startswith("TREO"), out
    assert any("[arm A]" in f for f in out["flags_per_seed"])


# ---------------------------------------------------------------- min_seeds + fingerprint

def test_SCRIPT_cham_bang_min_seeds_100_khong_phai_30():
    """`run_ladder` gọi `compare(pairs)` KHÔNG truyền `min_seeds` ⇒ dùng hằng 30. Prereg khoá 100.
    Đi lại đường đó là âm thầm chấm bằng ngưỡng sai."""
    src = (ROOT / "scripts/run_dm304.py").read_text(encoding="utf-8")
    assert "compare(pairs, min_seeds=MIN_SEEDS_FOR_VARIANT_COMPARISON)" in src
    assert MIN_SEEDS_FOR_VARIANT_COMPARISON == 100


def test_fingerprint_actors_co_MOT_nguon():
    """STOP-D dùng `fingerprint_actors`. Trước 2026-08-05 nó chỉ sống ở `scripts/` ⇒ một cổng STOP
    của prereg phụ thuộc hàm ngoài thư viện. Nay ở `sim_metrics`; script phải IMPORT chứ không
    định nghĩa lại — hai bản sao hơi khác nhau là cách một cổng tất định mất hiệu lực im lặng."""
    from gsm_sim.sim_metrics import fingerprint_actors  # noqa: F401

    probe = (ROOT / "scripts/probe_adherence_truth.py").read_text(encoding="utf-8")
    assert "from gsm_sim.sim_metrics import fingerprint_actors" in probe
    assert "def fingerprint_actors" not in probe, "probe vẫn giữ bản sao thứ hai"


def test_SCRIPT_kiem_fingerprint_CA_HAI_ngay():
    """Prereg nói ngày 0, brief nói ngày 1 ⇒ đính chính: kiểm CẢ HAI. Ngày 0 kiểm tất định thế
    giới; ngày 1 kiểm tất định SAU khi `DriverMemory` truyền qua — chỗ multiday thật sự có thể mất
    tất định."""
    src = (ROOT / "scripts/run_dm304.py").read_text(encoding="utf-8")
    assert "for d in (0, 1):" in src, "STOP-D phải kiểm cả ngày 0 lẫn ngày 1"


def test_SCRIPT_KHONG_quy_suc_khoe_ra_VND():
    """`cam_vinh_vien` của prereg. Cổng thô nhưng chỗ này đáng có một cổng thô: nó là ranh giới
    §1.2b, và một dòng nhân tỉ giá lọt vào đây thì mọi phát biểu sau đó đều hỏng."""
    src = (ROOT / "scripts/run_dm304.py").read_text(encoding="utf-8")
    for token in ("rest_min_total *", "* vnd_per", "rest_to_vnd", "health_vnd"):
        assert token not in src, f"có dấu hiệu quy sức khoẻ ra tiền: {token!r}"
