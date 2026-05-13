import { describe, it, expect } from 'vitest';
import { entriesToContentEntries } from './content-helpers';
import type { ContentEntry } from './cross-links';

describe('entriesToContentEntries', () => {
  it('maps Astro entries to ContentEntry shape', () => {
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
        id: 'fn-001',
        collection: 'fieldNotes',
        references: ['ch-04'],
        cites: ['evidence-a'],
        patterns: ['hub-and-spoke'],
      },
    ]);
  });

  it('falls back to entry.id when data.id is missing (e.g. chapters)', () => {
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
