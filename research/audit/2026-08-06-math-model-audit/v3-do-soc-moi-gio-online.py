import sys; from pathlib import Path
ROOT = Path.cwd(); sys.path.insert(0, str(ROOT / "src"))
from gsm_sim.config import Config
from gsm_sim.entities import Actor
from gsm_sim.runner import run_once
cfg = Config.load(str(ROOT / "configs/pilot_dongda.yaml"))
tieu = {"tong": 0.0}
goc = Actor.consume_soc
def wrap(self, km, pct_per_km, *a, **k):
    tieu["tong"] += float(km) * float(pct_per_km)
    return goc(self, km, pct_per_km, *a, **k)
Actor.consume_soc = wrap
try:
    tong_online = 0.0; n=0
    for s in (1000,1001,1002):
        res = run_once(cfg, s)
        for a in res.actors:
            tong_online += float(getattr(a,"online_min",0.0))
        n += 1
finally:
    Actor.consume_soc = goc
gio = tong_online/60.0
print(f"3 seed: tong SOC tieu {tieu['tong']:.0f} pp · tong online {gio:.0f} gio")
print(f"=> DO DUOC: {tieu['tong']/gio:.2f} pp SOC moi GIO ONLINE")
print(f"   solver gia dinh: soc_bands=10 => 1 band = 10pp; soc_cost_per_bucket=1 band/30' => 20,00 pp/gio")
r = (tieu['tong']/gio)/20.0
print(f"   ty so DO/GIA-DINH = {r:.3f}  => solver {'UOC QUA CAO' if r<0.9 else ('UOC QUA THAP' if r>1.1 else 'KHOP (trong +-10%)')}")
