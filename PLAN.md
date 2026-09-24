# KidharMilega Business-Fit Quiz — Plan v3

A separate app that answers one question: **"Which business should I start in India?"**
It supersedes the two earlier drafts (business-fit quiz PRD v0.1, overhaul PRD v2) where they conflict.

## Decisions (agreed)

| Topic | Decision |
|---|---|
| Personality model | **Hybrid.** Score with RIASEC (interests) and Big Five (traits). Show users an MBTI-style four-letter type and a plain-language archetype ("ENFP · The Brand Builder"). |
| Scope | Business ideas only. No careers or jobs. |
| App | Separate repo (`km-quiz`), static site on GitHub Pages (`docs/`). No backend. |
| Idea database | **Fixed list first**, then enrich each idea with online research. Scraped posts are evidence attached to ideas; they do not create new ideas by themselves. |
| Tagging | Ground every idea in **O*NET occupations** (idea → 1–3 O*NET-SOC codes). RIASEC comes from O*NET Interests. Trait demands come from O*NET Work Styles. No LLM guessing. |
| Primary idea sources | **Shark Tank India pitch list** (base for new ideas), **r/StartUpIndia**, **r/SharkTankIndia**. The other sources in PRD v2 are deferred. |
| Budget | As low as possible: free data, client-side scoring, cached pipeline, LLM only where it clearly pays off. |

## How it works

```
data/ideas_seed.csv ──┐
                      ├─ pipeline/tag_ideas.py ──► docs/data/ideas.json ──► quiz (docs/)
data/onet/occupations.csv (pipeline/fetch_onet.py)
```

**Quiz (33 taps, about 3 min)**
- Optional district picker (state → district). If the district's ODOP product maps to an idea, that idea gets a +0.05 local-advantage boost. The result page always shows a "Your district" card linking to the KidharMilega product page.
- 4 constraint questions: budget, location, team, time. These are hard filters. If fewer than 3 ideas survive, the filters relax in this order: time → location → budget. The result screen says when that happened.
- 18 interest items (3 per RIASEC dimension)
- 10 trait items (2 per Big Five trait, one reverse-keyed)

**Matching** (`docs/scoring.js`)
- `score = 0.72 × interest fit + 0.28 × trait fit − team penalty − risk penalty`
  - Interest fit: Pearson correlation between the user's and the idea's RIASEC profiles. O*NET's own Interest Profiler matches this way.
  - Trait fit: penalises traits the user is short on for that idea; having more than the idea needs costs little.
  - Risk penalty: applied when an anxious user (low stability) lands on a ₹2L+ idea.
- Output: 1 top pick plus 2 runners-up, preferring different sub-categories.
- "Why this fits you" copy is template-based and never shows RIASEC or Big Five jargon.
- Type code: E/I from extraversion, N/S from openness, F/T from agreeableness, J/P from conscientiousness.

**Idea tags.** Each idea averages its O*NET occupations: interests from Career Interest Types, trait demands from Work Styles. O*NET is the only source; there are no hand-assigned codes. Every non-solo idea also lists a manager or owner occupation (e.g. Food Service Managers, Retail Supervisors), so the work of running the business counts, not just the frontline work. Examples:
- "Home Bakery" = Bakers + Chefs
- "Social Media Agency" = Marketing Specialists + Graphic Designers + PR Specialists

**Tech and hardware ideas are bucketed by what the founder does day to day**, assuming a co-founder or team builds the tech:
- Apps: EdTech, HealthTech, FinTech, Community & Social, Services Marketplace, Content & Media, Gaming & Esports, B2B SaaS.
- Hardware: Consumer Gadgets, Safety & Security Devices, Deep-Tech, Industrial Solutions, Medical Devices.

## Idea record (target schema for enrichment)

The seed columns exist today. Enrichment adds the rest:

```
id, slug, name, category, sub_category, pitch, onet_codes, budget_band, location, team, time_mode   ← seed
startup_cost_min/max (₹), monthly_revenue_min/max (₹), time_to_first_revenue, margin_band
case_studies[]: {source, url, brand/founder, summary (original words), numbers, year}
  ← Shark Tank pitches: ask, valuation, revenue, margins, deal outcome
  ← Reddit posts: first-hand costs, revenue and mistakes
skills_required[], tools[], govt_schemes[], how_to_start[5–7], risks[]
evidence_count, quality_score (0–100), last_updated
```

## Sources

