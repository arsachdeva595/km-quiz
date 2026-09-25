#!/usr/bin/env python3
"""
build_pages.py — build the "Should you start X in 2026?" guide pages.

Each page combines three layers:
  - content/playbooks/<model>.json   written once per business model: market reality,
                                     setup costs, unit economics, hard truths, 90-day plan
  - content/ideas/<key>.json         written per idea: verdict, what's different, FAQ
  - docs/data/ideas.json + odop.json real data: Shark Tank pitches, ODOP districts,
                                     O*NET personality fit, related ideas

Only ideas with both a playbook and an idea file get a page, so pages can be
written and reviewed in batches.

Run:  python3 pipeline/build_pages.py            # → site/ideas/<key>/index.html
      python3 pipeline/build_pages.py --preview  # also site/preview.html (all pages in one file)
"""

import html, json, re, sys
from datetime import date
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
PLAYBOOKS = ROOT / "content" / "playbooks"
IDEAS_TXT = ROOT / "content" / "ideas"
IDEAS     = ROOT / "docs" / "data" / "ideas.json"
PITCHES   = ROOT / "data" / "sharktank" / "pitches.json"
ODOP      = ROOT / "docs" / "data" / "odop.json"
OUT       = ROOT / "site"

SITE      = "https://kidharmilega.in"
IDEAS_URL = "/ideas/"
QUIZ_URL  = "/quiz/"
UPDATED   = "September 2026"

DIMS = list("RIASEC")
DIM_LABELS = {"R": "Maker", "I": "Thinker", "A": "Creator", "S": "Helper", "E": "Persuader", "C": "Organiser"}
DIM_PHRASES = {
    "R": "like working with your hands and real, physical things",
    "I": "like figuring out how and why things work",
    "A": "like creating things in your own style",
    "S": "like helping, teaching and looking after people",
    "E": "like selling, persuading and taking charge",
    "C": "like order, numbers and systems that run smoothly",
}
ARCHETYPES = {
    "RI": "The Builder-Engineer", "RA": "The Maker", "RS": "The Hands-on Helper", "RE": "The Hustling Doer",
    "RC": "The Reliable Operator", "IA": "The Inventor", "IS": "The Expert Guide", "IE": "The Strategist",
    "IC": "The Analyst", "AS": "The Creative Mentor", "AE": "The Brand Builder", "AC": "The Detail Designer",
    "SE": "The Community Builder", "SC": "The Service Pro", "EC": "The Trader",
}

# One carefully worded list, so every page says the same thing about each scheme.
SCHEMES = {
    "udyam": ("Udyam registration", "Free, online, Aadhaar-based MSME registration. Most MSME benefits, including priority-sector bank loans, start here."),
    "mudra": ("PM Mudra Yojana", "Collateral-free bank loans in four tiers: Shishu (up to ₹50,000), Kishore (up to ₹5 lakh), Tarun (up to ₹10 lakh) and Tarun Plus (up to ₹20 lakh, for borrowers who repaid a Tarun loan)."),
    "pmegp": ("PMEGP", "Credit-linked subsidy for new units: projects up to ₹50 lakh (manufacturing) or ₹20 lakh (services), with 15–35% of project cost as subsidy depending on your category and whether you are in a rural area."),
    "pmfme": ("PMFME", "35% credit-linked capital subsidy, up to ₹10 lakh per unit, for micro food-processing businesses. ODOP products get priority."),
    "cgtmse": ("CGTMSE", "A government credit guarantee that lets banks lend to micro and small enterprises without collateral. Ask your bank for a CGTMSE-covered loan."),
    "standup": ("Stand-Up India", "Bank loans from ₹10 lakh to ₹1 crore for new businesses started by women or SC/ST founders."),
    "vishwakarma": ("PM Vishwakarma", "For registered traditional artisans (potters, toy makers, tailors and other listed trades): skill training with a stipend, a ₹15,000 toolkit incentive and collateral-free loans at 5% interest."),
    "startupindia": ("Startup India (DPIIT recognition)", "Recognised startups get easier compliance, tax-holiday eligibility and access to government seed and fund-of-funds programmes."),
}


