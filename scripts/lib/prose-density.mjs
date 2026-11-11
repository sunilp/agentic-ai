// "you" and hedge density per 1,000 words of prose (frontmatter, imports, code and tags removed).
// Guidance for the governance guide's reader gate, not a hard fail.
const HEDGES = ['may', 'might', 'could', 'perhaps', 'possibly', 'likely', 'generally', 'typically', 'usually', 'often', 'somewhat', 'arguably', 'tends to', 'in some cases', 'to some extent'];
const YOU = new Set(['you', 'your', "you're", 'yours', 'yourself']);

export function proseOf(mdx) {
  return mdx
    .replace(/^---\n[\s\S]*?\n---\n/, '')
    .replace(/^import .*$/gm, '')
    .replace(/```[\s\S]*?```/g, '')
    .replace(/<[^>]+>/g, ' ');
}

export function density(mdx) {
  const text = proseOf(mdx).toLowerCase();
  const words = text.match(/[a-z][a-z'-]*/g) ?? [];
  const n = words.length || 1;
  const you = words.filter((w) => YOU.has(w)).length;
  let hedges = 0;
  for (const h of HEDGES) hedges += (text.match(new RegExp(`\\b${h}\\b`, 'g')) ?? []).length;
  return { words: words.length, youPer1k: +((you * 1000) / n).toFixed(1), hedgesPer1k: +((hedges * 1000) / n).toFixed(1) };
}
