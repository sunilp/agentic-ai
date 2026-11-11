import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { STEPS, kitUrl, stepByN } from '~/data/governance-path';
import { EXAMPLES } from '~/data/governance-examples';
import policy from '~/data/governance-policy.json';
import { OVERRIDES, TIER_ROWS, computeTier } from '~/lib/governance-tier';
import { bySlug, ENTRIES, type Entry, type Layer, type Stage } from '~/data/pattern-language';

// Generated llms-full.txt: the full text of the four editorial streams,
// cleaned of MDX scaffolding, so an LLM can ingest the Lab's own version
// rather than scraped HTML. The book chapters are linked from llms.txt, not
// inlined here.
//
// Patterns are appended below as their own section: the catalogue's full
// essay text (~46,000 words across 26 entries) was previously entirely
// absent from this file, the single largest LLM-search gap on the site.
function clean(body: string): string {
  return body
    .replace(/^import .*$/gm, '') // drop MDX component imports
    .replace(/<Footer3Col[\s\S]*?\/>/g, '') // drop the footer component block
    .replace(/<PullQuote>([\s\S]*?)<\/PullQuote>/g, '> $1') // pull quote -> blockquote
    .replace(/<[^>]+>/g, '') // drop any remaining JSX tags, keep their text
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

const LAYER_LABEL: Record<Layer, string> = { capability: 'Capability', control: 'Control', evidence: 'Evidence' };
const STAGE_LABEL: Record<Stage, string> = {
  design: 'Design',
  build: 'Build',
  evaluate: 'Evaluate',
  operate: 'Operate',
  govern: 'Govern',
};

// Same wording as statusLabel in src/pages/patterns/index.astro, duplicated
// rather than imported since that one lives in a .astro file.
function statusLabel(e: Entry): string {
  if (e.status === 'proposed') return 'proposed';
  if (e.status === 'documented') return `documented, ${e.attributedTo.who}`;
  return `restated, after ${e.nearestPrior[0].who}`;
}

export async function GET(context: APIContext) {
  const base = (context.site?.toString() ?? 'https://agenticlab.sunilprakash.com/').replace(/\/$/, '');

  const [fieldNotes, signal, recipes, labs, patternEssays, govEssays] = await Promise.all([
    getCollection('fieldNotes'),
    getCollection('signal'),
    getCollection('recipes'),
    getCollection('labs'),
    getCollection('patterns'),
    getCollection('governance'),
  ]);
  const patternsBySlug = new Map(patternEssays.map((e) => [e.id, e]));

  const byDateDesc = (a: any, b: any) =>
    (b.data.date?.getTime?.() ?? 0) - (a.data.date?.getTime?.() ?? 0);

  const sections: Array<[string, string, any[]]> = [
    ['Field Notes', 'field-notes', [...fieldNotes].sort(byDateDesc)],
    ['Signals', 'signal', [...signal].sort(byDateDesc)],
    ['Recipes', 'recipes', [...recipes]],
    ['Lab Notes', 'labs', [...labs].sort(byDateDesc)],
  ];

  let out = `# Agent Engineering Lab, full text

Generated from ${base}/. The canonical source for each piece is the URL under it.
The book chapters are indexed at ${base}/llms.txt and published at ${base}/book/.
`;

  for (const [label, path, entries] of sections) {
    out += `\n\n========================================\n${label.toUpperCase()}\n========================================\n`;
    for (const e of entries) {
      out += `\n\n---\n\n# ${e.data.title}\n\nSource: ${base}/${path}/${e.id}/\n`;
      if (e.data.dek) out += `\n${e.data.dek}\n`;
      out += `\n${clean(e.body ?? '')}\n`;
    }
  }

  // Patterns: only entries with a published essay carry body text; every
  // ENTRIES slug currently has one (checked against patternsBySlug), same
  // guard /patterns/index.astro and llms.txt.ts use.
  const patterns = ENTRIES.filter((e) => e.kind === 'pattern' && patternsBySlug.has(e.slug));
  const antiPatterns = ENTRIES
    .filter((e) => e.kind === 'anti-pattern' && patternsBySlug.has(e.slug))
    .sort((a, b) => a.name.localeCompare(b.name));

  const patternEntryText = (meta: Entry) => {
    const entry = patternsBySlug.get(meta.slug)!;
    let text = `\n\n---\n\n# ${meta.name}\n\nSource: ${base}/patterns/${meta.slug}/\n`;
    text += `\n${meta.oneLine}\n`;
    text += `\nLayer: ${LAYER_LABEL[meta.layer]} · Stage: ${STAGE_LABEL[meta.primaryStage]} · Status: ${statusLabel(meta)}\n`;
    if (meta.kind === 'anti-pattern' && meta.replacedBy) {
      const replacement = bySlug(meta.replacedBy);
      if (replacement) text += `\nReplaced by: ${replacement.name} (${base}/patterns/${replacement.slug}/)\n`;
    }
    text += `\n${clean(entry.body ?? '')}\n`;
    return text;
  };

  out += `\n\n========================================\nPATTERNS\n========================================\n`;
  for (const meta of patterns) out += patternEntryText(meta);

  // Anti-patterns get their own clearly labelled subsection, mirroring
  // llms.txt.ts, so an LLM never reads e.g. "Silent Fail Open" as a
  // recommendation rather than a named failure.
  out += `\n\n----------------------------------------\nANTI-PATTERNS (DO NOT USE)\n----------------------------------------\nNamed failures, not recommendations. Each one names the pattern that replaces it.\n`;
  for (const meta of antiPatterns) out += patternEntryText(meta);

  // Governance guide: labels survive clean(), which drops every tag, so mark tracks,
  // shortcuts and the deep dive in words first, and print the data-driven lists and
  // tables as plain text from the same data the components use. Steps print in path order.
  const TIERS = ['T1', 'T2', 'T3', 'T4'] as const;
  const overrideList = OVERRIDES.map((o) => `- Item ${o.item}, ${o.floor === 'T1' ? 'automatic T1' : 'minimum T2'}: ${o.text}.`).join('\n');
  const tierTable = `What the tier changes (${policy.source}):\n` + TIER_ROWS.map(([key, label]) =>
    `- ${label}: ${TIERS.map((t) => `${t} ${policy.tiers[t].name}: ${policy.tiers[t][key]}`).join('; ')}.`).join('\n');
  const examplesTable = "The framework's six worked examples: its recorded scores, run through its rule.\n" + EXAMPLES.map((e) => {
    const r = computeTier(e);
    const overrides = e.overrides.length ? e.overrides.join(', ') : 'none';
    return `- ${e.name} (${e.matrix}, ${kitUrl(`examples/${e.slug}/risk-assessment.md`)}): scored ${r.scored}, overrides ${overrides}, tier ${r.tier}. ${r.reasons.join(' ')}${e.rationale ? ` ${e.rationale}` : ''}`;
  }).join('\n');
  const govClean = (body: string) =>
    clean(body
      .replace(/<ul>\s*\{OVERRIDES\.map[\s\S]*?<\/ul>/, () => overrideList)
      .replace(/<TierRequirements\s*\/>/g, () => tierTable)
      .replace(/<TierExamples\s*\/>/g, () => examplesTable)
      .replace(/<Track for="small">/g, '\nSmall team:\n')
      .replace(/<Track for="enterprise">/g, '\nEnterprise:\n')
      .replace(/<Shortcut quote="([^"]*)">/g, '\nThe shortcut: "$1"\n')
      .replace(/<DeepDive>/g, '\nDeep dive\n'));
  const govBySlug = new Map(govEssays.filter((e) => e.data.status !== 'draft').map((e) => [e.id, e]));
  out += `\n\n========================================\nAI GOVERNANCE, FROM SCRATCH\n========================================\n`;
  for (const s of STEPS) {
    const e = govBySlug.get(s.slug);
    if (!e) continue;
    out += `\n\n---\n\n# Step ${s.n}: ${s.title}\n\nSource: ${base}/governance/${s.slug}/\n`;
    const rests = s.n === 22 ? 'every step' : s.restsOn.length ? s.restsOn.map((n) => `${n} ${stepByN(n)!.short}`).join(', ') : 'nothing';
    out += `\n${e.data.dek}\n\nDone when: ${s.doneWhen}\n`;
    if (s.doneWhenSmall) out += `Done when (small team): ${s.doneWhenSmall}\n`;
    out += `Rests on: ${rests}.\n`;
    if (s.patterns.length) out += `Patterns: ${s.patterns.join(', ')}.\n`;
    out += `Starter kit: ${s.kit.map(kitUrl).join(' ')}\n`;
    out += `\n${govClean(e.body ?? '')}\n`;
  }

  return new Response(out, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
