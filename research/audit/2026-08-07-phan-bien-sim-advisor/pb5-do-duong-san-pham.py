# -*- coding: utf-8 -*-
"""pb5 — DO duong san pham S1 + card. Chi DO, khong sua gi.

Mau so: CHI tai xe BIKE (d-*, r-*) — dung tap ma `advisor.py::_advice_raw` cho di qua cua
(`driver_id.startswith(("d-","r-"))`). Tranh bay M5 (mau so nhiem car/premium).
Gio hoi: DUNG BA moc client that goi (`ui/web/js/cards.js` KIND_HOURS = 9:00 / 14:00 / 21:30).
"""
import sys, json, re, collections
from pathlib import Path
ROOT = Path(r"C:\Users\Cuong\OneDrive - Hanoi University of Science and Technology\Documents\GitHub\My\GSM-Driver-Agent")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "ui" / "backend"))
import polars as pl
from app.adapters import advisor
from app.adapters.mockdata import _table
from gsm_core.solvers import bonus_feasibility
from gsm_core.advisor import verifier as V
from gsm_core.vn_format import render_number_vn

pol = advisor.policy()
trips = _table("trips")
all_drivers = sorted(trips["driver_id"].unique().to_list())
bike = [d for d in all_drivers if d.startswith(("d-", "r-"))]
nonbike = [d for d in all_drivers if not d.startswith(("d-", "r-"))]
dates = sorted({s[:10] for s in trips["request_time"].to_list()})

KIND_HOURS = {"brief": 9 * 60, "nudge": 14 * 60, "recap": 21 * 60 + 30}
SAMPLE_DATES = dates[7::12]          # 7 ngay rai deu, bo tuan dau (thieu lich su)
print("N bike =", len(bike), "| N non-bike =", len(nonbike))
print("dates =", SAMPLE_DATES)

HEDGE = ["ước", "uoc tinh", "không đảm bảo", "phụ thuộc", "có thể", "khoảng",
         "chưa", "không chắc", "nguy cơ", "khó khả thi", "sát biên", "không phải cam kết"]
MONEY_KIND = ["gross", "payout", "net", "doanh thu", "thực nhận", "trước phí", "sau phí"]

rows = []
for did in bike:
    for date in SAMPLE_DATES:
        for kind, nm in KIND_HOURS.items():
            raw = advisor._advice_raw(did, date, nm)
            out = advisor.advice(did, date, nm)
            gi = None; rep = None
            try:
                gi = advisor.build_gi(did, date, nm)
                rep = bonus_feasibility.solve(gi, pol)
            except Exception as e:
                pass
            rows.append({"driver": did, "date": date, "kind": kind, "now_min": nm,
                         "raw": raw, "out": out, "gi": gi, "rep": rep})

print("tong luot goi =", len(rows))

# ---------------- 1. phan bo nhanh ----------------
cnt = collections.Counter()
for r in rows:
    o = r["out"]
    if o["silent"]["is_silent"]:
        cnt["SILENT:" + o["silent"]["reason_code"]] += 1
    else:
        for it in o["items"]:
            cnt["ITEM:" + it["reason_code"]] += 1
print("\n== phan bo nhanh (sau verifier) ==")
for k, v in cnt.most_common():
    print(f"  {k:42s} {v:6d}  {v/len(rows)*100:5.2f}%")

# ---------------- 2. cliff item: sinh ra bao nhieu, song sot bao nhieu ----------------
n_cliff_raw = 0; n_cliff_kept = 0; n_cliff_rendered = 0
cliff_examples = []
for r in rows:
    craw = [it for it in r["raw"]["items"] if it["reason_code"] == "acceptance_near_threshold"]
    ckept = [it for it in r["out"].get("items", []) if it["reason_code"] == "acceptance_near_threshold"]
    n_cliff_raw += len(craw); n_cliff_kept += len(ckept)
    # client (cards.js brief/nudge/recap) CHI ve items[0]
    if r["out"].get("items") and r["out"]["items"][0]["reason_code"] == "acceptance_near_threshold":
        n_cliff_rendered += 1
    if craw and len(cliff_examples) < 3:
        cliff_examples.append({"driver": r["driver"], "date": r["date"], "now_min": r["now_min"],
                               "item": craw[0], "verify_errors": advisor._verify_item(craw[0])})
