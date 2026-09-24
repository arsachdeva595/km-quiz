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

**Quiz (32 taps, about 3 min)**
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

**Idea tags.** Each idea averages its O*NET occupations. Examples:
- "Home Bakery" = Bakers + Chefs
- "Social Media Agency" = Marketing Specialists + Graphic Designers + PR Specialists

Until O*NET is fetched, ideas use hand-assigned provisional codes. `tag_ideas.py` reports how often the provisional code agrees with O*NET, so disagreements can be reviewed.

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

1. **Shark Tank India pitch list** (user-supplied).
   - Each pitch maps to a generic idea. For example, a millet-cookie brand maps to "Millet Snacks Brand".
   - If a pitch fits no existing idea, propose a new one (with O*NET codes) for manual approval.
   - Each pitch then becomes a case study with real numbers (ask, valuation, revenue, margins).
2. **r/SharkTankIndia.** Discussion threads per pitch: public reaction, follow-ups, "where are they now".
3. **r/StartUpIndia.** First-hand founder posts: costs, revenue, what went wrong. Keep only posts with numbers or concrete detail.
4. **KidharMilega ODOP data (787 districts).** Links the manufacturing and craft ideas to the districts where the raw material and clusters are. 62 of KidharMilega's 76 existing ideas map into the seed via `km_legacy_id` (from `business_ideas.csv`).

**Collection method (low cost).**
- Reddit: the official API (free, non-commercial tier) or the public `.json` listings, rate-limited and cached to `data/raw/`.
- Store raw text once and never re-fetch.
- Summaries are written in our own words, with a link back to the source. Never copy post text word for word.

**LLM use.**
- One extraction call per source document, turning raw text into structured facts, with results cached.
- Use Claude Haiku through the Batch API (about half price) with prompt caching.
- Mapping pitches to ideas is done in bulk: one call handles about 50 pitches, with the idea list in a cached prompt.
- The cost estimate in PRD v2 used out-of-date pricing. Re-estimate once the Shark Tank list size is known.

## 30-day plan (revised)

| Days | Work | Output |
|---|---|---|
| 1–2 ✅ | Seed list, O*NET tagging pipeline, quiz and matching, tests | 131 ideas, working quiz (this commit) |
| 3 | Run `fetch_onet.py`, fix any unknown SOC codes, review provisional-vs-O*NET disagreements | O*NET-grounded tags |
| 4–6 | Import the Shark Tank list, map pitches to ideas, approve new ideas | Seed grows (target 250–400 ideas), each with ≥1 Shark Tank case study where possible |
| 7–10 | Reddit collectors for r/SharkTankIndia and r/StartUpIndia; link threads to pitches and ideas | `data/raw/reddit/`, evidence linked per idea |
| 11–15 | Extraction pass (Haiku batch): costs, revenue, lessons, risks per idea; `quality_score` | `data/ideas_enriched.json` |
| 16–19 | Idea pages: one static page per idea (costs, case studies, how to start, related ideas) | `docs/ideas/<slug>/` |
| 20–22 | Quiz links to idea pages; result cards show costs plus a case-study teaser ("A Shark Tank brand in this space did ₹X/month") | Richer results |
| 23–26 | Pilot with 30–50 people: satisfaction per result, drop-off per question, trim weak items | Tuned weights and questions |
| 27–29 | SEO (meta, sitemap, internal links), share card image, privacy-friendly analytics | Launch-ready |
| 30 | Soft launch to the Instagram audience | Live |

## Open items

- **Shark Tank list.** Need the file (format and columns) to write the importer.
- **Hosting domain.** Subdomain of kidharmilega.in, or a path on it?
- **Network.** This build environment can't reach `onetcenter.org` or `reddit.com`. Run those steps locally, or allow the hosts in the cloud environment's network settings.
- **Consult CTA.** Booking link for the result screen.
- **Question count.** 32 exceeds v0.1's 10–15 target. The pilot decides whether to cut to 2 interest items per dimension.
