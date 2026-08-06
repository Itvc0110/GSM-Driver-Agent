import sys, itertools; from pathlib import Path
ROOT = Path.cwd(); sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
from gsm_core.policy import PolicyBundle
from gsm_core.solvers.shift_dp import solve
from tests.test_shift_dp import POLICY_REC, _spi
pol = PolicyBundle.from_record(POLICY_REC)
am = []; n = 0
shapes = {"phang3": lambda B: [3.0]*B, "phang1.4": lambda B: [1.4]*B,
          "rang_cua": lambda B: [(1.0 if i%2 else 4.0) for i in range(B)],
          "giam": lambda B: [max(0.3, 4.0 - 0.25*i) for i in range(B)],
          "tang": lambda B: [0.3 + 0.25*i for i in range(B)]}
for B, pts, soc, (sn, sf), th in itertools.product(
        (6,10,12,14,16,20), (0,40,55,95,140,155,195), (30.0,60.0,95.0),
        shapes.items(), ("2026-07-01T06:00:00+07:00","2026-07-01T12:00:00+07:00","2026-07-01T17:00:00+07:00")):
    spi = _spi(buckets=B, points=pts, soc=soc, forecast=sf(B), t_now=th)
    d = solve(spi, pol)["solution"]["delta_payout"]; n += 1
    if d < -1e-6: am.append((B, pts, soc, sn, th[11:16], round(d,1)))
print(f"quet {n} cau hinh · so cau hinh co delta_payout < 0: {len(am)} = {len(am)/n:.2%}")
if am:
    am.sort(key=lambda x: x[-1])
    print("  te nhat 8:"); [print("   ", x) for x in am[:8]]
else:
    print("  => KHONG tai tao duoc delta<0 tren luoi nay (agent bao 4,0% tren luoi cua no)")
