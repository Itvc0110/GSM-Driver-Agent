"""Probe PB-04 vong 2: nhieu seed + chi tiet.
Them: acceptance/completion tai luot NOI (neu fix doc solution.feasible thi cai gi bi cam),
va so sanh S1 duoi HAI cach dung hist (1 bucket in-shift vs 2 bucket = memory day-average).
"""
import sys, math, json, collections
sys.path.insert(0, "src")

from gsm_sim.config import Config
from gsm_sim import runner
from gsm_sim.advice_bridge import AdviceActionBridge
from gsm_core.solvers import bonus_feasibility as bf

ROWS = []
_orig = AdviceActionBridge.check_shift_extend


def patched(self, actor, now_min, soc_threshold):
    pts = int(actor.points)
    online = actor.online_min
    shift_end = actor.shift_end_min
    gap = self.policy.next_tier_gap(pts)
    acc, comp = actor.acceptance_rate, actor.completion_rate
    res = _orig(self, actor, now_min, soc_threshold)
    add, why = res
    if why == "channel_off":
        return res
    if not (add and add > 0):
        ROWS.append({"add": 0.0, "why": why, "arc": actor.archetype})
        return res
    gp = int(gap[0])
    online_h = max(0.5, online / 60.0)
    rate = pts / online_h
    need_flat = gp / rate * 60.0
    gi = self.build_bonus_gap_input(actor, now_min)
    hist1 = gi["historical_points_per_hour"]
    hist2 = {"peak": rate, "offpeak": rate}        # gia lap duong multiday (memory)
    start_h = (now_min / 60.0) % 24.0
    out = {}
    for tag, h in (("h1", hist1), ("h2", hist2)):
        w = bf._walk(self.policy, h, start_h, gp)
        hh = w["hours_to_gap"]
        out["need_" + tag] = None if math.isinf(hh) else hh * 60.0
    se_h = (shift_end / 60.0) % 24.0 if shift_end < 1440 else 24.0
    w2 = bf._walk(self.policy, hist1, se_h, gp)
    ROWS.append({
        "add": add, "why": why, "arc": actor.archetype, "aid": actor.actor_id,
        "now_h": round(now_min / 60.0, 2), "shift_end_h": round(shift_end / 60.0, 2),
        "pts": pts, "gap": gp, "rate_flat": round(rate, 2),
        "need_flat": round(need_flat, 1),
        "need_s1_1bucket": out["need_h1"], "need_s1_2bucket_avg": out["need_h2"],
        "hist": dict(hist1),
        "pts_possible_in_extend_from_shiftend": round(bf._points_possible(
            w2["checkpoints"], self.extend_max_min / 60.0), 2),
        "need_from_shiftend": (None if math.isinf(w2["hours_to_gap"])
                               else round(w2["hours_to_gap"] * 60.0, 1)),
        "acc": round(acc, 3), "comp": round(comp, 3),
        "acc_ok": acc >= self.policy.bonus_min_acceptance,
        "comp_ok": comp >= self.policy.bonus_min_completion,
    }, )
    return res


AdviceActionBridge.check_shift_extend = patched
cfg = Config.load("configs/pilot_dongda.yaml")
d = cfg.data
d["advice"]["enabled"] = True
d["advice"]["coverage"] = "all"
d["advice"]["channels"]["shift_extend"] = True
seeds = [int(x) for x in sys.argv[1:]]
for s in seeds:
    runner.run_once(cfg, s)

spoke = [r for r in ROWS if r["add"] > 0]
print("seeds:", seeds, "| calls:", len(ROWS), "| NOI:", len(spoke))
print("reason all:", dict(collections.Counter(r["why"] for r in ROWS).most_common()))
print("arc NOI:", dict(collections.Counter(r["arc"] for r in spoke)))
print("shift_end gio NOI:", dict(sorted(collections.Counter(
    int(r["shift_end_h"]) for r in spoke).items())))
wc = [r for r in spoke if r["pts_possible_in_extend_from_shiftend"] <= 1e-9]
print("NOI ma cua so keo 100%% ngoai khung diem: %d/%d = %.1f%%"
      % (len(wc), len(spoke), 100.0 * len(wc) / max(1, len(spoke))))
print("  arc:", dict(collections.Counter(r["arc"] for r in wc)))
unreach = [r for r in spoke if r["need_s1_1bucket"] is None]
print("NOI ma walk-tu-now noi KHONG dat trong ngay: %d" % len(unreach))
same = [r for r in spoke if r["need_s1_1bucket"] is not None
        and abs(r["need_s1_1bucket"] - r["need_flat"]) < 0.5]
print("NOI ma need_S1(1bucket) == need_flat (±0.5'): %d/%d" % (len(same), len(spoke)))
same2 = [r for r in spoke if r["need_s1_2bucket_avg"] is not None
         and abs(r["need_s1_2bucket_avg"] - r["need_flat"]) < 0.5]
print("NOI ma need_S1(2bucket=day avg, duong multiday) == need_flat: %d/%d"
      % (len(same2), len(spoke)))
rat = sorted(r["need_s1_1bucket"] / r["need_flat"] for r in spoke
             if r["need_s1_1bucket"] is not None)
if rat:
    print("ratio need_S1/need_flat: n=%d min=%.3f p50=%.3f p90=%.3f max=%.3f"
          % (len(rat), rat[0], rat[len(rat) // 2], rat[int(0.9 * (len(rat) - 1))], rat[-1]))
    print("  so luot S1 UOC IT HON flat (ratio<0.99): %d ; NHIEU HON (>1.01): %d"
          % (sum(1 for x in rat if x < 0.99), sum(1 for x in rat if x > 1.01)))
bad_acc = [r for r in spoke if not r["acc_ok"] or not r["comp_ok"]]
print("NOI ma acceptance/completion DUOI nguong (=> solution.feasible False, se bi cam neu fix doc feasible): %d/%d"
      % (len(bad_acc), len(spoke)))
print("--- chi tiet luot NOI ---")
for r in spoke:
    print(json.dumps(r, ensure_ascii=False))
