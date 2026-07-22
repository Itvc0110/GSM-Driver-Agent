# T-004 — Official Bike Policy Source Register

**Purpose:** A small, link-only research handoff for later reviewer work. This is
not a policy database, prompt context, or a runtime dependency.

**Reviewed:** 2026-07-21–22 · **Authority:** public first-party Green SM pages
only (`greensm.com`, `cdn.xanhsm.com`) · **Snapshot:** 2026-07-21.

## How to use this register

1. Re-fetch the linked official page when T-011 (policy registry) or a future
   OCR/reviewer task is explicitly opened.
2. Record the page version/hash and compare the effective date before extracting
   any fact. The page HTML changed between the two T-004 fetches, so no old
   extraction is assumed current.
3. A reviewer, not an LLM, verifies text in tables/images before a number,
   threshold, reward, fee, or eligibility statement is used.

## Current-priority official sources

| Source | Cohort stated by source | Why retained | Official link |
| --- | --- | --- | --- |
| Express 2H operating guide | Core-owned, Platform, RTO | Delivery workflow and operating rules; scope explicitly names all three tracks. | [Green SM Express 2H](https://www.greensm.com/vn-vi/news/green-sm-express-huong-dan-van-doanh-va-cap-nhat-khung-gio-hoat-dong-dich-vu-green-express-2h) |
| Express location-mismatch support | Core-owned, Platform, RTO | Support procedure and service-specific fare support; verify dates and amount before use. | [Fare support](https://www.greensm.com/vn-vi/news/chinh-sach-ho-tro-cuoc-phi-tai-xe-gap-loi-dinh-vi-don-hang-express-doanh-nghiep) |
| Bike Platform income guarantee | Platform | Income, activity, joining and battery-benefit evidence for Platform only. | [Platform income guarantee](https://www.greensm.com/vn-vi/news/chinh-sach-dam-bao-thu-nhap-cho-green-bike-platform) |
| Bike Platform/RTO conduct | Platform, RTO | Conduct and operations reference; no literal Hà Nội scope is needed for this non-monetary guidance. | [Platform conduct](https://www.greensm.com/vn-vi/news/bo-quy-tac-ung-xu-danh-cho-doi-tac-tai-xe-bike-platform) |
| RTO battery-account rule | RTO | Battery-account and support-channel guidance for RTO. | [RTO battery account](https://www.greensm.com/vn-vi/news/doi-pin-dung-tai-khoan-bao-ve-quyen-loi-van-doanh) |
| Generic Bike conduct | `green_bike_unspecified` | Official Bike conduct reference, but it does not prove core-owned/Platform/RTO membership. | [Generic Bike conduct](https://www.greensm.com/vn-vi/news/cap-nhat-bo-quy-tac-ung-xu-danh-cho-doi-tac-tai-xe-bike) |
| Generic Bike income/operations | `green_bike_unspecified` | Official Bike income/reward/operation evidence with Hà Nội in the page; track is still unspecified. | [Generic Bike income](https://www.greensm.com/vn-vi/news/cap-nhat-chinh-sach-thu-nhap-van-doanh-ha-noi-ho-chi-minh-dong-nai) |

## Discovery entrypoints

- [Driver Center](https://www.greensm.com/vn-vi/driver-center) — first official
  place to inspect driver-oriented child pages.
- [Official sitemap](https://www.greensm.com/sitemap.xml) — source discovery only;
  marketing/customer pages must not become driver-policy evidence without review.

## Non-negotiable guardrails

- `green_bike_unspecified` never auto-matches `core_owned`, `platform`, or `rto`.
- Exact track is mandatory for F0. A missing track means ask for the operating
  model; do not return a numeric entitlement or eligibility answer.
- Any monetary/local rule needs matching track, city/service, lifecycle/effective
  date, first-party source and reviewer approval. A generic Bike page cannot be
  used to label a policy as xe công ty.
- Archive, campaign, recruitment and customer-promotion content are discovery or
  historical material only, never F0 input.

## Deliberate repository boundary

The compact [text-only corpus](./t004-current-policy-text-corpus-2026-07-22.json)
and its [safe-reading guide](./T004_TEXT_CORPUS_USAGE.md) are retained for human
inspection and later reviewer work. Raw HTML, image assets, OCR/vision
transcriptions, crawler scripts and test fixtures remain excluded so the
repository does not mistake them for production knowledge. A later source change
still requires a re-fetch and reviewer decision before any policy fact is used.
