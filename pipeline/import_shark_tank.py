#!/usr/bin/env python3
"""
import_shark_tank.py — turn the Shark Tank India dataset into idea evidence.

Reads   data/sharktank/shark_tank_india.csv            (all seasons; ₹ amounts in lakhs)
        data/sharktank/raw/season1.csv                 (optional, not committed: briefs + Reddit links)
        data/sharktank/overrides.csv                    (optional: manual pitch → idea fixes)
Writes  data/sharktank/pitches.json   cleaned pitch records, each mapped to an idea slug
        data/sharktank/pitch_map.csv  one row per pitch, for reviewing the mapping

Run:  python3 pipeline/import_shark_tank.py
"""

import csv, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sharktank_rules import RULES, APP_BUCKETS, APP_DEFAULT, HARDWARE_BUCKETS, HARDWARE_DEFAULT

ROOT      = Path(__file__).resolve().parent.parent
ST_DIR    = ROOT / "data" / "sharktank"
RAW_FULL  = ST_DIR / "shark_tank_india.csv"
RAW_S1    = ST_DIR / "raw" / "season1.csv"
OVERRIDES = ST_DIR / "overrides.csv"
OUT_JSON  = ST_DIR / "pitches.json"
OUT_MAP   = ST_DIR / "pitch_map.csv"
SEED      = ROOT / "data" / "ideas_seed.csv"

SHARKS = ["Namita", "Vineeta", "Anupam", "Aman", "Peyush", "Ritesh", "Amit"]
COMPILED = [(slug, re.compile(pat, re.I), inds) for slug, pat, inds in RULES]
SECOND_PASS = {
    "@app":      ([(s, re.compile(p, re.I)) for s, p in APP_BUCKETS], APP_DEFAULT),
    "@hardware": ([(s, re.compile(p, re.I)) for s, p in HARDWARE_BUCKETS], HARDWARE_DEFAULT),
}


def num(v):
    v = (v or "").strip().replace(",", "")
    try:
        return float(v)
    except ValueError:
        return None


