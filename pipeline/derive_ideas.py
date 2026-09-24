#!/usr/bin/env python3
"""
derive_ideas.py — grow the idea list from real evidence.

  - Shark Tank India: each pitch that maps to a business model becomes a
    generic idea named after what the brand sells ("Kerala Banana Chips"),
    with the brand kept as its case study.
  - ODOP: each distinct district product becomes an idea ("Channapatna Toys"),
    linked to the districts that make it. Its budget comes from the districts'
    setup costs.

Ideas whose names duplicate the hand-curated catalog, or each other, are
dropped. Manual fixes go in data/ideas_derived_overrides.csv:
  ref,action,name,pitch     action = skip | rename   (ref = S1E1P1 or odop:<key>)

Reads   data/sharktank/pitches.json, docs/data/odop.json, data/ideas_catalog.csv,
        data/business_models.csv
Writes  data/ideas_derived.csv

Run:  python3 pipeline/derive_ideas.py
"""

import csv, json, re, statistics
from collections import defaultdict
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
PITCHES   = ROOT / "data" / "sharktank" / "pitches.json"
ODOP      = ROOT / "docs" / "data" / "odop.json"
CATALOG   = ROOT / "data" / "ideas_catalog.csv"
MODELS    = ROOT / "data" / "business_models.csv"
OVERRIDES = ROOT / "data" / "ideas_derived_overrides.csv"
OUT       = ROOT / "data" / "ideas_derived.csv"

FIELDS = ["id", "sector", "name", "pitch", "target_market", "model_slug",
          "budget_band", "location", "team", "time_mode", "source", "ref"]

# Words that say nothing about the specific idea; a name made only of these is too generic.
GENERIC = set("""
a an and the of for in with by to from & - based product products processing process processed
agro agri agricultural agriculture food foods item items goods good brand brands online company
handicraft handicrafts handloom handlooms textile textiles garment garments readymade ready made
apparel apparels engineering light industry industrial tourism furniture wood wooden work craft crafts
spice spices vegetable vegetables fruit fruits fisheries fishery marine dairy milk allied products
other others various clothing clothes cloth sightseeing medical religious machine machinery machines
fmcg cluster activities
""".split())

STOP_SUFFIX = re.compile(r"\s+(brand|brands|company|online|products? online)$", re.I)


SPELLING = {
    "chilly": "chilli", "chillies": "chilli", "chilies": "chilli", "chili": "chilli", "chilie": "chilli",
    "chillie": "chilli", "mircha": "chilli", "madhubhani": "madhubani", "jewllery": "jewellery",
    "jewelry": "jewellery", "silverfiligree": "silver filigree", "daal": "dal", "zardosi": "zardozi",
    "peanuts": "groundnut", "peanut": "groundnut", "groundnuts": "groundnut", "icecream": "ice cream",
    "icecreams": "ice cream", "arecanut": "areca nut", "soyabean": "soya bean", "tarkashi": "tarakashi",
}


def norm_key(name):
    text = name.lower()
    for a, b in SPELLING.items():
        text = re.sub(rf"\b{a}\b", b, text)
    words = re.findall(r"[a-z0-9]+", text)
    words = [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]
    return " ".join(w for w in words if w not in {"brand", "and", "the", "of", "for", "with", "a"})


def significant(name):
    return {w for w in norm_key(name).split() if w not in GENERIC and len(w) > 2}


def similar(a, b):
    sa, sb = significant(a), significant(b)
    if not sa or not sb:
        return False
    return len(sa & sb) / len(sa | sb) >= 0.6


def title(text):
    words = text.split()
    return " ".join(w if any(c.isupper() for c in w[1:]) or w.isupper() else w[:1].upper() + w[1:] for w in words)


def budget_band(rupees):
    if rupees is None:
        return ""
    return "1" if rupees < 50_000 else "2" if rupees < 200_000 else "3" if rupees < 1_000_000 else "4"


def lakh(v):
    return f"₹{v / 100:g} Cr" if v >= 100 else f"₹{v:g}L"


def load_overrides():
    if not OVERRIDES.exists():
        return {}
    with open(OVERRIDES, encoding="utf-8") as f:
        return {r["ref"]: r for r in csv.DictReader(f)}


# ── Shark Tank ───────────────────────────────────────────────────────────────

