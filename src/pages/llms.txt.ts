import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

// Generated llms.txt: a curated, link-first index of the Lab for LLMs and
// answer engines. Built from the content collections so it never goes stale.
export async function GET(context: APIContext) {
  const base = (context.site?.toString() ?? 'https://agenticlab.sunilprakash.com/').replace(/\/$/, '');

  const [chapters, fieldNotes, signal, recipes, labs] = await Promise.all([
    getCollection('chapters'),
    getCollection('fieldNotes'),
    getCollection('signal'),
    getCollection('recipes'),
    getCollection('labs'),
  ]);

  const byDateDesc = (a: any, b: any) =>
    (b.data.date?.getTime?.() ?? 0) - (a.data.date?.getTime?.() ?? 0);
  const blurb = (d: any) => d.description ?? d.dek ?? '';
  const line = (e: any, path: string) =>
    `- [${String(e.data.id).toUpperCase()}: ${e.data.title}](${base}/${path}/${e.id}/): ${blurb(e.data)}`;

  const fn = [...fieldNotes].sort(byDateDesc).map((e) => line(e, 'field-notes')).join('\n');
  const sg = [...signal].sort(byDateDesc).map((e) => line(e, 'signal')).join('\n');
  const rc = [...recipes].map((e) => line(e, 'recipes')).join('\n');
  const lab = [...labs].sort(byDateDesc).map((e) => line(e, 'labs')).join('\n');
  const ch = [...chapters]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((e) => `- [${e.data.title}](${base}/book/${e.id}/): ${e.data.description ?? ''}`)
    .join('\n');

  const body = `# Agent Engineering Lab

> A working publication on building agent systems that survive contact with reality. Field Notes, Signals, Recipes, Lab Notes, and an interactive Bench, grounded in evidence. Written by Sunil Prakash.

- Site: ${base}/
- Full text for ingestion: ${base}/llms-full.txt
- RSS: ${base}/rss.xml
- The book, "Agentic AI for Serious Engineers" (the canonical reference): https://www.amazon.com/dp/B0GVG6848F

## What this is

The Lab is a layered editorial system. The book is the canonical reference. Four ongoing streams sit alongside it: Field Notes are observations from inside the work, Signals are commentary on the discourse around agent engineering, Recipes are buildable-in-an-afternoon walkthroughs with verified code, and Lab Notes are empirical experiments with measured results. Evidence, Patterns, and Projects are reference material. The Bench is an interactive, in-browser playground.

## Field Notes
${fn}

Index: ${base}/field-notes/

## Signals
${sg}

Index: ${base}/signal/

## Recipes
${rc}

Index: ${base}/recipes/

## Lab Notes
${lab}

Index: ${base}/labs/

## The Bench (interactive)

- [Loop Lab](${base}/bench/): toggle the external fences on an agent loop and watch the same agent either delete a production database or get stopped, in the browser, no setup.

## The book

${ch}

## Navigation

- Home: ${base}/
- About: ${base}/about/
- Start here: ${base}/start/
- Manifesto: ${base}/manifesto/
- The Bench: ${base}/bench/
- Patterns: ${base}/patterns/

## Voice and audience

Written for backend engineers, platform engineers, staff-plus engineers, architects, and technical leads building AI systems for production. The work favors opinionated engineering judgment, named failure modes, working code, restraint over breadth, and evidence over hype.

## Author

Sunil Prakash, an engineering leader and researcher focused on enterprise AI systems, agent identity, and production agent architecture. Profile: https://sunilprakash.com
`;

  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