def esc(s):
    return html.escape(str(s), quote=True)


def lakh(v):
    if v is None:
        return ""
    return f"₹{v / 100:g} Cr" if v >= 100 else f"₹{v:g}L"


def rupees(r):
    return "" if not r else lakh(r / 100000)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def significant(name):
    stop = {"and", "the", "of", "for", "with", "brand", "products", "product", "processing", "based",
            "snacks", "crafts", "craft", "online", "d2c", "store", "service", "services"}
    words = {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z]+", name.lower())}
    return {w for w in words if w not in stop and len(w) > 3}


def archetype(riasec):
    a, b = sorted(DIMS, key=lambda d: -riasec[DIMS.index(d)])[:2]
    key = a + b if DIMS.index(a) < DIMS.index(b) else b + a
    return ARCHETYPES[key], a, b


def cosine(x, y):
    num = sum(a * b for a, b in zip(x, y))
    den = (sum(a * a for a in x) ** 0.5) * (sum(b * b for b in y) ** 0.5)
    return num / den if den else 0


# ── Data helpers ─────────────────────────────────────────────────────────────

def load():
    data = json.loads(IDEAS.read_text(encoding="utf-8"))
    models = {m["slug"]: m for m in data["models"]}
    ideas = data["ideas"]
    for i in ideas:
        i["m"] = models[i["model"]]
    districts = json.loads(ODOP.read_text(encoding="utf-8"))
    return models, ideas, districts


def idea_districts(idea, districts):
    """ODOP districts for this exact idea (by product name), else for its business model."""
    exact = []
    if idea.get("odop_here"):
        keys = set(idea["odop_here"]["keys"])
        exact = [d for d in districts if f"{d['district']}|{d['state']}" in keys]
    if not exact:
        words = significant(idea["name"])
        exact = [d for d in districts if words & significant(d["product"])]
    if exact:
        return exact, True
    return [d for d in districts if d["idea"] == idea["model"]], False


SYNONYMS = {"attar": {"perfume", "fragrance", "attar"}, "perfume": {"perfume", "fragrance", "attar"},
            "makhana": {"makhana", "foxnut"}, "foxnut": {"makhana", "foxnut"}, "kurta": {"kurta", "clothing", "wear"},
            "chikankari": {"chikan", "chikankari", "lucknow"}, "toy": {"toy", "toys", "wooden"}}


def idea_words(idea):
    words = significant(idea["name"]) | significant(idea.get("phrase", ""))
    for w in list(words):
        words |= SYNONYMS.get(w, set())
    return words


def pitch_example(p):
    deal = p["deal"]
    return {"name": p["name"], "what": p.get("brief") or p["description"], "season": p["season"], "episode": p["episode"],
            "city": p["city"].split(",")[0], "revenue_lakh": p["yearly_revenue_lakh"],
            "ask": {"amount_lakh": p["ask"]["amount_lakh"], "equity_pct": p["ask"]["equity_pct"]},
            "deal": None if not deal else {"amount_lakh": deal["amount_lakh"], "equity_pct": deal["equity_pct"], "sharks": deal["sharks"]}}


def shark_examples(idea, pitches):
    m = idea["m"]
    out = []
    if idea.get("inspired_by"):
        out.append(("inspired", idea["inspired_by"]))
    # Pitches in the same business model whose description matches this idea come first.
    words = idea_words(idea)
    close = [p for p in pitches if p.get("idea_slug") == idea["model"] and words & significant(p["description"])]
    close.sort(key=lambda p: (p["deal"] is None, -(p["yearly_revenue_lakh"] or 0)))
    for p in close[:3]:
        if not any(x[1]["name"] == p["name"] for x in out):
            out.append(("close", pitch_example(p)))
    for e in (m.get("sharktank") or {}).get("examples", []):
        if not any(x[1]["name"] == e["name"] for x in out):
            out.append(("space", e))
    if idea.get("d2c") and len(out) < 3:
        for e in m.get("sharktank_d2c") or []:
            out.append(("d2c", e))
    return out[:4]


