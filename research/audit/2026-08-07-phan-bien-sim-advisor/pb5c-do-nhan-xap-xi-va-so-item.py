# -*- coding: utf-8 -*-
import sys, json, collections
from pathlib import Path
ROOT = Path(r"C:\Users\Cuong\OneDrive - Hanoi University of Science and Technology\Documents\GitHub\My\GSM-Driver-Agent")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "ui" / "backend"))
from app.adapters import advisor
from app.adapters.mockdata import _table
from gsm_core.solvers import bonus_feasibility

pol = advisor.policy()
trips = _table("trips")
alld = sorted(trips["driver_id"].unique().to_list())
bike = [d for d in alld if d.startswith(("d-", "r-"))]
dates = sorted({s[:10] for s in trips["request_time"].to_list()})
SAMPLE_DATES = dates[7::12]
KIND_HOURS = {"brief": 9*60, "nudge": 14*60, "recap": 21*60+30}

meth = collections.Counter(); nitems_raw = collections.Counter(); nitems_out = collections.Counter()
src_gio = collections.Counter(); caveat_txt = collections.Counter()
n_hours_number = 0; n_hours_with_approx_label = 0
for did in bike:
    for date in SAMPLE_DATES:
        for kind, nm in KIND_HOURS.items():
            gi = advisor.build_gi(did, date, nm)
            meth[gi["historical_rate_method"]] += 1
            raw = advisor._advice_raw(did, date, nm)
            out = advisor.advice(did, date, nm)
            nitems_raw[len(raw["items"])] += 1
            nitems_out[len(out.get("items", []))] += 1
            for it in out.get("items", []):
                caveat_txt[it.get("caveat", "")] += 1
                for n in it.get("numbers", []):
                    if n["name"] == "gio_can_them":
                        n_hours_number += 1
                        src_gio[n["source"]] += 1
                        if "xấp xỉ" in it.get("caveat", "") or "ước lượng" in it.get("caveat", ""):
                            n_hours_with_approx_label += 1
print("historical_rate_method phan bo:", dict(meth))
print("so item TRUOC verifier:", dict(nitems_raw))
print("so item SAU  verifier:", dict(nitems_out))
print(f"the mang so 'gio_can_them': {n_hours_number}; trong do co nhan xap xi/uoc luong: "
      f"{n_hours_with_approx_label} = {n_hours_with_approx_label/max(1,n_hours_number)*100:.1f}%")
print("nguon ghi cho gio_can_them:", dict(src_gio))
print("\ncac chuoi caveat khac nhau:")
for t, c in caveat_txt.most_common():
    print(f"  x{c:5d} | {t}")
