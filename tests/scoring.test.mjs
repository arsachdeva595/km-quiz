import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { QUESTIONS } from "../docs/questions.js";
import { hydrate, computeProfile, match, scoreIdea, typeCode, archetype, interestFit, whyCopy } from "../docs/scoring.js";

const data = JSON.parse(readFileSync(new URL("../docs/data/ideas.json", import.meta.url)));
const ideas = hydrate(data);
const districts = JSON.parse(readFileSync(new URL("../docs/data/odop.json", import.meta.url)));

function answersFor({ likes = [], traits = {}, ...constraints }) {
  const a = { budget: 4, location: "open", team: "small", time: "full", ...constraints };
  for (const q of QUESTIONS) {
    if (q.kind === "interest") a[q.id] = likes.includes(q.dim) ? 5 : 1;
    if (q.kind === "trait") {
      const level = traits[q.trait] ?? 3;
      a[q.id] = q.reverse ? 6 - level : level;
    }
  }
  return a;
}

test("every question has a unique id", () => {
  assert.equal(new Set(QUESTIONS.map((q) => q.id)).size, QUESTIONS.length);
});

test("profile normalises answers to 0–1 and handles reverse keying", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["A"], traits: { extraversion: 5 } }));
  assert.equal(p.riasec.A, 1);
  assert.equal(p.riasec.R, 0);
  assert.equal(p.traits.extraversion, 1);
  assert.equal(p.traits.openness, 0.5);
});

test("type code maps Big Five traits to four letters", () => {
  assert.equal(typeCode({ extraversion: 0.8, openness: 0.7, agreeableness: 0.2, conscientiousness: 0.9 }), "ENTJ");
  assert.equal(typeCode({ extraversion: 0.1, openness: 0.2, agreeableness: 0.6, conscientiousness: 0.3 }), "ISFP");
});

test("archetype is order-independent", () => {
  assert.equal(archetype({ R: 0, I: 0, A: 0.9, S: 0, E: 0.8, C: 0 }), "The Brand Builder");
  assert.equal(archetype({ R: 0, I: 0, A: 0.8, S: 0, E: 0.9, C: 0 }), "The Brand Builder");
});

test("interest fit is 1 for identical shapes and handles flat profiles", () => {
  assert.ok(Math.abs(interestFit([1, 0, 0, 0, 0, 0], [0.9, 0.1, 0.1, 0.1, 0.1, 0.1]) - 1) < 1e-9);
  const flat = interestFit([0.5, 0.5, 0.5, 0.5, 0.5, 0.5], [1, 0, 0, 0, 0, 0]);
  assert.ok(flat > 0 && flat < 1);
});

test("hands-on + organised profile gets a hands-on idea", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["R", "C"] }));
  const { top } = match(ideas, p);
  assert.ok(["R", "C"].includes(top.idea.code[0]), `got ${top.idea.name} (${top.idea.code})`);
});

test("creative + persuasive profile gets an A/E idea", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["A", "E"] }));
  const { top } = match(ideas, p);
  assert.ok(/[AE]/.test(top.idea.code.slice(0, 2)), `got ${top.idea.name} (${top.idea.code})`);
});

test("hard filters: online side-hustle under ₹50K", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["I", "C"], budget: 1, location: "online", time: "side" }));
  const { top, runnersUp, relaxed } = match(ideas, p);
  assert.deepEqual(relaxed, []);
  for (const r of [top, ...runnersUp]) {
    assert.equal(r.idea.budget, 1);
    assert.ok(["online", "any"].includes(r.idea.location));
    assert.notEqual(r.idea.time, "full");
  }
});

test("filters relax instead of returning nothing", () => {
  const tiny = ideas.filter((i) => i.budget === 4).slice(0, 5);
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["S"], budget: 1 }));
  const res = match(tiny, p);
  assert.ok(res.top);
  assert.equal(res.runnersUp.length, 2);
  assert.ok(res.relaxed.includes("budget"));
});

test("runners-up come from different sub-categories when possible", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["S", "E"] }));
  const { top, runnersUp } = match(ideas, p);
  const subs = [top, ...runnersUp].map((r) => r.idea.sub);
  assert.equal(new Set(subs).size, 3);
});