print(f"\n== E3.1 acceptance_cliff ==\n  sinh boi solver+adapter (truoc verifier): {n_cliff_raw}"
      f"\n  song sot sau verifier            : {n_cliff_kept}"
      f"\n  duoc client ve (items[0])        : {n_cliff_rendered}")
for e in cliff_examples:
    print("   VD:", e["driver"], e["date"], e["now_min"], "|", e["item"]["message"][:90])
    print("       verify_errors =", e["verify_errors"])

# ---------------- 3. tier_vnd = TONG hay BIEN? ----------------
over = []
for r in rows:
    for it in r["out"].get("items", []):
        if it["reason_code"] != "feasible_gap":
            continue
        gi = r["gi"]; sol = r["rep"]["solution"]
        locked = pol.bonus_at(int(gi["points_now"]))
        shown = sol["tier_vnd"]
        over.append({"driver": r["driver"], "date": r["date"], "now_min": r["now_min"],
                     "points_now": gi["points_now"], "shown_vnd": shown,
                     "locked_vnd": locked, "marginal_vnd": shown - locked})
n_over = sum(1 for o in over if o["locked_vnd"] > 0)
print(f"\n== the 'Con voi duoc moc thuong X' : X = TONG moc hay PHAN TANG THEM? ==")
print(f"  tong the feasible_gap                 : {len(over)}")
print(f"  the co moc THAP HON DA CHOT (locked>0): {n_over}"
      f"  = {n_over/max(1,len(over))*100:.1f}%")
if n_over:
    import statistics
    ratios = [o["shown_vnd"]/o["marginal_vnd"] for o in over if o["marginal_vnd"] > 0]
    gaps = [o["shown_vnd"]-o["marginal_vnd"] for o in over if o["locked_vnd"] > 0]
    print(f"  boi so thoi phong shown/marginal      : median {statistics.median(ratios):.2f}x"
          f"  min {min(ratios):.2f}x  max {max(ratios):.2f}x")
    print(f"  so tien thoi them (shown - marginal)  : median {statistics.median(gaps):,.0f}d"
          f"  max {max(gaps):,.0f}d  TONG {sum(gaps):,.0f}d")
    byt = collections.Counter((o["shown_vnd"], o["locked_vnd"]) for o in over)
    for (s, l), c in byt.most_common():
        print(f"     shown {s:>7,}d | da chot {l:>7,}d | bien {s-l:>7,}d | {c} the")

# ---------------- 4. nguon cua tung so (luat 2) ----------------
src_bad = collections.Counter()
n_dp = 0; n_dp_with_trips = 0
for r in rows:
    if r["rep"] is None:
        continue
    rep = r["rep"]
    rate_src = None
    for n in rep["numbers"]:
        if n["unit"] == "points_per_hour":
            rate_src = n["source"]
    if rate_src == "dp:policy_theoretical":
        n_dp += 1
    for it in r["out"].get("items", []):
        for n in it.get("numbers", []):
            if n["name"] == "cuoc_can_them":
                src_bad[(rate_src, n["source"])] += 1
                if rate_src == "dp:policy_theoretical":
                    n_dp_with_trips += 1
print(f"\n== nhan NGUON cua `cuoc_can_them` vs nguon THAT cua rate ==")
print(f"  luot rate = dp:policy_theoretical (thieu lich su): {n_dp} / {len(rows)}"
      f" = {n_dp/len(rows)*100:.1f}%")
for (rs, ns), c in src_bad.most_common():
    print(f"  rate_source={rs!s:28s} -> the ghi source={ns!r}  x{c}")

# ---------------- 5. cham 3 luat CLAUDE §5 tren text MAT the ----------------
viol = collections.Counter(); total_cards = 0
sample_cards = []
for r in rows:
    for it in r["out"].get("items", []):
        total_cards += 1
        face = f"{it.get('title','')} {it.get('message','')}"
        rendered = [render_number_vn(n["value"], advisor._UNIT_KEY.get(n.get("unit"), "count"))
                    for n in it.get("numbers", []) if n.get("value") is not None]
        bare = V.check_bare_numbers(face, rendered)
        has_money = any(n.get("unit") == "vnd" for n in it.get("numbers", [])) or "đ" in face
        money_labeled = any(k in face.lower() for k in MONEY_KIND) or \
            any(k in json.dumps(it, ensure_ascii=False).lower() for k in ["gross", "payout", "net_"])
        hedged = any(h in face.lower() for h in HEDGE)
        if bare:
            viol["L2_so_tran_tren_mat_the"] += 1
        if has_money and not money_labeled:
            viol["L1_tien_khong_tach_gross_payout_net"] += 1
        if not hedged:
            viol["L3_mat_the_khong_neu_bat_dinh"] += 1
        if not it.get("caveat"):
            viol["L3b_khong_co_caveat_nao"] += 1
