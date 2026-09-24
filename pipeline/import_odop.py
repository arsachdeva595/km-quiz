#!/usr/bin/env python3
"""
import_odop.py — map each district's ODOP (One District One Product) to a quiz
idea and build the district index the quiz uses for its "Your district" card.

Reads   data/odop/districts.csv     trimmed export of kidharmilega's data/districts.csv
        data/odop/overrides.csv     optional manual product → idea fixes (district_name,idea_slug)
Writes  data/odop/odop_map.csv      one row per district, for reviewing the mapping
        docs/data/odop.json         compact district index loaded by the quiz

Refresh districts.csv from the kidharmilega repo when its ODOP data changes.

Run:  python3 pipeline/import_odop.py
"""

import csv, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from odop_rules import RULES

ROOT      = Path(__file__).resolve().parent.parent
ODOP_DIR  = ROOT / "data" / "odop"
SRC       = ODOP_DIR / "districts.csv"
OVERRIDES = ODOP_DIR / "overrides.csv"
OUT_MAP   = ODOP_DIR / "odop_map.csv"
OUT_JSON  = ROOT / "docs" / "data" / "odop.json"
SEED      = ROOT / "data" / "business_models.csv"

SITE = "https://kidharmilega.in/products/"
COMPILED = [(slug, re.compile(pat, re.I)) for slug, pat in RULES]


def map_product(product):
    for slug, rx in COMPILED:
        if rx.search(product):
            return slug  # "" = heavy industry, deliberately unmapped
    return ""


def rupees(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def first_sentence(text, limit=220):
    text = (text or "").strip()
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    s = m.group(1) if m else text
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


def main():
    with open(SEED, encoding="utf-8") as f:
        valid = {r["slug"] for r in csv.DictReader(f)}
    bad_rules = {s for s, _ in RULES if s} - valid
    if bad_rules:
        sys.exit(f"odop_rules.py uses unknown idea slugs: {sorted(bad_rules)}")

    overrides = {}
    if OVERRIDES.exists():
        with open(OVERRIDES, encoding="utf-8") as f:
            overrides = {r["district_name"]: r["idea_slug"] for r in csv.DictReader(f)}

    with open(SRC, encoding="utf-8") as f:
        districts = list(csv.DictReader(f))

    out = []
    for d in districts:
        product = d["odop_product_name"]
        idea = overrides.get(d["district_name"]) or map_product(product)
        out.append({
            "district": d["district_name"],
            "state":    d["state"],
            "product":  product,
            "idea":     idea,
            "cost":     [rupees(d["min_setup_cost"]), rupees(d["max_setup_cost"])],
            "margin":   d["gross_margin_d2c"],
            "breakeven": d["breakeven_timeline"],
            "why":      first_sentence(d["why_this_district"]),
            "url":      SITE + d["page_slug"] + "/",
        })

    out.sort(key=lambda x: (x["state"], x["district"]))
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    with open(OUT_MAP, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["state", "district", "product", "idea_slug"])
        for x in out:
            w.writerow([x["state"], x["district"], x["product"], x["idea"]])

    mapped = [x for x in out if x["idea"]]
    print(f"✓ {len(out)} districts → {OUT_JSON.relative_to(ROOT)}  (mapped {len(mapped)}, unmapped {len(out) - len(mapped)})")
    print("  Top ODOP ideas: " + ", ".join(f"{s} ({n})" for s, n in Counter(x["idea"] for x in mapped).most_common(10)))
    unmapped = Counter(x["product"] for x in out if not x["idea"])
    if unmapped:
        print("  Unmapped products: " + ", ".join(sorted(unmapped)))


if __name__ == "__main__":
    main()