test("why copy is plain language (no jargon)", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["A", "S"], traits: { extraversion: 5 } }));
  const { top } = match(ideas, p);
  const copy = whyCopy(top, p);
  assert.ok(copy.includes(top.idea.name));
  assert.doesNotMatch(copy, /RIASEC|Big Five|Holland/i);
});

test("matching is deterministic", () => {
  const p = computeProfile(QUESTIONS, answersFor({ likes: ["E"] }));
  assert.equal(match(ideas, p).top.idea.id, match(ideas, p).top.idea.id);
});

test("district ODOP idea gets a local-advantage boost and a mention", () => {
  const lucknow = districts.find((d) => d.district === "Lucknow");
  assert.equal(lucknow.idea, "handloom-textiles-brand");
  const base = computeProfile(QUESTIONS, answersFor({ likes: ["A", "R"] }));
  const local = computeProfile(QUESTIONS, { ...answersFor({ likes: ["A", "R"] }), district: lucknow });
  const idea = ideas.find((i) => i.slug === lucknow.idea);
  const before = scoreIdea(idea, base), after = scoreIdea(idea, local);
  assert.ok(after.score > before.score);
  assert.ok(after.local && !before.local);
  assert.match(whyCopy(after, local, { district: lucknow }), /Lucknow's ODOP product/);
});

test("skipping the district question changes nothing", () => {
  const a = answersFor({ likes: ["S"] });
  const skipped = computeProfile(QUESTIONS, { ...a, district: null });
  assert.equal(match(ideas, skipped).top.idea.id, match(ideas, computeProfile(QUESTIONS, a)).top.idea.id);
});

test("every ODOP district links to a KidharMilega product page", () => {
  for (const d of districts) assert.match(d.url, /^https:\/\/kidharmilega\.in\/products\/[a-z0-9-]+\/$/);
});

test("1000+ ideas: the 500-idea sheet, every model, Shark Tank and ODOP ideas", () => {
  assert.ok(ideas.length >= 1000, `${ideas.length}`);
  assert.equal(ideas.filter((i) => i.source === "sheet-500").length, 500);
  assert.equal(new Set(ideas.map((i) => i.id)).size, ideas.length);
  assert.equal(new Set(ideas.map((i) => i.model)).size, data.models.length);
  for (const i of ideas) assert.ok(i.modelData && i.riasec.length === 6, i.name);
  for (const i of ideas.filter((x) => x.source === "sharktank")) assert.ok(i.inspired_by?.name, i.name);
  for (const i of ideas.filter((x) => x.source === "odop")) assert.ok(i.odop_here?.keys.length, i.name);
});

test("the exact ODOP product of the user's district beats its sibling ideas", () => {
  const lucknow = districts.find((d) => d.district === "Lucknow");
  const p = computeProfile(QUESTIONS, { ...answersFor({ likes: ["A", "R"] }), district: lucknow });
  const exact = ideas.find((i) => i.odop_here?.keys.includes("Lucknow|Uttar Pradesh"));
  const sibling = ideas.find((i) => i.model === exact.model && i.id !== exact.id);
  assert.ok(scoreIdea(exact, p).score > scoreIdea(sibling, p).score);
});

test("D2C ideas without enough own Shark Tank pitches get D2C brand examples", () => {
  const d2c = ideas.filter((i) => i.d2c && (i.modelData.sharktank?.examples.length ?? 0) < 3);
  assert.ok(d2c.length > 0);
  for (const i of d2c) {
    const ex = i.modelData.sharktank_d2c;
    assert.ok(ex?.length, i.name);
    for (const e of ex) assert.ok(e.space && e.deal, e.name);
  }
});

test("ideas sharing a model are tie-broken per answer set, not always the same", () => {
  const siblings = ideas.filter((i) => i.model === "handloom-textiles-brand");
  assert.ok(siblings.length > 10);
  const tops = new Set();
  for (let n = 0; n < 12; n++) {
    const a = answersFor({ likes: ["A", "R"] });
    a.o1 = 1 + (n % 5); a.x1 = 1 + ((n * 2) % 5);
    tops.add(match(siblings, computeProfile(QUESTIONS, a)).top.idea.id);
  }
  assert.ok(tops.size > 1);
  const fixed = computeProfile(QUESTIONS, answersFor({ likes: ["A", "R"] }));
  assert.equal(match(siblings, fixed).top.idea.id, match(siblings, fixed).top.idea.id);
});
