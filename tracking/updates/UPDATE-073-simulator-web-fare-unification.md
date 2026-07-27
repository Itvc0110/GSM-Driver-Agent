# UPDATE-073 - Simulator/Web Driver fare unification

- **Date:** 2026-07-27
- **Owner:** Cuong / AI agent, implementation directly approved by user
- **Type:** feature + ui + docs
- **Task:** UI-FARE-01

## Summary

The Web Driver UI now consumes one canonical MOCK pricing adapter backed by
`gsm_sim.PolicyBundle` and `configs/pilot_dongda.yaml`. OSRM and deterministic
fallback routing use the same distance quote; lifecycle `/trip/step` no longer
contains static fares; the UI exposes gross, trip payout and provenance without
changing the income ledger.

## Before / after

| Surface | Before | After |
| --- | --- | --- |
| Simulator | `PolicyBundle` | unchanged canonical source |
| Route API | `round(distance_km * 24000)` | `quote_distance(total_dist_km)` for OSRM and fallback |
| `/trip/step` | static 116k/85k/145k | `fare_vnd: null`; route quote owns pricing |
| Incoming/active/history | one unlabelled fare | gross + trip payout + `sim-policy-v0` + MOCK |
| Demo completion | no fare provenance | updates `S.demoTrips` only; money/ledger byte-equivalent |

## Implementation and files

| File | Change |
| --- | --- |
| `ui/backend/app/adapters/sim_pricing.py` | cached `PolicyBundle` adapter; rejects negative distance; returns gross/payout/share/version/mock metadata |
| `ui/backend/app/models.py` | additive route quote fields; nullable trip-step fare |
| `ui/backend/app/routers/routing.py` | canonical quote on OSRM and fallback branches |
| `ui/backend/app/simulator.py` | removed three static trip-step fares; generator returns null |
| `ui/web/js/api.js` | provenance-checked quote formatter; no pricing formula |
| `ui/web/js/app.js`, `ui/web/index.html` | display gross/payout/version/mock and preserve ledger boundary |
| `ui/backend/tests/*`, `ui/web/tests/demo-pricing.mjs` | pricing, route, lifecycle, conservation and formatter regressions |
| `ui/README.md`, `ui/docs/SCREEN-PARITY.md` | canonical fare contract and UI parity notes |

## Evidence and assumptions

| Claim | Label | Evidence |
| --- | --- | --- |
| `distance <= 2km` gross = 13,000 | FACT/MOCK | `PolicyBundle.gross_fare`, config, regression test |
| `3.5km` gross = 19,450; payout = 14,588 | FACT/MOCK | `test_demo_pricing.py`, OSRM route test |
| Policy version/share | FACT/MOCK | config resolves `sim-policy-v0`, share `0.75` |
| Same distance gives same quote on OSRM/fallback | OBSERVED-CODE | route branch tests and shared adapter |
| This is active GSM pricing | NOT TRUE | active track/market/service/effective-date values remain D-POL-05/D-POL-06 |

## Verification

| Command | Result |
| --- | --- |
| `python -m pytest ui/backend/tests -q` | 31 passed, 1 dependency deprecation warning |
| full root suite, split by file due 10-minute command limit | 531 passed, 4 skipped (535 collected); first group 293 passed, second group 238 passed / 4 skipped |
| `node ui/web/tests/demo-pricing.mjs` | passed |
| `node --check ui/web/js/api.js` | passed |
| `node --check ui/web/js/app.js` | passed |
| `git diff --check` | pending final run |

## Visual verification V-11

- **Status:** `WAITING-VERDICT`
- **Scenario:** launch `/app/`, incoming -> active -> completed; compare API/UI
  gross 19,450 and payout 14,588 for 3.5km; verify policy badge and unchanged
  income pill/chart. Then inspect `/app/mo-phong/` offer gross against engine.
- **Technical observation:** live route at 7.4km rendered gross 36,220 and
  payout 27,165 with `sim-policy-v0 · MOCK · share 75%`; after completion the
  income pill remained 439,636 and 22 trips. Simulator journey exposed engine
  gross values, including the 13,000 base-fare boundary.
- **Reviewer:** user verdict remains required for V-11; this commit/push is
  explicitly authorized by the user despite the pending human visual verdict.

## Adversarial review

1. Provider distance remains the pricing basis: different OSRM/fallback
   distances can legitimately produce different values; identical distances are
   exact matches.
2. No `24000` formula remains in the current backend/Web path. The legacy guide
   still mentions it as historical documentation and is not served by FastAPI.
3. Gross, payout and estimated net remain separate; demo completion never writes
   `S.state.money`, income chart or payout ledger.
4. `sim-policy-v0` is synthetic and MOCK; it must not be promoted to active GSM
   policy without D-POL-06 evidence and an effective-date decision.

## Expansion checkpoint (T-039)

- **Schema:** additive route response fields only; no shared contract version
  bump required, Flutter route caller remains untouched.
- **Optimization:** none; pricing is deterministic arithmetic owned by the
  Simulator policy bundle, not an optimizer.
- **Feature:** UI can now show a traceable demo quote; no production fare
  feature is inferred.

## Follow-up / defer

- `D-POL-06`: active GSM fare/share by track, market, service and effective date.
- `V-11`: pending human visual verdict.
