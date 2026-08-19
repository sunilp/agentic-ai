/**
 * Home feed: merges the five publication streams into one dated list for the homepage.
 *
 * Rules:
 * - Newest first across Field Notes, Signal, Recipes, Labs and Architecture blueprints.
 * - Blueprints are a reference section that reads in order and is revised rather than
 *   republished, so at most `maxBlueprints` (default 1) appear: the most recently
 *   updated, lowest `order` on ties. Draft blueprints never appear, and a blueprint is
 *   never the featured piece (it slots into the list by its updated date).
 * - Featured = the newest editorial piece; the next `limit` (default 5) are the list.
 *
 * Inputs are plain shapes (not astro:content types) so this stays unit-testable.
 */

export type Stream = 'Field Note' | 'Signal' | 'Recipe' | 'Lab' | 'Blueprint';

export interface FeedItem {
  id: string;
  slug: string;
  stream: Stream;
  rubric: string;      // 'SG-004 · Signal'
  title: string;
  dek: string;
  href: string;
  date: Date;
  dateLabel: '' | 'Updated' | 'Verified';
  banner?: string;
  spot?: string;
  minutes?: number;
}

interface Base { id: string; slug?: string; title: string; }
export interface FieldNoteIn extends Base { dek: string; banner: string; spot?: string; date: Date; readingTime?: number; }
export interface SignalIn extends Base { dek: string; banner: string; date: Date; readingTime?: number; }
export interface RecipeIn extends Base { description: string; spot?: string; verifiedOn: Date; estimatedMinutes?: number; }
export interface LabIn extends Base { description: string; spot?: string; date: Date; readingTime?: number; }
export interface BlueprintIn extends Base { dek: string; spot?: string; order: number; updated: Date; readingTime?: number; status?: 'draft' | 'published'; }

export interface HomeFeedStreams {
  fieldNotes: FieldNoteIn[];
  signal: SignalIn[];
  recipes: RecipeIn[];
  labs: LabIn[];
  architecture: BlueprintIn[];
}

export interface HomeFeedOptions { limit?: number; maxBlueprints?: number; }

const rubric = (id: string, stream: Stream) => `${id.toUpperCase()} · ${stream}`;
const slugOf = (e: Base) => e.slug ?? e.id;

export function buildHomeFeed(
  streams: HomeFeedStreams,
  { limit = 5, maxBlueprints = 1 }: HomeFeedOptions = {},
): { featured: FeedItem | undefined; rest: FeedItem[] } {
  const items: FeedItem[] = [];

  for (const e of streams.fieldNotes) {
    items.push({ id: e.id, slug: slugOf(e), stream: 'Field Note', rubric: rubric(e.id, 'Field Note'), title: e.title, dek: e.dek,
      href: `/field-notes/${slugOf(e)}/`, date: e.date, dateLabel: '', banner: e.banner, spot: e.spot, minutes: e.readingTime });
  }
  for (const e of streams.signal) {
    items.push({ id: e.id, slug: slugOf(e), stream: 'Signal', rubric: rubric(e.id, 'Signal'), title: e.title, dek: e.dek,
      href: `/signal/${slugOf(e)}/`, date: e.date, dateLabel: '', banner: e.banner, minutes: e.readingTime });
  }
  for (const e of streams.recipes) {
    items.push({ id: e.id, slug: slugOf(e), stream: 'Recipe', rubric: rubric(e.id, 'Recipe'), title: e.title, dek: e.description,
      href: `/recipes/${slugOf(e)}/`, date: e.verifiedOn, dateLabel: 'Verified', spot: e.spot, minutes: e.estimatedMinutes });
  }
  for (const e of streams.labs) {
    items.push({ id: e.id, slug: slugOf(e), stream: 'Lab', rubric: rubric(e.id, 'Lab'), title: e.title, dek: e.description,
      href: `/labs/${slugOf(e)}/`, date: e.date, dateLabel: '', spot: e.spot, minutes: e.readingTime });
  }

  const blueprints = streams.architecture
    .filter((e) => (e.status ?? 'published') === 'published')
    .sort((a, b) => b.updated.getTime() - a.updated.getTime() || a.order - b.order)
    .slice(0, maxBlueprints);
  for (const e of blueprints) {
    items.push({ id: e.id, slug: slugOf(e), stream: 'Blueprint', rubric: rubric(e.id, 'Blueprint'), title: e.title, dek: e.dek,
      href: `/architecture/${slugOf(e)}/`, date: e.updated, dateLabel: 'Updated', spot: e.spot, minutes: e.readingTime });
  }

  items.sort((a, b) => b.date.getTime() - a.date.getTime() || a.id.localeCompare(b.id));

  const featuredIdx = items.findIndex((i) => i.stream !== 'Blueprint');
  const featured = featuredIdx === -1 ? undefined : items[featuredIdx];
  const others = items.filter((_, i) => i !== featuredIdx);
  return { featured, rest: others.slice(0, limit) };
}

/** 'Aug 14' when the year matches `now`, otherwise 'Dec 2, 2025'. */
export function formatFeedDate(date: Date, now: Date = new Date()): string {
  const sameYear = date.getFullYear() === now.getFullYear();
  // Frontmatter dates parse as UTC midnight; format in UTC so the day never shifts by build machine TZ.
  return date.toLocaleDateString('en-US', sameYear
    ? { month: 'short', day: 'numeric', timeZone: 'UTC' }
    : { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
}