def alternatives(idea, ideas, n=3):
    """Related ideas from other business models: similar personality profile, same or lower budget."""
    pool = [i for i in ideas if i["model"] != idea["model"] and i["budget"] <= idea["budget"]]
    pool.sort(key=lambda i: (-cosine(idea["m"]["riasec"], i["m"]["riasec"]), i["budget"], i["id"]))
    seen, out = set(), []
    for i in pool:
        if i["model"] in seen:
            continue
        seen.add(i["model"])
        out.append(i)
        if len(out) == n:
            break
    return out


def siblings(idea, ideas, n=6):
    return [i for i in ideas if i["model"] == idea["model"] and i["id"] != idea["id"]][:n]


def cluster_viability(n_districts, is_product):
    if not is_product:
        return "Not cluster-dependent", "Runs anywhere with local demand"
    if n_districts >= 5:
        return "High", f"ODOP product of {n_districts} districts"
    if n_districts >= 1:
        return "Medium", f"ODOP product of {n_districts} district{'s' if n_districts > 1 else ''}"
    return "Low", "No ODOP cluster; source from wholesale markets"


# ── Rendering ────────────────────────────────────────────────────────────────

BUDGET_LABELS = {1: "Under ₹50K", 2: "₹50K–2L", 3: "₹2–10L", 4: "₹10L+"}


def pitch_li(kind, e):
    ask = e["ask"]
    val_ask = ask["amount_lakh"] / ask["equity_pct"] * 100 if ask.get("equity_pct") else None
    if e["deal"]:
        d = e["deal"]
        val_deal = d["amount_lakh"] / d["equity_pct"] * 100 if d.get("equity_pct") else None
        outcome = f"Got <strong>{lakh(d['amount_lakh'])} for {d['equity_pct']:g}%</strong>"
        if d["sharks"]:
            outcome += f" from {esc(', '.join(d['sharks']))}"
        if val_ask and val_deal and val_deal < val_ask:
            cut = round((1 - val_deal / val_ask) * 100)
            outcome += f". The sharks valued it at {lakh(round(val_deal))}, {cut}% below the {lakh(round(val_ask))} the founders asked for."
        else:
            outcome += "."
    else:
        outcome = f"Asked {lakh(ask['amount_lakh'])} for {ask['equity_pct']:g}% (a {lakh(round(val_ask))} valuation) and left without a deal." if val_ask else "No deal."
    tag = {"inspired": "The pitch behind this idea", "close": "Closest match to this idea", "space": "Same business model", "d2c": f"D2C brand · {esc(e.get('space', ''))}"}[kind]
    rev = f" Yearly revenue at pitch: <strong>{lakh(e['revenue_lakh'])}</strong>." if e.get("revenue_lakh") else ""
    city = f", {esc(e['city'])}" if e.get("city") else ""
    return (f'<li class="pitch"><p class="pitch-tag">{tag}</p>'
            f'<h4>{esc(e["name"])} <span class="muted">Season {e["season"]}, Episode {e["episode"]}{city}</span></h4>'
            f'<p>{esc(e["what"])}.{rev}</p><p>{outcome}</p></li>')


