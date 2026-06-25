import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const [fieldNotes, signal, recipes, labs] = await Promise.all([
    getCollection('fieldNotes'),
    getCollection('signal'),
    getCollection('recipes'),
    getCollection('labs'),
  ]);

  const items = [
    ...fieldNotes.map((e) => ({
      title: `${e.data.id.toUpperCase()}: ${e.data.title}`,
      pubDate: e.data.date,
      description: e.data.description,
      link: `/field-notes/${e.id}/`,
      categories: ['Field Notes'],
    })),
    ...signal.map((e) => ({
      title: `${e.data.id.toUpperCase()}: ${e.data.title}`,
      pubDate: e.data.date,
      description: e.data.description,
      link: `/signal/${e.id}/`,
      categories: ['Signal'],
    })),
    ...recipes.map((e) => ({
      title: `${e.data.id.toUpperCase()}: ${e.data.title}`,
      pubDate: e.data.verifiedOn,
      description: e.data.description,
      link: `/recipes/${e.id}/`,
      categories: ['Recipes'],
    })),
    ...labs.map((e) => ({
      title: `${e.data.id.toUpperCase()}: ${e.data.title}`,
      pubDate: e.data.date,
      description: e.data.description,
      link: `/labs/${e.id}/`,
      categories: ['Labs'],
    })),
  ].sort((a, b) => b.pubDate.getTime() - a.pubDate.getTime());

  return rss({
    title: 'Agent Engineering Lab',
    description: 'Field Notes, Signal, Recipes, and Lab Reports from the agentic AI publication by Sunil Prakash.',
    site: context.site!,
    items,
    customData: `<language>en-us</language>`,
  });
}
