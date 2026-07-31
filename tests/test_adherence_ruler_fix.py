"""SỬA THƯỚC adherence kênh VỊ TRÍ — UPDATE-113 (Cường duyệt 2026-07-31).

Vì sao phải sửa (đo được, không phải suy luận): `standby_followed` = coin-true **∧ thi hành
được**. Các ca coin-true-không-thi-hành là code path THẬT (pop im lặng khi actor đã đứng
đúng ô; bận tới hết ca; bản năng ≠ WAIT ở `wait_only`). Đếm chúng thành "không theo" làm
`decision_adherence` lệch null ~2,4đp — ở n=30 seed z=−2,39 (cổng không bắn) nhưng ở n=100
seed z=**−4,40** ⇒ cổng z Poisson-binomial TREO arm oracle, tức không arm nào được báo Δ.

Thước mới tách HAI câu hỏi:
- `followed` = kết cục COIN tại lúc gán (tài xế có NGHE không) — từ `coin_follow_ids`;
- `execution_rate` = executed/coin_true (nghe rồi có LÀM ĐƯỢC không) — chỉ tiêu RIÊNG.
"""
from __future__ import annotations

from gsm_core.lifecycle import projections as P
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with
from gsm_sim.runner import Config, run_once
from gsm_sim.sim_metrics import adherence_audit


def _alloc(t_min, cell, assigned, coin_true, run_id="r1"):
    class _E:
        pass
    e = _E()
    e.t_min, e.actor_id, e.kind, e.cell, e.run_id = t_min, -1, "standby_alloc", cell, run_id
    e.detail = {"n_assigned": len(assigned), "assigned_ids": sorted(assigned),
                "coin_follow_ids": sorted(coin_true),
                "decision_ids": {str(a): f"slth-{run_id}-{a}-positioning-{int(t_min // 30)}"
                                 for a in assigned}}
    return e


def _exec(t_min, aid, cell, did, run_id="r1"):
    class _E:
        pass
    e = _E()
    e.t_min, e.actor_id, e.kind, e.cell, e.run_id = t_min, aid, "standby_followed", cell, run_id
    e.detail = {"decision_id": did, "channel": "positioning", "to_cell": cell}
    return e


def test_coin_true_khong_thi_hanh_van_tinh_la_NGHE():
    """3 người được gán, 2 người coin-true, nhưng KHÔNG AI thi hành được (pop im lặng).

    Thước CŨ: followed = 0/3 = 0,0 — sai, vì hai người ĐÃ nghe lời.
    Thước MỚI: followed = 2/3 ≈ nominal, và `execution_rate` = 0/2 = 0,0 nói đúng chuyện
    "nghe rồi không làm được" ở CHỖ RIÊNG của nó."""
    events = [_alloc(300.0, "A", [1, 2, 3], [1, 2])]
    lc = P.sim_events_to_lifecycle(events)
    view = P.adherence_view(lc)
    tot_dec = sum(v["decided"] for v in view.values())
    tot_fol = sum(v["followed"] for v in view.values())
    assert (tot_dec, tot_fol) == (3, 2), (tot_dec, tot_fol)


def test_thi_hanh_khong_lam_phinh_tu_so():
    """Người đã thi hành KHÔNG được đếm hai lần: `standby_followed` nay là marker THI HÀNH,
    không map thành `followed` nữa (nếu map, tử số thành 3 trên mẫu số 3 = 100% giả)."""
    did = "slth-r1-1-positioning-10"
    events = [_alloc(300.0, "A", [1, 2, 3], [1, 2]), _exec(310.0, 1, "A", did)]
    view = P.adherence_view(P.sim_events_to_lifecycle(events))
    assert sum(v["followed"] for v in view.values()) == 2, "thi hành làm phình tử số"


def test_execution_rate_la_chi_tieu_RIENG_khong_vao_adherence():
    """`execution_rate` phải có mặt và KHÔNG được trộn vào adherence."""
    cfg = _cfg_with(Config.load("configs/pilot_dongda.yaml"), enabled=True, actor_id=None,
                    channels=CHANNEL_LADDER["positioning"], coverage="all")
    r = run_once(cfg, 5100)
    au = adherence_audit(r)
    ex = au["execution"]["positioning"]
    assert ex["coin_true_n"] > 0 and ex["executed_n"] > 0
    assert 0.0 < ex["execution_rate"] <= 1.0
    # thi hành KHÔNG bao giờ vượt số người đã nghe
    assert ex["executed_n"] <= ex["coin_true_n"], ex
    pos = au["by_channel"]["positioning"]
    assert pos["followed"] == ex["coin_true_n"], (
        "tử số adherence phải là kết cục COIN, không phải số lần thi hành")


def test_thuoc_moi_dua_adherence_ve_sat_nominal():
    """Trên run thật: thước mới phải cho `decision_adherence` sát adherence danh nghĩa của
    đội (bias coin-vs-execution ~2,4đp biến mất vì nó đã tách sang execution_rate)."""
    from gsm_sim.parallel import nominal_adherence
    base = Config.load("configs/pilot_dongda.yaml")
    cfg = _cfg_with(base, enabled=True, actor_id=None,
                    channels=CHANNEL_LADDER["positioning"], coverage="all")
    r = run_once(cfg, 5100)
    au = adherence_audit(r)
    nom = nominal_adherence(base)
    tot_d = tot_f = 0
    exp = 0.0
    for key, row in au["by_channel_archetype"].items():
        ch, _, arche = key.partition("|")
        if ch != "positioning" or arche not in nom:
            continue
        tot_d += row["decided"]
        tot_f += row["followed"]
        exp += nom[arche] * row["decided"]
    assert tot_d > 0
    lech = abs(tot_f / tot_d - exp / tot_d)
    assert lech < 0.05, (
        f"adherence đo {tot_f / tot_d:.3f} vs danh nghĩa {exp / tot_d:.3f} — lệch "
        f"{lech * 100:.1f}đp, thước vẫn còn bias (một seed nên tolerance rộng; cổng z "
        f"gộp 100 seed mới là phép kiểm thật)")
