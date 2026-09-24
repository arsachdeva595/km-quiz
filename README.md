# KidharMilega Business-Fit Quiz

"Which business should I start?" — a quiz for India that matches your interests (RIASEC), personality (Big Five, shown as an MBTI-style type) and constraints (budget, location, team, time) against a curated list of business ideas.

See [PLAN.md](PLAN.md) for decisions, architecture and the 30-day plan.

## Layout

```
data/ideas_seed.csv        fixed list of business ideas (edit this)
data/onet/                 O*NET-derived occupation scores (generated)
pipeline/fetch_onet.py     download O*NET → data/onet/occupations.csv
pipeline/tag_ideas.py      seed + O*NET → docs/data/ideas.json
docs/                      the static site (GitHub Pages)
tests/                     scoring tests (node:test)
```

## Commands

```bash
python3 pipeline/fetch_onet.py   # needs access to onetcenter.org
npm run build                    # regenerate docs/data/ideas.json
npm test
npm run serve                    # http://localhost:8000
```

No dependencies beyond Python 3 and Node 18+.

## Adding an idea

Add a row to `data/ideas_seed.csv`:
- `onet_codes`: 1–3 O*NET-SOC codes for the work the founder actually does day to day.
- `riasec_provisional`: a fallback code.
- `budget_band`: 1 = under ₹50K, 2 = ₹50K–2L, 3 = ₹2–10L, 4 = over ₹10L.
- `location`: `online`, `local`, `rural` or `any`.
- `team`: `solo`, `small` or `team`.
- `time_mode`: `side`, `full` or `both`.

Then run `npm run build`.

## Attribution

Occupation interest and work-style data: O*NET® database by the U.S. Department of Labor, Employment and Training Administration, used under CC BY 4.0. Modified for this project.