1. **Shark Tank India, all 5 seasons.** 789 pitches in `data/sharktank/shark_tank_india.csv` (₹ amounts in lakhs). This is the base.
   - `pipeline/import_shark_tank.py` maps each pitch to a seed idea. It uses ordered keyword rules (`pipeline/sharktank_rules.py`) plus manual fixes (`data/sharktank/overrides.csv`).
   - Current result: 787 of 789 mapped. Review everything in `data/sharktank/pitch_map.csv`.
   - Each idea then gets evidence: pitch count, deal count, median yearly revenue, and 3 example brands with ask, deal, sharks and city. The result cards show this.
   - The Season 1 sheet adds brief profiles and Reddit links for 114 pitches. It stays out of git (`data/sharktank/raw/`) because it contains internal assignee names.
2. **r/SharkTankIndia.** Discussion threads per pitch: public reaction, follow-ups, "where are they now".
3. **r/StartUpIndia.** First-hand founder posts: costs, revenue, what went wrong. Keep only posts with numbers or concrete detail.
4. **O*NET.**
   - `data/onet/career_interest_types.csv` has RIASEC interest scores for 923 occupations. Every idea is now tagged from it (`fetch_onet.py --offline`).
   - `data/onet/work_styles.csv` (O*NET 30, "Work Styles Impact" scale) supplies trait demands. All 21 work styles are mapped to five traits, and each trait is converted to a percentile across occupations, so 0.5 means a typical job.
   - `data/onet/all_occupations.csv` (occupation list plus Job Zones) validates every occupation code in the seed.
5. **KidharMilega ODOP data (787 districts).** `data/odop/districts.csv` is a trimmed export of kidharmilega's `data/districts.csv`. Refresh it when that changes.
   - `pipeline/import_odop.py` maps each ODOP product to an idea using `pipeline/odop_rules.py`. Current result: 755 of 787 mapped; the rest are heavy industry (pharma, cement, steel…), left unmapped on purpose.
   - It writes `docs/data/odop.json`: district, product, setup cost, margins, break-even, why this district, and a link to its kidharmilega.in/products page. All 787 links match existing pages.
   - Idea cards show "ODOP product of N districts, including …" with links.
   - 62 of KidharMilega's 76 existing business ideas map into the seed via `km_legacy_id`.

**Collection method (low cost).**
- Reddit: the official API (free, non-commercial tier) or the public `.json` listings, rate-limited and cached to `data/raw/`.
- Store raw text once and never re-fetch.
- Summaries are written in our own words, with a link back to the source. Never copy post text word for word.

**LLM use.**
- The pitch → idea mapping uses keyword rules plus manual review, so it costs nothing.
- An LLM is only needed later, to extract costs and lessons from Reddit posts. Use Claude Haiku through the Batch API with prompt caching, and cache every result.

## 30-day plan (revised)

| Days | Work | Output |
|---|---|---|
| 1–2 ✅ | Seed list, O*NET tagging pipeline, quiz and matching, tests | 131 ideas, working quiz |
| 3 ✅ | Shark Tank India import (789 pitches, 5 seasons), pitch → idea mapping, evidence on result cards | 169 ideas, 89 with Shark Tank evidence |
| 4 ✅ | O*NET interest scores for all ideas (923 occupations); codes validated | 169 ideas O*NET-tagged, 85% agreement with hand tags |
| 5 ✅ | Work Styles traits; manager occupations on 63 ideas; App/Hardware split into 12 behavior buckets; hand codes removed | 183 O*NET-tagged ideas |
| 6 ✅ | ODOP plug: district question, local boost, district card and ODOP links to kidharmilega.in | 755 districts mapped |
| 7 | Review `pitch_map.csv` and `odop_map.csv` | Clean mappings |
| 7–10 | Reddit collectors for r/SharkTankIndia and r/StartUpIndia; link threads to pitches and ideas | `data/raw/reddit/`, evidence linked per idea |
| 11–15 | Extraction pass (Haiku batch): costs, revenue, lessons, risks per idea; `quality_score` | `data/ideas_enriched.json` |
| 16–19 | Idea pages: one static page per idea (costs, case studies, how to start, related ideas) | `docs/ideas/<slug>/` |
| 20–22 | Quiz links to idea pages; result cards show costs plus a case-study teaser ("A Shark Tank brand in this space did ₹X/month") | Richer results |
| 23–26 | Pilot with 30–50 people: satisfaction per result, drop-off per question, trim weak items | Tuned weights and questions |
| 27–29 | SEO (meta, sitemap, internal links), share card image, privacy-friendly analytics | Launch-ready |
| 30 | Soft launch to the Instagram audience | Live |

## Open items

- **Hosting domain.** Subdomain of kidharmilega.in, or a path on it?
- **Network.** This build environment can't reach `onetcenter.org` or `reddit.com`. Run those steps locally, or allow the hosts in the cloud environment's network settings.
- **Consult CTA.** Booking link for the result screen.
- **Question count.** 32 exceeds v0.1's 10–15 target. The pilot decides whether to cut to 2 interest items per dimension.
