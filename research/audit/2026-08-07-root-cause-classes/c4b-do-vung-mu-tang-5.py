"""C4b — ĐO vùng mù của tầng 5: khoá nào được định tuyến MỘT CHIỀU mà cổng KHÔNG soi?

Bối cảnh: `parallel._ONE_WAY_PREFIXES = ("veto_", "xveto_", "commit_")` đẩy ba họ khoá **ra khỏi**
bảng significance hai chiều, với lý lẽ chống Goodhart (`parallel.py:402-420`). Artifact in cạnh mỗi
khoá đó `"one_way_gate": "sim_metrics.health_guardrail_flags (D-M3-05)"`.

Câu hỏi: **cổng đó có thật sự soi chúng không?**

Phép đo (không đọc code mà suy — TIÊM và xem cổng có bắn):
  - với mỗi khoá k, dựng cặp (a, b) giống hệt nhau, rồi cho `b[k] = 0` (kịch bản "lan can SỤP VỀ 0")
  - cổng lành mạnh phải trả ≥1 flag; cổng im ⇒ khoá đó nằm ngoài tầm soi
  - song song: đọc `keys` của `aggregate_health_guardrail` để biết khoá nào vào được `a_mean`

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/c4b-do-vung-mu-tang-5.py
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))
# console Windows mặc định cp1252 ⇒ in tiếng Việt nổ UnicodeEncodeError (artifact JSON đã utf-8)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gsm_sim.parallel import _ONE_WAY_PREFIXES, aggregate_health_guardrail  # noqa: E402
from gsm_sim.sim_metrics import (EXTEND_RAILS, REST_RAILS,  # noqa: E402
                                 health_guardrail_flags)

OUT = pathlib.Path(__file__).with_suffix(".json")

# ⚠ CẬP NHẬT 2026-08-07 sau khi Cycle 4 thi công. Cổng THƯỜNG TRỰC nay là
# `tests/test_tang5_khong_co_vung_mu.py`; file này giữ lại làm HỒ SƠ tái tạo được của phép đo
# đã tìm ra vùng mù, và được cập nhật để không để lại một con số đã lỗi thời (đúng họ lỗi
# "bề mặt bằng chứng phân rã" mà Cycle 2 đi sửa).
#
# Khoá KHÔNG được soi riêng — ĐÚNG THIẾT KẾ, không phải vùng mù:
#   `*_calls_n` MẪU SỐ · `*_fired_n` TỔNG (cổng soi từng rail riêng)
#   `commit_made_n` kênh nói ít hơn ≠ suy giảm · `commit_broken_n` sụp về 0 là TỐT
#   `commit_cleared_n` nghỉ sớm tự nguyện ≠ suy giảm
# Soi bất kỳ khoá nào ở đây sẽ tạo **chiều khen**, đúng hướng Goodhart mà tầng 5 chặn.
KHONG_PHAI_LAN_CAN = {"veto_calls_n", "veto_fired_n", "xveto_calls_n", "xveto_fired_n",
                      "commit_made_n", "commit_broken_n", "commit_cleared_n"}


def khoa_mot_chieu() -> set[str]:
    """Mọi khoá tầng 5 mà `_ONE_WAY_PREFIXES` sẽ tóm — dựng từ CHÍNH các hằng rail."""
    ks = {f"veto_{r}_n" for r in REST_RAILS} | {"veto_calls_n", "veto_fired_n"}
    ks |= {f"xveto_{r}_n" for r in EXTEND_RAILS} | {"xveto_calls_n", "xveto_fired_n"}
    ks |= {"commit_made_n", "commit_kept_n", "commit_broken_n", "commit_cleared_n"}
    return {k for k in ks if k.startswith(_ONE_WAY_PREFIXES)}


def vao_a_mean() -> set[str]:
    """Khoá nào thực sự vào `a_mean`.

    ⚠ Bản đầu đọc danh sách `keys` bằng **regex trên source** — và nó vỡ ngay khi Cycle 4 đổi
    danh sách từ chép-tay sang SUY-RA-từ-hằng (regex khớp nhầm, báo 10 khoá vắng). Nay **gọi
    hàm thật** trên một cặp stub: đo cái hàm LÀM, không đo cái nó TRÔNG NHƯ."""
    class _Pair:
        pass

    p = _Pair()
    p.system_a = {**{k: 1.0 for k in khoa_mot_chieu()}, "rest_min_total": 10.0}
    p.system_b = dict(p.system_a)
    return set(aggregate_health_guardrail([p])["a_mean"])


def cong_co_soi(k: str, moi: set[str]) -> bool:
    """TIÊM: b[k] sụp về 0 so với a. Cổng lành mạnh phải tố giác."""
    a = {kk: 50.0 for kk in moi}
    a.update({"rest_min_total": 1000.0, "work_span_p90": 100.0, "drive_min_p90": 100.0,
              "commit_made_n": 100.0, "commit_kept_n": 40.0,
              "commit_broken_n": 30.0, "commit_cleared_n": 20.0})  # bao toan OK
    b = dict(a)
    b[k] = 0.0
    return len(health_guardrail_flags(a, b)) > 0


def main() -> None:
    moi = khoa_mot_chieu()
    trong_a_mean = vao_a_mean()
    rows, mu_gop, mu_cong, mu_that = [], [], [], []
    for k in sorted(moi):
        o_gop, o_cong = k in trong_a_mean, cong_co_soi(k, moi)
        rows.append({"khoa": k, "vao_a_mean": o_gop, "cong_soi": o_cong,
                     "la_lan_can": k not in KHONG_PHAI_LAN_CAN})
        if not o_gop:
            mu_gop.append(k)
        if not o_cong:
            mu_cong.append(k)
            if k not in KHONG_PHAI_LAN_CAN:
                mu_that.append(k)
        print(f"  {k:32s} vào a_mean={'CÓ ' if o_gop else 'KHÔNG'}   "
              f"cổng soi={'CÓ ' if o_cong else 'KHÔNG'}")

    print(f"\n=> KHÔNG vào a_mean        : {len(mu_gop):2d} khoá")
    print(f"=> cổng KHÔNG soi (thô)    : {len(mu_cong):2d} khoá")
    print(f"=> ⭐ VÙNG MÙ THẬT         : {len(mu_that):2d} khoá  "
          f"(đã trừ mẫu số/tổng — chúng không soi là ĐÚNG THIẾT KẾ)")
    for k in mu_that:
        print(f"     · {k}")

    OUT.write_text(json.dumps({
        "cau_hoi": "khoa nao duoc dinh tuyen MOT CHIEU ma cong health_guardrail_flags KHONG soi?",
        "phep_do": "tiem b[k]=0 (rail SUP VE 0) roi xem cong co bắn flag khong",
        "one_way_prefixes": list(_ONE_WAY_PREFIXES),
        "rows": rows,
        "khong_vao_a_mean": mu_gop,
        "cong_khong_soi_tho": mu_cong,
        "vung_mu_that": mu_that,
        "ghi_chu": ("veto_calls_n/veto_fired_n (va ban xveto_) la MAU SO va TONG, khong phai lan can "
                    "— cong soi tung rail rieng nen khong soi chung la DUNG THIET KE"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
