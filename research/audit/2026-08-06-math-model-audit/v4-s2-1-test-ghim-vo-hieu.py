import sys; from pathlib import Path
ROOT = Path.cwd(); sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
from gsm_core.policy import PolicyBundle
from gsm_core.solvers.shift_dp import solve, DEFAULT_PARAMS, _required_rest
from tests.test_shift_dp import POLICY_REC, _spi
pol = PolicyBundle.from_record(POLICY_REC)
print("DEFAULT_PARAMS bucket_min =", DEFAULT_PARAMS.get("bucket_min"), "| rest_min_per_4h =", DEFAULT_PARAMS.get("rest_min_per_4h"))
def show(tag, spi):
    r = solve(spi, pol); s = r["solution"]
    acts = [x["action"] for x in s["schedule"]]
    n_rest = sum(1 for a in acts if a == "REST")
    print(f"{tag:<34} delta={s['delta_payout']:+10.1f}  REST={n_rest}/{len(acts)}  acts={acts}")
# 1) DUNG fixture cua test ghim
show("fixture test (buckets=6)", _spi())
# 2) ca DAI hon => bat buoc co REST
for B in (8, 12, 14, 16, 20):
    show(f"buckets={B}", _spi(buckets=B, forecast=[3.0]*B))
# 3) R yeu cau la bao nhieu?
for B in (6, 12, 14, 20):
    print(f"   _required_rest(B={B}) =", _required_rest(B, DEFAULT_PARAMS, None, None))
