import sys; from pathlib import Path
ROOT = Path.cwd(); sys.path.insert(0, str(ROOT / "src"))
from gsm_sim.config import Config
from gsm_sim.geo import build_grid
from gsm_sim.runner import run_once
cfg = Config.load(str(ROOT / "configs/pilot_dongda.yaml"))
d = cfg.resolve_path("world.data_dir")
grid = build_grid(geom_path=d/cfg.get("world.geom_file"), stations_path=d/cfg.get("world.stations_file"),
                  poi_path=d/cfg.get("world.poi_file"), res=int(cfg.get("world.h3_res")),
                  res_report=int(cfg.get("world.h3_res_report")))
print("drop_demand_alpha =", cfg.get("demand.drop_demand_alpha", None))
tot_gen=out_gen=tot_done=out_done=0
for s in (1000,1001,1002,1003,1004):
    res = run_once(cfg, s)
    done = set()
    for e in res.events:
        if e.kind in ("trip_complete","order_complete","complete"):
            oid = (e.detail or {}).get("order_id")
            if oid is not None: done.add(oid)
    for o in res.orders:
        tot_gen += 1
        oc = not grid.is_core(o.drop_cell)
        out_gen += oc
        if o.order_id in done:
            tot_done += 1; out_done += oc
print(f"DON SINH   : drop ngoai loi {out_gen}/{tot_gen} = {out_gen/max(1,tot_gen):.1%}")
print(f"CUOC HOAN THANH: drop ngoai loi {out_done}/{tot_done} = {out_done/max(1,tot_done):.1%}  (n_done={tot_done/5:.0f}/ngay)")

# Bo sung: cuoc HOAN THANH do bang event 'trip_rated' (world.py:776, log tai order.drop_cell).
