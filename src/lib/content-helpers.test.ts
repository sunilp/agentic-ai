import { describe, it, expect } from 'vitest';
import { entriesToContentEntries } from './content-helpers';
import type { ContentEntry } from './cross-links';

describe('entriesToContentEntries', () => {
  it('keys by entry.id (the collection id), never by the frontmatter data.id', () => {
    // fieldNotes (like recipes, signal, labs, architecture) carry a frontmatter `id`
    // ("fn-001") distinct from their collection id / filename ("fn-001/index" here,
    // e.g. "incident-triage-durable-agent" for a lab). Every route on this site is
    // built from the collection id, so ContentEntry.id must be entry.id -- keying by
    // data.id here previously built a "Cited by" href from the frontmatter id and
    // 404'd (this is exactly how /labs/lab-001/ and /labs/lab-002/ 404'd from
    // field-notes and evidence pages).
    const entries = [
      {
        id: 'fn-001/index',
        collection: 'fieldNotes',
        data: {
          id: 'fn-001',
          title: 'X',
          references: ['ch-04'],
          cites: ['evidence-a'],
          patterns: ['hub-and-spoke'],
        },
      },
    ];
    const result = entriesToContentEntries(entries as any);
    expect(result).toEqual<ContentEntry[]>([
      {
        id: 'fn-001/index',
        collection: 'fieldNotes',
        references: ['ch-04'],
        cites: ['evidence-a'],
        patterns: ['hub-and-spoke'],
      },
    ]);
  });

  it('uses entry.id when data.id is missing too (e.g. chapters)', () => {
    const entries = [
      {
        id: '01-what-agentic-means',
        collection: 'chapters',
        data: {
          title: 'X',
          references: ['fn-001'],
        },
      },
    ];
    const result = entriesToContentEntries(entries as any);
    expect(result[0].id).toBe('01-what-agentic-means');
    expect(result[0].references).toEqual(['fn-001']);
  });

  it('handles missing reference fields gracefully', () => {
    const entries = [
      { id: 'x', collection: 'patterns', data: { slug: 'x', name: 'X', oneLine: '', whenToUse: '', whenNotToUse: '' } },
    ];
    const result = entriesToContentEntries(entries as any);
    expect(result[0].references).toBeUndefined();
    expect(result[0].cites).toBeUndefined();
    expect(result[0].patterns).toBeUndefined();
  });
});
