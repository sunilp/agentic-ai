/**
 * Map Astro Content Layer entries to ContentEntry shape for cross-links.
 *
 * Astro entries have references/cites/patterns nested under `data.*`. The cross-links
 * `buildReverseIndex` expects them at the top level. This mapper bridges the gap.
 *
 * Falls back to entry.id when frontmatter doesn't include a separate `id` field
 * (chapters use the filename as the canonical id).
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
    id: entry.data.id ?? entry.id,
    collection: entry.collection,
    references: entry.data.references,
    cites: entry.data.cites,
    patterns: entry.data.patterns,
  }));
}
