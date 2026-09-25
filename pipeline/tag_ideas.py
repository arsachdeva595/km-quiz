#!/usr/bin/env python3
"""
tag_ideas.py — build the index the quiz loads (docs/data/ideas.json).

Two layers:
  - Business models (data/business_models.csv): tagged with O*NET occupations,
    they carry the personality profile and the evidence.
  - Ideas: the specific ideas users see — hand-curated (data/ideas_catalog.csv)
    plus ones derived from Shark Tank pitches and ODOP products
    (data/ideas_derived.csv). Each points at one model and inherits its profile
    and evidence; budget, location, team and time can be overridden per idea.
    Derived ideas also carry their own evidence: the pitch that inspired them,
    or the districts whose ODOP they are. Models no catalog idea uses are
    offered as ideas themselves, so their evidence stays reachable.

Each model's profile is the average of its O*NET occupations in
data/onet/occupations.csv (built by fetch_onet.py). Every idea must have at
least one occupation with O*NET interest data. For the few occupations without
work-style data, traits are estimated from the RIASEC profile using the
well-documented interest↔personality correlations.

It also attaches evidence when present:
  - Shark Tank India pitches (data/sharktank/pitches.json)
  - ODOP districts whose product maps to the idea (docs/data/odop.json)

Run:  python3 pipeline/tag_ideas.py
Output: docs/data/ideas.json
"""

import csv, json, re, statistics, sys
from datetime import date
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
SEED      = ROOT / "data" / "business_models.csv"
ONET      = ROOT / "data" / "onet" / "occupations.csv"
ONET_LIST = ROOT / "data" / "onet" / "all_occupations.csv"
PITCHES   = ROOT / "data" / "sharktank" / "pitches.json"
ODOP      = ROOT / "docs" / "data" / "odop.json"
CATALOG   = ROOT / "data" / "ideas_catalog.csv"
DERIVED   = ROOT / "data" / "ideas_derived.csv"   # built by derive_ideas.py

# Models that are consumer brands selling online. Their pitches form the pool of
# D2C examples, and ideas built on them count as D2C.
D2C_MODELS = {
    "personal-care-brand", "d2c-apparel-brand", "healthy-snacks-brand", "beverage-brand",
    "jewellery-brand", "bags-and-accessories-brand", "footwear-brand", "eco-friendly-products-brand",
    "home-cleaning-products-brand", "nutrition-supplements-brand", "toys-and-games-brand",
    "handcrafted-home-decor", "ice-cream-and-desserts-brand", "pickle-and-papad-brand",
    "frozen-and-ready-to-cook-foods", "traditional-health-foods", "sweet-shop", "consumer-gadgets-brand",
    "handmade-soap-and-cosmetics", "pet-food-and-treats", "custom-gifting-store", "handloom-textiles-brand",
    "dropshipping-niche-store", "online-thrift-store", "sneaker-and-streetwear-resale", "spice-processing-unit",
    "honey-and-organic-produce", "cold-pressed-oil-mill", "fitness-apparel-brand", "ethnic-wear-label",
    "hair-accessories-brand", "oxidised-jewellery", "pottery-studio", "crockery-and-kitchenware-store",
    "candle-making", "soft-toys", "wooden-name-boards", "custom-tshirt-printing", "leather-goods-workshop",
}
D2C_WORDS = ("d2c", "online", "subscription", "e-commerce", "ecommerce", "brand")
OUT       = ROOT / "docs" / "data" / "ideas.json"

DIMS   = list("RIASEC")
TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]


def clamp(x):
    return max(0.0, min(1.0, x))


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
    examples = [pitch_example(p) for p in sorted(pitches, key=example_rank)[:3]]
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


def pitch_example(p, space=None):
    deal = p["deal"]
    ex = {
        "name":    p["name"],
        "what":    p.get("brief") or p["description"],
        "season":  p["season"],
        "episode": p["episode"],
        "city":    p["city"].split(",")[0],
        "revenue_lakh": p["yearly_revenue_lakh"],
        "ask":     {"amount_lakh": p["ask"]["amount_lakh"], "equity_pct": p["ask"]["equity_pct"]},
        "deal":    None if not deal else {
            "amount_lakh": deal["amount_lakh"], "equity_pct": deal["equity_pct"], "sharks": deal["sharks"],
        },
    }
    if space:
        ex["space"] = space
    return ex


def d2c_examples(slug, category, by_idea, model_names, model_category, n=3):
    """D2C Shark Tank brands for a model: its own pitches first, then D2C brands
    from the same category, then the strongest D2C brands overall."""
    own = sorted(by_idea.get(slug, []), key=example_rank)
    if len(own) >= n:
        return None  # the model's own Shark Tank block already covers it
    pool = [p for s in D2C_MODELS if s != slug for p in by_idea.get(s, []) if p["deal"]]
    pool.sort(key=lambda p: (model_category.get(p["idea_slug"]) != category,
                             -(p["yearly_revenue_lakh"] or 0)))
    picked = pool[: n - len(own)]
    return [pitch_example(p, model_names[p["idea_slug"]]) for p in picked]


def odop_summary(districts):
    if not districts:
        return None
    # One example per state first, so the list isn't five districts of one state.
    seen, examples = set(), []
    for d in districts:
        if d["state"] not in seen:
            seen.add(d["state"])
            examples.append({"district": d["district"], "state": d["state"], "product": d["product"], "url": d["url"]})
    return {"districts": len(districts), "examples": examples[:5],
            "keys": sorted(f"{d['district']}|{d['state']}" for d in districts)}