def render(idea, pb, it, ideas, districts, pitches):
    m = idea["m"]
    name, key = idea["name"], idea["key"]
    quiz = f"{QUIZ_URL}?idea={key}"
    arch, d1, d2 = archetype(m["riasec"])
    ds, exact = idea_districts(idea, districts)
    is_product = pb.get("cluster_based", True)
    via, via_note = cluster_viability(len(ds), is_product)
    idea["phrase"] = it["phrase"]
    exs = shark_examples(idea, pitches)
    st = m.get("sharktank")
    alts = alternatives(idea, ideas)
    sibs = siblings(idea, ideas)
    snap = pb["snapshot"]
    title = f"Should You Start {it['phrase']} in 2026? Costs, Margins & Fit Check"
    h1 = f"Should You Start {it['phrase']} in 2026?"
    desc = it["verdict"].split(". ")[0].rstrip(".") + ". Setup costs, margins, Shark Tank lessons and a 90-day plan."
    canonical = f"{SITE}{IDEAS_URL}{key}/"

    # 1. Verdict + snapshot
    tiles = [
        ("Initial capital", f"{snap['capital_bootstrap']}", f"Scaled: {snap['capital_scaled']}"),
        ("Gross margin", snap["margin_d2c"], snap["margin_production"]),
        ("Breakeven", snap["breakeven"], ""),
        ("Ease of distribution", f"{snap['distribution_score']} / 5", snap["distribution_note"]),
        ("ODOP / cluster viability", via, via_note),
    ]
    snap_html = "".join(f'<div class="tile"><p class="tile-label">{esc(a)}</p><p class="tile-value">{esc(b)}</p>'
                        f'{f"<p class=tile-note>{esc(c)}</p>" if c else ""}</div>' for a, b, c in tiles)

    # 2. Market reality
    tw = "".join(f"<li>{esc(x)}</li>" for x in pb["tailwinds"])
    hw = "".join(f"<li>{esc(x)}</li>" for x in pb["headwinds"])

    # 3. Unit economics
    rows = "".join(f"<tr><td>{esc(r['item'])}</td><td class=num>{esc(r['low'])} – {esc(r['high'])}</td><td>{esc(r['covers'])}</td></tr>"
                   for r in pb["setup_costs"])
    ue = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in pb["unit_economics"]["rows"])

    # 4. Shark Tank
    if exs:
        st_summary = ""
        if st:
            st_summary = (f'<p class="stat-line">{st["pitches"]} Shark Tank India pitch{"es" if st["pitches"] > 1 else ""} in this business model · '
                          f'{st["deals"]} got a deal' + (f' · median yearly revenue {lakh(st["median_revenue_lakh"])}' if st.get("median_revenue_lakh") else "") + "</p>")
        st_html = st_summary + '<ul class="pitches">' + "".join(pitch_li(k, e) for k, e in exs) + "</ul>"
    else:
        st_html = "<p>No Shark Tank India pitch matches this business model yet, so there's no investor record to learn from. The questions below are what investors ask in this category.</p>"
    probes = "".join(f"<li>{esc(x)}</li>" for x in pb["investor_probes"])

    # 5. Cluster / sourcing
    if ds:
        dl = "".join(f'<li><a href="{esc(d["url"])}">{esc(d["district"])}, {esc(d["state"])}</a> — {esc(d["product"])}'
                     + (f'<span class="muted"> · setup {rupees(d["cost"][0])}–{rupees(d["cost"][1])}, D2C margin {esc(d["margin"])}</span>' if d["cost"][0] else "")
                     + "</li>" for d in ds[:5])
        more = f'<p class="muted">{len(ds) - 5} more districts make this. See all on <a href="{SITE}/products/">KidharMilega</a>.</p>' if len(ds) > 5 else ""
        lead = ("These districts have this exact product as their ODOP, so raw material, skilled workers and finished-goods suppliers are concentrated there."
                if exact else "These districts have ODOP products that feed this business model.")
        cluster_html = f"<p>{lead}</p><ul class='districts'>{dl}</ul>{more}"
    elif is_product:
        cluster_html = "<p>No ODOP district specialises in this product, so you will source from wholesale markets near you.</p>"
    else:
        cluster_html = ""
    schemes = "".join(f"<li><strong>{esc(SCHEMES[s][0])}</strong>: {esc(SCHEMES[s][1])}</li>" for s in pb["schemes"])
    licences = "".join(f"<li>{esc(x)}</li>" for x in pb["licences"])

    # 6. Hard truths / 7. Plan
    truths = "".join(f"<li><h4>{esc(t['title'])}</h4><p>{esc(t['text'])}</p></li>" for t in pb["hard_truths"])
    plan = "".join(f'<li><p class="phase">Days {esc(p["days"])}</p><h4>{esc(p["title"])}</h4><ul>'
                   + "".join(f"<li>{esc(s)}</li>" for s in p["steps"]) + "</ul></li>" for p in pb["plan"])

    # 8. Decision gate
    alt_html = "".join(f'<li><a href="{IDEAS_URL}{i["key"]}/">{esc(i["name"])}</a> <span class="muted">· start {BUDGET_LABELS[i["budget"]]}</span></li>' for i in alts)
    sib_html = ", ".join(f'<a href="{IDEAS_URL}{i["key"]}/">{esc(i["name"])}</a>' for i in sibs)
    hubs = "".join(f'<li><a href="{esc(d["url"])}">{esc(d["product"])} in {esc(d["district"])}</a></li>' for d in ds[:3])

    faq = "".join(f"<details><summary>{esc(f['q'])}</summary><p>{esc(f['a'])}</p></details>" for f in it["faq"])

    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc,
         "dateModified": date.today().isoformat(), "author": {"@type": "Organization", "name": "KidharMilega"},
         "publisher": {"@type": "Organization", "name": "KidharMilega", "url": SITE}, "mainEntityOfPage": canonical},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in it["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Business ideas", "item": SITE + IDEAS_URL},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical}]},
    ]

    shark_cta = '<a class="btn ghost" href="#shark-tank">Read the Shark Tank examples ↓</a>' if exs else '<a class="btn ghost" href="#sourcing">See where to source ↓</a>'

    body = f"""
<article class="guide">
  <nav class="crumbs"><a href="/">Home</a> › <a href="{IDEAS_URL}">Business ideas</a> › {esc(m['category'])}</nav>
  <p class="eyebrow">{esc(m['category'])} · Updated {UPDATED}</p>
  <h1>{esc(h1)}</h1>
  <p class="dek">An honest reality check and setup guide: what it costs, what you keep, what Shark Tank India taught founders in this space, and a 90-day plan to test it.</p>
  <div class="cta-row">
    <a class="btn primary" href="{quiz}">Check your readiness →</a>
    {shark_cta}
  </div>

  <section id="verdict">
    <h2>The 30-second verdict</h2>
    <p class="verdict">{esc(it['verdict'])}</p>
    <div class="tiles">{snap_html}</div>
    <p class="fit-line">Best suited to <strong>{arch}</strong>: people who {DIM_PHRASES[d1]} and {DIM_PHRASES[d2]}. <a href="{quiz}">Take the fit check</a> to see how close you are.</p>
  </section>

  <section id="market">
    <h2>Market reality 2026: why now, or why not now?</h2>
    <div class="two-col">
      <div><h3>Tailwinds</h3><ul>{tw}</ul></div>
      <div><h3>Headwinds and traps</h3><ul>{hw}</ul></div>
    </div>
    <h3>What changed in 2026</h3>
    <p>{esc(pb['angle_2026'])}</p>
    <p>{esc(it['angle'])}</p>
  </section>

  <section id="costs">
    <h2>Real setup costs and unit economics</h2>
    <p class="muted">{esc(pb['cost_basis'])}</p>
    <div class="table-wrap"><table>
      <thead><tr><th>Line item</th><th>Cost range</th><th>What it covers</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
    <h3>Unit margin breakdown</h3>
    <p>{esc(pb['unit_economics']['example'])}</p>
    <div class="table-wrap"><table class="ue"><tbody>{ue}</tbody></table></div>
    <p>{esc(pb['unit_economics']['note'])}</p>
  </section>

  <section id="shark-tank">
    <h2>Ground reality: how Indian founders pitched it on Shark Tank</h2>
    {st_html}
    <h3>What investors grill founders on in this category</h3>
    <ul>{probes}</ul>
    <p class="muted">These are the recurring questions in this business model, not quotes from the episodes above.</p>
    <h3>The takeaway for a 2026 bootstrapper</h3>
    <p>{esc(pb['bootstrap_takeaway'])}</p>
  </section>

  <section id="sourcing">
    <h2>{'The cluster advantage: local sourcing and ODOP playbook' if is_product else 'Licences and government support'}</h2>
    {cluster_html}
    {f"<p>{esc(pb['sourcing_edge'])}</p>" if pb.get('sourcing_edge') else ''}
    <h3>Licences you'll need</h3>
    <ul>{licences}</ul>
    <h3>Government support worth checking</h3>
    <ul>{schemes}</ul>
    <p class="muted">Scheme limits change. Confirm current terms on the official portal or with your bank before applying.</p>
  </section>

  <section id="hard-truths">
    <h2>The hard truths: why most attempts fail in year one</h2>
    <ul class="truths">{truths}</ul>
  </section>

  <section id="plan">
    <h2>The 90-day execution blueprint</h2>
    <p>{esc(pb['plan_goal'])}</p>
    <ol class="plan">{plan}</ol>
  </section>

  <section id="decide" class="gate">
    <h2>Is this business the right fit for you?</h2>
    <p>Not every profitable business fits every founder. Take the 3-minute fit check to see whether your interests, personality, budget and location match {esc(name)}.</p>
    <a class="btn primary" href="{quiz}">Check your fit for {esc(name)} →</a>
    <div class="gate-links">
      {f'<div><h3>Explore sourcing hubs</h3><ul>{hubs}</ul></div>' if hubs else ''}
      <div><h3>Compare alternatives</h3><ul>{alt_html}</ul></div>
    </div>
    {f'<p class="muted">Other ideas on the same business model: {sib_html}.</p>' if sib_html else ''}
  </section>

  <section id="faq">
    <h2>Frequently asked questions</h2>
    {faq}
  </section>

  <footer class="method">
    <p><strong>How we built this guide.</strong> Personality fit comes from O*NET occupation data (U.S. Department of Labor, CC BY 4.0). Pitch data comes from Shark Tank India, seasons 1–5. District data comes from KidharMilega's ODOP research. Cost and margin figures are estimates for a small setup in 2026. Get local quotes before you commit money.</p>
  </footer>
</article>"""

    head = f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | KidharMilega</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{esc(h1)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>"""
    return head, body


CSS = """
:root{--accent:#00B4D8;--accent-ink:#0077A8;--accent-soft:#E6F8FD;--ink:#111;--mid:#4a4f55;--muted:#6b7378;--line:#E2EEF2;--bg:#fff;--bg-2:#F5FBFD;--good:#2D7D46;
  --display:'Fraunces',Georgia,serif;--body:'DM Sans',system-ui,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--accent:#36c6e6;--accent-ink:#7fdcf2;--accent-soft:#0f2e36;--ink:#eef3f5;--mid:#c3cbcf;--muted:#98a2a7;--line:#23343a;--bg:#0f1719;--bg-2:#152125;color-scheme:dark}}
:root[data-theme="dark"]{--accent:#36c6e6;--accent-ink:#7fdcf2;--accent-soft:#0f2e36;--ink:#eef3f5;--mid:#c3cbcf;--muted:#98a2a7;--line:#23343a;--bg:#0f1719;--bg-2:#152125;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 var(--body)}
.guide{max-width:760px;margin:0 auto;padding:24px 16px 64px}
a{color:var(--accent-ink)}
h1,h2,h3,h4{font-family:var(--display);line-height:1.2;text-wrap:balance;margin:0}
h1{font-size:clamp(30px,6vw,44px);margin:6px 0 12px}
h2{font-size:clamp(24px,4.5vw,30px);margin:0 0 14px}
h3{font-size:19px;margin:22px 0 8px}
h4{font-size:17px;margin:0 0 4px}
section{padding-top:40px;margin-top:40px;border-top:1px solid var(--line)}
p{margin:0 0 12px}
ul,ol{margin:0 0 12px;padding-left:20px}
li{margin:6px 0}
.crumbs,.muted,.eyebrow{color:var(--muted);font-size:14px}
.eyebrow{text-transform:uppercase;letter-spacing:.06em;margin:18px 0 0}
.dek{font-size:19px;color:var(--mid)}
.cta-row{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0 0}
.btn{display:inline-block;border-radius:999px;padding:12px 20px;font-weight:700;text-decoration:none;border:2px solid var(--accent)}
.btn.primary{background:var(--accent);color:#04262e}
.btn.ghost{color:var(--accent-ink)}
.btn:focus-visible{outline:3px solid var(--accent-ink);outline-offset:2px}
.verdict{font-size:20px;line-height:1.5}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:18px 0}
.tile{background:var(--bg-2);border:1px solid var(--line);border-radius:12px;padding:14px}
.tile-label{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin:0 0 4px}
.tile-value{font-weight:700;font-size:17px;margin:0;font-variant-numeric:tabular-nums}
.tile-note{font-size:14px;color:var(--mid);margin:4px 0 0}
.fit-line{background:var(--accent-soft);border-radius:12px;padding:12px 14px}
.two-col{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:4px 24px}
.table-wrap{overflow-x:auto;margin:0 0 14px}
table{width:100%;border-collapse:collapse;font-size:15px}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
td.num{white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:700}
table.ue td:first-child{width:55%}
.stat-line{font-weight:700}
.pitches,.truths,.plan{list-style:none;padding:0}
.pitch{border:1px solid var(--line);border-radius:12px;padding:14px;margin:10px 0}
.pitch-tag{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--accent-ink);margin:0 0 4px;font-weight:700}
.pitch h4 .muted{font-family:var(--body);font-weight:400}
.truths li{margin:0 0 14px}
.plan>li{border-left:3px solid var(--accent);padding:2px 0 2px 14px;margin:0 0 18px}
.phase{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--accent-ink);font-weight:700;margin:0}
.gate{background:var(--accent-soft);border:1px solid var(--accent);border-radius:16px;padding:24px 18px;margin-top:48px}
.gate-links{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:4px 24px;margin-top:10px}
details{border-bottom:1px solid var(--line);padding:12px 0}
summary{font-weight:700;cursor:pointer}
details p{margin:8px 0 0}
.method{margin-top:40px;font-size:14px;color:var(--muted)}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto}}
html{scroll-behavior:smooth}
"""


def page(head, body):
    return f"<!doctype html>\n<html lang=\"en\">\n<head>\n{head}\n</head>\n<body>{body}\n</body>\n</html>\n"


def main():
    models, ideas, districts = load()
    pitches = json.loads(PITCHES.read_text(encoding="utf-8"))
    by_key = {i["key"]: i for i in ideas}
    built = []
    for f in sorted(IDEAS_TXT.glob("*.json")):
        it = json.loads(f.read_text(encoding="utf-8"))
        idea = by_key.get(f.stem)
        if not idea:
            print(f"! content/ideas/{f.name}: no idea with key {f.stem}")
            continue
        pb_file = PLAYBOOKS / f"{idea['model']}.json"
        if not pb_file.exists():
            print(f"! {f.stem}: missing playbook for model {idea['model']}")
            continue
        pb = json.loads(pb_file.read_text(encoding="utf-8"))
        head, body = render(idea, pb, it, ideas, districts, pitches)
        out = OUT / "ideas" / idea["key"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(head, body), encoding="utf-8")
        built.append((idea, head, body))
    print(f"✓ {len(built)} guide pages → {OUT.relative_to(ROOT)}/ideas/")

    if "--preview" in sys.argv and built:
        # One file with every page, switchable by a menu, for review on a single link.
        options = "".join(f'<option value="p{n}">{esc(i["name"])}</option>' for n, (i, _, _) in enumerate(built))
        sections = "".join(f'<div class="pv" id="p{n}"{"" if n == 0 else " hidden"}>{b}</div>' for n, (_, _, b) in enumerate(built))
        pv_css = ".pv-bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}.pv-bar label{font-size:14px;color:var(--muted)}.pv-bar select{font:inherit;padding:8px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink);max-width:100%}"
        script = "<script>const s=document.getElementById('pv-select');s.onchange=()=>{document.querySelectorAll('.pv').forEach(p=>p.hidden=p.id!==s.value);window.scrollTo(0,0)};</script>"
        preview = (f'<title>Idea Guide Samples</title>\n<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet">'
                   f"<style>{CSS}{pv_css}</style>"
                   f'<div class="pv-bar"><label for="pv-select">Sample page</label><select id="pv-select">{options}</select>'
                   f'<span class="muted">Links on these pages point to kidharmilega.in paths that go live with the rollout.</span></div>'
                   f"{sections}{script}")
        (OUT / "preview.html").write_text(preview, encoding="utf-8")
        print(f"✓ preview → {OUT.relative_to(ROOT)}/preview.html")


if __name__ == "__main__":
    main()
