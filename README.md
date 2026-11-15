# KidharMilega Business-Fit Quiz

"Which business should I start?" — a quiz for India that matches your interests (RIASEC), personality (Big Five, shown as an MBTI-style type) and constraints (budget, location, team, time) against a curated list of business ideas.

See [PLAN.md](PLAN.md) for decisions, architecture and the 30-day plan.

## Layout

```
data/ideas_catalog.csv     hand-curated ideas (500-idea sheet + 63 models), each mapped to a business model (edit this)
data/ideas_derived.csv     ideas derived from Shark Tank pitches and ODOP products (generated)
data/ideas_derived_overrides.csv  rename or skip derived ideas (edit this)
data/business_models.csv   business models: O*NET occupations, budget, location, team, time
data/onet/                 O*NET occupation list + derived scores
data/sharktank/            Shark Tank India dataset, pitch → idea map, overrides
data/odop/                 ODOP districts (from kidharmilega), product → idea map
pipeline/fetch_onet.py     download O*NET → data/onet/occupations.csv
pipeline/import_shark_tank.py  pitches → data/sharktank/pitches.json (+ pitch_map.csv for review)
pipeline/sharktank_rules.py    keyword rules mapping pitches to ideas
pipeline/import_odop.py    ODOP districts → docs/data/odop.json (+ odop_map.csv for review)
pipeline/odop_rules.py     keyword rules mapping ODOP products to ideas
pipeline/derive_ideas.py   Shark Tank + ODOP → data/ideas_derived.csv
pipeline/tag_ideas.py      models + ideas + O*NET + Shark Tank + ODOP → docs/data/ideas.json
docs/                      the static site (GitHub Pages)
tests/                     scoring tests (node:test)
```

## Commands

```bash
python3 pipeline/fetch_onet.py --offline   # uses the committed O*NET CSVs
npm run build                    # Shark Tank + ODOP import → derived ideas → docs/data/ideas.json
npm test                         # JS scoring + Python importer tests
npm run serve                    # http://localhost:8000
```

No dependencies beyond Python 3 and Node 18+.

## Adding an idea

Add a row to `data/ideas_catalog.csv` with the `model_slug` of the business model it belongs to. Leave `budget_band`, `location`, `team` and `time_mode` blank to inherit them from the model, or fill them in where this idea differs. Then run `npm run build`.

## Adding a business model

Add a row to `data/business_models.csv`:
- `onet_codes`: 1–3 O*NET-SOC codes for the work the founder actually does day to day, plus a manager occupation if the founder runs a team.
- `budget_band`: 1 = under ₹50K, 2 = ₹50K–2L, 3 = ₹2–10L, 4 = over ₹10L.
- `location`: `online`, `local`, `rural` or `any`.
- `team`: `solo`, `small` or `team`.
- `time_mode`: `side`, `full` or `both`.

Then run `npm run build`.

## Idea guides and publishing to kidharmilega.in

> **Do not run a full guide re-export yet (as of 2026-11-15).** The live guides on kidharmilega.in have scheme
> figures that were corrected there after the September 2026 export and never ported back here: Mudra's April 2026
> collateral-free rule, PMEGP under the December 2023 guidelines, and Stand-Up India terms. A `--site` export from
> this repo would quietly bring the old figures back on every guide.
>
> Before any full export: port those corrections into this repo's guide source (`SCHEMES` in
> `pipeline/build_pages.py` and the playbooks/idea files), then build and compare the output against `guides/` in
> the kidharmilega repo; the only differences should be changes you intend. Until then, publish single guides only,
> by merging each one into the live copy in the kidharmilega repo (as was done for `cloud-kitchens`).
> `build_pages.py --site` refuses to run unless you pass `--live-fixes-ported`.

Guide pages (`/ideas/<key>/`) are built from `content/playbooks/<model>.json` (shared per business model) and
`content/ideas/<key>.json` (verdict, angle, optional extra FAQs, optional `playbook` override).

```bash
python3 pipeline/build_pages.py --preview          # all guides → site/, plus site/preview.html for review
python3 pipeline/build_pages.py --site ../kidharmilega/guides --only content/launch-1.txt
```

`--site` writes a bundle for kidharmilega: `ideas/` (guides + hub, with `<!--KM:NAV-->`/`<!--KM:FOOTER-->`
markers), `quiz/` (a copy of `docs/`) and `urls.txt`. kidharmilega's `build.py` copies the bundle into `docs/`,
fills in its own nav and footer, and adds the URLs to `sitemap.xml`. `--only` limits a release to a list of keys
(`content/launch-1.txt` is the first batch); guides only link to other guides in the same release.

The quiz reads `?idea=<key>` (every guide's call to action) and opens with a fit check for that idea.

## Attribution

Occupation interest and work-style data: O*NET® database by the U.S. Department of Labor, Employment and Training Administration, used under CC BY 4.0. Modified for this project.
