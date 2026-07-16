# Project Memory

Last updated: `2026-07-16`  
Current phase: `PHASE-000 / DRAFT`  
Last verified artifact/commit: `AI coding pack v0.1; no code repository was available in the supplied workspace.`

## Mission and boundaries

Driver Income OS optimizes safe, policy-compliant driver decision support. MVP covers shift/goal/bonus/charge/break/homeward/post-shift. No dispatch, order accept/decline/cancel advice or live hotspot recommendation.

## Active decisions

- LLM is explanation/constraint/policy-QA only; no numeric/policy authority.
- Synthetic data for contract/scenarios only; no production/uplift claim.
- Hierarchical constraints and scenario MPC/baselines before RL.
- Modular monolith + worker; two developers integrate through contracts.

## Active assumptions/blockers

- Official schemas, compensation definitions, policy bundle, dispatch boundary and data owners are not yet supplied.
- These are not blockers for PHASE-001 synthetic slice; they block shadow/live exposure.

## Contract/version ledger

- DriverStateSnapshot `1.0.0-draft`.
- OptimizationRequest `1.0.0-draft`.
- RecommendationEnvelope `1.0.0-draft`.
- Model/policy/net definition: `TBD`.

## Verified evidence

- Research and attached sol 5.6 incorporated into docs.
- Three JSON Schemas passed Draft 2020-12 compilation with date-time formats; action enums are consistent.
- Target-repository compatibility, local tests and architecture audit remain required after copying.

## Work ownership

- Dev A: domain/data/forecast/optimizer/simulator/evaluation.
- Dev B: API/recommendation/policy/explanation/integration/observability.

## Known issues

- No existing repository/code/config was present in the provided workspace, so stack/tree are proposed defaults, not an audit of target code.
- Legal/policy notes require approved owners/counsel before implementation.

## Next safe step

Copy the pack into target repo, run the master prompt, perform repo audit, resolve P0 questions, and draft PHASE-001 before scaffolding.
