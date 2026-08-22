/**
 * Map Astro Content Layer entries to ContentEntry shape for cross-links.
 *
 * Astro entries have references/cites/patterns nested under `data.*`. The cross-links
 * `buildReverseIndex` expects them at the top level. This mapper bridges the gap.
 *
 * Always key by `entry.id` (the collection id, i.e. the filename), never by the
 * optional `data.id` frontmatter field. Several collections (fieldNotes, recipes,
 * signal, labs, architecture) carry a frontmatter `id` distinct from their collection
 * id -- e.g. lab-002's frontmatter `id` is "lab-002" but it routes at
 * /labs/incident-triage-durable-agent/ (its collection id / filename). Every page on
 * this site routes by the collection id, so `entry.id` is the only value that is ever
 * safe to build an href from. Preferring `data.id` here (as this used to) built a
 * `ReverseLink.id` that 404s the moment a citing entry's frontmatter id and filename
 * diverge -- it did for architecture and patterns before they were special-cased, and
 * it did for labs, surfacing as /labs/lab-001/ and /labs/lab-002/ in "Cited by" /
 * "Referenced by" sections on field-notes and evidence pages. Chapters and patterns
 * have no separate `data.id`, so for them this is a no-op.
 */
import type { ContentEntry } from './cross-links';

interface AstroEntry {
  id: string;
  collection: string;
  data: {
    id?: string;
    references?: string[];
    cites?: string[];
    patterns?: string[];
  };
}

export function entriesToContentEntries(entries: AstroEntry[]): ContentEntry[] {
  return entries.map((entry) => ({
    id: entry.id,
    collection: entry.collection,
    references: entry.data.references,
    cites: entry.data.cites,
    patterns: entry.data.patterns,
  }));
}