print(f"\n== CHAM 3 LUAT CLAUDE §5 tren {total_cards} the THAT (mat the = title+message) ==")
for k, v in viol.most_common():
    print(f"  {k:38s} {v:6d} / {total_cards}  = {v/max(1,total_cards)*100:5.1f}%")

# ---------------- 6. 10 the that de dan chung ----------------
seen = set(); ten = []
for r in rows:
    o = r["out"]
    key = o["silent"]["reason_code"] if o["silent"]["is_silent"] else o["items"][0]["reason_code"]
    if key in seen and len(ten) >= 10:
        continue
    if key in seen:
        continue
    seen.add(key)
    ten.append({"driver": r["driver"], "date": r["date"], "now_min": r["now_min"],
                "kind": r["kind"], "out": o, "raw_items": [i["reason_code"] for i in r["raw"]["items"]],
                "gi": {k: v for k, v in (r["gi"] or {}).items()
                       if k in ("points_now", "acceptance_rate", "completion_rate",
                                "historical_rate_method", "hours_budget_remaining")}})
# bu cho du 10 bang cach lay them mau ngau nhien on dinh
i = 0
while len(ten) < 10 and i < len(rows):
    r = rows[i * 977 % len(rows)]
    ten.append({"driver": r["driver"], "date": r["date"], "now_min": r["now_min"],
                "kind": r["kind"], "out": r["out"],
                "raw_items": [it["reason_code"] for it in r["raw"]["items"]],
                "gi": {k: v for k, v in (r["gi"] or {}).items()
                       if k in ("points_now", "acceptance_rate", "completion_rate",
                                "historical_rate_method", "hours_budget_remaining")}})
    i += 1
print("\n== 10 THE THAT ==")
for j, c in enumerate(ten[:10], 1):
    o = c["out"]
    print(f"\n[{j}] {c['driver']} {c['date']} {c['now_min']}' ({c['kind']}) gi={c['gi']}")
    if o["silent"]["is_silent"]:
        print(f"   SILENT {o['silent']['reason_code']}: {o['silent']['message']}")
    for it in o.get("items", []):
        print(f"   TITLE  : {it['title']}")
        print(f"   MSG    : {it['message']}")
        print(f"   NUMBERS: {json.dumps(it['numbers'], ensure_ascii=False)}")
        print(f"   CAVEAT : {it['caveat']}")
        print(f"   conf={it['confidence']} code={it['reason_code']}")
    print(f"   raw_items truoc verifier = {c['raw_items']}  verify_errors={o.get('verify_errors')}")
    print(f"   co policy_thresholds? {'policy_thresholds' in o}")

# ---------------- 7. policy_thresholds co mat o moi payload khong? ----------------
miss = collections.Counter()
for r in rows:
    o = r["out"]
    if "policy_thresholds" not in o:
        k = o["silent"]["reason_code"] if o["silent"]["is_silent"] else "ITEM"
        miss["MISS:" + k] += 1
print(f"\n== E3.3 `policy_thresholds` VANG khoi payload ==  {sum(miss.values())}/{len(rows)}")
print(" ", dict(miss))
# duong non-bike (di qua v1) — nhanh no_active_channel
nb = advisor.advice(nonbike[0], SAMPLE_DATES[0], 14 * 60)
print("  non-bike v1 payload keys:", sorted(nb.keys()))

json.dump({"n_rows": len(rows), "branches": dict(cnt),
           "cliff": {"raw": n_cliff_raw, "kept": n_cliff_kept, "rendered": n_cliff_rendered},
           "tier_overstate": over[:50], "n_over": n_over, "n_feasible": len(over),
           "violations": dict(viol), "total_cards": total_cards,
           "missing_thresholds": dict(miss)},
          open(ROOT / "research/audit/2026-08-07-phan-bien-sim-advisor/_pb5-raw.json", "w",
               encoding="utf-8"), ensure_ascii=False, indent=1)
