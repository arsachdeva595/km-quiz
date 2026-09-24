import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { QUESTIONS } from "../docs/questions.js";
import { computeProfile, match, typeCode, archetype, interestFit, whyCopy } from "../docs/scoring.js";

const { ideas } = JSON.parse(readFileSync(new URL("../docs/data/ideas.json", import.meta.url)));

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
