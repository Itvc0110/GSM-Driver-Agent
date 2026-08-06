"""PB-04 (vong phan bien doc lap): tu tinh lai, khong tin so relay.

1) Tai lap HAI test GHIM trong tests/test_e1b_cong_thuc_kenh.py duoi 'ban sua' W_NOW.
2) Tu dem lai tren 88 luot NOI da ghi (pb04_out.txt) cac ty le W_END / W_NOW.
Chi DOC. Khong sua repo.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\Cuong\OneDrive - Hanoi University of Science and Technology\Documents\GitHub\My\GSM-Driver-Agent")
sys.path.insert(0, str(ROOT / "src"))

from gsm_sim.config import Config                     # noqa: E402
from gsm_sim.policy import PolicyBundle as SimPolicy   # noqa: E402
from gsm_core.policy import PolicyBundle as CorePolicy  # noqa: E402
from gsm_core.solvers import bonus_feasibility as bf   # noqa: E402

cfg = Config.load(ROOT / "configs" / "pilot_dongda.yaml")
sp = SimPolicy.from_config(cfg)
pol = CorePolicy.from_record(sp.to_core_record())
print("point_window", pol.point_window_hours, "peak", pol.point_peak_hours,
      "tiers", pol.day_bonus_tiers)

EXT = 60.0  # advice.shift_extend_max_min


def scenario(name, points, online_min, now_min, shift_end_min, fatigue_thr):
    gap = pol.next_tier_gap(points)
    gp = gap[0]
    rate = points / max(0.5, online_min / 60.0)
    need_flat = gp / rate * 60.0
    rem = max(0.0, shift_end_min - now_min)
    hour = int(now_min // 60) % 24
    hist = {("peak" if pol.is_peak(hour) else "offpeak"): round(rate, 3)}
    start = (now_min % 1440) / 60.0
    w = bf._walk(pol, hist, start, gp)
    h = w["hours_to_gap"]
    need_s1 = None if math.isinf(h) else h * 60.0
    print(f"\n--- {name} ---")
    print(f"  gap={gp} rate={rate:.3f}/h hist={hist} rem={rem:.0f}'")
    print(f"  need_FLAT={need_flat:.1f}'  need_S1_from_now="
          f"{'INF' if need_s1 is None else format(need_s1, '.1f')}'")
    for tag, need in (("FLAT", need_flat), ("S1_NOW", need_s1)):
        if need is None:
            print(f"  [{tag}] -> IM (khong dat trong ngay) => points_window_closed")
            continue
        if need <= rem:
            print(f"  [{tag}] -> reachable_in_shift (IM)")
            continue
        ne = need - rem
        proj = online_min + rem + ne * 1.15
        rail = proj > fatigue_thr
        print(f"  [{tag}] need_extra={ne:.1f}' proj={proj:.1f}' thr={fatigue_thr} "
              f"=> rail would_exceed_fatigue={'BAN' if rail else 'KHONG ban'}"
              + ("" if rail else f" ; cap_unreachable={ne > EXT}"))


# test_extend_khong_keo_khi_moc_dat_duoc_trong_ca
scenario("TEST-1 reachable_in_shift (now=01:00, ca ket 06:00)",
         points=55, online_min=60.0, now_min=60.0, shift_end_min=360.0,
         fatigue_thr=630.0)
# test_extend_rail_du_phong_cuoi_ca (bien ban knife-edge thr=1220)
scenario("TEST-2 rail would_exceed_fatigue (thr=1220, knife-edge)",
         points=35, online_min=700.0, now_min=700.0, shift_end_min=900.0,
         fatigue_thr=1220.0)

# ---------- tu dem lai tren 88 luot NOI ----------
rows = []
for line in (Path(sys.argv[0]).with_name("pb-04-raw-88-luot.txt")).read_text(
        encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if line.startswith("{") and '"add"' in line and '"now_h"' in line:
        rows.append(json.loads(line))
print(f"\n=== tu doc lai {len(rows)} luot NOI tu pb04_out.txt ===")
n = len(rows)
wend_ok = wnow_ok = wnow_inf = wend_inf = win_dead = 0
rail_flip = 0
for r in rows:
    rem = (r["shift_end_h"] - r["now_h"]) * 60.0
    if rem < 0:
        rem = 0.0
    if r["pts_possible_in_extend_from_shiftend"] <= 1e-9:
        win_dead += 1
    nfs = r["need_from_shiftend"]
    if nfs is None:
        wend_inf += 1
    elif nfs <= EXT + 1e-9:
        wend_ok += 1
    ns = r["need_s1_1bucket"]
    if ns is None:
        wnow_inf += 1
    elif ns > rem and (ns - rem) <= EXT + 1e-9:
        wnow_ok += 1
    # rail flip: S1 uoc IT hon flat >10% => need_extra nho hon => rail bot ban
    if ns is not None and r["need_flat"] > 0 and ns / r["need_flat"] < 0.9:
        rail_flip += 1
print(f"  cua so keo 100% ngoai khung diem : {win_dead}/{n} = {100*win_dead/n:.1f}%")
print(f"  W_END (ban sua NGUYEN VAN) con NOI: {wend_ok}/{n} = {100*wend_ok/n:.1f}%"
      f"   (vo nghiem/inf: {wend_inf}, huu han nhung > {EXT:.0f}': {n-wend_ok-wend_inf})")
print(f"  W_NOW (ban di tu now)      con NOI: {wnow_ok}/{n} = {100*wnow_ok/n:.1f}%"
      f"   (inf: {wnow_inf})")
print(f"  so luot S1 uoc need THAP hon flat >10% (=> ha rail met): {rail_flip}/{n}")
acc_bad = sum(1 for r in rows if not r["acc_ok"] or not r["comp_ok"])
print(f"  neu fix doc solution.feasible (co acc/comp): them {acc_bad}/{n} = "
      f"{100*acc_bad/n:.1f}% bi cam vi ty le duoi nguong")
same2 = sum(1 for r in rows if r["need_s1_2bucket_avg"] is not None
            and abs(r["need_s1_2bucket_avg"] - r["need_flat"]) < 0.5)
print(f"  duong MULTIDAY (hist=2 bucket day-avg): need_S1 == need_flat o {same2}/{n} luot"
      f" => fix KHONG sua duoc ve rate")
