import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';
import { bySlug } from '~/data/pattern-language';

export async function GET(context: APIContext) {
  const [fieldNotes, signal, recipes, labs, architecture, patterns] = await Promise.all([
    getCollection('fieldNotes'),
    getCollection('signal'),
    getCollection('recipes'),
    getCollection('labs'),
    getCollection('architecture'),
    getCollection('patterns'),
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
    ...architecture
      .filter((e) => e.data.status !== 'draft')
      .map((e) => ({
        title: `${e.data.id.toUpperCase()}: ${e.data.title}`,
        pubDate: e.data.updated,
        description: e.data.description,
        link: `/architecture/${e.id}/`,
        categories: ['Architecture'],
      })),
    ...patterns.map((e) => {
      const meta = bySlug(e.id);
      return {
        title: meta ? meta.name : e.id,
        pubDate: e.data.updated,
        description: e.data.description,
        link: `/patterns/${e.id}/`,
        categories: ['Patterns'],
      };
    }),
  ].sort((a, b) => b.pubDate.getTime() - a.pubDate.getTime());

  return rss({
    title: 'Agent Engineering Lab',
    description: 'Field Notes, Signal, Recipes, Lab Reports, and Architecture blueprints from the agentic AI publication by Sunil Prakash.',
    site: context.site!,
    items,
    customData: `<language>en-us</language>`,
  });
}
