#!/usr/bin/env python3
"""
fetch_onet.py — download O*NET occupation data and derive per-occupation
RIASEC + Big Five-style trait scores.

O*NET publishes, for ~900 occupations:
  - Interests.txt    RIASEC "Occupational Interest" (OI) scores, 1–7
  - Work Styles.txt  importance (IM) of work styles such as Dependability,
                     Innovation, Cooperation — 1–5
We map work styles onto five traits (openness, conscientiousness,
extraversion, agreeableness, stability) by name, so the mapping survives
O*NET taxonomy revisions. Unmapped style names are printed so they can be
added to TRAIT_KEYWORDS.

Run:  python3 pipeline/fetch_onet.py                # try newest release first
      python3 pipeline/fetch_onet.py --version 29_3
      python3 pipeline/fetch_onet.py --offline      # use local files only

Offline, interests come from data/onet/raw/Interests.txt or, failing that, the
committed data/onet/career_interest_types.csv (same columns, comma-separated).
Work Styles is optional: without it, trait columns are left blank and
tag_ideas.py estimates traits from the RIASEC profile.

Output: data/onet/occupations.csv
License: O*NET data is CC BY 4.0 — attribution lives in README and the site footer.
"""

import argparse, csv, sys, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "onet" / "raw"
INTERESTS_CSV = ROOT / "data" / "onet" / "career_interest_types.csv"
OUT     = ROOT / "data" / "onet" / "occupations.csv"

BASE_URL = "https://www.onetcenter.org/dl_files/database/db_{ver}_text/{name}"
VERSIONS = ["30_2", "30_1", "30_0", "29_3", "29_2", "29_1", "29_0", "28_3"]
FILES    = ["Occupation Data.txt", "Interests.txt", "Work Styles.txt"]

RIASEC = ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]

# Substring (lower-case) → trait. First match wins.
TRAIT_KEYWORDS = [
    ("innovation",            "openness"),
    ("analytical",            "openness"),
    ("curiosity",             "openness"),
    ("adaptab",               "openness"),
    ("ambiguity",             "openness"),
    ("dependab",              "conscientiousness"),
    ("attention to detail",   "conscientiousness"),
    ("achievement",           "conscientiousness"),
    ("persistence",           "conscientiousness"),
    ("initiative",            "conscientiousness"),
    ("cautious",              "conscientiousness"),
    ("social orientation",    "extraversion"),
    ("leadership",            "extraversion"),
    ("self-confidence",       "extraversion"),
    ("cooperation",           "agreeableness"),
    ("concern for others",    "agreeableness"),
    ("empathy",               "agreeableness"),
    ("humility",              "agreeableness"),
    ("sincerity",             "agreeableness"),
    ("stress tolerance",      "stability"),
    ("self-control",          "stability"),
    ("optimism",              "stability"),
]
TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]


def download(version):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        url = BASE_URL.format(ver=version, name=urllib.parse.quote(name))
        print(f"  ↓ {url}")
        with urllib.request.urlopen(url, timeout=60) as r:
            (RAW_DIR / name).write_bytes(r.read())


def read_tsv(name):
    path = RAW_DIR / name
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def read_interests():
    rows = read_tsv("Interests.txt")
    if rows is not None:
        return rows
    if INTERESTS_CSV.exists():
        with open(INTERESTS_CSV, encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    sys.exit("No interest data: need data/onet/raw/Interests.txt or data/onet/career_interest_types.csv")


def trait_for(element_name):
    low = element_name.lower()
    for kw, trait in TRAIT_KEYWORDS:
        if kw in low:
            return trait
    return None


def derive():
    interests = read_interests()
    titles = {r["O*NET-SOC Code"]: r["Title"] for r in (read_tsv("Occupation Data.txt") or interests) if r.get("Title")}

    riasec = defaultdict(dict)
    for r in interests:
        if r.get("Scale ID") == "OI" and r["Element Name"] in RIASEC:
            riasec[r["O*NET-SOC Code"]][r["Element Name"][0]] = (float(r["Data Value"]) - 1) / 6

    trait_vals = defaultdict(lambda: defaultdict(list))
    unmapped = set()
    work_styles = read_tsv("Work Styles.txt")
    if work_styles is None:
        print("  ! Work Styles.txt not found — trait columns left blank (estimated later from RIASEC).")
    for r in work_styles or []:
        if r.get("Scale ID") != "IM":
            continue
        t = trait_for(r["Element Name"])
        if t is None:
            unmapped.add(r["Element Name"])
            continue
        trait_vals[r["O*NET-SOC Code"]][t].append((float(r["Data Value"]) - 1) / 4)
    if unmapped:
        print(f"  ! Work styles not mapped to a trait: {sorted(unmapped)}")

    rows = []
    for soc, scores in sorted(riasec.items()):
        if len(scores) < 6:
            continue
        tv = trait_vals.get(soc, {})
        row = {"soc": soc, "title": titles.get(soc, "")}
        row.update({k: f"{scores[k]:.3f}" for k in "RIASEC"})
        for t in TRAITS:
            vals = tv.get(t)
            row[t] = f"{sum(vals)/len(vals):.3f}" if vals else ""
        rows.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["soc", "title", *"RIASEC", *TRAITS])
        w.writeheader()
        w.writerows(rows)
    print(f"✓ {len(rows)} occupations → {OUT.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="O*NET release, e.g. 29_3")
    ap.add_argument("--offline", action="store_true", help="skip download, use data/onet/raw/")
    args = ap.parse_args()

    if not args.offline:
        for ver in ([args.version] if args.version else VERSIONS):
            try:
                print(f"Trying O*NET {ver}…")
                download(ver)
                break
            except Exception as e:
                print(f"  ✗ {ver}: {e}")
        else:
            sys.exit("Could not download O*NET. Download the text files manually from "
                     "https://www.onetcenter.org/database.html into data/onet/raw/ and re-run with --offline.")
    derive()


if __name__ == "__main__":
    main()