def top_code(r, n=3):
    return "".join(sorted(DIMS, key=lambda d: -r[d])[:n])


def main():
    onet = load_onet()
    if not onet:
        sys.exit("data/onet/occupations.csv not found — run `python3 pipeline/fetch_onet.py --offline` first.")

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

    odop_by_idea = {}
    if ODOP.exists():
        for d in json.loads(ODOP.read_text(encoding="utf-8")):
            if d.get("idea"):
                odop_by_idea.setdefault(d["idea"], []).append(d)

    models, missing_codes, untagged = [], set(), []
    for row in seed:
        codes = [c.strip() for c in row["onet_codes"].split(";") if c.strip()]
        found = [onet[c] for c in codes if c in onet]
        missing_codes.update(c for c in codes if c not in onet)
        if not found:
            untagged.append(row["slug"])
            continue

        r = average(found, DIMS)
        t = average(found, TRAITS)
        fallback = traits_from_riasec(r)
        t = {k: (v if v is not None else fallback[k]) for k, v in t.items()}

        models.append({
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
            "sharktank": shark_tank_summary(by_idea.get(row["slug"], [])),
            "odop":     odop_summary(odop_by_idea.get(row["slug"], [])),
        })

    if untagged:
        sys.exit(f"No O*NET interest data for any occupation of: {untagged} — fix onet_codes in business_models.csv")

    model_by_slug = {m["slug"]: m for m in models}
    model_names = {m["slug"]: m["name"] for m in models}
    model_category = {m["slug"]: m["category"] for m in models}

    with open(CATALOG, encoding="utf-8") as f:
        catalog = list(csv.DictReader(f))
    if DERIVED.exists():
        with open(DERIVED, encoding="utf-8") as f:
            catalog += list(csv.DictReader(f))

    pitch_by_key = {}
    if PITCHES.exists():
        pitch_by_key = {p["key"]: p for p in json.loads(PITCHES.read_text(encoding="utf-8"))}
    odop_by_ref = {}
    if ODOP.exists():
        from derive_ideas import norm_key
        for d in json.loads(ODOP.read_text(encoding="utf-8")):
            odop_by_ref.setdefault("odop:" + norm_key(d["product"]).replace(" ", "-"), []).append(d)
    unknown = sorted({r["model_slug"] for r in catalog} - set(model_by_slug))
    if unknown:
        sys.exit(f"ideas_catalog.csv uses unknown model slugs: {unknown}")

    def is_d2c(sector, name, model):
        return model in D2C_MODELS or sector.lower().startswith("d2c") or any(w in name.lower() for w in D2C_WORDS)

    ideas, used_keys = [], set()

    def page_key(name):
        """URL slug for the idea's guide page, e.g. "Foxnut (Makhana) Snacks" → "foxnut-makhana-snacks"."""
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        key, n = base, 2
        while key in used_keys:
            key, n = f"{base}-{n}", n + 1
        used_keys.add(key)
        return key

    for r in catalog:
        m = model_by_slug[r["model_slug"]]
        ideas.append({
            "id":       int(r["id"]),
            "key":      page_key(r["name"]),
            "name":     r["name"],
            "pitch":    r["pitch"],
            "market":   r["target_market"],
            "sector":   r["sector"],
            "model":    m["slug"],
            "budget":   int(r["budget_band"] or m["budget"]),
            "location": r["location"] or m["location"],
            "team":     r["team"] or m["team"],
            "time":     r["time_mode"] or m["time"],
            "d2c":      is_d2c(r["sector"], r["name"], m["slug"]),
            "source":   r.get("source") or "sheet-500",
        })
        ref = r.get("ref") or ""
        if ref in pitch_by_key:
            ideas[-1]["inspired_by"] = pitch_example(pitch_by_key[ref])
        elif ref in odop_by_ref:
            ideas[-1]["odop_here"] = odop_summary(odop_by_ref[ref])
    used = {i["model"] for i in ideas}
    for m in models:
        if m["slug"] not in used:  # keep uncovered models reachable, with their evidence
            ideas.append({
                "id": 1000 + m["id"], "key": page_key(m["name"]), "name": m["name"], "pitch": m["pitch"], "market": "",
                "sector": m["category"], "model": m["slug"], "budget": m["budget"],
                "location": m["location"], "team": m["team"], "time": m["time"],
                "d2c": is_d2c("", m["name"], m["slug"]), "source": "model",
            })

    d2c_used = {i["model"] for i in ideas if i["d2c"]}
    for m in models:
        m["sharktank_d2c"] = (d2c_examples(m["slug"], m["category"], by_idea, model_names, model_category)
                              if m["slug"] in d2c_used else None)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generated": date.today().isoformat(),
        "dims": DIMS,
        "traits": TRAITS,
        "models": models,
        "ideas": ideas,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    from collections import Counter
    by_source = Counter(i["source"] for i in ideas)
    print(f"✓ {len(ideas)} ideas on {len(models)} models → {OUT.relative_to(ROOT)}  "
          + ", ".join(f"{k}: {v}" for k, v in sorted(by_source.items())))
    print(f"  Models with Shark Tank evidence: {sum(1 for m in models if m['sharktank'])}, "
          f"with ODOP districts: {sum(1 for m in models if m['odop'])}, "
          f"D2C ideas: {sum(i['d2c'] for i in ideas)}")
    if missing_codes:
        print(f"! O*NET codes without interest data (ignored): {sorted(missing_codes)}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
