"""CỔNG: `OSRM_BASE_URL` phải có người ĐỌC, và không mirror nào được sai tên miền.

Hai lỗi thật, tìm ra 2026-08-03 bằng cách **gọi thật** chứ không đọc code (UPDATE-128):

1. `.env` và `.env.example` mô tả `OSRM_BASE_URL` như tầng 1 của routing driver-app, nhưng
   `try_osrm()` **viết cứng** host ⇒ sửa biến không đổi hành vi. Cường hỏi *"có cần cập nhật
   OSRM_BASE_URL ở end của tôi không"* và câu trả lời trung thực lúc đó là *"đổi cũng không
   ảnh hưởng gì"* — một biến cấu hình vô nghĩa mà tài liệu lại nói là quan trọng. Đúng họ
   `D-M3-15` (cờ config không ai đọc), chỉ ở tầng biến môi trường nên `test_config_flags_wired`
   không quét tới.

2. Mirror thứ hai viết `router.project.osrm.org` (dấu **chấm**) thay vì `router.project-osrm.org`
   (gạch **ngang**). Đo được:

   | Host | DNS | TLS/HTTP |
   | --- | --- | --- |
   | `router.project-osrm.org` | phân giải OK | **HTTP 200 `code:"Ok"`** |
   | `router.project.osrm.org` | phân giải OK (**IP XOAY** — xem dưới) | **`CERTIFICATE_VERIFY_FAILED: Hostname mismatch`** |

   Nó phân giải được nên trông như host thật — nhưng chưa từng trả về một tuyến nào. Suite cũ
   không thể bắt: mọi test routing đều `monkeypatch` `urlopen`, nên tên miền không bao giờ bị
   phân giải thật. ⇒ **Cổng này kiểm CHUỖI URL, không gọi mạng** — cố ý, vì test phụ thuộc mạng
   là test giả xanh/giả đỏ.

   ⚠ **ĐÍNH CHÍNH của chính tôi:** bản đầu docstring này ghi IP cụ thể `74.63.219.252` cho host
   sai. **Số đó không tái lập được** — soi độc lập đo ra `212.92.105.211`, tôi đo lại ra
   `212.92.105.214`. Nó là **tên miền đỗ (parked) với IP xoay**, nên trích một IP cố định là ghi
   một con số không kiểm được — đúng loại claim mà repo đã trả giá (`+6.016đ`). Điều **tái lập
   được** và cũng là điều duy nhất cần biết: **TLS luôn từ chối vì hostname mismatch**.

⚠ Sự thật dễ hiểu sai, và nó tái lập được: hai mirror OSRM **cùng phân giải về một máy** —
`5.148.170.168` **và cùng cả IPv6 `2a02:418:39aa:8::7`** (hạ tầng FOSSGIS) ⇒ thêm mirror KHÔNG cho
thêm hạn mức. Ai gặp rate limit mà đi đổi mirror sẽ mất thời gian vô ích; đường đúng là tầng 2
(GraphHopper) hoặc cache.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT / "ui/backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "ui/backend"))

from app.routers import routing  # noqa: E402

WP = "105.8230,21.0130;105.8340,21.0210"


def test_OSRM_BASE_URL_thuc_su_duoc_doc(monkeypatch):
    """Đổi biến ⇒ URL dựng ra phải đổi. Đây là toàn bộ nội dung của chữ 'wired'."""
    monkeypatch.setenv("OSRM_BASE_URL", "https://osrm.vi-du-noi-bo.test")
    urls = routing.osrm_endpoints(WP)
    assert any("osrm.vi-du-noi-bo.test" in u for u in urls), (
        f"`OSRM_BASE_URL` không được đọc — mọi URL vẫn là host viết cứng: {urls}")


def test_thieu_bien_thi_dung_mac_dinh_CON_SONG(monkeypatch):
    """Xoá biến ⇒ phải rơi về mirror mặc định đã kiểm sống, không phải về rỗng/None."""
    monkeypatch.delenv("OSRM_BASE_URL", raising=False)
    urls = routing.osrm_endpoints(WP)
    assert any("router.project-osrm.org" in u for u in urls), urls
    assert all(u.startswith("http") for u in urls), urls


def test_bien_RONG_khong_lam_URL_hong(monkeypatch):
    """`OSRM_BASE_URL=` (khai nhưng để rỗng) là trạng thái RẤT dễ có trong `.env`.
    Bản cũ của `os.environ.get(..., default)` trả chuỗi rỗng ⇒ URL thành `/route/v1/...`."""
    monkeypatch.setenv("OSRM_BASE_URL", "   ")
    urls = routing.osrm_endpoints(WP)
    assert any("router.project-osrm.org" in u for u in urls), (
        f"biến rỗng phải rơi về mặc định, không dựng URL què: {urls}")


def test_KHONG_mirror_nao_dung_ten_mien_SAI(monkeypatch):
    """Chặn tái phát lỗi (2): `project.osrm.org` (chấm) là tên miền KHÔNG hợp lệ cho OSRM."""
    monkeypatch.delenv("OSRM_BASE_URL", raising=False)
    xau = [u for u in routing.osrm_endpoints(WP) if re.search(r"project\.osrm", u)]
    assert not xau, (
        "mirror dùng `router.project.osrm.org` (dấu CHẤM) — TLS trả Hostname mismatch, "
        f"mirror này không bao giờ chạy được. Đúng phải là `router.project-osrm.org`: {xau}")


def test_khong_goi_HAI_LAN_cung_mot_server(monkeypatch):
    """Đặt biến trùng mirror mặc định ⇒ không được sinh 2 URL y hệt.

    ⚠ Soi độc lập 2026-08-03 chỉ ra bản đầu của test này **RỖNG**: nó chỉ assert
    `len(urls) == len(set(urls))`, mà mirror A (`openstreetmap.de/routed-car`) và mirror B (biến
    env) **không bao giờ** trùng chuỗi trong ca mặc định ⇒ xanh cả khi xoá `dict.fromkeys`. Nay
    kiểm đúng ca gây trùng: biến env = CHÍNH mirror A."""
    monkeypatch.setenv("OSRM_BASE_URL", routing.OSRM_DE_BASE_URL)
    urls = routing.osrm_endpoints(WP)
    assert len(urls) == 1, (
        f"biến env trùng mirror A mà vẫn sinh {len(urls)} URL ⇒ gọi 2 lần cùng server; khi server "
        f"đang rate-limit thì đó là tự làm mình chậm gấp đôi: {urls}")
    # đối chứng: ca mặc định phải có ĐÚNG 2 mirror khác nhau (không được "dedupe" quá tay)
    monkeypatch.delenv("OSRM_BASE_URL", raising=False)
    assert len(routing.osrm_endpoints(WP)) == 2


def _stub_urlopen(monkeypatch, host_tra_loi: str):
    """Giả `urlopen`: CHỈ host chỉ định trả 200, còn lại lỗi. Trả về list URL đã được gọi."""
    import json as _json
    da_goi: list[str] = []

    class _Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return _json.dumps({"routes": [{
                "distance": 2400.0, "duration": 300.0,
                "geometry": {"coordinates": [[105.823, 21.013], [105.834, 21.021]]},
                "legs": [{"steps": []}]}]}).encode()

    def _open(req, *a, **k):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        da_goi.append(url)
        if host_tra_loi in url:
            return _Resp()
        raise OSError("fixture: mirror nay loi")

    monkeypatch.setattr(routing.urllib.request, "urlopen", _open)
    return da_goi


def test_nhan_source_dung_MIRROR_NAO_THUC_SU_tra_loi(monkeypatch):
    """🔴 Bản đầu của test này chỉ **grep văn bản** file nguồn (`"project_osrm_real" in src`) — soi
    độc lập gọi đúng nó là *"cổng trang trí: thoả mãn được bằng một COMMENT"*. Nay gọi thật
    `try_osrm` với `urlopen` giả và kiểm nhãn ứng với mirror **thực sự trả lời**.

    Và làm vậy thì lộ luôn lỗi thứ hai mà grep không thể thấy: phép so
    `OSRM_DE_BASE_URL in osrm_url` là so CHUỖI CÓ SCHEME, nên đặt
    `OSRM_BASE_URL=https://routing.openstreetmap.de/routed-car` (https, không http) làm mirror B
    trỏ về **chính openstreetmap.de** mà nhãn lại nói `project_osrm_real` — nhãn khẳng định sai
    xuất xứ dữ liệu, đúng họ lỗi `hanoi_street_graph_engine` mà UPDATE-120 vừa dọn."""
    from app.models import RouteCalculateRequest, WaypointItem
    req = RouteCalculateRequest(waypoints=[
        WaypointItem(lat=21.0130, lng=105.8230, name="A"),
        WaypointItem(lat=21.0210, lng=105.8340, name="B")])

    # (a) mirror A trả lời ⇒ nhãn openstreetmap_de
    monkeypatch.delenv("OSRM_BASE_URL", raising=False)
    _stub_urlopen(monkeypatch, "routing.openstreetmap.de")
    assert routing.try_osrm(req).source == "openstreetmap_de_osrm_real"

    # (b) chỉ mirror B (project-osrm) trả lời ⇒ nhãn project_osrm_real
    _stub_urlopen(monkeypatch, "router.project-osrm.org")
    assert routing.try_osrm(req).source == "project_osrm_real"

    # (c) mirror B trỏ về openstreetmap.de bằng scheme KHÁC ⇒ nhãn KHÔNG được nói sai xuất xứ
    monkeypatch.setenv("OSRM_BASE_URL", "https://routing.openstreetmap.de/routed-car")
    _stub_urlopen(monkeypatch, "https://routing.openstreetmap.de")
    r = routing.try_osrm(req)
    assert r.source == "openstreetmap_de_osrm_real", (
        f"dữ liệu đến TỪ routing.openstreetmap.de nhưng nhãn nói {r.source!r} — nhãn khẳng định "
        f"sai xuất xứ, đúng họ lỗi `hanoi_street_graph_engine` mà UPDATE-120 vừa dọn")


def test_host_LA_thi_KHONG_khang_dinh_xuat_xu():
    """Self-host hoặc mirror khác ⇒ `osrm_custom_real`: vẫn khai *đây là OSRM thật* nhưng KHÔNG
    khẳng định của ai. Khẳng định sai xuất xứ tệ hơn không khẳng định."""
    assert routing._osrm_source("http://localhost:5000/route/v1/driving/x") == "osrm_custom_real"
    assert routing._osrm_source("https://ROUTING.OpenStreetMap.DE/routed-car/route/v1/x") \
        == "openstreetmap_de_osrm_real", "so host phải KHÔNG phân biệt chữ hoa/thường"
    assert routing._osrm_source("https://router.project-osrm.org/route/v1/x") \
        == "project_osrm_real"


def test_moi_waypoint_deu_vao_URL(monkeypatch):
    """Đối chứng: sửa cách dựng URL không được làm rơi waypoint (lỗi im lặng tệ nhất — vẫn ra
    một tuyến hợp lệ, chỉ là tuyến của ít điểm hơn)."""
    monkeypatch.delenv("OSRM_BASE_URL", raising=False)
    for u in routing.osrm_endpoints(WP):
        assert WP in u, u
        assert "geometries=geojson" in u and "steps=true" in u, u


# 🔴 `test_nhan_source_phan_biet_duoc_HAI_mirror` ĐÃ XOÁ (2026-08-03).
#
# Nó chỉ assert `"project_osrm_real" in <văn bản routing.py>` — một cổng **grep**. Soi độc lập
# 2026-08-03 đo được: chuỗi đó xuất hiện **3 lần** trong `routing.py`, trong đó **2 lần nằm trong
# DOCSTRING** của `_osrm_source` ⇒ xoá sạch nhãn khỏi CODE mà cổng vẫn XANH nhờ lời giải thích.
# Đúng bẫy #2 của repo: test khắc lời giải thích thành bằng chứng.
#
# ⚠ Và nó bắt được một chỗ tôi **KHAI QUÁ**: UPDATE-128 §7c ghi cổng này đã được *"viết lại: gọi
# thật `try_osrm` với `urlopen` giả"*. Sự thật là tôi **THÊM** `test_nhan_source_dung_MIRROR_NAO_
# THUC_SU_tra_loi` (ở trên) mà **để nguyên** cổng grep cũ — hai test cùng tên chủ đề, một cái thật
# một cái trang trí, và bản ghi nói như thể chỉ còn cái thật. Nay xoá hẳn cái cũ: giữ nó lại chỉ để
# "có thêm một test" là giữ một dòng luôn xanh, và làm loãng đúng thứ nó định canh.
