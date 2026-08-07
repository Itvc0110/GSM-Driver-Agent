# -*- coding: utf-8 -*-
"""pb5 vong 2 — (i) cham 3 luat tren TEXT MAT THE dung logic cards.js;
(ii) duong v2 (checkpoint) voi tai xe KHONG-bike; (iii) dong hanh cua cliff."""
import sys, json, collections, statistics
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
nonbike = [d for d in alld if not d.startswith(("d-", "r-"))]
dates = sorted({s[:10] for s in trips["request_time"].to_list()})
SAMPLE_DATES = dates[7::12]
KIND_HOURS = {"brief": 9 * 60, "nudge": 14 * 60, "recap": 21 * 60 + 30}
HEDGE = ["ước", "không đảm bảo", "phụ thuộc", "có thể", "khoảng", "chưa",
         "không chắc", "nguy cơ", "khó khả thi", "sát biên", "không phải cam kết", "đừng cố"]

# ---------- (i) mat the theo cards.js ----------
def face_text(kind, it):
    """Tai lap dung `ui/web/js/cards.js`: brief/_render(title,message);
    nudge/_render(title, shortMsg); recap/_render('Tong ket ca hom nay', msg ghep client)."""
    if kind == "brief":
        return it["title"], it["message"]
    if kind == "nudge":
        fn = (it.get("numbers") or [None])[0]
        short = (f"{fn['name'].replace('_',' ')}: "
                 f"{('%s' % fn['value'])+' '+(fn.get('unit') or '')}") if fn else \
                it["message"].split(".")[0] + "."
        return it["title"], short
    # recap: title CUNG la 'Tong ket ca hom nay', message do CLIENT ghep tu driver_state
    return "Tổng kết ca hôm nay", ("Payout hôm nay <payout_vnd> (cuốc <trip_payout_vnd>) · "
                                   f"<n> cuốc. {it['title']} — mở \"Vì sao\" để xem chi tiết.")

stat = collections.Counter()
per_kind = collections.defaultdict(collections.Counter)
cliff_alone = 0; cliff_with_feasible = 0; cliff_cases = []
tot_cards = 0
for did in bike:
    for date in SAMPLE_DATES:
        for kind, nm in KIND_HOURS.items():
            raw = advisor._advice_raw(did, date, nm)
            out = advisor.advice(did, date, nm)
            rawcodes = [i["reason_code"] for i in raw["items"]]
            if "acceptance_near_threshold" in rawcodes:
                if "feasible_gap" in rawcodes:
                    cliff_with_feasible += 1
                    if len(cliff_cases) < 3:
                        gi = advisor.build_gi(did, date, nm)
                        cliff_cases.append({"d": did, "date": date, "nm": nm,
                                            "acc": gi["acceptance_rate"],
                                            "title": raw["items"][0]["title"],
                                            "msg": raw["items"][0]["message"],
                                            "cliff_msg": [i for i in raw["items"]
                                                          if i["reason_code"] ==
                                                          "acceptance_near_threshold"][0]["message"]})
                else:
                    cliff_alone += 1
            for it in out.get("items", []):
                tot_cards += 1
                t, m = face_text(kind, it)
                face = (t + " " + m).lower()
                hedged = any(h in face for h in HEDGE)
                money = "đ" in t or "đ" in m or any(n.get("unit") == "vnd"
                                                    for n in it.get("numbers", []))
                per_kind[kind]["n"] += 1
                if not hedged:
                    stat["L3_mat_the_KHONG_neu_bat_dinh"] += 1
                    per_kind[kind]["no_hedge"] += 1
                if money:
                    stat["L1_the_co_so_TIEN"] += 1
                    per_kind[kind]["money"] += 1
                    # co nhan gross/payout/net khong?
                    if not any(k in face for k in ["gross", "payout", "net",
                                                   "doanh thu", "thực nhận"]):
                        stat["L1_tien_KHONG_phan_loai"] += 1
                        per_kind[kind]["money_unlabeled"] += 1
print(f"tong the ve ra man = {tot_cards}")
for k, v in stat.most_common():
    print(f"  {k:36s} {v:5d} = {v/tot_cards*100:5.1f}%")
print("\n theo be mat:")
for k, c in per_kind.items():
    n = c["n"]
    print(f"  {k:6s} n={n:5d}  khong_hedge={c['no_hedge']:5d} ({c['no_hedge']/n*100:5.1f}%)"
          f"  tien_khong_phan_loai={c['money_unlabeled']:5d} ({c['money_unlabeled']/n*100:5.1f}%)")

print(f"\n== cliff di kem cai gi ==\n  cung the FEASIBLE ('con voi duoc moc thuong'): {cliff_with_feasible}"
      f"\n  cung the infeasible                          : {cliff_alone}")
for c in cliff_cases:
    print(f"   VD {c['d']} {c['date']} {c['nm']}' acc={c['acc']}")
    print(f"      TAI XE THAY : {c['title']} | {c['msg']}")
    print(f"      BI VUT      : {c['cliff_msg']}")

# ---------- (ii) duong v2: co cong doi bike khong? ----------
print("\n== duong v2 `ProductSolverOrchestrator.solve` voi tai xe KHONG-bike ==")
from app.services.advice_checkpoint import ProductSolverOrchestrator
orch = ProductSolverOrchestrator()
bad = []
for did in nonbike[:12]:
    t_now = f"{SAMPLE_DATES[3]}T14:00:00+07:00"
    try:
        res = orch.solve(did, t_now, 6 * 60, 22 * 60, surface="nudge")
    except Exception as e:
        print("  ERR", did, type(e).__name__, e); continue
    for c in res.candidates:
        if c.get("solver") == "S1" or "s1-" in json.dumps(c)[:200]:
            pass
    bad.append((did, [c.get("solver") for c in res.candidates], res.reasons))
for b in bad[:6]:
    print("  ", b)
# so sanh: v1 chan, v2 khong
v1 = advisor.advice(nonbike[0], SAMPLE_DATES[3], 14 * 60)
print("  v1 cho", nonbike[0], "->", v1["silent"])
gi = advisor.build_gi(nonbike[0], SAMPLE_DATES[3], 14 * 60)
rep = bonus_feasibility.solve(gi, pol)
print("  build_gi truc tiep (duong v2 dung):", {k: gi[k] for k in
      ("points_now", "next_tiers", "acceptance_rate", "completion_rate")})
print("  -> solution:", json.dumps(rep["solution"], ensure_ascii=False))
print("  -> digest  :", rep["problem_digest"])
n_nonbike_with_card = 0
for did in nonbike:
    for date in SAMPLE_DATES[:3]:
        g = advisor.build_gi(did, date, 14 * 60)
        r = bonus_feasibility.solve(g, pol)
        if r["solution"].get("tier_vnd"):
            n_nonbike_with_card += 1
print(f"  luot (40 tai xe car/premium x 3 ngay) sinh ra mot con so THUONG BIKE:"
      f" {n_nonbike_with_card}/{len(nonbike)*3}")