def shark_tank_ideas(models, d2c_models):
    out = []
    for p in json.loads(PITCHES.read_text(encoding="utf-8")):
        slug = p.get("idea_slug")
        if not slug:
            continue
        name = p["description"].strip().rstrip(".")
        name = re.sub(r"^(innovative|buy|offer)\s+", "", name, flags=re.I)
        name = STOP_SUFFIX.sub("", re.sub(r"\s{2,}", " ", name).strip(" -,:."))
        if re.match(r"^(for|with|in|where|saving|transforming|real|smart teens)\b", name, re.I):
            continue  # a slogan, not an idea name
        if len(name.split()) < 2:
            if slug in d2c_models and name:
                name = f"{name} Brand"
            else:
                continue
        if len(name) > 55:
            continue  # long marketing lines read badly as idea names
        name = title(name)
        m = models[slug]
        deal = p["deal"]
        outcome = (f"got {lakh(deal['amount_lakh'])} for {deal['equity_pct']:g}%" if deal
                   else f"asked {lakh(p['ask']['amount_lakh'])}, no deal")
        out.append({
            "sector": "Shark Tank India",
            "name": name,
            "pitch": f"Inspired by {p['name']} from {p['city'].split(',')[0] or 'India'}, who pitched this on "
                     f"Shark Tank India (S{p['season']} E{p['episode']}) and {outcome}.",
            "target_market": "",
            "model_slug": slug,
            "budget_band": "", "location": "", "team": "", "time_mode": "",
            "source": "sharktank",
            "ref": p["key"],
            "_model": m,
        })
    return out


# ── ODOP ─────────────────────────────────────────────────────────────────────

PRODUCE = {"fruit-and-vegetable-processing", "agro-processing-unit", "spice-processing-unit",
           "honey-and-organic-produce", "cold-pressed-oil-mill", "beverage-brand", "healthy-snacks-brand",
           "seafood-processing", "dairy-farm", "poultry-farm", "mushroom-farming", "nursery-and-plants",
           "pickle-and-papad-brand", "sweet-shop", "home-bakery"}
NAME_SUFFIX = {
    "fruit-and-vegetable-processing": "Processing", "agro-processing-unit": "Processing Unit",
    "seafood-processing": "Processing", "poultry-farm": "Farming", "mushroom-farming": "Farming",
    "dairy-farm": "Unit", "nursery-and-plants": "Nursery",
}


def odop_ideas():
    groups = defaultdict(list)
    for d in json.loads(ODOP.read_text(encoding="utf-8")):
        if d["idea"]:
            groups[(norm_key(d["product"]), d["idea"])].append(d)

    out = []
    for (key, slug), districts in sorted(groups.items()):
        product = min((d["product"] for d in districts), key=len).strip().rstrip(",")
        if not significant(product):
            continue  # "Agro Based Products", "Handicrafts" … the business model already covers these
        name = re.sub(r"\s*\(.*?\)", "", product).split(",")[0].strip(" -/")
        if len(name) > 45:
            continue
        suffix = NAME_SUFFIX.get(slug)
        if suffix and suffix.lower() not in name.lower():
            name = f"{name} {suffix}"
        elif slug in PRODUCE and not re.search(r"product|brand|processing", name, re.I):
            name = f"{name} Brand"
        places = [d["district"] for d in districts]
        where = ", ".join(places[:3]) + (f" and {len(places) - 3} more" if len(places) > 3 else "")
        if slug in PRODUCE:
            pitch = f"{product} is the ODOP of {where}. Buy direct from growers there and sell a processed, branded product."
        else:
            pitch = f"{product} is the ODOP of {where}. Work with its makers and sell their work to city and export buyers."
        mins = [d["cost"][0] for d in districts if d["cost"][0]]
        out.append({
            "sector": "ODOP (One District One Product)",
            "name": title(name),
            "pitch": pitch,
            "target_market": "",
            "model_slug": slug,
            "budget_band": budget_band(statistics.median(mins)) if mins else "",
            "location": "", "team": "", "time_mode": "",
            "source": "odop",
            "ref": "odop:" + key.replace(" ", "-"),
        })
    return out


def main():
    with open(MODELS, encoding="utf-8") as f:
        models = {r["slug"]: r for r in csv.DictReader(f)}
    with open(CATALOG, encoding="utf-8") as f:
        catalog_names = [r["name"] for r in csv.DictReader(f)]

    import tag_ideas  # shares the D2C model list
    overrides = load_overrides()

    kept, seen, dropped = [], {norm_key(n) for n in catalog_names}, 0
    existing = list(catalog_names)
    for idea in odop_ideas() + shark_tank_ideas(models, tag_ideas.D2C_MODELS):
        o = overrides.get(idea["ref"])
        if o and o["action"] == "skip":
            continue
        if o and o["action"] == "rename":
            idea["name"] = o["name"] or idea["name"]
            idea["pitch"] = o.get("pitch") or idea["pitch"]
        k = norm_key(idea["name"])
        if k in seen or any(similar(idea["name"], n) for n in existing):
            dropped += 1
            continue
        seen.add(k)
        existing.append(idea["name"])
        kept.append(idea)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for n, idea in enumerate(kept):
            base = 3000 if idea["source"] == "odop" else 2000
            idea["id"] = base + sum(1 for x in kept[:n] if x["source"] == idea["source"]) + 1
            w.writerow(idea)

    by_src = defaultdict(int)
    for i in kept:
        by_src[i["source"]] += 1
    print(f"✓ {len(kept)} derived ideas → {OUT.relative_to(ROOT)}  "
          f"(ODOP {by_src['odop']}, Shark Tank {by_src['sharktank']}; {dropped} duplicates dropped)")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
