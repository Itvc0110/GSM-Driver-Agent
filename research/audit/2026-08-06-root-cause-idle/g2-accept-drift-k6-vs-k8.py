import sys, copy, statistics
from pathlib import Path
ROOT = Path.cwd(); sys.path.insert(0, str(ROOT / "src"))
from gsm_sim.config import Config
from gsm_sim.runner import run_once
base = Config.load(str(ROOT / "configs/pilot_dongda.yaml"))
acc_cfg = base.get("actors.archetypes", None)
def cfg_k(k):
    d = copy.deepcopy(base._data); d.setdefault("dispatcher", {})["candidate_ring_k_max"] = k
    return Config(d, base.root_dir)
def do(cfg):
    per = {}
    for s in (1000,1001,1002,1003,1004):
        res = run_once(cfg, s)
        for a in res.actors:
            arch = getattr(a, "archetype", None) or getattr(a, "arch", "?")
            off = float(getattr(a, "orders_offered", 0.0)); acc = float(getattr(a, "orders_accepted", 0.0))
            if off > 0: per.setdefault(str(arch), []).append(acc/off)
    return {k: statistics.mean(v) for k, v in sorted(per.items())}
r6, r8 = do(cfg_k(6)), do(cfg_k(8))
print(f"{'archetype':<12}{'accept k=6':>12}{'accept k=8':>12}{'lech':>10}")
mx = 0.0
for k in sorted(set(r6) | set(r8)):
    a, b = r6.get(k, float('nan')), r8.get(k, float('nan'))
    d = b - a; mx = max(mx, abs(d))
    print(f"{k:<12}{a:12.4f}{b:12.4f}{d:+10.4f}")
print(f"\nLECH LON NHAT |k=8 - k=6| = {mx:.4f} ({mx*100:.2f}dp)  · dung sai Q-07 = 5,00dp")
print("=> " + ("TRONG dung sai => Q-07 KHONG chan k=8" if mx < 0.05 else "VUOT dung sai => Q-07 chan that"))
