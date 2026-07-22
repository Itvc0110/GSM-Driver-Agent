# T-004 — Current Policy Text Corpus

`t004-current-policy-text-corpus-2026-07-22.json` preserves the full fetched
text and minimum provenance metadata for the seven current-priority first-party
Green SM sources selected in T-004.

## What is included and excluded

- Included: `main_text`, official URL, source/version hash, fetch time, stated
  cohort, lifecycle, policy family and F0 track guardrails.
- Excluded: HTML, page navigation, image files, OCR/vision transcription,
  screenshots, crawler code and historical/discovery-only raw crawl material.
- The separate 30-card survey audit is not labelled as full text: those cards
  retain citations and metadata, but do not each contain a fetched `main_text`.

## Safe reading procedure

1. Identify the driver's `vehicle_track` (`core_owned`, `platform` or `rto`)
   and the question's service/city before reading a record.
2. Filter records by `f0_tracks`, lifecycle/status and policy family. Read only
   the matching record's `main_text` with its `source_url` and `source_version`.
3. If no matching record remains, return `no_current_evidence`; do not infer a
   number, reward, fee or eligibility from another track or a generic Bike page.
4. Treat every record as evidence for reviewer work, not as an approved policy
   fact. Monetary values, thresholds and eligibility require later reviewer
   approval in T-011 or a dedicated policy-review task.

## Non-negotiable scope rules

- `green_bike_unspecified` has an empty `f0_tracks` list. It never auto-matches
  `core_owned`, `platform` or `rto`.
- A source with `unverified_active` is useful context, but cannot establish a
  current numeric entitlement.
- `page_sha256` identifies the fetched snapshot. A later source change requires
  re-review; it does not silently update the corpus.

The corpus is intentionally a small, inspectable research artifact. It is not
automatically injected into an agent prompt or used as a production runtime
knowledge base.
