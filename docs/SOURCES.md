# Curated source policy

Seed records were reviewed against official pages on **2026-09-18**. They are paraphrases, not a live synchronized benefits database. The URLs below are also shown on every program card.

| Program | Official source | Page's last updated |
|---|---|---|
| SNAP | https://access.nyc.gov/programs/supplemental-nutrition-assistance-program-snap/ | 2026-07-06 |
| Fair Fares | https://access.nyc.gov/programs/fair-fares/ | 2025-11-06 |
| One Shot Deal | https://access.nyc.gov/programs/one-shot-deal/ | 2025-04-08 |
| Cash Assistance | https://access.nyc.gov/programs/cash-assistance/ | 2025-06-17 |
| Community Food Connection | https://access.nyc.gov/programs/emergency-food-assistance/ | 2026-06-18 |
| Homebase | https://access.nyc.gov/programs/homebase/ | 2024-04-04 |
| Unemployment | https://dol.ny.gov/you-file-claim-unemployment-faqs | Not stated; stored as null |

Fair Fares' cited table lists $23,475 for one person and $8,250 per additional person, ages 18–64. The engine uses this captured table, not an invented estimate. The UI explicitly directs users to verify current requirements. A newer agency rule can supersede the captured table even before the 90-day window ends.

`last_updated` is the publisher's displayed update date, not a policy effective date. `verified_at` records this project's source review. Rule version `nyc-2026-09-18.v1` identifies the initial implementation. The 90-day review gate is a conservative software policy; it does not establish legal validity. Future effective dates, emergency changes and conflicting official pages need human review.

To update: read the official page, compare rules and documents, update seed fields and boundary tests together, bump the rule version when logic changes, then restart to upsert the catalog. Never refresh verification timestamps automatically without checking source content.
