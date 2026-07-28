"""ĐA-01 — MỘT estimator tỷ lệ dùng chung cho sim và UI (T-042 việc 3).

Vấn đề đang có (đo 2026-07-27, hồ sơ `08-parity-sim-vs-ui.md` §2 + BUG-DSIM13-02):

- **UI rò tương lai**: `adapters/advisor.build_gi` lấy `acceptance_rate` từ `driver_statistic_daily`
  của **chính ngày đó** — aggregate CẢ NGÀY. Ở 9h sáng, S1 đã biết tỷ lệ cuối ngày.
- **UI có fallback 1.0**: `stat.get("acceptance_rate", 1.0) or 1.0` — "hoàn hảo" ⇒ gate thưởng đi
  qua nhầm khi thiếu dữ liệu.
- **SIM thoái hoá 0/0 → 1.0** (`entities.acceptance_rate`), phải vá bằng `acc_est` ở bridge.
- **Ba quy ước cho một khái niệm**: property → 1.0 · `journey` → None · UI → aggregate ngày.

ĐA-01 (Cường duyệt 2026-07-27): shrinkage `(k + m·p0)/(n + m)`, prior pooled, **không fallback
1.0**. Test này ràng buộc TÍNH CHẤT toán học của estimator trước khi nối vào bất kỳ đường nào.
"""

from __future__ import annotations

import pytest

from gsm_core.rates import shrunk_rate

P0 = 0.8970          # prior pooled đo từ `driver_statistic_daily` (176082/196306)


def test_no_data_returns_prior_not_one():
    """0/0 KHÔNG được là 1.0 — đó là lỗi đã trả giá (BUG-DSIM13-02) và là fallback mà ĐA-01
    cấm. Không có bằng chứng ⇒ trả về NIỀM TIN TRƯỚC, không phải 'hoàn hảo'."""
    assert shrunk_rate(0, 0, P0, m=20) == pytest.approx(P0)
    assert shrunk_rate(0, 0, P0, m=20) != 1.0


def test_shrinks_toward_prior_when_few_observations():
    """1 offer bị từ chối (0/1) không được kéo ước lượng xuống 0.0 — mẫu quá nhỏ."""
    r = shrunk_rate(0, 1, P0, m=20)
    assert 0.0 < r < P0, "phải nằm giữa 0 và prior, lệch nhẹ khỏi prior"
    assert r > 0.8, f"1 quan sát không được lật ước lượng: {r}"


def test_converges_to_empirical_with_many_observations():
    """Nhiều dữ liệu ⇒ prior mờ dần, ước lượng bám số thật."""
    r = shrunk_rate(500, 1000, P0, m=20)
    assert r == pytest.approx(0.5, abs=0.02)


def test_monotonic_in_k_and_n():
    """Nhận thêm ⇒ tỷ lệ không giảm; bị chào thêm mà không nhận ⇒ tỷ lệ không tăng."""
    assert shrunk_rate(6, 10, P0, m=20) > shrunk_rate(5, 10, P0, m=20)
    assert shrunk_rate(5, 11, P0, m=20) < shrunk_rate(5, 10, P0, m=20)


def test_bounded_and_m_controls_strength():
    """Luôn trong [0,1]; m lớn = tin prior hơn (co mạnh hơn)."""
    for k, n in ((0, 0), (0, 5), (5, 5), (3, 7), (100, 100)):
        assert 0.0 <= shrunk_rate(k, n, P0, m=20) <= 1.0
    weak, strong = shrunk_rate(0, 10, P0, m=1), shrunk_rate(0, 10, P0, m=50)
    assert strong > weak, "m lớn hơn phải co MẠNH hơn về prior"


def test_rejects_impossible_counts():
    """k > n là dữ liệu hỏng — phải nổ, không được lặng lẽ trả số đẹp."""
    with pytest.raises(ValueError):
        shrunk_rate(11, 10, P0, m=20)
    with pytest.raises(ValueError):
        shrunk_rate(-1, 10, P0, m=20)


def test_prior_must_be_a_probability():
    with pytest.raises(ValueError):
        shrunk_rate(1, 2, 1.5, m=20)