def display_name(name):
    """The dataset joins words ("BluePineFoods"); split camel case for display."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name.strip())


def pitch_key(row):
    return f"S{row['Season Number']}E{row['Episode Number']}P{row['Pitch Number']}"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def domain(url):
    m = re.search(r"(?:https?://)?(?:www\.)?([^/\s?]+)", (url or "").strip().lower())
    return m.group(1) if m and "." in m.group(1) else ""


def map_pitch(desc, industry):
    for slug, rx, inds in COMPILED:
        if inds and industry not in inds:
            continue
        if rx.search(desc):
            if slug in SECOND_PASS:
                buckets, default = SECOND_PASS[slug]
                for bucket, brx in buckets:
                    if brx.search(desc):
                        return bucket, f"{slug} → {brx.pattern[:40]}"
                return default, f"{slug} → default"
            return slug, rx.pattern
    return "", ""


def load_season1():
    """Brief profiles + Reddit links from the hand-curated Season 1 sheet, keyed by name and domain."""
    if not RAW_S1.exists():
        return {}
    extra = {}
    with open(RAW_S1, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            info = {"brief": r.get("Brief Profile", "").strip(),
                    "reddit": r.get("Reddit Brand Discussion", "").strip()}
            for k in (norm(r.get("Brand Name")), domain(r.get("Website"))):
                if k:
                    extra[k] = info
    return extra


def load_overrides():
    if not OVERRIDES.exists():
        return {}
    with open(OVERRIDES, encoding="utf-8") as f:
        return {r["key"]: r["idea_slug"] for r in csv.DictReader(f)}


def parse_row(r):
    deal_amount = num(r["Total Deal Amount"])
    sharks = [s for s in SHARKS if num(r.get(f"{s} Investment Amount")) or num(r.get(f"{s} Debt Amount"))]
    if num(r.get("Guest Investment Amount")) and r.get("Invested Guest Name", "").strip():
        sharks.append(r["Invested Guest Name"].strip())
    return {
        "key":           pitch_key(r),
        "name":          display_name(r["Startup Name"]),
        "description":   r["Business Description"].strip(),
        "industry":      r["Industry"].strip(),
        "season":        int(r["Season Number"]),
        "episode":       int(r["Episode Number"]),
        "air_date":      r["Original Air Date"].strip(),
        "started_in":    r["Started in"].strip(),
        "city":          r["Pitchers City"].strip(),
        "state":         r["Pitchers State"].strip(),
        "website":       r["Company Website"].strip(),
        "yearly_revenue_lakh": num(r["Yearly Revenue"]),
        "monthly_sales_lakh":  num(r["Monthly Sales"]),
        "gross_margin_pct":    num(r["Gross Margin"]),
        "net_margin_pct":      num(r["Net Margin"]),
        "bootstrapped":  r["Bootstrapped"].strip().lower() == "yes",
        "ask": {
            "amount_lakh":    num(r["Original Ask Amount"]),
            "equity_pct":     num(r["Original Offered Equity"]),
            "valuation_lakh": num(r["Valuation Requested"]),
        },
        "deal": None if not deal_amount else {
            "amount_lakh":    deal_amount,
            "equity_pct":     num(r["Total Deal Equity"]),
            "debt_lakh":      num(r["Total Deal Debt"]),
            "valuation_lakh": num(r["Deal Valuation"]),
            "sharks":         sharks,
        },
    }


def main():
    if not RAW_FULL.exists():
        sys.exit(f"Missing {RAW_FULL.relative_to(ROOT)} — put the Shark Tank India CSV there.")

    with open(SEED, encoding="utf-8") as f:
        valid_slugs = {r["slug"] for r in csv.DictReader(f)}
    s1 = load_season1()
    overrides = load_overrides()
    rule_slugs = {s for s, _, _ in RULES if not s.startswith("@")} | {s for s, _ in APP_BUCKETS + HARDWARE_BUCKETS} | {APP_DEFAULT, HARDWARE_DEFAULT}
    if rule_slugs - valid_slugs:
        sys.exit(f"sharktank_rules.py uses unknown idea slugs: {sorted(rule_slugs - valid_slugs)}")
    bad = {k: v for k, v in overrides.items() if v and v not in valid_slugs}
    if bad:
        sys.exit(f"overrides.csv uses unknown idea slugs: {bad}")

    pitches = []
    with open(RAW_FULL, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            p = parse_row(r)
            extra = s1.get(norm(p["name"])) or s1.get(domain(p["website"])) if p["season"] == 1 else None
            if extra:
                p["brief"] = extra["brief"] or None
                p["reddit_url"] = extra["reddit"] or None
            if p["key"] in overrides:
                p["idea_slug"], p["mapped_by"] = overrides[p["key"]], "override"
            else:
                p["idea_slug"], p["mapped_by"] = map_pitch(p["description"], p["industry"])
            pitches.append(p)

    OUT_JSON.write_text(json.dumps(pitches, indent=1, ensure_ascii=False), encoding="utf-8")
    with open(OUT_MAP, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "name", "industry", "description", "idea_slug", "mapped_by"])
        for p in pitches:
            w.writerow([p["key"], p["name"], p["industry"], p["description"], p["idea_slug"], p["mapped_by"]])

    mapped = [p for p in pitches if p["idea_slug"]]
    print(f"✓ {len(pitches)} pitches → {OUT_JSON.relative_to(ROOT)}  "
          f"(mapped {len(mapped)}, unmapped {len(pitches) - len(mapped)}, "
          f"season-1 extras {sum('brief' in p for p in pitches)})")
    top = Counter(p["idea_slug"] for p in mapped).most_common(12)
    print("  Most-pitched ideas: " + ", ".join(f"{s} ({n})" for s, n in top))
    unmapped = [p for p in pitches if not p["idea_slug"]]
    for p in unmapped[:40]:
        print(f"  ? {p['key']:<10} [{p['industry']}] {p['description']}")


if __name__ == "__main__":
    main()
