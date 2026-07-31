"""🔴 D-M3-15 — CỔNG: mọi cờ trong `configs/pilot_dongda.yaml` phải có người ĐỌC.

Vì sao cần một cổng thường trực (không phải một lần quét): mẫu *"thứ được khai báo nhưng không
có đường chạy"* đã sập **bốn lần** — `D-R12` · UPDATE-114 lỗ (a) · UPDATE-116 `D-M3-13` · và
chính lần quét sinh ra file này. `CLAUDE.md` §4b liệt kê *"config flag có thực sự được dùng"*
là hạng mục bắt buộc của adversarial self-review, nhưng chưa có gì thi hành nó.

Cái giá cụ thể của một cờ mồ côi: ai sweep nó để đo sẽ thấy Δ = 0 và kết luận **sai** rằng
"tham số này không ảnh hưởng" — trong khi thật ra tham số chưa từng được đọc. Đó là kết luận
sai có vẻ được hậu thuẫn bởi dữ liệu, loại tệ nhất.

Quét ra 5 cờ mồ côi (2026-08-01). **BA** trong số đó không chỉ mồ côi mà còn **mô tả SAI hành
vi** — chúng đã bị XOÁ; hai cờ còn lại là tính năng chưa implement nên nằm trong `CHUA_DUNG`:

| Cờ đã XOÁ | Khai trong yaml | Sự thật của sim | Lệch |
| --- | --- | --- | --- |
| `vehicle.swap_range_km` | 60 km | `100 / 1.6` = **62,5 km** | +4,2% |
| `vehicle.charge_range_km` | 110 km | `100 / 0.85` = **117,6 km** | +6,9% |
| `time.metrics_bucket_min` | 15′ | gộp theo **GIỜ** (`t_min // 60`, 4 chỗ) | 4× |

Phạm vi thật suy từ `*_consume_pct_per_km` (`behavior.soc_range_km`), nên hai khoá đầu là **số
dẫn xuất bị chép cứng rồi lệch dần** — đúng mẫu "hai nguồn sự thật cho một sự thật" của
`D-M3-11`, chỉ ở tầng config. XOÁ thay vì sửa giá trị: giữ một số dẫn xuất trong config là mời
gọi nó lệch lần nữa. Cờ thứ ba tệ hơn một chút — nó không dư, nó **nói sai**: người đọc config
tưởng metrics chia theo 15 phút.

Cách dùng cổng: thêm cờ mới mà chưa nối đường chạy ⇒ test ĐỎ. Muốn khai báo trước thì phải ghi
vào `CHUA_DUNG` kèm lý do — tức biến một sự im lặng thành một dòng khai báo có chủ ý.
"""
from __future__ import annotations

import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Cờ CỐ Ý chưa nối — mỗi dòng phải có lý do. Danh sách này là nơi duy nhất được phép "mồ côi".
CHUA_DUNG: dict[str, str] = {
    "newbie_program.combo_value_vnd":
        "Gói combo tân binh — chương trình combo CHƯA implement (chỉ `first_week_*` và "
        "`guarantee_*` có đường chạy trong `world.py`). Số PROXY, xem nhãn trong config.",
    "newbie_program.combo_min_trips_per_month":
        "Cùng lý do combo_value_vnd — ngưỡng của tính năng chưa implement.",
}


def _leaves(d, path=()):
    if isinstance(d, dict):
        for k, v in d.items():
            yield from _leaves(v, path + (str(k),))
    elif isinstance(d, list):
        return
    else:
        yield path, d


def _src_blob() -> str:
    parts = []
    for pat in ("src/**/*.py", "scripts/*.py", "ui/backend/app/**/*.py"):
        for p in ROOT.glob(pat):
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def test_moi_co_config_deu_co_nguoi_doc():
    cfg = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    blob = _src_blob()
    mo_coi = []
    for path, _val in _leaves(cfg):
        name = path[-1]
        if len(name) < 4 or name.isdigit():
            continue                                    # khoá quá ngắn ⇒ grep vô nghĩa
        dotted = ".".join(path)
        if dotted in CHUA_DUNG:
            continue
        # tên phải xuất hiện như một TOKEN (không phải substring của tên khác — bẫy đã gặp:
        # `swap_range_km` khớp nhờ `swap_range_km_per_pack`, một khoá hoàn toàn khác)
        if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", blob):
            mo_coi.append(dotted)
    assert not mo_coi, (
        "cờ config KHÔNG có người đọc — sweep nó sẽ ra Δ=0 và cho kết luận SAI rằng tham số "
        f"không ảnh hưởng: {mo_coi}. Nếu cố ý khai trước, thêm vào CHUA_DUNG kèm lý do.")


def test_CHUA_DUNG_khong_duoc_chua_co_DA_noi():
    """Đối chứng hai chiều: một cờ đã nối rồi mà vẫn nằm trong `CHUA_DUNG` là **nhãn sai** —
    nó dạy người đọc rằng cờ đó vô hiệu trong khi nó đang điều khiển hành vi thật."""
    blob = _src_blob()
    sai_nhan = [k for k in CHUA_DUNG
                if re.search(rf"(?<![A-Za-z0-9_]){re.escape(k.split('.')[-1])}(?![A-Za-z0-9_])",
                             blob)]
    assert not sai_nhan, f"khai 'chưa dùng' nhưng src CÓ đọc: {sai_nhan}"


def test_pham_vi_pin_KHONG_duoc_chep_cung_lai_trong_config():
    """Chặn tái phát: phạm vi pin là số DẪN XUẤT từ `*_consume_pct_per_km`. Chép cứng nó vào
    config tạo nguồn sự thật thứ hai, và lần trước hai nguồn đã lệch 4,2%/6,9%."""
    cfg = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    veh = cfg["vehicle"]
    for k in ("swap_range_km", "charge_range_km"):
        assert k not in veh, (
            f"`vehicle.{k}` quay lại config. Phạm vi = 100 / *_consume_pct_per_km "
            f"(`behavior.soc_range_km`); chép cứng nó sẽ lệch dần như lần trước.")
    for k in ("swap_consume_pct_per_km", "charge_consume_pct_per_km"):
        assert k in veh, f"thiếu `vehicle.{k}` — đây là THAM SỐ thật của phạm vi pin"


def test_metrics_bucket_khong_duoc_khai_lai_khi_sim_van_gop_theo_GIO():
    """Cùng họ với `*_range_km`: `time.metrics_bucket_min: 15` từng nằm trong config trong khi
    `sim_metrics` gộp theo **giờ cứng** (`int(t_min // 60)`, 4 chỗ) ⇒ cờ **mô tả sai hành vi**,
    không chỉ là cờ dư. Khai lại nó mà chưa sửa 4 chỗ hardcode là dựng lại đúng cái bẫy đó."""
    cfg = yaml.safe_load((ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8"))
    if "metrics_bucket_min" not in (cfg.get("time") or {}):
        return                                    # trạng thái đúng hiện nay
    blob = _src_blob()
    assert re.search(r"(?<![A-Za-z0-9_])metrics_bucket_min(?![A-Za-z0-9_])", blob), (
        "`time.metrics_bucket_min` quay lại config nhưng KHÔNG có ai đọc — sim vẫn gộp theo giờ")
