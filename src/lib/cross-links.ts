/**
 * Cross-link reverse-index builder.
 *
 * Content frontmatter contains forward references (`references`, `cites`, `patterns`).
 * At build time we walk all collections and compute the inverse — given an item ID,
 * which other items reference / cite / mention it.
 *
 * Used by layouts (ChapterLayout, EvidenceLayout, etc.) to render "Cited by..." footers
 * automatically, without authors maintaining back-links manually.
 */

export interface ContentEntry {
  id: string;
  collection: string;
  references?: string[];
  cites?: string[];
  patterns?: string[];
}

export interface ReverseLink {
  id: string;
  collection: string;
}

export interface ReverseLinks {
  referencedBy: ReverseLink[];
  citedBy: ReverseLink[];
  mentionedIn: ReverseLink[];      // pattern usages
}

export type ReverseIndex = Record<string, ReverseLinks>;

/**
 * Build a reverse-index of all references/cites/patterns across collections.
 */
export function buildReverseIndex(entries: ContentEntry[]): ReverseIndex {
  const idx: ReverseIndex = {};

  const ensure = (key: string): ReverseLinks => {
    if (!idx[key]) {
      idx[key] = { referencedBy: [], citedBy: [], mentionedIn: [] };
    }
    return idx[key];
  };

  for (const entry of entries) {
    const link: ReverseLink = { id: entry.id, collection: entry.collection };

    for (const refId of entry.references ?? []) {
      ensure(refId).referencedBy.push(link);
    }
    for (const citeId of entry.cites ?? []) {
      ensure(citeId).citedBy.push(link);
    }
    for (const patternSlug of entry.patterns ?? []) {
      ensure(patternSlug).mentionedIn.push(link);
    }
  }

  return idx;
}

/**
 * Get the reverse links for a single content ID. Safe for unknown IDs (returns empties).
 */
export function getReverseLinks(idx: ReverseIndex, id: string): ReverseLinks {
  return idx[id] ?? { referencedBy: [], citedBy: [], mentionedIn: [] };
}
