"""D-L4-M1 — sổ lan can nghỉ có mang thông tin về KÊNH không?

Agent `L4` báo: arm `advice.enabled=False` **vẫn** sinh 125/107/118 event `advice_rest_veto`,
và bật kênh cũng ra **đúng 125** (seed 5000) ⇒ `veto_*` là hàm của THẾ GIỚI, không của ADVICE.

Nếu đúng thì nhánh *"lan can SỤP VỀ 0"* của tầng 5 (`health_guardrail_flags` (i)) **chưa từng đo
được cái nó tưởng đang đo** — vì advice không thể làm rail ngừng bắn, rail bắn trước cổng kênh.

⚠ Đây là số agent báo, TÔI CHƯA TỰ KIỂM. Probe này để tôi tự đo.

Cấu trúc nghi phạm (đọc code, chưa đo):
  `should_defer_rest` (`advice_bridge.py`) kiểm 4 lan can **TRƯỚC** khi hỏi `rest_window_hour`
  — mà `rest_window_hour` mới là chỗ kiểm `self.ch_rest_window`. Và `world.py:1066` log MỌI
  kết cục không-defer, không lọc theo kênh.

Chạy:  uv run python research/audit/2026-08-07-root-cause-classes/m1-so-lan-can-co-mang-tin-ve-kenh-khong.py
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml  # noqa: E402

from gsm_sim.config import Config  # noqa: E402
from gsm_sim.runner import run_once  # noqa: E402
from gsm_sim.sim_metrics import REST_RAILS, rest_rails_audit  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).with_suffix(".json")
SEEDS = [5000, 5001, 5002]


def _cfg(**over) -> Config:
    data = copy.deepcopy(yaml.safe_load(
        (ROOT / "configs/pilot_dongda.yaml").read_text(encoding="utf-8")))
    adv = data.setdefault("advice", {})
    adv["enabled"] = over.get("enabled", False)
    adv["coverage"] = "all"
    adv.setdefault("channels", {})["rest_window"] = over.get("rest_window", False)
    return Config(data, ROOT)


def main() -> None:
    rows = []
    print(f"{'seed':>6} {'arm':<22} " + " ".join(f"{'veto_'+r:>18}" for r in REST_RAILS)
          + f" {'calls':>8} {'fired':>8}")
    for seed in SEEDS:
        for ten, kw in (("A: advice TẮT hẳn", {"enabled": False}),
                        ("B: rest_window BẬT", {"enabled": True, "rest_window": True})):
            au = rest_rails_audit(run_once(_cfg(**kw), seed))
            rows.append({"seed": seed, "arm": ten, **{k: au.get(k) for k in au
                                                      if k.startswith(("veto_", "commit_"))}})
            print(f"{seed:>6} {ten:<22} "
                  + " ".join(f"{au.get('veto_'+r, 0):>18}" for r in REST_RAILS)
                  + f" {au.get('veto_calls_n', 0):>8} {au.get('veto_fired_n', 0):>8}")

    print("\n=== PHÁN QUYẾT ===")
    dong_nhat, khac = [], []
    for i in range(0, len(rows), 2):
        a, b = rows[i], rows[i + 1]
        d = {k: (b.get(k, 0) - a.get(k, 0)) for k in a if k.startswith("veto_")}
        (dong_nhat if all(v == 0 for v in d.values()) else khac).append((a["seed"], d))
    for s, d in dong_nhat:
        print(f"  seed {s}: MỌI khoá veto_* GIỐNG HỆT giữa hai arm ⇒ sổ không mang tin về kênh")
    for s, d in khac:
        nz = {k: v for k, v in d.items() if v}
        print(f"  seed {s}: có khác — {nz}")
    print(f"\n  {len(dong_nhat)}/{len(SEEDS)} seed GIỐNG HỆT")
    print("  ⇒ nếu đa số giống hệt: nhánh 'lan can SỤP VỀ 0' của tầng 5 KHÔNG thể bắn, vì "
          "advice không làm rail ngừng bắn — rail bắn TRƯỚC cổng kênh.")

    OUT.write_text(json.dumps({
        "cau_hoi": "so lan can nghi co mang thong tin ve KENH khong?",
        "seeds": SEEDS, "rows": rows,
        "n_seed_giong_het": len(dong_nhat), "n_seed_khac": len(khac),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nartifact → {OUT}")


if __name__ == "__main__":
    main()
