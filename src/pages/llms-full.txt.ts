import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

// Generated llms-full.txt: the full text of the four editorial streams,
// cleaned of MDX scaffolding, so an LLM can ingest the Lab's own version
// rather than scraped HTML. The book chapters are linked from llms.txt, not
// inlined here.
function clean(body: string): string {
  return body
    .replace(/^import .*$/gm, '') // drop MDX component imports
    .replace(/<Footer3Col[\s\S]*?\/>/g, '') // drop the footer component block
    .replace(/<PullQuote>([\s\S]*?)<\/PullQuote>/g, '> $1') // pull quote -> blockquote
    .replace(/<[^>]+>/g, '') // drop any remaining JSX tags, keep their text
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export async function GET(context: APIContext) {
  const base = (context.site?.toString() ?? 'https://agenticlab.sunilprakash.com/').replace(/\/$/, '');

  const [fieldNotes, signal, recipes, labs] = await Promise.all([
    getCollection('fieldNotes'),
    getCollection('signal'),
    getCollection('recipes'),
    getCollection('labs'),
  ]);

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

  return new Response(out, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
