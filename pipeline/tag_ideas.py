#!/usr/bin/env python3
"""
tag_ideas.py — give every idea in data/ideas_seed.csv a RIASEC profile and
trait-demand profile, then write the compact index the quiz loads.

For each idea:
  - If its O*NET codes are found in data/onet/occupations.csv, the profile is
    the average of those occupations (tag_source = "onet").
  - Otherwise it falls back to the hand-assigned `riasec_provisional` code
    (tag_source = "provisional"), with traits estimated from RIASEC using the
    well-documented interest↔personality correlations (Artistic/Investigative
    ↔ openness, Social/Enterprising ↔ extraversion, Social ↔ agreeableness,
    Conventional ↔ conscientiousness).

It also attaches Shark Tank India evidence (pitch count, deal rate, median
revenue, example brands) from data/sharktank/pitches.json when present.

Run:  python3 pipeline/tag_ideas.py
Output: docs/data/ideas.json
"""

import csv, json, statistics, sys
from datetime import date
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
SEED      = ROOT / "data" / "ideas_seed.csv"
ONET      = ROOT / "data" / "onet" / "occupations.csv"
ONET_LIST = ROOT / "data" / "onet" / "all_occupations.csv"
PITCHES   = ROOT / "data" / "sharktank" / "pitches.json"
OUT       = ROOT / "docs" / "data" / "ideas.json"

DIMS   = list("RIASEC")
TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]
LETTER_WEIGHTS = [1.0, 0.75, 0.55]
BASELINE = 0.2


def clamp(x):
    return max(0.0, min(1.0, x))


def provisional_riasec(code):
    v = {d: BASELINE for d in DIMS}
    for letter, w in zip(code, LETTER_WEIGHTS):
        v[letter] = w
    return v


def traits_from_riasec(r):
    return {
        "openness":          clamp(0.25 + 0.40 * r["A"] + 0.30 * r["I"] - 0.10 * r["C"]),
        "conscientiousness": clamp(0.30 + 0.35 * r["C"] + 0.15 * r["R"] + 0.15 * r["E"]),
        "extraversion":      clamp(0.15 + 0.40 * r["E"] + 0.35 * r["S"] - 0.10 * r["I"]),
        "agreeableness":     clamp(0.30 + 0.45 * r["S"] - 0.10 * r["E"]),
        "stability":         0.5,
    }


def load_onet():
    if not ONET.exists():
        return {}
    with open(ONET, encoding="utf-8") as f:
        return {row["soc"]: row for row in csv.DictReader(f)}


def load_valid_codes():
    if not ONET_LIST.exists():
        return None
    with open(ONET_LIST, encoding="utf-8-sig") as f:
        return {row["Code"] for row in csv.DictReader(f)}


def example_rank(p):
    # Deals first, then pitches with revenue data, then newest.
    return (p["deal"] is None, p["yearly_revenue_lakh"] is None, -p["season"], -p["episode"])


def shark_tank_summary(pitches):
    if not pitches:
        return None
    revenues = [p["yearly_revenue_lakh"] for p in pitches if p["yearly_revenue_lakh"]]
    examples = []
    for p in sorted(pitches, key=example_rank)[:3]:
        deal = p["deal"]
        examples.append({
            "name":    p["name"],
            "what":    p.get("brief") or p["description"],
            "season":  p["season"],
            "episode": p["episode"],
            "city":    p["city"].split(",")[0],
            "revenue_lakh": p["yearly_revenue_lakh"],
            "ask":     {"amount_lakh": p["ask"]["amount_lakh"], "equity_pct": p["ask"]["equity_pct"]},
            "deal":    None if not deal else {
                "amount_lakh": deal["amount_lakh"], "equity_pct": deal["equity_pct"],
                "sharks": deal["sharks"],
            },
        })
    return {
        "pitches": len(pitches),
        "deals":   sum(p["deal"] is not None for p in pitches),
        "median_revenue_lakh": round(statistics.median(revenues), 1) if revenues else None,
        "revenue_reported": len(revenues),
        "examples": examples,
    }


def average(rows, keys):
    out = {}
    for k in keys:
        vals = [float(r[k]) for r in rows if r.get(k)]
        out[k] = sum(vals) / len(vals) if vals else None
    return out


def top_code(r, n=3):
    return "".join(sorted(DIMS, key=lambda d: -r[d])[:n])


def main():
    onet = load_onet()
    if not onet:
        print("! data/onet/occupations.csv not found — using provisional tags for every idea.\n"
              "  Run `python3 pipeline/fetch_onet.py` to ground tags in O*NET.")

    with open(SEED, encoding="utf-8") as f:
        seed = list(csv.DictReader(f))

    valid = load_valid_codes()
    if valid is not None:
        unknown = sorted({c for r in seed for c in r["onet_codes"].split(";") if c and c not in valid})
        if unknown:
            print(f"! O*NET codes not in all_occupations.csv: {unknown}")

    by_idea = {}
    if PITCHES.exists():
        for p in json.loads(PITCHES.read_text(encoding="utf-8")):
            if p.get("idea_slug"):
                by_idea.setdefault(p["idea_slug"], []).append(p)

    ideas, missing_codes, agree = [], set(), []
    for row in seed:
        codes = [c.strip() for c in row["onet_codes"].split(";") if c.strip()]
        found = [onet[c] for c in codes if c in onet]
        missing_codes.update(c for c in codes if onet and c not in onet)

        if found:
            r = average(found, DIMS)
            t = average(found, TRAITS)
            fallback = traits_from_riasec(r)
            t = {k: (v if v is not None else fallback[k]) for k, v in t.items()}
            source = "onet"
            agree.append(top_code(r, 1) in row["riasec_provisional"][:2])
        else:
            r = provisional_riasec(row["riasec_provisional"])
            t = traits_from_riasec(r)
            source = "provisional"

        ideas.append({
            "id":       int(row["id"]),
            "slug":     row["slug"],
            "name":     row["name"],
            "category": row["category"],
            "sub":      row["sub_category"],
            "pitch":    row["pitch"],
            "budget":   int(row["budget_band"]),
            "location": row["location"],
            "team":     row["team"],
            "time":     row["time_mode"],
            "riasec":   [round(r[d], 3) for d in DIMS],
            "traits":   [round(t[k], 3) for k in TRAITS],
            "code":     top_code(r),
            "source":   source,
            "sharktank": shark_tank_summary(by_idea.get(row["slug"], [])),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "dims": DIMS,
        "traits": TRAITS,
        "ideas": ideas,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    n_onet = sum(i["source"] == "onet" for i in ideas)
    n_st = sum(1 for i in ideas if i["sharktank"])
    print(f"✓ {len(ideas)} ideas → {OUT.relative_to(ROOT)}  (onet: {n_onet}, provisional: {len(ideas) - n_onet}, with Shark Tank evidence: {n_st})")
    if missing_codes:
        print(f"! O*NET codes not found (fix in ideas_seed.csv): {sorted(missing_codes)}")
    if agree:
        print(f"  Provisional vs O*NET top-letter agreement: {sum(agree)}/{len(agree)} "
              f"({100 * sum(agree) / len(agree):.0f}%) — review disagreements by hand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
