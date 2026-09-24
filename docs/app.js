import { QUESTIONS, INTEREST_SCALE, AGREE_SCALE } from "./questions.js";
import {
  computeProfile, match, whyCopy, typeCode, archetype, topDims,
  DIMS, DIM_LABELS, BUDGET_LABELS, RELAX_LABELS,
} from "./scoring.js";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

const PROMPTS = {
  interest: "How would you feel spending a good part of your day…",
  trait: "How much do you agree?",
  choice: "",
};

let ideas = [];
let answers = {};
let idx = 0;

const ideasReady = fetch("data/ideas.json").then((r) => r.json()).then((d) => { ideas = d.ideas; });

function show(id) {
  for (const s of document.querySelectorAll(".screen")) s.hidden = s.id !== id;
  window.scrollTo(0, 0);
}

function render() {
  const q = QUESTIONS[idx];
  $("bar").style.width = `${(idx / QUESTIONS.length) * 100}%`;
  $("counter").textContent = `Question ${idx + 1} of ${QUESTIONS.length}`;
  $("prompt").textContent = PROMPTS[q.kind];
  $("qtext").textContent = q.text;
  $("back").hidden = idx === 0;

  const opts = q.kind === "choice"
    ? q.options
    : (q.kind === "interest" ? INTEREST_SCALE : AGREE_SCALE).map((label, i) => ({ value: i + 1, label }));

  $("options").innerHTML = "";
  for (const o of opts) {
    const b = document.createElement("button");
    b.className = "opt" + (answers[q.id] === o.value ? " selected" : "");
    b.textContent = o.label;
    b.onclick = () => choose(q.id, o.value);
    $("options").appendChild(b);
  }
}

function choose(id, value) {
  answers[id] = value;
  if (idx < QUESTIONS.length - 1) {
    idx++;
    render();
  } else {
    finish();
  }
}

async function finish() {
  await ideasReady;
  const profile = computeProfile(QUESTIONS, answers);
  const result = match(ideas, profile);
  renderResult(profile, result);
  show("result");
}

function ideaCard(r, profile, isTop) {
  const i = r.idea;
  return `
    <article class="card ${isTop ? "top" : ""}">
      <p class="eyebrow">${isTop ? "Your best match" : "Also a strong fit"} · ${Math.round(r.score * 100)}% fit</p>
      <h3>${esc(i.name)}</h3>
      <p>${esc(i.pitch)}</p>
      <div class="meta">
        <span class="chip">${esc(i.category)}</span>
        <span class="chip">Start: ${BUDGET_LABELS[i.budget]}</span>
        <span class="chip">${i.team === "solo" ? "Solo-friendly" : i.team === "small" ? "Small team" : "Needs a team"}</span>
        <span class="chip">${i.time === "full" ? "Full-time" : "Can start part-time"}</span>
      </div>
      <p class="why">${esc(whyCopy(r, profile, { withIntro: isTop }))}</p>
    </article>`;
}

function renderResult(profile, { top, runnersUp, relaxed }) {
  const code = typeCode(profile.traits);
  const arch = archetype(profile.riasec);
  const [a, b] = topDims(profile.riasec, 2);
  const bars = [...DIMS]
    .sort((x, y) => profile.riasec[y] - profile.riasec[x])
    .map((d) => `
      <div class="bar-row"><span>${DIM_LABELS[d]}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${Math.round(profile.riasec[d] * 100)}%"></div></div>
      </div>`).join("");

  const relaxNote = relaxed.length
    ? `<p class="notice">Very few ideas matched all your filters, so we also included ${relaxed.map((r) => RELAX_LABELS[r]).join(" and ")}.</p>`
    : "";

  $("result").innerHTML = `
    <p class="eyebrow">Your founder type</p>
    <h1><span class="type-badge">${code}</span> ${arch}</h1>
    <p class="lede">You're strongest as a ${DIM_LABELS[a]} and ${DIM_LABELS[b]}.</p>
    <div class="bars">${bars}</div>
    ${relaxNote}
    ${ideaCard(top, profile, true)}
    ${runnersUp.map((r) => ideaCard(r, profile, false)).join("")}
    <div class="actions">
      <button id="share" class="btn primary">Share my result</button>
      <button id="retake" class="btn">Retake quiz</button>
    </div>
    <p class="fine">The four-letter type is a Myers-Briggs-style shorthand worked out from your personality answers.</p>`;

  $("retake").onclick = () => { answers = {}; idx = 0; show("intro"); };
  $("share").onclick = async () => {
    const text = `I'm ${code} · ${arch} — my best-fit business is ${top.idea.name}. Find yours:`;
    const url = location.href.split("#")[0];
    try {
      if (navigator.share) await navigator.share({ text, url });
      else { await navigator.clipboard.writeText(`${text} ${url}`); $("share").textContent = "Copied!"; }
    } catch { /* share sheet dismissed */ }
  };
}

$("start").onclick = () => { show("quiz"); render(); };
$("back").onclick = () => { if (idx > 0) { idx--; render(); } };
