import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
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

  const [fieldNotes, signal, recipes, labs, patternEssays] = await Promise.all([
    getCollection('fieldNotes'),
    getCollection('signal'),
    getCollection('recipes'),
    getCollection('labs'),
    getCollection('patterns'),
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

  return new Response(out, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
