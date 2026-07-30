"""Probe: adherence THẬT của từng kênh, đo từ COIN chứ không từ event log.

Vì sao cần: `decision_adherence` hiện đọc từ event log, mà event log của
`shift_extend` và `rest_window` chỉ ghi khi tài xế ĐÃ THEO (`D-M3-01`) ⇒ con số
tính ra là 1,0 theo cấu trúc. Muốn biết sự thật thì phải đo ở nguồn: mỗi lần
`coin_follows` được gọi là một lần advisor NÓI; giá trị nó trả về là tài xế có
nghe theo hay không. Đó là ground truth ĐỘC LẬP với event log.

Ba con số đang đá nhau về adherence thật của `shift_extend` (agent soi đưa
0,26-0,38; agent khác đưa ~50%; danh nghĩa theo archetype ~0,59-0,68) — probe này
để chốt, vì repo đã hai lần sập bẫy "cơ chế đúng, độ lớn sai" (sai 5,7x và 5,4x).

Đồng thời kiểm claim `L1-02`: bậc thang `rest_window` có BIT-IDENTICAL với
`s2_only` không (nếu kênh hoàn toàn bất động thì phải identical). Dùng fingerprint
PER-ACTOR, KHÔNG dùng `parallel.assert_crn` — `assert_crn` chỉ so danh sách đơn
sinh NGOÀI world nên nó trả True dù mọi quỹ đạo actor đã lệch (`D-M3-02`).

    uv run python scripts/probe_adherence_truth.py [--seeds 1000 1001 1002]

Mọi số là MOCK (`configs/pilot_dongda.yaml`), không phải số thật GSM.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json

from gsm_sim import advice_bridge as AB
from gsm_sim.parallel import CHANNEL_LADDER, _cfg_with, run_once
from gsm_sim.runner import Config

CONFIG = "configs/pilot_dongda.yaml"
DEFAULT_SEEDS = (1000, 1001, 1002)

# Event sim nào là "advisor đã nói" của kênh nào — để so con số ĐÃ BÁO với sự thật.
KIND_OF_CHANNEL = {
    "shift_plan": "advice_given",
    "accept_lift": "advice_bonus_gate",
    "shift_extend": "advice_shift_extend",
    "rest_window": "advice_rest_window",
}


def fingerprint_actors(result) -> str:
    """Digest PER-ACTOR của quỹ đạo + tiền + nghỉ.

    Thay `assert_crn`: nó chỉ so `(order_id, t_min, pickup_cell, gross_vnd)` của đơn,
    mà đơn sinh ngoài world ⇒ trả True dù actor lệch hết. Cái này bắt được nhiễm stream.
    """
    segs: dict[int, list] = collections.defaultdict(list)
    for s in result.segments:
        segs[s["actor_id"]].append((s["kind"], round(float(s["t0"]), 3), round(float(s["t1"]), 3)))
    rows = []
    for a in sorted(result.actors, key=lambda x: x.actor_id):
        rows.append((a.actor_id, sorted(segs.get(a.actor_id, [])),
                     round(float(a.payout_vnd), 6), int(a.trips_done),
                     round(float(a.rest_min), 6)))
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]


def probe_coins(base: Config, seeds) -> tuple[dict, dict]:
    """Đếm coin theo kênh (ground truth) + đếm event theo kênh (con số đã báo)."""
    coins: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    events: collections.Counter = collections.Counter()

    orig = AB.AdviceActionBridge.coin_follows
    orig_claim = AB.AdviceActionBridge._claim_effect

    def spy(self, actor, topic, now_min, material_revision, bucket_min=None):
        out = orig(self, actor, topic, now_min, material_revision, bucket_min)
        coins[topic]["theo" if out else "khong_theo"] += 1
        return out

    def spy_claim(self, actor, topic, now_min, bucket_min=None):
        out = orig_claim(self, actor, topic, now_min, bucket_min)
        # `claim_moi` = quyết định LẦN ĐẦU được áp tác động (dedup đúng);
        # `claim_lap` = hỏi lại cùng quyết định trong cùng bucket (bị chặn — đúng).
        coins[topic]["claim_moi" if out else "claim_lap"] += 1
        return out

    AB.AdviceActionBridge.coin_follows = spy
    AB.AdviceActionBridge._claim_effect = spy_claim
    try:
        cfg = _cfg_with(base, enabled=True, actor_id=None,
                        channels=CHANNEL_LADDER["all"], coverage="all")
        for s in seeds:
            r = run_once(cfg, s)
            for e in r.events:
                events[e.kind] += 1
    finally:
        AB.AdviceActionBridge.coin_follows = orig
        AB.AdviceActionBridge._claim_effect = orig_claim
    return coins, events


def probe_bit_identical(base: Config, seeds) -> list[tuple[int, str, str, bool]]:
    """L1-02: bậc thang `rest_window` có bit-identical với `s2_only` không?"""
    out = []
    for s in seeds:
        a = run_once(_cfg_with(base, enabled=True, actor_id=None,
                               channels=CHANNEL_LADDER["s2_only"], coverage="all"), s)
        b = run_once(_cfg_with(base, enabled=True, actor_id=None,
                               channels=CHANNEL_LADDER["rest_window"], coverage="all"), s)
        fa, fb = fingerprint_actors(a), fingerprint_actors(b)
        out.append((s, fa, fb, fa == fb))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    ap.add_argument("--skip-identical", action="store_true")
    args = ap.parse_args()

    base = Config.load(CONFIG)
    print(f"MOCK · {CONFIG} · seeds={args.seeds} · coverage=all · ladder=all\n")

    coins, events = probe_coins(base, args.seeds)
    nominal = AB.DEFAULT_ADHERENCE

    print("=== ADHERENCE THẬT, đo từ COIN (ground truth độc lập với event log) ===")
    print(f"{'kênh':<14}{'nói':>7}{'theo':>7}{'thật':>9}   {'event đã ghi':>13}{'báo cáo':>9}")
    for ch in ("shift_plan", "positioning", "accept_lift", "shift_extend", "rest_window"):
        c = coins.get(ch)
        if not c:
            print(f"{ch:<14}{'—':>7}{'—':>7}{'KHÔNG RÚT COIN':>9}")
            continue
        noi = c["theo"] + c["khong_theo"]
        thuc = c["theo"] / noi if noi else float("nan")
        kind = KIND_OF_CHANNEL.get(ch)
        n_ev = events.get(kind, 0) if kind else 0
        bao = (c["theo"] / n_ev) if n_ev else float("nan")
        print(f"{ch:<14}{noi:>7}{c['theo']:>7}{thuc:>9.3f}   {n_ev:>13}{bao:>9.3f}")

    print("\n=== 'nghe theo' rồi thì tác động có được ÁP không? (tách dedup vs MẤT) ===")
    print(f"{'kênh':<14}{'theo':>7}{'claim đầu':>11}{'claim chặn':>12}{'event':>8}{'HỤT':>6}")
    for ch in ("shift_plan", "positioning", "accept_lift", "shift_extend", "rest_window"):
        c = coins.get(ch)
        if not c or not (c["claim_moi"] or c["claim_lap"]):
            continue
        kind = KIND_OF_CHANNEL.get(ch)
        n_ev = events.get(kind, 0) if kind else 0
        print(f"{ch:<14}{c['theo']:>7}{c['claim_moi']:>11}{c['claim_lap']:>12}"
              f"{n_ev:>8}{c['claim_moi'] - n_ev:>6}")
    print("  → 'claim chặn' = hỏi lại CÙNG quyết định trong cùng bucket ⇒ chặn là ĐÚNG (R-01).")
    print("  → HỤT > 0 = quyết định đã TIÊU token _claim_effect mà KHÔNG có event ⇒ lời khuyên")
    print("    bất khả thi bị clamp SAU khi đã claim (L1-04) ⇒ quyết định mất hẳn.")

    print(f"\ndanh nghĩa theo archetype: {dict(sorted(nominal.items()))}")
    print("  → 'thật' = theo/nói (từ coin). 'báo cáo' = theo/số event đã ghi.")
    print("  → kênh nào 'báo cáo' = 1,000 mà 'thật' < 1,000 là kênh có MẪU SỐ HỎNG.")

    if not args.skip_identical:
        print("\n=== L1-02: bậc thang 'rest_window' có bit-identical với 's2_only'? ===")
        for s, fa, fb, same in probe_bit_identical(base, args.seeds):
            print(f"  seed {s}: s2_only={fa}  rest_window={fb}  {'IDENTICAL' if same else 'KHÁC'}")
        print("  (fingerprint PER-ACTOR: segments + payout + trips + rest_min;"
              " KHÔNG dùng assert_crn)")


if __name__ == "__main__":
    main()
